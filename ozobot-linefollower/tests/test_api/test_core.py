import typing
from unittest.mock import AsyncMock, call

import pytest
from ozobot.linefollower.api.core import LineFollower


@pytest.mark.parametrize(
    ["note", "octave", "expected_frequency"],
    [
        ["A", 5, 880],
        ["A", 7, 3520],
        ["C", 3, 130],
        ["C", 5, 523],
        ["C#", 3, 138],
        ["C#", 5, 554],
    ],
)
async def test_emit_note(note: typing.Any, octave: int, expected_frequency: int) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.emit_note(note, octave, 0, 0)

    driver.play_tone.assert_called_once_with(expected_frequency, 0, 0)


@pytest.mark.parametrize(
    ["number", "expected_sounds"],
    [
        [0, ["num0"]],
        [1, ["num1"]],
        [12, ["num12"]],
        [15, ["num15"]],
        [45, ["num40", "num5"]],
        [120, ["num1", "num100", "num20"]],
        [127, ["num1", "num100", "num20", "num7"]],
        [127.521, ["num1", "num100", "num20", "num7"]],
        [-312, ["minus", "num3", "num100", "num12"]],
        [-845, ["minus", "num8", "num100", "num40", "num5"]],
    ],
    ids=lambda x: repr(x),
)
async def test_say_number(number: int, expected_sounds: list[str]) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_number(number)

    driver.play_audio.assert_has_calls([call(sound) for sound in expected_sounds])
