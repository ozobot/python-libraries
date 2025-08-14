import asyncio
import typing

import pytest
from ozobot.webrtc.exceptions import QueueReaderConcurrentUseNotSupportedError, QueueReaderNotEnteredError
from ozobot.webrtc.utils import QueueReader


async def test_queue_wait_repeatedly() -> None:
    queue = asyncio.Queue[int]()
    expected_results = [1234, 2345, 3456]

    actual_results = []

    async def _waiter() -> list[int]:
        async with QueueReader[int](queue) as reader:
            async for result in reader.items():
                actual_results.append(result)
                if len(actual_results) == len(expected_results):
                    return actual_results

        return []

    async def _emitter() -> None:
        for val in expected_results:
            await queue.put(val)

    results = await asyncio.gather(_waiter(), _emitter())

    assert results[0] == expected_results
    assert results[1] is None


async def test_queue_wait_for_repeatedly_no_args() -> None:
    queue = asyncio.Queue[None]()
    expected_results = [None, None, None]

    actual_results: list[int | None] = []

    async def _waiter() -> list[int | None]:
        async with QueueReader[None](queue) as reader:
            async for result in reader.items():
                actual_results.append(result)
                if len(actual_results) == len(expected_results):
                    return actual_results
        return []

    async def _emitter() -> None:
        for val in expected_results:
            await queue.put(val)

    results = await asyncio.gather(_waiter(), _emitter())

    assert results[0] == expected_results
    assert results[1] is None


async def test_queue_wait_until() -> None:
    def _condition(e: typing.Any) -> typing.TypeGuard[int]:
        return int(e) > 5

    queue = asyncio.Queue[int]()
    async with QueueReader[int](queue) as reader:
        with pytest.raises(asyncio.TimeoutError):
            async with asyncio.timeout(0.01), asyncio.TaskGroup() as tg:
                _ = tg.create_task(reader.wait_until(_condition))
                await queue.put(2)

        async with asyncio.TaskGroup() as tg:
            t = tg.create_task(reader.wait_until(_condition))
            await asyncio.sleep(0.01)
            await queue.put(10)

            result = await t

            assert result == 10


async def test_queue_context_manager() -> None:
    queue = asyncio.Queue[int]()
    listener = QueueReader[int](queue)

    def _condition(x: typing.Any) -> typing.TypeGuard[int]:
        return True

    with pytest.raises(QueueReaderNotEnteredError):
        await anext(listener.items())

    with pytest.raises(QueueReaderNotEnteredError):
        await listener.wait_until(_condition)

    async with listener:
        with pytest.raises(QueueReaderConcurrentUseNotSupportedError):
            async with listener:
                ...
