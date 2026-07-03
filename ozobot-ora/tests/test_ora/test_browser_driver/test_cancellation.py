import asyncio
from unittest.mock import patch

import pytest
from ozobot.ora.datatypes import Cartesian
from ozobot.ora.driver.web import OraWebDriver
from ozobot.ora.exceptions import CancellationCausedUndefinedState, CancellationNotSupported
from ozobot.ora.units import quantities, units

_CORO_MODULE_PATH = "ozobot.ora.driver.web._rpcCoroutine"


async def test_no_cancellation():
    pose = Cartesian(
        units(0, quantities.mm),
        units(1, quantities.mm),
        units(2, quantities.mm),
        units(3, quantities.deg),
        units(4, quantities.deg),
        units(5, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        rpc.return_value = None
        driver = OraWebDriver()

        assert driver._cancelled_undefined_state is False

        await driver.move_linear(pose)

        assert driver._cancelled_undefined_state is False


async def test_cancellation():
    pose = Cartesian(
        units(0, quantities.mm),
        units(1, quantities.mm),
        units(2, quantities.mm),
        units(3, quantities.deg),
        units(4, quantities.deg),
        units(5, quantities.deg),
    )

    async def raise_cancelled(*args, **kwargs):
        raise asyncio.CancelledError()

    with patch(_CORO_MODULE_PATH) as rpc:
        rpc.side_effect = raise_cancelled
        driver = OraWebDriver()

        assert driver._cancelled_undefined_state is False

        with pytest.raises(CancellationNotSupported):
            await driver.move_linear(pose)

        assert driver._cancelled_undefined_state is True


async def test_reuse_after_cancellation():
    pose = Cartesian(
        units(0, quantities.mm),
        units(1, quantities.mm),
        units(2, quantities.mm),
        units(3, quantities.deg),
        units(4, quantities.deg),
        units(5, quantities.deg),
    )

    async def raise_cancelled(*args, **kwargs):
        raise asyncio.CancelledError()

    with patch(_CORO_MODULE_PATH) as rpc:
        rpc.side_effect = raise_cancelled
        driver = OraWebDriver()

        with pytest.raises(CancellationNotSupported):
            await driver.move_linear(pose)

        assert driver._cancelled_undefined_state is True

    with patch(_CORO_MODULE_PATH) as rpc:
        rpc.return_value = None
        with pytest.raises(CancellationCausedUndefinedState):
            await driver.move_linear(pose)
