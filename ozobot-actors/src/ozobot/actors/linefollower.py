from __future__ import annotations

import typing

from ozobot.actors.actors import ActorDispatcher, context
from ozobot.linefollower.api.core import LineFollower
from ozobot.linefollower.datatypes import ClassifiedColor, Color, Direction, LEDMask, Sample, TNote
from ozobot.linefollower.driver.interface import ReadableRegion, ReadableWatchableRegion, VirtualMemoryRegions


class _ProxyDataAccessRead[T]:
    def __init__(self, dispatcher: ActorDispatcher, value_type: type[ReadableRegion[T]], name: str) -> None:
        self._dispatcher = dispatcher
        self._value_type = value_type
        self._name = name

    async def read(self) -> T:
        obj = self._dispatcher.get_property(self._value_type, self._name)
        return await obj.read()


class _ProxyDataWatcher[T]:
    def __init__(self, dispatcher: ActorDispatcher, value_type: type[ReadableWatchableRegion[T]], name: str) -> None:
        self._dispatcher = dispatcher
        self._value_type = value_type
        self._name = name

    async def read(self) -> T:
        obj = self._dispatcher.get_property(self._value_type, self._name)
        return await obj.read()

    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[T]]]:
        obj = self._dispatcher.get_property(self._value_type, self._name)
        async with obj.watch() as reader:
            yield reader


class _ProxyVirtualMemoryRegions:
    def __getattr__(self, name: str) -> typing.Any:
        memory = context.dispatcher.get_property(object, "memory")
        if hasattr(memory, name):
            return getattr(memory, name)

        raise AttributeError(f"'memory' has no attribute '{name}'")


data: VirtualMemoryRegions = _ProxyVirtualMemoryRegions()


async def move(distance_mm: float, speed_mmps: float) -> None:
    await context.dispatcher.acall(LineFollower.move, distance_mm, speed_mmps)


async def rotate(angle_deg: float, angular_speed_degps: float) -> None:
    await context.dispatcher.acall(LineFollower.rotate, angle_deg, angular_speed_degps)


async def set_velocity(linear_mmps: float, angular_degps: float, duration_s: float) -> None:
    await context.dispatcher.acall(LineFollower.set_velocity, linear_mmps, angular_degps, duration_s)


async def emit_tone(frequency_hz: int, duration_s: float, volume: int) -> None:
    await context.dispatcher.acall(LineFollower.emit_tone, frequency_hz, duration_s, volume)


async def emit_note(note: TNote, octave: int, duration_s: float, volume: int) -> None:
    await context.dispatcher.acall(LineFollower.emit_note, note, octave, duration_s, volume)


async def emit_midi(midi_number: int, duration_s: float, volume: int) -> None:
    await context.dispatcher.call(LineFollower.emit_midi, midi_number, duration_s, volume)


async def play_audio(name: str) -> None:
    await context.dispatcher.acall(LineFollower.play_audio, name)


async def set_led(mask: LEDMask, color: Color) -> None:
    await context.dispatcher.acall(LineFollower.set_led, mask, color)


async def say_number(number: int) -> None:
    await context.dispatcher.acall(LineFollower.say_number, number)


async def say_direction(direction: Direction) -> None:
    await context.dispatcher.acall(LineFollower.say_direction, direction)


async def say_color(color: ClassifiedColor) -> None:
    await context.dispatcher.acall(LineFollower.say_color, color)


async def follow_line(direction: Direction) -> None:
    await context.dispatcher.acall(LineFollower.follow_line, direction)


async def align_with_line(direction: Direction) -> None:
    await context.dispatcher.acall(LineFollower.align_with_line, direction)
