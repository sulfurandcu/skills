---
name: debug-jlink
description: >-
  Debug and probe ARM/RISC-V MCUs with SEGGER J-Link using J-Link Commander,
  GDB Server, RTT, SWO, and IDE launch configs. Use when the user mentions
  J-Link, SEGGER, SWD/JTAG attach, GDB server, RTT, SWO trace, erase/flash via
  J-Link, probe connection errors, or MCU on-chip debug with a J-Link probe.
---

# J-Link MCU Debug

## When to use

Apply this skill when the workflow involves SEGGER J-Link: attach/flash/erase, `JLinkExe` / `JLinkGDBServer`, RTT/SWO, or Cortex-Debug / OpenOCD-style GDB front-ends driven by J-Link.

## Prerequisites

- J-Link software installed ([SEGGER downloads](https://www.segger.com/downloads/jlink/)). Typical install adds tools to PATH on Windows; on Linux/macOS use the package or unpacked install path the user configured.
- **Windows binaries** are often `JLink.exe` / `JLinkGDBServerCL.exe` under the install directory (older docs may say `JLinkExe`; same role).
- USB driver OK; cable is **SWDIO / SWCLK / GND / optional VTref sense** (3V3 reference, not powering the board unless the probe is designed to supply target power).
- Know **exact device name** as in J-Link (examples: `STM32F407VE`, `NRF52840_XXAA`). Wrong name breaks flash algorithms and sometimes attach.
- **HDSC / HC32**: strings are size-specific (e.g. `HC32F4A0_2M` vs `HC32F4A0_1M`). Match the **same** name in Commander, GDB server, flash tool (e.g. eide upload), and `launch.json`.

## Pick interface and speed

- **SWD** is default for Cortex-M: `-if SWD`
- **JTAG** when required by silicon/board: `-if JTAG`
- Start with moderate speed if unstable: `-speed 4000` (kHz) or `auto`; increase after link is reliable.

## J-Link Commander (`JLinkExe`)

Non-interactive one-shot (Windows example; use full path to `JLink.exe` if not on PATH):

```text
JLink.exe -device STM32F407VE -if SWD -speed 4000 -autoconnect 1 -CommanderScript script.jlink
```

`script.jlink` example:

```text
r
h
loadfile build/firmware.hex
r
g
q
```

Common interactive commands (after connect): `?` help, `r` reset, `h` halt, `g` go, `s` step, `mem` read memory, `w1`/`w4` write, `loadfile`, `erase`, `qc` quit.

Use Commander for quick **connectivity tests** before involving GDB or an IDE.

### Commander scripts: delays, run/halt, memory

- **`Sleep <ms>`** — host-side wait in milliseconds. Use after `g` to let the target run, or after `h` to **keep the core halted** while you attach from an IDE or inspect SWD.
- If **`g` errors with “CPU is not halted”** after attach (target already running), script **`h` then `g`** so `g` is issued from a halted state.
- **`mem8 <Addr>,<NumBytes>`** — raw bytes (comma syntax is common in V7.x).
- **`mem32 <Addr>,<NumWords>`** — 32-bit words (quantity is **word count**, not bytes). Good for dumping MMIO blocks when you know the peripheral base from the vendor header (e.g. `CM_TMR6_1_BASE`).

Example — run 10 s, halt, stay halted 10 s, then quit:

```text
h
g
Sleep 10000
h
Sleep 10000
qc
```

## GDB server (`JLinkGDBServer`)

Typical Cortex-M attach (host runs GDB, target via SWD):

```text
JLinkGDBServer -if SWD -device STM32F407VE -speed 4000 -localhostonly 1
```

Then GDB (toolchain `arm-none-eabi-gdb` or equivalent):

```text
target remote localhost:2331
monitor reset
load
```

Notes:

- Default GDB port is **2331** (SWO RTT channel setup may use additional ports depending on version).
- **Semihosting / semihost syscall** issues: ensure startup matches how the firmware was built; otherwise breakpoints in `printf` paths can look like hangs.
- **RTOS awareness**: add `-rtos GDBServer/RTOSPlugin_FreeRTOS` (or the matching plugin name for the RTOS) when thread-aware stepping is required.

## RTT (SEGGER Real-Time Transfer)

1. Firmware links **SEGGER RTT** library and initializes RTT buffers.
2. Use **RTT Viewer** GUI, or `JLinkRTTClient` / `JLinkRTTLogger` from the J-Link package.
3. If no output: verify buffer addresses (auto-scan in Viewer), correct core/device, and that the target is running (`g`).

## SWO / pin trace (Cortex-M)

- Enable SWO in firmware (ITM/TPIU init) at a baud compatible with the core clock and J-Link settings.
- Use J-Link SWO Viewer or GDB `monitor` SWO commands as documented for your J-Link version.
- **SWO pin** must be routed and configured on the MCU (often shared with JTAG TDO — check datasheet).

## IDE integration (concise patterns)

**VS Code — Cortex-Debug** (`launch.json` sketch):

```json
{
  "type": "cortex-debug",
  "request": "launch",
  "servertype": "jlink",
  "device": "STM32F407VE",
  "interface": "swd",
  "executable": "${workspaceFolder}/build/firmware.elf"
}
```

Adjust `device`, `executable`, `svdFile` if available, and `rtos` when using an RTOS package supported by the extension.

- **Multi-root / monorepo**: Prefer **`${workspaceFolder}`** (and paths under it) for `cwd` and `executable` when `launch.json` lives in a **board** or **app** subfolder. **`${workspaceRoot}`** often resolves to the **first** workspace folder and can point at the wrong ELF.
- **J-Link not on PATH**: set workspace/user setting **`cortex-debug.JLinkGDBServerPath`** to the full path of **`JLinkGDBServerCL.exe`** (or `JLinkGDBServer.exe`).
- **Embedded IDE (eide) flash**: set **`EIDE.JLink.InstallDirectory`** to the J-Link **install directory** (parent of `JLink.exe`) so upload finds the tools.

**Eclipse / MCUXpresso / STM32CubeIDE**: select SEGGER J-Link GDB server, same **device string** and **SWD**, point to the correct ELF.

## Troubleshooting checklist

- **Cannot connect / “No device found”**: wiring (SWDIO/SWCLK swap), target powered, NRST held low, BOOT pins forcing wrong mode, need `connect` under reset (`JLink.exe` supports connect strategies; try `JLink.exe -JLinkScriptFile` or Commander `connect` options per chip errata).
- **Wrong device name**: fix `-device` to the exact J-Link spelling.
- **Voltage / level**: VTref readback sane? Mixed 1V8/3V3 without level shifters causes flaky SWD.
- **Flash verify fails**: full chip erase, debugger not conflicting with WRP/option bytes, correct algorithm (device pack).
- **GDB connects but no breakpoints**: debug symbols (`-g`), load address matches linker script, optimization stripping symbols (`Og` preferred for debug).

## Agent workflow

1. Confirm **MCU part**, **interface (SWD/JTAG)**, and **host OS** if paths matter.
2. Reproduce with **J-Link Commander** or a minimal **GDB server + GDB** session before deep IDE config.
3. Capture exact **console text** from `JLinkGDBServer` / `JLink.exe` on failure; those lines usually identify wiring vs device vs permissions.
4. Only then adjust IDE `launch.json` or project debug settings to match the working CLI flags.
5. For **register/peripheral snapshots** without GDB, use Commander **`h`** + **`mem32`/`mem8`** at addresses from the **device header** (`*_BASE`, struct offsets); combine with **`Sleep`** to sample after the target has run for a defined time.

## Safety

Do not assume the agent can power targets through the probe. Prefer explicit user confirmation before **mass erase** or **option-byte** changes that can brick or lock devices.
