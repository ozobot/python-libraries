from __future__ import annotations

import typing

from ozobot.common.algebraic import ActorDispatcher
from ozobot.evo.api.core import Evo
from ozobot.evo.api.data_access import DataAccessRead, DataWatcher, FakeDataWatcher
from ozobot.evo.datatypes import Color, Direction, LEDMask, TNote, Sample

_evo_dispatcher = ActorDispatcher[Evo]()


class _ProxyDataAccessRead[T, U]:
    def __init__(
        self,
        dispatcher: ActorDispatcher[T],
        actor_type: type[T],
        value_type: type[DataAccessRead[typing.Any, U]],
        name: str,
    ) -> None:
        self._dispatcher = dispatcher
        self._actor_type = actor_type
        self._value_type = value_type
        self._name = name

    async def read(self) -> Sample[U]:
        obj = self._dispatcher.get_property(self._actor_type, self._value_type, self._name)
        return await obj.read()


class _ProxyDataWatcher[T, U]:
    def __init__(
        self,
        dispatcher: ActorDispatcher[T],
        actor_type: type[T],
        value_type: type[DataWatcher[typing.Any, U]],
        name: str,
    ) -> None:
        self._dispatcher = dispatcher
        self._actor_type = actor_type
        self._value_type = value_type
        self._name = name

    async def read(self) -> Sample[U]:
        obj = self._dispatcher.get_property(self._actor_type, self._value_type, self._name)
        return await obj.read()

    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        obj = self._dispatcher.get_property(self._actor_type, self._value_type, self._name)
        async with obj.watch() as reader:
            yield reader


class _ProxyFakeDataWatcher[T]:
    def __init__(
        self, dispatcher: ActorDispatcher[T], actor_type: type[T], value_type: type[FakeDataWatcher[T]], name: str
    ) -> None:
        self._dispatcher = dispatcher
        self._actor_type = actor_type
        self._value_type = value_type
        self._name = name

    async def read(self) -> Sample[T]:
        obj = self._dispatcher.get_property(self._actor_type, self._value_type, self._name)
        return await obj.read()

    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[T]]]:
        obj = self._dispatcher.get_property(self._actor_type, self._value_type, self._name)
        async with obj.watch() as reader:
            yield reader


battery = _ProxyDataAccessRead(_evo_dispatcher, Evo, DataAccessRead, "_property_battery")
color_codes = _ProxyDataWatcher(_evo_dispatcher, Evo, DataWatcher, "_watcher_color_codes")
line_color = _ProxyDataWatcher(_evo_dispatcher, Evo, DataWatcher, "_watcher_line_color")
surface_color = _ProxyDataWatcher(_evo_dispatcher, Evo, DataWatcher, "_watcher_surface_color")
intersection = _ProxyFakeDataWatcher(_evo_dispatcher, Evo, FakeDataWatcher, "_intersection")


async def move(distance_m: float, speed_mps: float) -> None:
    await _evo_dispatcher.acall(Evo, Evo.move, distance_m, speed_mps)


async def rotate(angle_deg: float, angular_speed_degps: float) -> None:
    await _evo_dispatcher.acall(Evo, Evo.rotate, angle_deg, angular_speed_degps)


async def set_velocity(linear_mps: float, angular_degps: float, duration_s: float) -> None:
    await _evo_dispatcher.acall(Evo, Evo.set_velocity, linear_mps, angular_degps, duration_s)


async def emit_tone(frequency_hz: int, duration_s: float, volume: int) -> None:
    await _evo_dispatcher.acall(Evo, Evo.emit_tone, frequency_hz, duration_s, volume)


async def emit_note(note: TNote, octave: int, duration_s: float, volume: int) -> None:
    await _evo_dispatcher.acall(Evo, Evo.emit_note, note, octave, duration_s, volume)


async def play_audio(name: str) -> None:
    await _evo_dispatcher.acall(Evo, Evo.play_audio, name)


async def set_led(mask: LEDMask, color: Color) -> None:
    await _evo_dispatcher.acall(Evo, Evo.set_led, mask, color)


async def follow_line(direction: Direction) -> None:
    await _evo_dispatcher.acall(Evo, Evo.follow_line, direction)


async def align_with_line(direction: Direction) -> None:
    await _evo_dispatcher.acall(Evo, Evo.align_with_line, direction)


async def set_follow_line_speed(speed_mps: float) -> None:
    await _evo_dispatcher.acall(Evo, Evo.set_follow_line_speed, speed_mps)
