from __future__ import annotations

import math
import random
from typing import Iterable

import numpy as np


def _time_vector(duration_s: float, fs_hz: float) -> np.ndarray:
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("Duration must be finite and positive")
    if not math.isfinite(fs_hz) or fs_hz <= 0:
        raise ValueError("Sampling frequency must be finite and positive")
    sample_count = max(1, int(round(duration_s * fs_hz)))
    return np.arange(sample_count, dtype=np.float64) / fs_hz


def generate_sine(
    frequency_hz: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    offset: float = 0.0,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
) -> np.ndarray:
    t = _time_vector(duration_s, sampling_frequency_hz)
    return amplitude * np.sin(2.0 * math.pi * frequency_hz * t + phase) + offset


def generate_square(
    frequency_hz: float,
    amplitude: float = 1.0,
    duty_cycle: float = 0.5,
    offset: float = 0.0,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
) -> np.ndarray:
    t = _time_vector(duration_s, sampling_frequency_hz)
    phase = (2.0 * math.pi * frequency_hz * t) % (2.0 * math.pi)
    square = np.where(phase < 2.0 * math.pi * duty_cycle, 1.0, -1.0)
    return amplitude * square + offset


def generate_triangle(
    frequency_hz: float,
    amplitude: float = 1.0,
    offset: float = 0.0,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
) -> np.ndarray:
    t = _time_vector(duration_s, sampling_frequency_hz)
    phase = (frequency_hz * t) % 1.0
    triangle = 2.0 * np.abs(2.0 * phase - 1.0) - 1.0
    return amplitude * triangle + offset


def generate_noise(
    amplitude: float = 1.0,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
    seed: int | None = None,
) -> np.ndarray:
    if seed is not None:
        random.seed(seed)
    sample_count = max(1, int(round(duration_s * sampling_frequency_hz)))
    return amplitude * np.random.default_rng(seed).normal(0.0, 1.0, size=sample_count)


def generate_multitone(
    frequencies_hz: Iterable[float],
    amplitudes: Iterable[float] | None = None,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
    phase_offset: float = 0.0,
) -> np.ndarray:
    freqs = list(frequencies_hz)
    amps = list(amplitudes) if amplitudes is not None else [1.0] * len(freqs)
    if len(freqs) != len(amps):
        raise ValueError("Frequencies and amplitudes length mismatch")
    t = _time_vector(duration_s, sampling_frequency_hz)
    signal = np.zeros_like(t, dtype=np.float64)
    for freq, amp in zip(freqs, amps):
        signal += amp * np.sin(2.0 * math.pi * freq * t + phase_offset)
    return signal


def generate_chirp(
    start_frequency_hz: float,
    end_frequency_hz: float,
    amplitude: float = 1.0,
    phase: float = 0.0,
    offset: float = 0.0,
    duration_s: float = 1.0,
    sampling_frequency_hz: float = 1000.0,
) -> np.ndarray:
    """Generate a linear-frequency sine sweep from start to end frequency."""
    if not math.isfinite(start_frequency_hz) or start_frequency_hz < 0:
        raise ValueError("Start frequency must be finite and nonnegative")
    if not math.isfinite(end_frequency_hz) or end_frequency_hz < 0:
        raise ValueError("End frequency must be finite and nonnegative")
    time_s = _time_vector(duration_s, sampling_frequency_hz)
    slope = (end_frequency_hz - start_frequency_hz) / duration_s
    phase_radians = 2.0 * math.pi * (
        start_frequency_hz * time_s + 0.5 * slope * np.square(time_s)
    ) + phase
    return offset + amplitude * np.sin(phase_radians)


def generate_delayed_signal(signal: np.ndarray, delay_samples: int) -> np.ndarray:
    """Delay a 1-D signal by inserting zeros; positive delay means a later output."""
    data = np.asarray(signal, dtype=np.float64)
    if data.ndim != 1:
        raise ValueError("Signal must be one-dimensional")
    if not np.all(np.isfinite(data)):
        raise ValueError("Signal must contain only finite values")
    if isinstance(delay_samples, bool) or not isinstance(delay_samples, (int, np.integer)):
        raise ValueError("Delay must be a nonnegative integer number of samples")
    if delay_samples < 0:
        raise ValueError("Delay must be a nonnegative integer number of samples")
    delayed = np.zeros_like(data)
    if delay_samples < data.size:
        delayed[delay_samples:] = data[: data.size - delay_samples]
    return delayed
