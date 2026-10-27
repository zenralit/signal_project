import numpy as np
import pytest

from signalscope.dsp import compute_stft, get_window, magnitude_to_db
from signalscope.signal import generate_chirp


def test_stft_frame_count_axes_and_sine_peak() -> None:
    sampling_rate = 1024.0
    window_size = 256
    hop_size = 64
    samples = np.sin(2.0 * np.pi * 32.0 * np.arange(1024) / sampling_rate)

    result = compute_stft(samples, sampling_rate, window_size, hop_size, "hann")

    assert result.magnitude.shape == (window_size // 2 + 1, 13)
    assert result.power.shape == result.magnitude.shape
    assert result.frequencies_hz[8] == pytest.approx(32.0)
    assert result.times_s[0] == pytest.approx((window_size - 1) / (2 * sampling_rate))
    assert result.frequency_resolution_hz == pytest.approx(4.0)
    assert result.time_step_s == pytest.approx(hop_size / sampling_rate)
    assert result.frequencies_hz[np.argmax(result.magnitude[:, 2])] == pytest.approx(32.0)
    assert np.max(result.magnitude[8, :]) == pytest.approx(1.0, abs=0.01)


def test_stft_chirp_peak_frequency_increases_over_time() -> None:
    sampling_rate = 1024.0
    samples = generate_chirp(
        20.0,
        200.0,
        duration_s=2.0,
        sampling_frequency_hz=sampling_rate,
    )
    result = compute_stft(samples, sampling_rate, 128, 32)
    peak_bins = np.argmax(result.magnitude[1:, :], axis=0) + 1
    peak_frequencies = result.frequencies_hz[peak_bins]

    assert peak_frequencies[-1] > peak_frequencies[0] + 100.0
    assert np.mean(np.diff(peak_frequencies) >= 0) > 0.8


@pytest.mark.parametrize("name", ["rectangular", "hann", "hamming"])
def test_supported_windows_have_expected_length(name: str) -> None:
    assert get_window(name, 16).shape == (16,)


def test_window_coefficients_match_expected_shapes() -> None:
    rectangular = get_window("rectangular", 16)
    hann = get_window("hann", 16)
    hamming = get_window("hamming", 16)

    assert np.all(rectangular == 1.0)
    assert hann[0] == pytest.approx(0.0)
    assert hann[-1] == pytest.approx(0.0)
    assert hamming[0] == pytest.approx(0.08)
    assert hamming[-1] == pytest.approx(0.08)


def test_frequency_resolution_and_time_step_follow_parameters() -> None:
    samples = np.zeros(2048)

    coarse = compute_stft(samples, 2048.0, 128, 64)
    fine = compute_stft(samples, 2048.0, 512, 32)

    assert fine.frequency_resolution_hz < coarse.frequency_resolution_hz
    assert fine.time_step_s < coarse.time_step_s


def test_db_conversion_is_finite_and_clamped_for_silence() -> None:
    result = magnitude_to_db(np.zeros((3, 4)), dynamic_range_db=60.0)

    assert np.all(np.isfinite(result))
    assert np.all(result == -60.0)
    assert magnitude_to_db(np.array([1.0, 0.1])) == pytest.approx([0.0, -20.0])


@pytest.mark.parametrize(
    ("samples", "sampling_rate", "window_size", "hop_size"),
    [
        (np.ones(16), 0.0, 8, 4),
        (np.ones(16), 100.0, 2, 1),
        (np.ones(16), 100.0, 8, 0),
        (np.ones(7), 100.0, 8, 4),
        (np.ones((2, 8)), 100.0, 8, 4),
    ],
)
def test_stft_rejects_invalid_input(
    samples: np.ndarray,
    sampling_rate: float,
    window_size: int,
    hop_size: int,
) -> None:
    with pytest.raises(ValueError):
        compute_stft(samples, sampling_rate, window_size, hop_size)
