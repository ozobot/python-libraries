from __future__ import annotations

import asyncio
import contextlib
import datetime
import typing
from uuid import UUID

from ozobot.ari import conversions
from ozobot.ari.exceptions import AriProtocolCommandError

from ozobot.ari.protocol import base, methods, notification, request, types, response
from ozobot.ari.transport import SerializingTransportLayer
from ozobot.ble.connection import open_client
from ozobot.jsonrpc.executor import Executor, Query
from ozobot.linefollower.api.watchers import LineFollowerWatcher, WatcherSubscription
from ozobot.linefollower.conversions import sample_from_protocol
from ozobot.linefollower.datatypes import Direction, LEDMask, Sample
from ozobot.linefollower.driver import Deserializable, VirtualMemoryRegions
from ozobot.webrtc import messaging
from ozobot.webrtc.connection import Channel
from ozobot.webrtc.signaling import negotiation, token

_ROUTING_KEY_SERVICE_UUID = UUID(
    "6b63040a-520e-4d24-0000-65c78f1d0000"
)  # taken from anvil-control/src/lib/ble-setup.ts
_ROUTING_KEY_CHARACTERISTIC_UUID = UUID("6b63040a-520e-4d24-0000-65c78f1d0001")


# class _HasTimestamp(typing.Protocol):
#     timestamp: int


# class _TimestampAndDeserializable(_HasTimestamp, Deserializable, typing.Protocol):
#     pass


# class _HasExecutionState(typing.Protocol):
#     executionState: Types.ExecutionStateEnum


# @typing.runtime_checkable
# class _HasCallStatus(typing.Protocol):
#     callStatus: Types.CallStatus


class _HasResultType(typing.Protocol):
    @property
    def type(self) -> typing.Literal["finished"] | str: ...


class _HasResult(typing.Protocol):
    @property
    def result(self) -> _HasResultType: ...


# class MemoryProperty[T](typing.Protocol):
#     address: int
#     xtype: type[T]

#     @property
#     def size(self) -> int: ...


# type _TWatchers = tuple[
#     WatcherSubscription[Types.ColorCode],
#     WatcherSubscription[Types.LineColor],
#     WatcherSubscription[Types.SurfaceColor],
# ]


# class NativeMemoryRegions(VirtualMemoryRegions):
#     def __init__(self, control: AsyncControl, watchers: _TWatchers) -> None:
#         color_code_watcher, line_color_watcher, surface_color_watcher = watchers

#         self.intersection_queue = EventWatcherQueue(Sample(Direction(0), 0))
#         self.intersection = EventWatcher(self.intersection_queue)

#         self.battery = NativeDataAccessRead(
#             control, VirtualMemory.batteryState, conversions.battery_state_from_protocol
#         )
#         self.color_code = NativeDataWatcher(
#             control, VirtualMemory.colorCode, color_code_watcher, conversions.color_code_from_protocol
#         )
#         self.line_color = NativeDataWatcher(
#             control, VirtualMemory.lineColor, line_color_watcher, conversions.line_color_from_protocol
#         )
#         self.surface_color = NativeDataWatcher(
#             control, VirtualMemory.surfaceColor, surface_color_watcher, conversions.surface_color_from_protocol
#         )


# class NativeDataAccessRead[T: _TimestampAndDeserializable, U]:
#     def __init__(
#         self, control: AsyncControl, property: MemoryProperty[T], from_protocol: typing.Callable[[T], U]
#     ) -> None:
#         self._control = control
#         self._property = property
#         self._from_protocol = from_protocol

#     async def read(self) -> Sample[U]:
#         ret = await self._control.MemRead(self._property.address, self._property.size)
#         val = self._property.type.deserialize(bytes(ret.data))
#         return sample_from_protocol(val, self._from_protocol)


# class NativeDataWatcher[T: _TimestampAndDeserializable, U]:
#     def __init__(
#         self,
#         control: AsyncControl,
#         property: MemoryProperty[T],
#         watcher: WatcherSubscription[T],
#         from_protocol: typing.Callable[[T], U],
#     ) -> None:
#         self._watcher = watcher
#         self._reader = NativeDataAccessRead(control, property, from_protocol)
#         self._from_protocol = from_protocol

#     async def read(self) -> Sample[U]:
#         return await self._reader.read()

#     @contextlib.asynccontextmanager
#     async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[U]]]:
#         async with self._watcher.watch() as reader:

#             async def _reader_converted() -> typing.AsyncIterator[Sample[U]]:
#                 async for r in reader:
#                     yield sample_from_protocol(r, self._from_protocol)

#             yield _reader_converted()


# @contextlib.asynccontextmanager
# async def create_memory_regions_structure(control: AsyncControl) -> typing.AsyncIterator[NativeMemoryRegions]:
#     config = (
#         VirtualMemory.colorCode,
#         VirtualMemory.lineColor,
#         VirtualMemory.surfaceColor,
#     )

#     watcher = LineFollowerWatcher(control)

#     # Until typing allows tuple mapping, we need to do the casts below. See: https://github.com/python/typing/issues/1383
#     type TExpectedInput = tuple[MemoryProperty[Types.ColorCode | Types.LineColor | Types.SurfaceColor]]
#     type TExpectedOutput = tuple[
#         WatcherSubscription[Types.ColorCode],
#         WatcherSubscription[Types.LineColor],
#         WatcherSubscription[Types.SurfaceColor],
#     ]
#     async with watcher.watch(typing.cast(TExpectedInput, config)) as subscriptions:
#         yield NativeMemoryRegions(control, typing.cast(TExpectedOutput, subscriptions))


class _EmptyMemory:
    def __getattr__(self, name):
        raise NotImplementedError("Memory attributes not yet implemented")


async def _get_routing_key_from_ble(
    address: str | None = None,
    id_prefix: str | None = None,
    name: str | None = None,
) -> str:
    async with open_client(name=name, id_prefix=id_prefix, address=address, product="ari") as ble_client:
        char = ble_client.get_characteristic(
            _ROUTING_KEY_SERVICE_UUID,
            _ROUTING_KEY_CHARACTERISTIC_UUID,
        )
        device_id_bytes = await char.read()
        return device_id_bytes.decode("utf8")


async def _create_webrtc_channel(connection_key: str) -> Channel:
    jwt = await token.get_jwt_token(token.TOKEN_ENDPOINT_URL, device_id=connection_key, mode="server")
    config = messaging.MessagingChannelConfig(device_id=connection_key, username="", password=jwt)
    async with messaging.create_channel_factory(config) as channel_factory:
        client = negotiation.SignalingCaller(channel_factory, connection_key)
        connection, channels = await client.signal(channels=("control",))

    return channels[0]


class NativeDriver:
    def __init__(self, executor: Executor) -> None:
        self._executor = executor
        self._next_request_id = 0
        self.memory = typing.cast(VirtualMemoryRegions, _EmptyMemory())

    @classmethod
    @contextlib.asynccontextmanager
    async def open(
        cls,
        address: str | None = None,
        id_prefix: str | None = None,
        name: str | None = None,
        connection_key: str | None = None,
    ) -> typing.AsyncIterator[NativeDriver]:
        if connection_key:
            routing_key = f"anvil.{connection_key}"
        else:
            routing_key = await _get_routing_key_from_ble(address=address, id_prefix=id_prefix, name=name)

        channel = await _create_webrtc_channel(routing_key)

        class WebrtcTransportAdapter:
            async def write(self, data: str) -> None:
                await channel.send(data)

            async def read(self) -> typing.AsyncIterator[str]:
                async for raw_data in channel.receive_str():
                    yield raw_data

        transport = SerializingTransportLayer(WebrtcTransportAdapter())
        async with Executor.create(transport, base.Cancellation) as ex:
            yield cls(ex)

    def _get_next_request_id(self) -> int:
        rid = self._next_request_id
        self._next_request_id += 1
        return rid

    async def move(self, distance_m: float, speed_ms: float) -> None:
        req = request.MoveStraightRequest(
            id=self._get_next_request_id(),
            params=request.MoveStraightRequestParams(distance=distance_m, speed=speed_ms),
        )
        async with Query(req, methods.MOVE_STRAIGHT).execute(self._executor) as q:
            await self._handle_response("MoveStraight", q.response)

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None:
        req = request.RotateRequest(
            id=self._get_next_request_id(),
            params=request.RotateRequestParams(angle=angle_rad, speed=angular_speed_radps),
        )
        async with Query(req, methods.ROTATE).execute(self._executor) as q:
            await self._handle_response("Rotate", q.response)

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None:
        req = request.VelocityRequest(
            id=self._get_next_request_id(),
            params=request.VelocityRequestParams(
                linear_speed=linear_mps, rotation_speed=angular_radps, expiration=duration_ms / 1000
            ),
        )
        async with Query(req, methods.VELOCITY).execute(self._executor) as q:
            await self._handle_response("Velocity", q.response)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        req = request.PlayToneRequest(
            id=self._get_next_request_id(),
            params=request.PlayToneRequestParams(frequency=frequency_hz, duration=duration_ms / 1000, volume=volume),
        )
        async with Query(req, methods.PLAY_TONE).execute(self._executor) as q:
            await self._handle_response("PlayTone", q.response)

    async def play_audio(self, audio_name: str) -> None:
        req = request.PlaySoundRequest(
            id=self._get_next_request_id(),
            params=request.PlaySoundRequestParams(name=audio_name, loop=False, volume=1.0),
        )
        async with Query(req, methods.PLAY_SOUND).execute(self._executor) as q:
            await self._handle_response("PlaySound", q.response)

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        lights = conversions.led_to_protocol(mask)
        color = types.Color(red=red, green=green, blue=blue)
        req = request.SetLEDRequest(
            id=self._get_next_request_id(), params=request.SetLEDRequestParams(lights=lights, color=color)
        )
        async with Query(req, methods.SET_LED).execute(self._executor) as q:
            await self._handle_response("SetLED", q.response)

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        direction_protocol = conversions.intersection_direction_to_protocol(direction)
        follow_arg = "Follow" if follow else "DoNotFollow"
        req = request.LineNavigationRequest(
            id=self._get_next_request_id(),
            params=request.LineNavigationRequestParams(
                direction=direction_protocol, follow=follow_arg, detect_color_codes=True
            ),
        )
        async with Query(req, methods.LINE_NAVIGATION).execute(self._executor) as q, asyncio.TaskGroup() as tg:
            notifications_task = tg.create_task(self._process_line_navigation_notifications(q.notifications))
            try:
                await self._handle_response("LineNavigation", q.response)
            finally:
                notifications_task.cancel()

    async def _process_line_navigation_notifications(
        self, it: typing.AsyncIterator[notification.LineNavigationNotification]
    ) -> None:
        async for msg in it:
            match msg.result:
                case types.Intersection():
                    # TODO: write intersection to event queue
                    # intersection = conversions.intersection_bitmap_from_protocol(event.intersection)
                    # timestamp = datetime.datetime.now()
                    # sample = Sample(intersection, timestamp)
                    # await self.memory.intersection_queue.write(sample)
                    pass
                case notification.LineNavigationColorNotificationBody():
                    # TODO: write color code to event queue
                    pass
                case _:
                    typing.assert_never(msg.result)

    # async def follow_speed(self, speed_mps: float) -> None:
    #     config = VirtualMemory.lineNavigationSpeed
    #     await self._control.MemWrite(config.address, config.size, Types.S8_24(speed_mps).serialize())

    async def _handle_response(self, function_name: str, resp: typing.Awaitable[_HasResult]) -> None:
        val = await resp
        if val.result.type != "finished":
            raise AriProtocolCommandError(function_name, val.result.type, description="call failed")
