from ozobot.common.asyncutils import CancellableTaskGroup
import asyncio
import typing

import pytest
from ozobot.common.asyncutils import async_iterator_never


async def _infinite():
    await asyncio.Future()


async def test_async_iterator_never() -> None:
    it = async_iterator_never()

    typing.assert_type(it, typing.AsyncGenerator[typing.Never])

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(0.1):
            await anext(it)


async def test_cancellable_task_group_cancel() -> None:
    with pytest.raises(asyncio.CancelledError):
        async with CancellableTaskGroup() as tg:
            tg.create_task(_infinite())
            tg.cancel()


async def test_cancellable_task_group_quiet_cancel() -> None:
    async with CancellableTaskGroup() as tg:
        tg.create_task(_infinite())
        tg.cancel_quietly()
