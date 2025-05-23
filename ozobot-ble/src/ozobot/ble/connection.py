from __future__ import annotations

import asyncio
import contextlib
import typing
from dataclasses import dataclass
from uuid import UUID, uuid4

import bleak
from loguru import logger

from ozobot.common.broadcast import BroadcastManager

from .datatypes import DeviceDescription


class BLEError(Exception): ...


class DeviceNotFoundError(BLEError): ...


class DeviceDescriptionError(BLEError):
    def __init__(self, reason: str):
        super().__init__(f"Device description does not match the expected one: {reason}")


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
    id_prefix: str | None = None,
) -> bleak.BLEDevice:
    async with scan_devices() as devices:
        async for device, handle in devices:
            normalized_id = device.id or ""

            name_match = name is None or device.name == name
            address_match = address is None or device.address == address
            id_match = id_prefix is None or normalized_id.startswith(id_prefix)

            if name_match and address_match and id_match:
                logger.info("Device scan match", device=device)
                return handle

    raise DeviceNotFoundError("Device with given parameters could not be found")


@contextlib.asynccontextmanager
async def open_client(
    *,
    name: str | None = None,
    address: str | None = None,
    id_prefix: str | None = None,
) -> typing.AsyncIterator[Client]:
    handle = await _get_device(name=name, address=address, id_prefix=id_prefix)
    logger.info("Opening connection")
    async with bleak.BleakClient(handle) as client:
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

    def get_characteristic(self, service: UUID, characteristic: UUID) -> Characteristic:
        with logger.contextualize(service=service, characteristic=characteristic):
            handle = CharacteristicHandle(service=service, characteristic=characteristic)
            if handle in self._characteristics:
                logger.debug("Reusing characteristic")
                char = self._characteristics[handle]
            else:
                logger.debug("Instantiating characteristic")
                char = Characteristic(client=self._client, service=service, characteristic=characteristic)
                self._characteristics[handle] = char

        return char


class Characteristic:
    @property
    def packet_size_max(self) -> int:
        return self._characteristic_handle.max_write_without_response_size

    def __init__(self, *, service: UUID, characteristic: UUID, client: bleak.BleakClient) -> None:
        self._notify_lock = asyncio.Lock()
        self._refcount = 0
        self._broadcast = BroadcastManager[bytes]()
        self._client = client
        self._characteristic_handle = self._get_gatt_characteristic(
            client, service=service, characteristic=characteristic
        )

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
            try:
                data = bytes(await self._read_queue.get())
            except asyncio.CancelledError:
                return
            yield data

    async def write(self, data: bytes) -> None:
        logger.debug("Writting data", len=len(data), bytes=data)
        await self._client.write_gatt_char(self._characteristic, data, response=False)
