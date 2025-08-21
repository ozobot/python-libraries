import contextlib
import typing
from dataclasses import dataclass

from ozobot.ari.driver import get_driver

from .core import Ari


@dataclass(frozen=True, kw_only=True)
class AriHandle:
    connection_key: str | None = None
    address: str | None = None
    id: str | None = None
    name: str | None = None

    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Ari]:
        Driver = get_driver()
        async with Driver.open(
            address=self.address, id=self.id, name=self.name, connection_key=self.connection_key
        ) as driver:
            ari = Ari(driver)
            yield ari
