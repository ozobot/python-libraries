import contextlib
import math
import typing

import pydantic
from loguru import logger
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample, SampleWithoutTimestamp
from ozobot.web.browser import _rpcCoroutine

from . import rpctypes
from .conversions import (
    color_code_from_web,
    color_from_web,
    direction_to_web,
    intersection_from_web,
    ir_message_from_web,
    led_to_web_json,
    robot_geometry_from_web,
)
from .exceptions import (
    InvalidWebRobotSelectorError,
    MemoryReadUnsuccessfulError,
    MissingRobotSelectorError,
)


class Rpc:
    def __init__(self, robot_name: str) -> None:
        self._name = robot_name

    @typing.overload
    async def execute[T: pydantic.BaseModel](self, req: rpctypes.BaseRequest, response_class: type[T]) -> T: ...

    @typing.overload
    async def execute[T](self, req: rpctypes.BaseRequest, response_class: pydantic.TypeAdapter[T]) -> T: ...

    async def execute(
        self, req: rpctypes.BaseRequest, response_class: type[pydantic.BaseModel] | pydantic.TypeAdapter[typing.Any]
    ) -> typing.Any:
        logger.debug("Sending request to web python", rpc=req)
        ret = await _rpcCoroutine(self._name, req.method, req.args)
        logger.debug("Received response from web-python", response=ret)

        if isinstance(response_class, pydantic.TypeAdapter):
            return response_class.validate_python(ret)
        return response_class.model_validate(ret)


# To make the code cleaner, we define the rpctypes.Sample[T] and list[rpctypes.Sample[T]] factories...
# We need to pass the runtime type as rpc.execute's response_type, but pydantic fails when T is
#     a generic type (e.g., TProtoFrom: pydantic.BaseModel bound to a function) and mypy fails when T is a
#     runtime type (e.g, T = type(int)). We use the following to satisfy both...
#     https://github.com/python/mypy/issues/13619
def _get_response_model_list[T](_type: type[T]) -> type[list[T]]:
    response_model = list[_type]  # type: ignore[valid-type]
    return response_model


class WebDataAccessWatch[TProtoFrom: pydantic.BaseModel, TLib]:
    def __init__(
        self,
        rpc: Rpc,
        property_name: str,
        *,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
    ) -> None:
        self._rpc = rpc
        self._property_name = property_name
        self._type = response_type
        self._from_protocol = from_protocol

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[TLib]]:
        yield self._watch_iter()

    async def _watch_iter(self) -> typing.AsyncIterator[TLib]:
        last_value: TProtoFrom | None = None

        while True:
            req = rpctypes.MemWatchRequest.create(
                name=self._property_name, last_value=last_value.model_dump() if last_value else None
            )
            response_model = pydantic.TypeAdapter(_get_response_model_list(self._type))
            values = await self._rpc.execute(req, response_model)
            last_value = values[-1]
            for sample in values:
                yield self._convert_from_protocol(sample)

    def _convert_from_protocol(self, value: TProtoFrom) -> TLib:
        if isinstance(value, self._type):
            converted_val = self._from_protocol(value)
            return converted_val
        else:
            raise MemoryReadUnsuccessfulError(self._property_name, f"got unexpected type {type(value)}")


class WebDataAccessRead[TProtoFrom: pydantic.BaseModel, TLib]:
    def __init__(
        self,
        rpc: Rpc,
        property_name: str,
        *,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
    ) -> None:
        self._rpc = rpc
        self._property_name = property_name
        self._type = response_type
        self._from_protocol = from_protocol

    async def read(self) -> TLib:
        req = rpctypes.MemReadRequest.create(name=self._property_name)
        resp = await self._rpc.execute(req, self._type)
        return self._from_protocol(resp)


class WebDataAccessReadWatch[TProtoFrom: pydantic.BaseModel, TLib]:
    def __init__(
        self,
        rpc: Rpc,
        property_name: str,
        *,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
    ) -> None:
        self._read = WebDataAccessRead(rpc, property_name, response_type=response_type, from_protocol=from_protocol)
        self._watch = WebDataAccessWatch(rpc, property_name, response_type=response_type, from_protocol=from_protocol)

    def watch(self) -> typing.AsyncContextManager[typing.AsyncIterator[TLib]]:
        return self._watch.watch()

    async def read(self) -> TLib:
        return await self._read.read()


class WebDataAccessReadWrite[TProtoFrom: pydantic.BaseModel, TProtoTo, TLib](WebDataAccessReadWatch[TProtoFrom, TLib]):
    def __init__(
        self,
        rpc: Rpc,
        property_name: str,
        *,
        property_key: str,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
        to_protocol: typing.Callable[[TLib], TProtoTo],
    ) -> None:
        super().__init__(rpc, property_name, response_type=response_type, from_protocol=from_protocol)
        self._rpc = rpc
        self._property_name = property_name
        self._type = response_type
        self._to_protocol = to_protocol
        self._property_key = property_key

    async def write(self, value: TLib) -> None:
        data = self._to_protocol(value)
        req = rpctypes.MemWriteRequest.create(name=self._property_name, data=data)
        await self._rpc.execute(req, rpctypes.ValidatedNone)


class WebMemoryRegions:
    def __init__(self, rpc: Rpc) -> None:
        self.color_code = WebDataAccessReadWatch(
            rpc,
            "colorCode",
            response_type=rpctypes.ColorCodeResponse,
            from_protocol=lambda x: SampleWithoutTimestamp(color_code_from_web(x.colors)),
        )

        self.intersection = WebDataAccessWatch(
            rpc,
            "intersection",
            response_type=rpctypes.IntersectionResponse,
            from_protocol=lambda x: SampleWithoutTimestamp(intersection_from_web(x.intersection)),
        )

        self.line_following_speed = WebDataAccessReadWrite(
            rpc,
            "lineFollowingSpeed",
            property_key="speed",
            response_type=rpctypes.ValidatedFloat,
            from_protocol=lambda x: x.root * 1000,
            to_protocol=lambda x: x / 1000,
        )

        self.surface_color = WebDataAccessReadWatch(
            rpc,
            "surfaceColor",
            response_type=rpctypes.ColorResponse,
            from_protocol=lambda x: Sample(None if x.color is None else color_from_web(x.color), x.timestamp),
        )

        self.line_color = WebDataAccessReadWatch(
            rpc,
            "lineColor",
            response_type=rpctypes.ColorResponse,
            from_protocol=lambda x: Sample(None if x.color is None else color_from_web(x.color), x.timestamp),
        )

        self.proximity_left_front = WebDataAccessReadWatch(
            rpc,
            "proximityLeftFront",
            response_type=rpctypes.IrProximityResponse,
            from_protocol=lambda m: Sample(m.value, m.timestamp),
        )
        self.proximity_right_front = WebDataAccessReadWatch(
            rpc,
            "proximityRightFront",
            response_type=rpctypes.IrProximityResponse,
            from_protocol=lambda m: Sample(m.value, m.timestamp),
        )

        self.ir_message_left_front = WebDataAccessReadWatch(
            rpc,
            "irMessageLeftFront",
            response_type=rpctypes.ReadIrResponse,
            from_protocol=lambda m: Sample(ir_message_from_web(m), m.timestamp),
        )
        self.ir_message_right_front = WebDataAccessReadWatch(
            rpc,
            "irMessageRightFront",
            response_type=rpctypes.ReadIrResponse,
            from_protocol=lambda m: Sample(ir_message_from_web(m), m.timestamp),
        )

        self.geometry = WebDataAccessRead(
            rpc,
            "geometry",
            response_type=rpctypes.RobotGeometryResponse,
            from_protocol=robot_geometry_from_web,
        )


class LineFollowerWebDriver:
    @property
    def memory(self) -> WebMemoryRegions:
        return self._memory

    def __init__(self, name: str) -> None:
        self._rpc = Rpc(name)
        self._memory = WebMemoryRegions(self._rpc)

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        *,
        name: str | None = None,
        **kwargs,
    ) -> typing.AsyncIterator[typing.Self]:
        if not name:
            raise MissingRobotSelectorError("name")

        for param_name, param_value in kwargs.items():
            if param_value is not None:
                raise InvalidWebRobotSelectorError(param_name)

        yield cls(name)

    async def move(self, distance_mm: float, speed_mmps: float) -> None:
        req = rpctypes.MoveStraightRequest(
            distance_m=distance_mm / 1000,
            speed_ms=speed_mmps / 1000,
        )
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        req = rpctypes.RotateRequest(
            angle_rad=math.radians(angle_deg),
            angular_speed_radps=math.radians(angular_speed_degps),
        )
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)

    async def velocity(self, linear_mmps: float, angular_degps: float, duration_ms: int) -> None:
        req = rpctypes.VelocityRequest(
            linear_speed_mps=linear_mmps / 1000,
            angular_speed_radps=math.radians(angular_degps),
            duration_ms=duration_ms,
        )
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        req = rpctypes.PlayToneRequest(frequency_hz=frequency_hz, duration_ms=duration_ms)
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)

    # async def play_audio(self, audio_name: str) -> None:
    #     robot specific implementation can be found in ari and evo packages

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        mask_json = led_to_web_json(mask)
        req = rpctypes.SetLedRequest(mask=mask_json, red=red, green=green, blue=blue, alpha=255)
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        way = direction_to_web(direction)

        req = rpctypes.LineNavigationRequest(direction=way, follow=follow)
        _ = await self._rpc.execute(req, rpctypes.ValidatedNone)
