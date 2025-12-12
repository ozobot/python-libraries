from unittest.mock import patch

from ozobot.ora.datatypes import Cartesian, Frame, Joints, Tool, ToolCollider, ToolType
from ozobot.ora.drivers.browser import OraWebDriver
from ozobot.ora.units import quantities, units

_CORO_MODULE_PATH = "ozobot.ora.drivers.browser._rpcCoroutine"


async def test_get_tool():
    return_value = {
        "endToolType": "noTool",
        "tcp": [0, 1, 2, 3, 4, 5],
        "centerOfGravity": [10, 20, 30],
        "weight": 100,
        "collisionModelType": 1,
    }

    with patch(_CORO_MODULE_PATH, return_value=return_value) as rpc:
        driver = OraWebDriver()
        frame = await driver.get_tool()
        rpc.assert_awaited_once_with("ora.listener", "getToolParameters", [])
        assert frame == Tool(
            type=ToolType.NO_TOOL,
            tcp=Frame(
                units(0, quantities.mm),
                units(1, quantities.mm),
                units(2, quantities.mm),
                units(5, quantities.deg),
                units(4, quantities.deg),
                units(3, quantities.deg),
            ),
            center_of_gravity=(units(10, quantities.mm), units(20, quantities.mm), units(30, quantities.mm)),
            weight=units(100, quantities.kg),
            collider=ToolCollider(1),
        )


async def test_get_frame():
    with patch(_CORO_MODULE_PATH, return_value=[0, 1, 2, 3, 4, 5]) as rpc:
        driver = OraWebDriver()
        frame = await driver.get_frame()
        rpc.assert_awaited_once_with("ora.listener", "getFrame", [])
        assert frame == Frame(
            units(0, quantities.mm),
            units(1, quantities.mm),
            units(2, quantities.mm),
            units(5, quantities.deg),
            units(4, quantities.deg),
            units(3, quantities.deg),
        )


async def test_get_pose():
    with patch(_CORO_MODULE_PATH, return_value=[0, 1, 2, 3, 4, 5]) as rpc:
        driver = OraWebDriver()
        frame = await driver.get_pose()
        rpc.assert_awaited_once_with("ora.listener", "getPose", [])
        assert frame == Cartesian(
            units(0, quantities.mm),
            units(1, quantities.mm),
            units(2, quantities.mm),
            units(5, quantities.deg),
            units(4, quantities.deg),
            units(3, quantities.deg),
        )


async def test_get_joints():
    with patch(_CORO_MODULE_PATH, return_value=[0, 1, 2, 3, 4, 5]) as rpc:
        driver = OraWebDriver()
        frame = await driver.get_joints()
        rpc.assert_awaited_once_with("ora.listener", "getJointPose", [])
        assert frame == Joints(
            units(0, quantities.deg),
            units(1, quantities.deg),
            units(2, quantities.deg),
            units(3, quantities.deg),
            units(4, quantities.deg),
            units(5, quantities.deg),
        )
