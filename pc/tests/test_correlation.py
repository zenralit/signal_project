import numpy as np
import pytest

from signalscope.dsp import (
    estimate_delay,
    normalized_cross_correlate,
)
from signalscope.signal import generate_delayed_signal


def test_positive_lag_means_signal_b_is_delayed() -> None:
    random = np.random.default_rng(42)
    signal_a = random.normal(size=512)
    delay_samples = 13
    signal_b = generate_delayed_signal(signal_a, delay_samples)

    estimate = estimate_delay(signal_a, signal_b, sampling_rate=10_000.0)

    assert estimate.lag_samples == delay_samples
    assert estimate.delay_seconds == pytest.approx(0.0013)
    assert estimate.correlation_value > 0.95


def test_normalized_correlation_is_amplitude_invariant() -> None:
    signal = np.random.default_rng(9).normal(size=256)

    result = normalized_cross_correlate(signal, signal * 4.0)

    peak_index = int(np.argmax(np.abs(result.values)))
    assert result.lags[peak_index] == 0
    assert result.values[peak_index] == pytest.approx(1.0)
    assert np.max(np.abs(result.values)) <= 1.0


def test_negative_lag_means_signal_b_is_earlier() -> None:
    random = np.random.default_rng(33)
    signal_b = random.normal(size=256)
    signal_a = generate_delayed_signal(signal_b, 8)

    estimate = estimate_delay(signal_a, signal_b, sampling_rate=1000.0)

    assert estimate.lag_samples == -8


def test_delay_estimate_for_silence_is_zero() -> None:
    estimate = estimate_delay(np.zeros(20), np.zeros(20), sampling_rate=1000.0)

    assert estimate.lag_samples == 0
    assert estimate.delay_seconds == 0.0
    assert estimate.correlation_value == 0.0


def test_normalized_correlation_handles_noisy_delayed_signal() -> None:
    random = np.random.default_rng(51)
    signal_a = random.normal(size=1024)
    signal_b = generate_delayed_signal(signal_a, 23)
    signal_b += random.normal(scale=0.15, size=signal_b.size)

    estimate = estimate_delay(signal_a, signal_b, sampling_rate=4000.0)

    assert estimate.lag_samples == 23
    assert estimate.correlation_value > 0.9


def test_unrelated_noise_has_no_strong_correlation_peak() -> None:
    random = np.random.default_rng(72)
    result = normalized_cross_correlate(
        random.normal(size=1024),
        random.normal(size=1024),
    )

    assert np.max(np.abs(result.values)) < 0.2


def test_delay_rejects_invalid_sampling_rate() -> None:
    with pytest.raises(ValueError, match="[Ss]ampling rate"):
        estimate_delay(np.ones(8), np.ones(8), sampling_rate=0.0)
