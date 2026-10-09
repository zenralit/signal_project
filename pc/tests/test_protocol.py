import numpy as np

from nawscope.protocol import Packet, decode_stream, encode_frame, parse_single_frame


def test_encode_decode_round_trip():
    payload = b"\x01\x02\x03\x04"
    frame = encode_frame(0x42, payload)
    packet = parse_single_frame(frame)
    assert packet.kind == 0x42
    assert packet.payload == payload


def test_decode_stream_handles_multiple_packets():
    packets = [encode_frame(0x11, b"abc"), encode_frame(0x22, b"def")]
    combined = b"".join(packets)
    decoded = decode_stream(combined)
    assert [p.kind for p in decoded] == [0x11, 0x22]
    assert [p.payload for p in decoded] == [b"abc", b"def"]


def test_dsp_helpers():
    x = np.array([0.0, 1.0, 0.0, -1.0], dtype=np.float64)
    assert abs(np.mean(x)) < 1e-12
    assert np.isclose(np.sqrt(np.mean(np.square(x))), 0.7071067811865476, rtol=1e-6)
    assert np.isclose(np.max(x) - np.min(x), 2.0)
