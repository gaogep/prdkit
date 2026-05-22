# reference 规范索引

本目录为 **撰写与 UI 设计** 规范；HTML 模板与壳文件见 **`assets/`**。

## 阅读顺序

| 顺序 | 资源键 | 用途 |
|------|--------|------|
| 1 | `reference/prd-writing-spec.md` | 系统矩阵、需求类型、章节目录、内容生成规则、PRD 模板 |
| 2 | `reference/design-spec.md` | 原型：**AGENT-0～13**；PRD 正文：APPENDIX |
| 3 | `assets/文档输出模板.html` | 三栏 HTML 骨架 |

## 硬约束摘要（生成前自检）

- **业务与正文**：遵循 `prd-writing-spec.md` §2、§5～§8。
- **壳与布局**：`design-spec.md` **AGENT-3**；三系统不得混用。
- **Logo**：`init` 时内嵌 `assets/logo.data-uri`，交付勿再附 png。
- **列表**：**AGENT-5**；**配置主从**：**AGENT-5b**；**弹窗/抽屉**：**AGENT-6**；多 Tab **AGENT-2**；**AGENT-7** 自检。
- **画布**：1440×900 固定（**AGENT-11**）；响应式仅 PRD 文字。
- **PRD 说明区**：**APPENDIX**（禁止抄进 slot）。
- **禁止** slot 内 `style=`；样式由 `tokens.css` + `proto-base.css` 提供。
