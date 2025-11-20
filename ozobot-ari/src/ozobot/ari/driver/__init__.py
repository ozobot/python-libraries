import sys
import typing

from ozobot.linefollower.datatypes import TimeOfFlight
from ozobot.linefollower.driver.interface import Driver, ReadableWatchableRegion, VirtualMemoryRegions
from ozobot.userio.interface import UserIoInterface


class AriVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def time_of_flight(self) -> ReadableWatchableRegion[TimeOfFlight]: ...


class AriDriver(Driver, UserIoInterface, typing.Protocol):
    @property
    def memory(self) -> AriVirtualMemory: ...

    @classmethod
    def open(
        cls,
        *,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
        connection_key: str | None = None,
    ) -> typing.AsyncContextManager[typing.Self]: ...


# this enables verbose errors when memory region implementations do not
# match the interfaces
if typing.TYPE_CHECKING:
    _vm: AriVirtualMemory
    from ozobot.ari.driver.native import NativeMemoryRegions
    from ozobot.ari.driver.web import AriWebMemoryRegions

    _vm = AriWebMemoryRegions()  # type: ignore[call-arg]
    _vm = NativeMemoryRegions()  # type: ignore[call-arg]


def get_driver() -> type[AriDriver]:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        from ozobot.ari.driver.web import AriWebDriver

        return AriWebDriver
    else:
        from ozobot.ari.driver.native import NativeDriver

        return NativeDriver
