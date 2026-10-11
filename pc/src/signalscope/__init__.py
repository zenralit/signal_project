"""SignalScope package."""

__version__ = "0.1.0"

__all__ = [
    "ProtocolError",
    "Packet",
    "encode_frame",
    "decode_stream",
    "generate_sine",
    "generate_square",
    "generate_triangle",
    "generate_noise",
    "generate_multitone",
    "compute_rms",
    "compute_mean",
    "compute_vpp",
    "fft_magnitude",
    "moving_average",
    "__version__",
]

from .protocol import Packet, ProtocolError, decode_stream, encode_frame
from .dsp import (
    compute_mean,
    compute_rms,
    compute_vpp,
    fft_magnitude,
    moving_average,
)
from .signal import (
    generate_multitone,
    generate_noise,
    generate_sine,
    generate_square,
    generate_triangle,
)
