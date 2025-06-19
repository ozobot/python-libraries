import pytest
from ozobot.evo.conversions import (
    battery_state_from_protocol,
    color_code_from_protocol,
    intersection_direction_to_protocol,
    intersection_bitmap_from_protocol,
    led_to_protocol,
    line_color_from_protocol,
    surface_color_from_protocol,
)
from ozobot.evo.datatypes import BatteryState, Color, ColorCode, Colors, Direction, LEDMask
from ozobot.evo.protocol import Types


def test_battery_state_from_protocol() -> None:
    assert battery_state_from_protocol(Types.Battery(1, 2, Types.BatteryFieldsEnum.Charging, 0)) == BatteryState(
        1, 2, True
    )
    assert battery_state_from_protocol(Types.Battery(1, 2, Types.BatteryFieldsEnum(0), 0)) == BatteryState(1, 2, False)


def test_color_code_from_protocol() -> None:
    assert color_code_from_protocol(Types.ColorCode(1, 0)) == ColorCode(1)


@pytest.mark.parametrize(
    ["protocol_color", "library_color"],
    argvalues=[
        (Types.SurfaceColorEnum.Black, Colors.BLACK),
        (Types.SurfaceColorEnum.Blue, Colors.BLUE),
        (Types.SurfaceColorEnum.Cyan, Colors.CYAN),
        (Types.SurfaceColorEnum.Green, Colors.GREEN),
        (Types.SurfaceColorEnum.Magenta, Colors.MAGENTA),
        (Types.SurfaceColorEnum.Red, Colors.RED),
        (Types.SurfaceColorEnum.White, Colors.WHITE),
        (Types.SurfaceColorEnum.Yellow, Colors.YELLOW),
        (Types.SurfaceColorEnum.Unknown, Colors.UNKNOWN),
    ],
    ids=lambda x: repr(x),
)
def test_surface_color_from_protocol(protocol_color: Types.SurfaceColorEnum, library_color: Color) -> None:
    assert surface_color_from_protocol(Types.SurfaceColor(protocol_color, 0, 0, 0)) == library_color


@pytest.mark.parametrize(
    ["protocol_color", "library_color"],
    argvalues=[
        (Types.LineColorEnum.Black, Colors.BLACK),
        (Types.LineColorEnum.Blue, Colors.BLUE),
        (Types.LineColorEnum.Green, Colors.GREEN),
        (Types.LineColorEnum.Red, Colors.RED),
        (Types.LineColorEnum.Unknown, Colors.UNKNOWN),
    ],
    ids=lambda x: repr(x),
)
def test_line_color_from_protocol(protocol_color: Types.LineColorEnum, library_color: Color) -> None:
    assert line_color_from_protocol(Types.LineColor(protocol_color, 0, 0)) == library_color


@pytest.mark.parametrize(
    ["protocol_led", "library_led"],
    argvalues=[
        (Types.LEDsMask.front_left, LEDMask.FRONT_LEFT),
        (Types.LEDsMask.front_left_center, LEDMask.FRONT_LEFT_CENTER),
        (Types.LEDsMask.front_right, LEDMask.FRONT_RIGHT),
        (Types.LEDsMask.front_right_center, LEDMask.FRONT_RIGHT_CENTER),
        (Types.LEDsMask.front_center, LEDMask.FRONT_CENTER),
        (Types.LEDsMask.top, LEDMask.TOP),
    ],
    ids=lambda x: repr(x),
)
def test_led_to_protocol(protocol_led: Types.LEDsMask, library_led: LEDMask) -> None:
    assert led_to_protocol(library_led) == protocol_led


def test_led_mask_to_protocol() -> None:
    assert (
        led_to_protocol(LEDMask.FRONT_CENTER | LEDMask.FRONT_LEFT)
        == Types.LEDsMask.front_center | Types.LEDsMask.front_left
    )


@pytest.mark.parametrize(
    ["protocol_direction", "library_direction"],
    argvalues=[
        (Types.IntersectionBitmap.Backward, Direction.BACKWARD),
        (Types.IntersectionBitmap.Straight, Direction.STRAIGHT),
        (Types.IntersectionBitmap.Left, Direction.LEFT),
        (Types.IntersectionBitmap.Right, Direction.RIGHT),
    ],
    ids=lambda x: repr(x),
)
def test_intersection_direction_to_protocol(
    protocol_direction: Types.IntersectionBitmap, library_direction: Direction
) -> None:
    assert intersection_direction_to_protocol(library_direction) == protocol_direction


def test_intersection_direction_mask_to_protocol() -> None:
    with pytest.raises(ValueError):
        intersection_direction_to_protocol(Direction.LEFT | Direction.RIGHT)


@pytest.mark.parametrize(
    ["protocol_direction", "library_direction"],
    argvalues=[
        (Types.IntersectionBitmap.Backward, Direction.BACKWARD),
        (Types.IntersectionBitmap.Straight, Direction.STRAIGHT),
        (Types.IntersectionBitmap.Left, Direction.LEFT),
        (Types.IntersectionBitmap.Right, Direction.RIGHT),
    ],
    ids=lambda x: repr(x),
)
def test_intersection_from_protocol(protocol_direction: Types.IntersectionBitmap, library_direction: Direction) -> None:
    assert intersection_bitmap_from_protocol(protocol_direction) == library_direction


def test_intersection_mask_from_protocol() -> None:
    result = intersection_bitmap_from_protocol(Types.IntersectionBitmap.Backward | Types.IntersectionBitmap.Left)

    assert result == Direction.LEFT | Direction.BACKWARD
