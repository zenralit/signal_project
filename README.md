# NawScope

NawScope is a teaching project for a digital oscilloscope and signal analyzer built around an Arduino Uno ATmega328P and a Python GUI on the PC.

The repository contains:

- `firmware/` — AVR firmware written in C with register-level ADC, timer-triggered acquisition, fixed buffer, UART and binary protocol.
- `pc/` — Python project with protocol parsing, DSP, signal generation, and a PySide6/pyqtgraph GUI scaffold.

This implementation focuses on a clean project structure and demonstrably working laboratory-grade DSP and protocol logic, while remaining realistic for the Arduino Uno memory and timing constraints.
