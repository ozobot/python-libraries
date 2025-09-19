import pytest
from ozobot.evo.conversions import (
    charger_state_from_protocol,
    color_code_from_protocol,
    intersection_bitmap_from_protocol,
    intersection_direction_to_protocol,
    ir_message_from_protocol,
    led_to_protocol,
    line_color_from_protocol,
    proximity_from_protocol,
    surface_color_from_protocol,
)
from ozobot.evo.protocol import Types
from ozobot.linefollower.datatypes import Color, ColorCode, Colors, Direction, IRMessage, IRProximity, LEDMask


def test_color_code_from_protocol() -> None:
    assert color_code_from_protocol(Types.ColorCode(0b100_000 | 0b001, 0)) == ColorCode(
        colors=(Colors.RED, Colors.BLUE)
    )


@pytest.mark.parametrize(
    ["protocol_color", "library_color"],
    argvalues=[
        (Types.SurfaceColorEnum.Black, Colors.BLACK),
        (Types.SurfaceColorEnum.Blue, Colors.BLUE),
        (Types.SurfaceColorEnum.Green, Colors.GREEN),
        (Types.SurfaceColorEnum.Red, Colors.RED),
        (Types.SurfaceColorEnum.White, Colors.WHITE),
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
        (Types.LEDsMask.button, LEDMask.BUTTON),
        (Types.LEDsMask.back, LEDMask.BACK),
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


def test_proximity_from_protocol() -> None:
    assert proximity_from_protocol(Types.IRProximity(1, 2, 3, 4, 5)) == IRProximity(
        right_front=4, left_front=2, right_rear=3, left_rear=1
    )


def test_ir_message_from_protocol() -> None:
    assert ir_message_from_protocol(Types.IRMessage(10, 20, 30)) == IRMessage(message=10, intensity=20)


@pytest.mark.parametrize(
    ["proto_value", "lib_value"],
    [
        [Types.ChargerStateEnum.Connected, "Connected"],
        [Types.ChargerStateEnum.Disconnected, "Disconnected"],
        [Types.ChargerStateEnum.LowPower, "LowPower"],
    ],
)
def test_charger_state_from_protocol(proto_value: Types.ChargerStateEnum, lib_value: str) -> None:
    assert charger_state_from_protocol(Types.ChargerState(state=proto_value, timestamp=0)) == lib_value
