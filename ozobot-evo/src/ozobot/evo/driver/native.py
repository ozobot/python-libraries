from __future__ import annotations

import contextlib
import math
import typing
from uuid import UUID

from ozobot.ble.connection import open_client
from ozobot.evo import conversions
from ozobot.evo.api.watchers import LineFollowerWatcher, WatcherSubscription
from ozobot.evo.driver.responses import handle_events, handle_response
from ozobot.evo.driver.shared import map_audio_name_to_filename
from ozobot.evo.protocol import AsyncControl, Types, VirtualMemory
from ozobot.linefollower.api.data_access import DataWatcherProxy, EventWatcher, EventWatcherQueue
from ozobot.linefollower.conversions import sample_from_protocol
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample
from ozobot.linefollower.driver.interface import Deserializable, Serializable

_SERVICE_UUID = UUID("8903136c-5f13-4548-a885-c58779136801")
_CHARACTERISTIC_UUID = UUID("8903136c-5f13-4548-a885-c58779136802")


@typing.runtime_checkable
class _HasTimestamp(typing.Protocol):
    timestamp: int


class _DeserializeAndSerializable(Deserializable, Serializable, typing.Protocol):
    pass


class MemoryProperty[T](typing.Protocol):
    address: int
    type: type[T]

    @property
    def size(self) -> int: ...


type _TWatchers = tuple[
    WatcherSubscription[Types.ColorCode],
    WatcherSubscription[Types.LineColor],
    WatcherSubscription[Types.SurfaceColor],
    WatcherSubscription[Types.IRProximity],
    WatcherSubscription[Types.IRMessage],
    WatcherSubscription[Types.IRMessage],
    WatcherSubscription[Types.IRMessage],
    WatcherSubscription[Types.IRMessage],
    WatcherSubscription[Types.Button],
    WatcherSubscription[Types.ChargerState],
]


async def _stop_execution(control: AsyncControl, *, request_id: int) -> None:
    async with control.StopExecution(request_id) as (resp, _):
        pass  # there's nothing to check in the StopExecution response


class NativeMemoryRegions:
    def __init__(self, control: AsyncControl, watchers: _TWatchers) -> None:
        color_code_watcher, line_color_watcher, surface_color_watcher, proximity_watcher = watchers[:4]
        ir_right_front_watcher, ir_left_front_watcher, ir_right_rear_watcher, ir_left_rear_watcher = watchers[4:8]
        button_watcher, charger_watcher = watchers[8:10]

        self.intersection_queue = EventWatcherQueue(Sample(Direction(0), 0))
        self.intersection = EventWatcher(self.intersection_queue)

        self.line_following_speed = NativeDataAccessReadWrite(
            control,
            VirtualMemory.lineNavigationSpeed,
            lambda s8_24: float(s8_24) * 1000,
            lambda fl: Types.S8_24(fl / 1000),
        )
        self.color_code = NativeDataWatcher(
            control, VirtualMemory.colorCode, color_code_watcher, conversions.color_code_from_protocol
        )
        self.line_color = NativeDataWatcher(
            control, VirtualMemory.lineColor, line_color_watcher, conversions.line_color_from_protocol
        )
        self.surface_color = NativeDataWatcher(
            control, VirtualMemory.surfaceColor, surface_color_watcher, conversions.surface_color_from_protocol
        )

        proximity = NativeDataWatcher(
            control, VirtualMemory.irProximity, proximity_watcher, conversions.proximity_from_protocol
        )

        self.proximity_right_front = DataWatcherProxy(proximity, convert=lambda p: p.right_front)
        self.proximity_left_front = DataWatcherProxy(proximity, convert=lambda p: p.left_front)
        self.proximity_right_rear = DataWatcherProxy(proximity, convert=lambda p: p.right_rear)
        self.proximity_left_rear = DataWatcherProxy(proximity, convert=lambda p: p.left_rear)

        self.ir_message_right_front = NativeDataWatcher(
            control, VirtualMemory.irMessageRightFront, ir_right_front_watcher, conversions.ir_message_from_protocol
        )

        self.ir_message_left_front = NativeDataWatcher(
            control, VirtualMemory.irMessageLeftFront, ir_left_front_watcher, conversions.ir_message_from_protocol
        )

        self.ir_message_right_rear = NativeDataWatcher(
            control, VirtualMemory.irMessageRightRear, ir_right_rear_watcher, conversions.ir_message_from_protocol
        )

        self.ir_message_left_rear = NativeDataWatcher(
            control, VirtualMemory.irMessageLeftRear, ir_left_rear_watcher, conversions.ir_message_from_protocol
        )

        self.button = NativeDataWatcher(control, VirtualMemory.button, button_watcher, lambda b: b.press)
        self.charger = NativeDataWatcher(
            control, VirtualMemory.chargerState, charger_watcher, conversions.charger_state_from_protocol
        )


class NativeDataAccessRead[T: Deserializable, U]:
    def __init__(
        self, control: AsyncControl, property: MemoryProperty[T], from_protocol: typing.Callable[[T], U]
    ) -> None:
        self._control = control
        self._property = property
        self._from_protocol = from_protocol

    async def read(self) -> Sample[U]:
        async with self._control.MemRead(self._property.address, self._property.size) as (resp, _):
            handle_response("MemRead", resp)

        val = self._property.type.deserialize(bytes(resp.data))
        if isinstance(val, _HasTimestamp):
            return sample_from_protocol(val, self._from_protocol)
        else:
            return Sample.now(self._from_protocol(val))


class NativeDataAccessReadWrite[T: _DeserializeAndSerializable, U](NativeDataAccessRead[T, U]):
    def __init__(
        self,
        control: AsyncControl,
        property: MemoryProperty[T],
        from_protocol: typing.Callable[[T], U],
        to_protocol: typing.Callable[[U], T],
    ) -> None:
        super().__init__(control, property, from_protocol)
        self._to_protocol = to_protocol

    async def write(self, data: U) -> None:
        raw_data = self._to_protocol(data).serialize()
        async with self._control.MemWrite(self._property.address, self._property.size, raw_data) as (resp, _):
            handle_response("MemWrite", resp)


class NativeDataWatcher[T: Deserializable, U]:
    def __init__(
        self,
        control: AsyncControl,
        property: MemoryProperty[T],
        watcher: WatcherSubscription[T],
        from_protocol: typing.Callable[[T], U],
    ) -> None:
        self._watcher = watcher
        self._reader = NativeDataAccessRead(control, property, from_protocol)
        self._from_protocol = from_protocol

    async def read(self) -> Sample[U]:
        return await self._reader.read()

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
        async with self._watcher.watch() as reader:

            async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
                async for r in reader:
                    if isinstance(r, _HasTimestamp):
                        yield sample_from_protocol(r, self._from_protocol)
                    else:
                        yield Sample.now(self._from_protocol(r))

            yield _reader_converted()


@contextlib.asynccontextmanager
async def create_memory_regions_structure(control: AsyncControl) -> typing.AsyncIterator[NativeMemoryRegions]:
    config = (
        VirtualMemory.colorCode,
        VirtualMemory.lineColor,
        VirtualMemory.surfaceColor,
        VirtualMemory.irProximity,
        VirtualMemory.irMessageRightFront,
        VirtualMemory.irMessageLeftFront,
        VirtualMemory.irMessageRightRear,
        VirtualMemory.irMessageLeftRear,
        VirtualMemory.button,
        VirtualMemory.chargerState,
    )

    watcher = LineFollowerWatcher(control)

    # Until typing allows tuple mapping, we need to do the casts below. See: https://github.com/python/typing/issues/1383
    type TExpectedInput = tuple[MemoryProperty[Types.ColorCode | Types.LineColor | Types.SurfaceColor]]

    async with watcher.watch(typing.cast(TExpectedInput, config)) as subscriptions:
        yield NativeMemoryRegions(control, typing.cast(_TWatchers, subscriptions))


class NativeDriver:
    def __init__(self, control: AsyncControl, memory: NativeMemoryRegions) -> None:
        self._control = control
        self.memory = memory

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncIterator[NativeDriver]:
        async with open_client(address=address, id=id, name=name) as client:
            char = client.get_characteristic(_SERVICE_UUID, _CHARACTERISTIC_UUID)
            control = AsyncControl(char)
            await _stop_execution(control, request_id=0)

            async with create_memory_regions_structure(control) as memory:
                yield cls(control, memory)

    async def move(self, distance_mm: float, speed_mmps: float) -> None:
        request_id = self._control.get_next_request_id()
        async with self._control.MoveStraight(request_id, distance_mm / 1000, speed_mmps / 1000) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                await handle_events("MoveStraight", evts)

    async def rotate(self, angle_deg: float, angular_speed_degps: float) -> None:
        request_id = self._control.get_next_request_id()
        async with self._control.Rotate(request_id, math.radians(angle_deg), math.radians(angular_speed_degps)) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                await handle_events("Rotate", evts)

    async def velocity(self, linear_mmps: float, angular_degps: float, duration_ms: int) -> None:
        request_id = self._control.get_next_request_id()
        async with self._control.Velocity(request_id, linear_mmps / 1000, math.radians(angular_degps), duration_ms) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                await handle_events("Velocity", evts)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        request_id = self._control.get_next_request_id()
        async with self._control.PlayTone(request_id, frequency_hz, duration_ms, volume) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                await handle_events("PlayTone", evts)

    async def play_audio(self, audio_name: str) -> None:
        filename = map_audio_name_to_filename(audio_name)
        filepath = f"/system/audio/{filename}.wav"

        request_id = self._control.get_next_request_id()
        async with self._control.ExecuteFile(request_id, filepath) as (resp, evts):
            async with self._cancellation(request_id=request_id):
                handle_response("ExecuteFile", resp)
                await handle_events("ExecuteFile", evts)

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        protocol_mask = conversions.led_to_protocol(mask)
        async with self._control.SetLED(protocol_mask, red, green, blue, 255) as (response, _):
            handle_response("SetLED", response)

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        direction_protocol = conversions.intersection_direction_to_protocol(direction)

        action = Types.LineNavigationAction.Follow if follow else Types.LineNavigationAction.DoNotFollow
        request_id = self._control.get_next_request_id()
        async with self._control.LineNavigation(request_id, direction_protocol, action) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                event = await handle_events("LineNavigation", evts)

        intersection = conversions.intersection_bitmap_from_protocol(event.intersection)
        sample = Sample.now(intersection)
        await self.memory.intersection_queue.write(sample)

    @contextlib.asynccontextmanager
    async def _cancellation(self, *, request_id: int) -> typing.AsyncIterator[None]:
        try:
            yield
        except BaseException as e:
            await _stop_execution(self._control, request_id=request_id)
            raise e
