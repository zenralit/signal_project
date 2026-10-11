from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QSpinBox,
    QWidget,
)


class ControlPanel(QGroupBox):
    def __init__(self, parent=None) -> None:
        super().__init__("Acquisition and DSP controls", parent)
        self.source = QComboBox()
        self.source.addItems(["Demo signal", "Arduino"])
        self.port = QComboBox()
        self.port.setMinimumWidth(150)
        self.refresh_ports = QPushButton("Refresh")
        self.connect_button = QPushButton("Connect")

        self.sampling_rate = QSpinBox()
        self.sampling_rate.setRange(100, 4000)
        self.sampling_rate.setSingleStep(100)
        self.sampling_rate.setValue(2000)
        self.adc_channel = QSpinBox()
        self.adc_channel.setRange(0, 5)
        self.reference_voltage = QDoubleSpinBox()
        self.reference_voltage.setRange(1.0, 5.5)
        self.reference_voltage.setSingleStep(0.1)
        self.reference_voltage.setValue(5.0)
        self.reference_voltage.setSuffix(" V")

        self.waveform = QComboBox()
        self.waveform.addItems(["Sine", "Square", "Triangle", "Noise"])
        self.demo_frequency = QDoubleSpinBox()
        self.demo_frequency.setRange(1, 10000)
        self.demo_frequency.setValue(100)
        self.demo_frequency.setSuffix(" Hz")

        self.filter = QComboBox()
        self.filter.addItems(["Off", "Moving average", "FIR low-pass"])
        self.cutoff = QDoubleSpinBox()
        self.cutoff.setRange(1, 2500)
        self.cutoff.setValue(250)
        self.cutoff.setSuffix(" Hz")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

        form = QFormLayout()
        source_row = QWidget()
        source_layout = QHBoxLayout(source_row)
        source_layout.setContentsMargins(0, 0, 0, 0)
        source_layout.addWidget(self.source)
        source_layout.addWidget(self.port, 1)
        source_layout.addWidget(self.refresh_ports)
        source_layout.addWidget(self.connect_button)
        form.addRow("Input", source_row)

        acquisition_row = QWidget()
        acquisition_layout = QHBoxLayout(acquisition_row)
        acquisition_layout.setContentsMargins(0, 0, 0, 0)
        acquisition_layout.addWidget(self.sampling_rate)
        acquisition_layout.addWidget(self.adc_channel)
        acquisition_layout.addWidget(self.reference_voltage)
        form.addRow("Fs / ADC channel / Vref", acquisition_row)

        dsp_row = QWidget()
        dsp_layout = QHBoxLayout(dsp_row)
        dsp_layout.setContentsMargins(0, 0, 0, 0)
        dsp_layout.addWidget(self.waveform)
        dsp_layout.addWidget(self.demo_frequency)
        dsp_layout.addWidget(self.filter)
        dsp_layout.addWidget(self.cutoff)
        form.addRow("Demo signal / filter", dsp_row)

        buttons = QWidget()
        button_layout = QHBoxLayout(buttons)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        form.addRow("Acquisition", buttons)
        self.setLayout(form)
