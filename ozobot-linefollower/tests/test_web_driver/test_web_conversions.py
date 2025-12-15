import pytest
from ozobot.linefollower.datatypes import (
    Color,
    ColorCode,
    Colors,
    Direction,
    IRMessage,
    LEDMask,
    RobotGeometry,
    TNamedColor,
)
from ozobot.linefollower.driver.web.conversions import (
    color_code_from_web,
    color_from_web,
    direction_to_web,
    intersection_from_web,
    ir_message_from_web,
    led_to_web_json,
    robot_geometry_from_web,
)
from ozobot.linefollower.driver.web.rpctypes import ClassifiedColor, ReadIrResponse, RobotGeometryResponse
from ozobot.linefollower.exceptions import SingleDirectionRequiredError


@pytest.mark.parametrize(
    ["mask", "expected"],
    [
        (LEDMask.TOP, {"top": True}),
        (LEDMask.BACK, {"back": True}),
        (LEDMask.BUTTON, {"button": True}),
        (LEDMask.FRONT_LEFT, {"front_left": True}),
        (LEDMask.FRONT_LEFT_CENTER, {"front_left_center": True}),
        (LEDMask.FRONT_CENTER, {"front_center": True}),
        (LEDMask.FRONT_RIGHT_CENTER, {"front_right_center": True}),
        (LEDMask.FRONT_RIGHT, {"front_right": True}),
        (
            LEDMask.TOP | LEDMask.FRONT_LEFT | LEDMask.FRONT_RIGHT,
            {"top": True, "front_left": True, "front_right": True},
        ),
    ],
)
def test_led_to_web_json(mask, expected):
    assert led_to_web_json(mask) == expected


@pytest.mark.parametrize(
    ["direction", "expected"],
    [
        (Direction.STRAIGHT, "Straight"),
        (Direction.BACKWARD, "Backward"),
        (Direction.LEFT, "Left"),
        (Direction.RIGHT, "Right"),
    ],
)
def test_direction_to_web_valid(direction, expected):
    assert direction_to_web(direction) == expected


def test_direction_to_web_invalid_length():
    with pytest.raises(SingleDirectionRequiredError):
        direction_to_web(Direction.LEFT | Direction.RIGHT)

    with pytest.raises(SingleDirectionRequiredError):
        direction_to_web(Direction(0))


@pytest.mark.parametrize(
    ["json_input", "expected"],
    [
        ({"Straight": True}, Direction.STRAIGHT),
        ({"Backward": True}, Direction.BACKWARD),
        ({"Left": True}, Direction.LEFT),
        ({"Right": True}, Direction.RIGHT),
        ({"Straight": True, "Left": True, "Right": False}, Direction.STRAIGHT | Direction.LEFT),
        ({}, Direction(0)),
    ],
)
def test_intersection_from_web(json_input, expected):
    assert intersection_from_web(json_input) == expected


def test_color_code_from_web() -> None:
    colors = ["Red", "Black", "Blue"]
    responses = [ClassifiedColor(red=0, green=0, blue=0, name=c) for c in colors]
    assert color_code_from_web(responses) == ColorCode(colors=(Colors.RED, Colors.BLACK, Colors.BLUE))


@pytest.mark.parametrize(
    ["web", "lib"],
    [
        ("Red", Colors.RED),
        ("Blue", Colors.BLUE),
        ("Green", Colors.GREEN),
        ("Black", Colors.BLACK),
        ("White", Colors.WHITE),
        ("Unknown", Colors.UNKNOWN),
    ],
)
def test_color_from_web(web: TNamedColor, lib: Color) -> None:
    assert color_from_web(ClassifiedColor(red=0, green=0, blue=0, name=web)) == lib


def test_ir_message_from_web() -> None:
    assert ir_message_from_web(ReadIrResponse(message=10, intensity=20)) == IRMessage(message=10, intensity=20)


def test_robot_geometry_from_web() -> None:
    assert robot_geometry_from_web(
        RobotGeometryResponse(
            ticks_per_meter=22281.69,
            wheel_track=0.0315,
            wheel_diameter=0.012,
            encoder_ticks_per_wheel_revolution=16 * 2 * 21 * 15 / 12.0,
            max_speed_limit=0.3,
        )
    ) == RobotGeometry(
        ticks_per_meter=22281.69,
        wheel_track=0.0315,
        wheel_diameter=0.012,
        encoder_ticks_per_wheel_revolution=16 * 2 * 21 * 15 / 12.0,
        max_speed_limit=0.3,
    )
