from dataclasses import dataclass

from ozobot.linefollower.api.data_access import DataWatcherProxy, EventWatcher, EventWatcherQueue
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

        assert (await anext(it_int)).value == 1
        assert (await anext(it_int)).value == 2

        assert (await anext(it_str)).value == "hello"
        assert (await anext(it_str)).value == "world"
