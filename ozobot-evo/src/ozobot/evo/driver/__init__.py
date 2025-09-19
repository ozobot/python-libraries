import sys
import typing

from ozobot.linefollower.datatypes import IRMessage
from ozobot.linefollower.driver.interface import Driver, ReadableWatchableRegion, VirtualMemoryRegions

__all__ = ["get_driver"]


class EvoVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def ir_message_left_rear(self) -> ReadableWatchableRegion[IRMessage]: ...

    @property
    def ir_message_right_rear(self) -> ReadableWatchableRegion[IRMessage]: ...

    @property
    def charger(self) -> ReadableWatchableRegion[typing.Literal["Connected", "Disconnected", "LowPower"]]: ...

    @property
    def button(self) -> ReadableWatchableRegion[bool]: ...


class EvoDriver(Driver, typing.Protocol):
    @property
    def memory(self) -> EvoVirtualMemory: ...

    @classmethod
    def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncContextManager[typing.Self]: ...

    async def stop_all(self): ...


def get_driver() -> type[EvoDriver]:
    if sys.platform == "emscripten":
        from ozobot.evo.driver.web import EvoWebDriver

        return EvoWebDriver
    else:
        from ozobot.evo.driver.native import NativeDriver

        return NativeDriver
