from __future__ import annotations

import enum

from typing import AsyncContextManager, Literal, Protocol, TypeAlias


TDirections: TypeAlias = Literal["backward", "left", "right", "straight"]


class LEDMask(enum.Flag):
    FRONT_CENTER = enum.auto()
    FRONT_LEFT = enum.auto()
    FRONT_LEFT_CENTER = enum.auto()
    FRONT_RIGHT = enum.auto()
    FRONT_RIGHT_CENTER = enum.auto()
    TOP = enum.auto()


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

    async def line_navigation(self, directions: TDirections, follow: bool) -> None: ...

    async def follow_speed(self, speed_mps: float) -> None: ...
