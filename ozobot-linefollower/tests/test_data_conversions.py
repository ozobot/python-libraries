import datetime

import pytest
from ozobot.linefollower.conversions import (
    direction_to_web,
    intersection_from_web,
    led_to_web_json,
    sample_from_protocol,
)
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample
from ozobot.linefollower.exceptions import SingleDirectionRequiredError


def test_sample_from_protocol() -> None:
    class _Data:
        def __init__(self, val1: int, val2: int) -> None:
            self.val1 = val1
            self.val2 = val2
            self.timestamp = 1

    sample = sample_from_protocol(_Data(1, 2), lambda d: d.val1 + d.val2)

    assert isinstance(sample, Sample)
    assert sample.data == 3
    assert sample.timestamp == datetime.datetime.fromtimestamp(1)


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
        (Direction.STRAIGHT, "Forward"),
        (Direction.BACKWARD, "Back"),
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
        ({"Forward": True}, Direction.STRAIGHT),
        ({"Back": True}, Direction.BACKWARD),
        ({"Left": True}, Direction.LEFT),
        ({"Right": True}, Direction.RIGHT),
        ({"Forward": True, "Left": True}, Direction.STRAIGHT | Direction.LEFT),
        ({}, Direction(0)),
    ],
)
def test_intersection_from_web(json_input, expected):
    assert intersection_from_web(json_input) == expected
