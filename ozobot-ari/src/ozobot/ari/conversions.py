import typing

from ozobot.ari.protocol import types
from ozobot.ari.protocol.types import TDirection
from ozobot.linefollower.datatypes import Color, ColorCode, Colors, Direction, LEDMask, TNamedColor


def led_to_protocol(mask: LEDMask) -> types.Lights:
    return types.Lights(
        back=LEDMask.BACK in mask,
        button=LEDMask.BUTTON in mask,
        frontCenter=LEDMask.FRONT_CENTER in mask,
        frontLeft=LEDMask.FRONT_LEFT in mask,
        frontLeftCenter=LEDMask.FRONT_LEFT_CENTER in mask,
        frontRight=LEDMask.FRONT_RIGHT in mask,
        frontRightCenter=LEDMask.FRONT_RIGHT_CENTER in mask,
        top=LEDMask.TOP in mask,
    )


def intersection_direction_to_protocol(direction: Direction) -> TDirection:
    if not len(direction) == 1:
        raise ValueError("Direction attribute needs to define exactly one direction")

    match direction:
        case Direction.LEFT:
            return "Left"
        case Direction.RIGHT:
            return "Right"
        case Direction.STRAIGHT:
            return "Straight"
        case Direction.BACKWARD:
            return "Backward"
        case _:
            typing.assert_never(direction)


def intersection_direction_from_protocol(direction: TDirection) -> Direction:
    match direction:
        case "Left":
            return Direction.LEFT
        case "Right":
            return Direction.RIGHT
        case "Straight":
            return Direction.STRAIGHT
        case "Backward":
            return Direction.BACKWARD
        case _:
            typing.assert_never(direction)


def intersection_bitmap_from_protocol(intersection_mask: types.Intersection) -> Direction:
    intersection = Direction(0)

    if intersection_mask.backward:
        intersection |= Direction.BACKWARD
    if intersection_mask.straight:
        intersection |= Direction.STRAIGHT
    if intersection_mask.left:
        intersection |= Direction.LEFT
    if intersection_mask.right:
        intersection |= Direction.RIGHT

    return intersection


def color_from_protocol(color: TNamedColor) -> Color:
    match color:
        case "green":
            return Colors.GREEN
        case "black":
            return Colors.BLACK
        case "red":
            return Colors.RED
        case "blue":
            return Colors.BLUE
        case "white":
            return Colors.WHITE
        case "cyan":
            return Colors.CYAN
        case "magenta":
            return Colors.MAGENTA
        case "yellow":
            return Colors.YELLOW
        case "unknown":
            return Colors.UNKNOWN
        case _:
            typing.assert_never(color)


def color_to_protocol(color: Color) -> TNamedColor:
    if color == Colors.GREEN:
        return "green"
    elif color == Colors.BLACK:
        return "black"
    elif color == Colors.RED:
        return "red"
    elif color == Colors.BLUE:
        return "blue"
    elif color == Colors.WHITE:
        return "white"
    else:
        return "unknown"


def color_code_from_protocol(color_code: list[TNamedColor]) -> ColorCode:
    return ColorCode(colors=tuple(color_from_protocol(c) for c in color_code))
