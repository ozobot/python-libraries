import contextlib
import math
import typing

import pydantic
from loguru import logger
from ozobot.linefollower.api.data_access import EventWatcher, EventWatcherQueue
from ozobot.linefollower.datatypes import ColorCode, Direction, LEDMask, Sample
from ozobot.linefollower.exceptions import (
    DriverCommandFailedError,
)
from ozobot.web import rpctypes
from ozobot.web.conversions import (
    color_from_web,
    direction_to_web,
    intersection_from_web,
    led_to_web_json,
)
from ozobot.web.exceptions import (
    InvalidWebRobotSelectorError,
    MemoryReadUnsuccessfulError,
    MissingRobotSelectorError,
)

try:
    # this library is only present in web-python web application distribution
    # if the import fails, we are running natively, and we can create a mock function instead
    from _ozo import _rpcCoroutine  # type: ignore[import]

except ImportError:
    logger.warning(
        "`_ozo` module could not be imported which is expected to happen when a web driver is used outside of the pyodide environment"
    )

    async def _rpcCoroutine(object_name: str, func_name: str, args: list[typing.Any]) -> typing.Any:
        raise NotImplementedError("`_rpcCoroutine` is only available in the pyodide environment")


@typing.runtime_checkable
class _HasTimestamp(typing.Protocol):
    timestamp: int


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

    async def read(self) -> Sample[TLib]:
        req = rpctypes.MemReadRequest(name=self._property_name)
        resp = await self._rpc.execute(req, self._type)
        return self._convert_from_protocol(resp)

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[TLib]]]:
        yield self._watch_iter()

    async def _watch_iter(self) -> typing.AsyncIterator[Sample[TLib]]:
        last_value: TProtoFrom | None = None

        while True:
            req = rpctypes.RetrieveFromDataStreamRequest(
                name=self._property_name, last_value=last_value.model_dump() if last_value else None
            )
            # we need to pass the runtime type to the WatcherResponse, but because it does not work
            # with TProtoFrom (pydantic fails), we just pass the runtime `self._type` there. That fails on mypy but
            # pydantic works fine, so lets ignore that
            response_model: pydantic.TypeAdapter[list[TProtoFrom]] = pydantic.TypeAdapter(list[self._type])  # type: ignore[name-defined]
            values = await self._rpc.execute(req, response_model)
            last_value = values[-1]
            for value in values:
                yield self._convert_from_protocol(value)

    def _convert_from_protocol(self, val: TProtoFrom) -> Sample[TLib]:
        if isinstance(val, self._type):
            converted_val = self._from_protocol(val)
            if isinstance(val, _HasTimestamp):
                return Sample(converted_val, timestamp=val.timestamp)
            else:
                return Sample.now(converted_val)
        else:
            raise MemoryReadUnsuccessfulError(self._property_name, f"got unexpected type {type(val)}")


class WebDataAccessReadWrite[TProtoFrom: pydantic.BaseModel, TProtoTo, TLib](WebDataAccessRead[TProtoFrom, TLib]):
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
        self._to_protocol = to_protocol
        self._property_key = property_key

    async def write(self, value: TLib) -> None:
        request_params = self._to_protocol(value)
        req = rpctypes.MemWriteRequest(method=f"set_{self._property_name}", **{self._property_key: request_params})
        await self._rpc.execute(req, rpctypes.BaseResponse)


class WebMemoryRegions:
    def __init__(self, rpc: Rpc) -> None:
        self.intersection_queue = EventWatcherQueue(Sample.now(Direction(0)))
        self.intersection = EventWatcher(self.intersection_queue)

        self.color_code_queue = EventWatcherQueue(Sample.now(ColorCode(colors=tuple())))
        self.color_code = EventWatcher(self.color_code_queue)

        self.line_following_speed = WebDataAccessReadWrite(
            rpc,
            "lineNavigationSpeed",
            property_key="speed",
            response_type=rpctypes.ValidatedFloat,
            from_protocol=lambda x: x.root * 1000,
            to_protocol=lambda x: x / 1000,
        )

        self.surface_color = WebDataAccessRead(
            rpc,
            "surfaceColor",
            response_type=rpctypes.ColorResponse,
            from_protocol=lambda x: color_from_web(x.color),
        )

        self.line_color = WebDataAccessRead(
            rpc,
            "lineColor",
            response_type=rpctypes.ColorResponse,
            from_protocol=lambda x: color_from_web(x.color),
        )


class WebDriver:
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
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        req = rpctypes.RotateRequest(
            angle_rad=math.radians(angle_deg),
            angular_speed_radps=math.radians(angular_speed_degps),
        )
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def velocity(self, linear_mmps: float, angular_degps: float, duration_ms: int) -> None:
        req = rpctypes.VelocityRequest(
            linear_speed_mps=linear_mmps / 1000,
            angular_speed_radps=math.radians(angular_degps),
            duration_ms=duration_ms,
        )
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        req = rpctypes.PlayToneRequest(frequency_hz=frequency_hz, duration_ms=duration_ms)
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    # async def play_audio(self, audio_name: str) -> None:
    #     robot specific implementation can be found in ari and evo packages

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        mask_json = led_to_web_json(mask)
        req = rpctypes.SetLedRequest(mask=mask_json, red=red, green=green, blue=blue, alpha=255)
        resp = await self._rpc.execute(req, rpctypes.BaseCallStatusResponse)
        self._validate_response(req.method, resp)

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        way = direction_to_web(direction)
        mode = "Follow" if follow else "DoNotFollow"

        req = rpctypes.LineNavigationRequest(direction=way, follow=mode)
        resp = await self._rpc.execute(req, rpctypes.IntersectionResponse)
        self._validate_response(req.method, resp)
        intersection = intersection_from_web(resp.intersection)
        await self.memory.intersection_queue.write(Sample.now(intersection))

    def _validate_response(
        self, command_name: str, resp: rpctypes.BaseExecutionStateResponse | rpctypes.BaseCallStatusResponse
    ):
        if isinstance(resp, rpctypes.BaseExecutionStateResponse) and resp.execution_state != "FinishedNormal":
            raise DriverCommandFailedError(command_name, resp.execution_state)

        if isinstance(resp, rpctypes.BaseCallStatusResponse) and resp.call_status != "CallSuccess":
            raise DriverCommandFailedError(command_name, resp.call_status)
