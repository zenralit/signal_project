from __future__ import annotations


class OscilloscopeView:
    def __init__(self) -> None:
        self.samples = []

    def update(self, samples):
        self.samples = list(samples)
