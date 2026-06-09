#!/usr/bin/env python3
"""
Serial (UART) helper: receive from port and send from stdin, or bridge two ports.

Requires: pip install pyserial
"""

from __future__ import annotations

import argparse
import sys
import threading
import time
try:
    import serial
    from serial import Serial, SerialException
except ImportError as e:
    print("Missing dependency: install with  pip install pyserial", file=sys.stderr)
    raise SystemExit(1) from e


def _open_port(
    port: str,
    baud: int,
    bytesize: int,
    parity: str,
    stopbits: float,
    timeout: float,
) -> Serial:
    parity_map = {
        "N": serial.PARITY_NONE,
        "E": serial.PARITY_EVEN,
        "O": serial.PARITY_ODD,
        "M": serial.PARITY_MARK,
        "S": serial.PARITY_SPACE,
    }
    stop_map = {1: serial.STOPBITS_ONE, 1.5: serial.STOPBITS_ONE_POINT_FIVE, 2: serial.STOPBITS_TWO}
    size_map = {5: serial.FIVEBITS, 6: serial.SIXBITS, 7: serial.SEVENBITS, 8: serial.EIGHTBITS}

    if bytesize not in size_map:
        raise ValueError(f"unsupported bytesize {bytesize}")
    if parity.upper() not in parity_map:
        raise ValueError(f"unsupported parity {parity}")
    if stopbits not in stop_map:
        raise ValueError(f"unsupported stopbits {stopbits}")

    return Serial(
        port=port,
        baudrate=baud,
        bytesize=size_map[bytesize],
        parity=parity_map[parity.upper()],
        stopbits=stop_map[stopbits],
        timeout=timeout,
    )


def run_terminal(
    port: str,
    baud: int,
    bytesize: int,
    parity: str,
    stopbits: float,
    echo_hex: bool,
    line_mode: bool,
) -> None:
    """Read serial in a thread; write lines from stdin to serial."""
    ser = _open_port(port, baud, bytesize, parity, stopbits, timeout=0.1)
    stop = threading.Event()

    def reader() -> None:
        try:
            while not stop.is_set():
                chunk = ser.read(4096)
                if not chunk:
                    continue
                if echo_hex:
                    sys.stdout.buffer.write(chunk.hex(" ").encode("ascii") + b"\n")
                else:
                    sys.stdout.buffer.write(chunk)
                sys.stdout.buffer.flush()
        except SerialException as ex:
            print(f"\n[reader] {ex}", file=sys.stderr)

    t = threading.Thread(target=reader, daemon=True)
    t.start()

    print(
        f"Opened {port} @ {baud} 8{parity}{int(stopbits) if stopbits == int(stopbits) else stopbits}. "
        "Type to send; Ctrl+C to exit.",
        file=sys.stderr,
    )

    try:
        if line_mode:
            for line in sys.stdin:
                ser.write(line.encode(sys.stdin.encoding or "utf-8", errors="replace"))
        else:
            while True:
                data = sys.stdin.buffer.read(1)
                if not data:
                    break
                ser.write(data)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        ser.close()
        t.join(timeout=2.0)


def run_bridge(
    port_a: str,
    port_b: str,
    baud: int,
    bytesize: int,
    parity: str,
    stopbits: float,
) -> None:
    """Forward bytes between two serial ports until interrupted."""
    a = _open_port(port_a, baud, bytesize, parity, stopbits, timeout=0.05)
    b = _open_port(port_b, baud, bytesize, parity, stopbits, timeout=0.05)
    stop = threading.Event()

    def forward(src: Serial, dst: Serial, name: str) -> None:
        try:
            while not stop.is_set():
                data = src.read(4096)
                if data:
                    dst.write(data)
        except SerialException as ex:
            print(f"[{name}] {ex}", file=sys.stderr)
        finally:
            stop.set()

    t1 = threading.Thread(target=forward, args=(a, b, "A->B"), daemon=True)
    t2 = threading.Thread(target=forward, args=(b, a, "B->A"), daemon=True)
    t1.start()
    t2.start()
    print(
        f"Bridge {port_a} <-> {port_b} @ {baud}. Ctrl+C to stop.",
        file=sys.stderr,
    )
    try:
        while t1.is_alive() and t2.is_alive():
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        a.close()
        b.close()


def main() -> None:
    p = argparse.ArgumentParser(description="UART listen/send or two-port bridge (pyserial).")
    p.add_argument("-p", "--port", help="Serial device (e.g. COM3 or /dev/ttyUSB0)")
    p.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default 115200)")
    p.add_argument("--bytesize", type=int, default=8, choices=[5, 6, 7, 8])
    p.add_argument("--parity", default="N", help="N E O M S (default N)")
    p.add_argument("--stopbits", type=float, default=1, choices=[1, 1.5, 2])
    p.add_argument(
        "--hex",
        action="store_true",
        help="Print received bytes as hex (terminal mode)",
    )
    p.add_argument(
        "--raw-stdin",
        action="store_true",
        help="Send stdin byte-by-byte (default: line-based text)",
    )
    p.add_argument(
        "--bridge",
        metavar="PORT_B",
        help="Bridge mode: forward between --port and this second port",
    )
    args = p.parse_args()

    if not args.port:
        p.error("--port is required unless using -h")

    if args.bridge:
        run_bridge(
            args.port,
            args.bridge,
            args.baud,
            args.bytesize,
            args.parity,
            args.stopbits,
        )
    else:
        run_terminal(
            args.port,
            args.baud,
            args.bytesize,
            args.parity,
            args.stopbits,
            echo_hex=args.hex,
            line_mode=not args.raw_stdin,
        )


if __name__ == "__main__":
    main()
