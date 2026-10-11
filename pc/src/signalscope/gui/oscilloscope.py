from __future__ import annotations

import pyqtgraph as pg


class OscilloscopeView(pg.PlotWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.setBackground("#111827")
        self.showGrid(x=True, y=True, alpha=0.25)
        self.setLabel("bottom", "Time", units="s")
        self.setLabel("left", "Voltage", units="V")
        self.setTitle("Time-domain waveform")
        self.addLegend()
        self.raw_curve = self.plot([], [], pen=pg.mkPen("#38bdf8", width=1.5), name="Input")
        self.filtered_curve = self.plot(
            [], [], pen=pg.mkPen("#f97316", width=2), name="Filtered"
        )

    def update(self, time_s, samples, filtered=None) -> None:
        self.raw_curve.setData(time_s, samples)
        if filtered is not None:
            self.filtered_curve.setData(time_s, filtered)
            self.filtered_curve.show()
        else:
            self.filtered_curve.hide()
