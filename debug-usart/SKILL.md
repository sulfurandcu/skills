---
name: debug-usart
description: >-
  Runs a Python UART/serial helper (listen on a COM/tty port, send from stdin,
  or bridge two ports) using pyserial. Use when the user works with serial/UART,
  COM ports, RS-232, USB-serial adapters, firmware logs, AT commands, or asks to
  monitor or forward serial data on Windows or Linux.
---

# UART serial proxy

## Location

- Bundled script: `./usart_proxy.py` in this skill directory
- Dependency: `pip install pyserial`

## Terminal mode (listen + send)

Background thread prints received data; type in the terminal to send lines to the port.

```bash
python ./usart_proxy.py -p COM3 -b 115200
```

Linux:

```bash
python ./usart_proxy.py -p /dev/ttyUSB0 -b 921600
```

- `--hex`: print received bytes as hex
- `--raw-stdin`: send stdin byte-by-byte instead of line-based text
- Optional: `--bytesize`, `--parity` (N/E/O/M/S), `--stopbits` (1 / 1.5 / 2)

## Bridge mode (two ports)

```bash
python ./usart_proxy.py -p COM3 --bridge COM4 -b 115200
```

Ctrl+C stops. Both ends use the same baud and framing in this script.

## Agent notes

- Windows ports: `COMn`; ensure the port is not open in another app.
- If baud or framing must differ per port, extend the script with separate arguments.
