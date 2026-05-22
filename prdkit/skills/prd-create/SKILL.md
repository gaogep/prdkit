---
name: prd-create
description: 基于 .memory 与套件内置规范，按「需求背景 → 功能架构 → 功能说明（逐功能）」顺序生成 HTML PRD；每完成一章（含原型与交互）发一条进度通知后自动续写下一章，无需用户回复「继续」。使用 prdkit-html 合并片段，禁止手写 Python 拼 HTML。在用户完成 prd-clarify、需产出 HTML PRD、或提及 prd_create、prd-create 时使用。
disable-model-invocation: true
---

# 套件约定（工作区无需 prdkit 目录）

| 用途 | 命令 |
|------|------|
| Hook | `prdkit-hook check create` / `prdkit-hook transit completed_create_or_modify` |
| 解析内置资源 | `prdkit path <资源键>` → **Read** |
| **HTML 合并（必用）** | `prdkit-html …`（**禁止**临时编写 Python 脚本拼模板） |

**资源键（生成前必读）**：

| 资源 | 键 |
|------|-----|
| 设计规范 | `reference/design-spec.md` |
| **原型铁律 / 撰写** | `reference/prototype-authoring.md`（**生成原型前必读**） |
| PRD 撰写规范 | `reference/prd-writing-spec.md` |
| PRD 三栏模板 | `assets/文档输出模板.html` |
| 系统壳 | `assets/催收后台-原型壳.html` / `业务后台-原型壳.html` / `质检后台-原型壳.html` |
| 原型绘制规范 | `reference/design-spec.md`（**AGENT-0～13**，止于此） |
| 原型 Token / 样式 | `assets/tokens.css` / `assets/proto-base.css`（init 注入，勿写入 slot） |
| Logo（内嵌） | `assets/logo.data-uri`（init 时写入 HTML，勿再复制 png） |

# 🛑 状态机防篡改最高禁令

1. **禁止**直接读写 `workflow_state.json`。
2. **唯一合法途径**：`prdkit-hook [check|transit] ...`

# 路径约定

- 输出目录与文件名由 **prd-init** 写入 `.memory/prd_output.json`（`output_dir`、`basename`）。
- 若缺失 `prd_output.json` 或用户明确要求改路径：**先询问**输出目录（默认 `prds/`）与 `basename`，更新配置后再继续。
- 目标 HTML 路径以 `prd_output.json` 的 `html_path` 为准（**禁止**覆盖套件内置 `assets/` 模板）。
- 进度追踪：`.memory/prd_index.md`（与 `prd-writing-spec.md` **§3** 一致）。

# Hook 门禁

```bash
prdkit-hook check create
```

Exit 1 → 原样输出并停止；Exit 0 → 继续。

# 角色与目标

基于 `.memory` 与设计规范，生成极简白话、左中右三栏、带高保真原型的单页 HTML PRD。按 **§3 章节目录顺序** 连续撰写：**写完一章 → 合并进 HTML → 更新 index → 发一条进度通知 → 立即写下一章**。

# 🛑 进度通知（无需用户说「继续」）

1. **每完成一章**（需求背景 / 功能架构 / 单个功能说明，且该章所需原型与交互已实现）→ 在回复中发**一条**进度通知，**然后在本轮继续**下一章。
2. **禁止**要求用户回复「继续」才往下写。
3. **禁止**在同一条通知里堆砌多章完成情况；每章一条短通知，可穿插在连续工作中。
4. 全部章节完成后，**另起一段**执行终稿闭环（Hook transit），可与最后一条功能通知同轮但须区分开。

**通知文案（照发）**：

| 完成范围 | 文案 |
|----------|------|
| 需求背景 | 已完成需求背景的撰写。 |
| 功能架构 | 已完成功能架构的撰写。 |
| 单个功能 | 功能XXX已完成撰写。 |

# 全局上下文（Hook 通过后）

1. Read `.memory/product_brief.md`、`.memory/prd_index.md`、`.memory/prd_output.json`、`.memory/architecture.md`（如有）
2. `prdkit path …` 后 Read 规范与模板；**涉及原型前必读** `reference/prototype-authoring.md`（含**原型铁律**）
3. 交付 HTML 基于 `文档输出模板.html`（三栏、Mermaid 放大等）

# 准备（仅首轮一次）

1. **Hook** 通过
2. 确认 `.memory/prd_output.json`；缺则向用户确认 `output_dir`、`basename`
3. **判断系统壳**（与截图/主流程一致，全文档仅一个）：
   - 用户给 **催收** 截图或主场景在催收 → `--shell 催收后台`
   - **业务后台** / **质检后台** 同理
   - 需求 **跨催收+业务**：见下节「跨系统」；**禁止**选业务壳却在 slot 画催收顶栏页
4. 若目标 HTML 不存在，执行（路径来自配置）：

```bash
prdkit-html init --output-dir <output_dir> --basename <basename> --shell <系统名>
```

# 🛑 HTML 修改铁律（create / modify 共用）

1. **只改标记区**：`prdkit:toc` / `prdkit:spec` / `prdkit:slot`（及工具写入的 `prdkit:page:<tab>`）；禁止改其它 DOM。
2. **禁止**对交付 HTML 全文 Search/Replace、禁止自写 Python/Node 合并脚本。
3. **每次** `prdkit-html` 合并后**必须**执行 `prdkit-html validate`；**失败即停**，禁止继续下一章。
4. 原型：同一 `--tab` 仅一页，改内容用**同 tab 再执行** `set-proto-page` 覆盖，禁止手贴重复片段。

# 🛑 PRD 页面骨架禁区（init 后禁止 Agent 修改）

下列结构 **不得增删改**（含多写 `</div>`、改属性、删 script）：

- `#prd-shell` 及子级顺序：`.panel-toc` → `.resizer-toc` → `.panel-proto` → `.resizer-spec` → `[data-panel="spec"]`
- `.prd-toolbar`、Mermaid 弹窗、文末三栏布局脚本（含 `getElementById("prd-shell")`）
- `.resizer-spec` 须为：`class="resizer resizer-spec" data-resize="spec"`（禁止 class 与 data-resize 粘连）

**禁止**重写 `<!-- prdkit:proto:start/end -->` 整块（除 `init` 外）。

# 🛑 HTML 写入：只用 prdkit-html

将每章内容先写入片段文件（建议 `.memory/prd_fragments/`），再调用 CLI 合并。**禁止**手写 Python 拼 HTML。

| 步骤 | 命令 |
|------|------|
| 更新左目录 | `prdkit-html set-toc --file <toc片段.html>` |
| 更新说明区整章 | `prdkit-html set-spec --section-id <sec-id> --file <spec片段.html>` |
| **追加/更新某一屏原型（推荐）** | `prdkit-html set-proto-page --tab <tab-id> --label <显示名> --file <page.html>` |
| 单屏或整 slot 骨架（慎用） | `prdkit-html set-proto-slot --file <slot.html>` |
| 交付前自检 | `prdkit-html validate` |
| 三栏一致性 | `prdkit-html check-consistency` / `--fix`（见 `prd-check` Skill） |
| 查看配置 | `prdkit-html show-config` |

片段须含正确 `id`（如 `sec-1`、`sec-3-2`）；UML 使用 `.mermaid-wrap` + `.mermaid` 结构。

# 🛑 跨系统 / 截图复刻（与 prd-modify 相同）

1. `init --shell` 全 PRD **只有一个** 壳；须与截图系统一致。
2. **跨系统流程**（如催收提交 → 业务审批）：拆 **两份 PRD** 各 `init` 一次，或 `init` 主系统、另一系统**仅说明区**不出 slot 高保真；**禁止**多系统揉进同一壳 Tab。
3. 多 Tab = 同系统多页面，≠ 多系统多壳。

# 🛑 原型铁律（违反即交付失败）

详见 `reference/prototype-authoring.md`，摘要：

1. 系统壳**仅** `prdkit-html init` 注入一次；业务只写 `#prototype-slot` 标记区。
2. 片段**禁止** `<style>`、**`style=` 内联**、`<script>`、`.app-layout` / 侧栏 / 顶栏壳。
3. 全页**仅一份** `proto-runtime.js`（init 注入）；禁止在 slot 再写脚本。
4. 多屏用 **Tab**（`set-proto-page`），禁止每功能整包覆盖 slot 或重复粘贴整页原型。
5. 有界面的功能：说明区写「见中原型 → Tab：**xxx**」；目录加 `data-proto-tab`。纯后端/接口/状态机无界面：写 `proto-exempt` 或关键词（见 `prd-check`），**可不**关联原型。
6. 终稿前执行 `prdkit-html validate` 须通过。

# 🛑 set-proto-page 协议

1. 片段内 `<div>` 与 `</div>` 数量须平衡，禁止闭合 `proto-pages` / `#prototype-slot` 父级。
2. 同一 `tab-id` 全文档**仅允许**一个 `data-proto-page`、一个 `data-tab` 按钮；改稿 = 同 tab 再跑 `set-proto-page`。
3. 合并后 `validate` 须通过（含 shell 与 Tab 重复检测）。

# 分步创建（连续执行，勿等待「继续」）

## 步骤 1：需求背景

1. 撰写需求背景 → 保存 `spec` 片段 → `prdkit-html set-spec --section-id sec-1 --file …`（按需 `set-toc`）
2. **`prdkit-html validate`**（失败则停止，禁止继续）
3. `prd_index.md` 需求背景项标 `- [x]`
3. 通知：`已完成需求背景的撰写。`
4. **立即进入步骤 2**（勿停等用户）

## 步骤 2：功能架构

1. 撰写功能架构 → `set-spec` / `set-toc` 合并
2. **`prdkit-html validate`**
3. index 标 `- [x]`
3. 通知：`已完成功能架构的撰写。`
4. **立即进入步骤 3**

## 步骤 3：功能说明（逐功能）

对每个仍为 `- [ ]` 的功能项（按 index 顺序）：

1. 撰写说明（含 `proto-ref` 指向 Tab）+ 必要 Mermaid
2. 首个需原型的功能：按 `design-spec.md` **AGENT-2（Tab）+ AGENT-5 / AGENT-5b（配置页）+ AGENT-6** 手写 `.memory/prd_fragments/<功能>/page.html`，再 `set-proto-page --tab …`（须 `validate` 通过）。**后续功能只追加新 Tab 或只改 spec**，禁止 `set-proto-slot` 整包覆盖
3. `set-spec --section-id <功能sec-id>`
4. **`prdkit-html validate`**（失败则停止，禁止处理下一功能）
5. index 该项 `- [x]`
6. 通知：`功能XXX已完成撰写。`
7. **立即处理下一功能**；全部完成后进入终稿闭环

# 终稿闭环

```bash
prdkit-html validate
```

**必须** 按 `prd-check` Skill：先 `check-consistency` 列出 **A/B/C 异常清单**；用户确认编号后再 `--fix-letters`（勿默认全量 `--fix`）。

```bash
prdkit-html check-consistency
# 用户确认后，例如修复 B、C：
prdkit-html check-consistency --fix-letters B,C
prdkit-html validate
prdkit-hook transit completed_create_or_modify
```

提示：PRD 已写入 `prd_output.json` 中的 `html_path`，可用 `/prd-modify` 或 `/prd-check` 迭代。

# 写入与版式约束

- 左目录与 `prd_index.md` 一致；锚点对应右侧 `id`
- Logo 已由 `init` 以 data URI 内嵌进原型壳，**禁止**再向 `output_dir` 复制 `logo.png`
- **禁止**修改套件内置 `assets/` 原文件

# 风格

极简白话；原型遵循 `design-spec.md` **AGENT-0～13** 与 `tokens.css` / `proto-base.css`。

# 原型 UI Skill 边界（必读）

- **禁止** `frontend-design` / `ui-ux-pro-max --design-system` 换字体配色；美感靠 **AGENT-5/5b 骨架 + validate + 业务文案**。
- **允许** `ui-ux-pro-max --domain ux|web` 仅作对照清单；改动只落在 `tokens.css` / `proto-base.css` / 片段 class，**禁止** slot 内 `<style>` 或改壳 DOM。
