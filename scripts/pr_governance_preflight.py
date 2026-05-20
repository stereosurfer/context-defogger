#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_BODY_FLAGS = {"--body", "-b", "--body-file", "-F"}


def strip_separator(args: list[str]) -> list[str]:
    if args and args[0] == "--":
        return args[1:]
    return args


def has_forbidden_body_flag(args: list[str]) -> bool:
    for arg in args:
        if arg in FORBIDDEN_BODY_FLAGS:
            return True
        if arg.startswith("--body=") or arg.startswith("--body-file="):
            return True
    return False


def run(command: list[str]) -> int:
    print("+ " + " ".join(command))
    return subprocess.run(command, cwd=ROOT).returncode


def preflight(body_file: str) -> int:
    body_path = Path(body_file)
    if not body_path.exists():
        print(f"FAIL: PR body file does not exist: {body_file}")
        return 1

    checks = [
        ["python3", "scripts/asgk.py", "pr-body-check", "--file", str(body_path)],
        ["python3", "scripts/policy_gate_check.py", "--pr-body", str(body_path)],
    ]
    for check in checks:
        result = run(check)
        if result != 0:
            print("FAIL: PR body governance preflight failed.")
            return result
    print("PR body governance preflight passed.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    return preflight(args.body_file)


def cmd_create(args: argparse.Namespace) -> int:
    gh_args = strip_separator(args.gh_args)
    if has_forbidden_body_flag(gh_args):
        print("FAIL: pass the PR body only through --body-file on this wrapper.")
        return 1
    result = preflight(args.body_file)
    if result != 0:
        return result
    return run(["gh", "pr", "create", *gh_args, "--body-file", args.body_file])


def cmd_edit(args: argparse.Namespace) -> int:
    gh_args = strip_separator(args.gh_args)
    if has_forbidden_body_flag(gh_args):
        print("FAIL: pass the PR body only through --body-file on this wrapper.")
        return 1
    result = preflight(args.body_file)
    if result != 0:
        return result
    return run(["gh", "pr", "edit", *gh_args, "--body-file", args.body_file])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run local PR body governance preflight before gh pr create/edit."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="Check a PR body file only.")
    check.add_argument("--body-file", required=True)
    check.set_defaults(func=cmd_check)

    create = sub.add_parser("create", help="Check a body file, then run gh pr create.")
    create.add_argument("--body-file", required=True)
    create.add_argument("gh_args", nargs=argparse.REMAINDER)
    create.set_defaults(func=cmd_create)

    edit = sub.add_parser("edit", help="Check a body file, then run gh pr edit.")
    edit.add_argument("--body-file", required=True)
    edit.add_argument("gh_args", nargs=argparse.REMAINDER)
    edit.set_defaults(func=cmd_edit)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
