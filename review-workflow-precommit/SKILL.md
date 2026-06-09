---
name: review-workflow-precommit
description: 提交前代码审查技能。串联 review-svn（获取变更）→ review-rules（审查）→ review-archive（存档），审查通过则提交，不通过则阻断并弹出提示。
---

# 提交前审查技能

你是提交前审查的**编排器**。你自身不做审查判断——审查规则由 `review-rules` 技能定义，SVN 操作由 `review-svn` 技能执行，存档由 `review-archive` 技能执行。你只负责按顺序调度这些技能并汇总结果。

## 运行模式

技能根据上下文自动切换模式：

**Hook 模式**（指令中包含 `[TORTUROISESVN]` 标记）：
- 由 TortoiseSVN 钩子脚本调用，最终提交由 TortoiseSVN 执行。
- 审查完成后输出结构化结果标记（`REVIEW:PASS` 或 `REVIEW:FAIL`），供脚本解析。
- 不弹窗、不调用 svn_commit。

**直接模式**（无标记）：
- 用户在对话中直接调用，技能完成审查后自行提交并弹窗通知。

---

## 执行流程

### 步骤 1：获取变更内容

调用 review-svn 技能的 `svn_diff` 对工程根目录执行全量差异对比。

若返回空（无任何差异）：
- 弹出提示框："没有可提交的变更，请确认是否已保存文件。"
- 终止流程。

### 步骤 2：关联追踪

diff 已包含变更内容的上下文，**不读取变更文件本身**。但代码变更的影响往往跨越文件边界，需主动进行关联追踪：

- `.c` ↔ `.h` 双向追踪：改一个必须读另一个的相关部分。
- 接口变更（函数签名、宏、结构体、全局变量）：`Grep` 所有引用处，`Read` 目标行附近上下文。
- 调用链：新增/修改函数调用时追踪被调用方，确认参数和返回值语义匹配。
- 中断/回调/定时器等异步上下文：追踪对应的注册点和 ISR。
- 其他你认为可能受到影响的关联。

用 `Grep` 定位 + `Read` offset/limit 精确定位，不读完整文件。

### 步骤 3：执行代码审查

依照 `review-rules` 技能中定义的审查规则，对变更代码逐项审查：
- 识别代码类型（MCU 裸机 C / 嵌入式 Linux App C）。
- 按内存安全、指针与数组安全、中断与并发、硬件交互、资源管理、错误处理、代码规范共 7 个维度进行检查。
- 每个问题标注严重度：**严重** / **警告** / **建议**。

### 步骤 4：生成并存档审查报告（不论审查结果如何均执行）

依照 `review-rules` 技能的模板生成审查报告（包含审查时间、审查范围、整体概览、问题及修复建议、审查结论），然后调用 `review-archive` 技能存储到：

```
<当前工作目录>.review/YYYY-MM-DD-HH-MM-SS.md
```

## 输出格式

报告存档后，两种模式各自输出结果。

### Hook 模式输出

审查完成后，在回复的**最后一行之前**输出以下结构化标记，供调用脚本解析：

审查通过（无「严重」且无「警告」）：
```
REVIEW:PASS
```

审查不通过：
```
REVIEW:FAIL
严重: N 个 | 警告: M 个 | 建议: K 个
<审查报告中「问题及修复建议」部分的完整内容>
```

注意：Hook 模式下不弹窗、不调用 svn_commit。TortoiseSVN 会根据 REVIEW:PASS/FAIL 决定是否提交，FAIL 时 ERRORFILE 内容会自动显示给用户。

### 直接模式输出

**审查通过**（无「严重」且无「警告」级别问题）：
1. 向用户展示审查报告（简要版）。
2. 生成提交信息（中文，概括本次变更内容，格式：`<类型>: <简要描述>`，类型为 fix/feat/refactor/docs 之一）。
3. 调用 review-svn 技能的 `svn_commit` 执行提交，传入生成的提交信息。
4. 弹出提示框显示："✅ 提交成功！"。

**审查不通过**（存在「严重」或「警告」级别问题）：
1. 向用户展示审查报告（完整版）。
2. 弹出提示框显示："❌ 提交失败！发现 N 个严重问题、M 个警告。请根据审查报告修复后重试。"
3. 不执行 svn_commit。

## 提示框实现

在 Windows 环境下使用 PowerShell 弹窗：

审查通过：
```powershell
powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('审查通过，代码已成功提交！', '提交成功', 'OK', 'Information')"
```

审查不通过：
```powershell
powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('发现 N 个严重问题、M 个警告。请根据审查报告修复后重试。', '提交失败', 'OK', 'Error')"
```

无变更时：
```powershell
powershell -Command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('没有可提交的变更，请确认是否已保存文件。', '提示', 'OK', 'Warning')"
```

## 提交信息生成规则

| 变更类型 | 前缀 | 示例 |
|----------|------|------|
| 新增功能 | feat: | feat: 添加ADC采样模块 |
| 修复Bug | fix: | fix: 修复串口接收中断溢出问题 |
| 重构 | refactor: | refactor: 抽取按键扫描状态机 |
| 文档/注释 | docs: | docs: 补充GPIO驱动使用说明 |

提交信息需用中文描述，控制在 50 字以内。

## 技能协作关系

```
review-svn ──→ 获取变更状态、差异内容、执行提交
review-rules ──→ 提供审查规则、输出模板
review-archive ──→ 存储审查报告
```

你只做编排，不替代上述任何一个技能的职责。
