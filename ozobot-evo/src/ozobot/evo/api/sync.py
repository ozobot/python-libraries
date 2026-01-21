from ozobot.evo.api.core import Evo
from ozobot.linefollower.api.sync import SyncLineFollower


class SyncEvo(SyncLineFollower):
    def __init__(self, evo: Evo) -> None:
        self._evo = evo
        super().__init__(evo)
