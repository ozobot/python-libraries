from ozobot.evo.api.core import Evo
from ozobot.linefollower.api.sync import SyncLineFollower, SyncMemoryRegions


class SyncEvoVirtualMemory(SyncMemoryRegions): ...


class SyncEvo(SyncLineFollower):
    @property
    def data(self) -> SyncEvoVirtualMemory:
        """
        Robot sensors.

        Contains virtual memory and sensor structures allowing a subset of read, write and watch methods.
        """

        return SyncEvoVirtualMemory(self._evo)

    def __init__(self, evo: Evo) -> None:
        self._evo = evo
        super().__init__(evo)
