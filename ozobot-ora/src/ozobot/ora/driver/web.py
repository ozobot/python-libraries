import contextlib
import typing
from logging import getLogger

from ozobot.ora.datatypes import (
    Cartesian,
    FingerGripperState,
    Frame,
    IoName,
    IoValue,
    IoValueType,
    Joints,
    ReferenceFrameModifier,
    Tool,
    ToolCollider,
    ToolType,
    VacuumGripperState,
)
from ozobot.ora.units import PhysicalQuantityDomain, Value, domains, number_to_value, quantities, units, value_to_number
from ozobot.web.browser import _rpcCoroutine

logger = getLogger(__name__)

_TIo = typing.TypeVar("_TIo", bool, float)
_TDomain = typing.TypeVar("_TDomain", bound=PhysicalQuantityDomain)


def _wpr_value_to_tuple(value: Cartesian | Frame) -> tuple[float, ...]:
    values = tuple(value)
    xyz = values[:3]
    wpr = reversed(values[3:])
    return (
        *value_to_number(xyz, expected_domain=domains.DistanceDomain()),
        *value_to_number(wpr, expected_domain=domains.AngleDomain()),
    )


def _tuple_to_frame(value: tuple[float, ...]) -> Frame:
    xyz = number_to_value(value[:3], physical_quantity=quantities.mm)
    rpy = number_to_value(value[3:], physical_quantity=quantities.deg)
    wpr = rpy[2], rpy[1], rpy[0]
    coordinates = xyz[0], xyz[1], xyz[2], wpr[0], wpr[1], wpr[2]  # this expressive expansion is needed because of mypy
    return Frame(*coordinates)


def _tuple_to_cartesian(value: tuple[float, ...]) -> Cartesian:
    xyz = number_to_value(value[:3], physical_quantity=quantities.mm)
    rpy = number_to_value(value[3:], physical_quantity=quantities.deg)
    wpr = rpy[2], rpy[1], rpy[0]
    coordinates = xyz[0], xyz[1], xyz[2], wpr[0], wpr[1], wpr[2]  # this expressive expansion is needed because of mypy
    return Cartesian(*coordinates)


class OraWebDriver:
    device_name: str

    def __init__(self, device_name: str | None = None):
        # FIXME: move default speed settings to a driver wrapper class
        self._default_tcp_speed_mm_s: float = 100
        self._default_tcp_acceleration_mm_s2: float = 2000
        self._default_tcp_jerk_mm_s3: float = 7000
        self._default_joint_speed_deg_s: float = 20
        self._default_joint_acceleration_deg_s2: float = 500
        self._default_joint_jerk_deg_s3: float = 11459

        self.device_name = device_name or "ora"
        if "." in self.device_name:
            raise ValueError("Ora device name must not contain '.'")

    @classmethod
    @contextlib.asynccontextmanager
    async def open(cls, *, name: str | None = None) -> typing.AsyncIterator["OraWebDriver"]:
        yield OraWebDriver(name)

    async def _controller(self, method_name: str, args: list[typing.Any] | None = None) -> typing.Any:
        return await _rpcCoroutine(self.device_name, method_name, args or [])

    async def _listener(self, method_name: str, args: list[typing.Any] | None = None) -> typing.Any:
        return await _rpcCoroutine(self.device_name + ".listener", method_name, args or [])

    async def get_tool(self) -> Tool:
        tool = await self._listener("getToolParameters")
        return Tool(
            type=ToolType(tool["endToolType"]),
            tcp=_tuple_to_frame(tool["tcp"]),
            center_of_gravity=number_to_value(tool["centerOfGravity"], physical_quantity=quantities.mm),
            weight=number_to_value(tool["weight"], physical_quantity=quantities.kg),
            collider=ToolCollider(tool["collisionModelType"]),
        )

    async def get_frame(self) -> Frame:
        frame = await self._listener("getFrame")
        return _tuple_to_frame(frame)

    async def get_pose(self) -> Cartesian:
        pose = await self._listener("getPose")
        return _tuple_to_cartesian(pose)

    async def get_joints(self) -> Joints:
        joints = await self._listener("getJointPose")
        return Joints(*number_to_value(joints, physical_quantity=quantities.deg))

    async def set_tool(self, tool: Tool):
        parameters = {
            "collisionModelType": tool.collider.model_type,
            "endToolType": tool.type.value,
            "tcp": _wpr_value_to_tuple(tool.tcp),
            "centerOfGravity": value_to_number(tool.center_of_gravity, expected_domain=domains.DistanceDomain()),
            "weight": value_to_number(tool.weight, expected_domain=domains.WeightDomain()),
        }

        return await self._controller("setToolParameters", [parameters])

    async def _set_tool_by_type(self, tool_type: typing.Literal["VACUUM_GRIPPER", "FINGER_GRIPPER", "NO_TOOL"]):
        # fixme: this is a workaround used by Blockly for not having the predefined tools available yet
        blockly_type_to_ts_api = {
            "VACUUM_GRIPPER": "vacuumGripper",
            "FINGER_GRIPPER": "fingerGripper",
            "NO_TOOL": "noTool",
        }

        tool_type_ts_api = blockly_type_to_ts_api[tool_type]

        return await self._controller(
            "setTool",
            [
                tool_type_ts_api,
            ],
        )

    async def set_frame(self, frame: Frame) -> None:
        return await self._controller(
            "setFrame",
            [
                _wpr_value_to_tuple(frame),
            ],
        )

    async def set_finger_gripper_state(self, state: FingerGripperState):
        return await self._controller(
            "setFingerGripperState",
            [
                state.value,
            ],
        )

    async def set_vacuum_gripper_state(self, state: VacuumGripperState, wait: bool = False):
        return await self._controller(
            "setVacuumGripperState",
            [
                state == VacuumGripperState.ON,
                wait,
            ],
        )

    async def move_linear(
        self,
        pose: Cartesian,
        reference_frame_modifier: ReferenceFrameModifier = ReferenceFrameModifier.ABSOLUTE,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ):
        pose_tuple = _wpr_value_to_tuple(pose)
        args = [
            pose_tuple[:3],
            pose_tuple[3:],
            reference_frame_modifier.value,
            *self._construct_linear_movement_kwargs(speed=speed, acceleration=acceleration, jerk=jerk),
        ]
        return await self._controller("moveLinear", args)

    async def move_joints(
        self,
        pose: Joints | Cartesian,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        jerk: Value[domains.AngularJerkDomain] | None = None,
    ):
        cmd_name = "moveJoint" if isinstance(pose, Joints) else "moveJointToCartesian"
        formatted_pose = (
            value_to_number(tuple(pose), expected_domain=domains.AngleDomain())
            if isinstance(pose, Joints)
            else _wpr_value_to_tuple(pose)
        )
        args = [
            formatted_pose,
            *self._construct_joint_movement_kwargs(speed=speed, acceleration=acceleration, jerk=jerk),
        ]
        return await self._controller(cmd_name, args)

    async def move_simple(self, pose: Cartesian):
        tuple_pose = _wpr_value_to_tuple(pose)
        return await self._controller(
            "moveToPosition",
            [
                tuple_pose[:3],
                tuple_pose[3:],
            ],
        )

    async def move_circle(
        self,
        p_aux: Cartesian,
        p_end: Cartesian,
        *,
        arc_angle: Value[domains.AngleDomain],
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ):
        args = [
            _wpr_value_to_tuple(p_aux),
            _wpr_value_to_tuple(p_end),
            arc_angle.as_base_quantity().value,
            *self._construct_linear_movement_kwargs(speed=speed, acceleration=acceleration, jerk=jerk),
        ]
        return await self._controller("moveCircle", args)

    async def set_defaults_linear(
        self,
        speed: Value[domains.SpeedDomain] | None = None,
        acceleration: Value[domains.AccelerationDomain] | None = None,
        jerk: Value[domains.JerkDomain] | None = None,
    ):
        speed_raw, acc_raw, jerk_raw = self._construct_linear_movement_kwargs(
            speed=speed, acceleration=acceleration, jerk=jerk
        )
        if speed_raw:
            self._default_tcp_speed_mm_s = speed_raw

        if acc_raw:
            self._default_tcp_acceleration_mm_s2 = acc_raw

        if jerk_raw:
            self._default_tcp_jerk_mm_s3 = jerk_raw

    async def set_defaults_joint(
        self,
        speed: Value[domains.RatioDomain] | None = None,
        acceleration: Value[domains.AngularAccelerationDomain] | None = None,
        jerk: Value[domains.AngularJerkDomain] | None = None,
    ):
        speed_raw, acc_raw, jerk_raw = self._construct_joint_movement_kwargs(
            speed=speed, acceleration=acceleration, jerk=jerk
        )
        if speed_raw:
            self._default_joint_speed_deg_s = speed_raw

        if acc_raw:
            self._default_joint_acceleration_deg_s2 = acc_raw

        if jerk_raw:
            self._default_joint_jerk_deg_s3 = jerk_raw

    async def _set_speed(self, speed_percent: float):
        await self.set_defaults_joint(
            speed=units(speed_percent, quantities.percent),
            acceleration=units(500, quantities.deg / quantities.s**2),
            jerk=None,
        )
        await self.set_defaults_linear(
            speed=units(500 * speed_percent / 100, quantities.mm / quantities.s),
            acceleration=units(2000, quantities.mm / quantities.s**2),
            jerk=None,
        )

        return await self._controller(
            "setSpeed",
            [
                speed_percent / 100,
            ],
        )

    async def get_inputs(self, inputs: typing.Sequence[IoName[_TIo]]) -> typing.Sequence[IoValue[_TIo]]:
        return await self._read_inputs(lambda args: self._controller("readInputs", args), inputs)

    async def wait_for_input_change(self, inputs: typing.Sequence[IoName[_TIo]]) -> typing.Sequence[IoValue[_TIo]]:
        return await self._read_inputs(lambda args: self._listener("waitForInputs", args), inputs)

    async def _read_inputs(
        self,
        call_component_fnc: typing.Callable[[list[typing.Any]], typing.Awaitable[typing.Any]],
        inputs: typing.Sequence[IoName[_TIo]],
    ) -> typing.Sequence[IoValue[_TIo]]:
        parameters = [{"index": input.index, "type": input.value_type.value} for input in inputs]

        values = await call_component_fnc(
            [
                parameters,
            ],
        )
        return typing.cast(
            typing.Sequence[IoValue[_TIo]],
            [
                IoValue(index=value["index"], value=value["value"], value_type=IoValueType(value["type"]))
                for value in values
            ],
        )

    async def write_outputs(self, outputs: typing.Sequence[IoValue[_TIo]]) -> None:
        parameters = [
            {"index": output.index, "type": output.value_type.value, "value": output.value} for output in outputs
        ]
        await self._controller(
            "writeOutputs",
            [
                parameters,
            ],
        )

    def _construct_joint_movement_kwargs(
        self,
        *,
        speed: Value[domains.RatioDomain] | None,
        acceleration: Value[domains.AngularAccelerationDomain] | None,
        jerk: Value[domains.AngularJerkDomain] | None,
    ) -> tuple[float, float, float]:
        return (
            self._default_joint_speed_deg_s
            if speed is None
            else speed.as_base_quantity().value / 100 * 180,  # convert percent to fraction and then to degrees
            self._default_joint_acceleration_deg_s2 if acceleration is None else acceleration.as_base_quantity().value,
            self._default_joint_jerk_deg_s3 if jerk is None else jerk.as_base_quantity().value,
        )

    def _construct_linear_movement_kwargs(
        self,
        *,
        speed: Value[domains.SpeedDomain] | None,
        acceleration: Value[domains.AccelerationDomain] | None,
        jerk: Value[domains.JerkDomain] | None,
    ) -> tuple[float, float, float]:
        return (
            self._default_tcp_speed_mm_s if speed is None else speed.as_base_quantity().value,
            self._default_tcp_acceleration_mm_s2 if acceleration is None else acceleration.as_base_quantity().value,
            self._default_tcp_jerk_mm_s3 if jerk is None else jerk.as_base_quantity().value,
        )
