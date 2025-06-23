import contextlib
from unittest.mock import Mock

from ozobot.evo.api.data_access import DataWatcher, FakeDataWatcher, FakeDataWatcherQueue
from ozobot.evo.api.sync import SyncWatcher
from ozobot.evo.datatypes import Sample
from ozobot.evo.protocol import Types


@contextlib.asynccontextmanager
async def _watcher_subs_iter():
    async def _iter():
        yield Types.Battery(1, 2, 3, 100)
        yield Types.Battery(10, 20, 30, 1000)

    yield _iter()


def test_sync_watcher_last() -> None:
    subs_mock = Mock(last=Types.Battery(1, 2, 3, 100))
    watcher = DataWatcher[Types.Battery, int](subs_mock, lambda b: b.voltage)
    sync_watcher = SyncWatcher(watcher)

    assert isinstance(sync_watcher.last, Sample)
    assert sync_watcher.last.data == 1


def test_fake_watcher_sync_watcher_last() -> None:
    q = FakeDataWatcherQueue(Sample(1, 0))
    watcher = FakeDataWatcher[int](q)
    sync_watcher = SyncWatcher(watcher)

    assert isinstance(sync_watcher.last, Sample)
    assert sync_watcher.last.data == 1
