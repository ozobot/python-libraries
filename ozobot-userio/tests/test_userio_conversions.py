import pytest
from ozobot.linefollower.datatypes import Direction, NamedColor
from ozobot.userio.conversions import get_type_name, get_web_type_name


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
