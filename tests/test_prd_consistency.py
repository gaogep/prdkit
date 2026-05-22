"""prd-check / check-consistency 测试。"""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from prdkit.html_tool import apply_default_slot_scaffold, inject_prdkit_assets, inject_shell, replace_between_markers, set_proto_slot  # noqa: E402
from prdkit.paths import resolve  # noqa: E402
from prdkit.prd_consistency import (  # noqa: E402
    apply_fixes,
    check_consistency,
    check_layout_issues,
    check_shell_alignment,
    detect_embedded_shell,
    extract_proto_tabs,
)


def _minimal_prd_html() -> str:
    template = (ROOT / "prdkit/data/assets/文档输出模板.html").read_text(encoding="utf-8")
    shell = (ROOT / "prdkit/data/assets/业务后台-原型壳.html").read_text(encoding="utf-8")
    html = inject_shell(template, shell)
    html = inject_prdkit_assets(html)
    html = re.sub(
        r'(<div class="prd-embed")',
        r'<div class="prd-embed" data-prdkit-shell="业务后台"',
        html,
        count=1,
    )
    html = apply_default_slot_scaffold(html)
    toc = """<ul class="toc-tree">
<li><a class="toc-l1" href="#sec-3">3 功能说明</a>
<ul><li><a href="#sec-3-1" data-proto-tab="audit">3.1 平账审核</a></li></ul></li>
</ul>"""
    spec = """<h2 id="sec-3">3 功能说明</h2>
<h3 id="sec-3-1">3.1 平账审核</h3>
<p>规则说明。</p>"""
    slot = """<div class="proto-shell" id="proto-root">
<div class="proto-tabs"><button type="button" class="proto-tab" data-tab="audit">平账审核</button></div>
<div class="proto-pages"><div class="proto-page" data-proto-page="audit" hidden><div class="proto-list-page">x</div></div></div>
</div>"""
    html = replace_between_markers(html, "toc", toc)
    html = replace_between_markers(html, "spec", spec)
    html = set_proto_slot(html, slot)
    return html


class PrdConsistencyTests(unittest.TestCase):
    def test_missing_proto_ref_detected(self):
        html = _minimal_prd_html()
        issues = check_consistency(html)
        codes = {i.code for i in issues}
        self.assertIn("SPEC_MISSING_PROTO_REF", codes)

    def test_auto_fix_inserts_proto_ref(self):
        html = _minimal_prd_html()
        issues = check_consistency(html)
        fixed, applied = apply_fixes(html, issues)
        self.assertTrue(applied)
        self.assertIn("proto-ref", fixed)
        after = check_consistency(fixed)
        self.assertFalse(any(i.code == "SPEC_MISSING_PROTO_REF" for i in after))

    def test_extract_proto_tabs(self):
        slot = '<button data-tab="a">A</button><div data-proto-page="a"></div>'
        self.assertEqual(extract_proto_tabs(slot)["a"], "A")

    def test_layout_order_ok(self):
        html = _minimal_prd_html()
        self.assertEqual(check_layout_issues(html), [])

    def test_layout_wrong_panel_order(self):
        bad = (
            '<div class="prd-shell" id="prd-shell">'
            '<aside class="panel panel-spec" data-panel="spec"></aside>'
            '<section class="panel panel-proto" data-panel="proto"></section>'
            '<aside class="panel panel-toc" data-panel="toc"></aside>'
            "</div>"
        )
        codes = {i.code for i in check_layout_issues(bad)}
        self.assertIn("LAYOUT_PANEL_ORDER", codes)
        self.assertIn("LAYOUT_TOC_POSITION", codes)

    def test_shell_detect_business(self):
        html = _minimal_prd_html()
        self.assertEqual(detect_embedded_shell(html), "业务后台")

    def test_shell_wrong_system(self):
        html = _minimal_prd_html()
        issues = check_shell_alignment(
            html,
            expected_shell="催收后台",
            index_text="催收后台\n贷后催收",
            brief_text="",
        )
        self.assertTrue(any(i.code == "SHELL_WRONG_SYSTEM" for i in issues))


if __name__ == "__main__":
    unittest.main()
