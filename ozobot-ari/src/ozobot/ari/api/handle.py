import contextlib
import typing
from dataclasses import dataclass

from ozobot.ari.driver import get_driver
from ozobot.common.sync import as_sync_context_manager
from ozobot.linefollower.api.handle import BaseHandle

from .core import Ari
from .sync import SyncAri


@dataclass(frozen=True, kw_only=True)
class BaseAriHandle(BaseHandle):
    connection_key: str | None = None
    """
    Connection key from the Ari's screen.

    If this field is set, a connection is open to the specified robot through WiFi (WebRTC). No BLE communication is done.

    .. warning::
        If this field is set, all the other fields are ignored. 
    """


@dataclass(frozen=True, kw_only=True)
class AriHandle(BaseAriHandle):
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
class SyncAriHandle(BaseAriHandle):
    @contextlib.contextmanager
    def connect(self) -> typing.Iterator[SyncAri]:
        """
        Return :py:class:`SyncAri` connection context manager.
        """

        cm_ari = AriHandle(**self.__dict__).connect()
        with as_sync_context_manager(cm_ari) as ari:
            yield SyncAri(ari)
