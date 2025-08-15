from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass

from loguru import logger
from ozobot.common.asyncutils import CancellableTaskGroup, async_iterator_never
from ozobot.common.broadcast import BroadcastManager
from ozobot.jsonrpc.exceptions import CancelledByClientError, CancelledByServerError

type _TMessageId = int


class _AbstractJsonRpcMessage(typing.Protocol):
    @property
    def id(self) -> _TMessageId: ...

    @property
    def jsonrpc(self) -> str: ...


class _AbstractJsonRpcCancellationMessage(_AbstractJsonRpcMessage, typing.Protocol):
    @property
    def code(self) -> int | None: ...

    @property
    def message(self) -> str | None: ...

    @classmethod
    def create(cls, id: int, code: int, message: str | None) -> typing.Self: ...


class _MessageReader[T: _AbstractJsonRpcMessage](typing.Protocol):
    def read(self) -> typing.AsyncIterator[T]: ...


class _MessageWriter[T: _AbstractJsonRpcMessage](typing.Protocol):
    async def write(self, data: T) -> None: ...


class _MessageReaderWriter[T: _AbstractJsonRpcMessage](_MessageReader[T], _MessageWriter[T], typing.Protocol): ...


@dataclass(frozen=True)
class Method[
    TRequest: _AbstractJsonRpcMessage,
    TResponse: _AbstractJsonRpcMessage | typing.Never,
    TNotification: _AbstractJsonRpcMessage | typing.Never,
]:
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


class Query[TReq: _AbstractJsonRpcMessage, TRes: _AbstractJsonRpcMessage, TNotif: _AbstractJsonRpcMessage]:
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
                raise asyncio.CancelledError(reason) from None
            except asyncio.InvalidStateError:
                pass  # this means there was no exception set


class Executor[TMsg: _AbstractJsonRpcMessage, TCancellationMsg: _AbstractJsonRpcCancellationMessage]:
    def __init__(
        self,
        broadcast: BroadcastManager[TMsg | TCancellationMsg],
        writer: _MessageWriter[TMsg | TCancellationMsg],
        cancellation_message_type: type[TCancellationMsg],
    ) -> None:
        self._broadcast = broadcast
        self._writer = writer
        self._cancellation_message_type = cancellation_message_type

    @classmethod
    @contextlib.asynccontextmanager
    async def create(
        cls,
        transport: _MessageReaderWriter[TMsg | TCancellationMsg],
        cancellation_message_type: type[TCancellationMsg],
    ) -> typing.AsyncIterator[Executor[TMsg, TCancellationMsg]]:
        broadcast = BroadcastManager[TMsg | TCancellationMsg]()

        async def _read() -> typing.Never:
            while True:
                async for msg in transport.read():
                    await broadcast.broadcast(msg)

        try:
            async with asyncio.TaskGroup() as tg:
                program_exception: Exception | None = None
                read_task_exception: BaseException | None = None
                read_task = tg.create_task(_read())

                try:
                    yield Executor(broadcast, transport, cancellation_message_type)
                except Exception as err:
                    program_exception = err
                finally:
                    # check if there was read_task exception
                    try:
                        read_task_exception = read_task.exception()
                    except asyncio.InvalidStateError:
                        pass
                    read_task.cancel()
        except* Exception:
            # we'll handle the read_task exception manually
            pass

        # reraise exceptions outside the taskgroup to get a nice trace
        if program_exception:
            raise program_exception

        if read_task_exception:
            raise read_task_exception

    @contextlib.asynccontextmanager
    async def _run_executor[
        TReq: _AbstractJsonRpcMessage,
        TRes: _AbstractJsonRpcMessage,
        TNotif: _AbstractJsonRpcMessage,
    ](
        self,
        response_iter: typing.AsyncIterator[TRes],
        notification_iter: typing.AsyncIterator[TNotif],
        cancellation_iter: typing.AsyncIterator[_AbstractJsonRpcCancellationMessage],
        message_id: int,
    ) -> typing.AsyncIterator[_ExecutorQuery[TRes, TNotif]]:
        async with CancellableTaskGroup() as tg:
            cancellation_future = asyncio.Future[None]()

            async def _await_cancellation_from_server() -> None:
                message = await anext(cancellation_iter)
                cancellation_future.set_exception(
                    CancelledByServerError(message.id, message.code, message.message or "")
                )
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
                if not cancellation_future.done():
                    # the exception can originate from the program itself (when the control is given above by `yield`)
                    #     or by failing the TaskGroup which cancels the program. We'll only consider this the "program cancellation",
                    #     when the "Cancelled by user" has no already been set
                    logger.debug("Request cancelled by asyncio.CancelledError", id=message_id)
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
                yield iter
        else:
            yield async_iterator_never()

    async def _iterate_messages[T: _AbstractJsonRpcMessage | _AbstractJsonRpcCancellationMessage](
        self, id: _TMessageId, message_type: type[T], read_queue: asyncio.Queue[TMsg | TCancellationMsg]
    ) -> typing.AsyncGenerator[T]:
        while True:
            message = await read_queue.get()

            if isinstance(message, message_type) and message.id == id:
                yield message

    async def _send_cancellation_message(self, id: _TMessageId, message: str) -> None:
        msg = self._cancellation_message_type.create(id, 0, message)
        await self._writer.write(msg)
