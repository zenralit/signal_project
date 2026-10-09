from __future__ import annotations

from ..protocol import TYPE_COMMAND, encode_frame


class SerialConnection:
    """Small interface wrapper around a serial port."""

    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 115200) -> None:
        self.port = port
        self.baudrate = baudrate
        self._serial = None

    def open(self):
        try:
            import serial  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("pyserial is required for serial communication") from exc
        self._serial = serial.Serial(self.port, self.baudrate, timeout=0.1)
        return self._serial

    def close(self):
        if self._serial is not None:
            self._serial.close()
            self._serial = None

    def write_command(self, command: int, payload: bytes = b"") -> None:
        if self._serial is None:
            raise RuntimeError("Serial port is not open")
        self._serial.write(encode_frame(TYPE_COMMAND, bytes([command]) + payload))

    def read_packets(self, timeout_s: float = 0.1):
        if self._serial is None:
            raise RuntimeError("Serial port is not open")
        raw = self._serial.read(self._serial.in_waiting or 64)
        return raw
