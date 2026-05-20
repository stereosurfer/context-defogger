#!/usr/bin/env python3
"""Dependency-light governance hygiene checker.

The checker validates newline-delimited changed-path lists. Its default mode is
positive validation: any blocked path returns a non-zero exit code.

For opt-in negative fixtures, pass ``--expect-blocked``. In that mode, the
command succeeds only when at least one blocked path is found. This lets the
repository prove that known-bad path fixtures are still blocked without loading
those fixtures as positive examples.
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path


PROTECTED_PATTERNS = [
    ".env",
    ".env.",
    "secrets/",
    "credentials/",
    "private_keys/",
    "node_modules/",
    ".git/",
]

BINARY_PRIVATE_SUFFIXES = [
    ".pdf",
    ".epub",
    ".docx",
    ".pptx",
    ".xlsx",
    ".png",
    ".jpg",
    ".jpeg",
    ".tif",
    ".tiff",
]

ALLOWED_GENERATED_PREFIXES = ["tests/fixtures/", "examples/"]
RUNTIME_ARTIFACT_PREFIXES = ["runs/", "corpus/", "artifacts/"]


def normalize_path(path: str) -> str:
    """Normalize path text from git/GitHub style lists.

    This is intentionally conservative. It does not resolve symlinks or touch the
    filesystem; it only normalizes textual path separators and leading ``./``.
    """

    cleaned = path.strip().replace("\\", "/")
    while cleaned.startswith("./"):
        cleaned = cleaned[2:]
    return cleaned


def load_paths(paths_file: Path) -> list[str]:
    """Read path lines, ignoring blanks and comment lines.

    Negative fixtures commonly include YAML-ish metadata in comments. Those
    comments must not be treated as repository paths.
    """

    paths: list[str] = []
    for raw_line in paths_file.read_text(encoding="utf-8").splitlines():
        path = normalize_path(raw_line)
        if not path or path.startswith("#"):
            continue
        paths.append(path)
    return paths


def load_git_paths(git_base: str, git_head: str) -> list[str]:
    """Collect changed paths from a git diff range.

    The checker stays dependency-light and API-free. It asks local git for the
    name-only diff and then applies the same textual normalization used for
    fixture files.
    """

    result = subprocess.run(
        ["git", "diff", "--name-only", git_base, git_head],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "git diff failed"
        raise RuntimeError(message)
    return [
        normalize_path(raw_line)
        for raw_line in result.stdout.splitlines()
        if normalize_path(raw_line)
    ]


def is_blocked(path: str) -> str | None:
    p = normalize_path(path)

    for pattern in PROTECTED_PATTERNS:
        if p == pattern.rstrip("/") or p.startswith(pattern):
            return f"protected path: {pattern}"

    if any(p.lower().endswith(suffix) for suffix in BINARY_PRIVATE_SUFFIXES):
        if not any(p.startswith(prefix) for prefix in ALLOWED_GENERATED_PREFIXES):
            return "private/binary source-like file outside fixture/example path"

    for prefix in RUNTIME_ARTIFACT_PREFIXES:
        if p.startswith(prefix) and not any(
            p.startswith(allowed_prefix) for allowed_prefix in ALLOWED_GENERATED_PREFIXES
        ):
            return f"runtime artifact path: {prefix}"

    return None


def collect_failures(paths: list[str]) -> list[tuple[str, str]]:
    failures: list[tuple[str, str]] = []
    for path in paths:
        reason = is_blocked(path)
        if reason:
            failures.append((path, reason))
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check changed paths for protected paths and runtime artifacts."
    )
    parser.add_argument("--paths-file", help="Newline-delimited path list.")
    parser.add_argument("--git-base", help="Base revision for git diff --name-only.")
    parser.add_argument("--git-head", help="Head revision for git diff --name-only.")
    parser.add_argument(
        "--expect-blocked",
        action="store_true",
        help="Succeed only when the paths file contains at least one blocked path.",
    )
    args = parser.parse_args()

    using_paths_file = bool(args.paths_file)
    using_git_range = bool(args.git_base or args.git_head)
    if using_paths_file == using_git_range:
        print("FAIL: provide exactly one of --paths-file or --git-base/--git-head.")
        return 1
    if using_git_range and not (args.git_base and args.git_head):
        print("FAIL: --git-base and --git-head must be provided together.")
        return 1

    try:
        paths = (
            load_paths(Path(args.paths_file))
            if using_paths_file
            else load_git_paths(args.git_base, args.git_head)
        )
    except RuntimeError as exc:
        print(f"FAIL: {exc}")
        return 1

    failures = collect_failures(paths)

    for path, reason in failures:
        print(f"BLOCKED {path}: {reason}")

    if args.expect_blocked:
        if failures:
            print(
                f"Governance hygiene negative check passed: {len(failures)} blocked path(s) detected."
            )
            return 0
        print("FAIL: expected at least one blocked path, but none were detected.")
        return 1

    if failures:
        print(f"FAIL: {len(failures)} blocked path(s) detected.")
        return 1

    print(f"Governance hygiene check passed: {len(paths)} path(s) checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
