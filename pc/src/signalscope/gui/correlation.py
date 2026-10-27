from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ..dsp import CorrelationResult, DelayEstimate


class CorrelationView(QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.delay_ms = QDoubleSpinBox()
        self.delay_ms.setRange(0.0, 1000.0)
        self.delay_ms.setDecimals(2)
        self.delay_ms.setSingleStep(1.0)
        self.delay_ms.setSuffix(" ms")
        self.delay_ms.setToolTip(
            "Create Signal B by delaying Signal A. Positive delay means B occurs later."
        )
        self.signal_source = QComboBox()
        self.signal_source.addItems(["Synthetic multitone", "Current acquisition"])
        self.signal_source.setToolTip(
            "Use a reproducible synthetic signal to demonstrate delay, or correlate the "
            "currently acquired waveform against its delayed copy."
        )
        self.delay_summary = QLabel("Estimated delay: — | Peak correlation: —")
        self.delay_summary.setWordWrap(True)

        self.signals_plot = pg.PlotWidget()
        self.signals_plot.setBackground("#111827")
        self.signals_plot.showGrid(x=True, y=True, alpha=0.25)
        self.signals_plot.setLabel("bottom", "Time", units="s")
        self.signals_plot.setLabel("left", "Amplitude")
        self.signals_plot.setTitle("Signal A and delayed Signal B")
        self.signals_plot.addLegend()
        self.signal_a_curve = self.signals_plot.plot(
            [], [], pen=pg.mkPen("#38bdf8", width=1.5), name="Signal A"
        )
        self.signal_b_curve = self.signals_plot.plot(
            [], [], pen=pg.mkPen("#f97316", width=1.5), name="Signal B"
        )

        self.correlation_plot = pg.PlotWidget()
        self.correlation_plot.setBackground("#111827")
        self.correlation_plot.showGrid(x=True, y=True, alpha=0.25)
        self.correlation_plot.setLabel("bottom", "Lag", units="samples")
        self.correlation_plot.setLabel("left", "Normalized correlation")
        self.correlation_plot.setTitle("Normalized cross-correlation (not Pearson coefficient)")
        self.correlation_curve = self.correlation_plot.plot(
            [], [], pen=pg.mkPen("#a78bfa", width=1.5)
        )
        self.peak_marker = self.correlation_plot.plot(
            [], [], pen=None, symbol="o", symbolSize=9, symbolBrush="#f97316"
        )
        self.peak_line = pg.InfiniteLine(
            angle=90,
            movable=False,
            pen=pg.mkPen("#f97316", style=Qt.PenStyle.DashLine),
        )
        self.correlation_plot.addItem(self.peak_line)
        self.peak_line.hide()

        controls = QFormLayout()
        controls.addRow("Signal pair", self.signal_source)
        controls.addRow("Synthetic relative delay", self.delay_ms)
        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.delay_summary)
        layout.addWidget(self.signals_plot, 1)
        layout.addWidget(self.correlation_plot, 1)

    def update_signals(
        self,
        time_s: np.ndarray,
        signal_a: np.ndarray,
        signal_b: np.ndarray,
    ) -> None:
        self.signal_a_curve.setData(time_s, signal_a)
        self.signal_b_curve.setData(time_s, signal_b)

    def update_correlation(
        self,
        result: CorrelationResult | None,
        estimate: DelayEstimate | None,
        sampling_rate_hz: float,
    ) -> None:
        if result is None or estimate is None:
            self.correlation_curve.setData([], [])
            self.peak_marker.setData([], [])
            self.peak_line.hide()
            self.delay_summary.setText("Estimated delay: — | Peak correlation: —")
            return

        self.correlation_curve.setData(result.lags, result.values)
        self.peak_line.setPos(estimate.lag_samples)
        self.peak_line.show()
        self.peak_marker.setData(
            [estimate.lag_samples],
            [estimate.correlation_value],
        )
        self.delay_summary.setText(
            f"Estimated delay: {estimate.delay_seconds * 1000:.3f} ms "
            f"({estimate.lag_samples} samples at {sampling_rate_hz:g} Hz) | "
            f"Peak correlation: {estimate.correlation_value:.3f}"
        )
