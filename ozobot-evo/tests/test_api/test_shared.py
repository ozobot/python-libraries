import pytest
from ozobot.evo.driver.shared import map_audio_name_to_filename


@pytest.mark.parametrize(
    ["audio_name", "file_name"],
    [
        ["num0", "01040000"],
        ["num1", "01040001"],
        ["num10", "0104000A"],
        ["num15", "0104000F"],
        ["num20", "01040014"],
        ["num70", "01040046"],
        ["num100", "01040064"],
    ],
)
def test_map_audio_name_to_filename(audio_name: str, file_name: str) -> None:
    assert map_audio_name_to_filename(audio_name) == file_name
