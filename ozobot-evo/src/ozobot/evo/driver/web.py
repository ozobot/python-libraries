from ozobot.evo.driver.shared import map_audio_name_to_filename
from ozobot.evo.webprotocol import types as webtypes
from ozobot.web import conversions
from ozobot.web.driver import Rpc, WebDataAccessReadWatch, WebDriver, WebMemoryRegions
from ozobot.web.rpctypes import ReadIrResponse, ValidatedInt, ValidatedNone


class EvoWebMemoryRegions(WebMemoryRegions):
    def __init__(self, rpc: Rpc) -> None:
        super().__init__(rpc)

        self.ir_message_left_rear = WebDataAccessReadWatch(
            rpc,
            "irMessageLeftRear",
            response_type=ReadIrResponse,
            from_protocol=conversions.ir_message_from_web,
        )
        self.ir_message_right_rear = WebDataAccessReadWatch(
            rpc,
            "irMessageRightRear",
            response_type=ReadIrResponse,
            from_protocol=conversions.ir_message_from_web,
        )

        self.proximity_left_rear = WebDataAccessReadWatch(
            rpc,
            "proximityLeftRear",
            response_type=ValidatedInt,
            from_protocol=lambda m: m.root,
        )
        self.proximity_right_rear = WebDataAccessReadWatch(
            rpc,
            "proximityRightRear",
            response_type=ValidatedInt,
            from_protocol=lambda m: m.root,
        )

        self.button = WebDataAccessReadWatch(
            rpc,
            "button",
            response_type=webtypes.ButtonResponse,
            from_protocol=lambda m: m.press,
        )
        self.charger = WebDataAccessReadWatch(
            rpc,
            "charger",
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
        req = webtypes.PlayAudioRequest(
            filename=map_audio_name_to_filename(audio_name),
        )
        _ = await self._rpc.execute(req, ValidatedNone)
