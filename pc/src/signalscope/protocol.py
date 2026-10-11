from __future__ import annotations

from dataclasses import dataclass

SYNC_BYTE = 0xA5
MAX_PAYLOAD_SIZE = 64

TYPE_ADC_BLOCK = 0x01
TYPE_CONFIGURATION = 0x02
TYPE_MEASUREMENT = 0x03
TYPE_ERROR = 0x04
TYPE_DEVICE_INFO = 0x05
TYPE_COMMAND = 0x06

COMMAND_START = 0x10
COMMAND_STOP = 0x11
COMMAND_SET_SAMPLING_RATE = 0x12
COMMAND_SET_ADC_CHANNEL = 0x13
COMMAND_DEVICE_INFO = 0x14


class ProtocolError(ValueError):
    """Raised when a protocol frame is malformed."""


@dataclass(frozen=True)
class Packet:
    kind: int
    payload: bytes


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
    if not 0 <= kind <= 0xFF:
        raise ValueError("Packet type must fit in one byte")
    if len(payload) > MAX_PAYLOAD_SIZE:
        raise ValueError(f"Payload exceeds {MAX_PAYLOAD_SIZE} bytes")
    body = bytes((SYNC_BYTE, kind)) + len(payload).to_bytes(2, "little") + payload
    return body + crc16_ccitt(body).to_bytes(2, "little")


def parse_single_frame(frame: bytes) -> Packet:
    if len(frame) < 6:
        raise ProtocolError("Frame is too short")
    if frame[0] != SYNC_BYTE:
        raise ProtocolError("Missing sync byte")
    length = int.from_bytes(frame[2:4], "little")
    if length > MAX_PAYLOAD_SIZE:
        raise ProtocolError("Payload length exceeds protocol limit")
    if len(frame) != 6 + length:
        raise ProtocolError("Length does not match frame size")
    expected_crc = crc16_ccitt(frame[:-2])
    if int.from_bytes(frame[-2:], "little") != expected_crc:
        raise ProtocolError("CRC mismatch")
    return Packet(kind=frame[1], payload=bytes(frame[4:-2]))


class PacketParser:
    """Incremental parser; retains incomplete data and resynchronizes after corruption."""

    def __init__(self) -> None:
        self._buffer = bytearray()
        self.crc_errors = 0
        self.discarded_bytes = 0

    def reset(self) -> None:
        self._buffer.clear()

    def feed(self, data: bytes) -> list[Packet]:
        self._buffer.extend(data)
        packets: list[Packet] = []

        while True:
            try:
                sync_index = self._buffer.index(SYNC_BYTE)
            except ValueError:
                self.discarded_bytes += len(self._buffer)
                self._buffer.clear()
                break
            if sync_index:
                self.discarded_bytes += sync_index
                del self._buffer[:sync_index]
            if len(self._buffer) < 4:
                break

            payload_length = int.from_bytes(self._buffer[2:4], "little")
            if payload_length > MAX_PAYLOAD_SIZE:
                self.discarded_bytes += 1
                del self._buffer[0]
                continue

            frame_length = 6 + payload_length
            if len(self._buffer) < frame_length:
                break
            frame = bytes(self._buffer[:frame_length])
            try:
                packet = parse_single_frame(frame)
            except ProtocolError:
                self.crc_errors += 1
                self.discarded_bytes += 1
                del self._buffer[0]
                continue
            packets.append(packet)
            del self._buffer[:frame_length]
        return packets


def decode_stream(stream: bytes) -> list[Packet]:
    parser = PacketParser()
    packets = parser.feed(stream)
    if parser._buffer:
        raise ProtocolError("Incomplete frame at end of stream")
    return packets


def encode_adc_block(samples: list[int], sampling_frequency_hz: int, sequence: int) -> bytes:
    if not 1 <= sampling_frequency_hz <= 0xFFFF:
        raise ValueError("Sampling frequency must be in range 1..65535 Hz")
    if not 0 <= sequence <= 0xFFFF:
        raise ValueError("Sequence number must fit in 16 bits")
    if not 1 <= len(samples) <= 30:
        raise ValueError("ADC packet must carry between 1 and 30 samples")
    payload = bytearray()
    payload.extend(sampling_frequency_hz.to_bytes(2, "little"))
    payload.extend(sequence.to_bytes(2, "little"))
    for sample in samples:
        if not 0 <= sample <= 1023:
            raise ValueError("ADC samples must be 10-bit values")
        payload.extend(sample.to_bytes(2, "little"))
    return encode_frame(TYPE_ADC_BLOCK, bytes(payload))


def decode_adc_block(packet: Packet) -> tuple[int, int, list[int]]:
    if packet.kind != TYPE_ADC_BLOCK or len(packet.payload) < 6 or len(packet.payload) % 2:
        raise ProtocolError("Malformed ADC block")
    sampling_frequency_hz = int.from_bytes(packet.payload[:2], "little")
    sequence = int.from_bytes(packet.payload[2:4], "little")
    samples = [
        int.from_bytes(packet.payload[index : index + 2], "little")
        for index in range(4, len(packet.payload), 2)
    ]
    if sampling_frequency_hz == 0 or any(sample > 1023 for sample in samples):
        raise ProtocolError("Invalid ADC block values")
    return sampling_frequency_hz, sequence, samples
