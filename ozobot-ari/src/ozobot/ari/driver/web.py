from ozobot.ari.driver.shared import geometry
from ozobot.ari.driver.web_conversions import time_of_flight_from_web
from ozobot.ari.webprotocol import types as webtypes
from ozobot.linefollower.datatypes import Direction, NamedColor, Sample
from ozobot.linefollower.driver.web import (
    LineFollowerWebDriver,
    Rpc,
    WebMemoryRegions,
)
from ozobot.linefollower.driver.web.driver import WebDataAccessWatch
from ozobot.userio.web import UserIoWebDriverComponent


class AriWebMemoryRegions(WebMemoryRegions):
    def __init__(self, rpc: Rpc) -> None:
        super().__init__(rpc)

        self.time_of_flight = WebDataAccessWatch(
            rpc,
            "timeOfFlight",
            response_type=webtypes.TimeOfFlightResponse,
            from_protocol=lambda t: Sample(time_of_flight_from_web(t), t.timestamp),
        )

        self.geometry = geometry


class AriWebDriver(LineFollowerWebDriver):
    @property
    def memory(self) -> AriWebMemoryRegions:
        return self._ari_memory

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self._userio_component = UserIoWebDriverComponent(self._rpc)
        self._ari_memory = AriWebMemoryRegions(self._rpc)

    async def user_io_print(self, message: str) -> None:
        return await self._userio_component.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        return await self._userio_component.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._userio_component.prompt(message, _type, options, cancellable=cancellable)
