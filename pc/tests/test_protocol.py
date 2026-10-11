import numpy as np
import pytest

from signalscope.protocol import (
    PacketParser,
    ProtocolError,
    decode_adc_block,
    decode_stream,
    encode_adc_block,
    encode_frame,
    parse_single_frame,
)


def test_encode_decode_round_trip():
    payload = b"\x01\x02\x03\x04"
    frame = encode_frame(0x42, payload)
    packet = parse_single_frame(frame)
    assert packet.kind == 0x42
    assert packet.payload == payload


def test_parser_handles_fragmented_input_and_multiple_packets():
    first = encode_frame(0x11, b"abc")
    second = encode_frame(0x22, b"def")
    parser = PacketParser()
    assert parser.feed(b"noise" + first[:3]) == []
    assert parser.feed(first[3:] + second[:1]) == [
        parse_single_frame(first)
    ]
    assert parser.feed(second[1:]) == [parse_single_frame(second)]


def test_parser_recovers_after_bad_crc():
    damaged = bytearray(encode_frame(0x11, b"bad"))
    damaged[-1] ^= 0xFF
    following = encode_frame(0x22, b"valid")
    parser = PacketParser()
    packets = parser.feed(bytes(damaged) + following)
    assert packets == [parse_single_frame(following)]
    assert parser.crc_errors == 1


def test_bad_crc_single_frame_is_rejected():
    damaged = bytearray(encode_frame(0x11, b"bad"))
    damaged[-1] ^= 1
    with pytest.raises(ProtocolError, match="CRC"):
        parse_single_frame(bytes(damaged))


def test_frame_payload_is_bounded():
    with pytest.raises(ValueError, match="exceeds"):
        encode_frame(0x01, bytes(65))
    assert len(decode_stream(encode_frame(0x01, bytes(64)))) == 1


def test_adc_block_round_trip():
    frame = encode_adc_block([0, 1, 512, 1023], 2000, 17)
    packet = parse_single_frame(frame)
    assert decode_adc_block(packet) == (2000, 17, [0, 1, 512, 1023])


def test_adc_block_rejects_out_of_range_values():
    with pytest.raises(ValueError, match="10-bit"):
        encode_adc_block([1024], 2000, 0)


def test_dsp_measurements_and_adc_conversion():
    from signalscope.dsp import adc_to_voltage, compute_mean, compute_rms, compute_vpp

    x = np.array([0.0, 1.0, 0.0, -1.0])
    assert compute_mean(x) == 0.0
    assert np.isclose(compute_rms(x), np.sqrt(0.5))
    assert compute_vpp(x) == 2.0
    assert np.allclose(adc_to_voltage(np.array([0, 1023]), 5.0), [0, 5])


def test_fft_frequency_and_filter_length():
    from signalscope.dsp import fft_magnitude, fir_lowpass, moving_average

    fs_hz = 2048
    time_s = np.arange(1024) / fs_hz
    signal = np.sin(2 * np.pi * 128 * time_s)
    bins, magnitude = fft_magnitude(signal, fs_hz, "hann")
    assert bins[np.argmax(magnitude[1:]) + 1] == 128
    assert moving_average(signal, 7).shape == signal.shape
    assert fir_lowpass(signal, 200, fs_hz).shape == signal.shape
