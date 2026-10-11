from __future__ import annotations

from ..protocol import encode_frame


def available_ports() -> list[tuple[str, str]]:
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError("Install the PC dependencies with: python -m pip install -e .") from exc
    return [(port.device, port.description) for port in list_ports.comports()]


def command_frame(command: int, payload: bytes = b"") -> bytes:
    return encode_frame(0x06, bytes((command,)) + payload)
