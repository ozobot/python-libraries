from __future__ import annotations

import typing

from ozobot.evo.driver import EvoDriver
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import IRMessage, Sample
from ozobot.linefollower.driver.interface import ReadableWatchableRegion, VirtualMemoryRegions


class EvoVirtualMemory(VirtualMemoryRegions, typing.Protocol):
    @property
    def proximity_right_rear(self) -> ReadableWatchableRegion[Sample[float]]: ...

    @property
    def proximity_left_rear(self) -> ReadableWatchableRegion[Sample[float]]: ...

    @property
    def ir_message_left_rear(self) -> ReadableWatchableRegion[Sample[IRMessage]]: ...

    @property
    def ir_message_right_rear(self) -> ReadableWatchableRegion[Sample[IRMessage]]: ...


# this enables verbose errors when memory region implementations do not
# match the interfaces
if typing.TYPE_CHECKING:  # type: ignore[name-defined]
    _vm: EvoVirtualMemory
    from ozobot.evo.driver.native import NativeMemoryRegions
    from ozobot.evo.driver.web import EvoWebMemoryRegions

    _vm = EvoWebMemoryRegions()  # type: ignore[call-arg]
    _vm = NativeMemoryRegions()  # type: ignore[call-arg]


class Evo(LineFollower):
    @property
    def data(self) -> EvoVirtualMemory:
        return self._evo_driver.memory

    def __init__(self, driver: EvoDriver) -> None:
        super().__init__(driver)
        self._evo_driver = driver
