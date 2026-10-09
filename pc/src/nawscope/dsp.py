from __future__ import annotations

import math

import numpy as np

from .signal import generate_multitone, generate_noise, generate_sine, generate_square, generate_triangle


def compute_mean(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.mean(samples))


def compute_rms(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(samples))))


def compute_vpp(samples: np.ndarray) -> float:
    if samples.size == 0:
        return 0.0
    return float(np.max(samples) - np.min(samples))


def fft_magnitude(samples: np.ndarray, sampling_frequency_hz: float, window: str = "hann") -> tuple[np.ndarray, np.ndarray]:
    samples = np.asarray(samples, dtype=np.float64)
    if samples.size == 0:
        return np.array([], dtype=np.float64), np.array([], dtype=np.float64)
    if window == "hann":
        win = np.hanning(samples.size)
    else:
        win = np.ones(samples.size, dtype=np.float64)
    windowed = samples * win
    spectrum = np.fft.rfft(windowed)
    magnitudes = np.abs(spectrum)
    bins = np.fft.rfftfreq(samples.size, d=1.0 / sampling_frequency_hz)
    return bins, magnitudes


def estimate_frequency_zero_crossing(samples: np.ndarray, sampling_frequency_hz: float) -> float:
    if samples.size < 2:
        return 0.0
    zero_crossings = np.where(np.diff(np.sign(samples)) != 0)[0]
    if zero_crossings.size < 2:
        return 0.0
    average_period = np.mean(np.diff(zero_crossings)) / sampling_frequency_hz
    if average_period <= 0:
        return 0.0
    return 1.0 / average_period


def moving_average(samples: np.ndarray, window_size: int = 5) -> np.ndarray:
    data = np.asarray(samples, dtype=np.float64)
    if data.size == 0:
        return data.copy()
    if window_size <= 1:
        return data.copy()
    kernel = np.ones(window_size, dtype=np.float64) / float(window_size)
    pad = np.pad(data, (window_size // 2, window_size - 1 - window_size // 2), mode="edge")
    return np.convolve(pad, kernel, mode="valid")


def fir_lowpass(samples: np.ndarray, cutoff_hz: float, sampling_frequency_hz: float, taps: int = 9) -> np.ndarray:
    if taps <= 0:
        return np.asarray(samples, dtype=np.float64).copy()
    if cutoff_hz <= 0 or cutoff_hz >= sampling_frequency_hz / 2:
        return np.asarray(samples, dtype=np.float64).copy()
    n = np.arange(taps)
    center = (taps - 1) / 2.0
    coeffs = np.sinc(2.0 * cutoff_hz * (n - center) / sampling_frequency_hz)
    coeffs *= np.hamming(taps)
    coeffs /= np.sum(coeffs)
    data = np.asarray(samples, dtype=np.float64)
    padded = np.pad(data, (taps // 2, taps - 1 - taps // 2), mode="edge")
    return np.convolve(padded, coeffs, mode="valid")


def dominant_frequency(samples: np.ndarray, sampling_frequency_hz: float) -> float:
    bins, magnitudes = fft_magnitude(samples, sampling_frequency_hz)
    if bins.size == 0:
        return 0.0
    idx = int(np.argmax(magnitudes[1:])) + 1 if magnitudes.size > 1 else 0
    return float(bins[idx])
