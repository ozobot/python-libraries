import contextlib
import datetime
import typing
from unittest.mock import AsyncMock, Mock, sentinel

from ozobot.evo.api.data_access import DataAccessRead, DataWatcher, FakeDataWatcher, FakeDataWatcherQueue
from ozobot.evo.api.watchers import WatcherSubscription
from ozobot.evo.datatypes import Sample
from ozobot.evo.driver.driver import Driver
from ozobot.evo.protocol import Types


class _Wrapper:
    def __init__(self, val):
        self.val = val


async def test_access_read() -> None:
    driver = AsyncMock(
        spec=Driver,
        mem_read=AsyncMock(
            return_value=Types.Battery(0, 1, 2, 100),
        ),
    )

    r = DataAccessRead(driver, sentinel.property, _Wrapper)
    retval = await r.read()

    assert isinstance(retval, Sample)
    assert isinstance(retval.data, _Wrapper)
    assert retval.data.val == Types.Battery(0, 1, 2, 100)
    assert retval.timestamp == datetime.datetime.fromtimestamp(100)


async def test_fake_data_watcher() -> None:
    q = FakeDataWatcherQueue[int](Sample(0, 0))
    w = FakeDataWatcher[int](q)

    assert w.last.data == 0
    await q.write(Sample(1, 0))
    assert w.last.data == 1

    async with w.watch() as reader:
        await q.write(Sample(2, 0))
        async for sample in reader:
            assert sample.data == 2
            break


async def test_data_watcher() -> None:
    async def _reader():
        yield Types.Battery(1, 0, 0, 0)
        yield Types.Battery(2, 0, 0, 100)
        yield Types.Battery(3, 0, 0, 200)

    @contextlib.asynccontextmanager
    async def _watcher() -> typing.AsyncIterator[typing.AsyncIterator[int]]:
        yield _reader()

    subs = Mock(spec=WatcherSubscription, last=Types.Battery(10, 0, 0, 1000), read=lambda: _watcher())
    w = DataWatcher[Types.Battery, int](subs, lambda b: b.voltage)

    assert w.last == Sample(10, 1000)

    async with w.watch() as reader:
        data = [await anext(reader) for _ in range(3)]

    assert data == [
        Sample(1, 0),
        Sample(2, 100),
        Sample(3, 200),
    ]
