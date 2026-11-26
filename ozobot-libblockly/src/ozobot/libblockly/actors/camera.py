from __future__ import annotations

import sys
import typing

from ozobot.actors.actors import context
from ozobot.common.exceptions import PlatformNotSupportedError
from ozobot.web.browser import _rpcCoroutine


class CameraWebDriver:
    def __init__(self, name: str) -> None:
        self._name = name

    async def grab_image(self) -> str:
        return await _rpcCoroutine(self._name, "grabImage", [])


if typing.TYPE_CHECKING:
    type CameraDriver = CameraWebDriver
else:
    type CameraDriver = typing.Any


def get_driver(name: str) -> CameraDriver:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        return CameraWebDriver(name)
    else:
        raise PlatformNotSupportedError("Camera")


class Camera:
    """
    Camera actor representation

    .. note::
      `Camera` Python API is experimental and may change
    """

    def __init__(self, name: str):
        self.device_name = name
        self._driver = get_driver(name)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def grab_image(self) -> str:
        return await self._driver.grab_image()


async def grab_image() -> str:
    """
    Grabs image from camera.

    .. note::
      `grab_image` Python API is experimental and may change
    """
    return await context.dispatcher.acall(Camera.grab_image)
