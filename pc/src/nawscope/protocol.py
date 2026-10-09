from __future__ import annotations

from dataclasses import dataclass
from typing import List

SYNC_BYTE = 0xA5

TYPE_ADC_BLOCK = 0x01
TYPE_CONFIGURATION = 0x02
TYPE_MEASUREMENT = 0x03
TYPE_ERROR = 0x04
TYPE_DEVICE_INFO = 0x05
TYPE_COMMAND = 0x06


class ProtocolError(ValueError):
    """Raised when a protocol frame is malformed."""


@dataclass(frozen=True)
class Packet:
    kind: int
    payload: bytes

    @property
    def raw(self) -> bytes:
        frame = bytearray()
        frame.append(SYNC_BYTE)
        frame.append(self.kind)
        frame.extend(len(self.payload).to_bytes(2, byteorder="little", signed=False))
        frame.extend(self.payload)
        frame.extend(crc16_ccitt(frame).to_bytes(2, byteorder="little", signed=False))
        return bytes(frame)


def crc16_ccitt(data: bytes, initial: int = 0xFFFF) -> int:
    crc = initial
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(kind: int, payload: bytes = b"") -> bytes:
    packet = Packet(kind=kind, payload=bytes(payload))
    return packet.raw


def decode_stream(stream: bytes) -> List[Packet]:
    packets: List[Packet] = []
    i = 0
    while i < len(stream):
        if stream[i] != SYNC_BYTE:
            i += 1
            continue
        if i + 6 > len(stream):
            break
        kind = stream[i + 1]
        length = int.from_bytes(stream[i + 2 : i + 4], byteorder="little", signed=False)
        total = 1 + 1 + 2 + length + 2
        if i + total > len(stream):
            break
        payload = bytes(stream[i + 4 : i + 4 + length])
        crc = int.from_bytes(stream[i + 4 + length : i + 4 + length + 2], byteorder="little", signed=False)
        body = stream[i : i + 4 + length]
        expected = crc16_ccitt(body) & 0xFFFF
        if crc != expected:
            raise ProtocolError(f"CRC mismatch for frame type {kind!r}")
        packets.append(Packet(kind=kind, payload=payload))
        i += total
    return packets


def parse_single_frame(frame: bytes) -> Packet:
    if len(frame) < 7:
        raise ProtocolError("Frame is too short")
    if frame[0] != SYNC_BYTE:
        raise ProtocolError("Missing sync byte")
    kind = frame[1]
    length = int.from_bytes(frame[2:4], byteorder="little", signed=False)
    if len(frame) != 4 + length + 2:
        raise ProtocolError("Length does not match frame size")
    payload = frame[4 : 4 + length]
    crc = int.from_bytes(frame[4 + length : 4 + length + 2], byteorder="little", signed=False)
    expected = crc16_ccitt(frame[: 4 + length])
    if crc != expected:
        raise ProtocolError("CRC mismatch")
    return Packet(kind=kind, payload=payload)
