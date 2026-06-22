---
name: debug-shell
description: >-
  通过串口与设备建立 Shell 交互会话。支持交互式终端、单命令执行、
  批量命令脚本、会话日志记录。当用户需要登录嵌入式设备的串口 Shell、
  通过 COM/tty 端口与设备命令行交互、或自动化执行串口命令时使用此技能。
---

# 串口 Shell 交互

## 位置

- 捆绑脚本：本技能目录下的 `./shell_proxy.py`
- 依赖：`pip install pyserial`

## 交互模式（默认）

打开串口并进入交互式 Shell 会话，从终端输入命令，实时查看设备回显。

```bash
python ./shell_proxy.py -p COM3 -b 115200
```

Linux：

```bash
python ./shell_proxy.py -p /dev/ttyUSB0 -b 921600
```

- `--hex`：以十六进制格式打印接收到的数据（用于调试乱码）
- `--log <file>`：将会话记录到指定文件
- `--crlf`：发送命令时使用 CR+LF 换行（某些嵌入式 shell 要求）
- `--encoding <enc>`：指定串口编码（默认 utf-8，常见设备可能用 gbk/latin-1）
- 可选：`--bytesize`、`--parity`（N/E/O/M/S）、`--stopbits`（1 / 1.5 / 2）

按 `Ctrl+]` 退出会话（不会直接断开串口，先发送 exit 命令）。

## 单命令模式

发送一条命令，等待响应后退出。适合在脚本中调用。

```bash
python ./shell_proxy.py -p COM3 -b 115200 --cmd "ifconfig"
python ./shell_proxy.py -p COM3 -b 115200 --cmd "cat /proc/version" --timeout 5
```

- `--cmd <command>`：要执行的命令
- `--timeout <seconds>`：等待响应的超时时间（默认 3 秒）
- `--prompt <pattern>`：期望的 Shell 提示符（用于判断命令输出结束）
- `--log <file>`：将输出记录到文件

## 批量脚本模式

从文件读取命令逐条执行。

```bash
python ./shell_proxy.py -p COM3 -b 115200 --script ./commands.txt
```

命令文件格式（每行一条命令，`#` 开头为注释）：

```
# 查看系统信息
uname -a
cat /proc/cpuinfo
# 查看网络配置
ifconfig
```

## 启动时自动发送

连接后先发送初始化命令（如登录、切换目录等）：

```bash
python ./shell_proxy.py -p COM3 -b 115200 --init "root" --init "cd /app"
```

多个 `--init` 按顺序依次发送，每条之间等待 `--init-delay` 秒（默认 0.5）。

## Agent 注意事项

- Windows 端口：`COMn`；确保端口未被其他应用程序（如 PuTTY、SecureCRT）占用。
- 嵌入式设备串口 Shell 常见波特率：115200、921600、1500000。
- 如果设备回显乱码，先尝试 `--encoding gbk` 或 `--hex` 查看原始字节。
- 某些 Bootloader（如 U-Boot）使用不同的换行符，可用 `--crlf` 适配。
- 退出交互模式前，建议先输入 `exit` 正常登出，避免设备端残留登录会话。
- 需要两个串口互通时，请使用 `debug-usart` 技能的桥接模式。
