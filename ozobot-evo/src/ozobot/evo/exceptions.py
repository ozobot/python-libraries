class EvoError(Exception): ...


class FileNotFoundError(EvoError):
    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")
