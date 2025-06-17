import typing

from ozobot.evo.protocol import Types
from ozobot.evo.datatypes import BatteryState, ColorCode, Color, Colors


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
