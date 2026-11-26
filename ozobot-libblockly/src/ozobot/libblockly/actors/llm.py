from __future__ import annotations

import sys
import typing

import pydantic
from ozobot.actors.actors import context
from ozobot.common.exceptions import PlatformNotSupportedError
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.linefollower.driver.web import Rpc, rpctypes
from ozobot.userio import conversions
from ozobot.userio.datatypes import TUserIoPrompt


class PromptLLMRequest(rpctypes.BaseRequest):
    method: typing.Literal["prompt_llm"] = "prompt_llm"
    prompt: str
    images: list[str]
    type: TUserIoPrompt

    @property
    def args(self) -> tuple:
        return ([self.prompt], self.images, self.type)


class LLMWebDriver:
    def __init__(self, name: str) -> None:
        self._rpc = Rpc(name)

    async def prompt_llm[T: (str, int, float, bool, NamedColor, Direction)](
        self, _type: type[T], prompt: str, images: list[str]
    ) -> T:
        req = PromptLLMRequest(prompt=str(prompt), images=images, type=conversions.get_type_name(_type))
        response_model: pydantic.TypeAdapter[str | float | bool | None] = pydantic.TypeAdapter(
            str | float | bool | None
        )
        response = await self._rpc.execute(req, response_model)
        if issubclass(_type, (NamedColor, Direction)) and isinstance(response, str):
            response = response.capitalize()
        return conversions.cast_web_prompt_response(_type, response)


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
