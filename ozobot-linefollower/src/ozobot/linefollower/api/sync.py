from __future__ import annotations

from ozobot.common.sync import as_sync
from ozobot.linefollower.datatypes import ClassifiedColor, Color, ColorCode, Direction, LEDMask, TAudio, TNote
from ozobot.linefollower.driver.interface import ReadableRegion, ReadableWritableRegion

from .core import LineFollower


class SyncDataAccessRead[T]:
    def __init__(self, reader: ReadableRegion[T]) -> None:
        self._reader = reader

    @as_sync
    async def read(self) -> T:
        return await self._reader.read()


class SyncDataAccessReadWrite[T](SyncDataAccessRead[T]):
    def __init__(self, reader: ReadableWritableRegion[T]) -> None:
        super().__init__(reader)
        self._writer = reader

    @as_sync
    async def write(self, data: T) -> None:
        await self._writer.write(data)


class SyncMemoryRegions:
    def __init__(self, linefollower: LineFollower) -> None:
        self.line_following_speed = SyncDataAccessReadWrite(linefollower.data.line_following_speed)
        self.line_color = SyncDataAccessRead(linefollower.data.line_color)
        self.surface_color = SyncDataAccessRead(linefollower.data.surface_color)


class SyncLineFollower:
    def __init__(self, linefollower: LineFollower) -> None:
        self._linefollower = linefollower

    @as_sync
    async def move(self, distance_m: float, speed_mps: float) -> None:
        await self._linefollower.move(distance_m, speed_mps)

    @as_sync
    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        await self._linefollower.rotate(angle_deg, angular_speed_degps)

    @as_sync
    async def set_velocity(self, linear_mps: float, angular_degps: float, duration_s: float) -> None:
        await self._linefollower.set_velocity(linear_mps, angular_degps, duration_s)

    @as_sync
    async def emit_tone(self, frequency_hz: int, duration_s: float, volume_percent: int) -> None:
        await self._linefollower.emit_tone(frequency_hz, duration_s, volume_percent)

    @as_sync
    async def emit_midi(self, midi_number: int, duration_s: float, volume_percent: int) -> None:
        await self._linefollower.emit_midi(midi_number, duration_s, volume_percent)

    @as_sync
    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume_percent: int) -> None:
        await self._linefollower.emit_note(note, octave, duration_s, volume_percent)

    @as_sync
    async def play_audio(self, name: TAudio) -> None:
        await self._linefollower.play_audio(name)

    @as_sync
    async def say_number(self, number: int | float) -> None:
        await self._linefollower.say_number(number)

    @as_sync
    async def say_color(self, color: ClassifiedColor) -> None:
        await self._linefollower.say_color(color)

    @as_sync
    async def say_direction(self, direction: Direction) -> None:
        await self._linefollower.say_direction(direction)

    @as_sync
    async def set_led(self, mask: LEDMask, color: Color) -> None:
        await self._linefollower.set_led(mask, color)

    @as_sync
    async def follow_line(self, direction: Direction) -> tuple[Direction, list[ColorCode]]:
        async with self._linefollower.data.color_code.watch() as color_codes:
            intersection = await self._linefollower.follow_line(direction)

        return intersection, [cc.value async for cc in color_codes]

    @as_sync
    async def align_with_line(self, direction: Direction) -> None:
        await self._linefollower.align_with_line(direction)
