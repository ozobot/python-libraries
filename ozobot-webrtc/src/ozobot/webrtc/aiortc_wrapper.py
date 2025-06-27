from __future__ import annotations

import asyncio
import enum
import typing
from dataclasses import dataclass

import aiortc
import aiortc.sdp
import pyee
from ozobot.webrtc.utils import QueueReader


class ConnectionState(enum.Enum):
    CONNECTED = "connected"
    CONNECTING = "connecting"
    CLOSED = "closed"
    FAILED = "failed"
    NEW = "new"

    @classmethod
    def from_string(cls, string: str) -> typing.Self:
        return cls(string)


class IceGatheringState(enum.Enum):
    COMPLETE = "complete"
    GATHERING = "gathering"
    NEW = "new"

    @classmethod
    def from_string(cls, string: str) -> typing.Self:
        return cls(string)


class IceConnectionState(enum.Enum):
    CHECKING = "checking"
    COMPLETED = "completed"
    CLOSED = "closed"
    FAILED = "failed"
    NEW = "new"

    @classmethod
    def from_string(cls, string: str) -> typing.Self:
        return cls(string)


class SignalingState(enum.Enum):
    CLOSED = "closed"
    HAVE_LOCAL_OFFER = "have-local-offer"
    HAVE_REMOTE_OFFER = "have-remote-offer"
    STABLE = "stable"

    @classmethod
    def from_string(cls, string: str) -> typing.Self:
        return cls(string)


class ReadyState(enum.Enum):
    CONNECTING = "connecting"
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


@dataclass(frozen=True, kw_only=True)
class IceCandidate:
    candidate: str
    sdp_mid: str | None
    sdp_mline_index: int | None


@dataclass(frozen=True, kw_only=True)
class SessionDescription:
    sdp: str
    type: typing.Literal["offer", "answer"]


def _register_event_callback[U](
    instance: pyee.EventEmitter, event_name: str, parser: typing.Callable[[typing.Any], U] | typing.Callable[[], U]
) -> QueueReader[U]:
    queue = asyncio.Queue[U]()

    @instance.on(event_name)
    def _handler(*args) -> None:
        value = parser(*args)
        queue.put_nowait(value)

    return QueueReader(queue)


class DataChannel:
    @property
    def label(self) -> str:
        return self._instance.label

    @property
    def ready_state(self) -> QueueReader[ReadyState]:
        return self._ready_state

    @property
    def messages(self) -> QueueReader[str | bytes]:
        return self._messages

    @property
    def errors(self) -> QueueReader[str]:
        return self._errors

    def __init__(self, data_channel: aiortc.RTCDataChannel):
        self._instance = data_channel

        self._errors: QueueReader[str] = _register_event_callback(self._instance, "error", lambda m: m)
        self._messages: QueueReader[str | bytes] = _register_event_callback(self._instance, "message", lambda m: m)
        self._ready_state_queue = asyncio.Queue[ReadyState]()
        self._ready_state = QueueReader[ReadyState](self._ready_state_queue)

        if self._instance.readyState == "open":
            self._ready_state_queue.put_nowait(ReadyState.OPEN)

        self._instance.on("close", lambda: self._ready_state_queue.put_nowait(ReadyState.CLOSED))
        self._instance.on("open", lambda: self._ready_state_queue.put_nowait(ReadyState.OPEN))

    def send(self, msg: str | bytes) -> None:
        self._instance.send(msg)

    def close(self) -> None:
        self._instance.close()


@dataclass
class IceServerConfiguration:
    url: str
    username: str | None = None
    credential: str | None = None


@dataclass
class ConnectionConfiguration:
    iceServers: list[IceServerConfiguration]


class PeerConnection:
    @property
    def connection_state(self) -> ConnectionState:
        state = ConnectionState.from_string(self._instance.connectionState)
        return state

    @property
    def ice_gathering_state(self) -> IceGatheringState:
        state = IceGatheringState.from_string(self._instance.iceGatheringState)
        return state

    @property
    def signaling_state(self) -> SignalingState:
        state = SignalingState.from_string(self._instance.signalingState)
        return state

    @property
    def ice_connection_state(self) -> IceConnectionState:
        state = IceConnectionState.from_string(self._instance.iceConnectionState)
        return state

    @property
    def local_description(self) -> QueueReader[SessionDescription]:
        return self._local_description

    @property
    def connection_state_events(self) -> QueueReader[ConnectionState]:
        return self._connection_state_events

    @property
    def ice_gathering_events(self) -> QueueReader[IceGatheringState]:
        return self._ice_gathering_events

    @property
    def signaling_events(self) -> QueueReader[SignalingState]:
        return self._signaling_events

    @property
    def ice_connection_events(self) -> QueueReader[IceConnectionState]:
        return self._ice_connection_events

    @property
    def local_candidates(self) -> QueueReader[IceCandidate]:
        # these are not currently emitted by `aiortc`
        return QueueReader[IceCandidate](asyncio.Queue())

    @property
    def data_channels(self) -> QueueReader[DataChannel]:
        return self._data_channel_events

    def __init__(self, configuration: ConnectionConfiguration) -> None:
        config = aiortc.RTCConfiguration(
            iceServers=[
                aiortc.RTCIceServer(urls=c.url, username=c.username, credential=c.credential)
                for c in configuration.iceServers
            ]
        )
        self._instance = aiortc.RTCPeerConnection(config)
        self._connection_state_events = _register_event_callback(
            self._instance, "connectionstatechange", lambda: self.connection_state
        )
        self._local_description_queue = asyncio.Queue[SessionDescription]()
        self._local_description = QueueReader[SessionDescription](self._local_description_queue)
        self._data_channel_events = _register_event_callback(self._instance, "datachannel", DataChannel)
        self._ice_gathering_events = _register_event_callback(
            self._instance, "icegatheringstatechange", lambda: self.ice_gathering_state
        )
        self._signaling_events = _register_event_callback(
            self._instance, "signalingstatechange", lambda: self.signaling_state
        )
        self._ice_connection_events = _register_event_callback(
            self._instance, "iceconnectionstatechange", lambda: self.ice_connection_state
        )

    async def set_remote_description(self, description: SessionDescription) -> None:
        _description = aiortc.RTCSessionDescription(
            sdp=description.sdp,
            type=description.type,
        )
        await self._instance.setRemoteDescription(_description)

    async def add_remote_candidate(self, candidate: IceCandidate) -> None:
        _candidate = aiortc.sdp.candidate_from_sdp(candidate.candidate)
        _candidate.sdpMid = candidate.sdp_mid
        _candidate.sdpMLineIndex = candidate.sdp_mline_index
        await self._instance.addIceCandidate(_candidate)

    async def create_and_set_offer(self) -> None:
        await self._instance.setLocalDescription(await self._instance.createOffer())
        candidate = SessionDescription(sdp=self._instance.localDescription.sdp, type="offer")
        await self._local_description_queue.put(candidate)

    async def create_and_set_answer(self) -> None:
        await self._instance.setLocalDescription(await self._instance.createAnswer())
        candidate = SessionDescription(sdp=self._instance.localDescription.sdp, type="answer")
        await self._local_description_queue.put(candidate)

    def create_data_channel(self, label: str) -> DataChannel:
        return DataChannel(self._instance.createDataChannel(label))

    async def close(self) -> None:
        await self._instance.close()
