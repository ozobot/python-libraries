from __future__ import annotations

from typing import AsyncContextManager, Protocol, Self

from ozobot.linefollower.api.watchers import WatcherSubscription
from ozobot.linefollower.datatypes import Direction, LEDMask


class Deserializable(Protocol):
    @classmethod
    def deserialize(cls, data: bytes) -> Self: ...


class Serializable(Protocol):
    def serialize(self) -> bytes: ...


class MemoryProperty[T](Protocol):
    address: int
    type: type[T]

    @property
    def size(self) -> int: ...


class Driver(Protocol):
    @classmethod
    def open(
        cls,
        address: str | None = None,
        id_prefix: str | None = None,
        name: str | None = None,
    ) -> AsyncContextManager[Driver]: ...

    async def move(self, distance_m: float, speed_ms: float) -> None: ...

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None: ...

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None: ...

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None: ...

    async def play_audio(self, audio_name: str) -> None: ...

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None: ...

    async def line_navigation(self, direction: Direction, follow: bool) -> Direction: ...

    async def follow_speed(self, speed_mps: float) -> None: ...

    async def stop_all(self) -> None: ...

    def watch[T: Deserializable](
        self, config: tuple[MemoryProperty[T], ...]
    ) -> AsyncContextManager[tuple[WatcherSubscription[T], ...]]: ...

    async def mem_read[T: Deserializable](self, prop: MemoryProperty[T]) -> T: ...

    async def mem_write[T: Serializable](self, prop: MemoryProperty[T], value: T) -> None: ...
