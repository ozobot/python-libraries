import asyncio
import typing
import uuid

from ozobot.ari.protocol import base, methods, request, types
from ozobot.ari.transport import SerializingTransportLayer
from ozobot.ble.connection import open_client
from ozobot.jsonrpc import executor
from ozobot.webrtc import messaging
from ozobot.webrtc.signaling import negotiation, token


async def main() -> None:
    async with open_client(name="Ari RWMB") as ble_client:
        char = ble_client.get_characteristic(
            uuid.UUID("6b63040a-520e-4d24-0000-65c78f1d0000"),  # taken from anvil-control/src/lib/ble-setup.ts
            uuid.UUID("6b63040a-520e-4d24-0000-65c78f1d0001"),
        )
        device_id_bytes = await char.read()
        device_id = device_id_bytes.decode("utf8")

    jwt = await token.get_jwt_token(token.TOKEN_ENDPOINT_URL, device_id=device_id, mode="server")
    config = messaging.MessagingChannelConfig(device_id=device_id, username="", password=jwt)
    async with messaging.create_channel_factory(config) as channel_factory:
        client = negotiation.SignalingCaller(channel_factory, device_id)

        connection, channels = await client.signal(channels=("control",))

    channel = channels[0]

    class WebrtcTransportAdapter:
        async def write(self, data: str) -> None:
            await channel.send(data)

        async def read(self) -> typing.AsyncIterator[str]:
            async for raw_data in channel.receive_str():
                yield raw_data

    transport = SerializingTransportLayer(WebrtcTransportAdapter())
    async with executor.Executor.create(transport, base.Cancellation) as ex:
        # req = request.RotateRequest(id=1, params=request.RotateRequestParams(angle=90, speed=90))
        # req = request.MoveStraightRequest(id=1, params=request.MoveStraightRequestParams(distance=0.1, speed=0.05))
        # req = request.VelocityRequest(id=1, params=request.VelocityRequestParams(expiration=1, linear_speed=0.1, rotation_speed=0))
        # req = request.LineNavigationRequest(id=1, params=request.LineNavigationRequestParams(direction="Straight", follow="Follow", detect_color_codes=True))
        # req = request.PlayToneRequest(id=1, params=request.PlayToneRequestParams(frequency=1000, duration=1, volume=1))

        req = request.SetLEDRequest(id=1, params=request.SetLEDRequestParams(lights=types.Lights(back=True, top=True, frontCenter=True), color=types.Color(red=0, green=0, blue=255)))
        async with executor.Query(req, methods.SET_LED).execute(ex) as query:
            async def _print_notifications():
                async for n in query.notifications:
                    print(n)

            asyncio.create_task(_print_notifications())
            result = await query.response
            print(result)


asyncio.run(main())
