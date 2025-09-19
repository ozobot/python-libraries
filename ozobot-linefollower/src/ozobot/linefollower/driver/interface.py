from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Protocol, Self

from ozobot.linefollower.datatypes import Color, ColorCode, Direction, LEDMask, Sample


class Deserializable(Protocol):
    @classmethod
    def deserialize(cls, data: bytes) -> Self: ...


class Serializable(Protocol):
    def serialize(self) -> bytes: ...


class ReadableRegion[T](Protocol):
    async def read(self) -> Sample[T]: ...


class ReadableWritableRegion[T](ReadableRegion, Protocol):
    async def write(self, data: T) -> None: ...


class ReadableWatchableRegion[T](ReadableRegion[T], Protocol):
    def watch(self) -> AbstractAsyncContextManager[AsyncIterator[Sample[T]]]: ...


class VirtualMemoryRegions(Protocol):
    @property
    def line_following_speed(self) -> ReadableWritableRegion[float]: ...

    @property
    def color_code(self) -> ReadableWatchableRegion[ColorCode]: ...

    @property
    def line_color(self) -> ReadableWatchableRegion[Color]: ...

    @property
    def surface_color(self) -> ReadableWatchableRegion[Color]: ...

    @property
    def intersection(self) -> ReadableWatchableRegion[Direction]: ...


class Driver(Protocol):
    @property
    def memory(self) -> VirtualMemoryRegions: ...

    async def move(self, distance_m: float, speed_ms: float) -> None: ...

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None: ...

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None: ...

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None: ...

    async def play_audio(self, audio_name: str) -> None: ...

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None: ...

    async def line_navigation(self, direction: Direction, follow: bool) -> None: ...
