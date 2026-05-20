from __future__ import annotations

import re

from asgk_lib.common import field_block_lines, yaml_dedent


def normalized_task_field_label(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", label.strip().lower()).strip("_")


def parse_markdown_task_field_sections(text: str) -> dict[str, object]:
    fields: dict[str, object] = {}
    matches = list(re.finditer(r"^#{2,6}\s+(.+?)\s*$", text, flags=re.MULTILINE))
    for index, match in enumerate(matches):
        field = normalized_task_field_label(match.group(1))
        if not field:
            continue
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        content = text[start:end].strip()
        if not content or content in {"_No response_", "No response"}:
            continue
        fields[field] = content
    return fields


def material_items(value: object) -> list[str]:
    if isinstance(value, list):
        return [
            str(item).strip().strip('"').strip("'")
            for item in value
            if str(item).strip().strip('"').strip("'")
        ]
    if not isinstance(value, str):
        return []
    items: list[str] = []
    for line in value.splitlines():
        cleaned = line.strip()
        if not cleaned or cleaned in {"```", "```yaml", "```text"}:
            continue
        cleaned = re.sub(r"^[-*]\s+", "", cleaned)
        cleaned = re.sub(r"^- \[[ xX]\]\s+", "", cleaned)
        cleaned = cleaned.strip().strip('"').strip("'")
        if cleaned:
            items.append(cleaned)
    return items


def task_packet_yaml_source(text: str) -> str:
    bad_input = field_block_lines(text, "bad_input")
    if bad_input is not None:
        return yaml_dedent(bad_input)
    task_packet = field_block_lines(text, "task_packet")
    if task_packet is not None:
        return yaml_dedent(task_packet)
    return text


def parse_simple_task_packet_yaml(text: str) -> dict[str, object]:
    """Parse the repository's dependency-free task-packet YAML subset.

    This is not a general YAML parser. It covers the canonical task-packet shape:
    top-level scalar fields and top-level list fields. For full YAML features,
    keep the source in JSON or add a separately approved dependency.
    """

    packet: dict[str, object] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        match = re.match(r"^([A-Za-z0-9_\-]+)[ \t]*:[ \t]*(.*?)\s*$", line)
        if not match:
            index += 1
            continue
        field = match.group(1)
        value = match.group(2).strip()
        if value:
            packet[field] = value.strip('"').strip("'")
            index += 1
            continue

        children: list[str] = []
        index += 1
        while index < len(lines):
            child = lines[index]
            child_stripped = child.strip()
            if (
                child_stripped
                and not child.startswith((" ", "\t"))
                and re.match(r"^[A-Za-z0-9_\-]+[ \t]*:", child_stripped)
            ):
                break
            if child_stripped:
                item = re.match(r"^[ \t]*-[ \t]*(.*?)\s*$", child)
                if item:
                    item_value = item.group(1).strip().strip('"').strip("'")
                    if item_value:
                        children.append(item_value)
            index += 1
        packet[field] = children
    return packet
