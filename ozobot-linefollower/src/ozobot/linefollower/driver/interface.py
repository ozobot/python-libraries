from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import AbstractAsyncContextManager
from typing import Protocol, Self

from ozobot.linefollower.datatypes import (
    ClassifiedColor,
    ColorCode,
    Direction,
    IRMessage,
    LEDMask,
    RobotGeometry,
    Sample,
    SampleWithoutTimestamp,
)


class Deserializable(Protocol):
    @classmethod
    def deserialize(cls, data: bytes) -> Self: ...


class Serializable(Protocol):
    def serialize(self) -> bytes: ...


class ReadableRegion[T](Protocol):
    async def read(self) -> T: ...


class ReadableWritableRegion[T](ReadableRegion, Protocol):
    async def write(self, data: T) -> None: ...


class WatchableRegion[T](Protocol):
    def watch(self) -> AbstractAsyncContextManager[AsyncIterator[T]]: ...


class ReadableWatchableRegion[T](ReadableRegion[T], WatchableRegion[T], Protocol): ...


class VirtualMemoryRegions(Protocol):
    @property
    def geometry(self) -> ReadableRegion[RobotGeometry]: ...

    @property
    def line_following_speed(self) -> ReadableWritableRegion[float]: ...

    @property
    def color_code(self) -> WatchableRegion[SampleWithoutTimestamp[ColorCode]]: ...

    @property
    def line_color(self) -> ReadableWatchableRegion[Sample[ClassifiedColor | None]]: ...

    @property
    def surface_color(self) -> ReadableWatchableRegion[Sample[ClassifiedColor | None]]: ...

    @property
    def intersection(self) -> WatchableRegion[SampleWithoutTimestamp[Direction]]: ...

    @property
    def ir_message_left_front(self) -> ReadableWatchableRegion[Sample[IRMessage]]: ...

    @property
    def ir_message_right_front(self) -> ReadableWatchableRegion[Sample[IRMessage]]: ...

    @property
    def proximity_right_front(self) -> ReadableWatchableRegion[Sample[float]]: ...

    @property
    def proximity_left_front(self) -> ReadableWatchableRegion[Sample[float]]: ...


class Driver(Protocol):
    @property
    def memory(self) -> VirtualMemoryRegions: ...

    async def move(self, distance_mm: float, speed_mmps: float) -> None: ...

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None: ...

    async def velocity(self, linear_mmps: float, angular_degps: float, duration_ms: int) -> None: ...

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None: ...

    async def play_audio(self, audio_name: str) -> None: ...

    async def set_led(self, mask: LEDMask, red: float, green: float, blue: float) -> None: ...

    async def line_navigation(self, direction: Direction, follow: bool) -> None: ...
