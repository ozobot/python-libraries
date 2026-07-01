import asyncio
import contextlib
import typing
from unittest.mock import Mock, patch

import pytest
from ozobot.ari.driver.native import AriNativeDriver
from ozobot.ari.driver.transport import _BleTransport, _create_webrtc_transport, _NoRoutingKeyError
from ozobot.ari.exceptions import BlocklyApplicationNotResponding


class _MockSession:
    def __init__(self, read_queue: asyncio.Queue[bytes] | None = None) -> None:
        self._read_queue = read_queue
        self._written: list[bytes] = []

    async def read(self) -> typing.AsyncIterator[bytes]:
        if self._read_queue is None:
            raise NotImplementedError
        while True:
            yield await self._read_queue.get()

    async def write(self, data: bytes) -> None:
        self._written.append(data)


class _MockStrTransport:
    async def read(self) -> typing.AsyncIterator[str]:
        await asyncio.Future()
        yield ""

    async def write(self, data: str) -> None:
        pass


class _SlowMockSession(_MockSession):
    async def write(self, data: bytes) -> None:
        self._written.append(data)
        await asyncio.sleep(0)


async def test_ble_transport_write() -> None:
    write_session = _MockSession()
    read_session = _MockSession(asyncio.Queue())
    transport = _BleTransport(write_session, read_session, packet_size_max=100)

    await transport.write("hello")

    assert write_session._written == [b"\x00\x00\x00\x05hello"]


async def test_ble_transport_write_chunks() -> None:
    write_session = _MockSession()
    read_session = _MockSession(asyncio.Queue())
    transport = _BleTransport(write_session, read_session, packet_size_max=5)

    await transport.write("hello")

    # Frame is: 4-byte prefix (0x00000005) + "hello" = 9 bytes.
    # With packet_size_max=5 we expect two writes.
    assert write_session._written == [b"\x00\x00\x00\x05h", b"ello"]


async def test_ble_transport_write_is_locked() -> None:
    read_queue = asyncio.Queue[bytes]()
    write_session = _SlowMockSession()
    read_session = _MockSession(read_queue)
    transport = _BleTransport(write_session, read_session, packet_size_max=5)

    await asyncio.gather(transport.write("hello"), transport.write("world"))

    # Each frame is 9 bytes (4-byte prefix + 5-byte payload) and is split into
    # two writes. Without locking the chunks could interleave; with locking each
    # complete frame is written before the next one starts.
    frame1 = b"\x00\x00\x00\x05hello"
    frame2 = b"\x00\x00\x00\x05world"
    option_a = [frame1[:5], frame1[5:], frame2[:5], frame2[5:]]
    option_b = [frame2[:5], frame2[5:], frame1[:5], frame1[5:]]
    assert write_session._written == option_a or write_session._written == option_b


async def test_ble_transport_read() -> None:
    read_queue = asyncio.Queue[bytes]()
    write_session = _MockSession()
    read_session = _MockSession(read_queue)
    transport = _BleTransport(write_session, read_session, packet_size_max=100)

    await read_queue.put(b"\x00\x00\x00\x05hello")

    result = await anext(aiter(transport.read()))
    assert result == "hello"


async def test_ble_transport_read_split_across_chunks() -> None:
    read_queue = asyncio.Queue[bytes]()
    write_session = _MockSession()
    read_session = _MockSession(read_queue)
    transport = _BleTransport(write_session, read_session, packet_size_max=100)

    frame = b"\x00\x00\x00\x05hello"
    await read_queue.put(frame[:5])
    await read_queue.put(frame[5:])

    result = await anext(aiter(transport.read()))
    assert result == "hello"


async def test_ble_transport_read_multiple_messages_in_chunk() -> None:
    read_queue = asyncio.Queue[bytes]()
    write_session = _MockSession()
    read_session = _MockSession(read_queue)
    transport = _BleTransport(write_session, read_session, packet_size_max=100)

    frame = b"\x00\x00\x00\x05hello" + b"\x00\x00\x00\x05world"
    await read_queue.put(frame)

    it = aiter(transport.read())
    assert await anext(it) == "hello"
    assert await anext(it) == "world"


async def test_open_uses_ble_backend() -> None:
    mock_transport = _MockStrTransport()

    @contextlib.asynccontextmanager
    async def _mock_ble_transport(*, address, id, name, client=None):
        yield mock_transport

    with patch(
        "ozobot.ari.driver.transport._create_ble_transport", side_effect=_mock_ble_transport
    ) as ble_transport_mock:
        with patch("ozobot.ari.driver.transport._create_webrtc_transport") as webrtc_transport_mock:
            async with AriNativeDriver.open(
                address="11:22:33:44:55:66", id="1234", name="ARI-ABCDEF", transport_backend="ble"
            ) as driver:
                assert isinstance(driver, AriNativeDriver)
                ble_transport_mock.assert_called_once_with(address="11:22:33:44:55:66", id="1234", name="ARI-ABCDEF")
                webrtc_transport_mock.assert_not_called()


async def test_open_uses_webrtc_backend() -> None:
    mock_transport = _MockStrTransport()

    @contextlib.asynccontextmanager
    async def _mock_webrtc_transport(*, address, id, name, connection_key):
        yield mock_transport

    with patch(
        "ozobot.ari.driver.transport._create_webrtc_transport", side_effect=_mock_webrtc_transport
    ) as webrtc_transport_mock:
        with patch("ozobot.ari.driver.transport._create_ble_transport") as ble_transport_mock:
            async with AriNativeDriver.open(connection_key="1234abcd", transport_backend="webrtc") as driver:
                assert isinstance(driver, AriNativeDriver)
                webrtc_transport_mock.assert_called_once_with(
                    address=None,
                    id=None,
                    name=None,
                    connection_key="1234abcd",
                )
                ble_transport_mock.assert_not_called()


async def test_open_auto_uses_webrtc_when_routing_key_valid() -> None:
    mock_transport = _MockStrTransport()
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    @contextlib.asynccontextmanager
    async def _mock_from_key(routing_key: str):
        yield mock_transport

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch(
            "ozobot.ari.driver.transport._fetch_routing_key_with_timeout", return_value="anvil.testkey"
        ) as fetch_mock:
            with patch(
                "ozobot.ari.driver.transport._webrtc_transport_from_routing_key", side_effect=_mock_from_key
            ) as from_key_mock:
                with patch("ozobot.ari.driver.transport._create_ble_transport_from_client") as ble_mock:
                    async with AriNativeDriver.open(
                        address="11:22:33:44:55:66", id="1234", name="ARI-ABCDEF"
                    ) as driver:
                        assert isinstance(driver, AriNativeDriver)
                    fetch_mock.assert_called_once_with(mock_client)
                    from_key_mock.assert_called_once_with("anvil.testkey")
                    ble_mock.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        _NoRoutingKeyError("routing key unavailable"),
        _NoRoutingKeyError("empty routing key"),
        BlocklyApplicationNotResponding(),
    ],
)
async def test_open_auto_falls_back_to_ble_when_routing_key_fetch_fails(failure: Exception) -> None:
    mock_transport = _MockStrTransport()
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    @contextlib.asynccontextmanager
    async def _mock_ble_from_client(ble_client):
        yield mock_transport

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch(
            "ozobot.ari.driver.transport._fetch_routing_key_with_timeout",
            side_effect=failure,
        ):
            with patch(
                "ozobot.ari.driver.transport._create_ble_transport_from_client",
                side_effect=_mock_ble_from_client,
            ) as ble_mock:
                with patch("ozobot.ari.driver.transport._webrtc_transport_from_routing_key") as from_key_mock:
                    async with AriNativeDriver.open(
                        address="11:22:33:44:55:66", id="1234", name="ARI-ABCDEF"
                    ) as driver:
                        assert isinstance(driver, AriNativeDriver)
                    ble_mock.assert_called_once_with(mock_client)
                    from_key_mock.assert_not_called()


async def test_open_auto_propagates_when_webrtc_fails() -> None:
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    @contextlib.asynccontextmanager
    async def _failing_webrtc(routing_key: str):
        raise RuntimeError("webrtc failed")
        yield  # pragma: no cover

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch("ozobot.ari.driver.transport._fetch_routing_key_with_timeout", return_value="anvil.testkey"):
            with patch("ozobot.ari.driver.transport._webrtc_transport_from_routing_key", side_effect=_failing_webrtc):
                with patch("ozobot.ari.driver.transport._create_ble_transport_from_client") as ble_mock:
                    with pytest.raises(RuntimeError, match="webrtc failed"):
                        async with AriNativeDriver.open(address="11:22:33:44:55:66", id="1234", name="ARI-ABCDEF"):
                            pass
                    ble_mock.assert_not_called()


async def test_create_webrtc_transport_with_connection_key() -> None:
    mock_transport = _MockStrTransport()

    @contextlib.asynccontextmanager
    async def _mock_from_key(routing_key: str):
        yield mock_transport

    with patch(
        "ozobot.ari.driver.transport._webrtc_transport_from_routing_key", side_effect=_mock_from_key
    ) as from_key_mock:
        async with _create_webrtc_transport(connection_key="1234abcd") as transport:
            assert transport is mock_transport
        from_key_mock.assert_called_once_with("anvil.1234abcd")


async def test_create_webrtc_transport_auto_blocking_valid_key() -> None:
    mock_transport = _MockStrTransport()
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    @contextlib.asynccontextmanager
    async def _mock_from_key(routing_key: str):
        yield mock_transport

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch(
            "ozobot.ari.driver.transport._fetch_routing_key_with_timeout", return_value="anvil.testkey"
        ) as fetch_mock:
            with patch(
                "ozobot.ari.driver.transport._webrtc_transport_from_routing_key", side_effect=_mock_from_key
            ) as from_key_mock:
                async with _create_webrtc_transport(address="11:22:33:44:55:66") as transport:
                    assert transport is mock_transport
                fetch_mock.assert_called_once_with(mock_client)
                from_key_mock.assert_called_once_with("anvil.testkey")


async def test_create_webrtc_transport_auto_blocking_unavailable_key() -> None:
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch(
            "ozobot.ari.driver.transport._fetch_routing_key_with_timeout",
            side_effect=_NoRoutingKeyError("routing key unavailable"),
        ):
            with patch("ozobot.ari.driver.transport._webrtc_transport_from_routing_key") as from_key_mock:
                with pytest.raises(_NoRoutingKeyError):
                    async with _create_webrtc_transport(address="11:22:33:44:55:66"):
                        pass
                from_key_mock.assert_not_called()


async def test_create_webrtc_transport_timeout() -> None:
    mock_client = Mock()

    @contextlib.asynccontextmanager
    async def _mock_open_client(**kwargs):
        yield mock_client

    async def _slow_fetch(ble_client):
        await asyncio.sleep(10)
        return "anvil.never"

    with patch("ozobot.ari.driver.transport.open_client", side_effect=_mock_open_client):
        with patch("ozobot.ari.driver.transport._ROUTING_KEY_FETCH_TIMEOUT_S", 0.1):
            with patch("ozobot.ari.driver.transport._fetch_routing_key", side_effect=_slow_fetch):
                with patch("ozobot.ari.driver.transport._webrtc_transport_from_routing_key") as from_key_mock:
                    with pytest.raises(_NoRoutingKeyError):
                        async with _create_webrtc_transport(address="11:22:33:44:55:66"):
                            pass
                    from_key_mock.assert_not_called()
