import contextlib
import typing
from dataclasses import dataclass

from ozobot.common.sync import as_sync_context_manager
from ozobot.evo.driver import get_driver
from ozobot.linefollower.api.handle import BaseHandle

from .core import Evo
from .sync import SyncEvo


@dataclass(frozen=True, kw_only=True)
class EvoHandle(BaseHandle):
    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Evo]:
        """
        Return :py:class:`Evo` connection context manager.
        """

        Driver = get_driver()
        async with Driver.open(address=self.address, id=self.id, name=self.name) as driver:
            evo = Evo(driver)
            yield evo


@dataclass(frozen=True, kw_only=True)
class SyncEvoHandle(BaseHandle):
    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncEvo]:
        """
        Return :py:class:`SyncEvo` connection context manager.
        """

        cm_evo = EvoHandle(**self.__dict__).connect()
        with as_sync_context_manager(cm_evo) as evo:
            yield SyncEvo(evo)
