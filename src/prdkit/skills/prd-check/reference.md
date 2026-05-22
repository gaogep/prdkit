# prd-check 参考

## proto-ref 规范

```html
<p class="proto-ref">见中原型 → Tab：<strong>平账审核</strong></p>
```

`<strong>` 文案应与 `data-tab` 按钮文字一致，或与 `data-proto-tab` 值对应 Tab 的 label。

## 目录联动

```html
<a href="#sec-3-2" data-proto-tab="audit">3.2 平账审核</a>
```

- `href` 必须对应说明区存在的 `id`
- `data-proto-tab` 必须对应 slot 内 `data-proto-page` / `data-tab`

## 功能节最小集（sec-3-*）

每个需高保真的功能应同时满足：

1. `prd_index.md` 有勾选项
2. 目录有 `#sec-3-x` 链接
3. 说明有 `proto-ref` + 实质规则（或 `[TODO]`）
4. 原型有对应 Tab（若声明「见中原型」）

## 编造判定

以下视为需替换或标 TODO（除非用户原文即如此）：

- `测试1`、`aaa`、`示例功能点`、`示例小节`
- 无业务含义的「按钮」「操作」

已写 `[TODO: …]` / `{待填写}` 的不报错。
