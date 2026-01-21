import asyncio
from unittest.mock import AsyncMock, call

from ozobot.evo.api.core import Evo


async def test_set_velocity() -> None:
    driver = AsyncMock()
    lf = Evo(driver)
    await lf.set_velocity(100, 0, 1)

    driver.velocity.assert_awaited_once_with(100, 0, 1000)


async def test_set_velocity_override() -> None:
    """Test the behavior of `set_velocity` when overridden by another call of `set_velocity`"""

    fut1 = asyncio.Future[None]()
    fut2 = asyncio.Future[None]()

    futs = iter([fut1, fut2])

    async def _await_next_fut(*args):
        fut = next(futs)
        await fut

    driver = AsyncMock()
    driver.velocity.side_effect = _await_next_fut
    lf = Evo(driver)

    async with asyncio.TaskGroup() as tg:
        call1 = tg.create_task(lf.set_velocity(100, 0, -1))
        await asyncio.sleep(0.1)  # let it boil

        call2 = tg.create_task(lf.set_velocity(200, 0, -1))
        await asyncio.sleep(0.1)  # let it boil

        assert fut1.cancelled()

        # call1 has ended now
        assert call1.done()
        await call1

        # let's finish the other call
        assert not call2.done()
        fut2.set_result(None)
        await call2

    driver.velocity.assert_has_calls(
        [
            call(100, 0, -1000),
            call(200, 0, -1000),
        ]
    )
