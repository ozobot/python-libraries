from __future__ import annotations

from _ozo import _rpcCoroutine
from ozobot.actors.actors import context
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.userio import conversions


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


async def prompt_llm[T: (str, float, int, bool, NamedColor, Direction)](
    _type: type[T], prompt: str, images: list[str]
) -> T:
    return await context.dispatcher.acall(LLMBot.prompt_llm, _type, prompt, images)
