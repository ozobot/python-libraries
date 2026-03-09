from __future__ import annotations

from contextlib import AbstractAsyncContextManager
from typing import Protocol, Self

from ozobot.linefollower.api.data_access import WatcherOutputContainer
from ozobot.linefollower.datatypes import (
    ColorCode,
    Direction,
    IRMessage,
    LEDMask,
    NamedColor,
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
    async def read(self) -> T:
        """
        Read a single data sample from the memory region.

        One-time readout of data from robot. While simple, calling this in loop can be slow and
        does not guarantee all data changes will be read out (i.e., when data changes multiple times between readouts).

        Useful for initial readouts or reading constant data.
        """


class ReadableWritableRegion[T](ReadableRegion, Protocol):
    async def write(self, data: T) -> None:
        """
        Write data to the robot.
        """


class WatchableRegion[T](Protocol):
    def watch(self) -> AbstractAsyncContextManager[WatcherOutputContainer[T]]:
        """
        Watch for data changes.

        Continuously watches given data region, emitting a data sample on change. More verbose than :py:attr:`read` but guarantees
        all the changes will be read.

        The property is in fact an asynchronous context manager which starts the monitoring on entering the context and
        stops it on exiting the context. The context manager yields a container that can be used as asynchronous iterator or
        as object with :py:meth:`WatcherOutputContainer.collect` which returns a list of collected samples. The container is valid even after the context has been closed.

        :return: Asynchronous context manager :py:class:`WatcherOutputContainer` on enter

        .. codeblock:: python
            async with robot.data.example_region.watch() as container:
                async for sample in aiter(container):
                    print(sample)

            samples = container.collect()
            print(samples)
        """


class ReadableWatchableRegion[T](ReadableRegion[T], WatchableRegion[T], Protocol): ...


class VirtualMemoryRegions(Protocol):
    """
    Robot related configuration, constants and sensor readouts.
    """

    @property
    def geometry(self) -> ReadableRegion[RobotGeometry]:
        """
        Robot geometry.
        """

    @property
    def line_following_speed(self) -> ReadableWritableRegion[float]:
        """
        Line following speed in mm/s.
        """

    @property
    def color_code(self) -> WatchableRegion[SampleWithoutTimestamp[ColorCode]]:
        """
        Color codes detected during line following.
        """

    @property
    def line_color(self) -> ReadableWatchableRegion[Sample[NamedColor | None]]:
        """
        Line color detected.

        Classified color detected by the line sensor. Returns `None` if the color cannot be classified.
        """

    @property
    def surface_color(self) -> ReadableWatchableRegion[Sample[NamedColor | None]]:
        """
        Surface color detected.

        Classified color detected by the surface sensor. Returns `None` if the color cannot be classified.
        """

    @property
    def intersection(self) -> WatchableRegion[SampleWithoutTimestamp[Direction]]:
        """
        Intersections detected during line following.
        """

    @property
    def ir_message_left_front(self) -> ReadableWatchableRegion[Sample[IRMessage]]:
        """
        Message received by the left front IR sensor.
        """

    @property
    def ir_message_right_front(self) -> ReadableWatchableRegion[Sample[IRMessage]]:
        """
        Message received by the right front IR sensor.
        """

    @property
    def obstacle_right_front(self) -> ReadableWatchableRegion[Sample[float]]:
        """
        Right front IR sensor's measured intensity reflected from obstacle.
        """

    @property
    def obstacle_left_front(self) -> ReadableWatchableRegion[Sample[float]]:
        """
        Left front IR sensor's measured intensity reflected from obstacle.
        """


class Driver(Protocol):
    @property
    def memory(self) -> VirtualMemoryRegions: ...

    async def move(self, distance_mm: float, speed_mmps: float) -> None: ...

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None: ...

    async def velocity(self, linear_mmps: float, angular_degps: float, duration_ms: int) -> None: ...

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None: ...

    async def play_audio_asset(self, audio_name: str) -> None: ...

    async def set_led(self, mask: LEDMask, red: float, green: float, blue: float) -> None: ...

    async def line_navigation(self, direction: Direction, follow: bool) -> None: ...
