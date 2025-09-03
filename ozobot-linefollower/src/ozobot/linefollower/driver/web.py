import contextlib
import typing

from loguru import logger
from ozobot.linefollower.conversions import led_to_web_json
from ozobot.linefollower.datatypes import Direction, LEDMask

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


class WebDriver:
    def __init__(self, name: str) -> None:
        self._name = name
        self.memory = None

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncIterator[typing.Self]:
        if id:
            raise NotImplementedError("Web driver cannot select robots by their ID")

        if address:
            raise NotImplementedError("Web driver cannot select robots by their address")

        if not name:
            raise ValueError("Robot name missing")

        yield cls(name)

    async def _rpc(self, func_name: str, args: list[typing.Any] | None = None) -> typing.Any:
        ret = await _rpcCoroutine(self._name, func_name, args or [])
        print(func_name, "returned", ret)  # TODO: check
        return ret

    async def move(self, distance_m: float, speed_ms: float) -> None:
        await self._rpc("MoveStraight", [distance_m, speed_ms])

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None:
        await self._rpc("Rotate", [angle_rad, angular_speed_radps])

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None:
        await self._rpc("Velocity", [linear_mps, angular_radps, duration_ms])

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        await self._rpc("PlayTone", [frequency_hz, duration_ms])

    # async def play_audio(self, audio_name: str) -> None:
    #     robot specific implementation in ari and evo packages

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        mask_json = led_to_web_json(mask)
        await self._rpc("SetLED", [mask_json, red, green, blue, 255])

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        way = direction_to_web_direction(direction)
        mode = "Follow" if follow else "DoNotFollow"
        
        ret = await self._rpc("LineNavigation", [way, mode])
        intersection = intersection_from_web(ret["intersection"])
        # TODO: notification
        
    async def stop_all(self) -> None:
        await self._rpc("StopExecution")
