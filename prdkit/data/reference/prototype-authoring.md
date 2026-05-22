# PRD 中原型撰写规范（prototype-authoring）

与 `design-spec.md` **AGENT-0～AGENT-13** 及 `prd-create` Skill 配套。Agent 生成 HTML 原型前**必读**（勿读 APPENDIX 拼 DOM）。

---

## 跨系统 / 截图复刻（违反即交付失败）

1. **`prdkit-html init --shell` 全文档仅一个壳**，写入 `data-prdkit-shell`（勿手改）；须与用户截图/主流程系统一致。
2. **禁止**在 slot 内再画 `.app-layout` / `.app-sidebar` / `.app-header`（`validate` 会报错）—— 即禁止「业务壳里嵌一整页催收界面」。
3. **催收 → 业务** 等跨系统：优先 **两个 basename 各 init**；否则次要系统只写说明区 + 流程图，slot 仅主系统页面。
4. Tab 仅用于 **同一壳** 下的多屏，不能替代第二套壳。

## 原型铁律（违反即视为交付失败）

1. **系统壳仅在 `prdkit-html init` 注入一次**；业务只写入 `#prototype-slot` 标记区内（`<!-- prdkit:slot:start -->` … `<!-- prdkit:slot:end -->`）。
2. **`set-proto-slot` / `set-proto-page` 的片段不得包含** `<style>`、**`style=` 内联**、`<script>`、`<html>`、`<body>`、`.app-layout`、`.app-sidebar`、`.app-header` 等壳结构。
3. **全文档只允许一份原型交互脚本**：由 `init` 注入的 `proto-runtime.js`（`data-prdkit-proto-runtime`）；禁止在 slot 或说明区再写 `<script>`。
4. **多页面 = Tab**（`.proto-tabs` + `.proto-page[data-proto-page]`）；禁止把多个完整页面纵向堆叠或重复粘贴整包原型。
5. **画布固定 1440×900**（详见 design-spec **AGENT-11**）：勿在 slot 内做移动端响应式改版；小屏/折叠规则只写 PRD 说明区。
6. **每个功能说明节须在 spec 中注明原型 Tab**：如「见中原型 → Tab：**平账审核**」；目录项可加 `data-proto-tab="tab-id"` 与说明区联动。

---

## PRD 三栏骨架铁律（防 modify 把模板改坏）

1. **禁止**修改 `#prd-shell`、`.panel-toc` / `.panel-proto` / `.panel-spec`、`.resizer-toc` / `.resizer-spec`、`.prd-toolbar` 及文末三栏 `script`。
2. `data-panel="spec"` **必须**位于 `#prd-shell` 内部；若说明区被挤到页面下方，多为 shell 被多余 `</div>` 提前闭合。
3. `.resizer-spec` 必须为：`class="resizer resizer-spec" data-resize="spec"`。
4. **每次** `prdkit-html` 合并后执行 `prdkit-html validate`（含 shell + Tab 重复检测）；失败**不得**继续下一项。

---

## set-proto-page 协议（防 Tab 重复堆叠）

1. 工具会为每 Tab 写入 `<!-- prdkit:page:<tab>:start/end -->`；**禁止**在片段里手写这些标记。
2. 同一 `tab-id` 改内容：再次执行 `set-proto-page --tab <同一id>`（先剥离旧页再写入），**禁止**把 `page.html` 手贴进 HTML。
3. 片段 `<div>` / `</div>` 须平衡；禁止在片段中闭合 `proto-pages` 或 slot 父级。
4. `validate` 会检查：每个 `data-proto-page` / `data-tab` 在 slot 内仅出现 1 次。

---

## 推荐工作流（P0～P3）

| 阶段 | 动作 | 命令 |
|------|------|------|
| 首轮 | 创建 HTML + 壳 + 默认 Tab 骨架 | `prdkit-html init …` |
| 第一个需原型的功能 | 按 `reference/design-spec.md` **AGENT-5 / AGENT-6** 骨架手写 `.memory/.../page.html` | `set-proto-page --tab <id> --file …` |
| 后续功能 | **只**追加 Tab 页或改 spec；勿 `set-proto-slot` 整包覆盖 | `set-proto-page --tab <id> --file …` |
| 仅单屏 MVP | 可 `set-proto-slot` 一次（仍须过校验） | `set-proto-slot --file …` |
| 交付前 | 自检 | `prdkit-html validate` |

片段建议路径：`.memory/prd_fragments/<功能>/page.html`（纯 DOM，无 style/script）。

---

## 片段白名单与反例

**允许**：表格、表单、按钮、`.query-form`、`.filter-grid`、`.proto-modal`（结构）、`data-toggle-filter` / `data-open-modal` 等（见 design-spec AGENT-5/6）。

**禁止（反例）**：

```html
<!-- ❌ 内联样式 -->
<table style="width:100%">…</table>

<!-- ❌ 整页壳 + 脚本 -->
<style>.x{}</style>
<script>function boot(){}</script>
<div class="app-layout">…</div>

<!-- ❌ 重复 id -->
<input id="chk-all" />
…
<input id="chk-all" />
```

---

## Tab 与目录联动（P3）

- Tab 按钮：`<button type="button" class="proto-tab" data-tab="audit">平账审核</button>`
- 页面：`<div class="proto-page" data-proto-page="audit" hidden>…</div>`
- 目录：`<a href="#sec-3-2" data-proto-tab="audit">3.2 平账审核</a>`
- 说明区首段建议：`<p class="proto-ref">见中原型 → Tab：<strong>平账审核</strong></p>`

切换 API：`PRDKIT.switchProtoTab('audit')`（由 `proto-runtime.js` 提供）。

---

## 标准片段（P1）

| 资源键 | 用途 |
|--------|------|
| `reference/design-spec.md` | **AGENT-0～13**（列表 AGENT-5、配置 AGENT-5b、弹窗 AGENT-6） |
| `assets/fragments/strategy-config-slot.html` | 配置主从页参考片段（AGENT-5b） |
| `assets/tokens.css` | 设计 Token 变量（init 注入，勿复制进片段） |
| `assets/proto-base.css` | 列表页/表格/按钮/弹层（init 注入，勿复制进片段） |
| `assets/proto-runtime.js` | Tab、侧栏折叠、目录联动（init 注入） |

---

## 中长期：iframe 隔离（P4）

当单页内样式仍难稳定时，可将中原型改为 iframe 加载独立 `proto.html`（与 PRD 页样式完全隔离）。当前默认仍为 **内嵌 `.prd-embed`**；选用 iframe 须在 PRD 元信息中注明，并单独维护 `proto.html` + 壳文件，不在本规范默认路径内。

---

## 交付前自检

```bash
prdkit-html validate
```

须通过：slot 无 script/style、无 `style=` 内联、无重复 `id`、无重复 Tab、`#prd-shell` 结构完整、`resizer-spec` 属性正确、仅一份 `data-prdkit-proto-runtime`；**含列表页时**另过 design-spec **AGENT-7** 启发式（由 `validate` 自动执行）。
