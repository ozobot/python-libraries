from __future__ import annotations

import asyncio
import contextlib
import functools
import typing

from ozobot.linefollower.datatypes import Color, Direction, LEDMask, Sample

from .core import Evo, TNote
from .data_access import DataAccessRead, DataWatcher, EventWatcher

_loop = asyncio.new_event_loop()


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


class SyncDataAccessRead[T]:
    def __init__(self, reader: DataAccessRead[typing.Any, T] | DataWatcher[typing.Any, T] | EventWatcher[T]) -> None:
        self._reader = reader

    @as_sync
    async def read(self) -> Sample[T]:
        return await self._reader.read()


class EvoSync:
    def __init__(self, evo_async: Evo) -> None:
        self._evo = evo_async
        self.intersection = SyncDataAccessRead(self._evo.intersection)
        self.color_codes = SyncDataAccessRead(self._evo.color_codes)
        self.surface_color = SyncDataAccessRead(self._evo.surface_color)
        self.line_color = SyncDataAccessRead(self._evo.line_color)
        self.battery = SyncDataAccessRead(self._evo.battery)

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
    async def emit_note(self, note: TNote, octave: int, duration_s: float, volume: int) -> None:
        await self._evo.emit_note(note, octave, duration_s, volume)

    @as_sync
    async def set_led(self, mask: LEDMask, color: Color) -> None:
        await self._evo.set_led(mask, color)

    @as_sync
    async def follow_line(self, direction: Direction) -> None:
        await self._evo.follow_line(direction)

    @as_sync
    async def align_with_line(self, direction: Direction) -> None:
        await self._evo.align_with_line(direction)

    @as_sync
    async def set_follow_line_speed(self, speed_mps: float) -> None:
        await self._evo.set_follow_line_speed(speed_mps)
