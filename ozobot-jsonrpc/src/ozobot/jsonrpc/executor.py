from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass

from ozobot.common.asyncutils import CancellableTaskGroup, async_iterator_never
from ozobot.common.broadcast import BroadcastManager
from ozobot.common.logging import logger
from ozobot.jsonrpc.exceptions import CancelledByClientError, CancelledByServerError, JsonRpcError

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


class _AbstractJsonRpcErrorDetail(typing.Protocol):
    @property
    def code(self) -> int: ...

    @property
    def message(self) -> str: ...


class _AbstractJsonRpcErrorMessage(_AbstractJsonRpcMessage, typing.Protocol):
    @property
    def error(self) -> _AbstractJsonRpcErrorDetail: ...


class _MessageReader[T: _AbstractJsonRpcMessage](typing.Protocol):
    def read(self) -> typing.AsyncIterator[T]: ...


class _MessageWriter[T: _AbstractJsonRpcMessage](typing.Protocol):
    async def write(self, data: T) -> None: ...


class _MessageReaderWriter[T: _AbstractJsonRpcMessage](_MessageReader[T], _MessageWriter[T], typing.Protocol): ...


_TRequest_co = typing.TypeVar("_TRequest_co", bound=_AbstractJsonRpcMessage, covariant=True)
_TResponse_co = typing.TypeVar("_TResponse_co", bound=_AbstractJsonRpcMessage, covariant=True)
_TNotification_co = typing.TypeVar("_TNotification_co", bound=_AbstractJsonRpcMessage, covariant=True)


class Method(typing.Generic[_TRequest_co, _TResponse_co, _TNotification_co]):
    def __init__(
        self,
        request: type[_TRequest_co],
        response: type[_TResponse_co] | None,
        notification: type[_TNotification_co] | None,
    ) -> None:
        self.request = request
        self.response = response
        self.notification = notification

    @classmethod
    def without_response(
        cls, request: type[_TRequest_co], notification: type[_TNotification_co]
    ) -> Method[_TRequest_co, typing.Never, _TNotification_co]:
        return Method(request, None, notification)

    @classmethod
    def without_notifications(
        cls, request: type[_TRequest_co], response: type[_TResponse_co]
    ) -> Method[_TRequest_co, _TResponse_co, typing.Never]:
        return Method(request, response, None)


@dataclass(frozen=True, kw_only=True)
class _ExecutorQuery[TResponse, TNotification]:
    _response: typing.AsyncIterator[TResponse]
    notifications: typing.AsyncIterator[TNotification]
    cancel: typing.Callable[[], None]

    @property
    def response(self) -> typing.Awaitable[TResponse]:
        return anext(self._response)


_TReq_co = typing.TypeVar("_TReq_co", bound=_AbstractJsonRpcMessage, covariant=True)
_TRes_co = typing.TypeVar("_TRes_co", bound=_AbstractJsonRpcMessage, covariant=True)
_TNotif_co = typing.TypeVar("_TNotif_co", bound=_AbstractJsonRpcMessage, covariant=True)


class Query(typing.Generic[_TReq_co, _TRes_co, _TNotif_co]):
    def __init__(self, request: _TReq_co, method: Method[_TReq_co, _TRes_co, _TNotif_co]) -> None:
        self._request = request
        self._method = method


@dataclass(frozen=True)
class Executor[
    TOut: _AbstractJsonRpcMessage,
    TIn: _AbstractJsonRpcMessage,
    TCancellationMsg: _AbstractJsonRpcCancellationMessage,
    TErrorMsg: _AbstractJsonRpcErrorMessage,
]:
    _broadcast: BroadcastManager[TIn | TCancellationMsg | TErrorMsg]
    _writer: _MessageWriter[TOut | TCancellationMsg]
    _cancellation_message_type: type[TCancellationMsg]
    _error_message_type: type[TErrorMsg]

    @classmethod
    @contextlib.asynccontextmanager
    async def create(
        cls,
        transport: _MessageReaderWriter[TIn | TCancellationMsg | TErrorMsg],
        cancellation_message_type: type[TCancellationMsg],
        error_message_type: type[TErrorMsg],
    ) -> typing.AsyncIterator[Executor[TIn, TIn, TCancellationMsg, TErrorMsg]]:
        broadcast = BroadcastManager[TIn | TCancellationMsg | TErrorMsg]()

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
                    yield Executor[TIn, TIn, TCancellationMsg, TErrorMsg](
                        broadcast, transport, cancellation_message_type, error_message_type
                    )
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
    async def execute[TRes: _AbstractJsonRpcMessage, TNotif: _AbstractJsonRpcMessage](
        self, query: Query[TOut, TRes, TNotif]
    ) -> typing.AsyncIterator[_ExecutorQuery[TRes, TNotif]]:
        message_id = query._request.id
        await self._writer.write(query._request)

        async with (
            self._expect_messages(message_id, query._method.response) as response_iter,
            self._expect_messages(message_id, query._method.notification) as notification_iter,
            self._expect_messages(message_id, self._cancellation_message_type) as cancellation_iter,
            self._expect_messages(message_id, self._error_message_type) as error_iter,
        ):
            try:
                async with self._run_executor(
                    response_iter,
                    notification_iter,
                    cancellation_iter,
                    error_iter,
                    message_id,
                ) as query_ctx:
                    yield query_ctx
            except (CancelledByServerError, CancelledByClientError) as err:
                reason = err.args[0]
                if isinstance(err, CancelledByClientError):
                    await self._send_cancellation_message(message_id, reason)
                logger.debug("Request cancelled", id=message_id, reason=reason)
                raise asyncio.CancelledError(reason) from None
            except asyncio.InvalidStateError:
                pass  # this means there was no exception set

    @contextlib.asynccontextmanager
    async def _run_executor[
        TRes: _AbstractJsonRpcMessage,
        TNotif: _AbstractJsonRpcMessage,
    ](
        self,
        response_iter: typing.AsyncIterator[TRes],
        notification_iter: typing.AsyncIterator[TNotif],
        cancellation_iter: typing.AsyncIterator[_AbstractJsonRpcCancellationMessage],
        error_iter: typing.AsyncIterator[TErrorMsg],
        message_id: int,
    ) -> typing.AsyncIterator[_ExecutorQuery[TRes, TNotif]]:
        async with CancellableTaskGroup() as tg:
            cancellation_future = asyncio.Future[None]()

            async def _await_cancellation_from_server() -> None:
                message = await anext(cancellation_iter)
                if not cancellation_future.done():
                    cancellation_future.set_exception(
                        CancelledByServerError(message.id, message.code, message.message or "")
                    )
                tg.cancel()

            async def _await_error_from_server() -> None:
                message = await anext(error_iter)
                if not cancellation_future.done():
                    cancellation_future.set_exception(
                        JsonRpcError(message.id, message.error.code, message.error.message)
                    )
                tg.cancel()

            def _cancel_by_client(reason: str) -> None:
                if not cancellation_future.done():
                    cancellation_future.set_exception(
                        CancelledByClientError(message_id, reason),
                    )
                tg.cancel()

            query_ctx = _ExecutorQuery(
                _response=response_iter,
                notifications=notification_iter,
                cancel=lambda: _cancel_by_client("Cancelled by user"),
            )
            tg.create_task(_await_cancellation_from_server())
            tg.create_task(_await_error_from_server())

            try:
                yield query_ctx
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
    async def _expect_messages[
        T: _AbstractJsonRpcMessage | _AbstractJsonRpcCancellationMessage | _AbstractJsonRpcErrorMessage
    ](self, id: _TMessageId, message_type: type[T] | None) -> typing.AsyncIterator[typing.AsyncGenerator[T]]:
        if message_type:
            with self._broadcast.output() as queue:
                iter = self._iterate_messages(id, message_type, queue)
                yield iter
        else:
            yield async_iterator_never()

    async def _iterate_messages[
        T: _AbstractJsonRpcMessage | _AbstractJsonRpcCancellationMessage | _AbstractJsonRpcErrorMessage
    ](
        self, id: _TMessageId, message_type: type[T], read_queue: asyncio.Queue[TIn | TCancellationMsg | TErrorMsg]
    ) -> typing.AsyncGenerator[T]:
        while True:
            message = await read_queue.get()

            if isinstance(message, message_type) and message.id == id:
                yield message

    async def _send_cancellation_message(self, id: _TMessageId, message: str) -> None:
        msg = self._cancellation_message_type.create(id, 0, message)
        await self._writer.write(msg)
