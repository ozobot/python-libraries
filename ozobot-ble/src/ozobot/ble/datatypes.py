from __future__ import annotations

import typing
from dataclasses import dataclass

from bleak import AdvertisementData, BLEDevice

ProductName = typing.Literal["evo", "jot15b"]

_products: dict[int, ProductName] = {
    0: "evo",
    4: "jot15b",
}


@dataclass(kw_only=True, frozen=True)
class DeviceDescription:
    name: str | None
    address: str
    product: ProductName | None
    version: tuple[int, int, int] | None
    id: str | None
    rssi: int | None

    @classmethod
    def parse_from_advertisement_data(cls, device: BLEDevice, adv_data: AdvertisementData) -> DeviceDescription:
        VENDOR_ID: int = int("03eb", 16)
        PACKET_ID: int = 0

        manufacturer_data = adv_data.manufacturer_data.get(VENDOR_ID, bytes())

        if manufacturer_data and manufacturer_data[0] == PACKET_ID and len(manufacturer_data) > 24:
            device_id = manufacturer_data[1:17].hex().upper()
            product = _products.get(manufacturer_data[22], None)

            version = (
                int(manufacturer_data[23]) & 0b0111_1111,
                int(manufacturer_data[24]),
                int.from_bytes(manufacturer_data[25:27], "little") if len(manufacturer_data[23:27]) == 4 else 0,
            )
        else:
            device_id = None
            version = None
            product = None

        return DeviceDescription(
            name=device.name,
            address=device.address,
            rssi=adv_data.rssi,
            id=device_id,
            version=version,
            product=product,
        )
