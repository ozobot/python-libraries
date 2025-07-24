from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass

from loguru import logger
from ozobot.common.asyncutils import CancellableTaskGroup, async_iterator_never
from ozobot.common.broadcast import BroadcastManager
from ozobot.jsonrpc.exceptions import CancelledByClientError, CancelledByServerError
from ozobot.jsonrpc.framing import FrameReader, FrameWriter

CANCELLATION_JSONRPC_TYPE = "com/ozobot/jsonrpc/2.0/cancellation"
NOTIFICATION_JSONRPC_TYPE = "com/ozobot/jsonrpc/2.0/notification"

type _TMessageId = int


class AbstractJsonRpcMessage(typing.Protocol):
    @property
    def id(self) -> _TMessageId: ...

    @property
    def jsonrpc(self) -> str: ...


class AbstractJsonRpcCancellationMessage(AbstractJsonRpcMessage, typing.Protocol):
    @classmethod
    def create(cls, id: int, code: int, message: str | None) -> typing.Self: ...


@dataclass(frozen=True)
class Method[TRequest, TResponse, TNotification]:
    request: type[TRequest]
    response: type[TResponse] | None
    notification: type[TNotification] | None

    @classmethod
    def without_response(
        cls, request: type[TRequest], notification: type[TNotification]
    ) -> Method[TRequest, typing.Never, TNotification]:
        return Method(request, None, notification)

    @classmethod
    def without_notifications(
        cls, request: type[TRequest], response: type[TResponse]
    ) -> Method[TRequest, TResponse, typing.Never]:
        return Method(request, response, None)


@dataclass(frozen=True, kw_only=True)
class _ExecutorQuery[TResponse, TNotification]:
    response: typing.Awaitable[TResponse]
    notifications: typing.AsyncIterator[TNotification]
    cancel: typing.Callable[[], None]


class Query[TReq: AbstractJsonRpcMessage, TRes: AbstractJsonRpcMessage, TNotif: AbstractJsonRpcMessage]:
    def __init__(self, request: TReq, method: Method[TReq, TRes, TNotif]) -> None:
        self._request = request
        self._method = method

    @contextlib.asynccontextmanager
    async def execute(self, executor: Executor) -> typing.AsyncIterator[_ExecutorQuery[TRes, TNotif]]:
        message_id = self._request.id
        await executor._writer.write(self._request)

        async with (
            executor._expect_messages(message_id, self._method.response) as response_iter,
            executor._expect_messages(message_id, self._method.notification) as notification_iter,
            executor._expect_messages(message_id, executor._cancellation_message_type) as cancellation_iter,
        ):
            try:
                async with executor._run_executor(
                    response_iter, notification_iter, cancellation_iter, message_id
                ) as query:
                    yield query
            except (CancelledByServerError, CancelledByClientError) as err:
                reason = err.args[0]
                if isinstance(err, CancelledByClientError):
                    await executor._send_cancellation_message(message_id, reason)
                logger.debug("Request cancelled", id=message_id, reason=reason)
                raise asyncio.CancelledError(reason)
            except asyncio.InvalidStateError:
                pass  # this means there was no exception set


class Executor[TMsg: AbstractJsonRpcMessage, TCancellationMsg: AbstractJsonRpcCancellationMessage]:
    def __init__(
        self,
        broadcast: BroadcastManager[TMsg | TCancellationMsg],
        writer: FrameWriter[TMsg | TCancellationMsg],
        cancellation_message_type: type[TCancellationMsg],
    ) -> None:
        self._broadcast = broadcast
        self._writer = writer
        self._cancellation_message_type = cancellation_message_type

    @classmethod
    @contextlib.asynccontextmanager
    async def create(
        cls,
        reader: FrameReader[TMsg],
        writer: FrameWriter[TMsg | TCancellationMsg],
        cancellation_message_type: type[TCancellationMsg],
    ) -> typing.AsyncIterator[Executor[TMsg, TCancellationMsg]]:
        broadcast = BroadcastManager[TMsg | TCancellationMsg]()

        async def _read() -> typing.Never:
            while True:
                async for msg in reader.read():
                    await broadcast.broadcast(msg)

        async with asyncio.TaskGroup() as tg:
            read_task = tg.create_task(_read())

            try:
                yield Executor(broadcast, writer, cancellation_message_type)
            finally:
                read_task.cancel()

    @contextlib.asynccontextmanager
    async def _run_executor[TReq: AbstractJsonRpcMessage, TRes: AbstractJsonRpcMessage, TNotif: AbstractJsonRpcMessage](
        self,
        response_iter: typing.AsyncIterator[TRes],
        notification_iter: typing.AsyncIterator[TNotif],
        cancellation_iter: typing.AsyncIterator[AbstractJsonRpcCancellationMessage],
        message_id: int,
    ) -> typing.AsyncIterator[_ExecutorQuery[TRes, TNotif]]:
        async with CancellableTaskGroup() as tg:
            cancellation_future = asyncio.Future[None]()

            async def _await_cancellation_from_server() -> None:
                message = await anext(cancellation_iter)
                id = message.id
                code = message.code if hasattr(message, "code") else -1
                cancellation_message = message.message if hasattr(message, "message") else ""
                cancellation_future.set_exception(CancelledByServerError(id, code, cancellation_message))
                tg.cancel()

            def _cancel_by_client(reason: str) -> None:
                cancellation_future.set_exception(
                    CancelledByClientError(message_id, reason),
                )
                tg.cancel()

            query = _ExecutorQuery(
                response=anext(response_iter),
                notifications=notification_iter,
                cancel=lambda: _cancel_by_client("Cancelled by user"),
            )
            tg.create_task(_await_cancellation_from_server())

            try:
                yield query
            except asyncio.CancelledError:
                logger.debug("Request cancelled by asyncio.CancelledError", id=message_id)
                # the exception can originate from the program itself (when the control is given above by `yield`)
                #     or by failing the TaskGroup which cancels the program. We'll only consider this the "program cancellation",
                #     when the "Cancelled by user" has no already been set
                if not cancellation_future.done():
                    _cancel_by_client("Program cancellation")
            except Exception:
                logger.exception("Request cancelled by error", id=message_id)
                _cancel_by_client("General failure")
            finally:
                tg.cancel_quietly()

        try:
            ex = cancellation_future.exception()
            if ex:
                raise ex
        except asyncio.InvalidStateError:
            pass  # this means there was no exception set

    @contextlib.asynccontextmanager
    async def _expect_messages(
        self, id: _TMessageId, message_type: type[TMsg | TCancellationMsg] | None
    ) -> typing.AsyncIterator[typing.AsyncGenerator[TMsg | TCancellationMsg]]:
        if message_type:
            with self._broadcast.output() as queue:
                iter = self._iterate_messages(id, message_type, queue)
                try:
                    yield iter
                finally:
                    await iter.aclose()
        else:
            yield async_iterator_never()

    async def _iterate_messages[T: AbstractJsonRpcMessage | AbstractJsonRpcCancellationMessage](
        self, id: _TMessageId, message_type: type[T], read_queue: asyncio.Queue[TMsg | TCancellationMsg]
    ) -> typing.AsyncGenerator[T]:
        while True:
            message = await read_queue.get()

            if isinstance(message, message_type) and message.id == id:
                yield message

    async def _send_cancellation_message(self, id: _TMessageId, message: str) -> None:
        msg = self._cancellation_message_type.create(id, 0, message)
        await self._writer.write(msg)
