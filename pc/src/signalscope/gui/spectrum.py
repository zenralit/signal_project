from __future__ import annotations

import pyqtgraph as pg


class SpectrumView(pg.PlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setBackground("#111827")
        self.showGrid(x=True, y=True, alpha=0.25)
        self.setLabel("bottom", "Frequency", units="Hz")
        self.setLabel("left", "Peak magnitude", units="V")
        self.setTitle("Single-sided amplitude spectrum")
        self.addLegend()
        self.raw_curve = self.plot([], [], pen=pg.mkPen("#38bdf8", width=1.5), name="Input")
        self.filtered_curve = self.plot(
            [], [], pen=pg.mkPen("#f97316", width=2), name="Filtered"
        )
        self.nyquist_line = pg.InfiniteLine(
            angle=90, movable=False, pen=pg.mkPen("#ef4444", style=pg.QtCore.Qt.PenStyle.DashLine)
        )
        self.addItem(self.nyquist_line)

    def update(self, bins_hz, magnitudes, nyquist_hz, filtered=None) -> None:
        self.raw_curve.setData(bins_hz, magnitudes)
        if filtered is not None:
            self.filtered_curve.setData(bins_hz, filtered)
            self.filtered_curve.show()
        else:
            self.filtered_curve.hide()
        self.nyquist_line.setPos(nyquist_hz)
