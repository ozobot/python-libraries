import typing

from ozobot.ari.protocol import memread, notification, types
from ozobot.ari.webprotocol import types as webtypes
from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    ColorCode,
    Colors,
    Direction,
    IRMessage,
    LEDMask,
    TDirection,
    TimeOfFlight,
    TNamedColor,
)
from ozobot.linefollower.exceptions import InvalidClassifiedColorError


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
            return "Forward"
        case Direction.BACKWARD:
            return "Back"
        case _:
            typing.assert_never(direction)


def intersection_direction_from_protocol(direction: TDirection) -> Direction:
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


def intersection_bitmap_from_protocol(intersection_mask: types.Intersection) -> Direction:
    intersection = Direction(0)

    if intersection_mask.back:
        intersection |= Direction.BACKWARD
    if intersection_mask.forward:
        intersection |= Direction.STRAIGHT
    if intersection_mask.left:
        intersection |= Direction.LEFT
    if intersection_mask.right:
        intersection |= Direction.RIGHT

    return intersection


def color_from_protocol(color: TNamedColor) -> ClassifiedColor:
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
        case _:
            typing.assert_never(color)


def color_to_protocol(color: ClassifiedColor) -> TNamedColor:
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

    raise InvalidClassifiedColorError(color)


def color_code_from_protocol(color_code: list[TNamedColor]) -> ColorCode:
    return ColorCode(colors=tuple(color_from_protocol(c) for c in color_code))


def ir_message_from_protocol(ir_message: memread.MemReadResponseReadIr) -> IRMessage:
    return IRMessage(
        message=ir_message.message,
        intensity=ir_message.intensity,
    )


def time_of_flight_from_protocol(time_of_flight: notification.TimeOfFlightNotificationBody) -> TimeOfFlight:
    return TimeOfFlight(
        distance=time_of_flight.distance * 1000,
        deviation=time_of_flight.deviation * 1000,
    )


def time_of_flight_from_web(time_of_flight: webtypes.TimeOfFlightResponse) -> TimeOfFlight:
    return TimeOfFlight(
        distance=time_of_flight.distance * 1000,
        deviation=time_of_flight.deviation * 1000,
    )
