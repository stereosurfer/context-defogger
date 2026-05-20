from __future__ import annotations

import re
from pathlib import Path


def release_version_tuple(tag: str) -> tuple[int, int, int] | None:
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag.strip())
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def find_latest_completed_readme_versions(text: str) -> list[str]:
    return re.findall(
        r"ASGK\s+(v\d+\.\d+\.\d+)\s+is\s+the\s+latest\s+completed\s+source-only\s+GitHub\s+release",
        text,
        flags=re.IGNORECASE,
    )


def release_state_stale_patterns(tag: str) -> list[tuple[str, str]]:
    escaped = re.escape(tag)
    return [
        (rf"{escaped}[^\n.]*candidate", f"{tag} is still described as candidate"),
        (rf"candidate[^\n.]*{escaped}", f"{tag} is still described as candidate"),
        (rf"{escaped}[^\n.]*pending", f"{tag} is still described as pending"),
        (rf"pending[^\n.]*{escaped}", f"{tag} is still described as pending"),
        (
            rf"{escaped}[^\n.]*requires[^\n.]*release execution",
            f"{tag} still appears to require release execution",
        ),
        (
            rf"{escaped}[^\n.]*tag or GitHub release requires",
            f"{tag} still appears to require tag or GitHub release creation",
        ),
        (
            rf"{escaped}[^\n.]*release execution[^\n.]*not_started",
            f"{tag} release execution is still marked not_started",
        ),
    ]


def release_ledger_patterns() -> dict[str, list[tuple[str, str]]]:
    return {
        "current status": [
            (
                r"Completed source-only releases are recorded in GitHub releases and release\s+issues:",
                "CURRENT_STATUS.md duplicates a release-history ledger",
            ),
        ],
        "roadmap": [
            (
                r"^\s*source_only_v\d+(?:_\d+)*_release_execution:",
                "roadmap duplicates per-release execution records",
            ),
        ],
        "release policy": [
            (
                r"^## v\d+\.\d+(?:\.\d+)? Release (?:Preparation|Execution) Record$",
                "source-only release policy duplicates per-release execution records",
            ),
        ],
    }


def check_release_state_docs(
    *,
    tag: str,
    release_title: str,
    readme_path: Path,
    roadmap_path: Path,
    current_status_path: Path,
    release_policy_path: Path | None = None,
) -> list[str]:
    failures: list[str] = []
    if release_version_tuple(tag) is None:
        failures.append(f"release tag must be semver-like vX.Y.Z: {tag}")

    docs = [
        ("README", readme_path),
        ("roadmap", roadmap_path),
        ("current status", current_status_path),
    ]
    if release_policy_path is not None and release_policy_path.exists():
        docs.append(("release policy", release_policy_path))
    texts: dict[str, str] = {}
    for label, path in docs:
        if not path.exists():
            failures.append(f"missing {label} release-state file: {path}")
            continue
        texts[label] = path.read_text(encoding="utf-8")

    readme = texts.get("README", "")
    if readme:
        latest_versions = find_latest_completed_readme_versions(readme)
        if not latest_versions:
            failures.append("README does not identify the latest completed source-only GitHub release")
        for version in latest_versions:
            if version != tag:
                failures.append(f"README latest completed release is {version}, expected {tag}")
        if tag not in readme:
            failures.append(f"README does not mention released tag {tag}")

    combined_text = "\n\n".join(texts.values())
    if release_title and release_title not in combined_text:
        failures.append(f"release title not found in release-state docs: {release_title}")

    for label, text in texts.items():
        for pattern, reason in release_state_stale_patterns(tag):
            if re.search(pattern, text, flags=re.IGNORECASE):
                failures.append(f"{label}: {reason}")
        for pattern, reason in release_ledger_patterns().get(label, []):
            if re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE):
                failures.append(f"{label}: {reason}")

    return failures
