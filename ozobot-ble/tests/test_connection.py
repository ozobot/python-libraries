import contextlib
import typing
from unittest.mock import AsyncMock, Mock, patch, sentinel
from uuid import UUID

import pytest
from ozobot.ble.connection import (
    Client,
    Characteristic,
    DeviceDescription,
    DeviceNotFoundError,
    open_client,
    scan_devices,
)


async def _mock_advertisement_data() -> typing.AsyncGenerator[tuple[Mock, Mock], None]:
    dev_1 = Mock(
        address="11:22:33:44:55:66",
    )
    dev_1.name = None
    adv_data_1 = Mock(
        manufacturer_data={},
        rssi=-50,
    )

    dev_2 = Mock(
        address="77:88:99:AA:BB:CC",
    )
    dev_2.name = "EVO-123456"
    adv_data_2 = Mock(
        manufacturer_data={
            0x03EB: b"\x00"
            + b"\x00\x01\x02\x03\x04\x05\x06\x07\x00\x01\x02\x03\x04\x05\x06\x07"
            + b"\x00\x00\x00\x00\x00"
            + b"\x04"
            + b"\x05\x06\x07\x00"
        },
        rssi=-60,
    )

    yield dev_1, adv_data_1
    yield dev_2, adv_data_2


def _mock_scanner(scanner_class: AsyncMock) -> None:
    scanner_class().start = AsyncMock()
    scanner_class().stop = AsyncMock()
    scanner_class().advertisement_data = Mock(return_value=_mock_advertisement_data())


async def test_scan_devices() -> None:
    with patch("ozobot.ble.connection.bleak.BleakScanner") as mock_scanner_cls:
        _mock_scanner(mock_scanner_cls)
        async with scan_devices() as device_iter:
            devices = [device async for device in device_iter]

        assert len(devices) == 2
        print(devices[1])
        desc_1, dev_1 = devices[0]
        desc_2, dev_2 = devices[1]

        assert desc_1.name is None
        assert desc_1.address == "11:22:33:44:55:66"
        assert desc_1.product is None

        assert desc_2.name == "EVO-123456"
        assert desc_2.address == "77:88:99:AA:BB:CC"
        assert desc_2.product == "jot15b"
        assert desc_2.id == "00010203040506070001020304050607"
        assert desc_2.version == (5, 6, 7)


@contextlib.asynccontextmanager
async def _scan_devices() -> typing.AsyncGenerator[
    tuple[DeviceDescription, Mock], None
]:
    desc1 = DeviceDescription(
        name="EVO-123456",
        address="11:22:33:44:55:66",
        id="00112233445566778899AABBCCDDEEFF",
        rssi=10,
        version=(10, 20, 30),
        product="jot15b",
    )

    dev1 = sentinel.scanned_device_1

    desc2 = DeviceDescription(
        name="EVO-ABCDEF",
        address="AA:BB:CC:DD:EE:FF",
        id="FFEEDDCCBBAA99887766554433221100",
        rssi=20,
        version=(1, 2, 3),
        product="evo",
    )

    dev2 = sentinel.scanned_device_2

    async def _gen():
        yield desc1, dev1
        yield desc2, dev2

    yield _gen()


@pytest.mark.parametrize(
    argnames=["filters", "expected_device"],
    argvalues=[
        ({"name": "EVO-123456"}, sentinel.scanned_device_1),
        ({"name": "EVO-ABCDEF"}, sentinel.scanned_device_2),
        (
            {
                "name": "EVO-123456",
                "id_prefix": "001122",
                "address": "11:22:33:44:55:66",
            },
            sentinel.scanned_device_1,
        ),
        (
            {"name": "EVO-123456", "id_prefix": "asdf", "address": "11:22:33:44:55:66"},
            None,
        ),
    ],
)
async def test_open_client(
    filters: dict[str, str], expected_device: Mock | None
) -> None:
    with (
        patch("ozobot.ble.connection.bleak.BleakClient") as client_cls,
        patch("ozobot.ble.connection.scan_devices") as scan_devices_func,
    ):
        scan_devices_func.return_value = _scan_devices()
        exception_check = (
            contextlib.nullcontext()
            if expected_device
            else pytest.raises(DeviceNotFoundError)
        )

        with exception_check:
            async with open_client(**filters):
                client_cls.assert_called_once_with(expected_device)


def test_client_get_characteristic():
    svc_uuid = UUID("128a15bd-6340-4d6a-ab5b-3b1d434d3296")
    char_uuid = UUID("658ae4fe-7e98-4bb2-a0c0-0243c00ebdce")
    char2_uuid = UUID("88888888-7e98-4bb2-a0c0-0243c00ebdce")

    bleak_client_mock = Mock()
    client = Client(bleak_client_mock)
    characteristic1 = client.get_characteristic(svc_uuid, char_uuid)
    characteristic1_copy = client.get_characteristic(svc_uuid, char_uuid)

    assert characteristic1 is characteristic1_copy

    characteristic2 = client.get_characteristic(svc_uuid, char2_uuid)
    assert characteristic1 is not characteristic2


def _get_mock_characteristic() -> tuple[Characteristic, Mock]:
    svc_uuid = UUID("128a15bd-6340-4d6a-ab5b-3b1d434d3296")
    char_uuid = UUID("658ae4fe-7e98-4bb2-a0c0-0243c00ebdce")
    bleak_client_mock = AsyncMock()
    bleak_client_mock.services.get_service = Mock()

    char = Characteristic(
        service=svc_uuid, characteristic=char_uuid, client=bleak_client_mock
    )

    return char, bleak_client_mock


async def test_session_open():
    char, bleak_client_mock = _get_mock_characteristic()

    bleak_client_mock.start_notify.assert_not_called()
    bleak_client_mock.stop_notify.assert_not_called()

    async with char.open_session():
        bleak_client_mock.start_notify.assert_awaited_once()
        bleak_client_mock.stop_notify.assert_not_called()

        async with char.open_session():
            bleak_client_mock.start_notify.assert_awaited_once()
            bleak_client_mock.stop_notify.assert_not_called()

        bleak_client_mock.start_notify.assert_awaited_once()
        bleak_client_mock.stop_notify.assert_not_called()

    bleak_client_mock.start_notify.assert_awaited_once()
    bleak_client_mock.stop_notify.assert_awaited_once()


async def test_session_write():
    char, bleak_client_mock = _get_mock_characteristic()

    async with char.open_session() as s1, char.open_session() as s2:
        assert bleak_client_mock.write_gatt_char.call_count == 0
        await s1.write(b"")
        await s2.write(b"")
        assert bleak_client_mock.write_gatt_char.call_count == 2


async def test_session_read():
    char, bleak_client_mock = _get_mock_characteristic()

    async with char.open_session() as s1, char.open_session() as s2:
        await char._notify_callback(char._characteristic_handle, b"hello world")
        read1 = await anext(s1.read())
        read2 = await anext(s2.read())

        assert read1 == b"hello world"
        assert read2 == b"hello world"
