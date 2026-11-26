from __future__ import annotations

import sys
import typing

from ozobot.actors.actors import context
from ozobot.common.exceptions import PlatformNotSupportedError
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.userio import conversions
from ozobot.web.browser import _rpcCoroutine


class LLMWebDriver:
    def __init__(self, name: str) -> None:
        self._name = name

    async def prompt_llm[T: (str, int, float, bool, NamedColor, Direction)](
        self, _type: type[T], prompt: str, images: list[str]
    ) -> T:
        type_str = conversions.get_type_name(_type)
        args = [[str(prompt)], images, type_str]
        result = await _rpcCoroutine(self._name, "prompt_llm", args)
        if issubclass(_type, (NamedColor, Direction)):
            result = result.capitalize()
        return conversions.cast_web_prompt_response(_type, result)


if typing.TYPE_CHECKING:
    type LLMDriver = LLMWebDriver
else:
    type LLMDriver = typing.Any


def get_driver(name: str) -> LLMDriver:
    # don't use if sys.platform directly, mypy will then only check the platform specific branch
    platform: str = sys.platform

    if platform == "emscripten":
        return LLMWebDriver(name)
    else:
        raise PlatformNotSupportedError("LLM")


class LLMBot:
    """
    LLM actor representation

    .. note::
      `LLMBot` Python API is experimental and may change
    """

    def __init__(self, name: str):
        self.device_name = name
        self._driver = get_driver(name)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def prompt_llm[T: (str, int, float, bool, NamedColor, Direction)](
        self, _type: type[T], prompt: str, images: list[str]
    ) -> T:
        return await self._driver.prompt_llm(_type, prompt, images)


async def prompt_llm[T: (str, float, int, bool, NamedColor, Direction)](
    _type: type[T], prompt: str, images: list[str]
) -> T:
    return await context.dispatcher.acall(LLMBot.prompt_llm, _type, prompt, images)
