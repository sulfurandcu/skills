---
name: debug-usart
description: >-
  使用 pyserial 运行 Python UART/串口辅助工具（监听 COM/tty 端口、从 stdin 发送、
  或桥接两个端口）。当用户使用串口/UART、COM 端口、RS-232、USB 转串口适配器、
  固件日志、AT 指令，或要求在 Windows 或 Linux 上监控或转发串口数据时使用此技能。
---

# UART 串口代理

## 位置

- 捆绑脚本：本技能目录下的 `./usart_proxy.py`
- 依赖：`pip install pyserial`

## 终端模式（监听 + 发送）

后台线程打印接收到的数据；在终端中输入内容即可按行发送到串口。

```bash
python ./usart_proxy.py -p COM3 -b 115200
```

Linux：

```bash
python ./usart_proxy.py -p /dev/ttyUSB0 -b 921600
```

- `--hex`：以十六进制格式打印接收到的字节
- `--raw-stdin`：逐字节发送 stdin 而不是按行发送文本
- 可选：`--bytesize`、`--parity`（N/E/O/M/S）、`--stopbits`（1 / 1.5 / 2）

## 桥接模式（两个端口）

```bash
python ./usart_proxy.py -p COM3 --bridge COM4 -b 115200
```

按 Ctrl+C 停止。此脚本中两端使用相同的波特率和帧格式。

## Agent 注意事项

- Windows 端口：`COMn`；确保端口未被其他应用程序占用。
- 如果每个端口需要不同的波特率或帧格式，请使用单独的参数扩展脚本。
