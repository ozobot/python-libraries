from unittest.mock import patch

from ozobot.ora.datatypes import Cartesian, Joints, ReferenceFrameModifier
from ozobot.ora.driver.web import OraWebDriver
from ozobot.ora.units import quantities, units

_CORO_MODULE_PATH = "ozobot.ora.driver.web._rpcCoroutine"


async def test_move_linear():
    pose = Cartesian(
        units(0, quantities.mm),
        units(1, quantities.mm),
        units(2, quantities.mm),
        units(3, quantities.deg),
        units(4, quantities.deg),
        units(5, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.move_linear(pose, ReferenceFrameModifier.ABSOLUTE)
        rpc.assert_awaited_with(
            "ora",
            "moveLinear",
            [
                (0, 1, 2),
                (5, 4, 3),
                "global",
                100,
                2000,
                7000,
            ],
        )

        await driver.move_linear(pose, ReferenceFrameModifier.RELATIVE)
        rpc.assert_awaited_with(
            "ora",
            "moveLinear",
            [
                (0, 1, 2),
                (5, 4, 3),
                "relative",
                100,
                2000,
                7000,
            ],
        )

        await driver.move_linear(pose, ReferenceFrameModifier.TOOL)
        rpc.assert_awaited_with(
            "ora",
            "moveLinear",
            [
                (0, 1, 2),
                (5, 4, 3),
                "tool",
                100,
                2000,
                7000,
            ],
        )

        await driver.move_linear(
            pose,
            ReferenceFrameModifier.ABSOLUTE,
            speed=units(10, quantities.mm / quantities.s),
            acceleration=units(20, quantities.mm / quantities.s**2),
            jerk=units(30, quantities.mm / quantities.s**3),
        )
        rpc.assert_awaited_with(
            "ora",
            "moveLinear",
            [
                (0, 1, 2),
                (5, 4, 3),
                "global",
                10,
                20,
                30,
            ],
        )


async def test_move_joints_joint_pose():
    pose = Joints(
        units(00, quantities.deg),
        units(10, quantities.deg),
        units(20, quantities.deg),
        units(30, quantities.deg),
        units(40, quantities.deg),
        units(50, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.move_joints(pose)
        rpc.assert_awaited_with(
            "ora",
            "moveJoint",
            [
                (00, 10, 20, 30, 40, 50),
                20,
                500,
                11459,
            ],
        )

        await driver.move_joints(
            pose,
            speed=units(10, quantities.percent),
            acceleration=units(20, quantities.deg / quantities.s**2),
            jerk=units(30, quantities.deg / quantities.s**3),
        )
        rpc.assert_awaited_with(
            "ora",
            "moveJoint",
            [
                (00, 10, 20, 30, 40, 50),
                18,
                20,
                30,
            ],
        )


async def test_move_joints_cartesian_pose():
    pose = Cartesian(
        units(00, quantities.mm),
        units(10, quantities.mm),
        units(20, quantities.mm),
        units(30, quantities.deg),
        units(40, quantities.deg),
        units(50, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.move_joints(
            pose,
            speed=units(10, quantities.percent),
            acceleration=units(20, quantities.deg / quantities.s**2),
            jerk=units(30, quantities.deg / quantities.s**3),
        )
        rpc.assert_awaited_with(
            "ora",
            "moveJointToCartesian",
            [
                (0, 10, 20, 50, 40, 30),
                18,
                20,
                30,
            ],
        )


async def test_move_circ():
    pose1 = Cartesian(
        units(0, quantities.mm),
        units(10, quantities.mm),
        units(20, quantities.mm),
        units(30, quantities.deg),
        units(40, quantities.deg),
        units(50, quantities.deg),
    )

    pose2 = Cartesian(
        units(100, quantities.mm),
        units(200, quantities.mm),
        units(300, quantities.mm),
        units(400, quantities.deg),
        units(500, quantities.deg),
        units(600, quantities.deg),
    )

    with patch(_CORO_MODULE_PATH) as rpc:
        driver = OraWebDriver()
        await driver.move_circle(
            pose1,
            pose2,
            arc_angle=units(90, quantities.deg),
            speed=units(10, quantities.percent),
            acceleration=units(20, quantities.deg / quantities.s**2),
            jerk=units(30, quantities.deg / quantities.s**3),
        )
        rpc.assert_awaited_with(
            "ora",
            "moveCircle",
            [
                (0, 10, 20, 50, 40, 30),
                (100, 200, 300, 600, 500, 400),
                90,
                10,
                20,
                30,
            ],
        )
