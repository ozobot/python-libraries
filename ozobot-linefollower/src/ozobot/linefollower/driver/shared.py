from ozobot.linefollower.datatypes import TAudio
from ozobot.linefollower.exceptions import AudioFileNotFoundError

_map_audioname_filename: dict[TAudio, str] = {
    "happy": "01010100",
    "sad": "01010110",
    "surprised": "01010170",
    "laugh": "01010250",
}


def map_audio_name_to_filename(audio_name: TAudio) -> str:
    if audio_name in _map_audioname_filename:
        return _map_audioname_filename[audio_name]
    else:
        raise AudioFileNotFoundError(audio_name)
