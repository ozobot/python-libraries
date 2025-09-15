import pytest
from ozobot.ari import conversions
from ozobot.ari.conversions import color_code_from_protocol, color_from_protocol, color_to_protocol
from ozobot.ari.protocol import types
from ozobot.linefollower.datatypes import Color, ColorCode, Colors, Direction, LEDMask, TDirection, TNamedColor


@pytest.mark.parametrize(
    ["protocol_led", "library_led"],
    argvalues=[
        (types.Lights(frontLeft=True), LEDMask.FRONT_LEFT),
        (types.Lights(frontLeftCenter=True), LEDMask.FRONT_LEFT_CENTER),
        (types.Lights(frontRight=True), LEDMask.FRONT_RIGHT),
        (types.Lights(frontRightCenter=True), LEDMask.FRONT_RIGHT_CENTER),
        (types.Lights(frontCenter=True), LEDMask.FRONT_CENTER),
        (types.Lights(top=True), LEDMask.TOP),
        (types.Lights(button=True), LEDMask.BUTTON),
        (types.Lights(back=True), LEDMask.BACK),
    ],
    ids=lambda x: repr(x),
)
def test_led_to_protocol(protocol_led: types.Lights, library_led: LEDMask) -> None:
    assert conversions.led_to_protocol(library_led) == protocol_led


@pytest.mark.parametrize(
    ["direction", "protocol_direction"],
    argvalues=[
        (Direction.STRAIGHT, "Forward"),
        (Direction.BACKWARD, "Back"),
        (Direction.LEFT, "Left"),
        (Direction.RIGHT, "Right"),
    ],
    ids=lambda x: repr(x),
)
def test_intersection_direction_to_protocol(direction: Direction, protocol_direction: TDirection) -> None:
    assert conversions.intersection_direction_to_protocol(direction) == protocol_direction


@pytest.mark.parametrize(
    ["protocol_direction", "direction"],
    argvalues=[
        ("Forward", Direction.STRAIGHT),
        ("Back", Direction.BACKWARD),
        ("Left", Direction.LEFT),
        ("Right", Direction.RIGHT),
    ],
    ids=lambda x: repr(x),
)
def test_intersection_direction_from_protocol(protocol_direction: TDirection, direction: Direction) -> None:
    assert conversions.intersection_direction_from_protocol(protocol_direction) == direction


@pytest.mark.parametrize(
    ["intersection", "expected_direction"],
    argvalues=[
        (types.Intersection(forward=True), Direction.STRAIGHT),
        (types.Intersection(left=True), Direction.LEFT),
        (types.Intersection(right=True), Direction.RIGHT),
        (types.Intersection(back=True), Direction.BACKWARD),
    ],
    ids=lambda x: repr(x),
)
def test_intersection_bitmap_from_protocol(intersection: types.Intersection, expected_direction: Direction) -> None:
    assert conversions.intersection_bitmap_from_protocol(intersection) == expected_direction


@pytest.mark.parametrize(
    ["color", "protocol_color"],
    argvalues=[
        (Colors.BLACK, "Black"),
        (Colors.RED, "Red"),
        (Colors.GREEN, "Green"),
        (Colors.BLUE, "Blue"),
        (Colors.WHITE, "White"),
        (Colors.UNKNOWN, "Unknown"),
    ],
    ids=lambda x: repr(x),
)
def test_color_from_protocol(color: Color, protocol_color: TNamedColor) -> None:
    assert color_from_protocol(protocol_color) == color


@pytest.mark.parametrize(
    ["color", "protocol_color"],
    argvalues=[
        (Colors.BLACK, "Black"),
        (Colors.RED, "Red"),
        (Colors.GREEN, "Green"),
        (Colors.BLUE, "Blue"),
        (Colors.WHITE, "White"),
        (Colors.UNKNOWN, "Unknown"),
    ],
    ids=lambda x: repr(x),
)
def test_color_to_protocol(color: Color, protocol_color: TNamedColor) -> None:
    assert color_to_protocol(color) == protocol_color


def test_color_code_from_protocol() -> None:
    assert color_code_from_protocol(["Red", "Black", "Blue"]) == ColorCode(
        colors=(Colors.RED, Colors.BLACK, Colors.BLUE)
    )
