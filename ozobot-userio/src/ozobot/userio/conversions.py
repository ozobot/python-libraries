import typing

from ozobot.linefollower import conversions as lf_conversions
from ozobot.linefollower.datatypes import Color, Direction, TDirection, TNamedColor
from ozobot.userio.datatypes import TUserIoPrompt
from ozobot.userio.exceptions import (
    UnexpectedUserIoPromptOptionTypeError,
    UnexpectedUserIoPromptResponseReceivedError,
    UnexpectedUserIoPromptTypeError,
)
from ozobot.web import conversions as web_conversions


def get_type_name(_type: type[str | int | float | bool | Color | Direction]) -> TUserIoPrompt:
    if _type == str:
        return "string"
    elif _type == int or _type == float:
        return "number"
    elif _type == bool:
        return "boolean"
    elif _type == Color:
        return "surfaceColor"
    elif _type == Direction:
        return "direction"
    else:
        raise UnexpectedUserIoPromptTypeError(_type)


def get_type_options[T: (str, float, int, bool, Color, Direction)](
    options: list[T], _type: type[T]
) -> list[str | float | int | bool | TNamedColor | TDirection]:
    for opt in options:
        if not isinstance(opt, _type):
            raise UnexpectedUserIoPromptOptionTypeError(opt, _type)

    protocol_options: list[str | float | int | bool | TNamedColor | TDirection] = []
    for opt in options:
        if isinstance(opt, Color):
            protocol_options.append(web_conversions.color_to_web(opt))
        elif isinstance(opt, Direction):
            protocol_options.append(web_conversions.direction_to_web(opt))
        else:
            protocol_options.append(opt)

    return protocol_options


def cast_web_prompt_response[T](_type: type[T], value: typing.Any) -> T:
    if _type is str:
        return typing.cast(T, value)
    elif _type is int:
        return typing.cast(T, int(value))
    elif _type is float:
        return typing.cast(T, float(value))
    elif _type is bool:
        return typing.cast(T, bool(value))
    elif _type is Color and lf_conversions.is_named_color(value):
        return typing.cast(T, web_conversions.color_from_web(value))
    elif _type is Direction and web_conversions.is_named_web_direction(value):
        return typing.cast(T, web_conversions.direction_from_web(value))
    else:
        raise UnexpectedUserIoPromptResponseReceivedError(value, _type)
