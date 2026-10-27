from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

WindowName = Literal["rectangular", "hann", "hamming"]


@dataclass(frozen=True)
class STFTResult:
    frequencies_hz: np.ndarray
    times_s: np.ndarray
    magnitude: np.ndarray
    power: np.ndarray
    window_size: int
    hop_size: int
    sampling_rate_hz: float
    window_name: str

    @property
    def frequency_resolution_hz(self) -> float:
        return self.sampling_rate_hz / self.window_size

    @property
    def time_step_s(self) -> float:
        return self.hop_size / self.sampling_rate_hz


def get_window(name: str, size: int) -> np.ndarray:
    """Return a named window of `size` coefficients."""
    if isinstance(size, bool) or not isinstance(size, (int, np.integer)) or size < 3:
        raise ValueError("Window size must be an integer of at least 3 samples")
    normalized_name = name.strip().lower()
    if normalized_name == "rectangular":
        return np.ones(size, dtype=np.float64)
    if normalized_name == "hann":
        return np.hanning(size)
    if normalized_name == "hamming":
        return np.hamming(size)
    raise ValueError(f"Unsupported window: {name!r}")


def compute_stft(
    samples: np.ndarray,
    sampling_rate: float,
    window_size: int,
    hop_size: int,
    window: WindowName | str = "hann",
) -> STFTResult:
    """Compute one-sided, amplitude-normalized STFT magnitude and power.

    Matrix axes are (frequency_bin, time_frame). Frame times denote frame centers;
    only complete frames are used, with no implicit padding at either signal edge.
    """
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("Sampling rate must be a finite positive number")
    if isinstance(window_size, bool) or not isinstance(window_size, (int, np.integer)):
        raise ValueError("Window size must be an integer")
    if window_size < 3:
        raise ValueError("Window size must be at least 3 samples")
    if isinstance(hop_size, bool) or not isinstance(hop_size, (int, np.integer)):
        raise ValueError("Hop size must be an integer")
    if not 1 <= hop_size <= window_size:
        raise ValueError("Hop size must be between 1 and window size")

    data = np.asarray(samples, dtype=np.float64)
    if data.ndim != 1:
        raise ValueError("Samples must be a one-dimensional array")
    if not np.all(np.isfinite(data)):
        raise ValueError("Samples must contain only finite values")
    if data.size < window_size:
        raise ValueError("Signal must contain at least one complete window")

    coefficients = get_window(str(window), int(window_size))
    frame_count = 1 + (data.size - window_size) // hop_size
    frames = sliding_window_view(data, window_size)[::hop_size][:frame_count]
    spectrum = np.fft.rfft(frames * coefficients[None, :], axis=1)
    magnitude = np.abs(spectrum) / np.sum(coefficients)
    if window_size % 2 == 0:
        magnitude[:, 1:-1] *= 2.0
    else:
        magnitude[:, 1:] *= 2.0

    start_indices = np.arange(frame_count, dtype=np.float64) * hop_size
    times_s = (start_indices + (window_size - 1) / 2.0) / sampling_rate
    frequencies_hz = np.fft.rfftfreq(window_size, d=1.0 / sampling_rate)
    magnitude_by_frequency = magnitude.T.copy()

    return STFTResult(
        frequencies_hz=frequencies_hz,
        times_s=times_s,
        magnitude=magnitude_by_frequency,
        power=np.square(magnitude_by_frequency),
        window_size=int(window_size),
        hop_size=int(hop_size),
        sampling_rate_hz=float(sampling_rate),
        window_name=str(window).lower(),
    )


def magnitude_to_db(
    magnitude: np.ndarray,
    *,
    dynamic_range_db: float = 80.0,
    reference: float | None = None,
) -> np.ndarray:
    """Convert nonnegative amplitude values to dB relative to a positive reference.

    Values below the selected dynamic range are clamped, avoiding log(0) and
    keeping the image levels useful for both silent and non-silent signals.
    """
    values = np.asarray(magnitude, dtype=np.float64)
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Magnitude values must be finite and nonnegative")
    if not np.isfinite(dynamic_range_db) or dynamic_range_db <= 0:
        raise ValueError("Dynamic range must be a finite positive number")
    if reference is None:
        reference = float(np.max(values)) if values.size else 0.0
        if reference == 0.0:
            reference = 1.0
    if not np.isfinite(reference) or reference <= 0:
        raise ValueError("Reference magnitude must be a finite positive number")

    epsilon = np.finfo(np.float64).tiny
    decibels = 20.0 * np.log10(np.maximum(values, epsilon) / reference)
    return np.maximum(decibels, -dynamic_range_db)
