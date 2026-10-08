import contextlib
import typing
from types import TracebackType

from ozobot.ari.driver import AriDriver, TransportBackend, get_driver
from ozobot.common.sync import as_sync_context_manager
from ozobot.linefollower.api.handle import BaseHandle

from .core import Ari
from .sync import SyncAri


class BaseAriHandle(BaseHandle):
    def __init__(
        self,
        *,
        connection_key: str | None = None,
        transport_backend: TransportBackend = "auto",
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self._connection_key = connection_key
        self._transport_backend = transport_backend

    @property
    def connection_key(self) -> str | None:
        """
        Connection key from the Ari's screen.

        If this field is set, a connection is opened to the specified robot through WiFi (WebRTC). No BLE communication is done.

        .. warning::
            If this field is set, all the other fields are ignored.

        .. warning::
            ``transport_backend`` must be set to ``"webrtc"`` when this field is used.
        """

        return self._connection_key

    @property
    def transport_backend(self) -> TransportBackend:
        """Transport backend used for the connection. Must be ``"webrtc"`` when ``connection_key`` is set."""
        return self._transport_backend


class AriHandle(BaseAriHandle):
    def __init__(
        self,
        *,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
        connection_key: str | None = None,
        transport_backend: TransportBackend = "auto",
    ) -> None:
        super().__init__(
            address=address,
            id=id,
            name=name,
            connection_key=connection_key,
            transport_backend=transport_backend,
        )
        self._exit_stack = contextlib.AsyncExitStack()

    async def __aenter__(self) -> Ari:
        Driver = get_driver()
        # the cast is essential for mypy to correctly infer `enter_async_context` return value
        driver_context = typing.cast(
            contextlib.AbstractAsyncContextManager[AriDriver],
            Driver.open(
                address=self.address,
                id=self.id,
                name=self.name,
                connection_key=self.connection_key,
                transport_backend=self.transport_backend,
            ),
        )

        driver = await self._exit_stack.enter_async_context(driver_context)
        return Ari(driver)

    async def __aexit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        await self._exit_stack.__aexit__(exc_type, exc_val, exc_tb)


class SyncAriHandle(BaseAriHandle):
    def __init__(
        self,
        *,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
        connection_key: str | None = None,
        transport_backend: TransportBackend = "auto",
    ) -> None:
        super().__init__(
            address=address,
            id=id,
            name=name,
            connection_key=connection_key,
            transport_backend=transport_backend,
        )
        self._exit_stack = contextlib.ExitStack()

    def __enter__(self) -> SyncAri:
        async_handle = AriHandle(
            address=self.address,
            id=self.id,
            name=self.name,
            connection_key=self.connection_key,
            transport_backend=self.transport_backend,
        )
        handle_context = self._exit_stack.enter_context(as_sync_context_manager(async_handle))
        return SyncAri(handle_context)

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self._exit_stack.__exit__(exc_type, exc_val, exc_tb)
