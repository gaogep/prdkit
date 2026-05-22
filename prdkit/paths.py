from __future__ import annotations

from importlib import resources
from pathlib import Path


def _walk_files(base) -> list[str]:
    keys: list[str] = []
    if not base.exists():
        return keys
    for item in sorted(base.rglob("*")):
        if item.is_file() and not item.name.startswith("."):
            rel = item.relative_to(base)
            keys.append(rel.as_posix())
    return keys


def list_resources() -> list[str]:
    """列出所有可通过 `prdkit path <资源键>` 解析的内置资源键。"""
    root = resources.files("prdkit")
    keys: list[str] = []
    keys.extend(_walk_files(root.joinpath("data")))
    for skill_dir in sorted(root.joinpath("skills").iterdir()):
        if skill_dir.is_dir():
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                keys.append(f"skill/{skill_dir.name}/SKILL.md")
    return sorted(keys)


def resolve(resource: str) -> Path:
    """Resolve a bundled resource path.

    Examples:
        reference/prd-writing-spec.md
        reference/design-spec.md
        assets/文档输出模板.html
        skill/prd-clarify/SKILL.md
    """
    normalized = resource.replace("\\", "/").strip("/")
    if not normalized:
        raise FileNotFoundError("资源路径不能为空")

    parts = normalized.split("/")
    if parts[0] == "skill":
        rel = Path("skills", *parts[1:])
    else:
        rel = Path("data", *parts)

    root = resources.files("prdkit")
    candidate = root.joinpath(*rel.parts)
    if not candidate.exists():
        raise FileNotFoundError(f"未找到套件资源: {resource}")

    with resources.as_file(candidate) as path:
        return Path(path)
