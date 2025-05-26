from __future__ import annotations

from typing import AsyncContextManager, PropertyMetadata, Protocol, Self

from ozobot.evo.api.watchers import WatcherSubscription
from ozobot.evo.datatypes import LEDMask, TDirection


class _Deserializable(Protocol):
    @classmethod
    def deserialize(cls, data: bytes) -> Self: ...


class WatcherConfig[T: _Deserializable](Protocol):
    address: int
    size: int
    type: T


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

    async def execute_file(self, filename: str) -> None: ...

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None: ...

    async def line_navigation(self, direction: TDirection, follow: bool) -> None: ...

    async def follow_speed(self, speed_mps: float) -> None: ...

    async def stop_all(self) -> None: ...

    async def watch[T](self, config: tuple[PropertyMetadata[T], ...]) -> WatcherSubscription[T]: ...
