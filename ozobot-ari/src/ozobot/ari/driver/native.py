from __future__ import annotations

import asyncio
import contextlib
import typing
from uuid import UUID

from ozobot.ari import conversions
from ozobot.ari.exceptions import AriProtocolCommandError, MemoryReadUnsuccessfulError, MemoryWriteUnsuccessfulError
from ozobot.ari.protocol import base, memread, memwrite, methods, notification, request, types
from ozobot.ari.protocol.memread import MemReadResponseBody
from ozobot.ari.protocol.memwrite import MemWriteRequestParams
from ozobot.ari.transport import SerializingTransportLayer
from ozobot.ble.connection import open_client
from ozobot.jsonrpc.executor import Executor, Query
from ozobot.linefollower.api.data_access import EventWatcher, EventWatcherQueue
from ozobot.linefollower.conversions import sample_from_protocol
from ozobot.linefollower.datatypes import ColorCode, Direction, LEDMask, Sample
from ozobot.linefollower.driver import VirtualMemoryRegions
from ozobot.webrtc import messaging
from ozobot.webrtc.connection import Channel
from ozobot.webrtc.signaling import negotiation, token

_ROUTING_KEY_SERVICE_UUID = UUID(
    "6b63040a-520e-4d24-0000-65c78f1d0000"
)  # taken from anvil-control/src/lib/ble-setup.ts
_ROUTING_KEY_CHARACTERISTIC_UUID = UUID("6b63040a-520e-4d24-0000-65c78f1d0001")


@typing.runtime_checkable
class _HasTimestamp(typing.Protocol):
    timestamp: int


class _HasResultType(typing.Protocol):
    @property
    def type(self) -> typing.Literal["finished"] | str: ...


class _HasResult(typing.Protocol):
    @property
    def result(self) -> _HasResultType: ...


class NativeMemoryRegions(VirtualMemoryRegions):
    def __init__(self, executor: Executor, request_id: _RequestIdCounter) -> None:
        self.intersection_queue = EventWatcherQueue(Sample.now(Direction(0)))
        self.intersection = EventWatcher(self.intersection_queue)

        self.color_code_queue = EventWatcherQueue(Sample.now(ColorCode(colors=tuple())))
        self.color_code = EventWatcher(self.color_code_queue)

        self.line_following_speed = NativeDataAccessReadWrite(
            executor,
            request_id,
            "lineFollowingSpeed",
            response_type=memread.MemReadResponseLinearVelocity,
            from_protocol=lambda r: r.velocity,
            to_protocol=lambda v: memwrite.MemWriteRequestLineFollowingSpeedParams(value=v),
        )

        self.surface_color = NativeDataAccessRead(
            executor,
            request_id,
            "surfaceColor",
            response_type=memread.MemReadResponseSurfaceColor,
            from_protocol=lambda resp: conversions.color_from_protocol(resp.color),
        )
        self.line_color = NativeDataAccessRead(
            executor,
            request_id,
            "lineColor",
            response_type=memread.MemReadResponseLineColor,
            from_protocol=lambda resp: conversions.color_from_protocol(resp.color),
        )


class _RequestIdCounter:
    def __init__(self) -> None:
        self._next_request_id = 0

    def get_next(self) -> int:
        rid = self._next_request_id
        self._next_request_id += 1
        return rid


class NativeDataAccessRead[TProtoFrom: MemReadResponseBody, TLib]:
    def __init__(
        self,
        executor: Executor,
        id_counter: _RequestIdCounter,
        name: str,
        *,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
    ) -> None:
        self._executor = executor
        self._name = name
        self._type = response_type
        self._from_protocol = from_protocol
        self._request_id_counter = id_counter

    async def read(self) -> Sample[TLib]:
        req = memread.MemReadRequest(
            id=self._request_id_counter.get_next(),
            params=memread.MemReadRequestParams(segment=self._name),
        )
        async with Query(req, methods.MEM_READ).execute(self._executor) as q:
            resp = await q.response
            return self._convert_from_protocol(resp.result)

    @contextlib.asynccontextmanager
    async def watch(self) -> typing.AsyncIterator[typing.AsyncIterator[Sample[TLib]]]:
        req = memread.WatchRequest(
            id=self._request_id_counter.get_next(),
            params=memread.MemReadRequestParams(segment=self._name),
        )
        async with Query(req, methods.WATCH).execute(self._executor) as q:
            yield self._watch_iter(q.notifications)

    async def _watch_iter(
        self, iter: typing.AsyncIterator[memread.WatchNotification]
    ) -> typing.AsyncIterator[Sample[TLib]]:
        async for val in iter:
            yield self._convert_from_protocol(val.notification)

    def _convert_from_protocol(self, val: MemReadResponseBody) -> Sample[TLib]:
        if isinstance(val, self._type):
            if isinstance(val, _HasTimestamp):
                return sample_from_protocol(val, self._from_protocol)
            else:
                return Sample.now(self._from_protocol(val))
        else:
            raise MemoryReadUnsuccessfulError(self._name, "unexpected type received")


class NativeDataAccessReadWrite[TProtoFrom: MemReadResponseBody, TProtoTo: MemWriteRequestParams, TLib](
    NativeDataAccessRead[TProtoFrom, TLib]
):
    def __init__(
        self,
        executor: Executor,
        id_counter: _RequestIdCounter,
        name: str,
        *,
        response_type: type[TProtoFrom],
        from_protocol: typing.Callable[[TProtoFrom], TLib],
        to_protocol: typing.Callable[[TLib], TProtoTo],
    ) -> None:
        super().__init__(executor, id_counter, name, response_type=response_type, from_protocol=from_protocol)
        self._to_protocol = to_protocol

    async def write(self, value: TLib) -> None:
        request_params = self._to_protocol(value)
        req = memwrite.MemWriteRequest(
            id=self._request_id_counter.get_next(),
            params=request_params,
        )
        async with Query(req, methods.MEM_WRITE).execute(self._executor) as q:
            resp = await q.response
            if not resp.result.success:
                raise MemoryWriteUnsuccessfulError(self._name, "failure reported")


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
        self._request_id = _RequestIdCounter()
        self.memory = NativeMemoryRegions(executor, self._request_id)

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

    async def move(self, distance_m: float, speed_ms: float) -> None:
        req = request.MoveStraightRequest(
            id=self._request_id.get_next(),
            params=request.MoveStraightRequestParams(distance=distance_m, speed=speed_ms),
        )
        async with Query(req, methods.MOVE_STRAIGHT).execute(self._executor) as q:
            await self._handle_response("MoveStraight", q.response)

    async def rotate(self, angle_rad: float, angular_speed_radps: float) -> None:
        req = request.RotateRequest(
            id=self._request_id.get_next(),
            params=request.RotateRequestParams(angle=angle_rad, speed=angular_speed_radps),
        )
        async with Query(req, methods.ROTATE).execute(self._executor) as q:
            await self._handle_response("Rotate", q.response)

    async def velocity(self, linear_mps: float, angular_radps: float, duration_ms: int) -> None:
        req = request.VelocityRequest(
            id=self._request_id.get_next(),
            params=request.VelocityRequestParams(
                linear_speed=linear_mps, rotation_speed=angular_radps, expiration=duration_ms / 1000
            ),
        )
        async with Query(req, methods.VELOCITY).execute(self._executor) as q:
            await self._handle_response("Velocity", q.response)

    async def play_tone(self, frequency_hz: int, duration_ms: int, volume: int) -> None:
        req = request.PlayToneRequest(
            id=self._request_id.get_next(),
            params=request.PlayToneRequestParams(frequency=frequency_hz, duration=duration_ms / 1000, volume=volume),
        )
        async with Query(req, methods.PLAY_TONE).execute(self._executor) as q:
            await self._handle_response("PlayTone", q.response)

    async def play_audio(self, audio_name: str) -> None:
        req = request.PlaySoundRequest(
            id=self._request_id.get_next(),
            params=request.PlaySoundRequestParams(name=audio_name, loop=False, volume=1.0),
        )
        async with Query(req, methods.PLAY_SOUND).execute(self._executor) as q:
            await self._handle_response("PlaySound", q.response)

    async def set_led(self, mask: LEDMask, red: int, green: int, blue: int) -> None:
        lights = conversions.led_to_protocol(mask)
        color = types.Color(red=red, green=green, blue=blue)
        req = request.SetLEDRequest(
            id=self._request_id.get_next(), params=request.SetLEDRequestParams(lights=lights, color=color)
        )
        async with Query(req, methods.SET_LED).execute(self._executor) as q:
            await self._handle_response("SetLED", q.response)

    async def line_navigation(self, direction: Direction, follow: bool) -> None:
        direction_protocol = conversions.intersection_direction_to_protocol(direction)
        follow_arg = "Follow" if follow else "DoNotFollow"
        req = request.LineNavigationRequest(
            id=self._request_id.get_next(),
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
                    intersection = conversions.intersection_bitmap_from_protocol(msg.result)
                    sample_intersection = Sample.now(intersection)
                    await self.memory.intersection_queue.write(sample_intersection)
                case notification.LineNavigationColorNotificationBody():
                    color_code = conversions.color_code_from_protocol(msg.result.colors)
                    sample_color_code = Sample.now(color_code)
                    await self.memory.color_code_queue.write(sample_color_code)
                case _:
                    typing.assert_never(msg.result)

    async def _handle_response(self, function_name: str, resp: typing.Awaitable[_HasResult]) -> None:
        val = await resp
        if val.result.type != "finished":
            raise AriProtocolCommandError(function_name, val.result.type, description="call failed")
