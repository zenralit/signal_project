from __future__ import annotations

import math
import random
from typing import Iterable

import numpy as np


def _time_vector(duration_s: float, fs_hz: float) -> np.ndarray:
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
