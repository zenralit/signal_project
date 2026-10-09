from __future__ import annotations

import argparse

from nawscope import __version__


def main() -> None:
    parser = argparse.ArgumentParser(description="NawScope signal analyzer")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="serial port for Arduino connection")
    parser.add_argument("--baud", type=int, default=115200, help="UART baud rate")
    args = parser.parse_args()
    print(f"NawScope {__version__} ready on {args.port} @ {args.baud} baud")


if __name__ == "__main__":
    main()
