import typing

from ozobot.actors.actors import context
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


class Ora(typing.Protocol):
    async def get_tool(self) -> Tool: ...

    async def get_frame(self) -> Frame: ...

    async def get_pose(self) -> Cartesian: ...

    async def get_joints(self) -> Joints: ...

    async def set_tool(self, tool: Tool) -> None: ...

    async def set_frame(self, frame: Frame) -> None: ...

    async def set_finger_gripper_state(self, state: FingerGripperState) -> None: ...

    async def set_vacuum_gripper_state(self, state: VacuumGripperState, wait: bool = False) -> None: ...

    async def move_linear(
        self,
        pose: Cartesian,
        reference_frame_modifier: ReferenceFrameModifier = ReferenceFrameModifier.ABSOLUTE,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
    ) -> None: ...

    async def move_joints(
        self,
        pose: Joints | Cartesian,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
    ) -> None: ...

    async def move_simple(self, pose: Cartesian) -> None: ...

    async def move_circle(
        self,
        p_aux: Cartesian,
        p_end: Cartesian,
        *,
        arc_angle: Value[domains.AngleDomain],
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
    ) -> None: ...

    async def set_default_radius(self, radius: Value[domains.DistanceDomain]) -> None: ...

    async def set_defaults_linear(
        self,
        speed: Value[domains.SpeedDomain] | None,
        acceleration: Value[domains.AccelerationDomain] | None,
        jerk: Value[domains.JerkDomain] | None,
    ) -> None: ...

    async def set_defaults_joint(
        self,
        speed: Value[domains.RatioDomain] | None,
        acceleration: Value[domains.AngularAccelerationDomain] | None,
        jerk: Value[domains.AngularJerkDomain] | None,
    ) -> None: ...

    async def get_inputs[T: (bool, float)](self, inputs: typing.Sequence[IoName[T]]) -> typing.Sequence[IoValue[T]]: ...

    async def wait_for_input_change[T: (bool, float)](
        self, inputs: typing.Sequence[IoName[T]]
    ) -> typing.Sequence[IoValue[T]]: ...

    async def write_outputs[T: (bool, float)](self, outputs: typing.Sequence[IoValue[T]]) -> None: ...


async def get_tool() -> Tool:
    return await context.dispatcher.acall(Ora.get_tool)


async def get_frame() -> Frame:
    return await context.dispatcher.acall(Ora.get_frame)


async def get_pose() -> Cartesian:
    return await context.dispatcher.acall(Ora.get_pose)


async def get_joints() -> Joints:
    return await context.dispatcher.acall(Ora.get_joints)


async def set_tool(tool: Tool) -> None:
    return await context.dispatcher.acall(Ora.set_tool, tool)


async def set_frame(frame: Frame) -> None:
    return await context.dispatcher.acall(Ora.set_frame, frame)


async def set_finger_gripper_state(state: FingerGripperState) -> None:
    return await context.dispatcher.acall(Ora.set_finger_gripper_state, state)


async def set_vacuum_gripper_state(state: VacuumGripperState, wait: bool = False) -> None:
    return await context.dispatcher.acall(Ora.set_vacuum_gripper_state, state, wait)


async def move_linear(
    pose: Cartesian,
    reference_frame_modifier: ReferenceFrameModifier = ReferenceFrameModifier.ABSOLUTE,
    speed: Value[domains.SpeedDomain] | None = None,
    acceleration: Value[domains.AccelerationDomain] | None = None,
    cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
) -> None:
    return await context.dispatcher.acall(Ora.move_linear, pose, reference_frame_modifier, speed, acceleration, cont)


async def move_joints(
    pose: Joints | Cartesian,
    speed: Value[domains.RatioDomain] | None = None,
    acceleration: Value[domains.AngularAccelerationDomain] | None = None,
    cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
) -> None:
    return await context.dispatcher.acall(Ora.move_joints, pose, speed, acceleration, cont)


async def move_simple(pose: Cartesian) -> None:
    return await context.dispatcher.acall(Ora.move_simple, pose)


async def move_circle(
    p_aux: Cartesian,
    p_end: Cartesian,
    *,
    arc_angle: Value[domains.AngleDomain],
    speed: Value[domains.SpeedDomain] | None = None,
    acceleration: Value[domains.AccelerationDomain] | None = None,
    cont: Value[domains.DistanceDomain] | typing.Literal["yes"] | None = None,
) -> None:
    return await context.dispatcher.acall(
        Ora.move_circle, p_aux, p_end, arc_angle=arc_angle, speed=speed, acceleration=acceleration, cont=cont
    )


async def set_default_radius(radius: Value[domains.DistanceDomain]) -> None:
    return await context.dispatcher.acall(Ora.set_default_radius, radius)


async def set_defaults_linear(
    speed: Value[domains.SpeedDomain] | None,
    acceleration: Value[domains.AccelerationDomain] | None,
    jerk: Value[domains.JerkDomain] | None,
) -> None:
    return await context.dispatcher.acall(Ora.set_defaults_linear, speed, acceleration, jerk)


async def set_defaults_joint(
    speed: Value[domains.RatioDomain] | None,
    acceleration: Value[domains.AngularAccelerationDomain] | None,
    jerk: Value[domains.AngularJerkDomain] | None,
) -> None:
    return await context.dispatcher.acall(Ora.set_defaults_joint, speed, acceleration, jerk)


async def get_inputs[T: (bool, float)](inputs: typing.Sequence[IoName[T]]) -> typing.Sequence[IoValue[T]]:
    return await context.dispatcher.acall(Ora.get_inputs, inputs)


async def wait_for_input_change[T: (bool, float)](inputs: typing.Sequence[IoName[T]]) -> typing.Sequence[IoValue[T]]:
    return await context.dispatcher.acall(Ora.wait_for_input_change, inputs)


async def write_outputs[T: (bool, float)](outputs: typing.Sequence[IoValue[T]]) -> None:
    return await context.dispatcher.acall(Ora.write_outputs, outputs)
