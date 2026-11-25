from __future__ import annotations

from _ozo import _rpcCoroutine
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.userio import conversions
from ozobot.userio.web import UserIoWebDriverComponent
from ozobot.linefollower.driver.web import Rpc
from ozobot.actors.actors import context


IMPLICIT_BROWSER_TERMINAL_NAME = "BROWSER_TERMINAL"


class BrowserTerminal:
    def __init__(self, name: str = IMPLICIT_BROWSER_TERMINAL_NAME):
        self.device_name = name
        rpc = Rpc(name)
        self._userio_component = UserIoWebDriverComponent(rpc)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def user_io_print(self, message: str):
        return await self._userio_component.print(message)

    async def user_io_alert(self, message: str, *, cancellable: bool = False):
        return await self._userio_component.alert(message, cancellable=cancellable)

    async def user_io_prompt[T: (str, float, int, bool, NamedColor, Direction)](
        self,
        message: str,
        _type: type[T],
        options: list[T],
        *,
        cancellable: bool = False,
    ) -> T:
        return await self._userio_component.prompt(
            message, _type, options, cancellable=cancellable
        )


class LLMBot:
    """
    LLM actor representation

    .. note::
      `LLMBot` Python API is experimental and may change
    """

    def __init__(self, name: str):
        self.device_name = name

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def prompt_llm[T: (str, int, float, bool, NamedColor, Direction)](
        self, _type: type[T], prompt: str, images: list[str]
    ) -> T:
        type_str = conversions.get_type_name(_type)
        args = [[str(prompt)], images, type_str]
        result = await _rpcCoroutine(self.device_name, "prompt_llm", args)
        if issubclass(_type, (NamedColor, Direction)):
            result = result.capitalize()
        return conversions.cast_web_prompt_response(_type, result)


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


async def prompt_llm[T: (str, float, int, bool, NamedColor, Direction)](
    _type: type[T], prompt: str, images: list[str]
) -> T:
    return await context.dispatcher.acall(LLMBot.prompt_llm, _type, prompt, images)


async def grab_image() -> str:
    """
    Grabs image from camera.

    .. note::
      `grab_image` Python API is experimental and may change
    """
    return await context.dispatcher.acall(Camera.grab_image)
