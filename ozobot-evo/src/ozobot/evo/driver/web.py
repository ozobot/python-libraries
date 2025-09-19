from ozobot.evo.driver.shared import map_audio_name_to_filename
from ozobot.evo.webprotocol import types as webtypes
from ozobot.linefollower.api.data_access import DataWatcherProxy
from ozobot.web.driver import Rpc, WebDataAccessRead, WebDriver, WebMemoryRegions
from ozobot.web.rpctypes import BaseExecutionStateResponse


class EvoWebMemoryRegions(WebMemoryRegions):
    def __init__(self, rpc: Rpc) -> None:
        super().__init__(rpc)

        proximity = WebDataAccessRead(
            rpc,
            "irProximity",
            response_type=webtypes.ProximityResponse,
            from_protocol=lambda m: m,
        )

        self.proximity_left_front = DataWatcherProxy(proximity, convert=lambda m: m.left_front)
        self.proximity_right_front = DataWatcherProxy(proximity, convert=lambda m: m.right_front)
        self.proximity_left_rear = DataWatcherProxy(proximity, convert=lambda m: m.left_rear)
        self.proximity_right_rear = DataWatcherProxy(proximity, convert=lambda m: m.right_rear)

        self.ir_message_left_front = WebDataAccessRead(
            rpc,
            "irMessageLeftFront",
            response_type=webtypes.ReadIrResponse,
            from_protocol=lambda m: m.message,
        )
        self.ir_message_right_front = WebDataAccessRead(
            rpc,
            "irMessageRightFront",
            response_type=webtypes.ReadIrResponse,
            from_protocol=lambda m: m.message,
        )
        self.ir_message_left_rear = WebDataAccessRead(
            rpc,
            "irMessageLeftRear",
            response_type=webtypes.ReadIrResponse,
            from_protocol=lambda m: m.message,
        )
        self.ir_message_right_rear = WebDataAccessRead(
            rpc,
            "irMessageRightRear",
            response_type=webtypes.ReadIrResponse,
            from_protocol=lambda m: m.message,
        )

        self.button = WebDataAccessRead(
            rpc,
            "button",
            response_type=webtypes.ButtonResponse,
            from_protocol=lambda m: m.press,
        )
        self.charger = WebDataAccessRead(
            rpc,
            "chargerState",
            response_type=webtypes.ChargerStateResponse,
            from_protocol=lambda m: m.state,
        )


class EvoWebDriver(WebDriver):
    @property
    def memory(self) -> EvoWebMemoryRegions:
        return self._evo_memory

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._evo_memory = EvoWebMemoryRegions(self._rpc)

    async def play_audio(self, audio_name: str) -> None:
        req = webtypes.ExecuteFileRequest(
            filename=f"/system/audio/{map_audio_name_to_filename(audio_name)}.wav",
        )
        resp = await self._rpc.execute(req, BaseExecutionStateResponse)
        self._validate_response(req.method, resp)
