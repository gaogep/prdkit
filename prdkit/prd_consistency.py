"""PRD 三栏一致性检查与可安全自动修复项。"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

from prdkit.html_tool import MARKERS, SLOT_END, SLOT_START, replace_between_markers, validate_shell_structure

INDEX_PATH = Path(".memory/prd_index.md")
REPORT_PATH = Path(".memory/prd_check_latest.json")

# 模板占位 / 明显编造（不含已标注 TODO）
FABRICATION_RE = re.compile(
    r"(?:"
    r"测试\s*[12一二]?|"
    r"\b(?:aaa|xxx|foo|bar|asdf|test)\b|"
    r"示例功能点|示例小节|"
    r"^按钮$|^操作$|^字段\d*$"
    r")",
    re.I | re.M,
)

STRUCTURAL_SEC = frozenset({"sec-1", "sec-2", "sec-1-1", "sec-2-1"})

# 说明区为后端/接口/状态机类需求时可不关联原型（见 is_proto_exempt_section）
BACKEND_LOGIC_RE = re.compile(
    r"(?:"
    r"后端逻辑|后端接口|后端服务|"
    r"纯接口|接口调用|接口逻辑|"
    r"状态机|状态变化|状态流转|状态迁移|"
    r"无(?:需|须)?(?:界面|原型|高保真)|"
    r"不(?:需|用|关联|出)(?:原型|界面|高保真)|"
    r"(?:仅|只)(?:后端|服务端|接口)|"
    r"服务端逻辑|"
    r"\bAPI\b|RESTful?|webhook|消息队列|定时任务|批处理"
    r")",
    re.I,
)

PANEL_ORDER = ("toc", "proto", "spec")

SYSTEM_KEYWORDS: dict[str, list[str]] = {
    "催收后台": ["催收后台", "催收系统", "催收平台", "贷后催收", "催收作业"],
    "业务后台": ["业务后台", "运营后台", "支付后台", "订单管理", "风控和金融配置"],
    "质检后台": ["质检后台", "质检系统", "质检平台", "质检作业"],
}

MARKER_IN_PANEL = {
    "toc": MARKERS["toc"][0],
    "spec": MARKERS["spec"][0],
    "proto": SLOT_START,
}


@dataclass
class Issue:
    code: str
    severity: str  # error | warn
    message: str
    auto_fixable: bool = False
    context: dict = field(default_factory=dict)
    letter: str = ""  # 清单编号 A、B、C…（供用户确认后选择性修复）


def _index_to_letter(index: int) -> str:
    """0 → A, 25 → Z, 26 → AA。"""
    n = index + 1
    chars: list[str] = []
    while n:
        n, rem = divmod(n - 1, 26)
        chars.append(chr(65 + rem))
    return "".join(reversed(chars))


def assign_issue_letters(issues: list[Issue]) -> list[Issue]:
    ordered = sorted(issues, key=lambda i: (0 if i.severity == "error" else 1, i.code, i.message))
    return [replace(it, letter=_index_to_letter(i)) for i, it in enumerate(ordered)]


def parse_fix_letters(text: str) -> set[str]:
    """解析用户输入：B C D / B,C,D / 全部 / all。"""
    raw = text.strip()
    if not raw:
        return set()
    if raw.lower() in {"全部", "all", "*"}:
        return set()  # 空集表示「全部可自动修」
    parts = re.split(r"[\s,，、;；]+", raw.upper())
    return {p.strip() for p in parts if re.fullmatch(r"[A-Z]{1,3}", p.strip())}


def save_check_report(data: dict, cwd: Path | None = None) -> Path:
    base = cwd or Path.cwd()
    path = base / REPORT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _between(html: str, start: str, end: str) -> str:
    m = re.search(re.escape(start) + r"(.*?)" + re.escape(end), html, flags=re.DOTALL | re.I)
    return m.group(1) if m else ""


def extract_regions(html: str) -> dict[str, str]:
    toc_s, toc_e = MARKERS["toc"]
    spec_s, spec_e = MARKERS["spec"]
    return {
        "toc": _between(html, toc_s, toc_e),
        "spec": _between(html, spec_s, spec_e),
        "slot": _between(html, SLOT_START, SLOT_END),
    }


def extract_proto_tabs(slot: str) -> dict[str, str]:
    """tab_id -> label（按钮文案优先）。"""
    tabs: dict[str, str] = {}
    for tab, label in re.findall(
        r'<button[^>]*\bdata-tab=["\']([^"\']+)["\'][^>]*>([^<]*)</button>',
        slot,
        flags=re.I | re.DOTALL,
    ):
        tabs[tab.strip()] = re.sub(r"\s+", " ", label).strip() or tab.strip()
    for tab in re.findall(r'\bdata-proto-page=["\']([^"\']+)["\']', slot, flags=re.I):
        tid = tab.strip()
        tabs.setdefault(tid, tid)
    return tabs


def extract_toc_links(toc: str) -> list[dict[str, str]]:
    links = []
    for m in re.finditer(
        r'<a\s+([^>]*?)>([^<]*)</a>',
        toc,
        flags=re.I | re.DOTALL,
    ):
        attrs, text = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
        href_m = re.search(r'href=["\']#([^"\']+)["\']', attrs, re.I)
        tab_m = re.search(r'data-proto-tab=["\']([^"\']+)["\']', attrs, re.I)
        if href_m:
            links.append(
                {
                    "sec_id": href_m.group(1).strip(),
                    "text": text,
                    "proto_tab": tab_m.group(1).strip() if tab_m else "",
                }
            )
    return links


def extract_spec_sections(spec: str) -> list[dict[str, str]]:
    headings = list(
        re.finditer(
            r'<h([23])[^>]*\bid=["\']([^"\']+)["\'][^>]*>([^<]*)</h\1>',
            spec,
            flags=re.I,
        )
    )
    sections: list[dict[str, str]] = []
    for i, m in enumerate(headings):
        sec_id = m.group(2).strip()
        body = spec[m.end() : headings[i + 1].start() if i + 1 < len(headings) else len(spec)]
        proto_tabs: set[str] = set()
        for ref in re.findall(
            r'class=["\']proto-ref["\'][^>]*>.*?Tab[：:]\s*(?:<strong>)?([^<*]+)',
            body,
            flags=re.I | re.DOTALL,
        ):
            proto_tabs.add(ref.strip())
        for ref in re.findall(r'data-proto-tab=["\']([^"\']+)["\']', body, re.I):
            proto_tabs.add(ref.strip())
        sections.append(
            {
                "sec_id": sec_id,
                "title": re.sub(r"\s+", " ", m.group(3)).strip(),
                "proto_tabs": sorted(proto_tabs),
                "body": body,
            }
        )
    return sections


def extract_spec_ids(spec: str) -> set[str]:
    return {m.strip() for m in re.findall(r'\bid=["\']([^"\']+)["\']', spec, flags=re.I)}


def parse_index_features(index_text: str) -> list[str]:
    if not index_text.strip():
        return []
    lines = index_text.splitlines()
    in_features = False
    names: list[str] = []
    for line in lines:
        if re.match(r"^#+\s*功能说明", line) or re.match(r"^3\.?\s*\*?\*?功能说明", line):
            in_features = True
            continue
        if in_features and re.match(r"^#+\s+", line) and "功能说明" not in line:
            break
        m = re.match(r"^\s*[-*]\s+\[[ xX]\]\s+(.+)$", line)
        if in_features and m:
            names.append(m.group(1).strip())
    return names


def _tab_label_match(tab_id: str, label: str, ref: str) -> bool:
    ref_l = ref.lower().strip()
    return ref_l == tab_id.lower() or ref_l == label.lower() or ref_l in label.lower()


def _section_plain_text(sec: dict[str, str]) -> str:
    body_plain = re.sub(r"<[^>]+>", " ", sec.get("body", ""))
    return f"{sec.get('title', '')}\n{body_plain}"


def is_proto_exempt_section(sec: dict[str, str]) -> bool:
    """后端逻辑 / 纯接口 / 状态变化等说明节，允许无 proto-ref、无 Tab 绑定。"""
    body = sec.get("body", "")
    if re.search(r'\bclass=["\'][^"\']*\bproto-exempt\b', body, flags=re.I):
        return True
    if re.search(r'\bdata-proto-exempt=["\']true["\']', body, flags=re.I):
        return True
    if "prdkit:proto-exempt" in body:
        return True
    text = _section_plain_text(sec)
    if re.search(r"本(?:节|功能|需求)?[^。\n]{0,40}(?:无需|不需|不用)(?:原型|界面|高保真)", text, re.I):
        return True
    return bool(BACKEND_LOGIC_RE.search(text))


def _panel_open_positions(html: str) -> dict[str, int]:
    positions: dict[str, int] = {}
    for panel in PANEL_ORDER:
        m = re.search(
            rf'<(?:aside|section)\b[^>]*\bdata-panel=["\']{panel}["\']',
            html,
            flags=re.I,
        )
        if m:
            positions[panel] = m.start()
    return positions


def _panel_span(html: str, panel: str) -> tuple[int, int] | None:
    m = re.search(
        rf'<(?:aside|section)\b[^>]*\bdata-panel=["\']{panel}["\']',
        html,
        flags=re.I,
    )
    if not m:
        return None
    start = m.start()
    others = []
    for other in PANEL_ORDER:
        if other == panel:
            continue
        nm = re.search(rf'\bdata-panel=["\']{other}["\']', html[m.end() :], flags=re.I)
        if nm:
            others.append(m.end() + nm.start())
    end = min(others) if others else len(html)
    return start, end


def check_layout_issues(html: str) -> list[Issue]:
    """三栏 DOM 顺序与标记区是否落在正确面板。"""
    issues: list[Issue] = []
    positions = _panel_open_positions(html)

    if len(positions) < 3:
        missing = [p for p in PANEL_ORDER if p not in positions]
        issues.append(
            Issue(
                code="LAYOUT_PANEL_MISSING",
                severity="error",
                message=f'缺少三栏面板 data-panel={"/".join(missing)}，页面布局已损坏',
                auto_fixable=False,
                context={"missing": missing},
            )
        )
        return issues

    toc_pos, proto_pos, spec_pos = (
        positions["toc"],
        positions["proto"],
        positions["spec"],
    )
    if not (toc_pos < proto_pos < spec_pos):
        issues.append(
            Issue(
                code="LAYOUT_PANEL_ORDER",
                severity="error",
                message="三栏顺序错误：应为 目录(toc) → 原型(proto) → 说明(spec)",
                auto_fixable=False,
                context={"positions": positions},
            )
        )
        if toc_pos > proto_pos:
            issues.append(
                Issue(
                    code="LAYOUT_TOC_POSITION",
                    severity="error",
                    message="目录区位置不对：须在原型区左侧（data-panel=toc 应在 proto 之前）",
                    auto_fixable=False,
                )
            )
        if proto_pos > spec_pos:
            issues.append(
                Issue(
                    code="LAYOUT_PROTO_POSITION",
                    severity="error",
                    message="原型区位置不对：须在说明区左侧（data-panel=proto 应在 spec 之前）",
                    auto_fixable=False,
                )
            )
        if spec_pos < proto_pos:
            issues.append(
                Issue(
                    code="LAYOUT_SPEC_POSITION",
                    severity="error",
                    message="说明区位置不对：须在最右侧（data-panel=spec 应在 proto 之后）",
                    auto_fixable=False,
                )
            )

    for err in validate_shell_structure(html):
        if "spec" in err and ("之外" in err or "shell" in err.lower()):
            issues.append(
                Issue(
                    code="LAYOUT_SPEC_OUTSIDE_SHELL",
                    severity="error",
                    message=err,
                    auto_fixable=False,
                )
            )

    for panel, marker in MARKER_IN_PANEL.items():
        pos = html.find(marker)
        if pos < 0:
            continue
        span = _panel_span(html, panel)
        if span and not (span[0] <= pos < span[1]):
            label = {"toc": "目录", "proto": "原型", "spec": "说明"}[panel]
            issues.append(
                Issue(
                    code=f"LAYOUT_{panel.upper()}_WRONG_PANEL",
                    severity="error",
                    message=f"{label}内容标记不在 data-panel={panel} 面板内（{marker} 位置错乱）",
                    auto_fixable=False,
                    context={"panel": panel, "marker": marker},
                )
            )

    return issues


def _read_declared_shell(html: str) -> str | None:
    m = re.search(
        r'\bdata-prdkit-shell=["\'](业务后台|催收后台|质检后台)["\']',
        html,
        flags=re.I,
    )
    return m.group(1).strip() if m else None


def detect_embedded_shell(html: str) -> str | None:
    """根据注入壳 DOM/CSS 指纹推断实际壳（与 init 注入一致）。"""
    proto_s, proto_e = MARKERS["proto"]
    embed = _between(html, proto_s, proto_e)
    if not embed.strip():
        embed = html
    window = embed[:12000]
    has_layout = "app-layout" in window
    has_sidebar = "app-sidebar" in window
    if "app-header" in window and not has_layout:
        return "催收后台"
    if has_sidebar:
        if "#001529" in window or "sidebar-bg: #001529" in window:
            return "业务后台"
        if "sidebar-bg: #ffffff" in window or "--sidebar-text: #409eff" in window:
            return "质检后台"
    declared = _read_declared_shell(html)
    return declared


def infer_expected_shell(
    index_text: str = "",
    brief_text: str = "",
    config_shell: str | None = None,
) -> str | None:
    if config_shell in SYSTEM_KEYWORDS:
        return config_shell
    combined = f"{brief_text}\n{index_text}"
    scores = {shell: sum(1 for kw in kws if kw in combined) for shell, kws in SYSTEM_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores.get(best, 0) > 0 else None


def infer_system_from_text(*texts: str) -> dict[str, int]:
    combined = "\n".join(texts)
    return {shell: sum(1 for kw in kws if kw in combined) for shell, kws in SYSTEM_KEYWORDS.items()}


def check_shell_alignment(
    html: str,
    *,
    expected_shell: str | None = None,
    index_text: str = "",
    brief_text: str = "",
) -> list[Issue]:
    issues: list[Issue] = []
    declared = _read_declared_shell(html)
    actual = detect_embedded_shell(html)
    expected = expected_shell or infer_expected_shell(index_text, brief_text, declared)

    if not actual:
        issues.append(
            Issue(
                code="SHELL_UNDETECTED",
                severity="warn",
                message="无法从原型区识别系统壳，请确认已 prdkit-html init 并注入壳",
                auto_fixable=False,
            )
        )
        return issues

    if declared and actual and declared != actual:
        issues.append(
            Issue(
                code="SHELL_DOM_MISMATCH",
                severity="error",
                message=f'data-prdkit-shell="{declared}" 与壳 DOM 指纹不一致（实测为 {actual}）',
                auto_fixable=False,
                context={"declared": declared, "actual": actual},
            )
        )

    if expected and actual != expected:
        issues.append(
            Issue(
                code="SHELL_WRONG_SYSTEM",
                severity="error",
                message=f"应用壳应为「{expected}」，当前原型为「{actual}」",
                auto_fixable=False,
                context={"expected": expected, "actual": actual},
            )
        )

    regions = extract_regions(html)
    text_scores = infer_system_from_text(index_text, brief_text, regions["spec"], regions["toc"])
    dominant = max(text_scores, key=text_scores.get) if any(text_scores.values()) else None
    if dominant and text_scores[dominant] >= 2 and actual != dominant:
        issues.append(
            Issue(
                code="SHELL_TEXT_MISMATCH",
                severity="error",
                message=f"目录/说明多处提及「{dominant}」，但 init 壳为「{actual}」",
                auto_fixable=False,
                context={"text_system": dominant, "actual": actual},
            )
        )

    slot = regions["slot"]
    if actual == "业务后台" and re.search(r"sidebar-nav|顶栏.*横菜单|催收作业", slot, re.I):
        issues.append(
            Issue(
                code="SHELL_SLOT_WRONG_CHROME",
                severity="error",
                message="业务后台壳的 slot 内出现催收式顶栏/菜单（禁止在 slot 手绘另一系统壳）",
                auto_fixable=False,
            )
        )
    if actual == "催收后台" and "app-sidebar" in slot:
        issues.append(
            Issue(
                code="SHELL_SLOT_WRONG_CHROME",
                severity="error",
                message="催收后台壳的 slot 内出现侧栏 .app-sidebar（禁止嵌业务/质检壳）",
                auto_fixable=False,
            )
        )

    return issues


def check_consistency(
    html: str,
    index_text: str = "",
    *,
    expected_shell: str | None = None,
    brief_text: str = "",
) -> list[Issue]:
    regions = extract_regions(html)
    proto_tabs = extract_proto_tabs(regions["slot"])
    proto_tab_ids = set(proto_tabs)
    toc_links = extract_toc_links(regions["toc"])
    spec_sections = extract_spec_sections(regions["spec"])
    spec_ids = extract_spec_ids(regions["spec"])
    sec_by_id = {s["sec_id"]: s for s in spec_sections}

    toc_sec_ids = {ln["sec_id"] for ln in toc_links}
    sec_to_toc_tab: dict[str, str] = {ln["sec_id"]: ln["proto_tab"] for ln in toc_links if ln["proto_tab"]}

    spec_refs_all: set[str] = set()
    proto_exempt_secs: set[str] = set()
    for sec in spec_sections:
        spec_refs_all.update(sec["proto_tabs"])
        if is_proto_exempt_section(sec):
            proto_exempt_secs.add(sec["sec_id"])

    issues: list[Issue] = []

    # 1. 原型 Tab 在说明/目录无对应
    for tab_id, label in proto_tabs.items():
        in_toc = tab_id in {ln["proto_tab"] for ln in toc_links if ln["proto_tab"]}
        in_spec = any(_tab_label_match(tab_id, label, r) for r in spec_refs_all)
        if not in_toc and not in_spec:
            issues.append(
                Issue(
                    code="PROTO_WITHOUT_SPEC_TOC",
                    severity="error",
                    message=f'原型 Tab「{label}」({tab_id}) 在说明区无 proto-ref、目录无 data-proto-tab',
                    auto_fixable=False,
                    context={"tab_id": tab_id, "label": label},
                )
            )

    # 2. 目录项悬空
    for ln in toc_links:
        if ln["sec_id"] not in spec_ids:
            issues.append(
                Issue(
                    code="TOC_ORPHAN_SEC",
                    severity="error",
                    message=f'目录「{ln["text"]}」指向 #{ln["sec_id"]}，说明区无此锚点',
                    auto_fixable=True,
                    context=ln,
                )
            )
        if ln["proto_tab"] and ln["proto_tab"] not in proto_tab_ids:
            issues.append(
                Issue(
                    code="TOC_ORPHAN_TAB",
                    severity="error",
                    message=f'目录「{ln["text"]}」data-proto-tab="{ln["proto_tab"]}" 在原型中不存在',
                    auto_fixable=True,
                    context=ln,
                )
            )
        if ln["proto_tab"] and ln["sec_id"] in proto_exempt_secs:
            issues.append(
                Issue(
                    code="TOC_PROTO_ON_EXEMPT_SEC",
                    severity="warn",
                    message=f'目录「{ln["text"]}」为后端/接口类说明，不应设 data-proto-tab',
                    auto_fixable=True,
                    context=ln,
                )
            )

    # 3. 说明节悬空 / proto-ref 无效
    for sec in spec_sections:
        sid = sec["sec_id"]
        proto_exempt = sid in proto_exempt_secs
        if sid.startswith("sec-3") and sid not in toc_sec_ids and sid not in STRUCTURAL_SEC:
            issues.append(
                Issue(
                    code="SPEC_WITHOUT_TOC",
                    severity="warn",
                    message=f'说明「{sec["title"]}」(#{sid}) 在目录无链接',
                    auto_fixable=True,
                    context={"sec_id": sid, "title": sec["title"]},
                )
            )
        for ref in sec["proto_tabs"]:
            if proto_tab_ids and not any(
                _tab_label_match(tid, proto_tabs[tid], ref) for tid in proto_tab_ids
            ):
                issues.append(
                    Issue(
                        code="SPEC_ORPHAN_PROTO_REF",
                        severity="error",
                        message=f'说明 #{sid} 指向原型 Tab「{ref}」，但 slot 中无对应 Tab',
                        auto_fixable=True,
                        context={"sec_id": sid, "ref": ref},
                    )
                )
        toc_tab = sec_to_toc_tab.get(sid, "")
        if not proto_exempt and toc_tab and not sec["proto_tabs"]:
            issues.append(
                Issue(
                    code="SPEC_MISSING_PROTO_REF",
                    severity="error",
                    message=f'说明 #{sid} 目录已绑 Tab「{toc_tab}」，正文缺少 proto-ref',
                    auto_fixable=True,
                    context={
                        "sec_id": sid,
                        "tab_id": toc_tab,
                        "label": proto_tabs.get(toc_tab, toc_tab),
                    },
                )
            )
        elif (
            not proto_exempt
            and sid.startswith("sec-3")
            and proto_tab_ids
            and not sec["proto_tabs"]
            and not toc_tab
            and sid != "sec-3"
            and not any(s["sec_id"].startswith(sid + "-") for s in spec_sections)
        ):
            issues.append(
                Issue(
                    code="SPEC_MISSING_PROTO_REF",
                    severity="warn",
                    message=f'功能说明 #{sid}「{sec["title"]}」未关联任何原型 Tab',
                    auto_fixable=False,
                    context={"sec_id": sid},
                )
            )

    # 目录有 tab 但说明无 proto-ref（与上互补：按 toc 查）
    for ln in toc_links:
        if not ln["proto_tab"] or ln["sec_id"] not in sec_by_id:
            continue
        if ln["sec_id"] in proto_exempt_secs:
            continue
        sec = sec_by_id[ln["sec_id"]]
        if not any(_tab_label_match(ln["proto_tab"], proto_tabs.get(ln["proto_tab"], ""), r) for r in sec["proto_tabs"]):
            issues.append(
                Issue(
                    code="SPEC_MISSING_PROTO_REF",
                    severity="error",
                    message=f'目录 #{ln["sec_id"]} 已设 data-proto-tab="{ln["proto_tab"]}"，说明区缺少 proto-ref',
                    auto_fixable=True,
                    context={
                        "sec_id": ln["sec_id"],
                        "tab_id": ln["proto_tab"],
                        "label": proto_tabs.get(ln["proto_tab"], ln["proto_tab"]),
                    },
                )
            )

    # 4. 编造 / 模板占位
    for region_name, body in regions.items():
        if not body.strip():
            continue
        for m in FABRICATION_RE.finditer(body):
            snippet = m.group(0)
            start = max(0, m.start() - 40)
            window = body[start : m.end() + 40]
            if "[TODO" in window or "{待填写}" in window:
                continue
            issues.append(
                Issue(
                    code="POSSIBLE_FABRICATION",
                    severity="warn",
                    message=f"{region_name} 区含可疑占位「{snippet}」",
                    auto_fixable=True,
                    context={"region": region_name, "match": snippet},
                )
            )

    issues.extend(check_layout_issues(html))
    issues.extend(
        check_shell_alignment(
            html,
            expected_shell=expected_shell,
            index_text=index_text,
            brief_text=brief_text,
        )
    )

    # index 与 HTML 粗对齐
    for name in parse_index_features(index_text):
        if name and name not in regions["spec"] and name not in regions["toc"]:
            issues.append(
                Issue(
                    code="INDEX_NOT_IN_HTML",
                    severity="warn",
                    message=f'prd_index 功能项「{name}」未出现在目录或说明正文',
                    auto_fixable=False,
                    context={"feature": name},
                )
            )

    # 去重（同 code + message）
    seen: set[tuple[str, str]] = set()
    unique: list[Issue] = []
    for it in issues:
        key = (it.code, it.message)
        if key not in seen:
            seen.add(key)
            unique.append(it)
    return unique


def _proto_ref_html(label: str) -> str:
    return f'<p class="proto-ref">见中原型 → Tab：<strong>{label}</strong></p>\n'


def apply_fixes(html: str, issues: list[Issue]) -> tuple[str, list[str]]:
    """仅应用结构性安全修复；编造项改为 [TODO] 需人工复核。"""
    applied: list[str] = []
    regions = extract_regions(html)
    spec = regions["spec"]
    toc = regions["toc"]
    proto_tabs = extract_proto_tabs(regions["slot"])

    fixable = [i for i in issues if i.auto_fixable]
    if not fixable:
        return html, applied

    # SPEC_MISSING_PROTO_REF：在对应 h2/h3 后插入 proto-ref
    for issue in fixable:
        if issue.code != "SPEC_MISSING_PROTO_REF":
            continue
        sid = issue.context.get("sec_id")
        label = issue.context.get("label") or issue.context.get("tab_id", "")
        if not sid or not label:
            continue
        pat = rf'(<h[23][^>]*\bid=["\']{re.escape(sid)}["\'][^>]*>[^<]*</h[23]>)'
        m = re.search(pat, spec, flags=re.I)
        if not m:
            continue
        after = spec[m.end() : m.end() + 280]
        if "proto-ref" in after:
            continue
        spec = spec[: m.end()] + "\n" + _proto_ref_html(label) + spec[m.end() :]
        applied.append(f"已在 #{sid} 下插入 proto-ref → {label}")

    # TOC_PROTO_ON_EXEMPT_SEC：去掉后端说明节上的 data-proto-tab
    for issue in fixable:
        if issue.code != "TOC_PROTO_ON_EXEMPT_SEC":
            continue
        sid = issue.context.get("sec_id", "")
        if sid:
            toc = re.sub(
                rf'(<a\s+[^>]*href=["\']#{re.escape(sid)}["\'][^>]*)'
                r'\s*data-proto-tab=["\'][^"\']+["\']',
                r"\1",
                toc,
                count=1,
                flags=re.I,
            )
            applied.append(f"已移除 #{sid} 目录项上的 data-proto-tab（后端/接口类说明）")

    # TOC：补 data-proto-tab
    for issue in fixable:
        if issue.code != "SPEC_MISSING_PROTO_REF":
            continue
        sid, tab_id = issue.context.get("sec_id"), issue.context.get("tab_id")
        if not sid or not tab_id:
            continue
        toc = re.sub(
            rf'(<a\s+)([^>]*href=["\']#{re.escape(sid)}["\'][^>]*)>',
            lambda m: (
                m.group(1) + m.group(2) + ("" if "data-proto-tab" in m.group(2) else f' data-proto-tab="{tab_id}"') + ">"
            ),
            toc,
            count=1,
            flags=re.I,
        )

    # TOC_ORPHAN_TAB：去掉无效 data-proto-tab
    for issue in fixable:
        if issue.code != "TOC_ORPHAN_TAB":
            continue
        tab = issue.context.get("proto_tab", "")
        toc = re.sub(rf'\s*data-proto-tab=["\']{re.escape(tab)}["\']', "", toc, flags=re.I)

    # TOC_ORPHAN_SEC：删除指向不存在 sec 的 <li>
    for issue in fixable:
        if issue.code != "TOC_ORPHAN_SEC":
            continue
        sid = issue.context.get("sec_id", "")
        toc = re.sub(
            rf"<li>\s*<a\s+[^>]*href=[\"']#{re.escape(sid)}[\"'][^>]*>.*?</a>\s*</li>\s*",
            "",
            toc,
            flags=re.DOTALL | re.I,
        )
        applied.append(f"已删除目录中无效链接 #{sid}")

    # SPEC_ORPHAN_PROTO_REF：删除错误 proto-ref 行
    for issue in fixable:
        if issue.code != "SPEC_ORPHAN_PROTO_REF":
            continue
        ref = issue.context.get("ref", "")
        spec = re.sub(
            rf'<p\s+class=["\']proto-ref["\'][^>]*>.*?{re.escape(ref)}.*?</p>\s*',
            "",
            spec,
            flags=re.I | re.DOTALL,
        )
        applied.append(f"已删除说明区无效 proto-ref「{ref}」")

    # POSSIBLE_FABRICATION：仅替换模板级占位
    for issue in fixable:
        if issue.code != "POSSIBLE_FABRICATION":
            continue
        match = issue.context.get("match", "")
        region = issue.context.get("region", "spec")
        if match in ("示例功能点", "示例小节"):
            todo = "[TODO: 填写真实功能名称]"
            if region == "spec":
                spec = spec.replace(match, todo)
            elif region == "toc":
                toc = toc.replace(match, todo)
            applied.append(f"已将「{match}」改为 {todo}")

    html = replace_between_markers(html, "spec", spec)
    html = replace_between_markers(html, "toc", toc)
    return html, applied


def _load_project_context(cwd: Path | None = None) -> tuple[str | None, str, str]:
    base = cwd or Path.cwd()
    config_shell: str | None = None
    index_text = ""
    brief_text = ""
    config_path = base / ".memory/prd_output.json"
    if config_path.is_file():
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            config_shell = data.get("shell")
        except json.JSONDecodeError:
            pass
    index_path = base / INDEX_PATH
    if index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8")
    brief_path = base / ".memory/product_brief.md"
    if brief_path.is_file():
        brief_text = brief_path.read_text(encoding="utf-8")
    return config_shell, index_text, brief_text


def run_check(
    html_path: Path,
    index_path: Path | None = None,
    apply: bool = False,
    fix_letters: str | None = None,
    cwd: Path | None = None,
) -> dict:
    html = html_path.read_text(encoding="utf-8")
    config_shell, index_default, brief_text = _load_project_context(cwd)
    index_text = index_default
    if index_path and index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8")
    issues = assign_issue_letters(
        check_consistency(
            html,
            index_text,
            expected_shell=config_shell,
            brief_text=brief_text,
        )
    )
    applied: list[str] = []
    fixed_letters: list[str] = []
    if apply or fix_letters:
        selected = parse_fix_letters(fix_letters or "")
        if apply and not fix_letters:
            to_fix = [i for i in issues if i.auto_fixable]
        elif not selected:
            to_fix = [i for i in issues if i.auto_fixable]
        else:
            to_fix = [i for i in issues if i.letter in selected and i.auto_fixable]
            skipped = selected - {i.letter for i in to_fix}
            manual = [i for i in issues if i.letter in selected and not i.auto_fixable]
            if skipped:
                applied.append(f"跳过无匹配或不可自动修编号: {', '.join(sorted(skipped))}")
            if manual:
                applied.append(
                    "需人工处理编号: "
                    + ", ".join(f"{i.letter}({i.code})" for i in manual)
                )
        if to_fix:
            html, fix_msgs = apply_fixes(html, to_fix)
            html_path.write_text(html, encoding="utf-8")
            applied.extend(fix_msgs)
            fixed_letters = [i.letter for i in to_fix]
            issues = assign_issue_letters(
                check_consistency(
                    html,
                    index_text,
                    expected_shell=config_shell,
                    brief_text=brief_text,
                )
            )
    data = {
        "html_path": str(html_path),
        "issue_count": len(issues),
        "error_count": sum(1 for i in issues if i.severity == "error"),
        "issues": [asdict(i) for i in issues],
        "applied_fixes": applied,
        "fixed_letters": fixed_letters,
        "report_path": str((cwd or Path.cwd()) / REPORT_PATH),
    }
    save_check_report(data, cwd)
    return data


def format_report(data: dict) -> str:
    lines = [
        f"PRD 一致性检查: {data['html_path']}",
        f"问题 {data['issue_count']}（error {data['error_count']}）",
    ]
    if data.get("applied_fixes"):
        lines.append("已自动修复:")
        for a in data["applied_fixes"]:
            lines.append(f"  - {a}")
    issues = data.get("issues") or []
    if issues:
        lines.append("")
        lines.append("异常清单（请确认要修复的编号）:")
        for it in issues:
            flag = "❌" if it["severity"] == "error" else "⚠️"
            letter = it.get("letter") or "?"
            fix = " [可自动修复]" if it.get("auto_fixable") else " [需人工]"
            lines.append(f"{letter}. {flag} [{it['code']}] {it['message']}{fix}")
        auto_letters = [it["letter"] for it in issues if it.get("auto_fixable") and it.get("letter")]
        if auto_letters:
            lines.append("")
            lines.append(
                "回复要修复的编号（空格或逗号分隔），例如: "
                + " ".join(auto_letters[:5])
                + (" …" if len(auto_letters) > 5 else "")
            )
            lines.append("或: 全部 / all — 修复所有可自动修项")
            lines.append(f"CLI: prdkit-html check-consistency --fix-letters {','.join(auto_letters[:3])}")
    else:
        lines.append("未发现异常。")
    return "\n".join(lines)
