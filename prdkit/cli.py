from __future__ import annotations

import argparse
import shutil
import sys
from importlib import resources
from pathlib import Path

from prdkit import __version__
from prdkit.banner import print_version_banner
from prdkit.paths import list_resources, resolve


def _bundled_skills_root() -> Path:
    root = resources.files("prdkit") / "skills"
    with resources.as_file(root) as path:
        return Path(path)


def _cursor_skills_dir() -> Path:
    return Path.home() / ".cursor" / "skills"


def cmd_path(args: argparse.Namespace) -> int:
    if args.list:
        for key in list_resources():
            print(key)
        return 0
    if not args.resource:
        print("❌ 请提供资源键，或使用 prdkit path --list 查看全部。", file=sys.stderr)
        return 1
    try:
        path = resolve(args.resource)
    except FileNotFoundError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    print(path)
    return 0


def _stamp_skill_md(dest_skill_md: Path, version: str) -> None:
    text = dest_skill_md.read_text(encoding="utf-8")
    line = f'prdkit-bundle-version: "{version}"'
    if line in text:
        return
    if text.startswith("---\n"):
        end = text.find("\n---\n", 4)
        if end != -1:
            front = text[4:end]
            rest = text[end + 5 :]
            if "prdkit-bundle-version:" in front:
                return
            dest_skill_md.write_text(
                f"---\n{front}\n{line}\n---\n{rest}",
                encoding="utf-8",
            )
            return
    dest_skill_md.write_text(f"<!-- {line} -->\n{text}", encoding="utf-8")


def cmd_install(args: argparse.Namespace) -> int:
    target_root = _cursor_skills_dir()
    source_root = _bundled_skills_root()
    if not source_root.exists():
        print(f"❌ 未找到内置 skills 目录: {source_root}", file=sys.stderr)
        return 1

    target_root.mkdir(parents=True, exist_ok=True)
    installed = []
    for skill_dir in sorted(source_root.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if not skill_md.is_file():
            continue
        dest = target_root / skill_dir.name
        if dest.exists() and not args.force:
            print(f"⏭  已存在，跳过: {dest}（使用 --force 覆盖）")
            continue
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(skill_dir, dest)
        _stamp_skill_md(dest / "SKILL.md", __version__)
        installed.append(skill_dir.name)

    if not installed:
        print("未安装任何 Skill（可能均已存在，可加 --force 覆盖）。")
        return 0

    print("✅ 已安装 Cursor Skills 至:", target_root)
    for name in installed:
        print(f"   - {name}")
    print("\n请重启 Cursor，在 Settings → Rules → Skills 中确认可见。")
    return 0


def cmd_version(_: argparse.Namespace) -> int:
    print_version_banner(__version__)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="prdkit",
        description="PRD 工作流套件：解析内置资源、安装 Cursor Skills",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    path_parser = sub.add_parser("path", help="输出内置资源的绝对路径（供 Read 工具使用）")
    path_parser.add_argument(
        "resource",
        nargs="?",
        help="如 reference/prd-writing-spec.md、assets/文档输出模板.html",
    )
    path_parser.add_argument(
        "--list",
        action="store_true",
        help="列出全部内置资源键",
    )
    path_parser.set_defaults(func=cmd_path)

    install_parser = sub.add_parser(
        "install",
        help="将内置 Skill 安装到 ~/.cursor/skills/",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="覆盖已存在的同名 Skill",
    )
    install_parser.set_defaults(func=cmd_install)

    version_parser = sub.add_parser("version", help="显示版本号")
    version_parser.set_defaults(func=cmd_version)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
