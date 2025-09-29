import pytest
from ozobot.linefollower.datatypes import Direction, LEDMask
from ozobot.linefollower.exceptions import SingleDirectionRequiredError
from ozobot.web.conversions import (
    direction_to_web,
    intersection_from_web,
    led_to_web_json,
)


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
