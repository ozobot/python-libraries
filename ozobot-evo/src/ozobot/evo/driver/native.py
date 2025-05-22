from __future__ import annotations

import contextlib
import typing
from uuid import UUID

from ozobot.ble.connection import Characteristic, open_client
from ozobot.evo.protocol import AsyncControl, Types
from ozobot.protocol_common.exceptions import OzobotProtocolCommandError

from .driver import LEDMask, TDirection


_SERVICE_UUID = UUID("8903136c-5f13-4548-a885-c58779136801")
_CHARACTERISTIC_UUID = UUID("8903136c-5f13-4548-a885-c58779136802")


class _HasExecutionState(typing.Protocol):
    executionState: Types.ExecutionStateEnum


@typing.runtime_checkable
class _HasCallStatus(typing.Protocol):
    callStatus: Types.CallStatus


@typing.runtime_checkable
class _HasResult(typing.Protocol):
    result: Types.IOResult


class NativeDriver:
    def __init__(self, characteristic: Characteristic) -> None:
        self._control = AsyncControl(characteristic)

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        address: str | None = None,
        id_prefix: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncIterator[NativeDriver]:
        async with open_client(address=address, id_prefix=id_prefix, name=name) as client:
            char = client.get_characteristic(_SERVICE_UUID, _CHARACTERISTIC_UUID)
            yield cls(char)

    async def move(self, distance_m: float, speed_ms: float) -> None:
        async with self._control.MoveStraight(self._control.get_next_request_id(), distance_m, speed_ms) as (
            resp,
            evts,
        ):
            await self._handle_events("MoveStraight", evts)

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None:
        async with self._control.Rotate(self._control.get_next_request_id(), angle_rad, angular_speed_radps) as (
            resp,
            evts,
        ):
            await self._handle_events("Rotate", evts)

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None:
        async with self._control.Velocity(
            self._control.get_next_request_id(), linear_mps, angular_radps, duration_ms
        ) as (resp, evts):
            await self._handle_events("Velocity", evts)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        async with self._control.PlayTone(self._control.get_next_request_id(), frequency_hz, duration_ms, volume) as (
            resp,
            evts,
        ):
            await self._handle_events("PlayTone", evts)

    async def execute_file(self, filename: str) -> None:
        async with self._control.ExecuteFile(self._control.get_next_request_id(), filename) as (resp, evts):
            self._handle_response("ExecuteFile", resp)
            await self._handle_events("ExecuteFile", evts)

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        protocol_mask: Types.LEDsMask = Types.LEDsMask(0)
        for led in mask:
            match led:
                case LEDMask.FRONT_LEFT:
                    protocol_mask |= Types.LEDsMask.front_left
                case LEDMask.FRONT_LEFT_CENTER:
                    protocol_mask |= Types.LEDsMask.front_left_center
                case LEDMask.FRONT_CENTER:
                    protocol_mask |= Types.LEDsMask.front_center
                case LEDMask.FRONT_RIGHT_CENTER:
                    protocol_mask |= Types.LEDsMask.front_right_center
                case LEDMask.FRONT_RIGHT:
                    protocol_mask |= Types.LEDsMask.front_right
                case LEDMask.TOP:
                    protocol_mask |= Types.LEDsMask.top
                case _:
                    typing.assert_never(led)

        response = await self._control.SetLED(protocol_mask, red, green, blue, 255)
        self._handle_response("SetLED", response)

    async def line_navigation(self, direction: TDirection, follow: bool) -> None:
        match direction:
            case "left":
                direction_protocol = Types.IntersectionDirection.Left
            case "right":
                direction_protocol = Types.IntersectionDirection.Right
            case "straight":
                direction_protocol = Types.IntersectionDirection.Straight
            case "backward":
                direction_protocol = Types.IntersectionDirection.Backward
            case _:
                typing.assert_never(direction)

        action = Types.LineNavigationAction.Follow if follow else Types.LineNavigationAction.DoNotFollow
        async with self._control.LineNavigation(self._control.get_next_request_id(), direction_protocol, action) as (
            resp,
            evts,
        ):
            await self._handle_events("LineNavigation", evts)

    async def follow_speed(self, speed_mps: float) -> None:
        speed_vmem_properties = self._control.property_metadata["lineNavigationSpeed"]
        response = await self._control.MemWrite(
            speed_vmem_properties["address"],
            speed_vmem_properties["type"].get_data_width(),
            Types.S8_24(speed_mps).serialize(),
        )
        self._handle_response("MemWrite(lineNavigationSpeed)", response)

    async def stop_all(self) -> None:
        await self._control.StopExecution(0)

    def _handle_response(self, function_name: str, response: _HasCallStatus | _HasResult) -> None:
        if isinstance(response, _HasCallStatus):
            if response.callStatus != Types.CallStatus.CallSuccess:
                raise OzobotProtocolCommandError(function_name, response.callStatus.name, description="call failed")
        elif isinstance(response, _HasResult):
            if response.result != Types.IOResult.Success:
                raise OzobotProtocolCommandError(function_name, response.result.name, description="call failed")

    async def _handle_events(self, function_name: str, events: typing.AsyncIterator[_HasExecutionState]) -> None:
        async for event in events:
            if event.executionState == Types.ExecutionStateEnum.FinishedNormal:
                return

            if event.executionState != Types.ExecutionStateEnum.Running:
                raise OzobotProtocolCommandError(
                    function_name,
                    event.executionState.name,
                    description="failure execution state",
                )
