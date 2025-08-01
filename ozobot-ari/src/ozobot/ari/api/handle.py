import contextlib
import typing
from dataclasses import dataclass

from ozobot.ari.driver import get_driver
from ozobot.common.sync import as_sync_context_manager

from .core import Ari
# from .sync import AriSync  # TODO


@dataclass(frozen=True, kw_only=True)
class AriHandle:
    connection_key: str | None = None
    address: str | None = None
    id_prefix: str | None = None
    name: str | None = None

    @contextlib.asynccontextmanager
    async def connect(self) -> typing.AsyncIterator[Ari]:
        Driver = get_driver()
        async with Driver.open(address=self.address, id_prefix=self.id_prefix, name=self.name, connection_key=self.connection_key) as driver:
            ari = Ari(driver)
            yield ari


# TODO
# @dataclass(frozen=True, kw_only=True)
# class AriSyncHandle:
#     address: str | None = None
#     id_prefix: str | None = None
#     name: str | None = None

#     @contextlib.contextmanager
#     def connect(self) -> typing.Iterator[EvoSync]:
#         handle = EvoHandle(address=self.address, id_prefix=self.id_prefix, name=self.name)
#         with as_sync_context_manager(handle.connect()) as evo:
#             yield EvoSync(evo)
