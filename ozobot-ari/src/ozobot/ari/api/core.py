import typing

from ozobot.ari.driver import AriDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import ClassifiedColor, Direction, Sample, TimeOfFlight
from ozobot.linefollower.driver.interface import ReadableWatchableRegion, VirtualMemoryRegions


class AriVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def time_of_flight(self) -> ReadableWatchableRegion[Sample[TimeOfFlight]]: ...


# this enables verbose errors when memory region implementations do not
# match the interfaces
if typing.TYPE_CHECKING:
    _vm: AriVirtualMemory
    from ozobot.ari.driver.native import NativeMemoryRegions
    from ozobot.ari.driver.web import AriWebMemoryRegions

    _vm = AriWebMemoryRegions()  # type: ignore[call-arg]
    _vm = NativeMemoryRegions()  # type: ignore[call-arg]


class Ari(LineFollower):
    @property
    def data(self) -> AriVirtualMemory:
        return self._ari_driver.memory

    def __init__(self, driver: AriDriver) -> None:
        super().__init__(driver)
        self._ari_driver = driver

    async def user_io_print(self, message: str) -> None:
        await self._ari_driver.user_io_print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False) -> None:
        await self._ari_driver.user_io_alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, ClassifiedColor, Direction)](
        self, message: str, _type: type[T], options: list[T], *, cancellable: bool = False
    ) -> T:
        return await self._ari_driver.user_io_prompt(message, _type, options, cancellable=cancellable)
