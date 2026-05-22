---
name: prd-check
description: 在 prd-create 或 prd-modify 终稿后、或用户调用 /prd-check 时，检查 PRD 三栏一致性/布局/系统壳，按 A B C 编号列出异常供用户确认，并按用户指定编号选择性自动修复。Use for prd-check, 三栏检查, 修复 B C D, check-consistency.
---

# PRD 三栏一致性检查（prd-check）

## 何时执行

| 时机 | 要求 |
|------|------|
| `prd-create` / `prd-modify` 终稿 | `validate` 通过后执行本 Skill |
| 用户 `/prd-check` | 完整流程 |

## 核心流程（必须遵守）

### 1. 检查并列出编号清单（默认不自动全量修复）

```bash
prdkit-html validate
prdkit-html check-consistency
```

将终端输出的 **异常清单** 原样呈现给用户，格式示例：

```text
异常清单（请确认要修复的编号）:
A. ❌ [SPEC_MISSING_PROTO_REF] 说明 #sec-3-1 … [可自动修复]
B. ⚠️ [POSSIBLE_FABRICATION] spec 区含可疑占位 … [可自动修复]
C. ❌ [SHELL_WRONG_SYSTEM] 应用壳应为「催收后台」… [需人工]
```

- 编号 **A、B、C…** 与 `.memory/prd_check_latest.json` 中 `issues[].letter` 一致。
- **禁止**在未经用户确认前执行 `check-consistency --fix` 全量修复（终稿闭环除外见下节）。

### 2. 等待用户确认

向用户说明：

- 回复要修的编号，例如：`B C D` 或 `B,C,D`
- 回复 `全部` / `all`：仅修复所有 **[可自动修复]** 项
- 标 **[需人工]** 的项：按 Skill 表格手改，不能指望 `--fix`

### 3. 按用户选择修复

用户回复 `B C D` 时：

```bash
prdkit-html check-consistency --fix-letters B,C,D
prdkit-html validate
```

Agent 也可读取 `.memory/prd_check_latest.json`，对 `letter ∈ {B,C,D}` 且 `auto_fixable: true` 的项执行上命令；`auto_fixable: false` 的项按「需人工」处理。

### 4. 复检

```bash
prdkit-html check-consistency
```

仍有异常则回到步骤 1；无异常则结束。

### 终稿闭环（create/modify）

1. `validate` → `check-consistency`（**列出清单**，有 error 则先处理或告知用户）
2. 若仅 warn 且用户未交互：可对 **可自动修** 项询问，或默认不修
3. 用户确认编号后 `--fix-letters` → `validate`

## 检查类别（非清单编号）

| 类别 | 内容 |
|------|------|
| 内容对齐 | `PROTO_*` / `SPEC_*` / `TOC_*` / `POSSIBLE_FABRICATION` |
| 布局 | `LAYOUT_*`（不可 `--fix`） |
| 系统壳 | `SHELL_*`（不可 `--fix`，须 `init --shell`） |

**后端/接口说明**可无原型：正文含 `后端逻辑`/`纯接口`/`状态变化` 等，或 `<p class="proto-exempt">`（见 [reference.md](reference.md)）。

## 命令

| 命令 | 作用 |
|------|------|
| `check-consistency` | 检查 + 输出 A/B/C 清单 + 写入 `prd_check_latest.json` |
| `check-consistency --fix-letters B,C,D` | 仅修指定编号（可自动修） |
| `check-consistency --fix` | 修全部可自动修（慎用，需用户同意） |
| `check-consistency --json` | JSON（含 `letter` 字段） |

## 需人工项（示例）

| 代码 | 动作 |
|------|------|
| `LAYOUT_*` / `SHELL_*` | `init` 恢复或换壳后重做标记区 |
| `PROTO_WITHOUT_SPEC_TOC` | 补 spec/toc 或删 Tab |
| 用户选中但 `auto_fixable: false` | `set-spec` / `set-toc` / `set-proto-page` 手改 |

## 禁止

- 未列清单就静默 `--fix` 全部
- 手改 `#prd-shell`
- 编造需求通过检查
