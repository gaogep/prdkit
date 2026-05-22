---
name: prd-check
description: 在 prd-create 或 prd-modify 终稿后、或用户调用 /prd-check 时，检查 PRD HTML 的目录/说明/原型对齐、三栏布局顺序、系统壳是否匹配，并自动修复可安全项。Use after prd-create, prd-modify, or when the user asks prd-check, 三栏一致性, 布局混乱, 壳用错.
---

# PRD 三栏一致性检查（prd-check）

## 何时执行（强制）

| 时机 | 要求 |
|------|------|
| `prd-create` 终稿闭环 | `validate` 通过后 **必须** 执行本 Skill |
| `prd-modify` 终稿闭环 | 同上 |
| 用户 `/prd-check` | 单独执行全流程 |

**顺序**：`prdkit-html validate`（DOM/原型结构）→ `prdkit-html check-consistency --fix`（三栏+布局+壳）→ 人工处理剩余项 → 再 `validate`。

## 检查项

### A. 三栏内容对齐

| # | 检查 | 代码 |
|---|------|------|
| 1 | 原型 Tab 在说明/目录无对应 | `PROTO_WITHOUT_SPEC_TOC` |
| 2 | 目录悬空 | `TOC_ORPHAN_SEC` / `TOC_ORPHAN_TAB` |
| 3 | 说明悬空 / proto-ref 无效 | `SPEC_*` |
| 4 | 编造占位 | `POSSIBLE_FABRICATION` |
| + | `prd_index` 未进 HTML | `INDEX_NOT_IN_HTML` |

### B. 页面布局（三栏位置）

| 检查 | 代码 |
|------|------|
| 缺少 toc/proto/spec 面板 | `LAYOUT_PANEL_MISSING` |
| 顺序不是 目录→原型→说明 | `LAYOUT_PANEL_ORDER` |
| 目录不在最左 | `LAYOUT_TOC_POSITION` |
| 原型不在中间 | `LAYOUT_PROTO_POSITION` |
| 说明不在最右 | `LAYOUT_SPEC_POSITION` |
| 说明区掉到 `#prd-shell` 外 | `LAYOUT_SPEC_OUTSIDE_SHELL` |
| `prdkit:toc/spec/slot` 标记不在对应面板内 | `LAYOUT_TOC/PROTO/SPEC_WRONG_PANEL` |

**布局类不可 `--fix` 自动修**：须从备份恢复，或 `init` 新 HTML 后仅重做 toc/spec/slot 标记区（禁止手改 `#prd-shell`）。

### C. 原型壳（系统匹配）

| 检查 | 代码 |
|------|------|
| `data-prdkit-shell` 与 DOM 指纹不一致 | `SHELL_DOM_MISMATCH` |
| `.memory/prd_output.json` 的 `shell` 与实测壳不一致 | `SHELL_WRONG_SYSTEM` |
| 目录/说明多次写「催收」但壳是「业务」等 | `SHELL_TEXT_MISMATCH` |
| 业务壳 slot 内手绘催收顶栏 / 催收壳 slot 内嵌侧栏 | `SHELL_SLOT_WRONG_CHROME` |

**壳匹配规则**（与 `design-spec` AGENT-3 一致）：

| 需求/截图系统 | `init --shell` |
|---------------|----------------|
| 催收 | `催收后台`（顶栏横菜单，无 `#001529` 侧栏） |
| 业务 | `业务后台`（深侧栏 `#001529`） |
| 质检 | `质检后台`（白侧栏蓝字） |

**壳类不可 `--fix`**：对目标 `basename` 重新 `prdkit-html init --shell <正确系统>`，再 `set-toc` / `set-spec` / `set-proto-page` 合并片段。

细则见 [reference.md](reference.md)。

## 命令

```bash
prdkit-html validate
prdkit-html check-consistency --fix
prdkit-html validate
```

```bash
prdkit-html check-consistency          # 只检查
prdkit-html check-consistency --json   # JSON
```

读取上下文：`.memory/prd_output.json`（`shell`）、`prd_index.md`、`product_brief.md`（推断期望壳）。

## 无法自动修复时（Agent）

| 代码 | 动作 |
|------|------|
| `LAYOUT_*` / `SHELL_*` | 禁止手改 shell；`init` 恢复或新建后重做标记区 |
| `SHELL_WRONG_SYSTEM` | 按上表换 `--shell` 后重做原型 |
| `PROTO_WITHOUT_SPEC_TOC` | 补 spec/toc 或删 Tab |
| `POSSIBLE_FABRICATION` | `[TODO]` 或真实文案 |

每步合并后 **`validate`**。

## `--fix` 自动范围

- proto-ref、`data-proto-tab`、删悬空目录/错误 proto-ref、模板占位改 TODO

**不会**自动：调整三栏顺序、更换系统壳。

## 禁止

- 手改 `#prd-shell`、三栏脚本
- 为通过检查编造需求
- 跳过 `validate`
