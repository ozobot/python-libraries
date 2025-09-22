from ozobot.ari import conversions
from ozobot.ari.webprotocol import types as webtypes
from ozobot.linefollower.datatypes import Color, Direction
from ozobot.userio.web import UserIoWebDriverComponent
from ozobot.web import rpctypes
from ozobot.web.driver import Rpc, WebDataAccessRead, WebDriver, WebMemoryRegions


class AriWebMemoryRegions(WebMemoryRegions):
    def __init__(self, rpc: Rpc) -> None:
        super().__init__(rpc)

        self.proximity_left_front = WebDataAccessRead(
            rpc,
            "proximityLeft",
            response_type=webtypes.ProximityResponse,
            from_protocol=lambda m: m.value,
        )
        self.proximity_right_front = WebDataAccessRead(
            rpc,
            "proximityRight",
            response_type=webtypes.ProximityResponse,
            from_protocol=lambda m: m.value,
        )
        self.proximity_left_rear = WebDataAccessRead(
            rpc,
            "proximityEdgeLeft",
            response_type=webtypes.ProximityResponse,
            from_protocol=lambda m: m.value,
        )
        self.proximity_right_rear = WebDataAccessRead(
            rpc,
            "proximityEdgeRight",
            response_type=webtypes.ProximityResponse,
            from_protocol=lambda m: m.value,
        )

        self.ir_message_left_front = WebDataAccessRead(
            rpc,
            "readIrLeft",
            response_type=webtypes.ReadIrResponse,
            from_protocol=conversions.ir_message_from_web,
        )
        self.ir_message_right_front = WebDataAccessRead(
            rpc,
            "readIrRight",
            response_type=webtypes.ReadIrResponse,
            from_protocol=conversions.ir_message_from_web,
        )

        self.time_of_flight = WebDataAccessRead(
            rpc,
            "timeOfFlight",
            response_type=webtypes.TimeOfFlightResponse,
            from_protocol=conversions.time_of_flight_from_web,
        )


class AriWebDriver(WebDriver):
    @property
    def memory(self) -> AriWebMemoryRegions:
        return self._ari_memory

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._userio_component = UserIoWebDriverComponent(self._rpc)
        self._ari_memory = AriWebMemoryRegions(self._rpc)

    async def play_audio(self, audio_name: str) -> None:
        req = webtypes.ExecuteFileRequest(filename=audio_name)
        resp = await self._rpc.execute(req, rpctypes.BaseExecutionStateResponse)
        self._validate_response(req.method, resp)

    async def user_io_print(self, message: str) -> None:
        return await self._userio_component.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        return await self._userio_component.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, Color, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._userio_component.prompt(message, _type, options, cancellable=cancellable)
