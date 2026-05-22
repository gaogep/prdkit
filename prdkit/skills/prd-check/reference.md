# prd-check 参考

## 用户确认与选择性修复

1. `prdkit-html check-consistency` → 得到 A/B/C… 清单，写入 `.memory/prd_check_latest.json`
2. 用户回复 `B C D` → `prdkit-html check-consistency --fix-letters B,C,D`
3. 对 `[需人工]` 项按 `code` 手改后重新检查

清单字段：`letter`、`code`、`message`、`auto_fixable`、`severity`。

## 三栏正确布局（DOM）

`#prd-shell` 内子节点顺序（左→右）：

```text
[data-panel="toc"] → .resizer-toc → [data-panel="proto"] → .resizer-spec → [data-panel="spec"]
```

标记区归属：

| 标记 | 必须在 |
|------|--------|
| `<!-- prdkit:toc:start -->` | `data-panel="toc"` 内 |
| `<!-- prdkit:slot:start -->` | `data-panel="proto"` 内（`#prototype-slot`） |
| `<!-- prdkit:spec:start -->` | `data-panel="spec"` 内 |

常见错乱现象：说明区整栏掉到页面最下方、中间灰色空白（关原型后说明未拉长见模板 CSS）、目录与原型对调。

## 系统壳识别（DOM 指纹）

| 壳 | DOM/CSS 特征 |
|----|----------------|
| 催收后台 | 有 `.app-header` + `.app-body`，**无** `.app-layout` / `.app-sidebar` |
| 业务后台 | `.app-layout` + `.app-sidebar`，CSS 含 `#001529` |
| 质检后台 | `.app-layout` + `.app-sidebar`，侧栏 `--sidebar-bg: #ffffff`、菜单蓝字 |

`data-prdkit-shell="业务后台|催收后台|质检后台"` 由 `init` 写入，须与上表一致。

## 期望壳推断顺序

1. `.memory/prd_output.json` → `shell`（权威）
2. `product_brief.md` / `prd_index.md` 关键词
3. 目录+说明正文多次出现的系统名（≥2 次触发 `SHELL_TEXT_MISMATCH`）

## proto-ref / 目录联动

**有界面**的功能：

```html
<p class="proto-ref">见中原型 → Tab：<strong>平账审核</strong></p>
<a href="#sec-3-2" data-proto-tab="audit">3.2 平账审核</a>
```

**无界面（后端/接口/状态机）** — 允许不关联任何原型：

```html
<h3 id="sec-3-5">3.5 账单状态同步</h3>
<p class="proto-exempt">本功能为后端逻辑，纯接口调用，无需原型。</p>
<p>状态变化：待支付 → 已支付 → 已结清 …</p>
```

识别规则（`is_proto_exempt_section`）：`proto-exempt` / `prdkit:proto-exempt` / `data-proto-exempt="true"`，或正文命中 `后端逻辑|纯接口|接口调用|状态变化|状态机|无需原型` 等关键词。豁免节**不要**写 `proto-ref` 或目录 `data-proto-tab`。

## 编造判定

`测试1`、`aaa`、`示例功能点` 等；已有 `[TODO]` / `{待填写}` 不报。
