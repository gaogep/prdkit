---
name: prd-modify
description: 在 PRD 已交付后解析 /prd-modify：宽泛意图双轨道，高精度自动直接修改；轨道 B 按章/功能修改后用 prdkit-html 合并，修改日志仅写 .memory/modify_logs，每章一条通知后自动续改下一项，无需用户说「继续」。在用户迭代 HTML PRD、或提及 prd_modify、prd-modify 时使用。
disable-model-invocation: true
---

# 套件约定（工作区无需 prdkit 目录）

| 用途 | 命令 |
|------|------|
| Hook | `prdkit-hook check modify` / `prdkit-hook transit <action>` |
| 修改日志（仅 .memory） | `prdkit-create-md .memory/modify_logs/…`（**禁止**写入 HTML 内「PRD 修改记录」表） |
| 设计规范 | `reference/design-spec.md`（**AGENT-0～13**） |
| 原型 / 骨架规范 | `reference/prototype-authoring.md`（**修改 HTML 前必读**） |
| 原型绘制规范 | `reference/design-spec.md`（**AGENT-0～13**） |
| 原型 Token / 样式 | `assets/tokens.css` / `assets/proto-base.css`（init 注入，勿写入 slot） |
| **HTML 合并** | `prdkit-html set-spec` / `set-proto-page` / `set-toc` / `validate` / `check-consistency`（**禁止**手写 Python 拼 HTML；**禁止** `set-proto-slot` 除非重建 slot 骨架） |
| 修改日志 | `prdkit-create-md .memory/modify_logs/YYYY-MM-DD_修改概要.md` |

路径相对项目根；目标 HTML 见 `.memory/prd_output.json` 的 `html_path`。

# 🛑 状态机防篡改最高禁令

禁止直接读写 `workflow_state.json`；仅 `prdkit-hook [check|transit] ...`。

# 🛑 HTML 修改铁律（modify 最高优先级）

1. **只改标记区**：`prdkit:toc` / `prdkit:spec` / `prdkit:slot` / `prdkit:page:<tab>`；**禁止**手改 `#prd-shell`、`.panel-*`、`.resizer-*`、三栏布局 `<script>`。
2. **禁止**对交付 HTML 全文替换、禁止自写合并脚本、禁止「修布局」式删补 `</div>`。
3. **每次** `prdkit-html` 命令后 **必须** `prdkit-html validate`；**Exit 非 0 则立即停止**，禁止继续下一项或批量合并。
4. 改原型：**只**用 `set-proto-page --tab <id>`；同一 tab 多次执行 = **覆盖**；禁止把 page 片段手贴进 HTML。
5. **禁止**在同一轮修改中先 `set-proto-slot` 再 `set-proto-page`（易清空 Tab 或叠层）。

# 🛑 PRD 页面骨架禁区

- `#prd-shell` 内须包含 `[data-panel="spec"]`（说明区不得在 shell 外）
- `.resizer-spec` 须含 `data-resize="spec"`（属性勿与 class 粘连）
- 文末须保留 `getElementById("prd-shell")` 布局脚本

骨架已坏（说明区掉到页面下方、`panelSpec` 报错）时：**禁止**手修 shell → 向用户说明需从备份恢复，或 `init` 新文件后仅重做 toc/spec/slot 标记区。

# 🛑 进度通知（轨道 B，无需「继续」）

1. 每完成**一章/一个功能**的修改并 `prdkit-html` 落盘且 **validate 通过** → **一条**通知 → **立即处理下一项**。
2. **禁止**要求用户回复「继续」。
3. **禁止**一条消息堆砌多条「已完成…修改」。

| 范围 | 通知 |
|------|------|
| 需求背景 | 已完成需求背景的修改。 |
| 功能架构 | 已完成功能架构的修改。 |
| 单个功能 | 功能XXX已完成修改。 |
| 其他 | 已完成【章节名】的修改。 |

# 角色与目标

轨道 B：**改一项 → prdkit-html 合并 → validate（必过）→ `.memory/modify_logs` 记一笔 → 通知 → 继续下一项**。

# 工作流

## 1. 合规检查

`prdkit-hook check modify` → 拦截则停止。

## 2. 意图解析

- **宽泛** → 双轨道 A/B，等待选择
- **高精度局部** → 静默 `prdkit-hook transit direct_modify`，说明已切轨道 B

## 3. 轨道切换

- **A**：`re_clarify` → `/prd-clarify` → 结束（不改 HTML）
- **B**：`direct_modify` → 步骤 4

## 4. 确定修改范围

Read `.memory/prd_index.md`、`prd_output.json`、目标 HTML、`reference/prototype-authoring.md`。列出待改项；多项时按 **需求背景 → 功能架构 → 功能说明** 排队。

若用户诉求为「原型乱 / 三栏坏 / 说明区掉下去」→ 走 **§修复乱文档**。

## 5. 分章修改（连续，每项）

1. 片段写入 `.memory/prd_fragments/` → `set-spec` / **`set-proto-page`（优先，同 tab 覆盖）** / `set-toc`
2. **`prdkit-html validate`（必须 exit 0，否则停止并报告，禁止继续）**
3. **禁止**在 HTML `spec` 区追加「PRD 修改记录」表；仅 `prdkit-create-md` 写入 `.memory/modify_logs/YYYY-MM-DD_*.md`
4. 发一条通知
5. **立即**处理下一项

## 6. 终稿闭环（单独说明段）

```bash
prdkit-html validate
```

**必须** 按 `prd-check` Skill：先 `check-consistency` 输出 **A/B/C 清单** 供确认；用户回复编号后 `--fix-letters`，再 `validate`。

```bash
prdkit-html check-consistency
prdkit-html check-consistency --fix-letters B,C,D
prdkit-html validate
prdkit-hook transit completed_create_or_modify
```

+ `modify_logs` 摘要（含一致性检查结果，**禁止** HTML 修改记录表）。

# §修复乱文档（原型重复 / shell 断裂）

**禁止**在 HTML 里大块删除「清重复」。

1. 若 `validate` 报 shell 错误：勿手改 → 建议备份后 `prdkit-html init` 新文件，或恢复备份，再只做标记区合并。
2. 若仅 slot 乱（重复 `data-proto-page`）：保留 slot 内**一份** `proto-root` + `proto-tabs` + `proto-pages`。
3. 按功能逐个：按 `design-spec.md` 修改 `.memory/.../page.html`，禁止 `style=` → `set-proto-page --tab <id> --file …` → **每步 validate**。
4. 全部通过后改 spec/toc（如需）；变更摘要只写 `modify_logs`。

# 风格

极简白话；原型遵循 `design-spec.md` **AGENT-0～13** 与 `tokens.css` / `proto-base.css`。

# 🛑 跨系统 / 截图复刻（禁止混壳）

1. 全 PRD 仅 **`init` 注入一个壳**（见 `prd_output.json` / `product_brief` 主系统）；**禁止**在业务壳 slot 内手绘另一系统的 `.app-layout` / 侧栏 / 顶栏（`validate` 会拦）。
2. 用户提供 **催收后台截图** → `init --shell 催收后台`；**质检截图** → `质检后台`；与截图系统不一致即错壳。
3. 流程跨 **催收 → 业务**（两系统）时 **禁止**把两系统原型揉进同一壳：
   - **推荐**：拆两份 PRD（两个 `basename` + 各 `init` 一次），说明区互相链接；
   - **或**：`init` 选主流程所在系统，另一系统**仅说明区文字 + 流程图**，不出该系统的 slot 高保真；
   - **禁止**「业务后台 Tab 里嵌一整页催收顶栏菜单」式假壳。
4. 多 Tab 只解决 **同系统多页面**，不解决 **多系统多壳**。

# 原型 UI Skill 边界（必读）

- **禁止** `frontend-design` / `ui-ux-pro-max --design-system` 换字体、配色、营销渐变（与 `design-spec` AGENT-0 冲突）。
- **美感来源**：严格执行 `design-spec` AGENT-5/5b 骨架 + `validate` + 业务向假数据；**不得**用外部 Skill 改 DOM 结构或壳。
- **允许**（仅自查对照）：`ui-ux-pro-max --domain ux|web` 核对 cursor、对比度、label、动效时长；发现问题只改 `tokens.css` / `proto-base.css` / 片段 class，**禁止**在 slot 加 `<style>`。

`prdkit-html validate` 执行 **design-spec AGENT-7**（#1～#11，含 a11y：label/for、focus-visible、对齐结构）。

# Hook 约定

Exit 1 禁止继续。
