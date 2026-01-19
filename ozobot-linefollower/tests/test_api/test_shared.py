import typing

import pytest
from ozobot.linefollower.datatypes import TAudio
from ozobot.linefollower.driver.shared import map_audio_name_to_filename
from ozobot.linefollower.exceptions import AudioFileNotFoundError


@pytest.mark.parametrize(
    ["audio_name", "file_name"],
    [
        ["happy", "01010100"],
        ["sad", "01010110"],
        ["surprised", "01010170"],
        ["laugh", "01010250"],
    ],
)
def test_map_emotion_name_to_asset_name(audio_name: TAudio, file_name: str) -> None:
    assert map_audio_name_to_filename(audio_name) == file_name


def test_audio_name_mapping_unknown() -> None:
    with pytest.raises(AudioFileNotFoundError):
        f: TAudio = "xyz does not exist"  # type: ignore[assignment]
        map_audio_name_to_filename(f)


def test_audio_name_mapping_completeness() -> None:
    """Test all allowed audio inputs"""

    audio_names = typing.get_args(TAudio.__value__)
    for audio_name in audio_names:
        _ = map_audio_name_to_filename(audio_name)
