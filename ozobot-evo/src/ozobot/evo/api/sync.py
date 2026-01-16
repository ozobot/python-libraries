from ozobot.evo.api.core import Evo
from ozobot.linefollower.api.sync import (
    SyncLineFollower,
    SyncMemoryRegions,
)


class SyncEvo(SyncLineFollower):
    @property
    def data(self) -> SyncMemoryRegions:
        return SyncMemoryRegions(self._evo)

    def __init__(self, evo: Evo) -> None:
        self._evo = evo
        super().__init__(evo)
