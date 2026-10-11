from __future__ import annotations

import time
from queue import Empty, Queue
from threading import Event

from PySide6.QtCore import QThread, Signal

from ..protocol import PacketParser


class SerialWorker(QThread):
    packet_received = Signal(object)
    connected = Signal()
    disconnected = Signal()
    error = Signal(str)

    def __init__(self, port: str, baudrate: int = 115200) -> None:
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._commands: Queue[bytes] = Queue()
        self._stop_requested = Event()

    def send_bytes(self, data: bytes) -> None:
        self._commands.put(bytes(data))

    def request_stop(self) -> None:
        self._stop_requested.set()

    def run(self) -> None:
        try:
            import serial
        except ImportError:
            self.error.emit("pyserial is missing. Run: python -m pip install -e .")
            self.disconnected.emit()
            return

        port = None
        try:
            port = serial.Serial(self.port, self.baudrate, timeout=0.05, write_timeout=1.0)
            parser = PacketParser()
            time.sleep(2.0)
            self.connected.emit()
            while True:
                while True:
                    try:
                        command = self._commands.get_nowait()
                    except Empty:
                        break
                    port.write(command)
                if self._stop_requested.is_set():
                    break
                data = port.read(max(port.in_waiting, 1))
                if data:
                    for packet in parser.feed(data):
                        self.packet_received.emit(packet)
            while not self._commands.empty():
                try:
                    port.write(self._commands.get_nowait())
                except Empty:
                    break
        except (serial.SerialException, OSError) as exc:
            if not self._stop_requested.is_set():
                self.error.emit(f"Serial connection failed: {exc}")
        finally:
            if port is not None and port.is_open:
                port.close()
            self.disconnected.emit()
