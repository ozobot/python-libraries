import typing

from ozobot.linefollower.datatypes import Color, ColorCode, Colors, Direction, IRMessage, LEDMask, RobotGeometry
from ozobot.linefollower.exceptions import SingleDirectionRequiredError

from .rpctypes import (
    ALLOWED_WEB_COLORS,
    ALLOWED_WEB_DIRECTIONS,
    ReadIrResponse,
    RobotGeometryResponse,
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


def color_from_web(color: TWebColor) -> Color:
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
            typing.assert_never(color.name)


def color_to_web(color: Color) -> TWebColor:
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


def color_code_from_web(colors: list[TWebColor]) -> ColorCode:
    return ColorCode(colors=tuple(color_from_web(c) for c in colors))


def is_web_direction(value: typing.Any) -> typing.TypeGuard[TWebDirection]:
    return value in ALLOWED_WEB_DIRECTIONS


def is_web_color(value: typing.Any) -> typing.TypeGuard[TWebColor]:
    return value in ALLOWED_WEB_COLORS


def ir_message_from_web(ir_message: ReadIrResponse) -> IRMessage:
    return IRMessage(
        message=ir_message.message,
        intensity=ir_message.intensity,
    )


def robot_geometry_from_web(robot_geometry: RobotGeometryResponse) -> RobotGeometry:
    return RobotGeometry(
        ticks_per_meter=robot_geometry.ticks_per_meter,
        wheel_track=robot_geometry.wheel_track,
        wheel_diameter=robot_geometry.wheel_diameter,
        encoder_ticks_per_wheel_revolution=robot_geometry.encoder_ticks_per_wheel_revolution,
        max_speed_limit=robot_geometry.max_speed_limit,
    )
