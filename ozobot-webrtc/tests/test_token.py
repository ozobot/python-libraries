import pytest
import typing
from aiohttp import web
from ozobot.webrtc.exceptions import CouldNotGetSignalingTokenError
from ozobot.webrtc.signaling.token import get_jwt_token


def _token_endpoint_factory(
    response: web.Response,
) -> typing.Callable[[web.Request], typing.Coroutine[None, None, web.Response]]:
    async def _token_endpoint(request: web.Request) -> web.Response:
        json = await request.json()
        assert json["mode"] in {"server", "client"}
        assert "deviceId" in json
        return response

    return _token_endpoint


async def test_get_jwt_token(aiohttp_server) -> None:
    app = web.Application()
    app.router.add_post("/", _token_endpoint_factory(web.Response(text="cHJldGVuZCB0aGlzIGlzIGEgdmFsaWQgand0IHRva2Vu")))
    server = await aiohttp_server(app)
    token = await get_jwt_token(server.make_url("/"), "some-device", "server")
    assert token == "cHJldGVuZCB0aGlzIGlzIGEgdmFsaWQgand0IHRva2Vu"


async def test_get_jwt_token_failing(aiohttp_server) -> None:
    app = web.Application()
    app.router.add_post("/", _token_endpoint_factory(web.Response(text="something really bad happened", status=500)))
    server = await aiohttp_server(app)
    with pytest.raises(CouldNotGetSignalingTokenError):
        _ = await get_jwt_token(server.make_url("/"), "some-device", "server")
