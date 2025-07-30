from __future__ import annotations

from ozobot.common.sync import as_sync
from ozobot.linefollower.datatypes import Color, Direction, LEDMask, Sample, TNote
from ozobot.linefollower.driver import ReadableRegion

from .core import LineFollower


class SyncDataAccessRead[T]:
    def __init__(self, reader: ReadableRegion[T]) -> None:
        self._reader = reader

    @as_sync
    async def read(self) -> Sample[T]:
        return await self._reader.read()


class _SyncMemoryRegions:
    def __init__(self, linefollower_async: LineFollower) -> None:
        self.intersection = SyncDataAccessRead(linefollower_async.memory.intersection)
        self.battery = SyncDataAccessRead(linefollower_async.memory.battery)
        self.color_code = SyncDataAccessRead(linefollower_async.memory.color_code)
        self.line_color = SyncDataAccessRead(linefollower_async.memory.line_color)
        self.surface_color = SyncDataAccessRead(linefollower_async.memory.surface_color)


class LineFollowerSync:
    def __init__(self, linefollower_async: LineFollower) -> None:
        self._linefollower = linefollower_async
        self.memory = _SyncMemoryRegions(linefollower_async)

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
    async def emit_tone(self, frequency_hz: int, duration_s: float, volume: int) -> None:
        await self._linefollower.emit_tone(frequency_hz, duration_s, volume)

    @as_sync
    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume: int) -> None:
        await self._linefollower.emit_note(note, octave, duration_s, volume)

    @as_sync
    async def set_led(self, mask: LEDMask, color: Color) -> None:
        await self._linefollower.set_led(mask, color)

    @as_sync
    async def follow_line(self, direction: Direction) -> None:
        await self._linefollower.follow_line(direction)

    @as_sync
    async def align_with_line(self, direction: Direction) -> None:
        await self._linefollower.align_with_line(direction)

    @as_sync
    async def set_follow_line_speed(self, speed_mps: float) -> None:
        await self._linefollower.set_follow_line_speed(speed_mps)
