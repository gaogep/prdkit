"""Terminal banner for `prdkit version`."""

from __future__ import annotations

import os
import sys

# 单字块（标准 figlet 风格），拼合时加间距，避免 P/R/D 粘连误读为 RDRKIT
_P = ["██████╗", "██╔══██╗", "██████╔╝", "██║", "██║", "╚═╝"]
_R = ["██████╗", "██╔══██╗", "██████╔╝", "██╔══██╗", "██║  ██╗", "╚═╝  ╚═╝"]
_D = ["██████╗", "██╔══██╗", "██║  ██╗", "██║   ██╗", "██████╔╝", "╚═════╝"]
_K = ["██╗  ██╗", "██║ ██╔╝", "█████╔╝", "██╔═██╗", "██║  ██╗", "╚═╝  ╚═╝"]
_I = ["██╗", "██║", "██║", "██║", "██║", "╚═╝"]
_T = ["████████╗", "╚══██╔══╝", "   ██║", "   ██║", "   ██║", "   ╚═╝"]

_APL = [
    "   █████╗ ██████╗ ██╗",
    "  ██╔══██╗██╔══██╗██║",
    "  ███████║██████╔╝██║",
    "  ██╔══██║██╔═══╝ ██║",
    "  ██║  ██║██║     ███████╗",
    "  ╚═╝  ╚═╝╚═╝     ╚══════╝",
]
_SEP = "              ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄   "

_LETTER_GAP = " "


def _merge_letters(*letters: list[str]) -> list[str]:
    padded = [[row.ljust(max(len(r) for r in letter)) for row in letter] for letter in letters]
    rows = len(padded[0])
    return [_LETTER_GAP.join(padded[i][row] for i in range(len(padded))) for row in range(rows)]


def _indent_prdkit(lines: list[str], prefix: str = "              ") -> list[str]:
    return [prefix + line for line in lines]


_PRDKIT = _indent_prdkit(_merge_letters(_P, _R, _D, _K, _I, _T))


def _build_banner() -> list[tuple[str, str]]:
    body: list[tuple[str, str]] = [(l, "apl") for l in _APL]
    body.append((_SEP, "sep"))
    body.extend((l, "prdkit") for l in _PRDKIT)

    width = max(len(line) for line, _ in body)
    lines: list[tuple[str, str]] = [
        ("╭" + "─" * width + "╮", "frame"),
        ("│" + " " * width + "│", "empty"),
    ]
    for line, section in body:
        lines.append(("│" + line.ljust(width) + "│", section))
    lines.append(("│" + " " * width + "│", "empty"))
    lines.append(("╰" + "─" * width + "╯", "frame"))
    return lines


_BANNER_LINES = _build_banner()


def _use_color() -> bool:
    return sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _style(code: str, text: str) -> str:
    if not _use_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def _render(line: str, section: str) -> str:
    if section == "frame" or section == "empty":
        return _style("90", line)
    if section == "sep":
        return _style("90", "│") + _style("35;1", line[1:-1]) + _style("90", "│")
    if section == "apl":
        return _style("90", "│") + _style("96;1", line[1:-1]) + _style("90", "│")
    if section == "prdkit":
        return _style("90", "│") + _style("92;1", line[1:-1]) + _style("90", "│")
    return line


def print_version_banner(version: str) -> None:
    for line, section in _BANNER_LINES:
        print(_render(line, section))
    print()
    print(_style("93;1", f"  ▸  version {version}"))
    print(_style("2", "  ▸  B端 PRD 工作流 · Hook · Cursor Skills"))
    print()
