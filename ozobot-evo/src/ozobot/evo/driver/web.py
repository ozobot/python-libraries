from ozobot.evo.driver.shared import geometry
from ozobot.evo.webprotocol import types as webtypes
from ozobot.linefollower.datatypes import Sample
from ozobot.linefollower.driver.web import (
    LineFollowerWebDriver,
    Rpc,
    WebDataAccessReadWatch,
    WebMemoryRegions,
    rpctypes,
)
from ozobot.linefollower.driver.web.conversions import ir_message_from_web


class EvoWebMemoryRegions(WebMemoryRegions):
    def __init__(self, rpc: Rpc) -> None:
        super().__init__(rpc)

        self.ir_message_left_rear = WebDataAccessReadWatch(
            rpc,
            "irMessageLeftRear",
            response_type=rpctypes.ReadIrResponse,
            from_protocol=lambda m: Sample(ir_message_from_web(m), m.timestamp),
        )
        self.ir_message_right_rear = WebDataAccessReadWatch(
            rpc,
            "irMessageRightRear",
            response_type=rpctypes.ReadIrResponse,
            from_protocol=lambda m: Sample(ir_message_from_web(m), m.timestamp),
        )

        self.obstacle_left_rear = WebDataAccessReadWatch(
            rpc,
            "proximityLeftRear",
            response_type=rpctypes.IrProximityResponse,
            from_protocol=lambda m: Sample(m.value, m.timestamp),
        )
        self.obstacle_right_rear = WebDataAccessReadWatch(
            rpc,
            "proximityRightRear",
            response_type=rpctypes.IrProximityResponse,
            from_protocol=lambda m: Sample(m.value, m.timestamp),
        )

        self.button = WebDataAccessReadWatch(
            rpc,
            "button",
            response_type=webtypes.ButtonResponse,
            from_protocol=lambda m: Sample(m.press, m.timestamp),
        )
        self.charger = WebDataAccessReadWatch(
            rpc,
            "charger",
            response_type=webtypes.ChargerStateResponse,
            from_protocol=lambda m: Sample(m.state, m.timestamp),
        )

        self.geometry = geometry


class EvoWebDriver(LineFollowerWebDriver):
    @property
    def memory(self) -> EvoWebMemoryRegions:
        return self._evo_memory

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._evo_memory = EvoWebMemoryRegions(self._rpc)
