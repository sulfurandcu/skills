---
name: debug-jlink
description: >-
  使用 SEGGER J-Link 调试和探测 ARM/RISC-V MCU，涵盖 J-Link Commander、
  GDB Server、RTT、SWO 以及 IDE 启动配置。当用户提到 J-Link、SEGGER、
  SWD/JTAG 连接、GDB server、RTT、SWO 跟踪、通过 J-Link 擦除/烧录、
  探针连接错误，或使用 J-Link 探针进行 MCU 片上调试时使用此技能。
---

# J-Link MCU 调试

## 适用场景

当工作流涉及 SEGGER J-Link 时应用此技能：连接/烧录/擦除、`JLinkExe` / `JLinkGDBServer`、RTT/SWO，或由 J-Link 驱动的 Cortex-Debug / OpenOCD 风格的 GDB 前端。

## 前置条件

- 已安装 J-Link 软件（[SEGGER 下载](https://www.segger.com/downloads/jlink/)）。Windows 上通常会将工具添加到 PATH；Linux/macOS 上使用用户配置的软件包或解压后的安装路径。
- **Windows 可执行文件**通常是安装目录下的 `JLink.exe` / `JLinkGDBServerCL.exe`（旧文档可能写成 `JLinkExe`，作用相同）。
- USB 驱动正常；接线为 **SWDIO / SWCLK / GND / 可选的 VTref 检测**（3.3V 参考电压，不给开发板供电，除非探针本身设计为提供目标电源）。
- 了解 J-Link 中的**精确设备名称**（例如：`STM32F407VE`、`NRF52840_XXAA`）。错误的名称会导致烧录算法失败，有时连连接都会失败。
- **HDSC / HC32**：字符串与容量相关（如 `HC32F4A0_2M` vs `HC32F4A0_1M`）。在 Commander、GDB server、烧录工具（如 eide upload）和 `launch.json` 中使用**相同**的名称。

## 查找 J-Link 工具

在使用 J-Link 命令之前，需要先定位工具路径。按以下顺序查找：

1. **检查 PATH** — 在终端中运行 `where JLink.exe`，如果找到则直接使用。
2. **默认安装路径** — 检查以下常见位置：
   - `C:\Program Files\SEGGER\JLink\`
   - `C:\Program Files (x86)\SEGGER\JLink\`
3. **注册表** — 查询 `HKEY_LOCAL_MACHINE\SOFTWARE\SEGGER\J-Link` 下的 `InstallPath` 值。

定位到安装目录后，关键可执行文件都在该目录下：

| 工具 | 文件名 |
|---|---|
| Commander | `JLink.exe` |
| GDB Server | `JLinkGDBServerCL.exe`（命令行）或 `JLinkGDBServer.exe`（GUI） |
| RTT Client | `JLinkRTTClient.exe` |
| RTT Logger | `JLinkRTTLogger.exe` |
| SWO Viewer | `JLinkSWOViewerCL.exe` |

如果工具不在 PATH 中，后续所有命令都需要使用**完整路径**，例如：
```text
"C:\Program Files\SEGGER\JLink\JLink.exe" -device STM32F407VE ...
```

## 选择接口和速度

- **SWD** 是 Cortex-M 的默认选择：`-if SWD`
- **JTAG** 当芯片/板子需要时使用：`-if JTAG`
- 如果不稳定，从中等速度开始：`-speed 4000`（kHz）或 `auto`；连接可靠后再提高速度。

## J-Link Commander（`JLinkExe`）

非交互式单次执行（Windows 示例；如果不在 PATH 中请使用 `JLink.exe` 的完整路径）：

```text
JLink.exe -device STM32F407VE -if SWD -speed 4000 -autoconnect 1 -CommanderScript script.jlink
```

`script.jlink` 示例：

```text
r
h
loadfile build/firmware.hex
r
g
q
```

常用交互命令（连接后）：`?` 帮助、`r` 复位、`h` 暂停、`g` 运行、`s` 单步、`mem` 读取内存、`w1`/`w4` 写入、`loadfile`、`erase`、`qc` 退出。

在接入 GDB 或 IDE 之前，使用 Commander 进行快速的**连通性测试**。

### Commander 脚本：延迟、运行/暂停、内存

- **`Sleep <ms>`** — 主机端等待，单位为毫秒。在 `g` 之后使用以使目标运行一段时间，或在 `h` 之后使用以**保持内核暂停**，方便从 IDE 连接或检查 SWD。
- 如果连接后 **`g` 报错 "CPU is not halted"**（目标已在运行），脚本中先 **`h` 再 `g`**，使 `g` 从暂停状态发出。
- **`mem8 <地址>,<字节数>`** — 原始字节（V7.x 中常用逗号语法）。
- **`mem32 <地址>,<字数>`** — 32 位字（数量是**字数**，不是字节数）。适用于在已知外设基地址（来自厂商头文件，如 `CM_TMR6_1_BASE`）时转储 MMIO 块。

示例 — 运行 10 秒，暂停，保持暂停 10 秒，然后退出：

```text
h
g
Sleep 10000
h
Sleep 10000
qc
```

## GDB Server（`JLinkGDBServer`）

典型的 Cortex-M 连接（主机运行 GDB，目标通过 SWD 连接）：

```text
JLinkGDBServer -if SWD -device STM32F407VE -speed 4000 -localhostonly 1
```

然后使用 GDB（工具链中的 `arm-none-eabi-gdb` 或等效工具）：

```text
target remote localhost:2331
monitor reset
load
```

注意事项：

- 默认 GDB 端口为 **2331**（SWO RTT 通道设置可能根据版本使用额外端口）。
- **半主机 / semihost 系统调用**问题：确保启动配置与固件的编译方式匹配；否则 `printf` 路径中的断点可能看起来像卡死。
- **RTOS 感知**：需要线程感知单步调试时，添加 `-rtos GDBServer/RTOSPlugin_FreeRTOS`（或对应 RTOS 的插件名称）。

## RTT（SEGGER 实时传输）

1. 固件链接 **SEGGER RTT** 库并初始化 RTT 缓冲区。
2. 使用 **RTT Viewer** 图形界面，或 J-Link 软件包中的 `JLinkRTTClient` / `JLinkRTTLogger`。
3. 如果没有输出：验证缓冲区地址（Viewer 中可自动扫描）、正确的内核/设备，以及目标是否正在运行（`g`）。

## SWO / 引脚跟踪（Cortex-M）

- 在固件中启用 SWO（ITM/TPIU 初始化），波特率需与内核时钟和 J-Link 设置兼容。
- 使用 J-Link SWO Viewer 或 GDB `monitor` SWO 命令（具体用法请参考你所用 J-Link 版本的文档）。
- **SWO 引脚**必须在 MCU 上正确布线并配置（通常与 JTAG TDO 共用 — 请查阅数据手册）。

## IDE 集成（简明模式）

**VS Code — Cortex-Debug**（`launch.json` 模板）：

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

根据实际情况调整 `device`、`executable`、`svdFile`（如果有的话），以及使用扩展支持的 RTOS 包时的 `rtos` 设置。

- **多根目录 / monorepo**：当 `launch.json` 位于 **board** 或 **app** 子文件夹中时，`cwd` 和 `executable` 优先使用 **`${workspaceFolder}`**（及其下的路径）。**`${workspaceRoot}`** 通常解析为**第一个**工作区文件夹，可能指向错误的 ELF。
- **J-Link 不在 PATH 中**：将工作区/用户设置 **`cortex-debug.JLinkGDBServerPath`** 设为 **`JLinkGDBServerCL.exe`**（或 `JLinkGDBServer.exe`）的完整路径。
- **Embedded IDE (eide) 烧录**：将 **`EIDE.JLink.InstallDirectory`** 设为 J-Link **安装目录**（`JLink.exe` 的父目录），以便 upload 能找到工具。

**Eclipse / MCUXpresso / STM32CubeIDE**：选择 SEGGER J-Link GDB server，使用相同的**设备字符串**和 **SWD**，指向正确的 ELF。

## 排查清单

- **无法连接 / "No device found"**：接线问题（SWDIO/SWCLK 接反）、目标未上电、NRST 被拉低、BOOT 引脚强制进入错误模式、需要在复位下连接（`JLink.exe` 支持连接策略；根据芯片勘误表尝试 `JLink.exe -JLinkScriptFile` 或 Commander 的 `connect` 选项）。
- **设备名称错误**：将 `-device` 修正为 J-Link 中的准确拼写。
- **电压 / 电平**：VTref 回读值是否正常？1.8V/3.3V 混用且无电平转换器会导致 SWD 不稳定。
- **烧录校验失败**：全片擦除、调试器与 WRP/选项字节无冲突、正确的算法（设备包）。
- **GDB 已连接但无断点**：调试符号（`-g`）、加载地址与链接脚本匹配、优化导致符号被剥离（调试建议使用 `Og`）。

## Agent 工作流程

1. 确认 **MCU 型号**、**接口（SWD/JTAG）** 以及**主机操作系统**（如果路径相关）。
2. 在深入 IDE 配置之前，先用 **J-Link Commander** 或最小化的 **GDB server + GDB** 会话复现问题。
3. 捕获 `JLinkGDBServer` / `JLink.exe` 失败时的**完整控制台输出**；这些输出通常能区分是接线问题、设备问题还是权限问题。
4. 然后再调整 IDE 的 `launch.json` 或项目调试设置，使其与已验证的 CLI 参数匹配。
5. 对于不需要 GDB 的**寄存器/外设快照**，使用 Commander 的 **`h`** + **`mem32`/`mem8`**，地址来自**设备头文件**（`*_BASE`、结构体偏移量）；配合 **`Sleep`** 在目标运行指定时间后进行采样。

## 安全事项

不要假设 agent 可以通过探针给目标供电。在执行**全片擦除**或**选项字节**更改之前，优先获取用户的明确确认，因为这些操作可能导致设备变砖或锁定。
