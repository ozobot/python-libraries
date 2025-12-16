import asyncio
import contextlib
import typing
from asyncio.queues import QueueEmpty

import pytest
from ozobot.common.sync import as_sync, as_sync_context_manager


@pytest.mark.asyncio(loop_scope="module")
def test_async_function() -> None:
    q = asyncio.Queue[str]()

    @as_sync
    async def test_function():
        await q.put("boo!")

    test_function()

    assert q.get_nowait() == "boo!"


@pytest.mark.asyncio(loop_scope="module")
async def test_async_function_from_async_context() -> None:
    q = asyncio.Queue[str]()

    @as_sync
    async def test_function():
        await q.put("boo!")

    with pytest.raises(RuntimeError):
        test_function()

    assert q.empty()


@pytest.mark.asyncio(loop_scope="module")
def test_async_context_manager() -> None:
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


@pytest.mark.asyncio(loop_scope="module")
async def test_async_context_manager_from_async_context() -> None:
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
