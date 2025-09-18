from ozobot.linefollower.exceptions import FileNotFoundError

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
    # numbers 0 - 19, 20, 30, 40, .., 90, 100
    **{
        f"num{i}": f"010400{format(i, 'x').rjust(2, '0').upper()}"
        for i in list(range(19)) + [20, 30, 40, 50, 60, 70, 80, 90, 100]
    },
    "minus": "010400FF",
}


def map_audio_name_to_filename(audio_name: str) -> str:
    filename = _map_audioname_filename.get(audio_name, None)
    if not filename:
        raise FileNotFoundError(audio_name)
    return filename
