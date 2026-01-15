import typing
from unittest.mock import AsyncMock, call

import pytest
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import ClassifiedColor, Colors, Direction
from ozobot.linefollower.exceptions import InvalidClassifiedColorError


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
    ["midi_number", "expected_frequency"],
    [
        [81, 880],
        [105, 3520],
        [48, 130],
        [72, 523],
        [49, 138],
        [73, 554],
    ],
)
async def test_emit_midi(midi_number: int, expected_frequency: int) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.emit_midi(midi_number, 0, 0)

    driver.play_tone.assert_called_once_with(expected_frequency, 0, 0)


@pytest.mark.parametrize(
    ["number", "expected_sounds"],
    [
        [0, ["num0"]],
        [1, ["num1"]],
        [120, ["num120"]],
        [-127.521, ["minus", "num127"]],
        [-112, ["minus", "num112"]],
    ],
    ids=lambda x: repr(x),
)
async def test_say_number(number: int, expected_sounds: list[str]) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_number(number)

    driver.play_audio.assert_has_calls([call(sound) for sound in expected_sounds])


@pytest.mark.parametrize(
    ["number"],
    [
        [200],
        [-200],
        [1000],
        [-1000],
    ],
    ids=lambda x: repr(x),
)
async def test_say_number_out_of_range(number: int) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    with pytest.raises(ValueError):
        await lf.say_number(number)

    driver.play_audio.assert_not_called()


@pytest.mark.parametrize(
    ["color", "audio_name"],
    [
        [Colors.BLACK, "01040200"],
        [Colors.BLUE, "01040204"],
        [Colors.GREEN, "01040202"],
        [Colors.RED, "01040201"],
        [Colors.WHITE, "01040207"],
    ],
    ids=lambda x: repr(x),
)
async def test_say_color(color: ClassifiedColor, audio_name: str) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_color(color)

    driver.play_audio.assert_called_with(audio_name)


async def test_say_color_invalid() -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    with pytest.raises(InvalidClassifiedColorError):
        await lf.say_color("not a color")  # type: ignore[arg-type]

    driver.play_audio.assert_not_called()


@pytest.mark.parametrize(
    ["direction", "audio_name"],
    [
        [Direction.LEFT, "01040102"],
        [Direction.RIGHT, "01040104"],
        [Direction.BACKWARD, "01040108"],
        [Direction.STRAIGHT, "01040101"],
    ],
    ids=lambda x: repr(x),
)
async def test_say_direction(direction: Direction, audio_name: str) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_direction(direction)

    driver.play_audio.assert_called_with(audio_name)


@pytest.mark.parametrize(
    ["audio_name", "asset_name"],
    [
        ["happy", "01010100"],
        ["sad", "01010110"],
        ["surprised", "01010170"],
        ["laugh", "01010250"],
        ["black", "01040200"],
        ["red", "01040201"],
        ["green", "01040202"],
        ["blue", "01040204"],
        ["cyan", "01040206"],
        ["magenta", "01040205"],
        ["yellow", "01040203"],
        ["white", "01040207"],
        ["forward", "01040101"],
        ["backward", "01040108"],
        ["left", "01040102"],
        ["right", "01040104"],
        ["minus", "010400FF"],
        ["num3", "01040003"],
        ["num10", "0104000A"],
        ["num120", "01040078"],
    ],
    ids=lambda x: repr(x),
)
async def test_play_audio(audio_name: str, asset_name: str) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.play_audio(audio_name)

    driver.play_audio.assert_called_with(asset_name)
