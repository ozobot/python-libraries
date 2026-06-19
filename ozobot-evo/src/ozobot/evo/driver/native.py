from __future__ import annotations

import contextlib
import math
import typing
from uuid import UUID

from ozobot.ble.connection import open_client
from ozobot.evo import conversions
from ozobot.evo.api.watchers import (
    RefCountedWatcher,
    WatcherManager,
)
from ozobot.evo.driver.responses import handle_events, handle_response
from ozobot.evo.driver.shared import geometry
from ozobot.evo.protocol import AsyncControl, Types, VirtualMemory
from ozobot.linefollower import ColorCode
from ozobot.linefollower.api.data_access import (
    DataWatcherProxy,
    EventWatcher,
    EventWatcherQueue,
    WatcherOutputContainer,
    WatcherOutputContainerRunner,
    deduplicate_samples,
)
from ozobot.linefollower.datatypes import (
    Direction,
    LEDMask,
    Sample,
    SampleWithoutTimestamp,
)
from ozobot.linefollower.driver.interface import Deserializable, Serializable

_SERVICE_UUID = UUID("8903136c-5f13-4548-a885-c58779136801")
_CHARACTERISTIC_UUID = UUID("8903136c-5f13-4548-a885-c58779136802")


class _DeserializeAndSerializable(Deserializable, Serializable, typing.Protocol):
    pass


class _DeserializableWithTimestamp(Deserializable, typing.Protocol):
    timestamp: int


class MemoryProperty[T](typing.Protocol):
    address: int
    type: type[T]

    @property
    def size(self) -> int: ...


async def _stop_execution(control: AsyncControl, *, request_id: int) -> None:
    async with control.StopExecution(request_id) as (resp, _):
        pass  # there's nothing to check in the StopExecution response


class NativeMemoryRegions:
    def __init__(self, control: AsyncControl, watcher_manager: WatcherManager) -> None:
        self.intersection_queue = EventWatcherQueue(SampleWithoutTimestamp(Direction(1)))
        self.intersection = EventWatcher(self.intersection_queue)

        self.line_following_speed = NativeDataAccessReadWrite(
            control,
            VirtualMemory.lineNavigationSpeed,
            lambda s8_24: float(s8_24) * 1000,
            lambda fl: Types.S8_24(fl / 1000),
        )
        self.color_code: NativeDataWatcher[Types.ColorCode, SampleWithoutTimestamp[ColorCode]] = NativeDataWatcher(
            control,
            VirtualMemory.colorCode,
            watcher_manager,
            lambda c: Sample(conversions.color_code_from_protocol(c), c.timestamp),
            skip_initial_value=True,
        )
        self.line_color = NativeDataWatcher(
            control,
            VirtualMemory.lineColor,
            watcher_manager,
            lambda c: Sample(conversions.line_color_from_protocol(c), c.timestamp),
        )
        self.surface_color = NativeDataWatcher(
            control,
            VirtualMemory.surfaceColor,
            watcher_manager,
            lambda c: Sample(conversions.surface_color_from_protocol(c), c.timestamp),
        )

        proximity = NativeDataWatcher(
            control, VirtualMemory.irProximity, watcher_manager, from_protocol=lambda x: Sample(x, x.timestamp)
        )

        self.ir_message_right_front = NativeDataWatcher(
            control,
            VirtualMemory.irMessageRightFront,
            watcher_manager,
            lambda m: Sample(conversions.ir_message_from_protocol(m), m.timestamp),
        )

        self.ir_message_left_front = NativeDataWatcher(
            control,
            VirtualMemory.irMessageLeftFront,
            watcher_manager,
            lambda m: Sample(conversions.ir_message_from_protocol(m), m.timestamp),
        )

        self.ir_message_right_rear = NativeDataWatcher(
            control,
            VirtualMemory.irMessageRightRear,
            watcher_manager,
            lambda m: Sample(conversions.ir_message_from_protocol(m), m.timestamp),
        )

        self.ir_message_left_rear = NativeDataWatcher(
            control,
            VirtualMemory.irMessageLeftRear,
            watcher_manager,
            lambda m: Sample(conversions.ir_message_from_protocol(m), m.timestamp),
        )

        self.button = NativeDataWatcher(
            control, VirtualMemory.button, watcher_manager, lambda b: Sample(b.press, b.timestamp)
        )
        self.charger = NativeDataWatcher(
            control,
            VirtualMemory.chargerState,
            watcher_manager,
            lambda c: Sample(conversions.charger_state_from_protocol(c), c.timestamp),
        )

        self.obstacle_right_front = DataWatcherProxy(
            proximity, convert=lambda p: Sample(p.value.rightFront, p.timestamp)
        )
        self.obstacle_left_front = DataWatcherProxy(proximity, convert=lambda p: Sample(p.value.leftFront, p.timestamp))
        self.obstacle_right_rear = DataWatcherProxy(proximity, convert=lambda p: Sample(p.value.rightRear, p.timestamp))
        self.obstacle_left_rear = DataWatcherProxy(proximity, convert=lambda p: Sample(p.value.leftRear, p.timestamp))

        self.geometry = geometry


class NativeDataAccessRead[T: Deserializable, U]:
    def __init__(
        self, control: AsyncControl, property: MemoryProperty[T], from_protocol: typing.Callable[[T], U]
    ) -> None:
        self._control = control
        self._property = property
        self._from_protocol = from_protocol

    async def _read_raw(self) -> T:
        async with self._control.MemRead(self._property.address, self._property.size) as (resp, _):
            handle_response("MemRead", resp)

        return self._property.type.deserialize(bytes(resp.data))

    async def read(self) -> U:
        val = await self._read_raw()
        return self._from_protocol(val)


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
        self._open_watcher_count = 0

    async def write(self, data: U) -> None:
        raw_data = self._to_protocol(data).serialize()
        async with self._control.MemWrite(self._property.address, self._property.size, raw_data) as (resp, _):
            handle_response("MemWrite", resp)


class NativeDataWatcher[T: _DeserializableWithTimestamp, U](NativeDataAccessRead[T, U]):
    def __init__(
        self,
        control: AsyncControl,
        property: MemoryProperty[T],
        watcher_manager: WatcherManager,
        from_protocol: typing.Callable[[T], U],
        skip_initial_value: bool = False,
    ) -> None:
        super().__init__(control, property, from_protocol)
        self._watcher = RefCountedWatcher(property, watcher_manager)
        self._from_protocol = from_protocol
        self._skip_initial_value = skip_initial_value

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[WatcherOutputContainer[U]]:
        async def _convert_iterator(it: typing.AsyncIterator[T]) -> typing.AsyncGenerator[U, None]:
            async for data in it:
                yield self._from_protocol(data)

        async with WatcherOutputContainerRunner[U]() as container_runner:
            async with self._watcher.watch() as unbuffered_reader:
                if self._skip_initial_value:
                    initial_value = (await self._read_raw()).timestamp
                else:
                    initial_value = None

                await container_runner.start(
                    _convert_iterator(deduplicate_samples(unbuffered_reader, initial_value=initial_value))
                )
                yield container_runner.output_container


class EvoNativeDriver:
    def __init__(self, control: AsyncControl, watcher_manager: WatcherManager) -> None:
        self._control = control
        self.memory = NativeMemoryRegions(control, watcher_manager)

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        address: str | None = None,
        id: str | None = None,
        name: str | None = None,
    ) -> typing.AsyncIterator[EvoNativeDriver]:
        async with open_client(address=address, id=id, name=name) as client:
            char = client.get_characteristic(_SERVICE_UUID, _CHARACTERISTIC_UUID, mtu_size_override=23)
            control = AsyncControl(char)
            await _stop_execution(control, request_id=0)

            async with WatcherManager.open(control) as watcher_manager:
                yield cls(control, watcher_manager)

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

    async def play_tone(self, frequency_hz: int, duration_ms: int) -> None:
        request_id = self._control.get_next_request_id()
        volume = 100  # volume parameter is currently ignored by evo
        async with self._control.PlayTone(request_id, frequency_hz, duration_ms, volume) as (
            resp,
            evts,
        ):
            async with self._cancellation(request_id=request_id):
                await handle_events("PlayTone", evts)

    async def play_audio_asset(self, asset_name: str) -> None:
        filepath = f"/system/audio/{asset_name}.wav"

        request_id = self._control.get_next_request_id()
        async with self._control.ExecuteFile(request_id, filepath) as (resp, evts):
            async with self._cancellation(request_id=request_id):
                handle_response("ExecuteFile", resp)
                await handle_events("ExecuteFile", evts)

    async def set_led(self, mask: LEDMask, red: float, green: float, blue: float) -> None:
        protocol_mask = conversions.led_to_protocol(mask)
        async with self._control.SetLED(protocol_mask, int(red * 255), int(green * 255), int(blue * 255), 255) as (
            response,
            _,
        ):
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
        sample = SampleWithoutTimestamp(intersection)
        await self.memory.intersection_queue.write(sample)

    @contextlib.asynccontextmanager
    async def _cancellation(self, *, request_id: int) -> typing.AsyncIterator[None]:
        try:
            yield
        except BaseException as e:
            await _stop_execution(self._control, request_id=request_id)
            raise e
