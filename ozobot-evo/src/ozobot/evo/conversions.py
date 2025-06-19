import typing

from ozobot.common.exceptions import OzobotDataTypeError
from ozobot.evo.datatypes import BatteryState, Color, ColorCode, Colors, Direction, LEDMask, Sample
from ozobot.evo.protocol import Types


class _HasTimestamp(typing.Protocol):
    timestamp: int


def battery_state_from_protocol(state: Types.Battery) -> BatteryState:
    if not isinstance(state, Types.Battery):
        raise OzobotDataTypeError(Types.Battery, type(state))

    return BatteryState(state.voltage, state.remainingPower, state.fields & Types.BatteryFieldsEnum.Charging)


def color_code_from_protocol(color_code: Types.ColorCode) -> ColorCode:
    if not isinstance(color_code, Types.ColorCode):
        raise OzobotDataTypeError(Types.ColorCode, type(color_code))
    return ColorCode(color_code.code)


def surface_color_from_protocol(surface_color: Types.SurfaceColor) -> Color:
    if not isinstance(surface_color, Types.SurfaceColor):
        raise OzobotDataTypeError(Types.SurfaceColor, type(surface_color))

    match surface_color.color:
        case Types.SurfaceColorEnum.Black:
            return Colors.BLACK
        case Types.SurfaceColorEnum.Blue:
            return Colors.BLUE
        case Types.SurfaceColorEnum.Cyan:
            return Colors.CYAN
        case Types.SurfaceColorEnum.Green:
            return Colors.GREEN
        case Types.SurfaceColorEnum.Magenta:
            return Colors.MAGENTA
        case Types.SurfaceColorEnum.Red:
            return Colors.RED
        case Types.SurfaceColorEnum.White:
            return Colors.WHITE
        case Types.SurfaceColorEnum.Yellow:
            return Colors.YELLOW
        case Types.SurfaceColorEnum.Unknown:
            return Colors.UNKNOWN
        case _:
            typing.assert_never(surface_color.color)


def line_color_from_protocol(line_color: Types.LineColor) -> Color:
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
            return Colors.UNKNOWN
        case _:
            typing.assert_never(line_color.color)


def led_to_protocol(mask: LEDMask) -> Types.LEDsMask:
    if not isinstance(mask, LEDMask):
        raise OzobotDataTypeError(LEDMask, type(mask))

    protocol_mask: Types.LEDsMask = Types.LEDsMask(0)
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


def sample_from_protocol[T: _HasTimestamp, U](protocol_data: T, convertor: typing.Callable[[T], U]) -> Sample[U]:
    return Sample(
        convertor(protocol_data),
        protocol_data.timestamp,
    )
