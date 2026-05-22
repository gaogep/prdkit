# prd-check 参考

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

```html
<p class="proto-ref">见中原型 → Tab：<strong>平账审核</strong></p>
<a href="#sec-3-2" data-proto-tab="audit">3.2 平账审核</a>
```

## 编造判定

`测试1`、`aaa`、`示例功能点` 等；已有 `[TODO]` / `{待填写}` 不报。
