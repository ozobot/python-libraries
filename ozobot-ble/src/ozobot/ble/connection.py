from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass
from uuid import UUID, uuid4

import bleak
from bleak import BleakBackend
from ozobot.ble.datatypes import TProductName
from ozobot.ble.exceptions import DeviceDescriptionError, DeviceNotFoundError, NoFilterSpecifiedError
from ozobot.common.broadcast import BroadcastManager
from ozobot.common.logging import logger
from ozobot.common.match import match_with_wildcard

from .datatypes import DeviceDescription


async def _scan_devices(
    scanner: bleak.BleakScanner,
) -> typing.AsyncIterator[tuple[DeviceDescription, bleak.BLEDevice]]:
    async for ble_device, adv_data in scanner.advertisement_data():
        device = DeviceDescription.parse_from_advertisement_data(ble_device, adv_data)
        logger.debug("Device scanned", device=device, supported=device.product is not None)

        yield device, ble_device


@contextlib.asynccontextmanager
async def scan_devices() -> typing.AsyncIterator[typing.AsyncIterator[tuple[DeviceDescription, bleak.BLEDevice]]]:
    scanner = bleak.BleakScanner()

    logger.debug("Starting BLE scanning")
    await scanner.start()

    try:
        yield _scan_devices(scanner)
    finally:
        logger.debug("Stopping BLE scanning")
        await scanner.stop()


async def _get_device(
    *,
    name: str | None = None,
    address: str | None = None,
    id: str | None = None,
    product: TProductName | None = None,
) -> bleak.BLEDevice:
    async with scan_devices() as devices:
        async for device, handle in devices:
            name_passes = name is None or match_with_wildcard(name, device.name or "")
            address_passes = address is None or match_with_wildcard(address, device.address)
            id_passes = id is None or match_with_wildcard(id, device.id or "")
            product_passes = product is None or device.product == product

            matches = [name_passes, address_passes, id_passes, product_passes]
            if all(matches):
                logger.info("Device scan match", device=device)
                return handle

    raise DeviceNotFoundError()


def _raise_when_no_filter(*filter_values: typing.Any) -> None:
    filter_values_valid = [v is not None for v in filter_values]
    if not any(filter_values_valid):
        raise NoFilterSpecifiedError()


@contextlib.asynccontextmanager
async def open_client(
    *,
    name: str | None = None,
    address: str | None = None,
    id: str | None = None,
    product: TProductName | None = None,
) -> typing.AsyncIterator[Client]:
    _raise_when_no_filter(name, address, id, product)
    handle = await _get_device(name=name, address=address, id=id, product=product)
    logger.info("Opening connection")
    async with bleak.BleakClient(handle) as client:
        # BlueZ doesn't have a proper way to get the MTU, so we have this hack.
        #     see: https://github.com/hbldh/bleak/blob/master/examples/mtu_size.py
        if client.backend_id == BleakBackend.BLUEZ_DBUS:
            await client._backend._acquire_mtu()  # type: ignore
        yield Client(client)
        logger.info("Closing connection")


@dataclass(frozen=True, kw_only=True)
class CharacteristicHandle:
    service: UUID
    characteristic: UUID


class Client:
    def __init__(self, client: bleak.BleakClient) -> None:
        self._client = client
        self._characteristics: dict[CharacteristicHandle, Characteristic] = {}

    def get_characteristic(
        self, service: UUID, characteristic: UUID, mtu_size_override: int | None = None
    ) -> Characteristic:
        with logger.contextualize(service=service, characteristic=characteristic):
            handle = CharacteristicHandle(service=service, characteristic=characteristic)
            if handle in self._characteristics:
                logger.debug("Reusing characteristic")
                char = self._characteristics[handle]
            else:
                logger.debug("Instantiating characteristic")
                char = Characteristic(
                    client=self._client,
                    service=service,
                    characteristic=characteristic,
                    mtu_size_override=mtu_size_override,
                )
                self._characteristics[handle] = char

        return char


class Characteristic:
    @property
    def packet_size_max(self) -> int:
        mtu = self._client.mtu_size if self._mtu_size_override is None else self._mtu_size_override
        return mtu - 3

    def __init__(
        self, *, service: UUID, characteristic: UUID, client: bleak.BleakClient, mtu_size_override: int | None = None
    ) -> None:
        self._notify_lock = asyncio.Lock()
        self._refcount = 0
        self._broadcast = BroadcastManager[bytes]()
        self._client = client
        self._mtu_size_override = mtu_size_override
        self._characteristic_handle = self._get_gatt_characteristic(
            client, service=service, characteristic=characteristic
        )

    async def read(self) -> bytearray:
        return await self._client.read_gatt_char(self._characteristic_handle)

    @contextlib.asynccontextmanager
    async def open_session(self) -> typing.AsyncIterator[Session]:
        with logger.contextualize(session=str(uuid4())):
            logger.debug(
                "Opening session",
                characteristic=self._characteristic_handle.uuid,
                service=self._characteristic_handle.service_uuid,
            )
            await self._subscribe_notifications()
            with self._broadcast.output() as read_queue:
                try:
                    yield Session(read_queue, self._client, self._characteristic_handle)
                finally:
                    await self._unsubscribe_notifications()

    async def _subscribe_notifications(self) -> None:
        async with self._notify_lock:
            self._refcount += 1

            if self._refcount > 1:
                return

            logger.debug("Subscribing")
            await self._client.start_notify(self._characteristic_handle, self._notify_callback)

    async def _unsubscribe_notifications(self) -> None:
        async with self._notify_lock:
            self._refcount -= 1

            if self._refcount < 1:
                logger.debug("Unsubscribing")
                await self._client.stop_notify(self._characteristic_handle)

    def _get_gatt_characteristic(
        self, client: bleak.BleakClient, *, service: UUID, characteristic: UUID
    ) -> bleak.BleakGATTCharacteristic:
        svc = client.services.get_service(service)
        if not svc:
            raise DeviceDescriptionError(f"service not found ({service})")

        char = svc.get_characteristic(characteristic)
        if not char:
            raise DeviceDescriptionError(f"characteristic not found ({characteristic})")

        return char

    async def _notify_callback(self, char: bleak.BleakGATTCharacteristic, data: bytearray) -> None:
        if char == self._characteristic_handle:
            logger.debug("Read data", len=len(data), bytes=data)
            await self._broadcast.broadcast(data)


class Session:
    def __init__(
        self,
        read_queue: asyncio.Queue[bytes],
        client: bleak.BleakClient,
        characteristic: bleak.BleakGATTCharacteristic,
    ):
        self._client = client
        self._characteristic = characteristic
        self._read_queue = read_queue

    async def read(self) -> typing.AsyncIterator[bytes]:
        while True:
            yield bytes(await self._read_queue.get())

    async def write(self, data: bytes) -> None:
        logger.debug("Writting data", len=len(data), bytes=data)
        await self._client.write_gatt_char(self._characteristic, data, response=False)
