from ozobot.linefollower.api.data_access import DataReadConstant
from ozobot.linefollower.datatypes import RobotGeometry
from ozobot.linefollower.exceptions import AudioFileNotFoundError

_map_audioname_filename = {
    "happy": "01010100",
    "sad": "01010110",
    "surprised": "01010170",
    "laugh": "01010250",
    "black": "01040200",
    "red": "01040201",
    "green": "01040202",
    "blue": "01040204",
    "cyan": "01040206",
    "magenta": "01040205",
    "yellow": "01040203",
    "white": "01040207",
    "forward": "01040101",
    "backward": "01040108",
    "left": "01040102",
    "right": "01040104",
    **{f"num{i}": f"010400{format(i, 'x').rjust(2, '0').upper()}" for i in list(range(199))},
    "minus": "010400FF",
}


def map_audio_name_to_filename(audio_name: str) -> str:
    filename = _map_audioname_filename.get(audio_name, None)
    if not filename:
        raise AudioFileNotFoundError(audio_name)
    return filename


geometry = DataReadConstant(
    lambda: RobotGeometry(
        ticks_per_meter=18851,
        wheel_track=0.023,
        wheel_diameter=0.01182,
        encoder_ticks_per_wheel_revolution=8 * 2 * 21 * 25 / 12,
        max_speed_limit=0.3,
    )
)
