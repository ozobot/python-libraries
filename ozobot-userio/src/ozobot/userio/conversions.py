import typing

from ozobot.linefollower.datatypes import Direction, NamedColor, TDirection, TNamedColor
from ozobot.linefollower.driver.web import conversions as web_conversions
from ozobot.linefollower.driver.web.rpctypes import TWebDirection
from ozobot.linefollower.exceptions import InvalidNamedColorError
from ozobot.userio.datatypes import TAriUserIoPromptDirections, TUserIoPrompt, TWebUserIoPrompt
from ozobot.userio.exceptions import (
    UnexpectedUserIoPromptOptionTypeError,
    UnexpectedUserIoPromptResponseReceivedError,
    UnexpectedUserIoPromptTypeError,
)


def color_to_protocol(color: NamedColor) -> TNamedColor:
    if color == NamedColor.GREEN:
        return "Green"
    elif color == NamedColor.BLACK:
        return "Black"
    elif color == NamedColor.RED:
        return "Red"
    elif color == NamedColor.BLUE:
        return "Blue"
    elif color == NamedColor.WHITE:
        return "White"

    raise InvalidNamedColorError(color)


def get_type_name(_type: type[str | int | float | bool | NamedColor | Direction]) -> TUserIoPrompt:
    if _type == str:
        return "string"
    elif any(issubclass(c, _type) for c in [float, int]):
        return "number"
    elif _type == bool:
        return "boolean"
    elif _type == NamedColor:
        return "surfaceColor"
    elif _type == Direction:
        return "direction"
    else:
        raise UnexpectedUserIoPromptTypeError(_type)


def native_intersection_direction_to_protocol(direction: Direction) -> TAriUserIoPromptDirections:
    if not len(direction) == 1:
        raise ValueError("Direction attribute needs to define exactly one direction")

    match direction:
        case Direction.LEFT:
            return "Left"
        case Direction.RIGHT:
            return "Right"
        case Direction.STRAIGHT:
            return "Forward"
        case Direction.BACKWARD:
            return "Back"
        case _:
            typing.assert_never(direction)


def native_intersection_direction_from_protocol(direction: TAriUserIoPromptDirections) -> Direction:
    match direction:
        case "Left":
            return Direction.LEFT
        case "Right":
            return Direction.RIGHT
        case "Forward":
            return Direction.STRAIGHT
        case "Back":
            return Direction.BACKWARD
        case _:
            typing.assert_never(direction)


def get_web_type_name(_type: type[str | int | float | bool | NamedColor | Direction]) -> TWebUserIoPrompt:
    if _type == str:
        return "string"
    elif any(issubclass(c, _type) for c in [float, int]):
        return "number"
    elif _type == bool:
        return "boolean"
    elif _type == NamedColor:
        return "color"
    elif _type == Direction:
        return "direction"
    else:
        raise UnexpectedUserIoPromptTypeError(_type)


def get_type_options[T: (str, float, int, bool, NamedColor, Direction)](
    options: list[T], _type: type[T]
) -> list[str | float | int | bool | TNamedColor | TDirection]:
    protocol_options: list[str | float | int | bool | TNamedColor | TDirection] = []
    for opt in options:
        if not isinstance(opt, _type):
            raise UnexpectedUserIoPromptOptionTypeError(opt, _type)

        if isinstance(opt, NamedColor):
            protocol_options.append(color_to_protocol(opt))
        elif isinstance(opt, Direction):
            protocol_options.append(native_intersection_direction_to_protocol(opt))
        else:
            protocol_options.append(opt)

    return protocol_options


def get_web_type_options[T: (str, float, int, bool, NamedColor, Direction)](
    options: list[T], _type: type[T]
) -> list[str | float | int | bool | TNamedColor | TWebDirection]:
    for opt in options:
        if not isinstance(opt, _type):
            raise UnexpectedUserIoPromptOptionTypeError(opt, _type)

    protocol_options: list[str | float | int | bool | TNamedColor | TDirection] = []
    for opt in options:
        if isinstance(opt, NamedColor):
            protocol_options.append(web_conversions.color_to_web(opt))
        elif isinstance(opt, Direction):
            protocol_options.append(web_conversions.direction_to_web(opt))
        else:
            protocol_options.append(opt)

    return protocol_options


def cast_web_prompt_response[T](_type: type[T], value: typing.Any) -> T:
    if _type is str:
        if value is None:
            return typing.cast(T, "")
        return typing.cast(T, value)
    elif _type is int:
        return typing.cast(T, int(value))
    elif _type is float:
        return typing.cast(T, float(value))
    elif any(issubclass(c, _type) for c in [float, int]):
        return typing.cast(T, float(value))
    elif _type is bool:
        return typing.cast(T, bool(value))
    elif _type is NamedColor and web_conversions.is_web_color(value):
        return typing.cast(T, web_conversions.color_from_web(value))
    elif _type is Direction and web_conversions.is_web_direction(value):
        return typing.cast(T, web_conversions.direction_from_web(value))
    else:
        raise UnexpectedUserIoPromptResponseReceivedError(value, _type)
