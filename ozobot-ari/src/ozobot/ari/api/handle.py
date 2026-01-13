import contextlib
import typing
from dataclasses import dataclass

from ozobot.ari.driver import AriDriver, get_driver
from ozobot.common.sync import as_sync_context_manager

from .core import Ari
from .sync import SyncAri


@dataclass(frozen=True, kw_only=True)
class AriHandle:
    """
    Factory dataclass for :py:class:`Ari` (asynchronnous variant).

    The instance of this class holds connection filters that describe which robot to connect to. If multiple selectors are
    specified, everyone has to match the same robot. Selector that are not defined (or set to None) are ignored.

    The native Python library only supports WebRTC transport. BLE is only used for scanning and acquiring the connection key.

    Only :py:attr:`name` selector is supported in Web Python.


    .. seealso::
        - :py:class:`SyncAriHandle` to use the synchronnous API
        - :py:class:`ozobot.evo.EvoHandle` or :py:class:`ozobot.evo.SyncEvoHandle` to use Evo
    """

    connection_key: str | None = None
    """
    Connection key from the Ari's screen.

    If this field is set, a connection is open to the specified robot through WiFi (WebRTC). No BLE communication is done.

    .. warning::
        If this field is set, all the other fields are ignored. 
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
    async def connect(self) -> typing.AsyncIterator[Ari]:
        """
        Return :py:class:`Ari` connection context manager.
        """
        Driver = get_driver()
        async with Driver.open(
            address=self.address, id=self.id, name=self.name, connection_key=self.connection_key
        ) as driver:
            ari = Ari(driver)
            yield ari


@dataclass(frozen=True, kw_only=True)
class SyncAriHandle:
    connection_key: str | None = None
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncAri]:
        """
        Return :py:class:`SyncAri` connection context manager.
        """

        Driver = get_driver()
        cm_driver: typing.AsyncContextManager[AriDriver] = Driver.open(address=self.address, id=self.id, name=self.name)
        with as_sync_context_manager(cm_driver) as driver:
            evo = SyncAri(driver)
            yield evo
