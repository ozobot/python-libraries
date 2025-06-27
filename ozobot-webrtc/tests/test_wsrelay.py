import asyncio
import contextlib
from collections.abc import AsyncIterator, Callable
from unittest.mock import patch

from yarl import URL

from ozobot.webrtc.wsrelay import WebSocketRelay
from .mockserver import MockWebSocketServer


@contextlib.asynccontextmanager
async def _open_with_mock_server(
    unused_tcp_port_factory: Callable[[], int],
) -> AsyncIterator[tuple[MockWebSocketServer, WebSocketRelay, asyncio.StreamReader, asyncio.StreamWriter]]:
    ws_port = unused_tcp_port_factory()
    relay_port = unused_tcp_port_factory()
    async with (
        MockWebSocketServer("localhost", ws_port).serve() as server,
        WebSocketRelay(URL(server.url), relay_port).serve() as relay,
    ):
        reader, writer = await asyncio.open_connection("localhost", relay_port)
        yield server, relay, reader, writer


async def test_relay_reading(unused_tcp_port_factory: Callable[[], int]) -> None:
    async with _open_with_mock_server(unused_tcp_port_factory) as (server, _, reader, _):
        await server.send_to_client("Hello world!\n")
        read = await reader.readline()
    assert read == b"Hello world!\n"


async def test_relay_writing(unused_tcp_port_factory: Callable[[], int]) -> None:
    async with _open_with_mock_server(unused_tcp_port_factory) as (server, _, _, writer):
        writer.write(b"Hello world!")
        async with asyncio.timeout(1):
            read = await server.read_received_from_client()
    assert read == "Hello world!"


async def test_relay_close_websocket_remote(unused_tcp_port_factory: Callable[[], int]) -> None:
    async with _open_with_mock_server(unused_tcp_port_factory) as (server, relay, _, writer):
        await asyncio.sleep(0.1)  # leave time for the relay to connect
        assert relay.num_active_handlers == 1

        # kill the mocked remote to simulate network problems
        server.close()
        await asyncio.sleep(0.1)  # leave time for the handler to close

        assert relay.num_active_handlers == 0


async def test_relay_close_tcp_local(unused_tcp_port_factory: Callable[[], int]) -> None:
    async with _open_with_mock_server(unused_tcp_port_factory) as (server, relay, _, writer):
        await asyncio.sleep(0.1)  # leave time for the relay to connect
        assert relay.num_active_handlers == 1

        # kill the mocked remote to simulate network problems
        writer.close()
        await asyncio.sleep(0.1)  # leave time for the handler to close

        assert relay.num_active_handlers == 0


async def test_relay_proxy_failure(unused_tcp_port_factory: Callable[[], int]) -> None:
    class _InstrumentationError(Exception):
        pass

    with patch("asyncio.streams.StreamWriter.write", side_effect=_InstrumentationError):
        async with _open_with_mock_server(unused_tcp_port_factory) as (server, relay, _, writer):
            await asyncio.sleep(0.1)  # leave time for the relay to connect
            assert relay.num_active_handlers == 1

            await server.send_to_client("Hello")
            await asyncio.sleep(0.1)  # leave time for the handler to fail

            assert relay.num_active_handlers == 0
