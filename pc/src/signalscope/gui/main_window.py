from __future__ import annotations

import numpy as np
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..dsp import (
    adc_to_voltage,
    apply_filter,
    compute_mean,
    compute_rms,
    compute_vpp,
    dominant_frequency,
    fft_magnitude,
)
from ..protocol import (
    COMMAND_DEVICE_INFO,
    COMMAND_SET_ADC_CHANNEL,
    COMMAND_SET_SAMPLING_RATE,
    COMMAND_START,
    COMMAND_STOP,
    TYPE_ADC_BLOCK,
    TYPE_DEVICE_INFO,
    TYPE_ERROR,
    Packet,
    decode_adc_block,
)
from ..serial.connection import available_ports, command_frame
from ..serial.worker import SerialWorker
from .controls import ControlPanel
from .oscilloscope import OscilloscopeView
from .spectrum import SpectrumView


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("игра проиграна давно")
        self.resize(1250, 850)

        self.control = ControlPanel()
        self.scope = OscilloscopeView()
        self.spectrum = SpectrumView()
        self.status = QLabel("Ready — select Demo signal or connect Arduino on A0.")
        self.status.setWordWrap(True)
        self.status.setMinimumHeight(25)
        self.metrics = {
            "samples": QLabel("Samples: 0"),
            "mean": QLabel("Mean: —"),
            "rms": QLabel("RMS: —"),
            "vpp": QLabel("Vpp: —"),
            "dominant": QLabel("Dominant f: —"),
            "nyquist": QLabel("Nyquist: —"),
        }
        self.warning = QLabel("")
        self.warning.setWordWrap(True)
        self.warning.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tabs = QTabWidget()
        tabs.addTab(self.scope, "Oscilloscope")
        tabs.addTab(self.spectrum, "Spectrum analyzer")
        metrics_widget = QWidget()
        metrics_layout = QVBoxLayout(metrics_widget)
        metrics_layout.setContentsMargins(8, 2, 8, 2)
        metrics_layout.addWidget(self.status)
        metrics_layout.addWidget(self.warning)
        metric_row = QWidget()
        row = QHBoxLayout(metric_row)
        row.setContentsMargins(0, 0, 0, 0)
        for label in self.metrics.values():
            row.addWidget(label)
        metrics_layout.addWidget(metric_row)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.addWidget(self.control)
        layout.addWidget(tabs, 1)
        layout.addWidget(metrics_widget)
        self.setCentralWidget(container)

        self._samples = np.empty(0, dtype=np.float64)
        self._sample_counter = 0
        self._last_sampling_rate = self.control.sampling_rate.value()
        self._random = np.random.default_rng()
        self._worker: SerialWorker | None = None
        self._running = False
        self._last_sequence: int | None = None
        self._has_error = False

        self._demo_timer = QTimer(self)
        self._demo_timer.setInterval(50)
        self._demo_timer.timeout.connect(self._generate_demo_samples)
        self._draw_timer = QTimer(self)
        self._draw_timer.setInterval(100)
        self._draw_timer.timeout.connect(self._refresh_plots)
        self._draw_timer.start()

        self.control.refresh_ports.clicked.connect(self._refresh_ports)
        self.control.connect_button.clicked.connect(self._toggle_connection)
        self.control.start_button.clicked.connect(self._start_acquisition)
        self.control.stop_button.clicked.connect(self._stop_acquisition)
        self.control.source.currentTextChanged.connect(self._source_changed)
        self.control.sampling_rate.valueChanged.connect(self._settings_changed)
        self.control.adc_channel.valueChanged.connect(self._settings_changed)
        self.control.reference_voltage.valueChanged.connect(self._settings_changed)
        self.control.filter.currentTextChanged.connect(self._refresh_plots)
        self.control.cutoff.valueChanged.connect(self._refresh_plots)
        self.control.demo_frequency.valueChanged.connect(self._refresh_plots)
        self.control.waveform.currentTextChanged.connect(self._refresh_plots)
        self._refresh_ports()
        self._source_changed(self.control.source.currentText())

    def _set_status(self, message: str, error: bool = False) -> None:
        self.status.setText(message)
        self.status.setStyleSheet("color: #f87171;" if error else "color: #cbd5e1;")
        self._has_error = error

    def _refresh_ports(self) -> None:
        selected = self.control.port.currentData()
        try:
            ports = available_ports()
        except RuntimeError as exc:
            self._set_status(str(exc), error=True)
            return
        self.control.port.clear()
        for device, description in ports:
            self.control.port.addItem(f"{device} — {description}", device)
        if selected:
            index = self.control.port.findData(selected)
            if index >= 0:
                self.control.port.setCurrentIndex(index)
        if not ports and self.control.source.currentText() == "Arduino":
            self._set_status("No COM ports found. Connect the Uno, then press Refresh.")

    def _source_changed(self, source: str) -> None:
        if self._running:
            self._stop_acquisition()
        is_arduino = source == "Arduino"
        self.control.port.setEnabled(is_arduino)
        self.control.refresh_ports.setEnabled(is_arduino)
        self.control.connect_button.setEnabled(is_arduino)
        self.control.adc_channel.setEnabled(is_arduino)
        self.control.reference_voltage.setEnabled(is_arduino)
        self.control.waveform.setEnabled(not is_arduino)
        self.control.demo_frequency.setEnabled(not is_arduino)
        if not is_arduino and self._worker is not None:
            self._disconnect_serial()
        self.control.connect_button.setEnabled(is_arduino)
        if is_arduino:
            self._refresh_ports()
        else:
            self._set_status("Demo mode ready. Press Start to generate sampled signals.")
        self._refresh_plots()

    def _toggle_connection(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            self._disconnect_serial()
            return
        port = self.control.port.currentData()
        if not port:
            self._set_status("Select an available COM port first.", error=True)
            return
        self._worker = SerialWorker(str(port))
        self._has_error = False
        self._worker.packet_received.connect(self._handle_packet)
        self._worker.connected.connect(self._serial_connected)
        self._worker.disconnected.connect(self._serial_disconnected)
        self._worker.error.connect(lambda message: self._set_status(message, error=True))
        self.control.connect_button.setEnabled(False)
        self._set_status(f"Opening {port}…")
        self._worker.start()

    def _serial_connected(self) -> None:
        self.control.connect_button.setText("Disconnect")
        self.control.connect_button.setEnabled(True)
        self._has_error = False
        self._set_status("Arduino connected. Potentiometer signal expected on selected ADC channel.")
        self._send_setting_commands()
        if self._worker is not None:
            self._worker.send_bytes(command_frame(COMMAND_DEVICE_INFO))

    def _serial_disconnected(self) -> None:
        if self.sender() is not self._worker:
            return
        self.control.connect_button.setText("Connect")
        self.control.connect_button.setEnabled(self.control.source.currentText() == "Arduino")
        if self._worker is not None and not self._worker.isRunning():
            self._worker = None
        if self.control.source.currentText() == "Arduino" and not self._has_error:
            self._set_status("Arduino disconnected.")

    def _disconnect_serial(self) -> None:
        worker = self._worker
        if worker is None:
            return
        if worker.isRunning():
            if self._running:
                worker.send_bytes(command_frame(COMMAND_STOP))
                self._running = False
            worker.request_stop()
            worker.wait(1500)
        self._worker = None
        self.control.connect_button.setText("Connect")
        self.control.connect_button.setEnabled(True)
        self.control.start_button.setEnabled(True)
        self.control.stop_button.setEnabled(False)

    def _send_setting_commands(self) -> None:
        if self._worker is None or not self._worker.isRunning():
            return
        fs_hz = self.control.sampling_rate.value()
        self._worker.send_bytes(
            command_frame(COMMAND_SET_SAMPLING_RATE, fs_hz.to_bytes(2, "little"))
        )
        self._worker.send_bytes(
            command_frame(COMMAND_SET_ADC_CHANNEL, bytes((self.control.adc_channel.value(),)))
        )

    def _settings_changed(self, _value=None) -> None:
        fs_hz = self.control.sampling_rate.value()
        if fs_hz != self._last_sampling_rate:
            self._last_sampling_rate = fs_hz
            self._samples = np.empty(0, dtype=np.float64)
            self._sample_counter = 0
        self._send_setting_commands()
        self._refresh_plots()

    def _start_acquisition(self) -> None:
        self._running = True
        self.control.start_button.setEnabled(False)
        self.control.stop_button.setEnabled(True)
        self._samples = np.empty(0, dtype=np.float64)
        self._sample_counter = 0
        self._last_sequence = None
        self._refresh_plots()
        if self.control.source.currentText() == "Arduino":
            if self._worker is None or not self._worker.isRunning():
                self._running = False
                self.control.start_button.setEnabled(True)
                self.control.stop_button.setEnabled(False)
                self._set_status("Connect to the Arduino before starting acquisition.", error=True)
                return
            self._send_setting_commands()
            self._worker.send_bytes(command_frame(COMMAND_START))
            self._set_status("Acquiring ADC samples from the Arduino…")
        else:
            self._demo_timer.start()
            self._set_status("Demo acquisition running.")

    def _stop_acquisition(self) -> None:
        self._demo_timer.stop()
        if self._worker is not None and self._worker.isRunning():
            self._worker.send_bytes(command_frame(COMMAND_STOP))
        self._running = False
        self.control.start_button.setEnabled(True)
        self.control.stop_button.setEnabled(False)
        self._set_status("Acquisition stopped.")

    def _generate_demo_samples(self) -> None:
        fs_hz = self.control.sampling_rate.value()
        count = max(1, round(fs_hz * self._demo_timer.interval() / 1000))
        time_s = (np.arange(self._sample_counter, self._sample_counter + count) / fs_hz)
        frequency_hz = self.control.demo_frequency.value()
        phase = 2 * np.pi * frequency_hz * time_s
        waveform = self.control.waveform.currentText()
        if waveform == "Sine":
            voltage = 2.5 + 1.5 * np.sin(phase)
        elif waveform == "Square":
            voltage = 2.5 + 1.5 * np.where(np.sin(phase) >= 0, 1.0, -1.0)
        elif waveform == "Triangle":
            fractional_phase = (frequency_hz * time_s) % 1.0
            voltage = 2.5 + 1.5 * (2 * np.abs(2 * fractional_phase - 1) - 1)
        else:
            voltage = 2.5 + 0.5 * self._random.normal(size=count)
        self._append_samples(voltage)
        self._sample_counter += count

    def _append_samples(self, new_samples: np.ndarray) -> None:
        self._samples = np.concatenate((self._samples, np.asarray(new_samples, dtype=np.float64)))
        if self._samples.size > 1024:
            self._samples = self._samples[-1024:]

    def _handle_packet(self, packet: Packet) -> None:
        if packet.kind == TYPE_ADC_BLOCK:
            try:
                fs_hz, sequence, samples = decode_adc_block(packet)
                if self._last_sequence is not None and sequence != ((self._last_sequence + 1) & 0xFFFF):
                    self._set_status(
                        f"ADC block gap detected near sequence {sequence}; inspect serial throughput.",
                        error=True,
                    )
                self._last_sequence = sequence
                if fs_hz != self.control.sampling_rate.value():
                    self._samples = np.empty(0, dtype=np.float64)
                    self._sample_counter = 0
                    self._last_sampling_rate = fs_hz
                self.control.sampling_rate.blockSignals(True)
                self.control.sampling_rate.setValue(fs_hz)
                self.control.sampling_rate.blockSignals(False)
                self._append_samples(
                    adc_to_voltage(np.asarray(samples), self.control.reference_voltage.value())
                )
            except (ValueError, OverflowError) as exc:
                self._set_status(f"Invalid ADC block: {exc}", error=True)
        elif packet.kind == TYPE_DEVICE_INFO:
            self._set_status("Arduino device information received; ready for acquisition.")
        elif packet.kind == TYPE_ERROR:
            error_code = packet.payload[0] if packet.payload else 0
            if error_code == 2:
                message = "AVR sample buffer overflowed; lower the sampling frequency."
            else:
                message = f"Arduino reported protocol/device error {error_code}."
            self._set_status(message, error=True)

    def _refresh_plots(self) -> None:
        if self._samples.size == 0:
            self.scope.update([], [], None)
            self.spectrum.update([], [], self.control.sampling_rate.value() / 2.0)
            return
        fs_hz = float(self.control.sampling_rate.value())
        nyquist_hz = fs_hz / 2.0
        count = self._samples.size
        time_s = np.arange(count, dtype=np.float64) / fs_hz
        filter_name = self.control.filter.currentText()
        filtered = None
        try:
            if filter_name != "Off":
                cutoff = min(
                    self.control.cutoff.value(),
                    max(1.0, nyquist_hz * 0.95),
                )
                filtered = apply_filter(self._samples, filter_name, fs_hz, cutoff)
        except ValueError as exc:
            self._set_status(f"Filter configuration error: {exc}", error=True)

        self.scope.update(time_s, self._samples, filtered)
        bins, magnitude = fft_magnitude(self._samples, fs_hz, "hann")
        filtered_magnitude = fft_magnitude(filtered, fs_hz, "hann")[1] if filtered is not None else None
        self.spectrum.update(bins, magnitude, nyquist_hz, filtered_magnitude)

        frequency_hz = dominant_frequency(self._samples, fs_hz)
        self.metrics["samples"].setText(f"Samples: {count}")
        self.metrics["mean"].setText(f"Mean: {compute_mean(self._samples):.3f} V")
        self.metrics["rms"].setText(f"RMS: {compute_rms(self._samples):.3f} V")
        self.metrics["vpp"].setText(f"Vpp: {compute_vpp(self._samples):.3f} V")
        self.metrics["dominant"].setText(
            f"Dominant f: {frequency_hz:.1f} Hz" if frequency_hz else "Dominant f: —"
        )
        self.metrics["nyquist"].setText(f"Nyquist: {nyquist_hz:.0f} Hz")
        self._update_aliasing_warning(frequency_hz, nyquist_hz)

    def _update_aliasing_warning(self, measured_frequency_hz: float, nyquist_hz: float) -> None:
        if self.control.source.currentText() == "Demo signal":
            input_frequency = self.control.demo_frequency.value()
            if input_frequency > nyquist_hz:
                alias_frequency = abs((input_frequency + nyquist_hz) % (2 * nyquist_hz) - nyquist_hz)
                self.warning.setText(
                    f"Aliasing demonstration: input {input_frequency:.1f} Hz exceeds "
                    f"Nyquist {nyquist_hz:.1f} Hz; expected sampled alias ≈ {alias_frequency:.1f} Hz."
                )
                self.warning.setStyleSheet("color: #f87171; font-weight: bold;")
                return
        if measured_frequency_hz > 0.8 * nyquist_hz:
            self.warning.setText(
                "Potential aliasing: a component is close to the Nyquist limit. "
                "The sampled data alone cannot reveal an already-aliased input."
            )
            self.warning.setStyleSheet("color: #fbbf24;")
            return
        self.warning.setText(
            "Sampling theorem: frequencies below Fs/2 are representable; "
            "anti-alias filtering must be applied before the ADC."
        )
        self.warning.setStyleSheet("color: #94a3b8;")

    def closeEvent(self, event) -> None:
        self._demo_timer.stop()
        self._draw_timer.stop()
        self._disconnect_serial()
        super().closeEvent(event)
