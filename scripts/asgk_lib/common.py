from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rel(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def read_text(path: str | Path) -> str:
    return rel(path).read_text(encoding="utf-8")


def has_see_chat(text: str) -> bool:
    return bool(re.search(r"\bsee\s+chat\b", text, flags=re.IGNORECASE))


def has_unresolved_todo(text: str) -> bool:
    return bool(re.search(r"\b(?:AI_TODO|TODO)\b", text))


def markdown_headings(text: str) -> set[str]:
    found: set[str] = set()
    for line in text.splitlines():
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            found.add(match.group(1).strip())
    return found


def markdown_section(text: str, heading: str) -> str:
    match = re.search(
        rf"^## {re.escape(heading)}\s+(.+?)(?:\n## |\Z)",
        text,
        flags=re.MULTILINE | re.DOTALL,
    )
    return match.group(1).strip() if match else ""


def line_field_exists(text: str, field: str) -> bool:
    return bool(re.search(rf"^[ \t]*{re.escape(field)}[ \t]*:", text, flags=re.MULTILINE))


def field_value(text: str, field: str) -> str | None:
    """Return a same-line scalar value for a lightweight YAML-like field."""

    match = re.search(
        rf"^[ \t]*{re.escape(field)}[ \t]*:[ \t]*(.*?)[ \t]*$",
        text,
        flags=re.MULTILINE,
    )
    if not match:
        return None
    return match.group(1).strip().strip('"').strip("'")


def normalized_field_value(text: str, field: str) -> str:
    value = field_value(text, field)
    if value is None:
        return ""
    return value.strip().strip('"').strip("'").lower()


def field_block_lines(text: str, field: str) -> list[str] | None:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        match = re.match(rf"^([ \t]*){re.escape(field)}[ \t]*:", line)
        if not match:
            continue
        field_indent = len(match.group(1).replace("\t", "    "))
        block: list[str] = []
        for child in lines[index + 1:]:
            stripped = child.strip()
            if not stripped:
                continue
            child_indent = len(re.match(r"^[ \t]*", child).group(0).replace("\t", "    "))
            if child_indent <= field_indent and re.match(r"^[A-Za-z0-9_\-]+[ \t]*:", stripped):
                break
            if child_indent > field_indent:
                block.append(child)
        return block
    return None


def list_field_has_material_item(text: str, field: str) -> bool:
    value = field_value(text, field)
    if value:
        return True
    block = field_block_lines(text, field)
    if block is None:
        return False
    for line in block:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        item = re.match(r"^-\s*(.*?)\s*$", stripped)
        if item and item.group(1).strip().strip('"').strip("'"):
            return True
    return False


def field_block_text(text: str, field: str) -> str:
    block = field_block_lines(text, field)
    return "\n".join(block or [])


def yaml_dedent(lines: list[str]) -> str:
    material = [line for line in lines if line.strip()]
    if not material:
        return ""
    min_indent = min(len(re.match(r"^[ \t]*", line).group(0).replace("\t", "    ")) for line in material)
    return "\n".join(line[min_indent:] if len(line) >= min_indent else line for line in lines)


def read_changed_paths(path: str | Path) -> set[str]:
    return {
        line.strip()
        for line in read_text(path).splitlines()
        if line.strip() and not line.strip().startswith("#")
    }


def normalize_repo_path(path: str) -> str:
    cleaned = path.strip().strip("`").strip('"').strip("'").replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def same_repo_path(left: str, right: str) -> bool:
    return normalize_repo_path(left) == normalize_repo_path(right)
