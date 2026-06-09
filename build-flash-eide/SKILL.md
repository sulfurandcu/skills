---
name: build-flash-eide
description: Build, rebuild, clean, and flash an Embedded IDE (eide) project through VS Code tasks. Use when the user asks to compile, burn, download, or flash firmware in this eide workspace.
---

# eide Build and Flash

## When to use

Use this skill when the user asks to:
- compile/build firmware
- flash/burn/download firmware to target
- run a build+flash sequence
- clean or rebuild this eide project

## Project defaults

- Workspace root: `e:/codespace/baseline/rtthread/baseline-eide`
- Task file: `board/v1.0.0/.vscode/tasks.json`
- Supported task labels:
  - `build`
  - `flash`
  - `build and flash`
  - `rebuild`
  - `clean`

These tasks call eide commands:
- `${command:eide.project.build}`
- `${command:eide.project.uploadToDevice}`
- `${command:eide.project.buildAndFlash}`
- `${command:eide.project.rebuild}`
- `${command:eide.project.clean}`

## Execution workflow

1. Confirm the request maps to one of the task labels above.
2. Execute the corresponding VS Code task in terminal.
3. Report clear result:
   - success/failure
   - key output lines (artifact path, flashing tool, error messages)
4. On failure, run focused recovery:
   - For build failures: try `clean` then `rebuild`.
   - For flash failures: verify probe/port/target power, then retry `flash`.

## Command mapping (agent side)

- Build only -> run task `build`
- Flash only -> run task `flash`
- Build and flash -> run task `build and flash`
- Force full rebuild -> run tasks `clean` then `rebuild`

## Troubleshooting checklist

- eide extension is installed and active in current VS Code/Cursor session.
- Correct eide project is opened (folder containing `board/v1.0.0/.vscode/tasks.json`).
- Download toolchain/debugger path is valid (for example J-Link executable path).
- Target device is connected and powered.
- Current workspace matches requested board/configuration.
