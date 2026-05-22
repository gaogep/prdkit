# assets 使用说明

本目录为 **prdkit 安装包内置资源**，通过 `prdkit path assets/<文件名>` 解析绝对路径后，由 Agent **Read** 读取；工作区无需复制 `prdkit/` 目录。

## 内置文件

| 资源键 | 用途 |
|--------|------|
| `assets/文档输出模板.html` | **PRD 单页交付骨架**（左目录 / 中原型 / 右说明，可拖拽分栏、Mermaid 放大） |
| `assets/logo.data-uri` | **Apl 品牌 Logo**（PNG data URI）；`prdkit-html init` 时写入壳内 `<img>`，**无需**随附 `logo.png` |
| `assets/催收后台-原型壳.html` | **催收后台** 顶栏 + 主区壳，`#prototype-slot` 内扩展业务原型 |
| `assets/tokens.css` / `proto-base.css` / `proto-runtime.js` | 设计 Token、列表页/表格/弹层、Tab 与目录联动（由 `init` 注入，勿写入 slot 片段） |
| `reference/design-spec.md` | **AGENT-0～13**（列表/弹窗骨架与类名；绘制 slot 前必读） |
| `reference/prototype-authoring.md` | **原型铁律** 与 Agent 工作流 |
| `assets/业务后台-原型壳.html` | **业务后台** 侧栏 + 顶栏壳 |
| `assets/质检后台-原型壳.html` | **质检后台** 白侧栏布局壳 |

查看全部资源键：`prdkit path --list`

## 可选扩展（团队自建，非包内必选）

| 建议路径 | 用途 |
|----------|------|
| `tokens.json`（可选） | 团队扩展 Token；默认以套件内置 `tokens.css` 为准 |
| `diagrams/` | draw.io / FigJam 导出图 |
| `screenshots/` | 参考截图（须脱敏） |

撰写与 UI 规范见 `reference/prd-writing-spec.md`、`reference/design-spec.md`（`prdkit path reference/...`）。

## 交付引用

用户项目 `prds/*.html` 由 `prdkit-html init` 生成时，Logo 已内嵌在 HTML 内，**无需**与 PRD 同目录放置 `logo.png`。

## 脱敏

上传截图或接口样例前，请确认已脱敏客户标识、账号、金额等敏感信息。
