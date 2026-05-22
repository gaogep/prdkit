"""PRD 三栏一致性检查与可安全自动修复项。"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from prdkit.html_tool import MARKERS, SLOT_END, SLOT_START, replace_between_markers

INDEX_PATH = Path(".memory/prd_index.md")

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


@dataclass
class Issue:
    code: str
    severity: str  # error | warn
    message: str
    auto_fixable: bool = False
    context: dict = field(default_factory=dict)


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


def check_consistency(html: str, index_text: str = "") -> list[Issue]:
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
    for sec in spec_sections:
        spec_refs_all.update(sec["proto_tabs"])

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

    # 3. 说明节悬空 / proto-ref 无效
    for sec in spec_sections:
        sid = sec["sec_id"]
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
        if toc_tab and not sec["proto_tabs"]:
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
            sid.startswith("sec-3")
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


def run_check(html_path: Path, index_path: Path | None = None, apply: bool = False) -> dict:
    html = html_path.read_text(encoding="utf-8")
    index_text = ""
    if index_path and index_path.is_file():
        index_text = index_path.read_text(encoding="utf-8")
    issues = check_consistency(html, index_text)
    applied: list[str] = []
    if apply and issues:
        html, applied = apply_fixes(html, issues)
        html_path.write_text(html, encoding="utf-8")
        issues = check_consistency(html, index_text)
    return {
        "html_path": str(html_path),
        "issue_count": len(issues),
        "error_count": sum(1 for i in issues if i.severity == "error"),
        "issues": [asdict(i) for i in issues],
        "applied_fixes": applied,
    }


def format_report(data: dict) -> str:
    lines = [
        f"PRD 一致性检查: {data['html_path']}",
        f"问题 {data['issue_count']}（error {data['error_count']}）",
    ]
    if data.get("applied_fixes"):
        lines.append("已自动修复:")
        for a in data["applied_fixes"]:
            lines.append(f"  - {a}")
    for it in data["issues"]:
        flag = "❌" if it["severity"] == "error" else "⚠️"
        fix = " [可自动修复]" if it.get("auto_fixable") else ""
        lines.append(f"{flag} [{it['code']}] {it['message']}{fix}")
    return "\n".join(lines)
