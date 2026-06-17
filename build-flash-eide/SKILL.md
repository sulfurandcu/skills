---
name: build-flash-eide
description: 通过 unify_builder.exe 构建、重新构建、清理和烧录 Embedded IDE (eide) 项目。当用户要求编译、烧录、下载或刷写固件时使用此技能。
---

# eide 构建与烧录

## 适用场景

当用户要求以下操作时使用此技能：
- 编译/构建固件
- 烧录/下载固件到目标设备
- 执行构建+烧录流程
- 清理或重新构建此 eide 项目

## 构建工具

`unify_builder.exe` 随 eide VS Code 扩展一起发布：

```
%USERPROFILE%\.vscode\extensions\cl.eide-3.27.2\res\tools\win32\unify_builder\unify_builder.exe
```

### 用法

```
unify_builder.exe -p <参数文件>               # 增量构建
unify_builder.exe -p <参数文件> --rebuild      # 强制全部重新构建
unify_builder.exe -p <参数文件> --dry-run      # 试运行（不实际编译）
unify_builder.exe -p <参数文件> --only-dump-compilerdb  # 导出 compile_commands.json
```

### 关键：工作目录

`unify_builder.exe` 必须在**项目根目录**下运行——即包含 `.eide/eide.yml` 的目录。`builder.params` 中的所有路径都是相对于该目录的。

## 项目自动发现

在执行任何构建/烧录操作之前，从当前工作区发现项目布局：

1. **找到 eide 项目根目录** — 在工作区下搜索 `.eide/eide.yml`。包含 `.eide/` 的目录即为项目根目录。可能存在多个项目（如 `board/v1.0.0/`）；选择用户所指的那个，或第一个找到的。

2. **定位 builder.params** — 在 `<项目根目录>/output/*/builder.params` 下查找。如果存在多个配置（如 `output/gcc/`、`output/debug/`），默认选择 `gcc`，除非用户另有指定。

3. **定位 commands.jlink**（用于烧录）— 与 `builder.params` 在同一目录下。

4. **提取工具链路径** — 读取 `builder.params` JSON 文件，获取 `toolchainLocation`（ARM GCC 路径）和 `env.ToolchainRoot`。

5. **提取烧录工具信息** — 读取 `.eide/eide.yml`，获取 `targets.<配置>.uploader` 和 `uploadConfigMap.<烧录器>` 以了解烧录工具和设备信息。

## 命令映射

| 请求 | 操作 |
|---|---|
| 构建 | 在项目根目录执行 `unify_builder.exe -p <参数文件>` |
| 重新构建 | 在项目根目录执行 `unify_builder.exe -p <参数文件> --rebuild` |
| 清理 | 删除 `<output>/.obj/` 然后执行 `--rebuild` |
| 烧录 | 使用命令文件运行烧录工具（J-Link / pyOCD 等） |
| 构建+烧录 | 先构建 → 成功后烧录 |

## 执行流程

### 第一步：发现项目

```
搜索工作区中的 .eide/eide.yml → 项目根目录
查找 output/*/builder.params → 参数文件 + 输出目录
读取 builder.params → 工具链路径、构建配置
读取 .eide/eide.yml → MCU 设备、烧录工具、烧录配置
```

### 第二步：构建

```bash
cd <项目根目录>
"<unify_builder.exe>" -p <参数文件相对路径>
# 或使用 --rebuild 强制重新构建
```

**成功**：退出码为 0，输出中包含 `build successfully !`
**失败**：退出码非零，输出中包含 `compilation failed` 或 `link failed`

错误详情出现在输出中 `---` 分隔符之后：文件路径、行号、错误信息以及失败的完整 gcc 命令。

### 第三步：烧录（如果需要）

从 `eide.yml` 读取烧录器类型 → `uploader` 字段（如 `JLink`）。

**对于 J-Link：**

```bash
JLink.exe -ExitOnError 1 -AutoConnect 1 -Device <设备> -If <接口> -Speed <速度> -CommandFile <commands.jlink>
```

- `<设备>` 来自 `uploadConfigMap.JLink.cpuInfo.cpuName`
- `<接口>` 默认为 `SWD`
- `<速度>` 来自 `uploadConfigMap.JLink.speed`
- `<commands.jlink>` 位于输出目录中，与 `builder.params` 同目录

`commands.jlink` 内容：
```
r
halt
loadfile "<hex文件路径>"
r
go
exit
```

**成功**：输出中包含 `O.K.` 并以 `Script processing completed.` 结尾。
**失败**：输出中包含 `ERROR`，可能是连接/探针/电源问题。

## 错误恢复

### 构建失败

1. **解析错误** — 从 `---` 之后的输出中查看，会显示文件、行号和编译器消息。
2. **builder.params 过期**：如果错误提示文件缺失/重命名，说明 `builder.params` 可能与 `eide.yml` 不同步。在 VS Code / Cursor 中打开项目并运行一次 eide 的 `build` 命令来重新生成，然后再继续直接构建。
3. **找不到工具链**：验证 `builder.params` 中的 `toolchainLocation` 路径是否存在，以及 `bin/arm-none-eabi-gcc.exe` 是否可访问。
4. **增量构建不一致**：使用 `--rebuild` 强制进行全新编译。
5. **修复源码后**：重新运行相同的构建命令（增量构建，仅重新编译已更改的文件）。

### 烧录失败

1. **连接问题**：检查探针 USB 连接、目标设备电源、SWD 接线（SWCLK/SWDIO/GND）。
2. **设备被锁定**：通过 `JLink.exe -Device <设备> -If SWD` 然后执行 `unlock <设备>` 来解锁。
3. 解决硬件问题后**重试**烧录命令。

## 排查清单

- [ ] 已找到 `.eide/eide.yml` → 项目根目录已确定
- [ ] `builder.params` 存在于 `output/<配置>/` 下
- [ ] `builder.params` 中的工具链路径有效
- [ ] 调用 `unify_builder.exe` 时工作目录为项目根目录
- [ ] 烧录工具可执行文件在 PATH 中或位于已知位置
- [ ] 目标设备已连接并通电（烧录时需要）
- [ ] `commands.jlink` 存在于输出目录中（J-Link 烧录时需要）
- [ ] 如果项目结构有变化，请先通过 eide VS Code 命令重新生成 `builder.params`
