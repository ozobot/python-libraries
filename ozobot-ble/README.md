# ozobot-ble

A Python library for communicating with Ozobot robots via Bluetooth Low Energy (BLE).
This is a backend library implementing bare control over BLE functionality. Consult your robot documentation to learn which user library can control your robot.

See the [monorepo](https://github.com/ozobot/python-libraries) for more details. 

## Features

- BLE device discovery and connection
- Device description parsing from advertisement data
- Built on [bleak](https://github.com/hbldh/bleak)

## Usage

```python
import asyncio
from ozobot.ble import open_client
from ozobot.ble.datatypes import TProductName

async def main() -> None:
  async with open_client(product="evo", name="optional-device-name", id="optional-device-id", address="optional-device-mac") as client:
    char = client.get_characteristic(service_uuid, characteristic_uuid)
    value = await char.read()  # current value
    async with char.open_session() as session:
      await session.write(b"data")
      async for data in session.read():
        print(data)

if __name__ == "__main__":
  asyncio.run(main())
```
