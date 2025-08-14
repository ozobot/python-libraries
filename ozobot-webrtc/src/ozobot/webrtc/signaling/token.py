import typing

import aiohttp
from ozobot.webrtc.exceptions import CouldNotGetSignalingTokenError

TOKEN_ENDPOINT_URL = "https://editor.ozobot.com/api/token?kind=amqp"


async def get_jwt_token(endpoint: str, device_id: str, mode: typing.Literal["client", "server"]) -> str:
    async with aiohttp.ClientSession() as session:
        body = {
            "deviceId": device_id,
            "mode": mode,
        }

        async with session.post(endpoint, json=body) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise CouldNotGetSignalingTokenError(resp.status, text)

            return text
