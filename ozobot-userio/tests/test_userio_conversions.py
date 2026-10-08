import typing

import pytest
from ozobot.linefollower import RawColor
from ozobot.linefollower.datatypes import Direction, NamedColor, TDirection, TNamedColor
from ozobot.linefollower.exceptions import InvalidNamedColorError
from ozobot.userio.conversions import (
    color_to_protocol,
    get_type_name,
    get_web_type_name,
    native_intersection_direction_from_protocol,
    native_intersection_direction_to_protocol,
)
from ozobot.userio.datatypes import TAriUserIoPromptDirections


@pytest.mark.parametrize(
    "what,expected",
    [
        [int, "number"],
        [float, "number"],
        [int | float, "number"],
        [int | float, "number"],
        [(int, float), "number"],
        [(int, float), "number"],
        [str, "string"],
        [bool, "boolean"],
        [NamedColor, "surfaceColor"],
        [Direction, "direction"],
    ],
)
def test_get_type_name(what, expected) -> None:
    assert get_type_name(what) == expected


@pytest.mark.parametrize(
    "what,expected",
    [
        [int, "number"],
        [float, "number"],
        [int | float, "number"],
        [int | float, "number"],
        [(int, float), "number"],
        [(int, float), "number"],
        [str, "string"],
        [bool, "boolean"],
        [NamedColor, "color"],
        [Direction, "direction"],
    ],
)
def test_get_web_type_name(what, expected) -> None:
    assert get_web_type_name(what) == expected


@pytest.mark.parametrize(
    ["color", "protocol_color"],
    argvalues=[
        (NamedColor.BLACK, "Black"),
        (NamedColor.RED, "Red"),
        (NamedColor.GREEN, "Green"),
        (NamedColor.BLUE, "Blue"),
        (NamedColor.WHITE, "White"),
    ],
    ids=lambda x: repr(x),
)
def test_color_to_protocol(color: NamedColor, protocol_color: TNamedColor) -> None:
    assert color_to_protocol(color) == protocol_color


def test_none_color_to_protocol() -> None:
    with pytest.raises(InvalidNamedColorError):
        c = typing.cast(NamedColor, None)
        _ = color_to_protocol(c)


def test_unknown_color_to_protocol() -> None:
    with pytest.raises(InvalidNamedColorError):
        c = typing.cast(NamedColor, RawColor(0.5, 0.5, 0.5))
        _ = color_to_protocol(c)


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
    assert native_intersection_direction_to_protocol(direction) == protocol_direction


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
def test_intersection_direction_from_protocol(
    protocol_direction: TAriUserIoPromptDirections, direction: Direction
) -> None:
    assert native_intersection_direction_from_protocol(protocol_direction) == direction
