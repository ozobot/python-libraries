import asyncio
import datetime
import typing
from unittest.mock import patch, sentinel

import pytest_asyncio
from ozobot.linefollower.api.sync import SyncDataAccessRead
from ozobot.linefollower.datatypes import Sample


@pytest_asyncio.fixture(scope="function")
async def patched_runner() -> typing.AsyncIterator[None]:
    """This patches the singleton runner for each test. Otherwise we'd get 'loop closed' errors (pytest-asyncio closes the loop)"""
    with patch("ozobot.common.sync._runner", asyncio.Runner()):
        yield


class _ReadableRegion:
    async def read(self) -> Sample[int]:
        return Sample(sentinel.value1, 0)


def test_data_read(patched_runner) -> None:
    sync_watcher = SyncDataAccessRead(_ReadableRegion())

    sample = sync_watcher.read()
    assert isinstance(sample, Sample)
    assert sample.value == sentinel.value1
    assert sample.timestamp == datetime.datetime.fromtimestamp(0)
