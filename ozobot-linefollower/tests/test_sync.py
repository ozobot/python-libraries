import datetime
from unittest.mock import sentinel

from ozobot.linefollower.api.sync import SyncDataAccessRead
from ozobot.linefollower.datatypes import Sample


class _ReadableRegion:
    async def read(self) -> Sample[int]:
        return Sample(sentinel.value1, 0)


def test_data_read() -> None:
    sync_watcher = SyncDataAccessRead(_ReadableRegion())

    sample = sync_watcher.read()
    assert isinstance(sample, Sample)
    assert sample.data == sentinel.value1
    assert sample.timestamp == datetime.datetime.fromtimestamp(0)
