from __future__ import annotations

from _ozo import _rpcCoroutine
from ozobot.actors.actors import context


class Camera:
    """
    Camera actor representation

    .. note::
      `Camera` Python API is experimental and may change
    """

    def __init__(self, name: str):
        self.device_name = name

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def grab_image(self) -> str:
        return await _rpcCoroutine(self.device_name, "grabImage", [])


async def grab_image() -> str:
    """
    Grabs image from camera.

    .. note::
      `grab_image` Python API is experimental and may change
    """
    return await context.dispatcher.acall(Camera.grab_image)
