from __future__ import annotations

import numpy as np

from ..signal import (
    generate_chirp,
    generate_delayed_signal,
    generate_multitone,
    generate_noise,
    generate_sine,
    generate_square,
    generate_triangle,
)


def compute_mean(samples: np.ndarray) -> float:
    data = np.asarray(samples, dtype=np.float64)
    return float(np.mean(data)) if data.size else 0.0


def compute_rms(samples: np.ndarray) -> float:
    data = np.asarray(samples, dtype=np.float64)
    return float(np.sqrt(np.mean(np.square(data)))) if data.size else 0.0


def compute_vpp(samples: np.ndarray) -> float:
    data = np.asarray(samples, dtype=np.float64)
    return float(np.ptp(data)) if data.size else 0.0


def adc_to_voltage(samples: np.ndarray, reference_voltage: float = 5.0) -> np.ndarray:
    if reference_voltage <= 0:
        raise ValueError("Reference voltage must be positive")
    data = np.asarray(samples, dtype=np.float64)
    if np.any((data < 0) | (data > 1023)):
        raise ValueError("ADC values must be in range 0..1023")
    return data * (reference_voltage / 1023.0)


def fft_magnitude(
    samples: np.ndarray, sampling_frequency_hz: float, window: str = "hann"
) -> tuple[np.ndarray, np.ndarray]:
    data = np.asarray(samples, dtype=np.float64)
    if sampling_frequency_hz <= 0:
        raise ValueError("Sampling frequency must be positive")
    if data.size == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    if window == "hann":
        weights = np.hanning(data.size) if data.size > 1 else np.ones(1)
    elif window == "rectangular":
        weights = np.ones(data.size, dtype=np.float64)
    else:
        raise ValueError(f"Unsupported window: {window}")
    spectrum = np.fft.rfft((data - np.mean(data)) * weights)
    magnitudes = np.abs(spectrum) / max(float(np.sum(weights)), 1.0)
    if data.size > 1:
        magnitudes[1:-1 if data.size % 2 == 0 else None] *= 2.0
    return np.fft.rfftfreq(data.size, d=1.0 / sampling_frequency_hz), magnitudes


def estimate_frequency_zero_crossing(samples: np.ndarray, sampling_frequency_hz: float) -> float:
    data = np.asarray(samples, dtype=np.float64)
    if sampling_frequency_hz <= 0:
        raise ValueError("Sampling frequency must be positive")
    if data.size < 3:
        return 0.0
    centered = data - np.mean(data)
    rising = np.flatnonzero((centered[:-1] <= 0) & (centered[1:] > 0))
    if rising.size < 2:
        return 0.0
    periods = np.diff(rising)
    return float(sampling_frequency_hz / np.mean(periods))


def dominant_frequency(samples: np.ndarray, sampling_frequency_hz: float) -> float:
    bins, magnitudes = fft_magnitude(samples, sampling_frequency_hz)
    if bins.size < 2:
        return 0.0
    return float(bins[1 + int(np.argmax(magnitudes[1:]))])


def moving_average(samples: np.ndarray, window_size: int = 5) -> np.ndarray:
    data = np.asarray(samples, dtype=np.float64)
    if window_size <= 0:
        raise ValueError("Window size must be positive")
    if data.size == 0 or window_size == 1:
        return data.copy()
    kernel = np.full(window_size, 1.0 / window_size, dtype=np.float64)
    left = (window_size - 1) // 2
    right = window_size - 1 - left
    return np.convolve(np.pad(data, (left, right), mode="edge"), kernel, mode="valid")


def fir_lowpass(
    samples: np.ndarray, cutoff_hz: float, sampling_frequency_hz: float, taps: int = 31
) -> np.ndarray:
    data = np.asarray(samples, dtype=np.float64)
    if sampling_frequency_hz <= 0 or not 0 < cutoff_hz < sampling_frequency_hz / 2:
        raise ValueError("Cutoff must lie strictly between 0 and Nyquist")
    if taps < 3 or taps % 2 == 0:
        raise ValueError("FIR tap count must be an odd integer >= 3")
    if data.size == 0:
        return data.copy()
    indices = np.arange(taps) - (taps - 1) / 2
    coefficients = 2 * cutoff_hz / sampling_frequency_hz * np.sinc(
        2 * cutoff_hz * indices / sampling_frequency_hz
    )
    coefficients *= np.hamming(taps)
    coefficients /= coefficients.sum()
    half = taps // 2
    return np.convolve(np.pad(data, (half, half), mode="edge"), coefficients, mode="valid")


def apply_filter(
    samples: np.ndarray, filter_name: str, sampling_frequency_hz: float, cutoff_hz: float
) -> np.ndarray:
    if filter_name == "Off":
        return np.asarray(samples, dtype=np.float64).copy()
    if filter_name == "Moving average":
        return moving_average(samples, window_size=9)
    if filter_name == "FIR low-pass":
        return fir_lowpass(samples, cutoff_hz, sampling_frequency_hz)
    raise ValueError(f"Unsupported filter: {filter_name}")


from .correlation import (
    CorrelationResult,
    DelayEstimate,
    cross_correlate,
    estimate_delay,
    normalized_cross_correlate,
)
from .spectrogram import (
    STFTResult,
    compute_stft,
    get_window,
    magnitude_to_db,
)

__all__ = [
    "CorrelationResult",
    "DelayEstimate",
    "STFTResult",
    "adc_to_voltage",
    "apply_filter",
    "compute_mean",
    "compute_rms",
    "compute_stft",
    "compute_vpp",
    "cross_correlate",
    "dominant_frequency",
    "estimate_delay",
    "estimate_frequency_zero_crossing",
    "fft_magnitude",
    "fir_lowpass",
    "generate_chirp",
    "generate_delayed_signal",
    "generate_multitone",
    "generate_noise",
    "generate_sine",
    "generate_square",
    "generate_triangle",
    "get_window",
    "magnitude_to_db",
    "moving_average",
    "normalized_cross_correlate",
]
