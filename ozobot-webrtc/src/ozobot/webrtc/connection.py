from __future__ import annotations

import contextlib
import typing
import uuid

from ozobot.webrtc.aiortc_wrapper import (
    ConnectionConfiguration,
    ConnectionState,
    DataChannel,
    IceCandidate,
    PeerConnection,
    ReadyState,
    SessionDescription,
)
from ozobot.webrtc.exceptions import WebRTCChannelUnexpectedDatatypeError, WebRTCConnectionUnexpectedStateError
from ozobot.webrtc.utils import QueueReader

__all__ = ["IceCandidate", "SessionDescription", "ConnectionFactory", "Connection", "Channel"]


def _is_end_state(
    s: typing.Any,
) -> typing.TypeGuard[typing.Literal[ConnectionState.CONNECTED | ConnectionState.FAILED | ConnectionState.CLOSED]]:
    return s in [ConnectionState.CONNECTED, ConnectionState.FAILED, ConnectionState.CLOSED]


class ConnectionFactory:
    @property
    def local_candidates(self) -> QueueReader[IceCandidate]:
        return self._connection.local_candidates

    @property
    def local_description(self) -> QueueReader[SessionDescription]:
        return self._connection.local_description

    def __init__(self, configuration: ConnectionConfiguration | None = None) -> None:
        _configuration = configuration or ConnectionConfiguration(iceServers=[])
        self._connection = PeerConnection(_configuration)

    async def construct(self) -> Connection:
        async with self._connection.connection_state_events:
            await self._connection.connection_state_events.wait_until(_is_end_state)

        if self._connection.connection_state != ConnectionState.CONNECTED:
            raise WebRTCConnectionUnexpectedStateError(str(self._connection.connection_state))

        return Connection(self._connection)

    async def close(self) -> None:
        await self._connection.close()

    async def add_remote_candidate(self, candidate: IceCandidate) -> None:
        await self._connection.add_remote_candidate(candidate)

    async def set_remote_description(self, description: SessionDescription) -> None:
        await self._connection.set_remote_description(description)

    async def create_offer(self) -> None:
        await self._connection.create_and_set_offer()

    async def create_answer(self) -> None:
        await self._connection.create_and_set_answer()

    def create_data_channel(self, label: str) -> Channel:
        return Channel(self._connection.create_data_channel(label))


class Connection:
    @property
    def state_change_events(self) -> QueueReader[ConnectionState]:
        return self._peer.connection_state_events

    def __init__(self, peer: PeerConnection):
        self.uuid = str(uuid.uuid4())
        self._peer = peer

    @contextlib.asynccontextmanager
    async def data_channels(self) -> typing.AsyncIterator[typing.AsyncIterator[Channel]]:
        async with self._peer.data_channels as channels:
            gen = self._data_channels(channels)
            try:
                yield gen
            finally:
                await gen.aclose()

    async def _data_channels(self, channels: QueueReader[DataChannel]) -> typing.AsyncGenerator[Channel]:
        async for channel in channels.items():
            yield Channel(channel)

    async def close(self) -> None:
        await self._peer.close()

    def __repr__(self) -> str:
        return f"Connection(uuid={self.uuid!r})"

    def __str__(self) -> str:
        return self.__repr__()


class Channel:
    _rtc_channel: DataChannel

    @property
    def label(self) -> str:
        return self._rtc_channel.label

    def __init__(self, channel: DataChannel):
        self._rtc_channel = channel

    async def error_events(self) -> typing.AsyncIterator[str]:
        async with self._rtc_channel.errors as listener:
            async for event in listener.items():
                yield event

    async def ready_state(self) -> typing.AsyncIterator[ReadyState]:
        async with self._rtc_channel.ready_state as ready_states:
            async for ready_state in ready_states.items():
                yield ready_state

    async def receive(self) -> typing.AsyncIterator[bytes | str]:
        async with self._rtc_channel.messages as listener:
            async for message in listener.items():
                yield message

    async def receive_bytes(self) -> typing.AsyncIterator[bytes]:
        async for message in self.receive():
            if isinstance(message, bytes):
                yield message
            else:
                raise WebRTCChannelUnexpectedDatatypeError(bytes, type(message))

    async def receive_str(self) -> typing.AsyncIterator[str]:
        async for message in self.receive():
            if isinstance(message, str):
                yield message
            else:
                raise WebRTCChannelUnexpectedDatatypeError(str, type(message))

    async def send(self, message: str) -> None:
        self._rtc_channel.send(message)

    def close(self) -> None:
        self._rtc_channel.close()

    def __repr__(self) -> str:
        return f"Channel(label={self.label!r})"

    def __eq__(self, other: typing.Any) -> bool:
        if not isinstance(other, Channel):
            return False

        return self._rtc_channel == other._rtc_channel

    def __hash__(self) -> int:
        return hash((Channel, self._rtc_channel))
