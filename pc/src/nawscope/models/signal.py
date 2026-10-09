from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SignalFrame:
    samples: list[float]
    sampling_frequency_hz: float
    channels: int = 1

    @property
    def size(self) -> int:
        return len(self.samples)
