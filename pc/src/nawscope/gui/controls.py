from __future__ import annotations


class ControlPanel:
    def __init__(self) -> None:
        self.filter_enabled = False
        self.filter_type = "low-pass"
        self.cutoff_hz = 100.0
