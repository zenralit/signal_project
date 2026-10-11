"""Serial port discovery and background acquisition."""

from .connection import available_ports, command_frame
from .worker import SerialWorker

__all__ = ["SerialWorker", "available_ports", "command_frame"]
