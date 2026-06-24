from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass, field

import pytest
from ozobot.jsonrpc.executor import Executor, Method, Query


@dataclass(frozen=True)
class _Message:
    id: int
    data: str
    jsonrpc: str = field(default="2.0")


@dataclass(frozen=True)
class _Cancel:
    id: int
    code: int
    message: str | None
    jsonrpc: str = field(default="com/ozobot/jsonrpc/2.0/cancellation")

    @classmethod
    def create(cls, id: int, code: int, message: str | None) -> _Cancel:
        return _Cancel(id, code, message)


@dataclass(frozen=True)
class _ErrorDetail:
    code: int
    message: str


@dataclass(frozen=True)
class _Error:
    id: int
    error: _ErrorDetail
    jsonrpc: str = field(default="2.0")


class _RequestA(_Message): ...


class _RequestB(_Message): ...


class _RequestC(_Message): ...


class _ResponseA(_Message): ...


class _ResponseB(_Message): ...


class _NotificationA(_Message): ...


class _NotificationC(_Message): ...


_method_a = Method(_RequestA, _ResponseA, _NotificationA)
_method_b = Method.without_notifications(_RequestB, _ResponseB)
_method_c = Method.without_response(_RequestC, _NotificationC)


class _QueueTransport:
    def __init__(
        self,
        to_transport: asyncio.Queue[_Message | _Cancel | _Error],
        from_transport: asyncio.Queue[_Message | _Cancel | _Error],
    ) -> None:
        self._read_queue = to_transport
        self._write_queue = from_transport

    async def read(self) -> typing.AsyncIterator[_Message | _Cancel | _Error]:
        while True:
            yield await self._read_queue.get()

    async def write(self, data: _Message | _Cancel | _Error) -> None:
        await self._write_queue.put(data)


async def test_executor_types() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    async with Executor[_Message, _Cancel, _Error].create(transport, _Cancel, _Error) as executor:
        async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
            resp = execution.response
            typing.assert_type(resp, typing.Awaitable[_ResponseA])
            typing.assert_type(execution.notifications, typing.AsyncIterator[_NotificationA])

            # silence "not awaited warning"
            resp.close()  # type: ignore


async def test_executor_types_no_response() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    async with Executor.create(transport, _Cancel, _Error) as executor:
        async with Query(_RequestB(id=1, data="hello world"), _method_b).execute(executor) as execution:  # type: ignore[arg-type]
            resp = execution.response
            typing.assert_type(resp, typing.Awaitable[_ResponseB])
            typing.assert_type(execution.notifications, typing.AsyncIterator[typing.Never])

            # silence "not awaited warning"
            resp.close()  # type: ignore


async def test_executor_types_no_notification() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    async with Executor.create(transport, _Cancel, _Error) as executor:
        async with Query(_RequestC(id=1, data="hello world"), _method_c).execute(executor) as execution:  # type: ignore[arg-type]
            resp = execution.response
            typing.assert_type(resp, typing.Awaitable[typing.Never])
            typing.assert_type(execution.notifications, typing.AsyncIterator[_NotificationC])

            # silence "not awaited warning"
            resp.close()  # type: ignore


async def test_executor_rpc() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    async with Executor.create(transport, _Cancel, _Error) as executor:
        async with Query(_RequestA(id=2, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
            assert await from_transport.get() == _RequestA(id=2, data="hello world")

            await to_transport.put(_ResponseB(id=1, data="other request"))
            await to_transport.put(_ResponseA(id=2, data="hi there"))
            async with asyncio.timeout(0.1):
                assert await execution.response == _ResponseA(id=2, data="hi there")

            with pytest.raises(asyncio.TimeoutError):
                async with asyncio.timeout(0.1):
                    await anext(execution.notifications)


async def test_executor_notifications() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    async with Executor.create(transport, _Cancel, _Error) as executor:
        async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
            assert await from_transport.get() == _RequestA(id=1, data="hello world")

            await to_transport.put(_NotificationA(id=1, data="hi there"))
            await to_transport.put(_NotificationC(id=2, data="other request"))
            await to_transport.put(_NotificationA(id=1, data="hello there"))

            notification_messages = [await anext(execution.notifications) for _ in range(2)]
            assert notification_messages == [
                _NotificationA(id=1, data="hi there"),
                _NotificationA(id=1, data="hello there"),
            ]

            with pytest.raises(asyncio.TimeoutError):
                async with asyncio.timeout(0.1):
                    await execution.response


async def test_executor_cancellation_explicit_by_client() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                execution.cancel()
                await asyncio.Future()

        assert await from_transport.get() == _Cancel(
            id=1, code=0, message="Request cancelled by client: Cancelled by user (request 1)"
        )


async def test_executor_cancellation_on_program_cancellation_by_client() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    with contextlib.suppress(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as _:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                raise asyncio.CancelledError()

    assert await from_transport.get() == _Cancel(
        id=1, code=0, message="Request cancelled by client: Program cancellation (request 1)"
    )


async def test_executor_cancellation_on_error_by_client() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    with contextlib.suppress(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as _:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                raise Exception("Some generic exception")

    assert await from_transport.get() == _Cancel(
        id=1, code=0, message="Request cancelled by client: General failure (request 1)"
    )


async def test_executor_cancellation_by_server() -> None:
    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    # when awaiting the response
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                await to_transport.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await execution.response

    # when awaiting notifications
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                await to_transport.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await anext(execution.notifications)

    # when not awaiting anything
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                await to_transport.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await asyncio.Future()  # wait for the cancellation message to process


async def test_executor_error_response() -> None:
    from ozobot.jsonrpc.exceptions import JsonRpcError

    to_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    from_transport = asyncio.Queue[_Message | _Cancel | _Error]()
    transport = _QueueTransport(to_transport, from_transport)

    with pytest.raises(JsonRpcError) as exc_info:
        async with Executor.create(transport, _Cancel, _Error) as executor:
            async with Query(_RequestA(id=1, data="hello world"), _method_a).execute(executor) as execution:  # type: ignore[arg-type]
                assert await from_transport.get() == _RequestA(id=1, data="hello world")
                await to_transport.put(_Error(id=1, error=_ErrorDetail(code=-32601, message="Method not found")))
                await execution.response

    assert exc_info.value.id == 1
    assert exc_info.value.code == -32601
    assert exc_info.value.message == "Method not found"
