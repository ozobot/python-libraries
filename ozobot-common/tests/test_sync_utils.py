import asyncio
import contextlib
import typing
from asyncio.queues import QueueEmpty
from unittest.mock import patch

import pytest
import pytest_asyncio
from ozobot.common.sync import as_sync, as_sync_context_manager


@pytest_asyncio.fixture(scope="function")
async def patched_runner() -> typing.AsyncIterator[None]:
    """This patches the singleton runner for each test. Otherwise we'd get 'loop closed' errors (pytest-asyncio closes the loop)"""
    with patch("ozobot.common.sync._runner", asyncio.Runner()):
        yield


def test_async_function(patched_runner) -> None:
    q = asyncio.Queue[str]()

    @as_sync
    async def test_function():
        await q.put("boo!")

    test_function()

    assert q.get_nowait() == "boo!"


async def test_async_function_from_async_context(patched_runner) -> None:
    q = asyncio.Queue[str]()

    @as_sync
    async def test_function():
        await q.put("boo!")

    with pytest.raises(RuntimeError):
        test_function()

    assert q.empty()


def test_async_context_manager(patched_runner) -> None:
    q = asyncio.Queue[str]()

    @contextlib.asynccontextmanager
    async def ctx() -> typing.AsyncIterator[None]:
        await q.put("hi")
        yield
        await q.put("bye")

    with as_sync_context_manager(ctx()):
        assert q.get_nowait() == "hi"
        with pytest.raises(QueueEmpty):
            _ = q.get_nowait()

    assert q.get_nowait() == "bye"


async def test_async_context_manager_from_async_context(patched_runner) -> None:
    q = asyncio.Queue[str]()

    @contextlib.asynccontextmanager
    async def ctx() -> typing.AsyncIterator[None]:
        await q.put("hi")
        yield
        await q.put("bye")

    with pytest.raises(RuntimeError):
        with as_sync_context_manager(ctx()):
            pass

    assert q.empty()
