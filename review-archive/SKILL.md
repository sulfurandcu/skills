---
name: review-archive
description: 将代码审查报告存档到当前工作目录下的「.review」目录，使用时间戳命名。
---

# 报告存档技能

将审查报告以 Markdown 文件形式持久化存储。

## 操作步骤

1. 使用当前工作目录作为存档根路径（无需通过 svn info 获取）。
2. 检查 `<当前工作目录>.review/` 目录是否存在，不存在则创建。
3. 获取当前时间戳，格式为 `YYYY-MM-DD-HH-MM-SS`。
4. 将审查报告内容写入 `<当前工作目录>.review/YYYY-MM-DD-HH-MM-SS.md`。

## 参数

- `<报告内容>`（必填）：完整的审查报告 Markdown 文本，由审查技能生成。
- `<当前工作目录>`（选填）：默认为当前工作目录。

## 执行

```bash
mkdir -p "<当前工作目录>.review"
```

然后将报告内容写入：

```
<当前工作目录>.review/<YYYY-MM-DD-HH-MM-SS>.md
```

## 返回模板

> ── 报告已存档 ──
> 路径: <当前工作目录>.review/<YYYY-MM-DD-HH-MM-SS>.md
> 大小: <文件大小>

文件路径不存在或写入失败时返回原始错误。
