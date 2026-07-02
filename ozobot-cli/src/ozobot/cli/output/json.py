from __future__ import annotations

import json
import typing

from ozobot.ble.datatypes import DeviceDescription


def _serialize(device: DeviceDescription) -> dict[str, typing.Any]:
    payload: dict[str, typing.Any] = {
        "name": device.name,
        "id": device.id,
        "address": device.address,
        "product": device.product,
        "rssi": device.rssi,
    }
    return payload


class JsonFormatter:
    def __init__(self, stream: typing.TextIO) -> None:
        self._stream = stream
        self._items: list[dict[str, typing.Any]] = []
        self._closed = False

    async def __aenter__(self) -> JsonFormatter:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: typing.Any,
    ) -> None:
        json.dump(self._items, self._stream, indent=2)
        self._closed = True

    async def emit(self, data: dict[str, typing.Any]) -> None:
        if self._closed:
            return

        self._items.append(data)
