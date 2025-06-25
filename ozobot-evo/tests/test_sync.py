from unittest.mock import AsyncMock, Mock, sentinel

from ozobot.evo.api.data_access import DataAccessRead, DataWatcher, FakeDataWatcher, FakeDataWatcherQueue
from ozobot.evo.api.sync import SyncDataAccessRead
from ozobot.evo.datatypes import Sample
from ozobot.evo.protocol import Types


def test_data_reader_read() -> None:
    subs_mock = Mock(mem_read=AsyncMock(return_value=Types.Battery(1, 2, 3, 100)))
    watcher = DataAccessRead[Types.Battery, int](subs_mock, sentinel.watcher, lambda b: b.voltage)
    sync_watcher = SyncDataAccessRead(watcher)

    sample = sync_watcher.read()
    assert isinstance(sample, Sample)
    assert sample.data == 1


def test_sync_watcher_read() -> None:
    driver_mock = Mock(mem_read=AsyncMock(return_value=Types.Battery(1, 2, 3, 100)))
    watcher = DataWatcher[Types.Battery, int](driver_mock, sentinel.property, sentinel.watcher, lambda b: b.voltage)
    sync_watcher = SyncDataAccessRead(watcher)

    sample = sync_watcher.read()
    assert isinstance(sample, Sample)
    assert sample.data == 1


def test_fake_watcher_read() -> None:
    q = FakeDataWatcherQueue(Sample(1, 0))
    watcher = FakeDataWatcher[int](q)
    sync_watcher = SyncDataAccessRead(watcher)

    sample = sync_watcher.read()
    assert isinstance(sample, Sample)
    assert sample.data == 1
