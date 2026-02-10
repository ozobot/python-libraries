import typing

from ozobot.linefollower.datatypes import (
    ColorCode,
    Direction,
    IRMessage,
    LEDMask,
    NamedColor,
    TNamedColor,
)
from ozobot.linefollower.driver.web.exceptions import InvalidColorCodeError
from ozobot.linefollower.exceptions import InvalidNamedColorError, SingleDirectionRequiredError

from .rpctypes import (
    ALLOWED_WEB_COLORS,
    ALLOWED_WEB_DIRECTIONS,
    ReadIrResponse,
    TWebColor,
    TWebDirection,
)


def led_to_web_json(mask: LEDMask) -> dict[str, bool]:
    """Converts `LEDMask` to the json representation expected by web-python"""
    mask_json = {}
    if mask & LEDMask.TOP:
        mask_json["top"] = True
    if mask & LEDMask.BACK:
        mask_json["back"] = True
    if mask & LEDMask.BUTTON:
        mask_json["button"] = True
    if mask & LEDMask.FRONT_LEFT:
        mask_json["front_left"] = True
    if mask & LEDMask.FRONT_LEFT_CENTER:
        mask_json["front_left_center"] = True
    if mask & LEDMask.FRONT_CENTER:
        mask_json["front_center"] = True
    if mask & LEDMask.FRONT_RIGHT_CENTER:
        mask_json["front_right_center"] = True
    if mask & LEDMask.FRONT_RIGHT:
        mask_json["front_right"] = True

    return mask_json


def direction_to_web(direction: Direction) -> TWebDirection:
    if len(direction) != 1:
        raise SingleDirectionRequiredError(direction)

    match direction:
        case Direction.STRAIGHT:
            return "Straight"
        case Direction.BACKWARD:
            return "Backward"
        case Direction.LEFT:
            return "Left"
        case Direction.RIGHT:
            return "Right"
        case _:
            typing.assert_never(direction)


def direction_from_web(direction: TWebDirection) -> Direction:
    return intersection_from_web({direction: True})


def intersection_from_web(intersection_json: dict[TWebDirection, bool]) -> Direction:
    mapping = {
        "Straight": Direction.STRAIGHT,
        "Backward": Direction.BACKWARD,
        "Left": Direction.LEFT,
        "Right": Direction.RIGHT,
    }

    direction = Direction(0)
    for name, value in mapping.items():
        if is_web_direction(name) and intersection_json.get(name, False):
            direction |= value

    return direction


def color_from_web(color: TWebColor) -> NamedColor:
    match color:
        case "Green":
            return NamedColor.GREEN
        case "Black":
            return NamedColor.BLACK
        case "Red":
            return NamedColor.RED
        case "Blue":
            return NamedColor.BLUE
        case "White":
            return NamedColor.WHITE
        case _:
            typing.assert_never(color.name)


def color_to_web(color: NamedColor) -> TNamedColor:
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


def color_code_from_web(web_colors: list[TWebColor]) -> ColorCode:
    colors: list[NamedColor] = []
    for web_color in web_colors:
        color = color_from_web(web_color)
        if not isinstance(color, NamedColor):
            raise InvalidColorCodeError(color)
        colors.append(color)

    return ColorCode(colors=tuple(colors))


def is_web_direction(value: typing.Any) -> typing.TypeGuard[TWebDirection]:
    return value in ALLOWED_WEB_DIRECTIONS


def is_web_color(value: typing.Any) -> typing.TypeGuard[TWebColor]:
    return value in ALLOWED_WEB_COLORS


def ir_message_from_web(ir_message: ReadIrResponse) -> IRMessage:
    return IRMessage(
        message=ir_message.message,
        intensity=ir_message.intensity,
    )
