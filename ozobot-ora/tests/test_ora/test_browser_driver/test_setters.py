from unittest.mock import patch

from ozobot.ora.datatypes import FingerGripperState, Frame, Tool, ToolCollider, ToolType, VacuumGripperState
from ozobot.ora.driver.web import OraWebDriver
from ozobot.ora.units import quantities, units

_CORO_MODULE_PATH = "ozobot.ora.driver.web._rpcCoroutine"


async def test_set_tool():
    tool = Tool(
        type=ToolType.NO_TOOL,
        tcp=Frame(
            units(0, quantities.mm),
            units(1, quantities.mm),
            units(2, quantities.mm),
            units(3, quantities.deg),
            units(4, quantities.deg),
            units(5, quantities.deg),
        ),
        center_of_gravity=(units(10, quantities.mm), units(20, quantities.mm), units(30, quantities.mm)),
        weight=units(100, quantities.kg),
        collider=ToolCollider(1),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_tool(tool)
        rpc.assert_awaited_once_with(
            "ora",
            "setToolParameters",
            [
                {
                    "endToolType": "noTool",
                    "tcp": (0, 1, 2, 5, 4, 3),
                    "centerOfGravity": (10, 20, 30),
                    "weight": 100,
                    "collisionModelType": 1,
                },
            ],
        )


async def test_set_frame():
    frame = Frame(
        units(0, quantities.mm),
        units(1, quantities.mm),
        units(2, quantities.mm),
        units(3, quantities.deg),
        units(4, quantities.deg),
        units(5, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_frame(frame)
        rpc.assert_awaited_once_with(
            "ora",
            "setFrame",
            [
                (0, 1, 2, 5, 4, 3),
            ],
        )


async def test_set_finger_gripper_state():
    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_finger_gripper_state(FingerGripperState.OPEN)
        rpc.assert_awaited_once_with(
            "ora",
            "setFingerGripperState",
            [
                "open",
            ],
        )


async def test_set_vacuum_gripper_state():
    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_vacuum_gripper_state(VacuumGripperState.ON)
        rpc.assert_awaited_once_with(
            "ora",
            "setVacuumGripperState",
            [
                True,
                False,
            ],
        )


async def test_set_defaults_linear():
    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_defaults_linear(
            units(10, quantities.mm / quantities.s),
            units(20, quantities.mm / quantities.s**2),
            units(30, quantities.mm / quantities.s**3),
        )
        rpc.assert_not_awaited()


async def test_set_defaults_joint():
    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.set_defaults_joint(
            units(10, quantities.percent),
            units(20, quantities.deg / quantities.s**2),
            units(30, quantities.deg / quantities.s**3),
        )
        rpc.assert_not_awaited()
