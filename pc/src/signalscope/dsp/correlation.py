from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CorrelationResult:
    lags: np.ndarray
    values: np.ndarray
    normalized: bool


@dataclass(frozen=True)
class DelayEstimate:
    lag_samples: int
    delay_seconds: float
    correlation_value: float


def _prepare_signals(
    signal_a: np.ndarray, signal_b: np.ndarray, *, demean: bool
) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(signal_a, dtype=np.float64)
    y = np.asarray(signal_b, dtype=np.float64)
    if x.ndim != 1 or y.ndim != 1:
        raise ValueError("Both signals must be one-dimensional arrays")
    if x.size == 0 or y.size == 0:
        raise ValueError("Both signals must contain at least one sample")
    if not np.all(np.isfinite(x)) or not np.all(np.isfinite(y)):
        raise ValueError("Signals must contain only finite values")
    if demean:
        x = x - np.mean(x)
        y = y - np.mean(y)
    return x, y


def _linear_cross_correlation(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    output_size = x.size + y.size - 1
    fft_size = 1 << (output_size - 1).bit_length()
    convolution = np.fft.irfft(
        np.fft.rfft(y, fft_size) * np.fft.rfft(x[::-1], fft_size),
        fft_size,
    )
    return convolution[:output_size]


def cross_correlate(
    signal_a: np.ndarray, signal_b: np.ndarray, *, demean: bool = False
) -> CorrelationResult:
    """Return linear cross-correlation and sample lags.

    Convention: a positive lag means signal B is delayed relative to signal A.
    The returned values are raw correlation sums, not Pearson coefficients.
    """
    x, y = _prepare_signals(signal_a, signal_b, demean=demean)
    values = _linear_cross_correlation(x, y)
    lags = np.arange(-x.size + 1, y.size, dtype=np.int64)
    return CorrelationResult(lags=lags, values=values, normalized=False)


def normalized_cross_correlate(
    signal_a: np.ndarray, signal_b: np.ndarray, *, demean: bool = True
) -> CorrelationResult:
    """Return energy-normalized cross-correlation, bounded to [-1, 1]."""
    x, y = _prepare_signals(signal_a, signal_b, demean=demean)
    denominator = float(np.linalg.norm(x) * np.linalg.norm(y))
    lags = np.arange(-x.size + 1, y.size, dtype=np.int64)
    if denominator == 0.0:
        values = np.zeros(lags.size, dtype=np.float64)
    else:
        values = _linear_cross_correlation(x, y) / denominator
        values = np.clip(values, -1.0, 1.0)
    return CorrelationResult(lags=lags, values=values, normalized=True)


def estimate_delay(
    signal_a: np.ndarray, signal_b: np.ndarray, sampling_rate: float
) -> DelayEstimate:
    """Estimate relative delay; positive values mean B follows A."""
    if not np.isfinite(sampling_rate) or sampling_rate <= 0:
        raise ValueError("Sampling rate must be a finite positive number")
    result = normalized_cross_correlate(signal_a, signal_b)
    if not np.any(result.values):
        return DelayEstimate(lag_samples=0, delay_seconds=0.0, correlation_value=0.0)
    peak_index = int(np.argmax(np.abs(result.values)))
    lag_samples = int(result.lags[peak_index])
    return DelayEstimate(
        lag_samples=lag_samples,
        delay_seconds=lag_samples / sampling_rate,
        correlation_value=float(result.values[peak_index]),
    )
