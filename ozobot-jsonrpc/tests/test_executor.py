from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass, field
from unittest.mock import Mock

import pytest
from ozobot.jsonrpc.executor import Executor, Method
from ozobot.jsonrpc.stream import Reader, Writer


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


def _get_mock_reader[T](queue: asyncio.Queue[T]) -> Reader:
    async def _read():
        while True:
            yield await queue.get()

    return Mock(spec=Reader, read=_read)


def _get_mock_writer[T](queue: asyncio.Queue[T]) -> Writer:
    return Mock(spec=Writer, write=queue.put)


async def test_executor_types() -> None:
    reader = _get_mock_reader(asyncio.Queue())
    writer = _get_mock_writer(asyncio.Queue())

    async with Executor.create(reader, writer, _Cancel) as executor:
        async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
            typing.assert_type(execution.response, typing.Awaitable[_ResponseA])
            typing.assert_type(execution.notifications, typing.AsyncIterator[_NotificationA])


async def test_executor_types_no_response() -> None:
    reader = _get_mock_reader(asyncio.Queue())
    writer = _get_mock_writer(asyncio.Queue())

    async with Executor.create(reader, writer, _Cancel) as executor:
        async with executor.execute(_RequestB(id=1, data="hello world"), _method_b) as execution:
            typing.assert_type(execution.response, typing.Awaitable[_ResponseB])
            typing.assert_type(execution.notifications, typing.AsyncIterator[typing.Never])


async def test_executor_types_no_notification() -> None:
    reader = _get_mock_reader(asyncio.Queue())
    writer = _get_mock_writer(asyncio.Queue())

    async with Executor.create(reader, writer, _Cancel) as executor:
        async with executor.execute(_RequestC(id=1, data="hello world"), _method_c) as execution:
            typing.assert_type(execution.response, typing.Awaitable[typing.Never])
            typing.assert_type(execution.notifications, typing.AsyncIterator[_NotificationC])


async def test_executor_rpc() -> None:
    read_queue = asyncio.Queue[_Message]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    async with Executor.create(reader, writer, _Cancel) as executor:
        async with executor.execute(_RequestA(id=2, data="hello world"), _method_a) as execution:
            assert await write_queue.get() == _RequestA(id=2, data="hello world")

            await read_queue.put(_ResponseB(id=1, data="other request"))
            await read_queue.put(_ResponseA(id=2, data="hi there"))
            async with asyncio.timeout(0.1):
                assert await execution.response == _ResponseA(id=2, data="hi there")

            with pytest.raises(asyncio.TimeoutError):
                async with asyncio.timeout(0.1):
                    await anext(execution.notifications)


async def test_executor_notifications() -> None:
    read_queue = asyncio.Queue[_Message]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    async with Executor.create(reader, writer, _Cancel) as executor:
        async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
            assert await write_queue.get() == _RequestA(id=1, data="hello world")

            await read_queue.put(_NotificationA(id=1, data="hi there"))
            await read_queue.put(_NotificationC(id=2, data="other request"))
            await read_queue.put(_NotificationA(id=1, data="hello there"))

            notification_messages = [await anext(execution.notifications) for _ in range(2)]
            assert notification_messages == [
                _NotificationA(id=1, data="hi there"),
                _NotificationA(id=1, data="hello there"),
            ]

            with pytest.raises(asyncio.TimeoutError):
                async with asyncio.timeout(0.1):
                    await execution.response


async def test_executor_cancellation_explicit_by_client() -> None:
    read_queue = asyncio.Queue[_Message]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                execution.cancel()
                await asyncio.Future()

        assert await write_queue.get() == _Cancel(
            id=1, code=0, message="Request cancelled by client: Cancelled by user (request 1)"
        )


async def test_executor_cancellation_on_program_cancellation_by_client() -> None:
    read_queue = asyncio.Queue[_Message]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    with contextlib.suppress(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as _:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                raise asyncio.CancelledError()

    assert await write_queue.get() == _Cancel(
        id=1, code=0, message="Request cancelled by client: Program cancellation (request 1)"
    )


async def test_executor_cancellation_on_error_by_client() -> None:
    read_queue = asyncio.Queue[_Message]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    with contextlib.suppress(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as _:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                raise Exception("Some generic exception")

    assert await write_queue.get() == _Cancel(
        id=1, code=0, message="Request cancelled by client: General failure (request 1)"
    )


async def test_executor_cancellation_by_server() -> None:
    read_queue = asyncio.Queue[_Message | _Cancel]()
    write_queue = asyncio.Queue[_Message]()
    reader = _get_mock_reader(read_queue)
    writer = _get_mock_writer(write_queue)

    # when awaiting the response
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                await read_queue.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await execution.response

    # when awaiting notifications
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                await read_queue.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await anext(execution.notifications)

    # when not awaiting anything
    with pytest.raises(asyncio.CancelledError):
        async with Executor.create(reader, writer, _Cancel) as executor:
            async with executor.execute(_RequestA(id=1, data="hello world"), _method_a) as execution:
                assert await write_queue.get() == _RequestA(id=1, data="hello world")
                await read_queue.put(_Cancel(id=1, code=0, message="Canceled by test"))
                await asyncio.Future()  # wait for the cancellation message to process
