from __future__ import annotations

import asyncio
import contextlib
import functools
import math
import typing
from dataclasses import dataclass

from loguru import logger
from ozobot.evo.datatypes import Color, LEDMask, TDirection
from ozobot.evo.driver import Driver, get_driver
from ozobot.evo.exceptions import EvoError

_loop = asyncio.get_event_loop()


def as_sync[**P, T](func: typing.Callable[P, typing.Awaitable[T]]) -> typing.Callable[P, T]:
    if func is None:
        raise Exception("Deceorator does not support arguments, remove parentheses")

    @functools.wraps(func)
    def _inner(*args, **kwargs):
        return _loop.run_until_complete(func(*args, **kwargs))

    return functools.update_wrapper(_inner, func)


@contextlib.contextmanager
def as_sync_context_manager[T](async_context_manager: typing.AsyncContextManager[T]) -> typing.Iterator[T]:
    exit_stack = contextlib.AsyncExitStack()
    try:
        yield _loop.run_until_complete(exit_stack.enter_async_context(async_context_manager))
    finally:
        _loop.run_until_complete(exit_stack.aclose())


_map_audioname_filename = {
    "happy": "01010100",
    "sad": "01010110",
    "surprise": "01010170",
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
    "numns": "010400FF",
    "num0": "01040000",
    # numbers
    **{f"num{i}": f"010400{format(i, 'x').rjust(2, '0').upper()}" for i in range(99)},
}

_TNote: typing.TypeAlias = typing.Literal["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]


class AudioFileNotFoundError(EvoError):
    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")


@dataclass(frozen=True, kw_only=True)
class EvoHandle:
    address: str | None = None
    id_prefix: str | None = None
    name: str | None = None

    @typing.overload
    def connect(self, *, get_async: typing.Literal[False] = False) -> typing.ContextManager[EvoSync]: ...

    @typing.overload
    def connect(self, *, get_async: typing.Literal[True]) -> typing.AsyncContextManager[Evo]: ...

    def connect(self, *, get_async: bool = False) -> typing.ContextManager[EvoSync] | typing.AsyncContextManager[Evo]:
        @contextlib.asynccontextmanager
        async def connect_async() -> typing.AsyncIterator[Evo]:
            Driver = get_driver()
            async with Driver.open(address=self.address, id_prefix=self.id_prefix, name=self.name) as driver:
                await driver.stop_all()
                yield Evo(driver)

        if get_async:
            return connect_async()
        else:

            @contextlib.contextmanager
            def connect_sync() -> typing.Iterator[EvoSync]:
                with as_sync_context_manager(connect_async()) as evo:
                    yield EvoSync(evo)

            return connect_sync()


class Evo:
    def __init__(self, driver: Driver) -> None:
        self._driver = driver

    async def move(self, distance_m: float, speed_mps: float) -> None:
        logger.debug("Moving", distance=distance_m, speed=speed_mps)
        await self._driver.move(distance_m, speed_mps)

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        logger.debug("Rotating", angle=angle_deg, anglle_speed=angular_speed_degps)
        await self._driver.rotate(
            math.radians(angle_deg),
            math.radians(angular_speed_degps),
        )

    async def set_velocity(self, linear_mps: float, angular_degps: float, duration_s: float) -> None:
        logger.debug("Setting velocity", linear=linear_mps, angular=angular_degps, duration=duration_s)
        await self._driver.velocity(
            linear_mps,
            math.radians(angular_degps),
            int(duration_s * 1000),
        )

    async def emit_tone(self, frequency_hz: int, duration_s: float, volume: int) -> None:
        logger.debug("Emitting tone", frequency=frequency_hz, duration=duration_s, volume=volume)
        await self._driver.play_tone(
            frequency_hz,
            int(duration_s * 1000),
            volume,
        )

    async def emit_note(self, note: _TNote, octave: int, duration_s: float, volume: int) -> None:
        notes = ["A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
        note_idx = notes.index(note.upper())

        if note_idx < 0:
            raise ValueError(f"Invalid note: {note_idx}")

        frequency_hz = self._convert_note_to_frequency(octave, note_idx)
        await self.emit_tone(
            frequency_hz,
            duration_s,
            volume,
        )

    @staticmethod
    def _convert_note_to_frequency(octave: int, note_idx: int) -> int:
        # credit goes to https://gist.github.com/CGrassin/26a1fdf4fc5de788da9b376ff717516e
        a4 = 440
        key = note_idx + 12 + ((octave - 2)* 12) + 1
        if note_idx < 3:
            key += 12

        frequency = a4 * 2 ** ((key - 49) / 12)
        return int(frequency)

    async def play_audio(self, name: str) -> None:
        filename = self._map_audio_name_to_filename(name)
        await self._driver.execute_file(f"/system/audio/{filename}.wav")

    @staticmethod
    def _map_audio_name_to_filename(audio_name: str) -> str:
        filename = _map_audioname_filename.get(audio_name, None)
        if not filename:
            raise
        return filename

    async def set_led(self, mask: LEDMask, color: Color) -> None:
        logger.debug("Setting LED", mask=mask, color=color)
        red = int(color.red * 255)
        green = int(color.green * 255)
        blue = int(color.blue * 255)
        await self._driver.set_led(mask, red, green, blue)

    async def follow_line(self, direction: TDirection) -> None:
        logger.debug("Following line", direction=direction)
        await self._driver.line_navigation(direction, follow=True)

    async def align_with_line(self, direction: TDirection) -> None:
        logger.debug("Aligning with line", direction=direction)
        await self._driver.line_navigation(direction, follow=False)

    async def set_follow_line_speed(self, speed_mps: float) -> None:
        logger.debug("Setting line following speed", speed=speed_mps)
        await self._driver.follow_speed(speed_mps)


class EvoSync:
    def __init__(self, evo_async: Evo) -> None:
        self._evo = evo_async

    @as_sync
    async def move(self, distance_m: float, speed_mps: float) -> None:
        await self._evo.move(distance_m, speed_mps)

    @as_sync
    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        await self._evo.rotate(angle_deg, angular_speed_degps)

    @as_sync
    async def set_velocity(self, linear_mps: float, angular_degps: float, duration_s: float) -> None:
        await self._evo.set_velocity(linear_mps, angular_degps, duration_s)

    @as_sync
    async def emit_tone(self, frequency_hz: int, duration_s: float, volume: int) -> None:
        await self._evo.emit_tone(frequency_hz, duration_s, volume)

    @as_sync
    async def emit_note(self, note: _TNote, octave: int, duration_s: float, volume: int) -> None:
        await self._evo.emit_note(note, octave, duration_s, volume)

    @as_sync
    async def set_led(self, mask: LEDMask, color: Color) -> None:
        await self._evo.set_led(mask, color)

    @as_sync
    async def follow_line(self, direction: TDirection) -> None:
        await self._evo.follow_line(direction)

    @as_sync
    async def align_with_line(self, direction: TDirection) -> None:
        await self._evo.align_with_line(direction)

    @as_sync
    async def set_follow_line_speed(self, speed_mps: float) -> None:
        await self._evo.set_follow_line_speed(speed_mps)
