from ozobot.webrtc.aiortc_wrapper import IceCandidate
from ozobot.webrtc.aiortc_wrapper import SessionDescription
import json
from unittest.mock import Mock, seal

import pydantic
import pytest
from aio_pika.abc import AbstractMessage

from ozobot.webrtc.datatypes import (
    ConnectionClosedBody,
    HandshakeRequestBody,
    HandshakeResponseBody,
    IceCandidateBody,
    LastIceCandidateData,
    Message,
    SdpAnswerBody,
    SdpOfferBody,
    parse_message,
    parse_message_body,
)
# from ozobot.webrtc.libdatachannel import Candidate, Description, DescriptionType


def test_handshake_request_parse() -> None:
    assert parse_message_body(
        """{
        "type": "handshakeRequest",
        "name": "myTestSession123"
    }"""
    ) == HandshakeRequestBody(name="myTestSession123")


def test_handshake_response_parse() -> None:
    assert parse_message_body(
        """{
        "type": "handshakeResponse",
        "status": "accepted"
    }"""
    ) == HandshakeResponseBody(status="accepted")


def test_connection_closed_parse() -> None:
    assert (
        parse_message_body(
            """{
                    "type": "connectionClosed"
                }"""
        )
        == ConnectionClosedBody()
    )

    assert parse_message_body(
        """{
        "type": "connectionClosed",
        "reason": "reject"
    }"""
    ) == ConnectionClosedBody(reason="reject")

    with pytest.raises(pydantic.ValidationError):
        parse_message_body(
            """{
            "type": "connectionClosed",
            "reason": "unknown reason here",
        }"""
        )


def test_sdp_offer_parse() -> None:
    data = {
        "type": "offer",
        "sdp": "v=0\r\no=rtc 548633581 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=msid-semantic:WMS *\r\n",
    }

    expected = SdpOfferBody(
        data=SessionDescription(
            sdp=data["sdp"],
            type="offer",
        )
    )

    sdp_offer_data = json.dumps(data)
    parsed = parse_message_body(f'{{"type": "sdpOffer", "data": {sdp_offer_data}}}')

    assert isinstance(parsed, SdpOfferBody)
    assert parsed.type == expected.type
    assert parsed.data.type == expected.data.type
    assert parsed.data.sdp == expected.data.sdp


def test_sdp_answer_parse() -> None:
    data = {
        "type": "answer",
        "sdp": "v=0\r\no=rtc 548633581 0 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=msid-semantic:WMS *\r\n",
    }

    expected = SdpAnswerBody(
        data=SessionDescription(
            sdp=data["sdp"],
            type="answer",
        )
    )

    sdp_answer_data = json.dumps(data)
    parsed = parse_message_body(f'{{"type": "sdpAnswer", "data": {sdp_answer_data}}}')

    assert isinstance(parsed, SdpAnswerBody)
    assert parsed.type == expected.type
    assert parsed.data.type == expected.data.type
    assert parsed.data.sdp == expected.data.sdp


def test_ice_candidate_parse() -> None:
    candidate = "candidate:0 1 UDP 2122252543 2272dee5-ba93-42ce-82c2-a7aadd7b5ce5.local 35415 typ host"
    mid = "0"
    mline_index = 1
    expected = IceCandidateBody(
        data=IceCandidate(candidate=candidate, sdp_mid=mid, sdp_mline_index=mline_index),
    )
    candidate_data = f'{{"candidate": "{candidate}","sdpMid":"{mid}", "sdpMLineIndex": {mline_index}}}'
    parsed = parse_message_body(f'{{"type": "iceCandidate","data": {candidate_data}}}')

    assert isinstance(parsed, IceCandidateBody)
    assert parsed.type == expected.type
    assert isinstance(parsed.data, IceCandidate)
    assert isinstance(expected.data, IceCandidate)
    assert parsed.data.candidate == expected.data.candidate
    assert parsed.data.sdp_mid == expected.data.sdp_mid
    assert parsed.data.sdp_mline_index == expected.data.sdp_mline_index


def test_ice_candidate_last_notification_parse() -> None:
    candidate_data = r'{"candidate": "","sdpMid":"0","sdpMLineIndex":0}'
    assert parse_message_body(f'{{"type": "iceCandidate","data": {candidate_data}}}') == IceCandidateBody(
        data=LastIceCandidateData()
    )


def test_ice_finished_parse() -> None:
    candidate_data = r'{"candidate": null,"sdpMid":"0","sdpMLineIndex":0}'
    assert parse_message_body(f'{{"type": "iceCandidate","data": {candidate_data}}}') == IceCandidateBody(data=None)


def test_unknown_type_parse() -> None:
    with pytest.raises(pydantic.ValidationError):
        parse_message_body('{"type": "someUnknownMessage"}')


def test_parse_message() -> None:
    message = Mock(spec=AbstractMessage)
    message.body = b'{"type": "connectionClosed"}'
    message.reply_to = "someQueue"
    seal(message)

    assert parse_message(message) == Message(body=ConnectionClosedBody(), reply_to="someQueue")
