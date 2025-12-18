import typing

from ozobot.evo.exceptions import OzobotDataTypeError, UnsupportedColorCodeNumberError
from ozobot.evo.protocol import Types
from ozobot.linefollower.datatypes import ClassifiedColor, ColorCode, Colors, Direction, IRMessage, IRProximity, LEDMask


def _color_from_color_code_number(num: int) -> ClassifiedColor:
    if num == 0:
        return Colors.BLACK
    elif num == 1:
        return Colors.RED
    elif num == 2:
        return Colors.GREEN
    elif num == 4:
        return Colors.BLUE

    raise UnsupportedColorCodeNumberError(num)


def color_code_from_protocol(color_code: Types.ColorCode) -> ColorCode:
    if not isinstance(color_code, Types.ColorCode):
        raise OzobotDataTypeError(Types.ColorCode, type(color_code))
    colors: list[ClassifiedColor] = []
    num = color_code.code
    while num > 0:
        mod = num & 0b111
        num = num >> 3
        colors.append(_color_from_color_code_number(mod))
    return ColorCode(colors=tuple(colors))


def surface_color_from_protocol(surface_color: Types.SurfaceColor) -> ClassifiedColor | None:
    if not isinstance(surface_color, Types.SurfaceColor):
        raise OzobotDataTypeError(Types.SurfaceColor, type(surface_color))

    match surface_color.color:
        case Types.SurfaceColorEnum.Black:
            return Colors.BLACK
        case Types.SurfaceColorEnum.Blue:
            return Colors.BLUE
        case Types.SurfaceColorEnum.Green:
            return Colors.GREEN
        case Types.SurfaceColorEnum.Red:
            return Colors.RED
        case Types.SurfaceColorEnum.White:
            return Colors.WHITE
        case Types.SurfaceColorEnum.Unknown:
            return None
        case _:
            typing.assert_never(surface_color.color)


def line_color_from_protocol(line_color: Types.LineColor) -> ClassifiedColor | None:
    if not isinstance(line_color, Types.LineColor):
        raise OzobotDataTypeError(Types.LineColor, type(line_color))

    match line_color.color:
        case Types.LineColorEnum.Black:
            return Colors.BLACK
        case Types.LineColorEnum.Blue:
            return Colors.BLUE
        case Types.LineColorEnum.Green:
            return Colors.GREEN
        case Types.LineColorEnum.Red:
            return Colors.RED
        case Types.LineColorEnum.Unknown:
            return None
        case _:
            typing.assert_never(line_color.color)


def led_to_protocol(mask: LEDMask) -> Types.LEDsMask:
    if not isinstance(mask, LEDMask):
        raise OzobotDataTypeError(LEDMask, type(mask))

    protocol_mask: Types.LEDsMask = Types.LEDsMask(0)
    all_front_mask = (
        Types.LEDsMask.front_left
        | Types.LEDsMask.front_left_center
        | Types.LEDsMask.front_center
        | Types.LEDsMask.front_right_center
        | Types.LEDsMask.front_right
    )
    for led in mask:
        match led:
            case LEDMask.FRONT_LEFT:
                protocol_mask |= Types.LEDsMask.front_left
            case LEDMask.FRONT_LEFT_CENTER:
                protocol_mask |= Types.LEDsMask.front_left_center
            case LEDMask.FRONT_CENTER:
                protocol_mask |= Types.LEDsMask.front_center
            case LEDMask.FRONT_RIGHT_CENTER:
                protocol_mask |= Types.LEDsMask.front_right_center
            case LEDMask.FRONT_RIGHT:
                protocol_mask |= Types.LEDsMask.front_right
            case LEDMask.TOP:
                protocol_mask |= Types.LEDsMask.top
            case LEDMask.BACK:
                protocol_mask |= Types.LEDsMask.back
            case LEDMask.BUTTON:
                protocol_mask |= Types.LEDsMask.button
            # ALL_FRONT and ALL_ROBOT should not be needed because the iterator only goes through
            # single bit values, but let's make mypy happy
            case LEDMask.ALL_FRONT:
                protocol_mask |= all_front_mask
            case LEDMask.ALL_ROBOT:
                protocol_mask |= all_front_mask | Types.LEDsMask.top | Types.LEDsMask.back | Types.LEDsMask.button
            case _:
                typing.assert_never(led)

    return protocol_mask


def intersection_direction_to_protocol(direction: Direction) -> Types.IntersectionDirection:
    if not isinstance(direction, Direction):
        raise OzobotDataTypeError(Direction, type(direction))

    if not len(direction) == 1:
        raise ValueError("Direction attribute needs to define exactly one direction")

    match direction:
        case Direction.LEFT:
            return Types.IntersectionDirection.Left
        case Direction.RIGHT:
            return Types.IntersectionDirection.Right
        case Direction.STRAIGHT:
            return Types.IntersectionDirection.Straight
        case Direction.BACKWARD:
            return Types.IntersectionDirection.Backward
        case _:
            typing.assert_never(direction)


def intersection_bitmap_from_protocol(intersection_mask: Types.IntersectionBitmap) -> Direction:
    if not isinstance(intersection_mask, Types.IntersectionBitmap):
        raise OzobotDataTypeError(Types.IntersectionBitmap, type(intersection_mask))

    intersection = Direction(0)
    for dir in intersection_mask:
        match dir:
            case Types.IntersectionBitmap.Backward:
                intersection |= Direction.BACKWARD
            case Types.IntersectionBitmap.Straight:
                intersection |= Direction.STRAIGHT
            case Types.IntersectionBitmap.Left:
                intersection |= Direction.LEFT
            case Types.IntersectionBitmap.Right:
                intersection |= Direction.RIGHT
            case _:
                typing.assert_never(dir)

    return intersection


def proximity_from_protocol(proximity: Types.IRProximity) -> IRProximity:
    return IRProximity(
        right_front=proximity.rightFront,
        left_front=proximity.leftFront,
        right_rear=proximity.rightRear,
        left_rear=proximity.leftRear,
    )


def ir_message_from_protocol(ir_message: Types.IRMessage) -> IRMessage:
    return IRMessage(
        message=ir_message.message,
        intensity=ir_message.intensity,
    )


def charger_state_from_protocol(
    charger_state: Types.ChargerState,
) -> typing.Literal["Connected", "Disconnected", "LowPower"]:
    match charger_state.state:
        case Types.ChargerStateEnum.Connected:
            return "Connected"
        case Types.ChargerStateEnum.Disconnected:
            return "Disconnected"
        case Types.ChargerStateEnum.LowPower:
            return "LowPower"
        case _:
            typing.assert_never(charger_state.state)
