import asyncio
import contextlib
import logging
import typing
from collections.abc import Callable
from typing import Literal

from ozobot.common.sync import as_sync
from ozobot.ora.driver import OraDriver

from .datatypes import (
    Cartesian,
    FingerGripperState,
    Frame,
    IoName,
    IoValue,
    Joints,
    ReferenceFrameModifier,
    Tool,
    ToolCollider,
    ToolType,
    VacuumGripperState,
)
from .queue import TaskQueue
from .units import Value, domains

_logger = logging.getLogger(__name__)

_TIo = typing.TypeVar("_TIo", bool, float)


def _reference_frame_to_literal(modifier: ReferenceFrameModifier) -> Literal["global", "relative", "tool"]:
    if modifier == ReferenceFrameModifier.ABSOLUTE:
        return "global"
    elif modifier == ReferenceFrameModifier.RELATIVE:
        return "relative"
    else:
        return "tool"


def wait(seconds: float) -> None:
    """Wait for the specified number of seconds."""

    # to the `as_sync` wrapping here, so that the function itself
    # has a nice signature for documentation
    @as_sync
    async def _sleep():
        await asyncio.sleep(seconds)

    _sleep()


class OraSync:
    _robot: OraDriver
    _task_queue: TaskQueue

    def __init__(self, robot: OraDriver):
        self._robot = robot
        self._task_queue = TaskQueue(3)

    @as_sync
    async def move_joints(
        self,
        pose: Joints | Cartesian,
        *,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
    ) -> None:
        run = self._task_queue.run_blocking
        _logger.debug("Running joints: pose=%s, radius=%s, runner=%s", pose, run)

        await run(self._robot.move_joints(pose, speed=speed, acceleration=acceleration))

    @as_sync
    async def move_linear(
        self,
        pose: Cartesian,
        *,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        reference: ReferenceFrameModifier = ReferenceFrameModifier.ABSOLUTE,
    ) -> None:
        run = self._task_queue.run_blocking
        _logger.debug("Running linear: pose=%s, radius=%s, runner=%s", pose, run)

        await run(
            self._robot.move_linear(pose, reference_frame_modifier=reference, speed=speed, acceleration=acceleration)
        )

    @as_sync
    async def move_circle(
        self,
        p_aux: Cartesian,
        p_end: Cartesian,
        *,
        arc_angle: Value[domains.AngleDomain],
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
    ) -> None:
        run = self._task_queue.run_blocking
        _logger.debug("Running circ: p_aux=%s, p_end=%s, radius=%s, runner=%s", p_aux, p_end, run)

        await run(self._robot.move_circle(p_aux, p_end, arc_angle=arc_angle, speed=speed, acceleration=acceleration))

    @as_sync
    async def set_defaults_joint(
        self,
        speed: Value[domains.RatioDomain] | None,
        acceleration: Value[domains.AngularAccelerationDomain] | None,
        jerk: Value[domains.AngularJerkDomain] | None,
    ) -> None:
        _logger.debug(
            "Setting defaults joint movement parameters: speed=%s, acceleration=%s, jerk=%s", speed, acceleration, jerk
        )

        await self._task_queue.run_blocking(
            self._robot.set_defaults_joint(speed=speed, acceleration=acceleration, jerk=jerk)
        )

    @as_sync
    async def set_defaults_linear(
        self,
        speed: Value[domains.SpeedDomain] | None,
        acceleration: Value[domains.AccelerationDomain] | None,
        jerk: Value[domains.JerkDomain] | None,
    ) -> None:
        _logger.debug(
            "Setting defaults linear movement parameters: speed=%s, acceleration=%s, jerk=%s", speed, acceleration, jerk
        )

        await self._task_queue.run_blocking(
            self._robot.set_defaults_linear(speed=speed, acceleration=acceleration, jerk=jerk)
        )

    @as_sync
    async def set_tool_state(self, state: FingerGripperState | VacuumGripperState) -> None:
        run = self._task_queue.run_blocking
        _logger.debug("Setting tool state: state=%s", state)

        if isinstance(state, FingerGripperState):
            await run(self._robot.set_finger_gripper_state(state))
        else:
            await run(self._robot.set_vacuum_gripper_state(state))

    @as_sync
    async def set_frame(self, frame: Frame) -> None:
        run = self._task_queue.run_blocking
        _logger.debug("Setting frame: frame=%s", frame)

        await run(self._robot.set_frame(frame))

    @as_sync
    async def set_tool(self, tool: Tool):
        run = self._task_queue.run_blocking
        _logger.debug("Setting tool: tool=%s", tool)

        await run(self._robot.set_tool(tool))

    @contextlib.contextmanager
    def frame(self, frame: Frame) -> typing.Iterator[None]:
        current_frame = self.get_frame()
        _logger.debug("Switching from old frame to new frame: old frame=%s, new frame=%s", current_frame, frame)
        try:
            self.set_frame(frame)
            yield
        finally:
            self.set_frame(current_frame)

    @contextlib.contextmanager
    def tool(self, tool: Tool) -> typing.Iterator[None]:
        current_tool = self.get_tool()
        try:
            self.set_tool(tool)
            yield
        finally:
            self.set_tool(current_tool)

    @as_sync
    async def get_frame(self) -> Frame:
        return await self._robot.get_frame()

    @as_sync
    async def get_tool(self) -> Tool:
        return await self._robot.get_tool()

    @as_sync
    async def get_pose(self) -> Cartesian:
        return await self._robot.get_pose()

    @as_sync
    async def get_joints(self) -> Joints:
        return await self._robot.get_joints()

    @as_sync
    async def read_input(self, inputs: typing.Sequence[IoName[_TIo]]) -> typing.Sequence[_TIo]:
        values = await self._robot.get_inputs(inputs)
        return [value.value for value in values]

    @as_sync
    async def write_output(self, values: dict[IoName[_TIo], _TIo]) -> None:
        spec = [IoValue(io.index, value, io.value_type) for io, value in values.items()]
        await self._robot.write_outputs(spec)

    @as_sync
    async def wait_for_input(
        self, inputs: typing.Sequence[IoName[_TIo]], predicate: Callable[[list[_TIo]], bool]
    ) -> typing.Sequence[_TIo]:
        while True:
            response = await self._robot.wait_for_input_change(inputs)
            values = [value.value for value in response]

            if predicate(values):
                return values


__all__ = (
    "OraSync",
    "Cartesian",
    "Joints",
    "ReferenceFrameModifier",
    "Frame",
    "Tool",
    "ToolType",
    "ToolCollider",
    "FingerGripperState",
    "VacuumGripperState",
)
