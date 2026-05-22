"""将 PRD 片段合并进 HTML 交付模板（供 Agent 调用，禁止手写拼接脚本）。"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from functools import lru_cache
from pathlib import Path

from prdkit.paths import resolve

CONFIG_FILE = ".memory/prd_output.json"

SHELL_BY_NAME = {
    "业务后台": "assets/业务后台-原型壳.html",
    "催收后台": "assets/催收后台-原型壳.html",
    "质检后台": "assets/质检后台-原型壳.html",
}

MARKERS = {
    "toc": ("<!-- prdkit:toc:start -->", "<!-- prdkit:toc:end -->"),
    "spec": ("<!-- prdkit:spec:start -->", "<!-- prdkit:spec:end -->"),
    "proto": ("<!-- prdkit:proto:start -->", "<!-- prdkit:proto:end -->"),
}

SLOT_START = "<!-- prdkit:slot:start -->"
SLOT_END = "<!-- prdkit:slot:end -->"


def page_marker_start(tab: str) -> str:
    return f"<!-- prdkit:page:{tab}:start -->"


def page_marker_end(tab: str) -> str:
    return f"<!-- prdkit:page:{tab}:end -->"

DEFAULT_SLOT_SCAFFOLD = """<div class="proto-shell" id="proto-root">
  <div class="proto-tabs" role="tablist" aria-label="原型页面"></div>
  <div class="proto-pages" id="proto-pages"></div>
</div>"""

FORBIDDEN_SLOT_PATTERNS = [
    (r"<style\b", "不得包含 <style>（样式由 tokens.css / proto-base.css 提供）"),
    (r"\bstyle\s*=", "不得包含 style= 内联样式（观感由 tokens.css / proto-base.css 统一）"),
    (r"<script\b", "不得包含 <script>（交互由 proto-runtime.js 提供）"),
    (r"<html\b", "不得包含 <html>"),
    (r"<body\b", "不得包含 <body>"),
    (r'\bclass=["\'][^"\']*\bapp-layout\b', "不得包含壳结构 .app-layout"),
    (r'\bclass=["\'][^"\']*\bapp-sidebar\b', "不得包含壳结构 .app-sidebar"),
    (r'\bid=["\']sidebar["\']', "不得包含壳 #sidebar"),
    (r'\bclass=["\'][^"\']*\bapp-header\b', "不得包含壳顶栏 .app-header（业务区外）"),
]

SHELL_STYLE_OVERRIDES = """
/* prdkit: 壳样式作用域修正（勿删） */
.prd-embed .app-layout,
.prd-embed .app-body {
  height: 100% !important;
  min-height: 0 !important;
  max-height: 100%;
}
.prd-embed .main-area,
.prd-embed .content-card {
  min-height: 0;
}
"""


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_logo_data_uri() -> str:
    """品牌 Logo 的 data URI，写入 HTML 后无需随附 logo.png。"""
    try:
        uri_path = resolve("assets/logo.data-uri")
        if uri_path.is_file():
            return uri_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        pass
    return ""


def embed_logo_in_html(html: str) -> str:
    uri = load_logo_data_uri()
    if not uri:
        return html
    return html.replace('src="logo.png"', f'src="{uri}"').replace("src='logo.png'", f"src='{uri}'")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def load_config(cwd: Path | None = None) -> dict:
    base = cwd or Path.cwd()
    path = base / CONFIG_FILE
    if not path.is_file():
        raise FileNotFoundError(
            f"未找到 {CONFIG_FILE}。请先执行 prdkit-html init 或在 prd-init 中确认输出目录。"
        )
    return json.loads(_read_text(path))


def save_config(config: dict, cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    path = base / CONFIG_FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    _write_text(path, json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    return path


def resolve_html_path(html: str | None, cwd: Path | None = None) -> Path:
    if html:
        return Path(html)
    config = load_config(cwd)
    return Path(config["html_path"])


def replace_between_markers(html: str, key: str, content: str) -> str:
    start, end = MARKERS[key]
    pattern = re.escape(start) + r".*?" + re.escape(end)
    replacement = f"{start}\n{content.strip()}\n{end}"
    if not re.search(pattern, html, flags=re.DOTALL):
        raise ValueError(f"模板中未找到标记 {start} … {end}")
    return re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)


def scope_shell_styles(css: str) -> str:
    """将壳内 html/body/100vh 规则限制在 .prd-embed 画布内。"""
    css = re.sub(r"html\s*,\s*body\s*\{", ".prd-embed {", css, flags=re.I)
    css = re.sub(r"(?<![\w-])html\s*\{", ".prd-embed {", css, flags=re.I)
    css = re.sub(r"(?<![\w-])body\s*\{", ".prd-embed {", css, flags=re.I)
    css = re.sub(
        r"(\.app-layout\s*\{[^}]*?)height:\s*100vh\s*;?",
        r"\1height: 100%;",
        css,
        flags=re.I | re.DOTALL,
    )
    css = re.sub(
        r"(\.app-layout\s*\{[^}]*?)min-height:\s*100vh\s*;?",
        r"\1min-height: 0;",
        css,
        flags=re.I | re.DOTALL,
    )
    css = re.sub(
        r"min-height:\s*calc\s*\(\s*100vh",
        "min-height: calc(100%",
        css,
        flags=re.I,
    )
    return css.strip() + "\n" + SHELL_STYLE_OVERRIDES.strip()


def extract_shell_parts(shell_html: str) -> tuple[str, str]:
    styles = "\n\n".join(
        m.strip() for m in re.findall(r"<style[^>]*>(.*?)</style>", shell_html, flags=re.DOTALL | re.I)
    )
    body_match = re.search(r"<body[^>]*>(.*)</body>", shell_html, flags=re.DOTALL | re.I)
    body = body_match.group(1).strip() if body_match else shell_html.strip()
    body = re.sub(r"<script[^>]*>.*?</script>", "", body, flags=re.DOTALL | re.I).strip()
    return styles, body


def ensure_slot_markers(body: str) -> str:
    if SLOT_START in body and SLOT_END in body:
        return body
    pattern = r'(<div[^>]*\bid=["\']prototype-slot["\'][^>]*>)(\s*)(</div>)'
    if re.search(pattern, body, flags=re.DOTALL | re.I):
        return re.sub(
            pattern,
            rf"\1\n{SLOT_START}\n{SLOT_END}\n\3",
            body,
            count=1,
            flags=re.DOTALL | re.I,
        )
    return body


def inject_shell(template_html: str, shell_html: str) -> str:
    styles, body = extract_shell_parts(shell_html)
    body = embed_logo_in_html(ensure_slot_markers(body))
    html = template_html
    if styles:
        scoped = scope_shell_styles(styles)
        html = html.replace(
            "</head>",
            f'\n<style data-prdkit-shell="true">\n{scoped}\n</style>\n</head>',
            1,
        )
    return replace_between_markers(html, "proto", body)


def inject_prdkit_assets(html: str) -> str:
    tokens_css = _read_text(resolve("assets/tokens.css"))
    proto_css = _read_text(resolve("assets/proto-base.css"))
    proto_js = _read_text(resolve("assets/proto-runtime.js"))
    if 'data-prdkit-tokens' not in html:
        html = html.replace(
            "</head>",
            f'\n<style data-prdkit-tokens="true">\n{tokens_css}\n</style>\n</head>',
            1,
        )
    if 'data-prdkit-proto-base' not in html:
        html = html.replace(
            "</head>",
            f'\n<style data-prdkit-proto-base="true">\n{proto_css}\n</style>\n</head>',
            1,
        )
    if 'data-prdkit-proto-runtime' not in html:
        html = html.replace(
            "</body>",
            f'\n<script data-prdkit-proto-runtime="true">\n{proto_js}\n</script>\n</body>',
            1,
        )
    return html


def apply_default_slot_scaffold(html: str) -> str:
    if SLOT_START not in html:
        raise ValueError("未找到 slot 标记，请先 prdkit-html init")
    inner = re.search(
        re.escape(SLOT_START) + r"(.*?)" + re.escape(SLOT_END),
        html,
        flags=re.DOTALL,
    )
    if inner and inner.group(1).strip():
        return html
    return set_proto_slot(html, DEFAULT_SLOT_SCAFFOLD)


def collect_ids(html: str) -> list[str]:
    return re.findall(r'\bid=["\']([^"\']+)["\']', html, flags=re.I)


def _strip_html_comments(fragment: str) -> str:
    return re.sub(r"<!--.*?-->", "", fragment, flags=re.DOTALL)


def _div_balance(fragment: str) -> int:
    opens = len(re.findall(r"<div\b", fragment, flags=re.I))
    closes = len(re.findall(r"</div>", fragment, flags=re.I))
    return opens - closes


def _find_div_close_end(html: str, open_pos: int) -> int | None:
    """Return index after the </div> that closes the <div> opening at open_pos."""
    depth = 0
    i = open_pos
    while i < len(html):
        m_open = re.search(r"<div\b", html[i:], flags=re.I)
        m_close = re.search(r"</div>", html[i:], flags=re.I)
        if not m_close:
            return None
        rel_open = i + m_open.start() if m_open else len(html) + 1
        rel_close = i + m_close.start()
        if m_open and rel_open < rel_close:
            depth += 1
            i = rel_open + 4
            continue
        depth -= 1
        i = rel_close + len("</div>")
        if depth == 0:
            return i
    return None


def _is_list_page_fragment(fragment: str) -> bool:
    return bool(
        re.search(r'\bclass=["\'][^"\']*\bquery-form\b', fragment, flags=re.I)
        or re.search(r'\bclass=["\'][^"\']*\bfilter-grid\b', fragment, flags=re.I)
    )


def validate_proto_interactive(fragment: str) -> list[str]:
    """design-spec AGENT-7#8：可点击控件类名与 data-* 挂载。"""
    errors: list[str] = []
    body = _strip_html_comments(fragment)

    for btn_m in re.finditer(r"<button\b([^>]*)>", body, flags=re.I):
        attrs = btn_m.group(1)
        if re.search(r"\bproto-tab\b", attrs, flags=re.I):
            continue
        if re.search(r"\bproto-seg-tab\b", attrs, flags=re.I) or re.search(
            r"\bproto-pill\b", attrs, flags=re.I
        ):
            continue
        if re.search(r"\bdata-toggle-filter\b", attrs, flags=re.I):
            if not re.search(r"\bbtn\b", attrs, flags=re.I):
                errors.append("AGENT-7#8: data-toggle-filter 须在 class 含 btn 的 <button> 上")
                break
            continue
        if not re.search(r"\bbtn\b", attrs, flags=re.I):
            errors.append("AGENT-7#8: 按钮须含 .btn / .btn-primary 等类（cursor 与 hover 由 CSS 提供）")
            break

    for attr in ("data-open-modal", "data-open-drawer", "data-close-modal", "data-close-drawer"):
        for m in re.finditer(rf"<(\w+)([^>]*)\b{re.escape(attr)}\b", body, flags=re.I):
            tag, attrs = m.group(1).lower(), m.group(2)
            if tag == "button" and re.search(r"\bbtn\b", attrs, flags=re.I):
                continue
            errors.append(
                f"AGENT-7#8: {attr} 须放在 class 含 btn 的 <button> 上（勿用裸 <a>/<span>）"
            )
            break
        else:
            continue
        break

    if re.search(r"\bproto-op\b[\s\S]{0,800}?<a\b[^>]*\bhref\s*=", body, flags=re.I):
        errors.append(
            "AGENT-7#10: 行内操作用 <button class=\"btn btn-link\">，禁止在 .proto-op 内使用 <a href>"
        )
    elif re.search(
        r"\bcol-actions\b[\s\S]{0,400}?<a\b[^>]*\bhref\s*=", body, flags=re.I
    ):
        errors.append("AGENT-7#10: 操作列禁止 <a href>，改用 button.btn-link")
    elif re.search(
        r"\btable-toolbar\b[\s\S]{0,400}?<a\b[^>]*\bhref\s*=", body, flags=re.I
    ):
        errors.append("AGENT-7#10: 工具栏禁止 <a href>，改用 button.btn-*")

    errors.extend(validate_proto_form_labels(fragment))
    return errors


def validate_proto_form_labels(fragment: str) -> list[str]:
    """design-spec AGENT-7#11：filter-item 内 label 与控件 id/for 关联。"""
    errors: list[str] = []
    body = _strip_html_comments(fragment)
    if not re.search(r"\bfilter-item\b", body, flags=re.I):
        return errors
    for item_m in re.finditer(
        r"<div[^>]*\bfilter-item\b[^>]*>([\s\S]*?)</div>",
        body,
        flags=re.I,
    ):
        block = item_m.group(1)
        if not re.search(r"\bfilter-label\b", block, flags=re.I):
            continue
        ctrl_m = re.search(
            r"<(?:input|select|textarea)\b[^>]*\bfilter-control\b",
            block,
            flags=re.I,
        )
        if not ctrl_m:
            continue
        label_m = re.search(r"<label[^>]*\bfilter-label\b[^>]*>", block, flags=re.I)
        if not label_m:
            errors.append("AGENT-7#11: 筛选项须使用 <label class=\"filter-label\">")
            break
        label_attrs = label_m.group(0)
        ctrl_attrs = ctrl_m.group(0)
        for_m = re.search(r'\bfor\s*=\s*["\']([^"\']+)["\']', label_attrs, flags=re.I)
        id_m = re.search(r'\bid\s*=\s*["\']([^"\']+)["\']', ctrl_attrs, flags=re.I)
        if not for_m or not id_m or for_m.group(1) != id_m.group(1):
            errors.append(
                "AGENT-7#11: filter-item 内 label.filter-label 须 for 关联 "
                "input/select/textarea.filter-control 的 id（且一致）"
            )
            break
    return errors


def validate_proto_list_align(fragment: str) -> list[str]:
    """design-spec AGENT-7#1/#2：筛选卡与表格卡结构对齐（非像素测量）。"""
    errors: list[str] = []
    body = _strip_html_comments(fragment)
    if not _is_list_page_fragment(body):
        return errors

    if re.search(r"\bproto-list-card\b[\s\S]*\bquery-form\b", body, flags=re.I):
        errors.append(
            "AGENT-7#1: query-form 不得嵌套在 proto-list-card 内（筛选与表格须同级）"
        )
    if re.search(r"\bproto-list-card\b[\s\S]*\bfilter-grid\b", body, flags=re.I):
        errors.append("AGENT-7#2: filter-grid 须在 query-form 内，不得放入 proto-list-card")
    if re.search(r"\bfilter-grid\b", body, flags=re.I) and not re.search(
        r"\bquery-form\b[\s\S]*\bfilter-grid\b", body, flags=re.I
    ):
        if not re.search(r"\bquery-form\b", body, flags=re.I):
            errors.append("AGENT-7#2: 含 filter-grid 时须有 query-form 包裹")
    if re.search(r"\bproto-table\b", body, flags=re.I) and not re.search(
        r"\bproto-list-card\b", body, flags=re.I
    ):
        errors.append("AGENT-7#2: proto-table 须包在 proto-list-card 内")

    return errors


def validate_proto_list_spec231(fragment: str) -> list[str]:
    """design-spec AGENT-7 列表页自检（启发式，非像素测量）。"""
    errors: list[str] = []
    body = _strip_html_comments(fragment)
    if not _is_list_page_fragment(body):
        return errors

    errors.extend(validate_proto_list_align(fragment))

    if re.search(r"\b200px\b", body, flags=re.I):
        errors.append("AGENT-7#3: 禁止筛选区固定像素总宽（如 200px×4），须 4 列 minmax(0,1fr) 等分")
    if re.search(
        r'(?:filter-grid|query-form)[^>]*\bstyle\s*=[^>]*(?:width|max-width)\s*:\s*\d+px',
        body,
        flags=re.I,
    ):
        errors.append("AGENT-7#3: 筛选区禁止内联固定 width/max-width（易导致窄于表格）")
    if re.search(r'label-position\s*=\s*["\'](?:left|right)', body, flags=re.I):
        errors.append("AGENT-7#4: 列表筛选禁止左右并排标签（须 label 在上、控件在下）")
    if re.search(
        r"filter-item[\s\S]*?<label(?![^>]*\bfilter-label\b)[^>]*>[\s\S]*?"
        r"(?:<input|<select|<textarea)",
        body,
        flags=re.I,
    ):
        errors.append("AGENT-7#4: 筛选项须用 .filter-label 置于 .filter-control 上方")

    if re.search(
        r"<div[^>]*\bfilter-item\b[^>]*>([\s\S]*?)</div>",
        body,
        flags=re.I,
    ):
        for item_m in re.finditer(
            r"<div[^>]*\bfilter-item\b[^>]*>([\s\S]*?)</div>",
            body,
            flags=re.I,
        ):
            item_html = item_m.group(1)
            if re.search(r"\bbtn-(?:primary|default)\b", item_html, flags=re.I) and not re.search(
                r"\bfilter-control\b", item_html, flags=re.I
            ):
                errors.append(
                    "AGENT-7#5: 重置/查询须在 .filter-bottom-bar，禁止作为 .filter-item 栅格末列"
                )
                break

    if re.search(r"filter-grid[\s\S]*?\bfilter-actions\b", body, flags=re.I) and not re.search(
        r"\bfilter-bottom-bar\b", body, flags=re.I
    ):
        errors.append("AGENT-7#5: .filter-actions 须置于 .filter-bottom-bar 内（与表格右缘对齐）")

    if re.search(
        r"(?:table-toolbar|proto-list-card|table-card)[^>]*\bstyle\s*=[^>]*padding[^>]*\b8px\b",
        body,
        flags=re.I,
    ):
        errors.append("AGENT-7#6: 表格区禁止 padding:8px（须与筛选区同一 --page-pad-x）")
    if re.search(r"\bproto-list-card\b[^>]*\bstyle\s*=", body, flags=re.I):
        errors.append("AGENT-7#6: .proto-list-card 禁止内联 padding（由 proto-base.css 统一）")

    for cell_m in re.finditer(
        r"<t[hd][^>]*\bstyle\s*=[^>]*padding\s*:\s*(\d+)px",
        body,
        flags=re.I,
    ):
        if int(cell_m.group(1)) < 12:
            errors.append("AGENT-7#7: 表格单元格 padding 须 ≥12px（推荐 .proto-table 16px）")
            break
    if re.search(r"<table\b", body, flags=re.I) and not re.search(
        r"\bproto-table\b", body, flags=re.I
    ):
        errors.append("AGENT-7#7: 表格须用 .proto-table（行高 ≥16px），禁止挤扁裸 table")

    if re.search(r"\bfilter-item--extra\b", body, flags=re.I) and not re.search(
        r"\bdata-toggle-filter\b", body, flags=re.I
    ):
        errors.append(
            "AGENT-7#9: 含 filter-item--extra 时须有 data-toggle-filter 收起按钮（见 AGENT-5）"
        )

    if re.search(r"<table\b", body, flags=re.I) and not re.search(
        r"\b(?:table-toolbar|proto-pager)\b", body, flags=re.I
    ):
        errors.append("AGENT-7#1/#2: 列表表格建议含 .table-toolbar 与 .proto-pager，与筛选卡同宽对齐")

    return errors


def validate_proto_config_layout(fragment: str) -> list[str]:
    """design-spec AGENT-5b：配置主从页结构。"""
    errors: list[str] = []
    if not re.search(r"\bproto-config-page\b", fragment, flags=re.I):
        return errors
    required = (
        "proto-config-split",
        "proto-strategy-rail",
        "proto-config-detail",
        "proto-config-shell",
    )
    for cls in required:
        if not re.search(rf"\b{cls}\b", fragment, flags=re.I):
            errors.append(f"配置页须含 .{cls}（见 design-spec AGENT-5b）")
    if re.search(r"\bproto-list-page\b", fragment, flags=re.I) and re.search(
        r"\bproto-config-page\b", fragment, flags=re.I
    ):
        errors.append("禁止同一片段同时根节点 proto-list-page 与 proto-config-page")
    return errors


def validate_proto_list_layout(fragment: str) -> list[str]:
    """列表页片段须使用标准类名，避免手写 table/inline 导致观感劣化。"""
    errors: list[str] = []
    if re.search(r"\bproto-config-page\b", fragment, flags=re.I):
        return validate_proto_config_layout(fragment)
    if not _is_list_page_fragment(fragment):
        return errors
    if not re.search(r"\bfilter-bottom-bar\b", fragment, flags=re.I):
        errors.append("列表页须含 .filter-bottom-bar（重置/查询底栏，见 design-spec AGENT-4）")
    if not re.search(r"\bproto-list-page\b", fragment, flags=re.I):
        errors.append("列表页根节点须为 .proto-list-page（见 design-spec AGENT-5）")
    if re.search(r"<table\b", fragment, flags=re.I) and not re.search(
        r'\bclass=["\'][^"\']*\bproto-table\b', fragment, flags=re.I
    ):
        errors.append('列表表格须使用 class="proto-table"，禁止裸 <table>')
    if re.search(r"<table\b", fragment, flags=re.I) and not re.search(
        r"\bproto-list-card\b", fragment, flags=re.I
    ):
        errors.append("列表页表格须包在 .proto-list-card 内（筛选卡与表格卡分离）")
    errors.extend(validate_proto_list_spec231(fragment))
    return errors


def validate_proto_fragment(fragment: str, existing_html: str | None = None) -> list[str]:
    errors: list[str] = []
    balance = _div_balance(fragment)
    if balance > 0:
        errors.append(f"片段中 <div> 比 </div> 多 {balance} 个，可能提前闭合父级容器")
    elif balance < 0:
        errors.append(f"片段中 </div> 比 <div> 多 {-balance} 个")
    check_body = _strip_html_comments(fragment)
    for pattern, msg in FORBIDDEN_SLOT_PATTERNS:
        if re.search(pattern, check_body, flags=re.I | re.DOTALL):
            errors.append(msg)
    if SLOT_START in fragment or SLOT_END in fragment:
        errors.append("片段不得包含 prdkit:slot 标记（由工具维护）")
    frag_ids = collect_ids(fragment)
    dup_in_frag = [k for k, v in Counter(frag_ids).items() if v > 1]
    if dup_in_frag:
        errors.append(f"片段内重复 id: {', '.join(dup_in_frag)}")
    if existing_html:
        existing_ids = set(collect_ids(existing_html))
        overlap = sorted(set(frag_ids) & existing_ids)
        if overlap:
            errors.append(f"与文档已有 id 冲突: {', '.join(overlap[:12])}" + ("…" if len(overlap) > 12 else ""))
    errors.extend(validate_proto_config_layout(fragment))
    errors.extend(validate_proto_list_layout(fragment))
    errors.extend(validate_proto_interactive(fragment))
    return errors


def validate_shell_structure(html: str) -> list[str]:
    errors: list[str] = []
    shell_opens = len(re.findall(r'\bid=["\']prd-shell["\']', html, flags=re.I))
    if shell_opens == 0:
        errors.append('缺少 id="prd-shell"（三栏骨架损坏）')
    elif shell_opens > 1:
        errors.append(f'存在 {shell_opens} 个 id="prd-shell"，骨架重复')
    spec_m = re.search(r'data-panel=["\']spec["\']', html, flags=re.I)
    if not spec_m:
        errors.append('缺少 data-panel="spec" 说明区面板')
    shell_m = re.search(r'<div[^>]*\bid=["\']prd-shell["\']', html, flags=re.I)
    if shell_m and spec_m:
        shell_close = _find_div_close_end(html, shell_m.start())
        if shell_close is not None and spec_m.start() > shell_close:
            errors.append("说明区 data-panel=spec 位于 #prd-shell 之外（曾有多余 </div> 提前闭合 shell）")
    for m in re.finditer(r"<div[^>]*\bresizer-spec\b[^>]*>", html, flags=re.I):
        tag = html[m.start() : html.find(">", m.start()) + 1]
        if 'data-resize="spec"' not in tag:
            errors.append(f"resizer-spec 标签损坏（缺少 data-resize=\"spec\"）: {tag[:80]}…")
    if "getElementById(\"prd-shell\")" not in html and "getElementById('prd-shell')" not in html:
        errors.append("缺少三栏布局脚本（getElementById(\"prd-shell\")），勿删除模板底部 script")
    return errors


def validate_proto_tabs(slot_body: str) -> list[str]:
    errors: list[str] = []
    for tab, count in Counter(re.findall(r'data-proto-page=["\']([^"\']+)["\']', slot_body, flags=re.I)).items():
        if count > 1:
            errors.append(f'Tab 页重复 data-proto-page="{tab}" 出现 {count} 次')
    for tab, count in Counter(re.findall(r'data-tab=["\']([^"\']+)["\']', slot_body, flags=re.I)).items():
        if count > 1:
            errors.append(f'Tab 按钮重复 data-tab="{tab}" 出现 {count} 次')
    return errors


def validate_html_document(html: str) -> list[str]:
    errors: list[str] = []
    errors.extend(validate_shell_structure(html))
    slot_match = re.search(
        re.escape(SLOT_START) + r"(.*?)" + re.escape(SLOT_END),
        html,
        flags=re.DOTALL,
    )
    if not slot_match:
        errors.append("缺少 #prototype-slot 的 prdkit:slot 标记区")
    else:
        slot_body = slot_match.group(1)
        errors.extend(validate_proto_fragment(slot_body))
        scripts_in_slot = re.findall(r"<script\b", slot_body, flags=re.I)
        if scripts_in_slot:
            errors.append("slot 区内不得含 <script>")
        errors.extend(validate_proto_tabs(slot_body))
        if _is_list_page_fragment(slot_body) and 'data-prdkit-tokens' not in html:
            errors.append(
                "列表页原型须由 init 注入 tokens.css（缺少 data-prdkit-tokens，请重新 prdkit-html init）"
            )
    runtime_count = len(re.findall(r'data-prdkit-proto-runtime=["\']true["\']', html, flags=re.I))
    if runtime_count == 0:
        errors.append("缺少 data-prdkit-proto-runtime（请 prdkit-html init）")
    elif runtime_count > 1:
        errors.append(f"存在 {runtime_count} 份 proto-runtime，应仅 1 份")
    dup_all = [k for k, v in Counter(collect_ids(html)).items() if v > 1]
    if dup_all:
        errors.append(f"全页重复 id（前 12 个）: {', '.join(dup_all[:12])}")
    proto_blocks = len(re.findall(re.escape(MARKERS["proto"][0]), html))
    if proto_blocks > 1:
        errors.append("prdkit:proto 标记重复，可能多次注入壳")
    boot_count = len(re.findall(r"\bfunction\s+boot\s*\(", html))
    if boot_count > 1:
        errors.append(f"检测到 {boot_count} 处 function boot()，请合并为单一 proto-runtime")
    return errors


def set_proto_slot(html: str, slot_html: str) -> str:
    content = f"{SLOT_START}\n{slot_html.strip()}\n{SLOT_END}"
    pattern = (
        r'(<div[^>]*\bid=["\']prototype-slot["\'][^>]*>\s*)'
        + re.escape(SLOT_START)
        + r".*?"
        + re.escape(SLOT_END)
    )
    if re.search(pattern, html, flags=re.DOTALL | re.I):
        return re.sub(
            pattern,
            lambda m: m.group(1) + content + "\n",
            html,
            count=1,
            flags=re.DOTALL | re.I,
        )
    raise ValueError("未找到 #prototype-slot 的 prdkit:slot 标记，请 prdkit-html init。")


def _sanitize_tab_id(tab_id: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "-", tab_id.strip())
    if not safe:
        raise ValueError("tab id 不能为空")
    return safe


def _ensure_proto_scaffold_in_slot(slot_html: str) -> str:
    if 'id="proto-pages"' in slot_html or 'id="proto-root"' in slot_html:
        return slot_html
    return DEFAULT_SLOT_SCAFFOLD


def _strip_proto_page_for_tab(slot_body: str, tab: str) -> str:
    start, end = page_marker_start(tab), page_marker_end(tab)
    pattern = re.escape(start) + r".*?" + re.escape(end)
    slot_body = re.sub(pattern, "", slot_body, flags=re.DOTALL)
    while True:
        m = re.search(
            rf'<div[^>]*\bdata-proto-page=["\']{re.escape(tab)}["\'][^>]*>',
            slot_body,
            flags=re.I,
        )
        if not m:
            break
        close = _find_div_close_end(slot_body, m.start())
        if close is None:
            break
        slot_body = slot_body[: m.start()] + slot_body[close:]
    while True:
        m = re.search(
            rf'<button[^>]*\bdata-tab=["\']{re.escape(tab)}["\'][^>]*>.*?</button>',
            slot_body,
            flags=re.DOTALL | re.I,
        )
        if not m:
            break
        slot_body = slot_body[: m.start()] + slot_body[m.end() :]
    return slot_body


def set_proto_page(html: str, tab_id: str, page_html: str, tab_label: str | None = None) -> str:
    tab = _sanitize_tab_id(tab_id)
    label = (tab_label or tab).strip()
    slot_match = re.search(
        re.escape(SLOT_START) + r"(.*?)" + re.escape(SLOT_END),
        html,
        flags=re.DOTALL,
    )
    if not slot_match:
        raise ValueError("未找到 slot 标记区")
    slot_body = _ensure_proto_scaffold_in_slot(slot_match.group(1).strip())
    slot_body = _strip_proto_page_for_tab(slot_body, tab)

    tab_btn = (
        f'<button type="button" class="proto-tab" role="tab" data-tab="{tab}" '
        f'aria-selected="false">{label}</button>'
    )
    page_inner = (
        f'<div class="proto-page" data-proto-page="{tab}" hidden role="tabpanel">\n'
        f"{page_html.strip()}\n</div>"
    )
    page_block = f"{page_marker_start(tab)}\n{page_inner}\n{page_marker_end(tab)}"

    if "proto-tab is-active" not in slot_body:
        tab_btn = tab_btn.replace('class="proto-tab"', 'class="proto-tab is-active"')
        page_inner = (
            page_inner.replace('class="proto-page"', 'class="proto-page is-active"')
            .replace(" hidden", "")
        )
        page_block = f"{page_marker_start(tab)}\n{page_inner}\n{page_marker_end(tab)}"
        tab_btn = tab_btn.replace('aria-selected="false"', 'aria-selected="true"')

    if 'class="proto-tabs"' not in slot_body:
        slot_body = _ensure_proto_scaffold_in_slot("")

    if re.search(rf'data-tab=["\']{re.escape(tab)}["\']', slot_body):
        slot_body = re.sub(
            rf'<button[^>]*\bdata-tab=["\']{re.escape(tab)}["\'][^>]*>.*?</button>',
            tab_btn,
            slot_body,
            count=1,
            flags=re.DOTALL | re.I,
        )
    else:
        slot_body = re.sub(
            r'(<div[^>]*class=["\'][^"\']*\bproto-tabs\b[^"\']*["\'][^>]*>)',
            rf"\1\n{tab_btn}",
            slot_body,
            count=1,
            flags=re.I,
        )

    marker_pattern = re.escape(page_marker_start(tab)) + r".*?" + re.escape(page_marker_end(tab))
    if re.search(marker_pattern, slot_body, flags=re.DOTALL):
        slot_body = re.sub(marker_pattern, page_block.strip(), slot_body, count=1, flags=re.DOTALL)
    else:
        slot_body = re.sub(
            r'(<div[^>]*\bid=["\']proto-pages["\'][^>]*>)',
            rf"\1\n{page_block}",
            slot_body,
            count=1,
            flags=re.I,
        )

    return set_proto_slot(html, slot_body)


def patch_spec_section(html: str, section_id: str, fragment: str) -> str:
    start, end = MARKERS["spec"]
    spec_match = re.search(
        re.escape(start) + r"(.*?)" + re.escape(end), html, flags=re.DOTALL
    )
    if not spec_match:
        raise ValueError("未找到 prdkit:spec 标记区")
    spec_body = spec_match.group(1)
    section_pattern = (
        rf'(<h[23][^>]*\bid=["\']{re.escape(section_id)}["\'][^>]*>.*?)'
        rf'(?=<h[23]\s|<\!--\s*prdkit:spec:end)'
    )
    if re.search(section_pattern, spec_body, flags=re.DOTALL | re.I):
        new_spec = re.sub(section_pattern, fragment.strip() + "\n", spec_body, count=1, flags=re.DOTALL | re.I)
    else:
        new_spec = spec_body.rstrip() + "\n\n" + fragment.strip() + "\n"
    return html[: spec_match.start(1)] + new_spec + html[spec_match.end(1) :]


def cmd_init(args: argparse.Namespace) -> int:
    shell = args.shell
    if shell not in SHELL_BY_NAME:
        print(f"❌ 未知系统壳: {shell}。可选: {', '.join(SHELL_BY_NAME)}", file=sys.stderr)
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    html_path = output_dir / f"{args.basename}.html"

    template = _read_text(resolve("assets/文档输出模板.html"))
    shell_html = _read_text(resolve(SHELL_BY_NAME[shell]))
    html = inject_shell(template, shell_html)
    html = inject_prdkit_assets(html)
    html = re.sub(
        r'(<div class="prd-embed")',
        f'<div class="prd-embed" data-prdkit-shell="{shell}"',
        html,
        count=1,
    )
    html = apply_default_slot_scaffold(html)
    if args.title:
        html = re.sub(r"<title>.*?</title>", f"<title>{args.title}</title>", html, count=1, flags=re.DOTALL)
    _write_text(html_path, html)

    config = {
        "output_dir": str(output_dir).replace("\\", "/"),
        "html_path": str(html_path).replace("\\", "/"),
        "shell": shell,
        "basename": args.basename,
    }
    save_config(config)
    print(f"✅ 已初始化 PRD HTML: {html_path}")
    print(f"✅ 已写入配置: {CONFIG_FILE}")
    return 0


def cmd_set_toc(args: argparse.Namespace) -> int:
    html_path = resolve_html_path(args.html)
    content = _read_text(Path(args.file))
    html = replace_between_markers(_read_text(html_path), "toc", content)
    _write_text(html_path, html)
    print(f"✅ 已更新目录区: {html_path}")
    return 0


def cmd_set_spec(args: argparse.Namespace) -> int:
    html_path = resolve_html_path(args.html)
    fragment = _read_text(Path(args.file))
    html = _read_text(html_path)
    if args.section_id:
        html = patch_spec_section(html, args.section_id, fragment)
    else:
        html = replace_between_markers(html, "spec", fragment)
    _write_text(html_path, html)
    print(f"✅ 已更新说明区: {html_path}" + (f" (#{args.section_id})" if args.section_id else ""))
    return 0


def cmd_set_proto_slot(args: argparse.Namespace) -> int:
    html_path = resolve_html_path(args.html)
    slot_html = _read_text(Path(args.file))
    html = _read_text(html_path)
    if args.validate:
        errors = validate_proto_fragment(slot_html, html)
        if errors:
            raise ValueError("原型片段校验失败:\n- " + "\n- ".join(errors))
    html = set_proto_slot(html, slot_html)
    _write_text(html_path, html)
    print(f"✅ 已更新 #prototype-slot: {html_path}")
    return 0


def cmd_set_proto_page(args: argparse.Namespace) -> int:
    html_path = resolve_html_path(args.html)
    page_html = _read_text(Path(args.file))
    html = _read_text(html_path)
    if args.validate:
        errors = validate_proto_fragment(page_html)
        if errors:
            raise ValueError("原型页面片段校验失败:\n- " + "\n- ".join(errors))
    html = set_proto_page(html, args.tab, page_html, args.label)
    _write_text(html_path, html)
    print(f"✅ 已更新 proto Tab「{args.tab}」: {html_path}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    html_path = resolve_html_path(args.html)
    html = _read_text(html_path)
    errors = validate_html_document(html)
    if errors:
        print(f"❌ {html_path} 校验未通过:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"✅ {html_path} 校验通过")
    return 0


def cmd_check_consistency(args: argparse.Namespace) -> int:
    from prdkit.prd_consistency import INDEX_PATH, format_report, run_check

    html_path = resolve_html_path(args.html)
    index_path = Path(args.index) if args.index else INDEX_PATH
    data = run_check(html_path, index_path, apply=args.fix)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_report(data))
    if data["error_count"] > 0:
        return 1
    if data["issue_count"] > 0 and not args.fix:
        return 1
    return 0


def cmd_show_config(_: argparse.Namespace) -> int:
    config = load_config()
    print(json.dumps(config, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prdkit-html",
        description="PRD HTML 模板合并工具（勿由 Agent 临时编写 Python 拼接脚本）",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    init_p = sub.add_parser("init", help="从模板创建 PRD HTML 并写入 .memory/prd_output.json")
    init_p.add_argument("--output-dir", required=True, help="输出目录（相对项目根，如 prds 或 docs/prd）")
    init_p.add_argument("--basename", required=True, help="HTML 文件名（不含 .html）")
    init_p.add_argument("--shell", required=True, choices=list(SHELL_BY_NAME), help="三系统壳")
    init_p.add_argument("--title", help="可选：页面 <title>")
    init_p.set_defaults(func=cmd_init)

    toc_p = sub.add_parser("set-toc", help="替换左侧目录（prdkit:toc 标记区）")
    toc_p.add_argument("--file", required=True, help="片段 HTML 文件路径")
    toc_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    toc_p.set_defaults(func=cmd_set_toc)

    spec_p = sub.add_parser("set-spec", help="替换/追加说明区章节")
    spec_p.add_argument("--file", required=True, help="片段 HTML 文件路径")
    spec_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    spec_p.add_argument(
        "--section-id",
        help="章节锚点 id（如 sec-1、sec-3-2）；省略则整体替换 spec 区",
    )
    spec_p.set_defaults(func=cmd_set_spec)

    proto_p = sub.add_parser("set-proto-slot", help="替换 slot 标记区内业务原型（单屏或整 Tab 骨架）")
    proto_p.add_argument("--file", required=True, help="片段 HTML 文件路径")
    proto_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    proto_p.add_argument(
        "--no-validate",
        action="store_true",
        help="跳过片段校验（不推荐）",
    )
    proto_p.set_defaults(func=cmd_set_proto_slot, validate=True)

    page_p = sub.add_parser("set-proto-page", help="追加/更新某个 proto Tab 页（推荐多屏）")
    page_p.add_argument("--tab", required=True, help="Tab id（如 audit-list）")
    page_p.add_argument("--label", help="Tab 显示名（默认同 tab id）")
    page_p.add_argument("--file", required=True, help="页面 DOM 片段路径")
    page_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    page_p.add_argument("--no-validate", action="store_true", help="跳过片段校验")
    page_p.set_defaults(func=cmd_set_proto_page, validate=True)

    val_p = sub.add_parser("validate", help="校验 PRD HTML 原型结构（重复 id、非法 slot 等）")
    val_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    val_p.set_defaults(func=cmd_validate)

    chk_p = sub.add_parser(
        "check-consistency",
        help="检查目录/说明/原型三栏一致性（孤儿 Tab、悬空链接、编造占位等）",
    )
    chk_p.add_argument("--html", help="目标 HTML（默认读 prd_output.json）")
    chk_p.add_argument("--index", help="prd_index 路径（默认 .memory/prd_index.md）")
    chk_p.add_argument("--fix", action="store_true", help="应用可安全自动修复后写回 HTML")
    chk_p.add_argument("--json", action="store_true", help="JSON 输出")
    chk_p.set_defaults(func=cmd_check_consistency)

    sub.add_parser("show-config", help="打印 .memory/prd_output.json").set_defaults(func=cmd_show_config)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "no_validate"):
        args.validate = not args.no_validate
    try:
        raise SystemExit(args.func(args))
    except (FileNotFoundError, ValueError) as exc:
        print(f"❌ {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
