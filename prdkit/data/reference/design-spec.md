# design-spec（Agent 优先版）

Vue 2 + Element UI 2.x 管理后台。**生成 HTML 原型**：按顺序读完 **AGENT-0 → AGENT-13** 后 **停止**；**禁止**为拼 DOM 阅读文末 APPENDIX。  
配套：`prototype-authoring.md`（流程铁律）、`tokens.css` + `proto-base.css`（init 注入）。

---

## AGENT-0｜模式与审美

- **方向**：工业 utilitarian B 端 = Element 色 + Ant Design Pro 疏朗列表；**不靠**换字体/渐变/不对称版式。
- **禁止** Cursor **`frontend-design`** skill（创意字体/渐变/不对称/纹理）；**禁止** `ui-ux-pro-max` 另起配色/字体。
- **允许**：`cursor:pointer`、150～250ms 过渡、`:focus-visible`（按钮/Tab/pill/输入框）、`prefers-reduced-motion`（见 `tokens.css`）；正文 `#606266` on `#fff` 满足对比度；图标用 SVG，**禁止 emoji**。
- **ui-ux-pro-max**：仅用 `--domain ux|web` 查 checklist；**禁止** `--design-system` 换配色字体。
- **观感底线**：`validate` 通过 + **AGENT-5/5b** 骨架齐全 + 业务向假数据即视为达标；**禁止**为「更好看」再挂 `frontend-design` 或改壳/字体；不达标时补 `proto-list-page` 链或 `proto-base.css`，勿换肤。
- **样式来源**：仅 `tokens.css` + `proto-base.css`；**禁止** `style=` / `<style>` / `<script>` / 自造 class / 自造 hex。
- **假数据**：用业务向文案（账单号、状态枚举），禁止「测试1」「aaa」。

---

## AGENT-1｜失败即停 TOP3

| # | 违反则原型失败 |
|---|----------------|
| 1 | 出现 `style=`、裸 `<table>`（无 `proto-table`）、`<button>` 无 `btn` 类 |
| 2 | 列表页：`proto-list-page` 完整链；配置页：根节点 `proto-config-page`（见 **AGENT-5b**） |
| 3 | 未跑 `prdkit-html validate`（含 AGENT-7 **#1～#11**） |

---

## AGENT-2｜流程铁律

完整流程见 `prototype-authoring.md`。摘要：

| 规则 | 要求 |
|------|------|
| 壳 | 仅 `prdkit-html init` 一次；业务只写 `prdkit:slot` |
| 多屏 | `set-proto-page` + Tab；禁止整页重复粘贴 |
| 脚本 | 全页仅一份 `proto-runtime.js`（init 注入） |
| 交付 | `prdkit-html validate` 通过 |
| Tab `set-proto-page` | **不要**手写 `proto-page` / `prdkit:page:*`（工具自动包裹） |
| Tab 单屏 `set-proto-slot` | 根节点 `proto-list-page`（或 AGENT-5 整块） |
| Tab 多屏 | 每 Tab 一份 `page.html`；说明区写 `见中原型 → Tab：**<tab-id>**`；目录 `data-proto-tab` |

---

## AGENT-3｜三系统壳（禁止混用）

| 系统 | 壳 | 布局 |
|------|-----|------|
| 催收后台 | `催收后台-原型壳.html` | 顶栏深灰横菜单，**无侧栏** |
| 业务后台 | `业务后台-原型壳.html` | 深侧栏 `#001529` + 白顶栏 |
| 质检后台 | `质检后台-原型壳.html` | **白侧栏蓝字** + 白顶栏 |

Logo：`init` 内嵌 `logo.data-uri`（勿附 png）。业务 **仅**写在 `#prototype-slot`（`prdkit:slot` 标记内）。

**跨系统（单 PRD 单壳）**

| 壳 | 识别 |
|----|------|
| 催收后台 | 顶栏深灰横菜单，**无** `#001529` 侧栏 |
| 业务后台 | 深侧栏 `#001529` + 白顶栏 |
| 质检后台 | **白侧栏蓝字** + 白顶栏 |

- `init --shell` 与上表一致；**禁止**业务壳 slot 内手绘催收顶栏/另一套侧栏（见 `prototype-authoring.md`）。
- 流程跨两系统：拆两份 PRD 或次要系统仅 APPENDIX/说明区，**禁止**双壳揉进同一 `proto-pages`。

---

## AGENT-4｜列表页硬约束

| 项 | 值 |
|----|-----|
| 底 | `#f0f2f5`；筛选卡 + 表格卡 **分离**，间距 16px |
| 栅格 | `.filter-grid`：`repeat(4, minmax(0,1fr))`；每行 4 项；控件 `width:100%` |
| 标签 | **上标签**；禁止左标签右输入 |
| 间距 | 标签-控件 8px；列 24px；行 20px；全页 `--page-pad-x: 24px` 对齐 |
| 按钮 | `.filter-bottom-bar` > `.filter-actions`；**默认靠右**；靠左：底栏再加 class `is-actions-start` |
| 收起 | **>12** 项：第 13 项起 `filter-item--extra`；`query-form` 默认 `is-filter-expanded`；底栏 `filter-collapse-wrap` + `data-toggle-filter`（`proto-runtime` 切换）。**≤12** 项：省略 `filter-collapse-wrap` |
| 表格 | `th/td` padding **16px**；字号 **14px**；列多时 `.proto-table-scroll-body` 加 `proto-table-scroll-wide` |
| 行操作 | ≤3 个 `btn-link`；更多用 `.proto-more`；工具栏 **仅 1 个** `btn-primary` |

---

## AGENT-5｜列表页 DOM 骨架（复制改文案，禁止改 class 层级）

**有数据行时删除** `proto-empty` 那一行；无数据时只保留 `proto-empty` 行、删示例数据行。

```html
<div class="proto-list-page">
  <div class="proto-crumb"><span>一级</span><span class="sep">/</span><span class="cur">当前页</span></div>
  <section class="query-form is-filter-expanded" aria-label="查询筛选">
    <div class="filter-grid">
      <div class="filter-item">
        <label class="filter-label" for="filter-fld-1">字段</label>
        <input type="text" id="filter-fld-1" class="filter-control" placeholder="请输入" />
      </div>
      <!-- >12 项：从第 13 项起 class 加 filter-item--extra -->
    </div>
    <div class="filter-bottom-bar">
      <!-- ≤12 项：删除整块 filter-collapse-wrap -->
      <div class="filter-collapse-wrap">
        <button type="button" class="btn btn-link" data-toggle-filter>收起</button>
      </div>
      <div class="filter-actions">
        <button type="button" class="btn btn-default">重置</button>
        <button type="button" class="btn btn-primary">查询</button>
      </div>
    </div>
  </section>
  <section class="proto-list-card" aria-label="数据列表">
    <div class="table-toolbar">
      <button type="button" class="btn btn-primary">导出</button>
    </div>
    <div class="proto-table-scroll-body">
      <table class="proto-table">
        <thead><tr><th>列</th><th class="col-actions">操作</th></tr></thead>
        <tbody>
          <tr>
            <td><span class="proto-tag proto-tag-g">已结清</span></td>
            <td><div class="proto-op"><button type="button" class="btn btn-link">查看</button></div></td>
          </tr>
          <!-- 无数据时改用下一行，并删除上方数据行 -->
          <tr><td colspan="99"><div class="proto-empty">暂无数据</div></td></tr>
        </tbody>
      </table>
    </div>
    <div class="proto-pager">
      <span class="proto-pager-total">共 1 条</span>
      <button type="button" class="btn btn-default" disabled>上一页</button>
      <button type="button" class="btn btn-default" disabled>下一页</button>
    </div>
  </section>
</div>
```

**控件变种（筛选项/表单元格内）**

```html
<label class="filter-label" for="filter-status">状态</label>
<select id="filter-status" class="filter-control"><option>全部</option><option>待审核</option></select>

<label class="filter-label" for="filter-remark">备注</label>
<textarea id="filter-remark" class="filter-control filter-textarea" rows="3" placeholder="请输入"></textarea>
```

组合筛选项：`.filter-compound` > `select.filter-control--sm` + `input.filter-control`。

**弹窗/抽屉挂载**：与 `proto-list-page` **同级**，写在同一 `page.html` 片段**末尾**（仍在 slot 内，勿塞进 `table` / `proto-list-card`）。

**加载态（可选，演示异步查询）**：表格区 `aria-busy="true"` 时，用 2～3 行骨架代替空白（见 AGENT-10）；有数据后删除骨架行。

```html
<!-- 加载中示例：tbody 内临时骨架，数据返回后删除 -->
<tr class="proto-skeleton-row"><td colspan="99"><span class="proto-skeleton-bar"></span></td></tr>
```

### AGENT-5b｜配置主从页 DOM（金融配置 / 策略列表等）

根节点 **`proto-config-page`**（**不是** `proto-list-page`）。类名见 AGENT-8 `CONFIG` 行。参考实现：`assets/fragments/strategy-config-slot.html`。

```html
<div class="proto-config-page">
  <div class="proto-config-channel">
    <label class="filter-label" for="cfg-channel">渠道</label>
    <select id="cfg-channel" class="filter-control filter-control--channel">
      <option selected>ANDROID</option>
    </select>
  </div>
  <section class="proto-list-card proto-config-shell" aria-label="配置主区">
    <div class="table-toolbar proto-config-head">
      <h2 class="proto-config-title">策略列表</h2>
      <div class="proto-config-head-actions">
        <button type="button" class="btn btn-default">次要</button>
        <button type="button" class="btn btn-primary">主操作</button>
      </div>
    </div>
    <div class="proto-config-split">
      <aside class="proto-strategy-rail" aria-label="版本列表">
        <div class="proto-strategy-search">
          <input type="search" class="filter-control" placeholder="搜索" aria-label="搜索" />
        </div>
        <ul class="proto-strategy-list">
          <li class="proto-strategy-item is-active">
            <div class="proto-strategy-item-body">
              <div class="proto-strategy-name">策略名称</div>
              <div class="proto-strategy-meta">2025-09-16 15:00:00</div>
            </div>
            <span class="proto-tag proto-tag-b">已全量</span>
          </li>
        </ul>
      </aside>
      <div class="proto-config-detail">
        <div class="proto-seg-tabs" role="tablist">
          <button type="button" class="proto-seg-tab is-active">额度策略</button>
          <button type="button" class="proto-seg-tab">费率策略</button>
        </div>
        <div class="proto-config-subbar">
          <div class="proto-pill-tabs" role="tablist">
            <button type="button" class="proto-pill is-active">全部</button>
            <button type="button" class="proto-pill">优质</button>
          </div>
          <div class="proto-config-subsearch">
            <input type="search" class="filter-control" placeholder="搜索" aria-label="搜索明细" />
          </div>
        </div>
        <div class="proto-policy-grid">
          <article class="proto-policy-card">
            <header class="proto-policy-card-hd">策略卡 1</header>
            <div class="proto-table-scroll-body">
              <table class="proto-table proto-table-compact">
                <thead><tr><th>类型</th><th class="col-num">限额</th></tr></thead>
                <tbody><tr><td>新客首贷</td><td class="col-num">600,000</td></tr></tbody>
              </table>
            </div>
            <footer class="proto-policy-card-ft">
              <span class="proto-tag proto-tag-w">普通</span>
              <span class="proto-policy-ref">引用机构: 3</span>
            </footer>
          </article>
        </div>
      </div>
    </div>
  </section>
</div>
```

顶栏渠道区无 `filter-item` 时：可用 `aria-label` 或 `label[for]` + `id`（与 AGENT-7#11 精神一致）。

---

## AGENT-6｜弹窗与抽屉 DOM

`data-modal` / `data-drawer`：遮罩与本体成对；默认 `hidden`；`data-open-modal` / `data-close-modal`（抽屉同理 `data-open-drawer` / `data-close-drawer`）。

### 弹窗

```html
<div class="proto-modal-backdrop" data-modal="x" hidden aria-hidden="true"></div>
<div class="proto-modal" data-modal="x" role="dialog" aria-modal="true" hidden>
  <div class="proto-modal-hd">
    <div>
      <h3 class="proto-modal-title" id="modal-x-title">标题</h3>
      <p class="proto-modal-desc">说明（可选）</p>
    </div>
    <button type="button" class="proto-modal-close" data-close-modal="x" aria-label="关闭">×</button>
  </div>
  <div class="proto-modal-bd">
    <div class="proto-field-group">
      <div class="proto-field-label">字段 <span class="proto-req">*</span></div>
      <input type="text" class="filter-control" placeholder="请输入" />
    </div>
  </div>
  <div class="proto-modal-ft">
    <button type="button" class="btn btn-default" data-close-modal="x">取消</button>
    <button type="button" class="btn btn-primary">确定</button>
  </div>
</div>
```

### 抽屉（画布内 `absolute`，勿 `fixed` 整页）

```html
<div class="proto-drawer-backdrop" data-drawer="d" hidden aria-hidden="true"></div>
<div class="proto-drawer" data-drawer="d" hidden>
  <div class="proto-drawer-hd">
    <div>
      <h3 class="proto-drawer-title">标题</h3>
      <p class="proto-drawer-desc">说明（可选）</p>
    </div>
    <button type="button" class="proto-drawer-close" data-close-drawer="d" aria-label="关闭">×</button>
  </div>
  <div class="proto-drawer-main">
    <p>详情内容</p>
  </div>
  <div class="proto-drawer-footer">
    <button type="button" class="btn btn-default" data-close-drawer="d">关闭</button>
  </div>
</div>
```

宽抽屉：抽屉根节点再加 `proto-drawer-wide`。打开示例：`<button type="button" class="btn btn-link" data-open-drawer="d">查看</button>`。

---

## AGENT-7｜validate 自检

**说明**：`prdkit-html validate` 自动检查 **#1～#11** 及 AGENT-1 结构项。#1/#2 为**结构启发式**（保证筛选卡与表格卡同级、同 `--page-pad-x`），非浏览器像素测量。

| # | 通过标准 | validate |
|---|----------|----------|
| 1 | 筛选区与表格区**同级**（`query-form` 与 `proto-list-card` 同在 `proto-list-page` 下，筛选不嵌进表格卡） | 是 |
| 2 | 筛选栅格在 `query-form` 内；表格在 `proto-list-card` 内（左右内边距由 CSS 统一） | 是 |
| 3 | 筛选 4 列 `1fr`，无固定像素总宽窄于表 | 是 |
| 4 | 全部上标签 | 是 |
| 5 | 重置/查询在 `.filter-bottom-bar` 右侧 | 是 |
| 6 | 筛选/表头/表体/分页同一 `--page-pad-x` | 是 |
| 7 | 表格行高 ≥16px；须 `.proto-table` | 是 |
| 8 | 可点击：`button` 含 `btn`；`proto-tab` 例外；`data-open-*` / `data-close-*` 仅 `button.btn` | 是 |
| 9 | 有 `filter-item--extra` 时必有 `data-toggle-filter` | 是 |
| 10 | 表格行内/工具栏操作须 `button.btn-link` 等，**禁止** `<a href>` 冒充按钮 | 是 |
| 11 | `.filter-item` 内 `label.filter-label` 须 `for` 关联控件的 `id` | 是 |

收起交互由 `proto-runtime.js` 切换 `query-form.is-filter-expanded` 并改按钮文案「收起/展开」。

---

## AGENT-8｜类名注册表（禁止自造）

```
TAB: proto-tabs, proto-tab, proto-pages, proto-page
LIST_ROOT: proto-list-page, proto-crumb, sep, cur
FILTER: query-form, is-filter-expanded, filter-grid, filter-item, filter-item--extra, filter-label, filter-control, filter-textarea, filter-compound, filter-control--sm, filter-bottom-bar, is-actions-start, filter-actions, filter-collapse-wrap, data-toggle-filter
TABLE: proto-list-card, table-toolbar, proto-table-scroll-body, proto-table-scroll-wide, proto-table, col-actions, proto-op, proto-more, proto-pager, proto-pager-total, proto-empty, proto-skeleton-row, proto-skeleton-bar
BTN: btn, btn-primary, btn-default, btn-link
TAG: proto-tag + proto-tag-w|g|r|b（警告/成功/危险/信息）
MODAL: proto-modal-backdrop, proto-modal, proto-modal-hd, proto-modal-bd, proto-modal-ft, proto-modal-title, proto-modal-desc, proto-modal-close, proto-field-group, proto-field-label, proto-req
DRAWER: proto-drawer-backdrop, proto-drawer, proto-drawer-wide, proto-drawer-hd, proto-drawer-title, proto-drawer-desc, proto-drawer-close, proto-drawer-main, proto-drawer-footer
CONFIG: proto-config-page, proto-config-channel, proto-config-shell, proto-strategy-rail, proto-strategy-list, proto-strategy-item, proto-seg-tabs, proto-seg-tab, proto-pill-tabs, proto-pill, proto-policy-grid, proto-policy-card（配置主从页，非列表页）
INTERACTIVE: proto-tab, proto-seg-tab, proto-pill, data-toggle-filter（可无 btn，见 AGENT-7#8）
```

`is-actions-start` 写在 **`filter-bottom-bar` 同一元素**上，与 `filter-bottom-bar` 为两个 class，非一个带点号的 class 名。

---

## AGENT-9｜视觉 token（执行即可，勿发挥）

- **对比度（勿改浅）**：正文 `#606266` on `#fff` ≥ **4.5:1**；主标题 `#303133` ≥ **7:1**；次要 `#909399` 仅用于说明/分页/表头辅助，**禁止**再浅于 `#909399` 作正文。
- 间距：8/16/24/32 阶梯；禁止 13px、19px 随意值。
- 表面：`#f0f2f5` 页底 → `#fff` 卡片 → 内区 `#fafafa`/`#f5f7fa` 最多 3 层。
- 阴影：卡片 `0 1px 4px rgba(0,21,41,.06)`；勿重阴影堆叠。
- 圆角：控件/卡片统一 4px（或卡片 6px 二档，勿混多种）。
- 字重：标题 600 / 区块 500 / 正文 400；数字列 `tabular-nums`。
- 主色 `#409EFF`：仅主按钮、链接、选中、焦点环；表格勿大面积铺蓝。
- 动效：`cubic-bezier(0.4,0,0.2,1)`，150～280ms；`tokens.css` 内 `@media (prefers-reduced-motion: reduce)` 关闭过渡。
- z-index：内容 0 → 热点 20 → 抽屉 100 → 全屏弹层 1000+。
- 焦点：`.btn` / `.proto-tab` / `.proto-seg-tab` / `.proto-pill` / `.filter-control` 使用 `:focus-visible` 轮廓（主色 2px）。

---

## AGENT-10｜交互

- 主操作：default / hover / active / disabled / loading（按钮可加 `disabled` 或文案「提交中…」演示）。
- **加载**：PRD 说明区写 `v-loading` / 查询中刷新列表；HTML 原型用 **骨架行**（`.proto-skeleton-row` + `.proto-skeleton-bar`）或表格区 `aria-busy="true"`，**禁止**无反馈长时间空白。
- 表格空：用 `proto-empty`；有数据勿留空态行、勿留骨架行（见 AGENT-5）。
- 行内操作：须 `<button class="btn btn-link">`，**禁止** `<a href>`；工具栏与行内 **勿多个** `btn-primary`。
- 弹窗/抽屉：独立确定/取消；Esc 可关（若适用）；提交成功须在 PRD 写明列表是否刷新。

---

## AGENT-11｜PRD 内嵌画布

- **画布尺寸**：中原型区固定 **1440×900**（见 `prototype-authoring.md`）；**勿**在 slot 内做移动端断点/汉堡菜单改版。
- **响应式**：真机适配、侧栏抽屉化、表转卡片等只写在 **APPENDIX / PRD 说明**，HTML 原型仍按桌面疏朗布局绘制。
- 热点 ≥32×32px；对应 `FR-xxx`；点击右侧/抽屉须有内容。
- 详情面板宽约主区 32%～40%。
- 多 Tab：说明区 + 目录 `data-proto-tab`（见 AGENT-2 Tab 行）。

---

## AGENT-12｜禁止（显廉价）

- 筛选 5～7 列挤一行；表 `padding<12px`；筛选固定宽 + 表 100%（左右不齐，**#1/#2 失败**）。
- 渐变大按钮；彩虹 tag；整行蓝底；emoji 图标。
- 空表无 `proto-empty`；有数据仍留 `proto-empty` 行；无 hover/focus；动画 >500ms。
- 行内 5 个链接不收 `proto-more`；宽表未加 `proto-table-scroll-wide`。

---

## AGENT-13｜页面范围（HTML）

| 类型 | slot HTML | PRD 说明区 |
|------|-----------|------------|
| 列表 + 筛选 | ✅ AGENT-5 | `el-form` / `el-table` / `el-pagination` |
| 配置主从（策略列表等） | ✅ **AGENT-5b** | APPENDIX + 主从交互说明 |
| 弹窗/抽屉 | ✅ AGENT-6（附于列表或配置页片段末） | `el-dialog` / `el-drawer` |
| 详情 / 分步纯表单 | ❌ 不出 slot | ✅ **APPENDIX** `el-*` 名 |

---

# ⛔ AGENT 止于此 · 以下仅供 PRD 正文 / 研发（禁止拼 slot DOM）

---

# APPENDIX｜PRD 说明区 Element 语义（禁止用于 slot HTML）

## A1 骨架

`el-container` / `el-header` 60px / `el-aside` 200～240px / `el-main`。写清侧栏折叠、主区「筛选+表格+分页」。**响应式**：小屏侧栏 `drawer`、表 `overflow-x`、筛选折叠 — 仅文字描述，原型仍 1440 桌面（见 AGENT-11）。

## A2 色彩

Primary `#409EFF` · Success `#67C23A` · Warning `#E6A23C` · Danger `#F56C6C` · Info `#909399`  
文案 `#303133` / `#606266` / `#909399` · 边框 `#DCDFE6`～`#EBEEF5` · 表头 `#F5F7FA`

## A3 表单

列表筛选：`label-position="top"`。编辑/详情：常 `right`。`el-input` / `el-select` / `el-date-picker` / `el-upload`；写清校验、必填、联动清空。

## A4 表格 / 分页 / 树

`el-table`（stripe、`v-loading`、empty）；行操作 ≤3 否则 dropdown；`el-pagination` pageSize；`el-tree` 单选/多选/lazy。查询/提交须写清 loading 与刷新行为（原型用 AGENT-10 骨架行示意）。

## A5 反馈

`Message` / `MessageBox` / `Notification` / `v-loading` — 同类操作统一方式。

## A6 弹层（文字）

`el-dialog` 480～720px · `el-drawer` · 勿用 popover 承载复杂表单。

## A7 按钮

primary 每视窗一个主焦点 · 行内 text · danger 须二次确认。

## A8 页面模式

| 模式 | 撰写 |
|------|------|
| 列表 | `el-form` + `el-table` + `el-pagination` |
| 配置主从 | 左列表 + 右 Tab/策略卡（HTML 见 AGENT-5b） |
| 弹窗 | `el-dialog` / `el-drawer` |
| 详情/分步表单 | 分组字段、步骤、保存粒度 |

## A9 Logo

init 内嵌 data URI；催收顶栏左；业务/质检侧栏左。

## A10 团队覆盖

Figma/主题 JSON 可放项目 `reference/`；元信息注明「视觉以项目 assets 为准」。
