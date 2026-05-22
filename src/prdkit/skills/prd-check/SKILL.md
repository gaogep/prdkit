---
name: prd-check
description: 在 prd-create 或 prd-modify 终稿后、或用户调用 /prd-check 时，检查 PRD HTML 的目录、说明、原型三栏是否互相矛盾（孤儿 Tab、悬空目录、缺 proto-ref、编造占位），并自动修复可安全项。Use after prd-create, prd-modify, or when the user asks to check PRD consistency, 三栏一致性, 目录原型说明对齐.
---

# PRD 三栏一致性检查（prd-check）

## 何时执行（强制）

| 时机 | 要求 |
|------|------|
| `prd-create` 终稿闭环 | `validate` 通过后 **必须** 执行本 Skill |
| `prd-modify` 终稿闭环 | 同上 |
| 用户 `/prd-check` | 单独执行全流程 |

**顺序**：`prdkit-html validate`（结构）→ `prdkit-html check-consistency --fix`（三栏）→ 人工处理剩余项 → 再 `validate`。

## 检查项（与用户四类问题一一对应）

| # | 检查 | 代码 |
|---|------|------|
| 1 | 原型 Tab 在说明无 `proto-ref`、目录无 `data-proto-tab` | `PROTO_WITHOUT_SPEC_TOC` |
| 2 | 目录 `href` 无对应说明锚点；`data-proto-tab` 无对应原型 | `TOC_ORPHAN_SEC` / `TOC_ORPHAN_TAB` |
| 3 | 功能说明无目录链；`proto-ref` 指向不存在的 Tab | `SPEC_WITHOUT_TOC` / `SPEC_MISSING_PROTO_REF` / `SPEC_ORPHAN_PROTO_REF` |
| 4 | 模板占位或可疑编造（测试1、aaa、示例功能点等） | `POSSIBLE_FABRICATION` |
| + | `prd_index.md` 功能项未出现在 HTML | `INDEX_NOT_IN_HTML` |

细则见 [reference.md](reference.md)。

## 命令（禁止手写 Python 拼 HTML）

```bash
# 只检查（有问题则 exit 1）
prdkit-html check-consistency

# 检查 + 自动修复可安全项并写回 HTML
prdkit-html check-consistency --fix

# JSON（便于记录到 modify_logs）
prdkit-html check-consistency --fix --json
```

可选：`--html` `--index .memory/prd_index.md`

## 工作流

### 1. 读取上下文

- `.memory/prd_output.json` → `html_path`
- `.memory/prd_index.md`
- 目标 HTML（toc / spec / slot 标记区）

### 2. 运行检查与自动修复

```bash
prdkit-html validate
prdkit-html check-consistency --fix
prdkit-html validate
```

### 3. 处理无法自动修复的项

| 代码 | Agent 动作 |
|------|------------|
| `PROTO_WITHOUT_SPEC_TOC` | 补 `set-spec`（`proto-ref`）+ `set-toc`（`data-proto-tab`），或删多余 Tab |
| `SPEC_MISSING_PROTO_REF`（未自动修） | 在对应 `#sec-*` 下写 `见中原型 → Tab：**<label>**` |
| `INDEX_NOT_IN_HTML` | 补目录/说明或更新 `prd_index.md` |
| `POSSIBLE_FABRICATION` | 改为 `[TODO: …]` 或真实业务文案；**禁止**保留编造 |

每改一处：`set-spec` / `set-toc` / `set-proto-page` → **`validate`**。

### 4. 终稿

- 再跑 `check-consistency`（无 `--fix`）直至 **0 error**（warn 可保留但须在回复中列出）
- `prd-modify`：摘要写入 `.memory/modify_logs/`（**禁止** HTML 修改记录表）
- 通知示例：`PRD 一致性检查完成，已自动修复 N 项；剩余 M 项 warn 待确认。`

## 自动修复范围（`--fix` 会做）

- 在说明章节标题下插入缺失的 `<p class="proto-ref">…</p>`
- 为目录链接补上 `data-proto-tab`
- 删除指向不存在 `#sec-*` 的目录项
- 删除说明区指向不存在 Tab 的 `proto-ref`
- 将「示例功能点/示例小节」改为 `[TODO: 填写真实功能名称]`

**不会**自动：新增整屏原型、编造业务规则、删除有效 Tab（需 Agent 决策）。

## 禁止

- 手改 `#prd-shell`、三栏布局脚本
- 为通过检查而编造需求或界面
- 跳过 `validate` 直接改 HTML 全文
