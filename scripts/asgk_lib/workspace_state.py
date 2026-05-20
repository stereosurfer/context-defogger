from __future__ import annotations

import json
import subprocess

from asgk_lib.common import ROOT, normalize_repo_path


def git_output(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(args, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return result.returncode, result.stdout.strip()


def _normalized_lines(output: str) -> list[str]:
    return [normalize_repo_path(line) for line in output.splitlines() if normalize_repo_path(line)]


def live_workspace_state(base_ref: str) -> dict[str, object]:
    branch_code, branch_output = git_output(["git", "branch", "--show-current"])
    branch = branch_output if branch_code == 0 else ""

    upstream_code, upstream_output = git_output(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    upstream = upstream_output if upstream_code == 0 else ""

    untracked_code, untracked_output = git_output(["git", "ls-files", "--others", "--exclude-standard"])
    untracked_paths = _normalized_lines(untracked_output) if untracked_code == 0 else []

    diff_code, diff_output = git_output(["git", "diff", "--name-only"])
    cached_code, cached_output = git_output(["git", "diff", "--cached", "--name-only"])
    changed_paths = sorted({
        path
        for output in (
            diff_output if diff_code == 0 else "",
            cached_output if cached_code == 0 else "",
            untracked_output if untracked_code == 0 else "",
        )
        for path in _normalized_lines(output)
    })

    merged_into_base = False
    merged_check_error = ""
    if branch:
        merged_code, merged_output = git_output(["git", "branch", "--merged", base_ref, "--format", "%(refname:short)"])
        if merged_code == 0:
            merged_into_base = branch in {
                line.strip()
                for line in merged_output.splitlines()
                if line.strip()
            }
        else:
            merged_check_error = merged_output or f"git branch --merged {base_ref} failed"

    return {
        "branch": branch,
        "upstream": upstream,
        "base_ref": base_ref,
        "merged_into_base": merged_into_base,
        "merged_check_error": merged_check_error,
        "untracked_paths": untracked_paths,
        "changed_paths": changed_paths,
    }


def workspace_state_findings(payload: dict[str, object], *, main_branch: str) -> list[dict[str, object]]:
    findings: list[dict[str, object]] = []

    def warn(field: str, reason: str, fix: str, **extra: object) -> None:
        findings.append({"severity": "WARN", "field": field, "reason": reason, "recommended_fix": fix, **extra})

    branch = str(payload.get("branch") or "")
    base_ref = str(payload.get("base_ref") or "origin/main")
    upstream = str(payload.get("upstream") or "")
    merged_into_base = bool(payload.get("merged_into_base"))
    merged_check_error = str(payload.get("merged_check_error") or "")
    untracked = payload.get("untracked_paths")
    untracked_paths = [str(path) for path in untracked] if isinstance(untracked, list) else []
    changed = payload.get("changed_paths")
    changed_paths = [str(path) for path in changed] if isinstance(changed, list) else []
    branch_is_stale = bool(payload.get("branch_is_stale"))
    if "branch_is_stale" not in payload:
        branch_is_stale = bool(branch and branch != main_branch and merged_into_base and not changed_paths)

    if not branch:
        warn("branch", "Current checkout appears to be detached or branch name is unavailable.", "Confirm the intended work branch before editing files.")
    elif branch_is_stale:
        warn("branch", f"Current branch `{branch}` is already merged into `{base_ref}`.", "Switch to main or create a fresh issue branch before starting a new work unit.")

    if branch != main_branch and not upstream:
        warn("upstream", f"Current branch `{branch or '<detached>'}` has no upstream branch recorded.", "Confirm branch tracking before relying on remote status.")

    if merged_check_error:
        warn("merged_into_base", f"Could not check whether the branch is merged into `{base_ref}`: {merged_check_error}", "Fetch the base ref or run the check again with a valid --base-ref.")

    if untracked_paths:
        warn(
            "untracked_paths",
            f"Workspace has {len(untracked_paths)} untracked path(s).",
            "Leave unrelated local artifacts alone, or intentionally move/remove them outside this work unit before validating changed-path scope.",
            paths=untracked_paths,
        )

    return findings


def print_workspace_state_result(
    payload: dict[str, object],
    findings: list[dict[str, object]],
    *,
    as_json: bool,
    strict: bool,
    expect_warnings: bool,
) -> int:
    result = "warn" if findings else "pass"
    output = {
        "result": result,
        "strict": strict,
        "expect_warnings": expect_warnings,
        "low_risk_inferred": False,
        "state": payload,
        "findings": findings,
    }
    if as_json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif findings:
        for finding in findings:
            paths = finding.get("paths")
            suffix = f" Paths: {', '.join(paths)}" if isinstance(paths, list) and paths else ""
            print(
                f"WARN: {finding['field']} - {finding['reason']} "
                f"Fix: {finding['recommended_fix']}{suffix}"
            )
        print("Workspace state check result: warn. No merge status was inferred.")
    else:
        print("Workspace state check passed. No merge status was inferred.")

    if expect_warnings and not findings:
        print("FAIL: expected workspace-state warnings, but none were reported.")
        return 1
    if strict and findings:
        return 1
    return 0
