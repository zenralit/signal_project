from __future__ import annotations


class SpectrumView:
    def __init__(self) -> None:
        self.fft_bins = []

    def update(self, bins, magnitudes):
        self.fft_bins = list(bins)
        self.magnitudes = list(magnitudes)
