import contextlib

import pytest
from ozobot.linefollower.datatypes import Color


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
        _ = Color(red=red, green=green, blue=blue)
