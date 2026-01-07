import asyncio
import typing
from dataclasses import dataclass

import pytest
from ozobot.linefollower.api.data_access import DataWatcherProxy, EventWatcher, EventWatcherQueue, buffered_iterator
from ozobot.linefollower.datatypes import Sample


class _ReadableEventWatcher[T](EventWatcher[Sample[T]]):
    async def read(self) -> T:
        return self._queue.last.value


async def test_event_watcher() -> None:
    q = EventWatcherQueue(Sample(0, 0))
    w = EventWatcher(q)

    async with w.watch() as reader:
        await q.write(Sample(2, 0))
        async for sample in reader:
            assert sample.value == 2
            break


async def test_watcher_proxy() -> None:
    @dataclass(frozen=True)
    class Data:
        data_int: int
        data_str: str

    source_queue = EventWatcherQueue(Sample(Data(0, ""), 0))
    source = _ReadableEventWatcher(source_queue)

    proxy_int = DataWatcherProxy(source, convert=lambda m: m.data_int)
    proxy_str = DataWatcherProxy(source, convert=lambda m: m.data_str)

    async with proxy_int.watch() as it_int, proxy_str.watch() as it_str:
        await source_queue.write(
            Sample(
                Data(
                    1,
                    "hello",
                ),
                0,
            ),
        )

        await source_queue.write(
            Sample(
                Data(
                    2,
                    "world",
                ),
                0,
            ),
        )

        assert (await anext(it_int)) == 1
        assert (await anext(it_int)) == 2

        assert (await anext(it_str)) == "hello"
        assert (await anext(it_str)) == "world"


async def test_buffered_iterator_finite(subtests: pytest.Subtests) -> None:
    """Test if a finite iterator gets exhausted"""

    async def _it() -> typing.AsyncIterator[int]:
        for i in range(4):
            yield i

    with subtests.test(msg="Close after exhauston"):
        async with buffered_iterator(_it()) as buffered_it:
            assert [v async for v in buffered_it] == list(range(4))

    with subtests.test(msg="Close before exhaustion"):
        async with buffered_iterator(_it()) as buffered_it:
            await asyncio.sleep(0.1)  # let the background task process the messages
        assert [v async for v in buffered_it] == list(range(4))


async def test_buffered_iterator_infinite() -> None:
    """Test if an infinite iterator does not block"""

    async def _it() -> typing.AsyncIterator[int]:
        yield 0
        yield 1
        await asyncio.Future()  # block forever to simulate infinite iterator

    async with buffered_iterator(_it()) as buffered_it:
        await asyncio.sleep(0.1)  # let the background task process the messages
    assert [v async for v in buffered_it] == list(range(2))
