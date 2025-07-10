from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Literal, TypedDict, TypeIs

import aio_pika
from ozobot.webrtc.connection import IceCandidate, SessionDescription
from ozobot.webrtc.exceptions import UnknownSdpTypeError
from pydantic import BaseModel, Field, TypeAdapter, field_serializer, field_validator


@dataclass(frozen=True)
class Message:
    body: MessageBody
    reply_to: str | None = None


class MessageBody(BaseModel):
    type: str


class HandshakeRequestBody(MessageBody):
    type: Literal["handshakeRequest"] = "handshakeRequest"
    name: str


class HandshakeResponseBody(MessageBody):
    type: Literal["handshakeResponse"] = "handshakeResponse"
    status: Literal["accepted", "rejected"]


class ConnectionClosedBody(MessageBody):
    type: Literal["connectionClosed"] = "connectionClosed"
    reason: Literal["reject", "timeout", "error"] | None = None


class SdpMessage(MessageBody):
    type: Literal["sdpOffer", "sdpAnswer"]
    data: SessionDescription

    @field_validator("data", mode="before")
    @classmethod
    def description_from_string(cls, message: dict[str, str] | SessionDescription) -> SessionDescription:
        if isinstance(message, SessionDescription):
            return message

        if SdpMessage._is_sdp_type(message["type"]):
            return SessionDescription(
                sdp=message["sdp"],
                type=message["type"],
            )
        else:
            raise UnknownSdpTypeError(message["type"])

    @staticmethod
    def _is_sdp_type(val: str) -> TypeIs[Literal["offer", "answer"]]:
        return val in ["offer", "answer"]

    @field_serializer("data", when_used="always")
    def serialize_description(self, description: SessionDescription) -> dict[str, str]:
        return {
            "type": description.type,
            "sdp": description.sdp,
        }


class SdpOfferBody(SdpMessage):
    type: Literal["sdpOffer"] = "sdpOffer"
    data: SessionDescription


class SdpAnswerBody(SdpMessage):
    type: Literal["sdpAnswer"] = "sdpAnswer"
    data: SessionDescription


class IceCandidateBody(MessageBody):
    type: Literal["iceCandidate"] = "iceCandidate"
    data: IceCandidate | LastIceCandidateData | None

    @field_validator("data", mode="before")
    @classmethod
    def candidate_from_sdp(
        cls, message: _CandidateMessageData | IceCandidate
    ) -> IceCandidate | LastIceCandidateData | None:
        if isinstance(message, IceCandidate | LastIceCandidateData) or message is None:
            return message

        for field in ["candidate", "sdpMid"]:
            assert field in message, f"`{field}` field missing"

        if message["candidate"] is None:
            return None

        if message["candidate"] == "":
            return LastIceCandidateData()

        return IceCandidate(
            candidate=message["candidate"],
            sdp_mid=message["sdpMid"],
            sdp_mline_index=message["sdpMLineIndex"],
        )

    @field_serializer("data", when_used="always")
    def serialize_candidate(
        self, candidate: IceCandidate | LastIceCandidateData | None
    ) -> _CandidateMessageData | _EmptyCandidateMessageData | None:
        if isinstance(candidate, LastIceCandidateData):
            return {"candidate": None}
        elif candidate is None:
            return None

        return {
            "candidate": candidate.candidate,
            "sdpMid": candidate.sdp_mid,
            "sdpMLineIndex": candidate.sdp_mline_index,
        }


class LastIceCandidateData(BaseModel):
    pass


class _CandidateMessageData(TypedDict):
    candidate: str
    sdpMid: str | None
    sdpMLineIndex: int | None


class _EmptyCandidateMessageData(TypedDict):
    candidate: None


IceCandidateBody.model_rebuild()

_TMessageBody = Annotated[
    HandshakeRequestBody
    | HandshakeResponseBody
    | ConnectionClosedBody
    | SdpOfferBody
    | SdpAnswerBody
    | IceCandidateBody,
    Field(discriminator="type"),
]
_MessageBodyAdapter: TypeAdapter[_TMessageBody] = TypeAdapter(_TMessageBody)


def parse_message_body(data: str) -> MessageBody:
    return _MessageBodyAdapter.validate_json(data)


def parse_message(raw_message_body: bytes, reply_to: str | None) -> Message:
    return Message(
        body=parse_message_body(raw_message_body.decode("utf8")),
        reply_to=reply_to,
    )
