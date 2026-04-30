"""
同步 Obsidian 笔记到 docs-site。

用法:
  python3 sync.py
  python3 sync.py --show
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict
from urllib.parse import unquote

SITE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = SITE_ROOT.parent
VAULT = PROJECT_ROOT / "tnote" / "课程讲义"
DOCS = SITE_ROOT / "src" / "content" / "docs"
MAPPING = SITE_ROOT / "mapping.json"

DIR_MAP = {
    "Windows 服务器安全配置": "windows-server-security",
    "数据库系统管理和运维": "database-admin",
    "01 项目一 走进Windows服务器": "01-intro",
    "实验三 数据": "lab3-data-sub",
}


def load_mapping() -> Dict[str, str]:
    if not MAPPING.exists():
        return {}
    return json.loads(MAPPING.read_text(encoding="utf-8"))


def save_mapping(mapping: Dict[str, str]) -> None:
    MAPPING.write_text(
        json.dumps(mapping, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def normalize_rel_path(path: Path) -> str:
    return path.as_posix()


def map_directory(rel_dir: Path) -> Path:
    mapped_parts = [DIR_MAP.get(part, part) for part in rel_dir.parts if part != "."]
    return Path(*mapped_parts) if mapped_parts else Path()


def to_ascii_name(filename: str) -> str:
    stem = Path(filename).stem
    prefix = ""
    match = re.match(r"^(\d+)", stem)
    if match:
        prefix = match.group(1)
        stem = stem[len(prefix) :].lstrip(" .-_")
    slug = re.sub(r"[^\w]", "-", stem).strip("-")
    slug = re.sub(r"-+", "-", slug).lower()
    if prefix and not slug.startswith(f"{prefix}-"):
        slug = f"{prefix}-{slug}"
    return f"{slug or 'untitled'}.md"


def extract_heading_title(content: str) -> str | None:
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else None


def extract_frontmatter_title(content: str) -> str | None:
    match = re.search(r"^---\ntitle:\s*(.+?)\n", content, re.MULTILINE)
    if not match:
        return None
    title = match.group(1).strip()
    if len(title) >= 2 and title[0] == title[-1] and title[0] in {"'", '"'}:
        title = title[1:-1]
    return title


def yaml_quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def get_route_from_target(target_rel: Path) -> str:
    if target_rel.stem.lower() == "readme":
        base = target_rel.parent.as_posix()
        return f"/{base}/" if base else "/"
    return f"/{target_rel.with_suffix('').as_posix()}"


def build_route_map(mapping: Dict[str, str]) -> Dict[str, str]:
    route_map: Dict[str, str] = {}
    for source_key, mapped_name in mapping.items():
        source_rel = Path(source_key)
        target_rel = map_directory(source_rel.parent) / mapped_name
        route_map[source_key] = get_route_from_target(target_rel)
    return route_map


def clean_link_target(link_target: str) -> str:
    base = unquote(link_target.split("#", 1)[0])
    base = re.sub(r"\s+[0-9a-f]{32}(?=\.md$)", "", base).strip()
    return base


def rewrite_links(content: str, source_rel: Path, route_map: Dict[str, str]) -> str:
    def replace_markdown_link(match: re.Match[str]) -> str:
        text, raw_target = match.group(1), match.group(2)
        if "://" in raw_target or raw_target.startswith("/"):
            return match.group(0)
        cleaned = clean_link_target(raw_target)
        if not cleaned.endswith(".md"):
            return match.group(0)

        try:
            resolved = (VAULT / source_rel.parent / cleaned).resolve().relative_to(
                VAULT.resolve()
            )
        except ValueError:
            return match.group(0)
        source_key = normalize_rel_path(resolved)
        route = route_map.get(source_key)
        if not route:
            return match.group(0)
        return f"[{text}]({route})"

    return re.sub(r"\[([^\]]+)\]\(([^)]+?)\)", replace_markdown_link, content)


def resolve_target(source_rel: Path, mapping: Dict[str, str]) -> Path:
    source_key = normalize_rel_path(source_rel)
    mapped_name = mapping.get(source_key)
    if not mapped_name:
        mapped_name = to_ascii_name(source_rel.name)
        mapping[source_key] = mapped_name
    return DOCS / map_directory(source_rel.parent) / mapped_name


def show_mapping(mapping: Dict[str, str]) -> None:
    print("\n" + "=" * 78)
    print(f'  {"Obsidian 源文件".center(36)}  {"站点目标文件".center(36)}')
    print("=" * 78)
    for source_key, mapped_name in sorted(mapping.items()):
        target_rel = map_directory(Path(source_key).parent) / mapped_name
        print(f"  {source_key:<38} {target_rel.as_posix():<36}")
    print("=" * 78)
    print(f"  共 {len(mapping)} 条映射\n")


def sync(mapping: Dict[str, str], force: bool = False) -> None:
    if not VAULT.exists():
        raise FileNotFoundError(f"Source vault not found: {VAULT}")

    source_files = sorted(VAULT.rglob("*.md"))
    new_mapped: list[str] = []

    for source_file in source_files:
        source_rel = source_file.relative_to(VAULT)
        source_key = normalize_rel_path(source_rel)
        if source_key in mapping:
            continue
        mapping[source_key] = to_ascii_name(source_rel.name)
        target_rel = map_directory(source_rel.parent) / mapping[source_key]
        new_mapped.append(f"{source_key} -> {target_rel.as_posix()}")

    route_map = build_route_map(mapping)
    updated = 0
    skipped = 0

    for source_file in source_files:
        source_rel = source_file.relative_to(VAULT)
        target_file = resolve_target(source_rel, mapping)
        if (
            not force
            and target_file.exists()
            and source_file.stat().st_mtime <= target_file.stat().st_mtime
        ):
            skipped += 1
            continue

        content = source_file.read_text(encoding="utf-8")
        content = rewrite_links(content, source_rel, route_map)

        existing_title = None
        if target_file.exists():
            existing_title = extract_frontmatter_title(
                target_file.read_text(encoding="utf-8")
            )
        else:
            target_file.parent.mkdir(parents=True, exist_ok=True)

        title = existing_title or extract_heading_title(content) or source_file.stem
        frontmatter = f"---\ntitle: {yaml_quote(title)}\n---\n\n"
        target_file.write_text(frontmatter + content, encoding="utf-8")
        updated += 1

    if new_mapped:
        print("[新文件自动映射]")
        for item in new_mapped:
            print(f"  {item}")
        save_mapping(mapping)

    print(f"\nDone: {updated} updated, {skipped} skipped")


def main() -> None:
    mapping = load_mapping()
    if "--show" in sys.argv:
        show_mapping(mapping)
        return
    sync(mapping, force="--force" in sys.argv)


if __name__ == "__main__":
    main()
