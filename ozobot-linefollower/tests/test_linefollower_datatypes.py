import contextlib

import pytest
from ozobot.linefollower.datatypes import ClassifiedColor, Color, Colors, RawColor


@pytest.fixture
def red() -> Color:
    return RawColor(red=1, green=0, blue=0)


@pytest.fixture
def almost_red() -> Color:
    return RawColor(red=0.999, green=0, blue=0.001)


@pytest.fixture
def blue() -> Color:
    return RawColor(red=0, green=0, blue=1)


@pytest.fixture
def classified_red() -> ClassifiedColor:
    return Colors.RED


@pytest.fixture
def classified_blue() -> ClassifiedColor:
    return Colors.BLUE


@pytest.mark.parametrize(
    ["red", "green", "blue", "is_valid"],
    (
        (0, 0, 0, True),
        (1, 0, 0, True),
        (1, 1, 1, True),
        (1.0, 1.0, 1.0, True),
        (0.5, 0.5, 0.5, True),
        (2, 0.5, 0.5, False),
        (-1, 0, 0, False),
    ),
)
def test_color_bounds(red: int | float, green: int | float, blue: int | float, is_valid: bool) -> None:
    expect_exception = contextlib.nullcontext() if is_valid else pytest.raises(ValueError)

    with expect_exception:
        _ = RawColor(red=red, green=green, blue=blue)


def test_color_str_repr(red: Color) -> None:
    assert str(red) == "red=1, green=0, blue=0"
    assert repr(red) == "RawColor(red=1, green=0, blue=0)"


def test_classified_color_str_repr(classified_red: ClassifiedColor) -> None:
    assert str(classified_red) == "Red"
    assert repr(classified_red) == "ClassifiedColor('Red', RawColor(red=1.0, green=0, blue=0))"


def test_color_hash(red: Color, blue: Color) -> None:
    assert hash(red) != hash(blue)


def test_classified_color_hash(classified_red: ClassifiedColor, classified_blue: ClassifiedColor) -> None:
    assert hash(classified_red) != hash(classified_blue)
    assert hash(classified_red) != None


def test_color_eq_color(red: Color, blue: Color) -> None:
    assert red == RawColor(red=1, green=0, blue=0)
    assert red == RawColor(red=1.0, green=0.0, blue=0.0)
    assert red != blue


def test_color_eq_classified_color(
    red: Color, classified_red: ClassifiedColor, classified_blue: ClassifiedColor
) -> None:
    assert red == classified_red
    assert red != classified_blue
    assert red != None


def test_classified_color_eq_color(classified_red: ClassifiedColor, red: Color, blue: Color) -> None:
    assert classified_red == red
    assert classified_red != blue


def test_classified_color_eq_classified_color(
    classified_blue: ClassifiedColor, classified_red: ClassifiedColor
) -> None:
    assert classified_red == ClassifiedColor("Red", RawColor(red=1.0, green=0, blue=0))
    assert classified_red != classified_blue
    assert classified_red != None


def test_color_is_color(red: Color, blue: Color, almost_red: Color) -> None:
    assert red.is_color(RawColor(red=1, green=0, blue=0))
    assert not red.is_color(almost_red, epsilon=0.00001)
    assert red.is_color(almost_red)
    assert not red.is_color(blue)


def test_color_is_classified_color(
    red: Color, classified_red: ClassifiedColor, classified_blue: ClassifiedColor
) -> None:
    assert red.is_color(classified_red)
    assert not red.is_color(classified_blue)
    assert not red.is_color(None)


def test_classified_color_is_color(classified_red: ClassifiedColor, red: Color, almost_red: Color, blue: Color) -> None:
    assert classified_red.is_color(red)
    assert classified_red.is_color(almost_red)
    assert not classified_red.is_color(blue)


def test_classified_color_is_classified_color(
    classified_blue: ClassifiedColor, classified_red: ClassifiedColor
) -> None:
    assert classified_red.is_color(ClassifiedColor("Red", RawColor(red=1.0, green=0, blue=0)))
    assert not classified_red.is_color(classified_blue)
    assert not classified_red.is_color(None)
