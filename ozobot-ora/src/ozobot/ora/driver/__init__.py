import sys
import typing

from ozobot.ora.datatypes import (
    Cartesian,
    FingerGripperState,
    Frame,
    IoName,
    IoValue,
    Joints,
    ReferenceFrameModifier,
    Tool,
    VacuumGripperState,
)
from ozobot.ora.units import Value, domains


class OraDriver(typing.Protocol):
    @classmethod
    def open(
        cls,
        *,
        name: str | None = None,
    ) -> typing.AsyncContextManager[typing.Self]: ...

    async def get_tool(self) -> Tool: ...

    async def get_frame(self) -> Frame: ...

    async def get_pose(self) -> Cartesian: ...

    async def get_joints(self) -> Joints: ...

    async def set_tool(self, tool: Tool): ...

    async def set_frame(self, frame: Frame) -> None: ...

    async def set_finger_gripper_state(self, state: FingerGripperState): ...

    async def set_vacuum_gripper_state(self, state: VacuumGripperState, wait: bool = False): ...

    async def move_linear(
        self,
        pose: Cartesian,
        reference_frame_modifier: ReferenceFrameModifier = ReferenceFrameModifier.ABSOLUTE,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ): ...

    async def move_joints(
        self,
        pose: Joints | Cartesian,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        jerk: Value[domains.AngularJerkDomain] | None = None,
    ): ...

    async def move_simple(self, pose: Cartesian): ...

    async def move_circle(
        self,
        p_aux: Cartesian,
        p_end: Cartesian,
        *,
        arc_angle: Value[domains.AngleDomain],
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ): ...

    async def set_defaults_linear(
        self,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ): ...

    async def set_defaults_joint(
        self,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        jerk: Value[domains.AngularJerkDomain] | None = None,
    ): ...

    async def get_inputs[TIo: (bool, float)](
        self, inputs: typing.Sequence[IoName[TIo]]
    ) -> typing.Sequence[IoValue[TIo]]: ...

    async def wait_for_input_change[TIo: (bool, float)](
        self, inputs: typing.Sequence[IoName[TIo]]
    ) -> typing.Sequence[IoValue[TIo]]: ...

    async def write_outputs[TIo: (bool, float)](self, outputs: typing.Sequence[IoValue[TIo]]) -> None: ...


if typing.TYPE_CHECKING:
    from ozobot.ora.driver.web import OraWebDriver

    instance: OraDriver = OraWebDriver()


def get_driver() -> type[OraDriver]:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        from ozobot.ora.driver.web import OraWebDriver

        return OraWebDriver
    else:
        raise NotImplementedError("ORA native driver not yet implemented")
