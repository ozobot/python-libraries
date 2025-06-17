import typing

from ozobot.evo.datatypes import BatteryState, Color, ColorCode, Colors, Intersection, LEDMask, TDirection
from ozobot.evo.protocol import Types


def battery_state_from_protocol(state: Types.Battery) -> BatteryState:
    return BatteryState(state.voltage, state.remainingPower, state.fields & Types.BatteryFieldsEnum.Charging)


def color_code_from_protocol(color_code: Types.ColorCode) -> ColorCode:
    return ColorCode(color_code.code)


def surface_color_from_protocol(surface_color: Types.SurfaceColor) -> Color:
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


def direction_to_protocol(direction: TDirection) -> Types.IntersectionDirection:
    match direction:
        case "left":
            return Types.IntersectionDirection.Left
        case "right":
            return Types.IntersectionDirection.Right
        case "straight":
            return Types.IntersectionDirection.Straight
        case "backward":
            return Types.IntersectionDirection.Backward
        case _:
            typing.assert_never(direction)


def intersection_from_protocol(intersection_mask: Types.IntersectionBitmap) -> Intersection:
    intersection = Intersection(0)
    for dir in intersection_mask:
        match dir:
            case Types.IntersectionBitmap.Backward:
                intersection |= Intersection.BACKWARD
            case Types.IntersectionBitmap.Straight:
                intersection |= Intersection.STRAIGHT
            case Types.IntersectionBitmap.Left:
                intersection |= Intersection.LEFT
            case Types.IntersectionBitmap.Right:
                intersection |= Intersection.RIGHT
            case _:
                typing.assert_never(dir)

    return intersection
