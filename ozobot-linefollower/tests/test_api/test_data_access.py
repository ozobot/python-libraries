import asyncio
import typing
from dataclasses import dataclass

import pytest
from ozobot.linefollower.api.data_access import (
    DataWatcherProxy,
    EventWatcher,
    EventWatcherQueue,
    WatcherOutputContainerRunner,
)
from ozobot.linefollower.datatypes import Sample


class _ReadableEventWatcher[T](EventWatcher[Sample[T]]):
    async def read(self) -> T:
        return self._queue.last.value


async def _aqueue_to_aiter[T](q: asyncio.Queue[T]) -> typing.AsyncGenerator[T]:
    while True:
        try:
            yield await q.get()
        except asyncio.QueueShutDown:
            return


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

    async with proxy_int.watch() as container_int, proxy_str.watch() as container_str:
        it_int = aiter(container_int)
        it_str = aiter(container_str)

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


async def test_watcher_container_aiter(subtests: pytest.Subtests) -> None:
    q = asyncio.Queue[int]()
    for d in range(3):
        await q.put(d)

    async with WatcherOutputContainerRunner[int]() as r:
        await r.start(_aqueue_to_aiter(q))
        with subtests.test("Iterate on present data"):
            it = aiter(r.output_container)
            assert [await anext(it) for _ in range(3)] == list(range(3))

        with subtests.test("Reiterate on present data"):
            it2 = aiter(r.output_container)
            assert [await anext(it2) for _ in range(3)] == list(range(3))

        with subtests.test("Continue iteration and wait for new data"):
            coro = typing.cast(
                typing.Coroutine[None, None, int],  # we need to cast anext -> Awaitable to be accepted by create_task
                anext(it),
            )
            task = asyncio.create_task(coro)
            await asyncio.sleep(0.1)
            await q.put(3)
            assert await task == 3

        q.shutdown()  # simulate watcher closing

    with subtests.test("Continue iteration after closing"):
        assert await anext(it2) == 3


async def test_watcher_container_collect(subtests: pytest.Subtests) -> None:
    q = asyncio.Queue[int]()
    for d in range(3):
        await q.put(d)

    async with WatcherOutputContainerRunner[int]() as r:
        await r.start(_aqueue_to_aiter(q))
        with subtests.test("Collect present data"):
            await asyncio.sleep(0.1)
            assert r.output_container.collect() == list(range(3))

        with subtests.test("Collect after update"):
            await q.put(3)
            await asyncio.sleep(0.1)
            assert r.output_container.collect() == list(range(4))

        q.shutdown()  # simulate watcher closing

    with subtests.test("Collect after closing"):
        assert r.output_container.collect() == list(range(4))


async def test_watcher_container_collect_flush_on_close(subtests: pytest.Subtests) -> None:
    q = asyncio.Queue[int]()
    for d in range(3):
        await q.put(d)

    async with WatcherOutputContainerRunner[int]() as r:
        await r.start(_aqueue_to_aiter(q))
        q.shutdown()  # simulate watcher closing

    assert r.output_container.collect() == list(range(3))
