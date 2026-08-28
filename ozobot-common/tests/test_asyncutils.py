import asyncio
import typing

import pytest
from ozobot.common.asyncutils import BackgroundTask, CancellableTaskGroup, async_iterator_never


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


async def test_background_task_runs_successfully() -> None:
    result = []

    async def _append() -> None:
        result.append(1)

    async with BackgroundTask() as bg:
        bg.start(_append())
        await asyncio.sleep(0.01)

    assert result == [1]


async def test_background_task_exception_propagated_directly() -> None:
    class CustomError(Exception):
        pass

    async def _raise() -> None:
        raise CustomError("test error")

    with pytest.raises(CustomError, match="test error"):
        async with BackgroundTask() as bg:
            bg.start(_raise())
            await asyncio.sleep(0.01)


async def test_background_task_exception_not_wrapped() -> None:
    class CustomError(Exception):
        pass

    async def _raise() -> None:
        raise CustomError("test error")

    try:
        async with BackgroundTask() as bg:
            bg.start(_raise())
            await asyncio.sleep(0.01)
    except ExceptionGroup:
        pytest.fail("Exception should not be wrapped in ExceptionGroup")
    except CustomError:
        pass


async def test_background_task_cancelled_on_exit() -> None:
    cancelled = False

    async def _long_running() -> None:
        nonlocal cancelled
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled = True
            raise

    async with BackgroundTask() as bg:
        bg.start(_long_running())
        await asyncio.sleep(0.01)

    assert cancelled


async def test_background_task_cancels_base_task_on_failure() -> None:
    class CustomError(Exception):
        pass

    async def _raise_after_delay() -> None:
        await asyncio.sleep(0.01)
        raise CustomError("background failure")

    sleep_interrupted = False

    async def _outer() -> None:
        nonlocal sleep_interrupted
        try:
            async with BackgroundTask() as bg:
                bg.start(_raise_after_delay())
                await asyncio.sleep(10)
        except CustomError:
            sleep_interrupted = True

    task = asyncio.create_task(_outer())
    await asyncio.sleep(0.05)
    await task

    assert sleep_interrupted
