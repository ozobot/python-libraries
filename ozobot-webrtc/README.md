# ozobot-webrtc

A Python library for establishing WebRTC connections with Ozobot devices, enabling real-time communication through data channels.
This is a backend library implementing bare WebRTC functionality. Consult your robot documentation to learn which user library can control your robot.

## Features

- WebRTC peer-to-peer connections with Ozobot devices
- AMQP-based signaling through WebSocket or TCP transports to estabilish the connection
- Built on [aiortc](github.com/aiortc/aiortc) for WebRTC functionality

## Basic Usage

```python
import asyncio

from ozobot.webrtc.signaling import SignalingCaller
from ozobot.webrtc.messaging import create_channel_factory, MessagingChannelConfig

async def main() -> None:
  # Configure messaging
  config = MessagingChannelConfig(
    device_id="your-connection-key",
    username="your-username", 
    password="your-password"
  )

  # Establish connection
  async with create_channel_factory(config) as factory:
    caller = SignalingCaller(factory, "your-queue-name")
    connection, channels = await caller.signal(channels=("control",))

    # Use the data channels
    data_channel = channels[0]
    await data_channel.send(b"Hello Ozobot!")

    async for data in channel.receive_str():
      print(data)


if __name__ == "__main__":
    asyncio.run(main())
```

## jwt authentication
If you don't have an username and password, you need to use jwt for authentication. In that case, use `get_jwt_token` from `ozobot.webrtc.signaling.token`
and use the resulting value as password. Keep username empty:
```python
from ozobot.webrtc.signaling.token import get_jwt_token, TOKEN_ENDPOINT_URL
await token = await get_jwt_token(TOKEN_ENDPOINT_URL, "your-connection-key", "server")
config = MessagingChannelConfig(
    device_id="your-connection-key",
    username="", 
    password=token,
)
```
