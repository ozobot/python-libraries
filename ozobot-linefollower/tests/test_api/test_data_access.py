from ozobot.linefollower.api.data_access import EventWatcher, EventWatcherQueue
from ozobot.linefollower.datatypes import Sample


async def test_event_watcher() -> None:
    q = EventWatcherQueue[int](Sample(0, 0))
    w = EventWatcher[int](q)

    assert (await w.read()).data == 0
    await q.write(Sample(1, 0))
    assert (await w.read()).data == 1

    async with w.watch() as reader:
        await q.write(Sample(2, 0))
        async for sample in reader:
            assert sample.data == 2
            break
