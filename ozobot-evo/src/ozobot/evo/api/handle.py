import contextlib
import typing
from dataclasses import dataclass

from ozobot.common.sync import as_sync_context_manager
from ozobot.evo.driver import EvoDriver, get_driver

from .core import Evo
from .sync import SyncEvo


@dataclass(frozen=True, kw_only=True)
class EvoHandle:
    """
    Factory dataclass for :py:class:`Evo` (asynchronnous variant).

    The instance of this class holds connection filters that describe which robot to connect to. If multiple selectors are
    specified, everyone has to match the same robot. Selector that are not defined (or set to None) are ignored.

    Only :py:attr:`name` selector is supported in Web Python.


    .. seealso::
        - :py:class:`ozobot.evo.SyncEvoHandle` to use the synchronnous API
        - :py:class:`ozobot.ari.AriHandle` or :py:class:`ozobot.ari.SyncAriHandle` to use Ari
    """

    address: str | None = None
    """
    BLE MAC address of the robot.

    Accepts wildmark '*' character that matches any string.
    """

    id: str | None = None
    """
    Robot ID.

    Accepts wildmark '*' character that matches any string.
    """

    name: str | None = None
    """
    Robot BLE name.

    Accepts wildmark '*' character that matches any string.
    """

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
class SyncEvoHandle:
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncEvo]:
        """
        Return :py:class:`SyncEvo` connection context manager.
        """

        Driver = get_driver()
        cm_driver: typing.AsyncContextManager[EvoDriver] = Driver.open(address=self.address, id=self.id, name=self.name)
        with as_sync_context_manager(cm_driver) as driver:
            evo = SyncEvo(driver)
            yield evo
