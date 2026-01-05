import typing

import pytest
from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    Color,
    ColorCode,
    Colors,
    Direction,
    IRMessage,
    LEDMask,
    RawColor,
)
from ozobot.linefollower.driver.web.conversions import (
    color_code_from_web,
    color_from_web,
    color_to_web,
    direction_to_web,
    intersection_from_web,
    ir_message_from_web,
    is_web_color,
    is_web_direction,
    led_to_web_json,
)
from ozobot.linefollower.driver.web.rpctypes import (
    ReadIrResponse,
    TWebColor,
    TWebDirection,
)
from ozobot.linefollower.exceptions import InvalidClassifiedColorError, SingleDirectionRequiredError


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
    colors: list[TWebColor] = ["Red", "Black", "Blue"]
    assert color_code_from_web(colors) == ColorCode(colors=(Colors.RED, Colors.BLACK, Colors.BLUE))


@pytest.mark.parametrize(
    ["web", "lib"],
    [
        ("Red", Colors.RED),
        ("Blue", Colors.BLUE),
        ("Green", Colors.GREEN),
        ("Black", Colors.BLACK),
        ("White", Colors.WHITE),
    ],
)
def test_color_from_web(web: TWebColor, lib: Color) -> None:
    assert color_from_web(web) == lib


@pytest.mark.parametrize(
    ["web", "lib"],
    [
        ("Red", Colors.RED),
        ("Blue", Colors.BLUE),
        ("Green", Colors.GREEN),
        ("Black", Colors.BLACK),
        ("White", Colors.WHITE),
    ],
)
def test_color_to_web(web: TWebColor | None, lib: ClassifiedColor) -> None:
    assert color_to_web(lib) == web


def test_none_color_to_web() -> None:
    with pytest.raises(InvalidClassifiedColorError):
        c = typing.cast(ClassifiedColor, None)
        assert color_to_web(c)


def test_unknown_color_to_web() -> None:
    with pytest.raises(InvalidClassifiedColorError):
        c = typing.cast(ClassifiedColor, RawColor(0.5, 0.5, 0.5))
        assert color_to_web(c)


def test_ir_message_from_web() -> None:
    assert ir_message_from_web(
        ReadIrResponse(
            message=10,
            intensity=20,
            timestamp=30,
        )
    ) == IRMessage(message=10, intensity=20)


@pytest.mark.parametrize(
    ["color"],
    [
        ["Red"],
        ["Blue"],
        ["Green"],
        ["Black"],
        ["White"],
    ],
)
def test_is_web_color(color: TWebColor) -> None:
    assert is_web_color(color)


@pytest.mark.parametrize(
    ["color"],
    [
        ["Hello"],
        ["World"],
        [None],
        [1234],
    ],
)
def test_is_not_web_color(color: TWebColor) -> None:
    assert not is_web_color(color)


@pytest.mark.parametrize(
    ["direction"],
    [
        ["Straight"],
        ["Backward"],
        ["Left"],
        ["Right"],
    ],
)
def test_is_web_direction(direction: TWebDirection) -> None:
    assert is_web_direction(direction)


@pytest.mark.parametrize(
    ["direction"],
    [
        ["Hello"],
        ["World"],
        [None],
        [1234],
    ],
)
def test_is_not_web_direction(direction: TWebDirection) -> None:
    assert not is_web_direction(direction)
