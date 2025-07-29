"""RFC 1662 framing library"""

import typing
from enum import Enum

from loguru import logger
from ozobot.jsonrpc.exceptions import UnknownFrameDecoderStateError


class _State(Enum):
    IDLE = 0
    RECEIVING = 1
    ESCAPING = 2
    FRAME_START = 3
    INIT = 4


class FrameDecoder:
    FRAME_FLAG = 0x7E
    FRAME_ESCAPE = 0x7D
    FRAME_ALT = 0x20

    def __init__(self):
        self._buffer = bytearray()
        self._state = _State.INIT

    def feed(self, data: bytes) -> typing.Iterator[bytes]:
        packets: list[bytes] = []
        for index, byte in enumerate(data):
            if self._state == _State.INIT:
                # Init state throws away all suffixes of partially-received packets.
                if byte == self.FRAME_FLAG:
                    # FRAME_START will wait for first non-FRAME_FLAG byte.
                    self._state = _State.FRAME_START
                else:
                    # Log the dropped bytes, but they are not critical on init
                    # - previous communication might have been interrupted and
                    # left the data in port buffer.
                    logger.info(f"Dropping non-framed prefix byte {byte:02x} ({byte}).")
            elif self._state == _State.IDLE:
                if byte == self.FRAME_FLAG:
                    self._state = _State.FRAME_START
                else:
                    self._state = _State.IDLE
                    # Log as warning, this issue in the middle of communication
                    # likely means serious problems on the wire.
                    logger.warning(f"Dropping non-framed byte {byte:02x} ({byte}).")
            elif self._state == _State.RECEIVING or self._state == _State.FRAME_START:
                # While still in FRAME_START, drop all FRAME_FLAG bytes and wait for first non-frame byte.
                if self._state == _State.FRAME_START and byte == self.FRAME_FLAG:
                    continue
                self._state = _State.RECEIVING
                if byte == self.FRAME_FLAG:
                    # Received end of frame, move the buffer as a complete packet and reset
                    packets.append(self._buffer)
                    self._buffer = bytes()
                    self._state = _State.IDLE
                elif byte == self.FRAME_ESCAPE:
                    # Escape encountered, mark that and continue
                    self._state = _State.ESCAPING
                else:
                    self._buffer += bytes([byte])
            elif self._state == _State.ESCAPING:
                self._buffer += bytes([byte ^ self.FRAME_ALT])
                self._state = _State.RECEIVING
            else:
                raise UnknownFrameDecoderStateError()

        yield from packets


def encode_frame(data: bytes) -> bytes:
    """Encodes `data` in RFC 1662 frame."""
    enc = bytearray([FrameDecoder.FRAME_FLAG])
    for byte in data:
        if byte in [FrameDecoder.FRAME_FLAG, FrameDecoder.FRAME_ESCAPE]:
            enc += bytearray([FrameDecoder.FRAME_ESCAPE, byte ^ FrameDecoder.FRAME_ALT])
        else:
            enc += bytearray([byte])
    enc += bytearray([FrameDecoder.FRAME_FLAG])
    return bytes(enc)
