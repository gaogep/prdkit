"""prdkit-html 合并工具测试。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from prdkit.html_tool import (  # noqa: E402
    SLOT_END,
    SLOT_START,
    embed_logo_in_html,
    inject_shell,
    inject_prdkit_assets,
    load_logo_data_uri,
    apply_default_slot_scaffold,
    patch_spec_section,
    replace_between_markers,
    scope_shell_styles,
    set_proto_page,
    set_proto_slot,
    validate_html_document,
    validate_proto_fragment,
    validate_proto_list_layout,
    validate_proto_list_spec231,
    validate_proto_tabs,
    validate_shell_structure,
)
from prdkit.paths import resolve  # noqa: E402


class HtmlToolTests(unittest.TestCase):
    def test_replace_between_markers(self) -> None:
        html = "<!-- prdkit:toc:start -->\nold\n<!-- prdkit:toc:end -->"
        out = replace_between_markers(html, "toc", "<div>new</div>")
        self.assertIn("new", out)
        self.assertNotIn("old", out)

    def test_patch_spec_section(self) -> None:
        html = (
            "<!-- prdkit:spec:start -->\n"
            '<h2 id="sec-1">旧</h2>\n'
            '<h2 id="sec-2">其他</h2>\n'
            "<!-- prdkit:spec:end -->"
        )
        frag = '<h2 id="sec-1">新标题</h2>\n<p>新正文</p>'
        out = patch_spec_section(html, "sec-1", frag)
        self.assertIn("新正文", out)
        self.assertIn('id="sec-2"', out)
        self.assertNotIn("旧</h2>", out)

    def test_init_injects_shell(self) -> None:
        template = resolve("assets/文档输出模板.html").read_text(encoding="utf-8")
        shell = resolve("assets/催收后台-原型壳.html").read_text(encoding="utf-8")
        out = inject_shell(template, shell)
        self.assertIn("催收后台", out)
        self.assertIn('id="prototype-slot"', out)
        self.assertIn("data-prdkit-shell", out)
        self.assertIn(SLOT_START, out)

    def test_embed_logo_replaces_src(self) -> None:
        uri = load_logo_data_uri()
        self.assertTrue(uri.startswith("data:image/png;base64,"))
        out = embed_logo_in_html('<img class="brand-logo" src="logo.png" alt="Apl">')
        self.assertNotIn('src="logo.png"', out)
        self.assertIn(uri, out)

    def test_inject_shell_embeds_logo(self) -> None:
        template = resolve("assets/文档输出模板.html").read_text(encoding="utf-8")
        shell = resolve("assets/业务后台-原型壳.html").read_text(encoding="utf-8")
        out = inject_shell(template, shell)
        self.assertNotIn('src="logo.png"', out)
        self.assertIn("data:image/png;base64,", out)

    def test_scope_shell_styles_rewrites_html_body(self) -> None:
        css = "html, body { margin: 0; height: 100vh; } .app-layout { height: 100vh; }"
        out = scope_shell_styles(css)
        self.assertIn(".prd-embed {", out)
        self.assertNotIn("html, body", out)

    def test_set_proto_slot_uses_markers(self) -> None:
        html = f'<div id="prototype-slot">\n{SLOT_START}\nold\n{SLOT_END}\n</div>'
        out = set_proto_slot(html, "<p>new</p>")
        self.assertIn("<p>new</p>", out)
        self.assertNotIn("old", out)

    def test_validate_proto_fragment_rejects_script(self) -> None:
        errs = validate_proto_fragment("<script>alert(1)</script>")
        self.assertTrue(any("script" in e.lower() for e in errs))

    def test_validate_proto_fragment_rejects_inline_style(self) -> None:
        errs = validate_proto_fragment('<div style="color:red">x</div>')
        self.assertTrue(any("style" in e for e in errs))

    def test_validate_minimal_list_page_passes(self) -> None:
        slot = (
            '<div class="proto-list-page"><section class="query-form">'
            '<div class="filter-grid"><div class="filter-item">'
            '<label class="filter-label" for="t1">x</label><input id="t1" class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button type="button" class="btn btn-primary">查询</button></div></div></section>'
            '<section class="proto-list-card"><div class="table-toolbar"></div>'
            '<table class="proto-table"><tr><td>a</td></tr></table>'
            '<div class="proto-pager"></div></section></div>'
        )
        self.assertEqual(validate_proto_fragment(slot), [])

    def test_validate_proto_list_layout_requires_bottom_bar(self) -> None:
        frag = '<section class="query-form"><div class="filter-grid"></div></section>'
        errs = validate_proto_list_layout(frag)
        self.assertTrue(any("filter-bottom-bar" in e for e in errs))

    def test_validate_spec231_rejects_button_in_filter_item(self) -> None:
        frag = (
            '<section class="query-form"><div class="filter-grid">'
            '<div class="filter-item"><button class="btn btn-primary">查询</button></div>'
            "</div><div class=\"filter-bottom-bar\"></div></section>"
            '<section class="proto-list-card"><table class="proto-table"></table>'
            '<div class="table-toolbar"></div><div class="proto-pager"></div></section>'
        )
        errs = validate_proto_list_spec231(frag)
        self.assertTrue(any("AGENT-7#5" in e for e in errs))

    def test_validate_requires_toggle_when_filter_extra(self) -> None:
        frag = (
            '<div class="proto-list-page"><section class="query-form">'
            '<div class="filter-grid">'
            '<div class="filter-item filter-item--extra"><label class="filter-label" for="t2">x</label>'
            '<input id="t2" class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button class="btn btn-primary">查询</button></div></div></section>'
            '<section class="proto-list-card"><table class="proto-table"></table>'
            '<div class="table-toolbar"></div><div class="proto-pager"></div></section></div>'
        )
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-7#9" in e for e in errs))

    def test_validate_list_align_rejects_nested_query_form(self) -> None:
        frag = (
            '<div class="proto-list-page"><section class="proto-list-card">'
            '<section class="query-form"><div class="filter-grid">'
            '<div class="filter-item"><label class="filter-label">x</label>'
            '<input class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button class="btn btn-primary">查询</button></div></div></section>'
            '<table class="proto-table"></table><div class="proto-pager"></div>'
            "</section></div>"
        )
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-7#1" in e for e in errs))

    def test_validate_rejects_anchor_in_proto_op(self) -> None:
        frag = (
            '<div class="proto-list-page"><section class="query-form">'
            '<div class="filter-grid"><div class="filter-item">'
            '<label class="filter-label" for="t1">x</label><input id="t1" class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button class="btn btn-primary">查询</button></div></div></section>'
            '<section class="proto-list-card"><table class="proto-table"><tbody><tr>'
            '<td><div class="proto-op"><a href="#">查看</a></div></td></tr></tbody></table>'
            '<div class="table-toolbar"></div><div class="proto-pager"></div></section></div>'
        )
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-7#10" in e for e in errs))

    def test_validate_rejects_data_open_modal_on_span(self) -> None:
        frag = '<span data-open-modal="x">打开</span>'
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-7#8" in e and "data-open-modal" in e for e in errs))

    def test_validate_spec231_rejects_fixed_200px(self) -> None:
        frag = (
            '<section class="query-form"><div class="filter-grid" style="width:200px">'
            '<div class="filter-item"><label class="filter-label" for="t3">x</label>'
            '<input id="t3" class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button class="btn btn-primary">查询</button></div></div></section>'
        )
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("style" in e or "AGENT-7" in e for e in errs))

    def test_validate_config_page_structure(self) -> None:
        frag = (
            '<div class="proto-config-page"><section class="proto-list-card proto-config-shell">'
            '<div class="proto-config-split">'
            '<aside class="proto-strategy-rail"></aside>'
            '<div class="proto-config-detail"></div></div></section></div>'
        )
        self.assertEqual(validate_proto_fragment(frag), [])

    def test_validate_config_page_missing_split(self) -> None:
        frag = '<div class="proto-config-page"><section class="proto-config-shell"></section></div>'
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-5b" in e or "proto-config-split" in e for e in errs))

    def test_validate_rejects_filter_label_without_for(self) -> None:
        frag = (
            '<div class="proto-list-page"><section class="query-form">'
            '<div class="filter-grid"><div class="filter-item">'
            '<label class="filter-label">x</label><input class="filter-control"/></div></div>'
            '<div class="filter-bottom-bar"><div class="filter-actions">'
            '<button class="btn btn-primary">查询</button></div></div></section>'
            '<section class="proto-list-card"><table class="proto-table"></table>'
            '<div class="table-toolbar"></div><div class="proto-pager"></div></section></div>'
        )
        errs = validate_proto_fragment(frag)
        self.assertTrue(any("AGENT-7#11" in e for e in errs))

    def test_init_injects_tokens_and_proto_css(self) -> None:
        template = resolve("assets/文档输出模板.html").read_text(encoding="utf-8")
        shell = resolve("assets/催收后台-原型壳.html").read_text(encoding="utf-8")
        html = inject_prdkit_assets(apply_default_slot_scaffold(inject_shell(template, shell)))
        self.assertIn("data-prdkit-tokens", html)
        self.assertIn("--page-pad-x", html)
        self.assertIn("data-prdkit-proto-base", html)

    def test_validate_proto_fragment_div_imbalance(self) -> None:
        errs = validate_proto_fragment("<div><div></div>")
        self.assertTrue(any("div" in e for e in errs))

    def test_validate_shell_on_template(self) -> None:
        template = resolve("assets/文档输出模板.html").read_text(encoding="utf-8")
        shell = resolve("assets/催收后台-原型壳.html").read_text(encoding="utf-8")
        html = inject_prdkit_assets(apply_default_slot_scaffold(inject_shell(template, shell)))
        self.assertEqual(validate_shell_structure(html), [])

    def test_set_proto_page_twice_no_duplicate(self) -> None:
        slot_inner = (
            '<div class="proto-shell" id="proto-root">'
            '<div class="proto-tabs" role="tablist"></div>'
            '<div class="proto-pages" id="proto-pages"></div>'
            "</div>"
        )
        html = f'<div id="prototype-slot">\n{SLOT_START}\n{slot_inner}\n{SLOT_END}\n</div>'
        html = set_proto_page(html, "audit", "<p>v1</p>", "审核")
        html = set_proto_page(html, "audit", "<p>v2</p>", "审核")
        self.assertEqual(html.count('data-proto-page="audit"'), 1)
        self.assertIn("v2", html)
        self.assertNotIn("v1", html)
        import re

        slot_body = re.search(
            re.escape(SLOT_START) + r"(.*?)" + re.escape(SLOT_END), html, re.DOTALL
        ).group(1)
        self.assertEqual(validate_proto_tabs(slot_body), [])

    def test_set_proto_page_adds_tab(self) -> None:
        slot_inner = (
            '<div class="proto-shell" id="proto-root">'
            '<div class="proto-tabs" role="tablist"></div>'
            '<div class="proto-pages" id="proto-pages"></div>'
            "</div>"
        )
        html = f'<div id="prototype-slot">\n{SLOT_START}\n{slot_inner}\n{SLOT_END}\n</div>'
        out = set_proto_page(html, "audit", "<p>审核页</p>", "平账审核")
        self.assertIn('data-tab="audit"', out)
        self.assertIn("平账审核", out)
        self.assertIn('data-proto-page="audit"', out)
        self.assertIn("审核页", out)


class HtmlToolCliTests(unittest.TestCase):
    def test_init_writes_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = {**os.environ, "PYTHONPATH": str(SRC)}
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "prdkit.html_tool",
                    "init",
                    "--output-dir",
                    "out",
                    "--basename",
                    "test_prd",
                    "--shell",
                    "催收后台",
                ],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            config = json.loads((cwd / ".memory/prd_output.json").read_text(encoding="utf-8"))
            self.assertEqual(config["output_dir"], "out")
            html_path = cwd / "out/test_prd.html"
            self.assertTrue(html_path.is_file())
            html = html_path.read_text(encoding="utf-8")
            self.assertIn("data-prdkit-proto-runtime", html)
            self.assertIn("proto-tabs", html)

    def test_validate_after_init(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            cwd = Path(tmp)
            env = {**os.environ, "PYTHONPATH": str(SRC)}
            subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "prdkit.html_tool",
                    "init",
                    "--output-dir",
                    "out",
                    "--basename",
                    "v",
                    "--shell",
                    "业务后台",
                ],
                cwd=cwd,
                env=env,
                check=True,
                capture_output=True,
            )
            result = subprocess.run(
                [sys.executable, "-m", "prdkit.html_tool", "validate"],
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
