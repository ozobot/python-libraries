import typing
from unittest.mock import AsyncMock, call

import pytest
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import Direction, NamedColor, TAudio
from ozobot.linefollower.exceptions import InvalidNamedColorError


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
async def test_play_note(note: typing.Any, octave: int, expected_frequency: int) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.play_note(note, octave, 0, 0)

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
async def test_play_midi(midi_number: int, expected_frequency: int) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.play_midi(midi_number, 0, 0)

    driver.play_tone.assert_called_once_with(expected_frequency, 0, 0)


@pytest.mark.parametrize(
    ["number", "expected_sounds"],
    [
        [0, ["01040000"]],
        [1, ["01040001"]],
        [120, ["01040078"]],
        [-127.521, ["010400FF", "0104007F"]],
        [-112, ["010400FF", "01040070"]],
    ],
    ids=lambda x: repr(x),
)
async def test_say_number(number: int, expected_sounds: list[str]) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_number(number)

    driver.play_audio_asset.assert_has_calls([call(sound) for sound in expected_sounds])


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

    driver.play_audio_asset.assert_not_called()


@pytest.mark.parametrize(
    ["color", "audio_name"],
    [
        [NamedColor.BLACK, "01040200"],
        [NamedColor.BLUE, "01040204"],
        [NamedColor.GREEN, "01040202"],
        [NamedColor.RED, "01040201"],
        [NamedColor.WHITE, "01040207"],
    ],
    ids=lambda x: repr(x),
)
async def test_say_color(color: NamedColor, audio_name: str) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.say_color(color)

    driver.play_audio_asset.assert_called_with(audio_name)


async def test_say_color_invalid() -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    with pytest.raises(InvalidNamedColorError):
        await lf.say_color("not a color")  # type: ignore[arg-type]

    driver.play_audio_asset.assert_not_called()


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

    driver.play_audio_asset.assert_called_with(audio_name)


@pytest.mark.parametrize(
    ["audio_name", "asset_name"],
    [
        ["happy", "01010100"],
        ["sad", "01010110"],
        ["surprised", "01010170"],
        ["laugh", "01010250"],
    ],
    ids=lambda x: repr(x),
)
async def test_play_audio(audio_name: TAudio, asset_name: str) -> None:
    driver = AsyncMock()
    lf = LineFollower(driver)
    await lf.play_audio(audio_name)

    driver.play_audio_asset.assert_called_with(asset_name)
