import typing

from ozobot.linefollower.datatypes import ClassifiedColor, Color, Colors, Direction, LEDMask, TDirection, TNamedColor
from ozobot.linefollower.exceptions import SingleDirectionRequiredError


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


def direction_to_web(direction: Direction) -> TDirection:
    if len(direction) != 1:
        raise SingleDirectionRequiredError(direction)

    match direction:
        case Direction.STRAIGHT:
            return "Forward"
        case Direction.BACKWARD:
            return "Back"
        case Direction.LEFT:
            return "Left"
        case Direction.RIGHT:
            return "Right"
        case _:
            typing.assert_never(direction)


def direction_from_web(direction: TDirection) -> Direction:
    return intersection_from_web({direction: True})


def intersection_from_web(intersection_json: dict[TDirection, bool]) -> Direction:
    mapping = {
        "Forward": Direction.STRAIGHT,
        "Back": Direction.BACKWARD,
        "Left": Direction.LEFT,
        "Right": Direction.RIGHT,
    }

    direction = Direction(0)
    for name, value in mapping.items():
        if name in intersection_json:
            direction |= value

    return direction


def color_from_web(color: TNamedColor) -> ClassifiedColor:
    match color:
        case "Green":
            return Colors.GREEN
        case "Black":
            return Colors.BLACK
        case "Red":
            return Colors.RED
        case "Blue":
            return Colors.BLUE
        case "White":
            return Colors.WHITE
        case "Unknown":
            return Colors.UNKNOWN
        case _:
            typing.assert_never(color)


def color_to_web(color: Color) -> TNamedColor:
    if color == Colors.GREEN:
        return "Green"
    elif color == Colors.BLACK:
        return "Black"
    elif color == Colors.RED:
        return "Red"
    elif color == Colors.BLUE:
        return "Blue"
    elif color == Colors.WHITE:
        return "White"
    else:
        return "Unknown"
