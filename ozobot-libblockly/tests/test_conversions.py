import math
from typing import Any

import pytest
from ozobot.libblockly.conversions import (
    InvalidValue,
    type_cast_bool,
    type_cast_color,
    type_cast_direction,
    type_cast_number,
)
from ozobot.linefollower.datatypes import Direction, NamedColor


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (5, 5),
        (1.5, 1.5),
        ("5", 5),
        ("-5", -5),
        ("1.5", 1.5),
        (" 2 ", 2),
        ("1e3", 1000.0),
        ("inf", math.inf),
        (True, 1),
        (False, 0),
    ],
)
def test_type_cast_number(value: Any, expected: int | float) -> None:
    result = type_cast_number(value)
    assert result == expected
    assert type(result) is type(expected)


def test_type_cast_number_nan() -> None:
    assert math.isnan(type_cast_number("nan"))


@pytest.mark.parametrize("value", ["abc", "", None])
def test_type_cast_number_invalid(value: Any) -> None:
    with pytest.raises(InvalidValue):
        type_cast_number(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (True, True),
        (False, False),
        (1, True),
        (0, False),
        (0.0, False),
        ("false", False),
        ("False", False),
        ("", False),
        ("true", True),
        ("anything", True),
        # truthy, although it might be surprising
        ("0", True),
        ("no", True),
        (None, False),
    ],
)
def test_type_cast_bool(value: Any, expected: bool) -> None:
    assert type_cast_bool(value) is expected


@pytest.mark.parametrize("name", ["BLACK", "BLUE", "GREEN", "RED", "WHITE"])
def test_type_cast_color(name: str) -> None:
    expected = getattr(NamedColor, name)
    assert type_cast_color(expected) is expected
    assert type_cast_color(name) is expected
    assert type_cast_color(name.lower()) is expected
    assert type_cast_color(f"NamedColor.{name}") is expected


@pytest.mark.parametrize("value", ["purple", "", "NamedColor.purple", 42, None])
def test_type_cast_color_invalid(value: Any) -> None:
    with pytest.raises(InvalidValue):
        type_cast_color(value)


@pytest.mark.parametrize("name", ["BACKWARD", "LEFT", "RIGHT", "STRAIGHT"])
def test_type_cast_direction(name: str) -> None:
    expected = getattr(Direction, name)
    assert type_cast_direction(expected) is expected
    assert type_cast_direction(name) is expected
    assert type_cast_direction(name.lower()) is expected
    assert type_cast_direction(f"Direction.{name}") is expected


@pytest.mark.parametrize("value", ["up", "", "Direction.up", 42, None])
def test_type_cast_direction_invalid(value: Any) -> None:
    with pytest.raises(InvalidValue):
        type_cast_direction(value)
