from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import QRectF, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..dsp import STFTResult, magnitude_to_db


class SpectrogramView(QWidget):
    settings_changed = Signal()

    _WINDOW_SIZE_OPTIONS = (128, 256, 512, 1024, 2048)
    _OVERLAP_OPTIONS = {
        "25% overlap": 0.75,
        "50% overlap": 0.5,
        "75% overlap": 0.25,
    }

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.window_size = QComboBox()
        for size in self._WINDOW_SIZE_OPTIONS:
            self.window_size.addItem(str(size), size)
        self.window_size.setCurrentIndex(self._WINDOW_SIZE_OPTIONS.index(512))
        self.window_size.setToolTip(
            "A larger window improves frequency resolution but reduces time resolution."
        )

        self.hop_mode = QComboBox()
        self.hop_mode.addItems((*self._OVERLAP_OPTIONS.keys(), "Custom hop size"))
        self.hop_mode.setCurrentText("50% overlap")
        self.hop_mode.setToolTip(
            "Overlap controls how frequently the STFT advances in time: more overlap "
            "means a smaller hop and denser time sampling."
        )
        self.custom_hop_size = QSpinBox()
        self.custom_hop_size.setRange(1, 512)
        self.custom_hop_size.setValue(256)
        self.custom_hop_size.setToolTip("Custom hop in samples; must not exceed the window size.")

        self.window_function = QComboBox()
        self.window_function.addItems(["Rectangular", "Hann", "Hamming"])
        self.window_function.setCurrentText("Hann")
        self.window_function.setToolTip(
            "Windowing reduces spectral leakage caused by observing a finite signal segment."
        )

        self.scale = QComboBox()
        self.scale.addItems(["Magnitude", "Power", "dB"])
        self.scale.setCurrentText("Magnitude")
        self.db_range = QDoubleSpinBox()
        self.db_range.setRange(20.0, 120.0)
        self.db_range.setSingleStep(10.0)
        self.db_range.setValue(80.0)
        self.db_range.setSuffix(" dB")
        self.db_range.setToolTip("Displayed dB dynamic range below the maximum magnitude.")

        self.sampling_rate = 2000.0
        self.resolution_label = QLabel()
        self.resolution_label.setWordWrap(True)
        self.resolution_label.setToolTip(
            "Frequency resolution is Fs/window size. Time step is hop size/Fs."
        )

        self.plot = pg.PlotWidget()
        self.plot.setBackground("#111827")
        self.plot.showGrid(x=True, y=True, alpha=0.25)
        self.plot.setLabel("bottom", "Time", units="s")
        self.plot.setLabel("left", "Frequency", units="Hz")
        self.plot.setTitle("Short-time Fourier transform")
        self.image = pg.ImageItem(axisOrder="row-major")
        color_map = pg.colormap.get("viridis")
        self.image.setLookupTable(color_map.getLookupTable(nPts=256))
        self.plot.addItem(self.image)
        self.message = pg.TextItem(
            "Waiting for signal samples.",
            color="#cbd5e1",
            anchor=(0.5, 0.5),
        )
        self.plot.addItem(self.message)
        self._color_limits = QLabel("Color intensity: magnitude (V peak)")

        controls = QFormLayout()
        controls.addRow("Window size", self.window_size)
        controls.addRow("Overlap / hop", self.hop_mode)
        controls.addRow("Custom hop", self.custom_hop_size)
        controls.addRow("Window function", self.window_function)
        scale_row = QWidget()
        from PySide6.QtWidgets import QHBoxLayout

        scale_layout = QHBoxLayout(scale_row)
        scale_layout.setContentsMargins(0, 0, 0, 0)
        scale_layout.addWidget(self.scale)
        scale_layout.addWidget(self.db_range)
        controls.addRow("Display scale", scale_row)

        layout = QVBoxLayout(self)
        layout.addLayout(controls)
        layout.addWidget(self.resolution_label)
        layout.addWidget(self.plot, 1)
        layout.addWidget(self._color_limits)

        self.window_size.currentIndexChanged.connect(self._window_size_changed)
        self.window_size.currentIndexChanged.connect(self._settings_changed)
        self.hop_mode.currentTextChanged.connect(self._hop_mode_changed)
        self.hop_mode.currentTextChanged.connect(self._settings_changed)
        self.custom_hop_size.valueChanged.connect(self._settings_changed)
        self.window_function.currentTextChanged.connect(self._settings_changed)
        self.scale.currentTextChanged.connect(self._scale_changed)
        self.db_range.valueChanged.connect(self._settings_changed)

        self._window_size_changed()
        self._hop_mode_changed()
        self._scale_changed()
        self._update_resolution_label()

    def _settings_changed(self, *_args) -> None:
        self._update_resolution_label()
        self.settings_changed.emit()

    def _window_size_changed(self, *_args) -> None:
        self.custom_hop_size.setMaximum(self.current_window_size)
        self.custom_hop_size.setValue(min(self.custom_hop_size.value(), self.current_window_size))
        self._update_resolution_label()

    def _hop_mode_changed(self, *_args) -> None:
        self.custom_hop_size.setEnabled(self.hop_mode.currentText() == "Custom hop size")
        self._update_resolution_label()

    def _scale_changed(self, *_args) -> None:
        is_db = self.scale.currentText() == "dB"
        self.db_range.setEnabled(is_db)
        self._update_resolution_label()

    @property
    def current_window_size(self) -> int:
        return int(self.window_size.currentData())

    @property
    def current_hop_size(self) -> int:
        mode = self.hop_mode.currentText()
        if mode == "Custom hop size":
            return self.custom_hop_size.value()
        overlap = self._OVERLAP_OPTIONS[mode]
        return max(1, round(self.current_window_size * (1.0 - overlap)))

    @property
    def current_window_name(self) -> str:
        return self.window_function.currentText().lower()

    def set_sampling_rate(self, sampling_rate_hz: float) -> None:
        if not np.isfinite(sampling_rate_hz) or sampling_rate_hz <= 0:
            raise ValueError("Sampling rate must be finite and positive")
        self.sampling_rate = float(sampling_rate_hz)
        self._update_resolution_label()

    def _update_resolution_label(self) -> None:
        if not hasattr(self, "resolution_label") or self.sampling_rate <= 0:
            return
        window_size = self.current_window_size
        hop_size = self.current_hop_size
        resolution_hz = self.sampling_rate / window_size
        time_step_s = hop_size / self.sampling_rate
        self.resolution_label.setText(
            f"Window: {window_size} samples | Fs: {self.sampling_rate:g} Hz | "
            f"Frequency resolution: {resolution_hz:.3f} Hz | "
            f"Time step: {time_step_s * 1000:.3f} ms ({hop_size} samples)"
        )

    def update_spectrogram(self, result: STFTResult | None) -> None:
        if result is None:
            self.image.clear()
            self.message.setText(
                f"Collect at least {self.current_window_size} samples to calculate the STFT."
            )
            window_duration = self.current_window_size / self.sampling_rate
            self.plot.setRange(
                xRange=(0.0, window_duration),
                yRange=(0.0, self.sampling_rate / 2.0),
                padding=0.02,
            )
            self.message.setPos(window_duration / 2.0, self.sampling_rate / 4.0)
            self.message.show()
            return
        self.message.hide()

        display_scale = self.scale.currentText()
        if display_scale == "Power":
            image_data = result.power
            color_label = "Color intensity: power (V²)"
        elif display_scale == "dB":
            dynamic_range = self.db_range.value()
            image_data = magnitude_to_db(
                result.magnitude,
                dynamic_range_db=dynamic_range,
            )
            color_label = f"Color intensity: dB relative to peak ({-dynamic_range:.0f} to 0 dB)"
        else:
            image_data = result.magnitude
            color_label = "Color intensity: magnitude (V peak)"

        if display_scale == "dB":
            levels = (-self.db_range.value(), 0.0)
        else:
            maximum = float(np.max(image_data)) if image_data.size else 0.0
            levels = (0.0, maximum if maximum > 0.0 else 1.0)
        self.image.setImage(image_data, autoLevels=False, levels=levels)
        self._color_limits.setText(color_label)

        frequency_step = result.frequency_resolution_hz
        time_step = result.time_step_s
        left = result.times_s[0] - time_step / 2.0
        bottom = result.frequencies_hz[0] - frequency_step / 2.0
        width = time_step * result.times_s.size
        height = frequency_step * result.frequencies_hz.size
        self.image.setRect(QRectF(left, bottom, width, height))
        self.plot.setLimits(
            xMin=left,
            xMax=left + width,
            yMin=0.0,
            yMax=result.sampling_rate_hz / 2.0,
        )
        self.plot.setRange(
            xRange=(left, left + width),
            yRange=(0.0, result.sampling_rate_hz / 2.0),
            padding=0.02,
        )
