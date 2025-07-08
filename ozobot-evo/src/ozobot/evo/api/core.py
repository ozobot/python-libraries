from __future__ import annotations

import contextlib
import datetime
import math
import typing

from loguru import logger
from ozobot.evo.api.data_access import DataAccessRead, DataWatcher, EventWatcher, EventWatcherQueue
from ozobot.evo.api.watchers import WatcherSubscription
from ozobot.evo.conversions import (
    battery_state_from_protocol,
    color_code_from_protocol,
    line_color_from_protocol,
    surface_color_from_protocol,
)
from ozobot.evo.datatypes import BatteryState, Color, ColorCode, Direction, LEDMask, Sample, TNote
from ozobot.evo.driver.driver import Driver, MemoryProperty
from ozobot.evo.exceptions import EvoError
from ozobot.evo.protocol import Types, VirtualMemory

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


class FileNotFoundError(EvoError):
    def __init__(self, audio_name: str) -> None:
        super().__init__(f"Audio file not found: {audio_name}")


class Evo:
    @property
    def battery(self) -> DataAccessRead[Types.Battery, BatteryState]:
        return self._property_battery

    @property
    def color_codes(self) -> DataWatcher[Types.ColorCode, ColorCode]:
        return self._watcher_color_codes

    @property
    def line_color(self) -> DataWatcher[Types.LineColor, Color]:
        return self._watcher_line_color

    @property
    def surface_color(self) -> DataWatcher[Types.SurfaceColor, Color]:
        return self._watcher_surface_color

    @property
    def intersection(self) -> EventWatcher[Direction]:
        return self._intersection

    def __init__(
        self,
        driver: Driver,
        watchers: tuple[
            WatcherSubscription[Types.ColorCode],
            WatcherSubscription[Types.LineColor],
            WatcherSubscription[Types.SurfaceColor],
        ],
    ) -> None:
        self._driver = driver
        self._watcher_color_codes = DataWatcher(
            self._driver, VirtualMemory.colorCode, watchers[0], color_code_from_protocol
        )
        self._watcher_line_color = DataWatcher(
            self._driver, VirtualMemory.lineColor, watchers[1], line_color_from_protocol
        )
        self._watcher_surface_color = DataWatcher(
            self._driver, VirtualMemory.surfaceColor, watchers[2], surface_color_from_protocol
        )
        self._property_battery = DataAccessRead[Types.Battery, BatteryState](
            driver, VirtualMemory.batteryState, battery_state_from_protocol
        )
        self._intersection_queue = EventWatcherQueue[Direction](Sample(Direction(0), 0))
        self._intersection = EventWatcher(self._intersection_queue)

    @classmethod
    @contextlib.asynccontextmanager
    async def open(cls, driver: Driver) -> typing.AsyncIterator[Evo]:
        config = (
            VirtualMemory.colorCode,
            VirtualMemory.lineColor,
            VirtualMemory.surfaceColor,
        )

        async with driver.watch(
            typing.cast(tuple[MemoryProperty[Types.ColorCode | Types.LineColor | Types.SurfaceColor], ...], config)
        ) as watchers:
            yield Evo(
                driver,
                typing.cast(
                    tuple[
                        WatcherSubscription[Types.ColorCode],
                        WatcherSubscription[Types.LineColor],
                        WatcherSubscription[Types.SurfaceColor],
                    ],
                    watchers,
                ),
            )

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

    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume: int) -> None:
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
        key = note_idx + 12 + ((octave - 2) * 12) + 1
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
            raise FileNotFoundError(audio_name)
        return filename

    async def set_led(self, mask: LEDMask, color: Color) -> None:
        logger.debug("Setting LED", mask=mask, color=color)
        red = int(color.red * 255)
        green = int(color.green * 255)
        blue = int(color.blue * 255)
        await self._driver.set_led(mask, red, green, blue)

    async def follow_line(self, direction: Direction) -> None:
        logger.debug("Following line", direction=direction)
        intersection = await self._driver.line_navigation(direction, follow=True)
        timestamp = datetime.datetime.now()
        sample = Sample(intersection, timestamp)
        await self._intersection_queue.write(sample)

    async def align_with_line(self, direction: Direction) -> None:
        logger.debug("Aligning with line", direTction=direction)
        intersection = await self._driver.line_navigation(direction, follow=False)
        timestamp = datetime.datetime.now()
        sample = Sample(intersection, timestamp)
        await self._intersection_queue.write(sample)

    async def set_follow_line_speed(self, speed_mps: float) -> None:
        logger.debug("Setting line following speed", speed=speed_mps)
        await self._driver.follow_speed(speed_mps)
