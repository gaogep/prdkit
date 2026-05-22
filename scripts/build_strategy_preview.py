#!/usr/bin/env python3
"""生成「金融配置 · 策略列表」独立预览 HTML（业务后台壳 + design-spec 配置页）。"""
from __future__ import annotations

import re
from pathlib import Path

from prdkit.html_tool import embed_logo_in_html, inject_prdkit_assets
from prdkit.paths import resolve

PREVIEW_STYLE = """
html, body { height: 100%; margin: 0; }
.prd-embed { height: 100vh; min-height: 100vh; display: flex; flex-direction: column; }
.prd-embed > .app-layout { flex: 1; min-height: 0; height: 100%; }
.prd-embed .welcome-block { display: none !important; }
.prd-embed .app-main { padding: 16px 24px 24px !important; align-items: stretch !important; }
"""

SIDEBAR_MENU = """
      <nav class="sidebar-menu" aria-label="业务菜单">
        <a class="menu-item" href="#"><span class="menu-label">订单管理</span></a>
        <a class="menu-item" href="#"><span class="menu-label">支付管理</span></a>
        <a class="menu-item" href="#"><span class="menu-label">审批管理</span></a>
        <a class="menu-item" href="#"><span class="menu-label">数据报表</span></a>
        <a class="menu-item" href="#"><span class="menu-label">运营工具</span></a>
        <a class="menu-item is-pay-active" href="javascript:void(0)"><span class="menu-label">风控和金融配置</span></a>
        <div class="sidebar-sub is-show" id="risk-sub">
          <a href="javascript:void(0)">策略分流</a>
          <a href="javascript:void(0)">策略配置</a>
          <a href="javascript:void(0)">机构配置</a>
          <a href="javascript:void(0)" class="is-active">金融配置</a>
          <a href="javascript:void(0)">风控配置</a>
          <a href="javascript:void(0)">风控策略</a>
        </div>
        <a class="menu-item" href="#"><span class="menu-label">系统配置</span></a>
      </nav>
"""


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out = root / "prds" / "策略配置-原型预览.html"
    shell = resolve("assets/业务后台-原型壳.html").read_text(encoding="utf-8")
    slot = resolve("assets/fragments/strategy-config-slot.html").read_text(encoding="utf-8")

    html = re.sub(
        r"<!-- prdkit:slot:start -->.*?<!-- prdkit:slot:end -->",
        f"<!-- prdkit:slot:start -->\n{slot}\n<!-- prdkit:slot:end -->",
        shell,
        count=1,
        flags=re.DOTALL,
    )
    html = re.sub(
        r'<nav class="sidebar-menu"[^>]*>.*?</nav>',
        SIDEBAR_MENU.strip(),
        html,
        count=1,
        flags=re.DOTALL,
    )
    html = html.replace("<span class=\"brand-title\">业务后台</span>", '<span class="brand-title">Management</span>')
    html = html.replace("<option selected>TH</option>", "<option selected>VNDX</option>")
    html = html.replace("跳转TH", "跳转VNDX")
    html = html.replace('<a class="menu-item is-active" href="#">', '<a class="menu-item" href="#">', 1)

    html = html.replace("<body>", f"<body>\n<div class=\"prd-embed\">", 1)
    html = html.replace("</body>", "</div>\n</body>", 1)
    html = inject_prdkit_assets(embed_logo_in_html(html))
    html = html.replace("</head>", f"<style data-prdkit-preview>{PREVIEW_STYLE}</style>\n</head>", 1)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(out)


if __name__ == "__main__":
    main()
