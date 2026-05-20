#!/usr/bin/env python3
from __future__ import annotations
import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path

from asgk_lib.common import (
    ROOT,
    field_block_lines,
    field_block_text,
    field_value,
    has_see_chat,
    has_unresolved_todo,
    line_field_exists,
    list_field_has_material_item,
    markdown_headings,
    markdown_section,
    normalize_repo_path,
    normalized_field_value,
    read_changed_paths,
    read_text,
    rel,
    same_repo_path,
    yaml_quote,
)
from asgk_lib.compact_handoff import compact_handoff_check
from asgk_lib.compact_target_upgrade import compact_target_upgrade_check
from asgk_lib.release_state import check_release_state_docs
from asgk_lib.status_policy import (
    CANONICAL_CURRENT_STATUS_PATH,
    CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS,
    CURRENT_STATUS_IMPACT_ALLOWED_VALUES,
    CURRENT_STATUS_IMPACT_REQUIRED_FIELDS,
    EMPTY_FOLLOWUP_VALUES,
    TRUE_VALUES,
)
from asgk_lib.target_install import (
    print_target_install_findings,
    target_install_findings,
)
from asgk_lib.text_fields import (
    material_items,
    parse_markdown_task_field_sections,
    parse_simple_task_packet_yaml,
    task_packet_yaml_source,
)
from asgk_lib.negative import (
    NEGATIVE_CASE_CHOICES,
    run_changed_path_hygiene_checks,
    run_negative_case,
    run_textual_negative_checks,
)
from asgk_lib.workspace_state import (
    live_workspace_state,
    print_workspace_state_result,
    workspace_state_findings,
)

PR_REQUIRED_HEADINGS = [
    "Summary", "Task Reference", "Changed Files", "Validation",
    "Evidence Of Completion", "Scope Boundaries", "Current Status Impact",
    "Runtime Output Status", "Merge Decision", "Known Gaps", "Handoff Report",
]
MERGE_DECISION_REQUIRED_FIELDS = [
    "issue", "lane", "intelligence_level", "durable_source_of_truth",
    "checks_passed", "allowed_paths_checked", "expected_output_checked",
    "contracts_checked", "schemas_checked", "storage_boundary",
    "runtime_artifact_boundary", "safety_review", "human_gates_checked",
    "result", "reason",
]
TASK_PACKET_REQUIRED_FIELDS = [
    "task_id",
    "lane",
    "intelligence_level",
    "intelligence_level_reason",
    "durable_source_of_truth",
    "objective",
    "product_context",
    "current_repository_context",
    "files_to_inspect_first",
    "allowed_paths",
    "expected_changes",
    "expected_output",
    "non_goals",
    "constraints",
    "plan",
    "checklist",
    "acceptance_sheet",
    "validation_commands",
    "stop_conditions",
    "rollback_expectations",
]
WORK_UNIT_REQUIRED_FIELDS = [
    "lane",
    "intelligence_level",
    "reason",
    "durable_source_of_truth",
    "objective",
    "plan",
    "checklist",
    "acceptance_sheet",
    "allowed_paths",
    "expected_output",
    "non_goals",
    "stop_conditions",
    "rollback_expectations",
]
WORK_UNIT_FIELD_ALIASES = {
    "reason": ["reason", "intelligence_level_reason"],
}
TASK_PACKET_LIST_FIELDS = [
    "files_to_inspect_first",
    "allowed_paths",
    "expected_changes",
    "non_goals",
    "constraints",
    "plan",
    "checklist",
    "acceptance_sheet",
    "validation_commands",
    "stop_conditions",
]
TASK_PACKET_SCALAR_FIELDS = [
    field for field in TASK_PACKET_REQUIRED_FIELDS if field not in TASK_PACKET_LIST_FIELDS
]
TASK_PACKET_ALLOWED_INTELLIGENCE_LEVELS = {
    "fast_basic",
    "standard",
    "advanced",
    "frontier",
}
HANDOFF_REQUIRED_FIELDS = [
    "active_issue", "active_pr", "branch", "objective", "current_state",
    "completed", "remaining", "allowed_paths", "modified_files",
    "validation_status", "blockers", "next_safe_action", "must_read",
    "must_not_do", "decisions", "open_questions",
]
HANDOFF_REQUIRED_LIST_FIELDS = [
    "completed", "remaining", "allowed_paths", "modified_files", "must_read",
    "must_not_do", "decisions", "open_questions",
]
HANDOFF_REQUIRED_SCALAR_FIELDS = ["active_issue"]
STATUS_REQUIRED_HEADINGS = [
    "Durable source of truth", "Current snapshot", "Active work",
    "Current validation entrypoint", "Closed gates", "Last completed",
    "Runtime artifact status", "Next safe action",
]
STATUS_FORBIDDEN_HISTORY_HEADINGS = [
    "History", "Work Log", "Chronological Log", "Completed Work Log",
]
STATUS_FORBIDDEN_PHRASES = [
    "full PR body", "raw CI log", "chat transcript", "see chat",
]
CONTEXT_TOKEN_ESTIMATE_CHARS_PER_TOKEN = 4
CONTEXT_MEASUREMENT_METHOD = (
    "estimated_repo_context_tokens = ceil(characters / 4); repo files only; "
    "excludes issue/PR text, system prompt, chat, tool output, model completion, "
    "and provider billing usage."
)
CONTEXT_PSEUDO_REFS = {
    "current github issue or pr",
    "current issue or pr",
    "current issue",
    "current pr",
    "open prs or current issue when relevant",
    "target file",
}
DOCS_ONLY_PRIMARY_PATH_PREFIXES = (
    "docs/control/",
    "docs/bootstrap/",
)
DOCS_ONLY_PRIMARY_PATHS = {
    "docs/control",
    "docs/bootstrap",
    "docs/DOCUMENT_MAP.md",
    "docs/DOCUMENT_REGISTRY.md",
    "docs/EVOLUTION_MODEL.md",
    "docs/QUICKSTART.md",
    "docs/INSTALL_SURFACE.md",
    "docs/SKILL_PACK.md",
}
OVERBROAD_FILES_TO_INSPECT_REFS = {
    ".",
    "/",
    "*",
    "**",
    "repo",
    "repository",
    "whole repo",
    "whole repository",
    "entire repo",
    "entire repository",
    "full repo",
    "full repository",
    "everything",
    "all files",
    "all docs",
    "all documents",
    "docs",
    "docs/",
    "docs/*",
    "docs/**",
    "docs/control",
    "docs/control/",
    "docs/control/*",
    "docs/control/**",
    "docs/bootstrap",
    "docs/bootstrap/",
    "docs/bootstrap/*",
    "docs/bootstrap/**",
}
def run_command(args: list[str], *, cwd: Path = ROOT) -> int:
    print("+ " + " ".join(args))
    return subprocess.run(args, cwd=cwd).returncode


def run_many(commands: list[list[str]]) -> int:
    failures = 0
    for command in commands:
        if run_command(command) != 0:
            failures += 1
    if failures:
        print(f"FAIL: {failures} command(s) failed.")
        return 1
    return 0


def run_policy_gate(pr_body: str | Path, *, as_json: bool = False) -> int:
    command = ["python3", "scripts/policy_gate_check.py", "--pr-body", str(pr_body)]
    if as_json:
        command.append("--json")
    return subprocess.run(command, cwd=ROOT).returncode


def run_policy_gate_capture(pr_body: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", "scripts/policy_gate_check.py", "--pr-body", str(pr_body)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def run_hygiene_capture(paths: list[str]) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmpdir:
        paths_file = Path(tmpdir) / "changed_paths.txt"
        paths_file.write_text("\n".join(paths) + ("\n" if paths else ""), encoding="utf-8")
        return subprocess.run(
            ["python3", "scripts/governance_hygiene.py", "--paths-file", str(paths_file)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )


def load_git_changed_paths(git_base: str, git_head: str) -> list[str]:
    if git_head.upper() in {"WORKTREE", "WT"}:
        diff_result = subprocess.run(
            ["git", "diff", "--name-only", git_base],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if diff_result.returncode != 0:
            raise RuntimeError(diff_result.stdout.strip() or "git diff failed")
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if untracked_result.returncode != 0:
            raise RuntimeError(untracked_result.stdout.strip() or "git ls-files failed")
        paths = {
            normalize_repo_path(line)
            for output in (diff_result.stdout, untracked_result.stdout)
            for line in output.splitlines()
            if normalize_repo_path(line)
        }
        return sorted(paths)

    result = subprocess.run(
        ["git", "diff", "--name-only", git_base, git_head],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or "git diff failed")
    return [
        normalize_repo_path(line)
        for line in result.stdout.splitlines()
        if normalize_repo_path(line)
    ]


def read_changed_path_list(path: str | Path) -> list[str]:
    return [
        normalize_repo_path(line)
        for line in read_text(path).splitlines()
        if normalize_repo_path(line) and not normalize_repo_path(line).startswith("#")
    ]


def git_remote_repo_slug() -> str:
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or "git remote get-url origin failed")
    remote = result.stdout.strip()
    match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)(?:\.git)?$", remote)
    if not match:
        raise RuntimeError(f"cannot infer GitHub repo from origin remote: {remote}")
    return f"{match.group('owner')}/{match.group('repo')}"


def load_live_work_unit(kind: str, number: str) -> dict[str, object]:
    repo = git_remote_repo_slug()
    endpoint = (
        f"repos/{repo}/issues/{number}"
        if kind == "issue"
        else f"repos/{repo}/pulls/{number}"
    )
    result = subprocess.run(
        ["gh", "api", endpoint],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f"gh api {endpoint} failed")
    payload = json.loads(result.stdout)
    if not isinstance(payload, dict):
        raise RuntimeError("GitHub work-unit payload must be a JSON object")
    payload["_asgk_requested_kind"] = kind
    return payload


def load_work_unit_payload(args: argparse.Namespace) -> dict[str, object]:
    sources = [bool(args.issue), bool(args.pr), bool(args.json_file)]
    if sum(sources) != 1:
        raise ValueError("provide exactly one of --issue, --pr, or --json-file")
    if args.json_file:
        payload = json.loads(read_text(args.json_file))
        if not isinstance(payload, dict):
            raise ValueError("work-unit JSON fixture must be an object")
        return payload
    if args.issue:
        return load_live_work_unit("issue", str(args.issue).lstrip("#"))
    return load_live_work_unit("pr", str(args.pr).lstrip("#"))


def work_unit_kind(payload: dict[str, object]) -> str:
    explicit = str(payload.get("kind") or payload.get("_asgk_requested_kind") or "").lower()
    if explicit in {"issue", "pr"}:
        return explicit
    if "pull_request" in payload or "merged" in payload or "mergeable" in payload:
        return "pr"
    return "issue"


def path_matches_allowed(path: str, allowed_path: str) -> bool:
    path = normalize_repo_path(path)
    allowed = normalize_repo_path(allowed_path).strip('"').strip("'")
    if not allowed or allowed in {"none", "none_for_source_only_release_execution"}:
        return False
    if allowed.endswith("/**"):
        return path.startswith(allowed[:-3].rstrip("/") + "/")
    if allowed.endswith("/"):
        return path.startswith(allowed)
    if any(char in allowed for char in "*?[]"):
        return fnmatch.fnmatchcase(path, allowed)
    return path == allowed


def parse_work_unit_task_fields(body: str) -> dict[str, object]:
    fields = parse_markdown_task_field_sections(body)
    fields.update(parse_simple_task_packet_yaml(body))
    return fields


def work_unit_field_value(fields: dict[str, object], field: str) -> object | None:
    for candidate in WORK_UNIT_FIELD_ALIASES.get(field, [field]):
        if candidate in fields:
            return fields[candidate]
    return None


def work_unit_required_field_failures(fields: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for field in WORK_UNIT_REQUIRED_FIELDS:
        value = work_unit_field_value(fields, field)
        if not material_items(value):
            failures.append(f"Work-unit body missing material required task field: {field}")
    return failures


def extract_allowed_paths(body: str) -> list[str]:
    fields = parse_work_unit_task_fields(body)
    return [
        normalize_repo_path(item)
        for item in material_items(fields.get("allowed_paths"))
    ]


def canonical_issue_scope_from_payload(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    kind = work_unit_kind(payload)
    number = payload.get("number")
    state = str(payload.get("state") or "").lower()
    title = str(payload.get("title") or "")
    fields = parse_work_unit_task_fields(str(payload.get("body") or ""))
    findings: list[dict[str, str]] = []
    canonical_fields: dict[str, list[str]] = {}

    if kind != "issue":
        findings.append({
            "field": "kind",
            "reason": f"canonical issue scope requires an issue payload, got {kind}",
        })

    for field in WORK_UNIT_REQUIRED_FIELDS:
        value = work_unit_field_value(fields, field)
        items = material_items(value)
        if field == "allowed_paths":
            items = [normalize_repo_path(item) for item in items]
        if not items:
            findings.append({
                "field": field,
                "reason": "missing material issue scope field",
            })
        canonical_fields[field] = items

    canonical_issue_scope = {
        "version": "asgk.compact_issue_scope.v1",
        "source": {
            "kind": kind,
            "number": number,
            "state": state,
            "title": title,
        },
        "required_fields": WORK_UNIT_REQUIRED_FIELDS,
        "fields": canonical_fields,
        "allowed_paths": canonical_fields.get("allowed_paths", []),
        "scope_rules": {
            "task_packet_may_narrow": True,
            "task_packet_must_not_expand": True,
            "low_risk_inferred": False,
        },
    }

    result = "fail" if findings else "pass"
    return result, {
        "result": result,
        "issue": number,
        "canonical_issue_scope": canonical_issue_scope,
        "low_risk_inferred": False,
        "findings": findings,
    }


def compact_scope_lock_from_payload(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    scope_result, scope_output = canonical_issue_scope_from_payload(payload)
    number = scope_output.get("issue")
    findings: list[dict[str, str]] = list(scope_output.get("findings", []))
    canonical_issue_scope = scope_output.get("canonical_issue_scope")

    if scope_result != "pass" or not isinstance(canonical_issue_scope, dict):
        return "fail", {
            "result": "fail",
            "issue": number,
            "low_risk_inferred": False,
            "findings": findings,
        }

    encoded = json.dumps(canonical_issue_scope, sort_keys=True, separators=(",", ":")).encode("utf-8")
    scope_hash = hashlib.sha256(encoded).hexdigest()
    scope_lock = {
        "version": "asgk.compact_scope_lock.v1",
        "issue": number,
        "scope_hash": scope_hash,
        "canonical_issue_scope_version": canonical_issue_scope.get("version"),
        "allowed_paths": canonical_issue_scope.get("allowed_paths", []),
        "low_risk_inferred": False,
    }
    return "pass", {
        "result": "pass",
        "issue": number,
        "scope_hash": scope_hash,
        "allowed_paths": canonical_issue_scope.get("allowed_paths", []),
        "scope_lock": scope_lock,
        "canonical_issue_scope": canonical_issue_scope,
        "low_risk_inferred": False,
        "findings": [],
    }


def extract_scope_hash(payload: dict[str, object]) -> str:
    scope_lock = payload.get("scope_lock")
    if isinstance(scope_lock, dict):
        return str(scope_lock.get("scope_hash") or "")
    return str(payload.get("scope_hash") or "")


def compare_scope_lock(current: dict[str, object], captured: dict[str, object]) -> list[dict[str, str]]:
    current_hash = extract_scope_hash(current)
    captured_hash = extract_scope_hash(captured)
    findings: list[dict[str, str]] = []
    if not captured_hash:
        findings.append({
            "field": "compare_file",
            "reason": "captured scope lock is missing scope_hash",
        })
    if not current_hash:
        findings.append({
            "field": "scope_hash",
            "reason": "current scope lock is missing scope_hash",
        })
    if current_hash and captured_hash and current_hash != captured_hash:
        findings.append({
            "field": "scope_hash",
            "reason": "captured scope lock does not match current issue scope",
        })
    return findings


def compact_pr_report_restricted_boundaries(paths: list[str]) -> list[str]:
    boundaries: list[str] = []
    boundary_patterns = [
        "AGENTS.md",
        "CLAUDE.md",
        ".github/**",
        ".codex/**",
        ".claude/**",
        "docs/control/**",
        "schemas/**",
        "contracts/**",
    ]
    for path in paths:
        normalized = normalize_repo_path(path)
        for pattern in boundary_patterns:
            if path_matches_allowed(normalized, pattern):
                boundaries.append(pattern)
                break
    return sorted(set(boundaries))


def compact_pr_report_status_checks(status_rollup: object) -> list[dict[str, str]]:
    checks: list[dict[str, str]] = []
    if not isinstance(status_rollup, list):
        return checks
    for item in status_rollup:
        if not isinstance(item, dict):
            continue
        checks.append({
            "name": str(item.get("name") or item.get("context") or "unnamed_check"),
            "status": str(item.get("status") or ""),
            "conclusion": str(item.get("conclusion") or ""),
            "details_url": str(item.get("detailsUrl") or item.get("targetUrl") or ""),
        })
    return checks


def compact_pr_report_agent_claims(payload: dict[str, object], body: str) -> dict[str, object]:
    merge_section = markdown_section(body, "Merge Decision")
    pr_body_claims = {
        "merge_decision_result": normalized_field_value(merge_section, "result"),
        "checks_passed": normalized_field_value(merge_section, "checks_passed"),
        "human_gates_checked": normalized_field_value(merge_section, "human_gates_checked"),
        "validation_evidence_checked": normalized_field_value(merge_section, "validation_evidence_checked"),
    }
    merge_ready_claimed = pr_body_claims["merge_decision_result"] == "merge_allowed"
    human_gate_claimed = pr_body_claims["human_gates_checked"] in TRUE_VALUES
    sources = ["pr_body.merge_decision.result"] if merge_ready_claimed else []
    if human_gate_claimed:
        sources.append("pr_body.human_gates_checked")

    fixture_claims: dict[str, object] = {}
    raw_fixture_claims = payload.get("agent_claims")
    if isinstance(raw_fixture_claims, dict):
        fixture_claims = dict(raw_fixture_claims)
        fixture_merge_result = str(fixture_claims.get("merge_result") or "").lower()
        if fixture_merge_result == "merge_allowed":
            merge_ready_claimed = True
            sources.append("agent_claims.merge_result")
        if fixture_claims.get("auto_merge_eligible") is True:
            merge_ready_claimed = True
            sources.append("agent_claims.auto_merge_eligible")
        if fixture_claims.get("human_gates_checked") is True:
            human_gate_claimed = True
            sources.append("agent_claims.human_gates_checked")

    return {
        "merge_ready_claimed": merge_ready_claimed,
        "human_gate_claimed": human_gate_claimed,
        "claim_sources": sorted(set(sources)),
        "pr_body": pr_body_claims,
        "fixture": fixture_claims,
    }


def compact_pr_report_claim_conflict_findings(
    agent_claims: dict[str, object],
    tool_findings: list[dict[str, str]],
    human_gate_findings: list[dict[str, str]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    if (tool_findings or human_gate_findings) and agent_claims.get("merge_ready_claimed") is True:
        findings.append({
            "field": "agent_claims",
            "reason": "agent-authored merge-ready claim conflicts with tool-derived blocking state",
        })
    if human_gate_findings and agent_claims.get("human_gate_claimed") is True:
        findings.append({
            "field": "agent_claims",
            "reason": "agent-authored human-gate claim conflicts with tool-derived restricted-boundary state",
        })
    return findings


def compact_pr_report_from_payload(payload: dict[str, object]) -> tuple[str, dict[str, object]]:
    if payload.get("metadata_available") is False:
        return "fail_closed", {
            "result": "fail_closed",
            "low_risk_inferred": False,
            "findings": [{
                "field": "metadata_available",
                "reason": "GitHub PR metadata is unavailable",
            }],
        }

    pr_number = payload.get("number")
    body = str(payload.get("body") or "")
    agent_claims = compact_pr_report_agent_claims(payload, body)
    changed_paths = pr_file_paths(payload.get("files"))
    issue_number = merge_decision_issue_number(body)
    issue_payload = pr_status_issue_payload(payload, issue_number) if issue_number is not None else None

    issue_scope_output: dict[str, object] | None = None
    scope_lock_output: dict[str, object] | None = None
    findings: list[dict[str, str]] = []

    if issue_number is None:
        findings.append({
            "field": "issue",
            "reason": "Merge Decision issue is missing",
        })
    elif issue_payload is None:
        findings.append({
            "field": "issue",
            "reason": f"closing issue #{issue_number} metadata is unavailable",
        })
    else:
        scope_result, issue_scope_output = canonical_issue_scope_from_payload(issue_payload)
        if scope_result != "pass":
            for finding in issue_scope_output.get("findings", []):
                if isinstance(finding, dict):
                    findings.append({
                        "field": str(finding.get("field") or "issue_scope"),
                        "reason": str(finding.get("reason") or "canonical issue scope failed"),
                    })
        lock_result, scope_lock_output = compact_scope_lock_from_payload(issue_payload)
        if lock_result != "pass":
            for finding in scope_lock_output.get("findings", []):
                if isinstance(finding, dict):
                    findings.append({
                        "field": str(finding.get("field") or "scope_lock"),
                        "reason": str(finding.get("reason") or "scope lock failed"),
                    })

    pr_status_result, pr_status_findings = check_pr_status_payload(payload)
    for finding in pr_status_findings:
        findings.append({
            "field": str(finding.get("field") or "pr_status"),
            "reason": str(finding.get("reason") or "PR status check failed"),
        })

    restricted_boundaries = compact_pr_report_restricted_boundaries(changed_paths)
    human_gate_findings = [
        {
            "field": "restricted_boundaries",
            "reason": "restricted boundary requires human review: " + ", ".join(restricted_boundaries),
        }
    ] if restricted_boundaries else []
    findings.extend(compact_pr_report_claim_conflict_findings(
        agent_claims,
        findings,
        human_gate_findings,
    ))

    derived_state = "fail" if findings else ("requires_human" if restricted_boundaries else "checkable_pass")
    result = "fail" if findings else ("requires_human" if restricted_boundaries else "pass")
    return result, {
        "result": result,
        "derived_state": derived_state,
        "low_risk_inferred": False,
        "agent_claims": agent_claims,
        "pr": {
            "number": pr_number,
            "url": payload.get("url"),
            "state": payload.get("state"),
            "is_draft": payload.get("isDraft"),
            "merge_state": payload.get("mergeStateStatus"),
            "review_decision": payload.get("reviewDecision"),
            "changed_paths": changed_paths,
            "status_checks": compact_pr_report_status_checks(payload.get("statusCheckRollup")),
            "closing_issue": issue_number,
        },
        "issue_scope": issue_scope_output.get("canonical_issue_scope") if issue_scope_output else None,
        "scope_lock": scope_lock_output.get("scope_lock") if scope_lock_output else None,
        "restricted_boundaries": restricted_boundaries,
        "human_gate_findings": human_gate_findings,
        "pr_status_result": pr_status_result,
        "findings": findings,
    }


def check_work_unit_payload(
    payload: dict[str, object],
    changed_paths: list[str],
) -> tuple[str, list[dict[str, object]], list[str]]:
    findings: list[dict[str, object]] = []
    kind = work_unit_kind(payload)
    number = payload.get("number")
    state = str(payload.get("state") or "").lower()
    body = str(payload.get("body") or "")

    def add(field: str, reason: str, fix: str) -> None:
        findings.append({
            "severity": "FAIL",
            "field": field,
            "reason": reason,
            "recommended_fix": fix,
        })

    if kind == "issue":
        if "pull_request" in payload:
            add(
                "kind",
                f"Work unit #{number or 'unknown'} is a pull request, not an issue.",
                "Use --pr for PR follow-up work or select an open issue with allowed_paths.",
            )
        if state != "open":
            add(
                "state",
                f"Issue state is not open: {state or 'missing'}.",
                "Select an open issue or create a new durable issue before changing files.",
            )
    elif kind == "pr":
        merged = payload.get("merged")
        if state not in {"open"} or merged is True:
            add(
                "state",
                f"PR state is not open or is already merged: state={state or 'missing'}, merged={merged}.",
                "Use only an open PR that still needs follow-up fixes, or create a new issue.",
            )
    else:
        add("kind", f"Unknown work-unit kind: {kind}", "Provide an issue or PR payload.")

    if has_see_chat(body):
        add(
            "body",
            "Work-unit body contains chat-only authority phrase: see chat.",
            "Move scope, acceptance, and handoff authority into the issue, PR, or repo docs.",
        )

    task_fields = parse_work_unit_task_fields(body)
    for failure in work_unit_required_field_failures(task_fields):
        add(
            "required_task_fields",
            failure,
            "Add the missing field to the GitHub issue, PR, or task packet before changing files.",
        )

    allowed_paths = extract_allowed_paths(body)
    if not allowed_paths:
        add(
            "allowed_paths",
            "Work-unit body does not include material allowed_paths.",
            "Add explicit allowed_paths to the GitHub issue, PR, or task packet.",
        )

    normalized_changed_paths = [normalize_repo_path(path) for path in changed_paths if normalize_repo_path(path)]
    if not normalized_changed_paths:
        add(
            "changed_paths",
            "No changed paths were provided or detected.",
            "Run this check with --paths-file or --git-base/--git-head after creating a bounded diff.",
        )

    unauthorized = [
        path for path in normalized_changed_paths
        if allowed_paths and not any(path_matches_allowed(path, allowed) for allowed in allowed_paths)
    ]
    for path in unauthorized:
        add(
            "changed_paths",
            f"Changed path is outside allowed_paths: {path}",
            "Remove the change, update the durable issue before writing, or create a separate issue.",
        )

    hygiene = run_hygiene_capture(normalized_changed_paths)
    if hygiene.returncode != 0:
        add(
            "changed_paths",
            "Changed-path hygiene failed for the supplied paths.",
            "Remove protected/runtime/private-source-like paths or keep the work human-gated.",
        )

    return ("fail" if findings else "pass"), findings, allowed_paths


def print_work_unit_result(
    payload: dict[str, object],
    result: str,
    findings: list[dict[str, object]],
    allowed_paths: list[str],
    changed_paths: list[str],
    *,
    as_json: bool,
) -> int:
    output = {
        "result": result,
        "low_risk_inferred": False,
        "work_unit": {
            "kind": work_unit_kind(payload),
            "number": payload.get("number"),
            "state": payload.get("state"),
            "url": payload.get("html_url") or payload.get("url"),
        },
        "allowed_paths": allowed_paths,
        "changed_paths": changed_paths,
        "findings": findings,
    }
    if as_json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif findings:
        for finding in findings:
            print(
                f"{finding['severity']}: {finding['field']} - "
                f"{finding['reason']} Fix: {finding['recommended_fix']}"
            )
        print("Work-unit check result: fail. No low-risk status was inferred.")
    else:
        print("Work-unit check passed. No low-risk status was inferred.")
    return 1 if findings else 0


def load_task_packet_payload(path: str | Path) -> tuple[dict[str, object], str]:
    text = read_text(path)
    if path_str := str(path):
        if path_str.endswith(".json"):
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError("task packet JSON must be an object")
            candidate = payload.get("bad_input") or payload.get("task_packet") or payload
            if not isinstance(candidate, dict):
                raise ValueError("bad_input or task_packet must be an object")
            return candidate, text
    source = task_packet_yaml_source(text)
    return parse_simple_task_packet_yaml(source), text


def context_ref_text(value: object) -> str:
    return normalize_repo_path(str(value).strip().strip('"').strip("'"))


def normalized_context_ref(value: object) -> str:
    return context_ref_text(value).lower()


def task_packet_files_to_inspect_first(packet: dict[str, object]) -> list[str]:
    value = packet.get("files_to_inspect_first")
    if not isinstance(value, list):
        return []
    return [context_ref_text(item) for item in value if str(item).strip().strip('"').strip("'")]


def task_packet_allowed_paths(packet: dict[str, object]) -> list[str]:
    value = packet.get("allowed_paths")
    if not isinstance(value, list):
        return []
    return [context_ref_text(item) for item in value if str(item).strip().strip('"').strip("'")]


def task_packet_scalar(packet: dict[str, object], field: str) -> str:
    value = packet.get(field)
    if isinstance(value, str):
        return value.strip()
    return ""


def has_github_issue_or_pr_ref(value: object) -> bool:
    text = str(value).strip().lower()
    if not text:
        return False
    if re.search(r"github\.com/.+/(issues|pull)/\d+", text):
        return True
    if re.search(r"\b(github[ -]?)?(issue|pr|pull request)\s*#?\d+\b", text):
        return True
    return bool(re.search(r"^#\d+\b", text))


def task_packet_github_issue_unavailable(packet: dict[str, object]) -> bool:
    return task_packet_scalar(packet, "github_issue_status").lower() == "pending_unavailable"


def task_packet_docs_only_primary_allowed(packet: dict[str, object]) -> bool:
    kind = task_packet_scalar(packet, "work_unit_kind").lower().replace("-", "_").replace(" ", "_")
    if kind not in {"docs_only_planning", "docs_only_control"}:
        return False
    allowed_paths = task_packet_allowed_paths(packet)
    return bool(allowed_paths) and all(is_docs_only_primary_path(path) for path in allowed_paths)


def is_docs_only_primary_path(path: object) -> bool:
    normalized = normalize_repo_path(str(path).strip().strip('"').strip("'"))
    return normalized in DOCS_ONLY_PRIMARY_PATHS or normalized.startswith(DOCS_ONLY_PRIMARY_PATH_PREFIXES)


def task_packet_issue_first_failures(packet: dict[str, object]) -> list[str]:
    source = task_packet_scalar(packet, "durable_source_of_truth")
    if has_github_issue_or_pr_ref(source):
        return []
    if task_packet_github_issue_unavailable(packet):
        return []
    if task_packet_docs_only_primary_allowed(packet):
        return []
    return [
        "executable task packet durable_source_of_truth must name a GitHub issue or PR when GitHub is available; "
        "task packets may refine issue scope but must not replace it, except for docs-only planning/control paths"
    ]


def is_context_pseudo_ref(value: object) -> bool:
    return normalized_context_ref(value) in CONTEXT_PSEUDO_REFS


def is_overbroad_files_to_inspect_ref(value: object) -> bool:
    ref = context_ref_text(value)
    lowered = ref.lower()
    if lowered in OVERBROAD_FILES_TO_INSPECT_REFS:
        return True
    if any(char in ref for char in "*?[]"):
        return True
    if is_context_pseudo_ref(ref):
        return False
    candidate = rel(ref)
    return candidate.exists() and candidate.is_dir()


def task_packet_context_ref_failures(packet: dict[str, object]) -> list[str]:
    failures: list[str] = []
    for item in task_packet_files_to_inspect_first(packet):
        if is_overbroad_files_to_inspect_ref(item):
            failures.append(f"files_to_inspect_first contains overbroad read request: {item}")
    return failures


def estimate_tokens_from_characters(characters: int) -> int:
    if characters <= 0:
        return 0
    return (characters + CONTEXT_TOKEN_ESTIMATE_CHARS_PER_TOKEN - 1) // CONTEXT_TOKEN_ESTIMATE_CHARS_PER_TOKEN


def context_budget_measurement(packet: dict[str, object]) -> dict[str, object]:
    files: list[dict[str, object]] = []
    missing_refs: list[str] = []
    pseudo_refs: list[str] = []
    overbroad_refs: list[str] = []
    read_errors: list[dict[str, str]] = []
    total_bytes = 0
    total_characters = 0

    for ref in task_packet_files_to_inspect_first(packet):
        if is_overbroad_files_to_inspect_ref(ref):
            overbroad_refs.append(ref)
            continue
        if is_context_pseudo_ref(ref):
            pseudo_refs.append(ref)
            continue
        path = rel(ref)
        if not path.exists():
            missing_refs.append(ref)
            continue
        if path.is_dir():
            overbroad_refs.append(ref)
            continue
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            read_errors.append({"path": ref, "error": f"utf-8 decode failed: {exc}"})
            continue
        total_bytes += len(raw)
        total_characters += len(text)
        files.append({
            "path": ref,
            "bytes": len(raw),
            "characters": len(text),
            "estimated_tokens": estimate_tokens_from_characters(len(text)),
        })

    return {
        "files": files,
        "files_count": len(files),
        "bytes": total_bytes,
        "characters": total_characters,
        "estimated_repo_context_tokens": estimate_tokens_from_characters(total_characters),
        "measurement_method": CONTEXT_MEASUREMENT_METHOD,
        "actual_model_tokens": "unavailable",
        "actual_model_token_source": "not_provided",
        "pseudo_refs": pseudo_refs,
        "missing_refs": missing_refs,
        "overbroad_refs": overbroad_refs,
        "read_errors": read_errors,
        "limits": (
            "Estimate covers UTF-8 text from repo files named in files_to_inspect_first only; "
            "it does not include GitHub issue or PR body text, system/developer prompts, chat history, "
            "tool output, retrieved web/app content, or model completion tokens."
        ),
    }


def print_context_budget_measurement(measurement: dict[str, object], *, as_json: bool) -> int:
    blocking = bool(measurement["missing_refs"] or measurement["overbroad_refs"] or measurement["read_errors"])
    if as_json:
        payload = {"result": "fail" if blocking else "pass", **measurement}
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print("Context budget measurement:")
        print(f"files_count: {measurement['files_count']}")
        print(f"bytes: {measurement['bytes']}")
        print(f"characters: {measurement['characters']}")
        print(f"estimated_repo_context_tokens: {measurement['estimated_repo_context_tokens']}")
        print(f"measurement_method: {measurement['measurement_method']}")
        print(f"actual_model_tokens: {measurement['actual_model_tokens']}")
        print(f"actual_model_token_source: {measurement['actual_model_token_source']}")
        for field in ["pseudo_refs", "missing_refs", "overbroad_refs", "read_errors"]:
            values = measurement[field]
            if values:
                print(f"{field}:")
                for value in values:
                    print(f"- {value}")
            else:
                print(f"{field}: none")
        print(f"limits: {measurement['limits']}")
    return 1 if blocking else 0


def task_packet_schema_failures(packet: dict[str, object], source_text: str) -> list[str]:
    failures: list[str] = []
    for field in TASK_PACKET_REQUIRED_FIELDS:
        if field not in packet:
            failures.append(f"missing task packet field: {field}")

    for field in TASK_PACKET_SCALAR_FIELDS:
        if field in packet:
            value = packet[field]
            if not isinstance(value, str) or not value.strip():
                failures.append(f"{field} must be a non-empty scalar")

    for field in TASK_PACKET_LIST_FIELDS:
        if field in packet:
            value = packet[field]
            if not isinstance(value, list):
                failures.append(f"{field} must be a list")
            elif not any(isinstance(item, str) and item.strip() for item in value):
                failures.append(f"{field} must contain at least one material item")

    intelligence_level = str(packet.get("intelligence_level", "")).strip().strip('"').strip("'")
    if intelligence_level and intelligence_level not in TASK_PACKET_ALLOWED_INTELLIGENCE_LEVELS:
        failures.append(
            "intelligence_level must be one of: "
            + ", ".join(sorted(TASK_PACKET_ALLOWED_INTELLIGENCE_LEVELS))
        )

    if has_see_chat(source_text):
        failures.append("task packet contains forbidden chat-only authority phrase: see chat")

    failures.extend(task_packet_issue_first_failures(packet))
    failures.extend(task_packet_context_ref_failures(packet))

    return failures


def compact_task_packet_compare(
    issue_payload: dict[str, object],
    packet: dict[str, object],
    packet_source_text: str,
) -> tuple[str, dict[str, object]]:
    findings: list[dict[str, str]] = []
    for failure in task_packet_schema_failures(packet, packet_source_text):
        findings.append({
            "field": "task_packet",
            "reason": failure,
        })

    scope_result, scope_output = canonical_issue_scope_from_payload(issue_payload)
    if scope_result != "pass":
        for finding in scope_output.get("findings", []):
            if isinstance(finding, dict):
                findings.append({
                    "field": f"issue_scope.{finding.get('field') or 'unknown'}",
                    "reason": str(finding.get("reason") or "canonical issue scope failed"),
                })

    issue_scope = scope_output.get("canonical_issue_scope")
    issue_allowed_paths: list[str] = []
    if isinstance(issue_scope, dict):
        raw_allowed = issue_scope.get("allowed_paths")
        if isinstance(raw_allowed, list):
            issue_allowed_paths = [
                normalize_repo_path(str(item))
                for item in raw_allowed
                if normalize_repo_path(str(item))
            ]

    packet_allowed_paths = task_packet_allowed_paths(packet)
    for path in packet_allowed_paths:
        if issue_allowed_paths and not any(path_matches_allowed(path, allowed) for allowed in issue_allowed_paths):
            findings.append({
                "field": "task_packet.allowed_paths",
                "reason": f"task packet expands issue allowed_paths: {path}",
            })

    result = "fail" if findings else "pass"
    return result, {
        "result": result,
        "low_risk_inferred": False,
        "issue": scope_output.get("issue"),
        "issue_scope": issue_scope,
        "task_packet": {
            "allowed_paths": packet_allowed_paths,
            "may_narrow_issue_scope": True,
            "must_not_expand_issue_scope": True,
            "narrows_scope": bool(packet_allowed_paths)
            and sorted(packet_allowed_paths) != sorted(issue_allowed_paths),
        },
        "findings": findings,
    }


def compact_pr_body_check(body_file: str | Path, report_file: str | Path) -> tuple[str, dict[str, object]]:
    body_path = rel(body_file)
    report_path = rel(report_file)
    findings: list[dict[str, str]] = []

    if not body_path.exists():
        findings.append({"field": "body_file", "reason": f"PR body file does not exist: {body_file}"})
        body_text = ""
    else:
        body_text = body_path.read_text(encoding="utf-8")

    headings = markdown_headings(body_text)
    if "Compiled Report Reference" not in headings:
        findings.append({
            "field": "Compiled Report Reference",
            "reason": "compact PR body must include a Compiled Report Reference section",
        })
    else:
        report_section = markdown_section(body_text, "Compiled Report Reference")
        if not normalized_field_value(report_section, "report_source"):
            findings.append({
                "field": "report_source",
                "reason": "Compiled Report Reference must name report_source",
            })

    if body_path.exists():
        pr_body_result = subprocess.run(
            ["python3", "scripts/asgk.py", "pr-body-check", "--file", str(body_path)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if pr_body_result.returncode != 0:
            findings.append({
                "field": "pr_body_check",
                "reason": "compact PR body failed required PR body structure checks",
            })

        policy_gate = run_policy_gate_capture(body_path)
        if policy_gate.returncode != 0:
            findings.append({
                "field": "policy_gate",
                "reason": "compact PR body failed policy gate checks",
            })

    report: dict[str, object] = {}
    if not report_path.exists():
        findings.append({"field": "report_json", "reason": f"compact PR report file does not exist: {report_file}"})
    else:
        try:
            loaded_report = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append({"field": "report_json", "reason": f"invalid compact PR report JSON: {exc}"})
            loaded_report = {}
        if not isinstance(loaded_report, dict):
            findings.append({"field": "report_json", "reason": "compact PR report JSON must be an object"})
        else:
            report = loaded_report

    report_result = str(report.get("result") or "").lower()
    if report and report_result != "pass":
        findings.append({
            "field": "report.result",
            "reason": f"compiled report result is not pass: {report_result or 'missing'}",
        })

    pr_status_result = report.get("pr_status_result")
    if report and pr_status_result is not None and str(pr_status_result).lower() != "pass":
        findings.append({
            "field": "report.pr_status_result",
            "reason": f"compiled report PR status result is not pass: {pr_status_result}",
        })

    derived_state = str(report.get("derived_state") or "").lower()
    if report and derived_state != "checkable_pass":
        findings.append({
            "field": "report.derived_state",
            "reason": f"compiled report derived_state is not checkable_pass: {derived_state or 'missing'}",
        })

    if report and report.get("low_risk_inferred") is not False:
        findings.append({
            "field": "report.low_risk_inferred",
            "reason": "compiled report must explicitly keep low_risk_inferred false",
        })

    report_findings = report.get("findings")
    if isinstance(report_findings, list) and report_findings:
        findings.append({
            "field": "report.findings",
            "reason": "compiled report has blocking findings",
        })

    result = "fail" if findings else "pass"
    return result, {
        "result": result,
        "low_risk_inferred": False,
        "body_file": normalize_repo_path(str(body_file)),
        "report_file": normalize_repo_path(str(report_file)),
        "compiled_report": {
            "result": report.get("result"),
            "derived_state": report.get("derived_state"),
            "pr_status_result": report.get("pr_status_result"),
            "low_risk_inferred": report.get("low_risk_inferred"),
            "restricted_boundaries": report.get("restricted_boundaries"),
        },
        "findings": findings,
    }


def print_failures(failures: list[str]) -> int:
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1
    print("Check passed.")
    return 0


def add_pr_status_finding(
    findings: list[dict[str, str]],
    field: str,
    reason: str,
    recommended_fix: str,
) -> None:
    findings.append(
        {
            "severity": "FAIL",
            "field": field,
            "reason": reason,
            "recommended_fix": recommended_fix,
        }
    )


def check_status_rollup(status_rollup: object, findings: list[dict[str, str]]) -> None:
    if not isinstance(status_rollup, list) or not status_rollup:
        add_pr_status_finding(
            findings,
            "statusCheckRollup",
            "No status checks were reported for this PR.",
            "Wait for GitHub Actions or investigate missing required checks.",
        )
        return

    passing_conclusions = {"SUCCESS", "SKIPPED", "NEUTRAL"}
    for item in status_rollup:
        if not isinstance(item, dict):
            add_pr_status_finding(
                findings,
                "statusCheckRollup",
                "Status check entry is not an object.",
                "Fetch PR status with gh pr view --json statusCheckRollup.",
            )
            continue
        name = str(item.get("name") or item.get("context") or "unnamed_check")
        status = str(item.get("status") or "").upper()
        conclusion = str(item.get("conclusion") or "").upper()
        if status and status != "COMPLETED":
            add_pr_status_finding(
                findings,
                f"statusCheckRollup.{name}",
                f"Status check is not complete: {status}.",
                "Wait for the check to complete before merge eligibility.",
            )
        elif conclusion not in passing_conclusions:
            add_pr_status_finding(
                findings,
                f"statusCheckRollup.{name}",
                f"Status check conclusion is not passing: {conclusion or 'missing'}.",
                "Fix the failing check or keep the PR merge-blocked.",
            )


def pr_file_paths(files: object) -> list[str]:
    if not isinstance(files, list):
        return []
    paths: list[str] = []
    for item in files:
        if isinstance(item, str):
            paths.append(item)
        elif isinstance(item, dict):
            path = item.get("path") or item.get("filename")
            if path:
                paths.append(str(path))
    return paths


def issue_number_from_value(value: str | None) -> int | None:
    if not value:
        return None
    match = re.search(r"#\s*(\d+)\b", value)
    if not match:
        return None
    return int(match.group(1))


def merge_decision_issue_number(body: str) -> int | None:
    merge_decision = markdown_section(body, "Merge Decision")
    return issue_number_from_value(field_value(merge_decision, "issue"))


def closing_issue_numbers(references: object) -> set[int]:
    if not isinstance(references, list):
        return set()
    numbers: set[int] = set()
    for item in references:
        if not isinstance(item, dict):
            continue
        number = item.get("number")
        if isinstance(number, int):
            numbers.add(number)
        elif isinstance(number, str) and number.isdigit():
            numbers.add(int(number))
    return numbers


def check_closing_issue_reference(payload: dict[str, object], body: str, findings: list[dict[str, str]]) -> None:
    issue_number = merge_decision_issue_number(body)
    if issue_number is None:
        return

    if "closingIssuesReferences" not in payload:
        add_pr_status_finding(
            findings,
            "closingIssuesReferences",
            "PR closing issue references are missing from the metadata payload.",
            "Fetch PR metadata with gh pr view --json closingIssuesReferences or provide fixture metadata.",
        )
        return

    if issue_number not in closing_issue_numbers(payload.get("closingIssuesReferences")):
        add_pr_status_finding(
            findings,
            "closingIssuesReferences",
            f"Merge Decision issue #{issue_number} is not a GitHub closing issue reference.",
            f"Use a GitHub closing keyword such as `Closes #{issue_number}` instead of a non-closing reference.",
        )


def pr_status_issue_payload(payload: dict[str, object], issue_number: int) -> dict[str, object] | None:
    for key in ["issue", "closingIssue", "workUnit"]:
        candidate = payload.get(key)
        if isinstance(candidate, dict):
            number = candidate.get("number")
            if number == issue_number or str(number) == str(issue_number):
                return candidate

    references = payload.get("closingIssuesReferences")
    if isinstance(references, list):
        for item in references:
            if not isinstance(item, dict):
                continue
            number = item.get("number")
            if number == issue_number or str(number) == str(issue_number):
                if item.get("body") is not None:
                    return item

    if payload.get("_asgk_live_lookup") is True:
        try:
            return load_live_work_unit("issue", str(issue_number))
        except RuntimeError:
            return None
    return None


def check_pr_issue_allowed_paths(payload: dict[str, object], body: str, findings: list[dict[str, str]]) -> None:
    issue_number = merge_decision_issue_number(body)
    if issue_number is None:
        return
    if "files" not in payload:
        return

    issue_payload = pr_status_issue_payload(payload, issue_number)
    if issue_payload is None:
        add_pr_status_finding(
            findings,
            "issue.allowed_paths",
            f"Closing issue #{issue_number} body is unavailable for allowed_paths verification.",
            "Fetch live PR status with --pr or provide fixture issue metadata with body and allowed_paths.",
        )
        return

    issue_body = str(issue_payload.get("body") or "")
    allowed_paths = extract_allowed_paths(issue_body)
    if not allowed_paths:
        add_pr_status_finding(
            findings,
            "issue.allowed_paths",
            f"Closing issue #{issue_number} does not include material allowed_paths.",
            "Add explicit allowed_paths to the closing issue before merge eligibility.",
        )
        return

    for path in pr_file_paths(payload.get("files")):
        normalized = normalize_repo_path(path)
        if not any(path_matches_allowed(normalized, allowed) for allowed in allowed_paths):
            add_pr_status_finding(
                findings,
                "files.allowed_paths",
                f"PR file is outside closing issue allowed_paths: {normalized}",
                "Remove the file from this PR or update the durable issue before merge eligibility.",
            )


def check_pr_status_payload(payload: dict[str, object]) -> tuple[str, list[dict[str, str]]]:
    findings: list[dict[str, str]] = []

    if payload.get("state") != "OPEN":
        add_pr_status_finding(
            findings,
            "state",
            f"PR state is not OPEN: {payload.get('state') or 'missing'}.",
            "Validate only open PRs before merge eligibility.",
        )

    if payload.get("isDraft") is True:
        add_pr_status_finding(
            findings,
            "isDraft",
            "PR is still draft.",
            "Mark the PR ready for review only after gates are complete.",
        )

    merge_state = str(payload.get("mergeStateStatus") or "").upper()
    if merge_state != "CLEAN":
        add_pr_status_finding(
            findings,
            "mergeStateStatus",
            f"PR merge state is not CLEAN: {merge_state or 'missing'}.",
            "Resolve merge conflicts, blocked state, or pending mergeability before merge.",
        )

    review_decision = str(payload.get("reviewDecision") or "").upper()
    if review_decision in {"CHANGES_REQUESTED", "REVIEW_REQUIRED"}:
        add_pr_status_finding(
            findings,
            "reviewDecision",
            f"Review decision blocks merge: {review_decision}.",
            "Resolve requested changes or required review before merge eligibility.",
        )

    check_status_rollup(payload.get("statusCheckRollup"), findings)

    body = payload.get("body")
    if body is None:
        body = ""
    body_text = str(body)
    with tempfile.TemporaryDirectory() as tmpdir:
        body_path = Path(tmpdir) / "pull_request_body.md"
        body_path.write_text(body_text, encoding="utf-8")
        policy_gate = run_policy_gate_capture(body_path)
        if policy_gate.returncode != 0:
            add_pr_status_finding(
                findings,
                "body",
                "PR body policy gate failed.",
                "Fix Current Status Impact, Merge Decision, source-of-truth, or PR structure fields.",
            )

    check_closing_issue_reference(payload, body_text, findings)
    check_pr_issue_allowed_paths(payload, body_text, findings)

    if "files" not in payload:
        add_pr_status_finding(
            findings,
            "files",
            "PR file list is missing.",
            "Fetch PR metadata with gh pr view --json files or provide a fixture with files.",
        )
    else:
        hygiene = run_hygiene_capture(pr_file_paths(payload.get("files")))
        if hygiene.returncode != 0:
            add_pr_status_finding(
                findings,
                "files",
                "Changed-path hygiene failed.",
                "Remove protected/runtime/private-source-like paths or keep the PR human-gated.",
            )

    return ("fail" if findings else "pass", findings)


def print_pr_status_result(payload: dict[str, object], result: str, findings: list[dict[str, str]], *, as_json: bool) -> int:
    output = {
        "result": result,
        "low_risk_inferred": False,
        "pr": payload.get("number"),
        "url": payload.get("url"),
        "findings": findings,
    }
    if as_json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif findings:
        for finding in findings:
            print(
                f"{finding['severity']}: {finding['field']} - "
                f"{finding['reason']} Fix: {finding['recommended_fix']}"
            )
        print("PR status check result: fail. No low-risk status was inferred.")
    else:
        print("PR status check passed. No low-risk status was inferred.")
    return 1 if findings else 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    commands = [
        ["python3", "scripts/check_project.py"],
        ["python3", "scripts/validate_bootstrap.py"],
        ["git", "diff", "--check"],
        ["python3", "scripts/asgk.py", "status-check"],
    ]
    baseline = run_many(commands)
    changed_paths = run_changed_path_hygiene_checks()
    textual = run_textual_negative_checks()
    return 1 if baseline or changed_paths or textual else 0


def cmd_validate(_args: argparse.Namespace) -> int:
    return run_many([["python3", "scripts/validate_bootstrap.py"]])


def cmd_hygiene(args: argparse.Namespace) -> int:
    command = ["python3", "scripts/governance_hygiene.py"]
    if args.paths_file:
        command.extend(["--paths-file", args.paths_file])
    if args.git_base or args.git_head:
        if args.git_base:
            command.extend(["--git-base", args.git_base])
        if args.git_head:
            command.extend(["--git-head", args.git_head])
    if args.expect_blocked:
        command.append("--expect-blocked")
    return run_many([command])


def cmd_negative(args: argparse.Namespace) -> int:
    return run_negative_case(args.case)


def cmd_policy_gate(args: argparse.Namespace) -> int:
    if bool(args.pr_body) == bool(args.github_event):
        return print_failures(["provide exactly one of --pr-body or --github-event"])

    if args.pr_body:
        return run_policy_gate(rel(args.pr_body), as_json=args.json)

    event = json.loads(rel(args.github_event).read_text(encoding="utf-8"))
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        payload = {
            "result": "skipped",
            "reason": "GitHub event payload does not contain a pull_request object.",
            "low_risk_inferred": False,
        }
        if args.json:
            print(json.dumps(payload, indent=2, sort_keys=True))
        else:
            print("Policy gate skipped: GitHub event payload has no pull_request object.")
        return 0

    body = pull_request.get("body")
    if body is None:
        body = ""

    with tempfile.TemporaryDirectory() as tmpdir:
        body_path = Path(tmpdir) / "pull_request_body.md"
        body_path.write_text(str(body), encoding="utf-8")
        return run_policy_gate(body_path, as_json=args.json)


def cmd_check_pr(args: argparse.Namespace) -> int:
    if bool(args.pr) == bool(args.json_file):
        return print_failures(["provide exactly one of --pr or --json-file"])

    if args.json_file:
        payload = json.loads(rel(args.json_file).read_text(encoding="utf-8"))
    else:
        command = [
            "gh", "pr", "view", str(args.pr),
            "--json",
            "number,title,state,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,body,files,url,closingIssuesReferences",
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout.strip() or "FAIL: gh pr view failed.")
            return result.returncode
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            payload["_asgk_live_lookup"] = True

    if not isinstance(payload, dict):
        return print_failures(["PR status payload must be a JSON object"])

    result, findings = check_pr_status_payload(payload)
    return print_pr_status_result(payload, result, findings, as_json=args.json)


def load_pr_payload(args: argparse.Namespace) -> dict[str, object]:
    if bool(args.pr) == bool(args.json_file):
        raise ValueError("provide exactly one of --pr or --json-file")
    if args.json_file:
        payload = json.loads(read_text(args.json_file))
    else:
        command = [
            "gh", "pr", "view", str(args.pr),
            "--json",
            "number,title,state,isDraft,mergeStateStatus,reviewDecision,statusCheckRollup,body,files,url,closingIssuesReferences",
        ]
        result = subprocess.run(
            command,
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if result.returncode != 0:
            raise RuntimeError(result.stdout.strip() or "gh pr view failed")
        payload = json.loads(result.stdout)
        if isinstance(payload, dict):
            payload["_asgk_live_lookup"] = True
    if not isinstance(payload, dict):
        raise ValueError("PR payload must be a JSON object")
    return payload


def cmd_compact_pr_report(args: argparse.Namespace) -> int:
    try:
        payload = load_pr_payload(args)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return print_failures([str(exc)])

    result, output = compact_pr_report_from_payload(payload)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print(f"Compact PR report passed for PR #{output.get('pr', {}).get('number')}.")
    elif result == "requires_human":
        boundaries = ", ".join(output.get("restricted_boundaries", []))
        print(f"Compact PR report requires human review for restricted boundary: {boundaries}")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact PR report failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_work_unit_check(args: argparse.Namespace) -> int:
    using_paths_file = bool(args.paths_file)
    using_git_range = bool(args.git_base or args.git_head)
    if using_paths_file == using_git_range:
        return print_failures(["provide exactly one of --paths-file or --git-base/--git-head"])
    if using_git_range and not (args.git_base and args.git_head):
        return print_failures(["--git-base and --git-head must be provided together"])

    try:
        payload = load_work_unit_payload(args)
        changed_paths = (
            read_changed_path_list(args.paths_file)
            if args.paths_file
            else load_git_changed_paths(args.git_base, args.git_head)
        )
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return print_failures([str(exc)])

    result, findings, allowed_paths = check_work_unit_payload(payload, changed_paths)
    return print_work_unit_result(
        payload,
        result,
        findings,
        allowed_paths,
        changed_paths,
        as_json=args.json,
    )


def cmd_compact_issue_scope(args: argparse.Namespace) -> int:
    sources = [bool(args.issue), bool(args.json_file)]
    if sum(sources) != 1:
        return print_failures(["provide exactly one of --issue or --json-file"])
    try:
        payload = (
            load_live_work_unit("issue", str(args.issue).lstrip("#"))
            if args.issue
            else json.loads(read_text(args.json_file))
        )
    except (RuntimeError, json.JSONDecodeError) as exc:
        return print_failures([str(exc)])
    if not isinstance(payload, dict):
        return print_failures(["compact issue-scope payload must be a JSON object"])

    result, output = canonical_issue_scope_from_payload(payload)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print(f"Canonical issue scope passed for issue #{output.get('issue')}.")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Canonical issue scope failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_compact_scope_lock(args: argparse.Namespace) -> int:
    sources = [bool(args.issue), bool(args.json_file)]
    if sum(sources) != 1:
        return print_failures(["provide exactly one of --issue or --json-file"])
    try:
        payload = (
            load_live_work_unit("issue", str(args.issue).lstrip("#"))
            if args.issue
            else json.loads(read_text(args.json_file))
        )
    except (RuntimeError, json.JSONDecodeError) as exc:
        return print_failures([str(exc)])
    if not isinstance(payload, dict):
        return print_failures(["compact scope-lock payload must be a JSON object"])

    result, output = compact_scope_lock_from_payload(payload)
    if result == "pass" and args.compare_file:
        try:
            captured = json.loads(read_text(args.compare_file))
        except json.JSONDecodeError as exc:
            return print_failures([str(exc)])
        if not isinstance(captured, dict):
            return print_failures(["captured scope-lock payload must be a JSON object"])
        compare_findings = compare_scope_lock(output, captured)
        if compare_findings:
            output["result"] = "fail"
            output["findings"] = compare_findings
            result = "fail"

    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print(f"Compact scope lock passed for issue #{output.get('issue')}: {output.get('scope_hash')}")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact scope lock failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_status_check(args: argparse.Namespace) -> int:
    status_path = rel(args.file)
    failures: list[str] = []
    if not status_path.exists():
        return print_failures([f"missing current status file: {args.file}"])

    text = status_path.read_text(encoding="utf-8")
    headings = markdown_headings(text)

    for heading in STATUS_REQUIRED_HEADINGS:
        if heading not in headings:
            failures.append(f"missing current status heading: ## {heading}")

    line_count = len(text.splitlines())
    if line_count > args.max_lines:
        failures.append(f"current status is too long: {line_count} lines > {args.max_lines}")

    if "python3 scripts/asgk.py doctor" not in text:
        failures.append("current status does not name python3 scripts/asgk.py doctor")

    if re.search(r"issue:\s*['\"]?#23\b", text):
        failures.append("current status appears to retain stale issue #23 active state")

    for heading in STATUS_FORBIDDEN_HISTORY_HEADINGS:
        if heading in headings:
            failures.append(f"forbidden history-log heading in current status: ## {heading}")

    lower_text = text.lower()
    for phrase in STATUS_FORBIDDEN_PHRASES:
        if phrase.lower() in lower_text:
            failures.append(f"forbidden current-status phrase: {phrase}")

    next_action = markdown_section(text, "Next safe action")
    if not next_action:
        failures.append("current status next safe action is empty")

    return print_failures(failures)


def cmd_closeout_check(args: argparse.Namespace) -> int:
    status_path = rel(args.file)
    if not status_path.exists():
        return print_failures([f"missing closeout status file: {args.file}"])

    text = status_path.read_text(encoding="utf-8")
    active_work = markdown_section(text, "Active work")
    next_safe_action = markdown_section(text, "Next safe action")
    failures: list[str] = []

    for issue in args.completed_issue:
        if issue and issue in active_work:
            failures.append(f"completed issue still appears in active work: {issue}")

    for pr in args.completed_pr:
        if pr and pr in active_work:
            failures.append(f"completed PR still appears in active work: {pr}")

    for branch in args.completed_branch:
        if branch and branch in active_work:
            failures.append(f"completed branch still appears in active work: {branch}")

    if not next_safe_action:
        failures.append("next safe action is empty")
    else:
        for pattern in CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS:
            if re.search(pattern, next_safe_action, flags=re.IGNORECASE):
                failures.append(f"next safe action appears to describe pre-merge closeout work: {pattern}")

    return print_failures(failures)


def cmd_current_status_impact_check(args: argparse.Namespace) -> int:
    pr_body = read_text(args.pr_body)
    changed_paths = read_changed_paths(args.changed_paths_file)
    current_status_path = args.file.lstrip("./")
    current_status_changed = any(
        same_repo_path(path, current_status_path)
        or same_repo_path(path, CANONICAL_CURRENT_STATUS_PATH)
        for path in changed_paths
    )
    current_status_section = markdown_section(pr_body, "Current Status Impact")
    handoff_section = markdown_section(pr_body, "Handoff Report")
    failures: list[str] = []

    if not current_status_section:
        return print_failures(["missing PR Current Status Impact section"])

    status = normalized_field_value(current_status_section, "status")
    if status not in CURRENT_STATUS_IMPACT_ALLOWED_VALUES:
        failures.append("Current Status Impact status must be updated, not_applicable, or deferred")

    reason = normalized_field_value(current_status_section, "reason")
    if reason in {"", "pending", "unknown", "none", "tbd", "todo"}:
        failures.append("Current Status Impact reason is missing or non-specific")

    updated = normalized_field_value(current_status_section, "current_status_updated_in_this_pr")
    if status == "updated" and updated not in TRUE_VALUES:
        failures.append("status is updated but current_status_updated_in_this_pr is not true")

    if current_status_changed and status != "updated":
        failures.append(f"{CANONICAL_CURRENT_STATUS_PATH} changed but Current Status Impact status is not updated")

    if status == "updated" and not current_status_changed:
        failures.append(f"Current Status Impact status is updated but {CANONICAL_CURRENT_STATUS_PATH} did not change")

    post_merge_safe = normalized_field_value(current_status_section, "post_merge_safe")
    if status == "updated" and post_merge_safe not in TRUE_VALUES:
        failures.append("status is updated but post_merge_safe is not true")

    follow_up = normalized_field_value(current_status_section, "follow_up_issue")
    if status == "deferred":
        has_handoff_next_action = bool(re.search(r"next safe action", handoff_section, flags=re.IGNORECASE))
        if follow_up in EMPTY_FOLLOWUP_VALUES and not has_handoff_next_action:
            failures.append("status is deferred without follow_up_issue or Handoff Report next safe action")
        if current_status_changed:
            failures.append(f"status is deferred but {CANONICAL_CURRENT_STATUS_PATH} changed")

    if current_status_changed:
        status_result = subprocess.run(
            ["python3", "scripts/asgk.py", "status-check", "--file", args.file],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if status_result.returncode != 0:
            failures.append("status-check failed for current status file")

        status_text = read_text(args.file)
        active_work = markdown_section(status_text, "Active work")
        next_safe_action = markdown_section(status_text, "Next safe action")

        if args.this_pr and args.this_pr in active_work:
            failures.append(f"current status active work points to this PR: {args.this_pr}")

        for issue in args.closing_issue:
            if issue and issue in active_work:
                failures.append(f"current status active work points to closing issue: {issue}")

        if args.this_branch and args.this_branch in active_work:
            failures.append(f"current status active work points to this branch: {args.this_branch}")

        if not next_safe_action:
            failures.append("current status next safe action is empty")
        else:
            for pattern in CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS:
                if re.search(pattern, next_safe_action, flags=re.IGNORECASE):
                    failures.append(f"next safe action appears to describe pre-merge closeout work: {pattern}")

    return print_failures(failures)


def cmd_pr_body_check(args: argparse.Namespace) -> int:
    text = read_text(args.file)
    failures: list[str] = []
    headings = markdown_headings(text)
    for heading in PR_REQUIRED_HEADINGS:
        if heading not in headings:
            failures.append(f"missing PR heading: ## {heading}")
    if has_see_chat(text):
        failures.append("PR body contains forbidden chat-only authority phrase: see chat")
    if "Current Status Impact" not in headings:
        failures.append("missing Current Status Impact section")
    else:
        current_status_section = markdown_section(text, "Current Status Impact")
        for field in CURRENT_STATUS_IMPACT_REQUIRED_FIELDS:
            if not line_field_exists(current_status_section, field):
                failures.append(f"missing Current Status Impact field: {field}")
    if "Merge Decision" not in headings:
        failures.append("missing Merge Decision section")
    else:
        for field in MERGE_DECISION_REQUIRED_FIELDS:
            if not line_field_exists(text, field):
                failures.append(f"missing Merge Decision field: {field}")
    result = field_value(text, "result")
    if result and "|" not in result and result not in {"merge_allowed", "merge_blocked"}:
        failures.append("Merge Decision field result must be merge_allowed or merge_blocked")
    checks_passed = field_value(text, "checks_passed")
    if checks_passed and checks_passed.lower() in {"pending", "unknown", "pending github actions"}:
        failures.append("checks_passed is pending or unknown")
    return print_failures(failures)


def cmd_task_packet_check(args: argparse.Namespace) -> int:
    try:
        packet, source_text = load_task_packet_payload(args.file)
    except (json.JSONDecodeError, ValueError) as exc:
        return print_failures([f"invalid task packet format: {exc}"])
    return print_failures(task_packet_schema_failures(packet, source_text))


def load_compact_task_packet_inputs(args: argparse.Namespace) -> tuple[dict[str, object], dict[str, object], str]:
    if args.json_file:
        if args.file or args.issue or args.issue_json_file:
            raise ValueError("use either --json-file or --file with --issue/--issue-json-file")
        payload = json.loads(read_text(args.json_file))
        if not isinstance(payload, dict):
            raise ValueError("compact task-packet fixture must be a JSON object")
        issue_payload = payload.get("issue")
        packet = payload.get("task_packet")
        if not isinstance(issue_payload, dict):
            raise ValueError("compact task-packet fixture must include issue object")
        if not isinstance(packet, dict):
            raise ValueError("compact task-packet fixture must include task_packet object")
        return issue_payload, packet, json.dumps(packet, sort_keys=True)

    if not args.file:
        raise ValueError("provide --file with --issue or --issue-json-file")
    if bool(args.issue) == bool(args.issue_json_file):
        raise ValueError("provide exactly one of --issue or --issue-json-file")

    packet, source_text = load_task_packet_payload(args.file)
    if args.issue:
        issue_payload = load_live_work_unit("issue", str(args.issue).lstrip("#"))
    else:
        issue_payload = json.loads(read_text(args.issue_json_file))
    if not isinstance(issue_payload, dict):
        raise ValueError("compact task-packet issue payload must be a JSON object")
    return issue_payload, packet, source_text


def cmd_compact_task_packet_check(args: argparse.Namespace) -> int:
    try:
        issue_payload, packet, source_text = load_compact_task_packet_inputs(args)
    except (RuntimeError, ValueError, json.JSONDecodeError) as exc:
        return print_failures([str(exc)])

    result, output = compact_task_packet_compare(issue_payload, packet, source_text)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print(f"Compact task packet check passed for issue #{output.get('issue')}.")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact task packet check failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_compact_pr_body_check(args: argparse.Namespace) -> int:
    result, output = compact_pr_body_check(args.body_file, args.report_json)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print("Compact PR body check passed. No low-risk status was inferred.")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact PR body check failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_compact_handoff_check(args: argparse.Namespace) -> int:
    result, output = compact_handoff_check(
        args.file,
        args.current_status,
        completed_issues=args.completed_issue,
        completed_prs=args.completed_pr,
        completed_branches=args.completed_branch,
    )
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print("Compact handoff check passed. No low-risk status was inferred.")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact handoff check failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_compact_target_upgrade_check(args: argparse.Namespace) -> int:
    result, output = compact_target_upgrade_check(args.manifest)
    if args.json:
        print(json.dumps(output, indent=2, sort_keys=True))
    elif result == "pass":
        print("Compact target upgrade check passed. No low-risk status was inferred.")
    else:
        for finding in output.get("findings", []):
            print(f"FAIL: {finding['field']} - {finding['reason']}")
        print("Compact target upgrade check failed. No low-risk status was inferred.")
    return 0 if result == "pass" else 1


def cmd_context_budget_measure(args: argparse.Namespace) -> int:
    try:
        packet, source_text = load_task_packet_payload(args.task_packet)
    except (json.JSONDecodeError, ValueError) as exc:
        return print_failures([f"invalid task packet format: {exc}"])
    failures = task_packet_schema_failures(packet, source_text)
    if failures:
        return print_failures(failures)
    measurement = context_budget_measurement(packet)
    return print_context_budget_measurement(measurement, as_json=args.json)


def cmd_handoff_check(args: argparse.Namespace) -> int:
    text = read_text(args.file)
    failures: list[str] = []
    for field in HANDOFF_REQUIRED_FIELDS:
        if not line_field_exists(text, field):
            failures.append(f"missing handoff field: {field}")
    if has_see_chat(text):
        failures.append("handoff packet contains forbidden chat-only authority phrase: see chat")
    if args.fail_on_todo and has_unresolved_todo(text):
        failures.append("handoff packet contains unresolved TODO or AI_TODO marker")
    next_safe_action = field_value(text, "next_safe_action")
    if next_safe_action is not None and not next_safe_action:
        failures.append("next_safe_action is empty")
    validation_status_value = field_value(text, "validation_status")
    if validation_status_value and validation_status_value.lower() == "unknown":
        failures.append("validation_status must not be unknown")
    if re.search(r"^[ \t]*status[ \t]*:[ \t]*['\"]?unknown['\"]?[ \t]*$", text, flags=re.MULTILINE):
        failures.append("validation_status.status must not be unknown")
    for field in HANDOFF_REQUIRED_SCALAR_FIELDS:
        value = field_value(text, field)
        if value is not None and not value:
            failures.append(f"{field} is empty")
    for field in HANDOFF_REQUIRED_LIST_FIELDS:
        if line_field_exists(text, field) and not list_field_has_material_item(text, field):
            failures.append(f"{field} has no material list item")
    return print_failures(failures)


def cmd_handoff_template(args: argparse.Namespace) -> int:
    active_issue = args.issue or "AI_TODO: active issue, e.g. #40"
    active_pr = args.pr or "AI_TODO: active PR or none with reason"
    branch = args.branch or "AI_TODO: current branch"
    objective = args.objective or "AI_TODO: summarize objective from durable source"

    packet = f"""handoff_packet:
  active_issue: {yaml_quote(active_issue)}
  active_pr: {yaml_quote(active_pr)}
  branch: {yaml_quote(branch)}
  objective: {yaml_quote(objective)}
  current_state: "AI_TODO: summarize current state from issue, PR, and repo files."
  completed:
    - "AI_TODO: completed step or output."
  remaining:
    - "AI_TODO: remaining bounded work."
  allowed_paths:
    - "AI_TODO: copy allowed path from issue."
  modified_files:
    - "AI_TODO: list modified file or none."
  validation_status:
    status: "not_run"
    evidence: "TODO: pass/fail/blocked/not_run evidence. Do not write unknown."
  blockers: "AI_TODO: blocker list or none."
  next_safe_action: "AI_TODO: one concrete next safe action."
  must_read:
    - "AGENTS.md"
    - "docs/handoff/CURRENT_STATUS.md"
    - "docs/control/HANDOFF_PACKET.md"
    - "docs/DOCUMENT_MAP.md"
  must_not_do:
    - "AI_TODO: forbidden action for the next actor."
  decisions:
    - "AI_TODO: durable decision already made, or none."
  open_questions:
    - "AI_TODO: open question requiring human/reviewer judgment, or none."
"""
    print(packet, end="")
    return 0


def cmd_target_install_check(args: argparse.Namespace) -> int:
    root = Path(args.repo_root).resolve()
    findings = target_install_findings(root)
    return print_target_install_findings(findings, as_json=args.json, strict=args.strict)


def cmd_target_install_plan(args: argparse.Namespace) -> int:
    from target_install_plan import build_plan as build_target_install_plan
    from target_install_plan import print_plan_text as print_target_install_plan_text

    root = Path(args.repo_root).resolve()
    plan = build_target_install_plan(root)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_target_install_plan_text(plan)
    return 0


def cmd_release_state_check(args: argparse.Namespace) -> int:
    failures = check_release_state_docs(
        tag=args.tag,
        release_title=args.release_title,
        readme_path=rel(args.readme),
        roadmap_path=rel(args.roadmap),
        current_status_path=rel(args.current_status),
        release_policy_path=rel(args.release_policy),
    )
    return print_failures(failures)


def cmd_workspace_state_check(args: argparse.Namespace) -> int:
    if args.json_file:
        payload = json.loads(read_text(args.json_file))
        if not isinstance(payload, dict):
            return print_failures(["workspace-state JSON fixture must be an object"])
    else:
        payload = live_workspace_state(args.base_ref)
    findings = workspace_state_findings(payload, main_branch=args.main_branch)
    return print_workspace_state_result(
        payload,
        findings,
        as_json=args.json,
        strict=args.strict,
        expect_warnings=args.expect_warnings,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="ASGK minimal validation CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("doctor", help="Run baseline positive and negative checks.")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("validate", help="Run bootstrap governance validation.")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("hygiene", help="Run changed-path governance hygiene.")
    p.add_argument("--paths-file")
    p.add_argument("--git-base")
    p.add_argument("--git-head")
    p.add_argument("--expect-blocked", action="store_true")
    p.set_defaults(func=cmd_hygiene)

    p = sub.add_parser("negative", help="Run opt-in negative checks.")
    p.add_argument("case", nargs="?", default="changed-paths", choices=NEGATIVE_CASE_CHOICES)
    p.set_defaults(func=cmd_negative)

    p = sub.add_parser("compact-issue-scope", help="Emit a canonical compact-governance issue scope object.")
    p.add_argument("--issue", help="GitHub issue number for live gh REST lookup.")
    p.add_argument("--json-file", help="Fixture or captured issue JSON payload.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_issue_scope)

    p = sub.add_parser("compact-scope-lock", help="Emit a deterministic compact-governance scope lock from an issue.")
    p.add_argument("--issue", help="GitHub issue number for live gh REST lookup.")
    p.add_argument("--json-file", help="Fixture or captured issue JSON payload.")
    p.add_argument("--compare-file", help="Captured scope-lock JSON to compare against the current issue scope.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_scope_lock)

    p = sub.add_parser("compact-pr-report", help="Compile a tool-derived compact PR report from GitHub PR metadata.")
    p.add_argument("--pr", help="GitHub pull request number for live gh lookup.")
    p.add_argument("--json-file", help="Fixture or captured gh pr view JSON payload.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_pr_report)

    p = sub.add_parser("compact-task-packet-check", help="Check a task packet only narrows canonical issue scope.")
    p.add_argument("--file", help="Task packet YAML/JSON file.")
    p.add_argument("--issue", help="GitHub issue number for live gh REST lookup.")
    p.add_argument("--issue-json-file", help="Fixture or captured issue JSON payload.")
    p.add_argument("--json-file", help="Fixture bundle with issue and task_packet objects.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_task_packet_check)

    p = sub.add_parser("compact-pr-body-check", help="Check a compact PR body against a compiled report.")
    p.add_argument("--body-file", required=True, help="Compact PR body markdown file.")
    p.add_argument("--report-json", required=True, help="Compiled compact PR report JSON file.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_pr_body_check)

    p = sub.add_parser("compact-handoff-check", help="Check a compact handoff against current-status freshness rules.")
    p.add_argument("--file", required=True, help="Compact handoff YAML-like file.")
    p.add_argument("--current-status", default="docs/handoff/CURRENT_STATUS.md", help="Current-status file to check.")
    p.add_argument("--completed-issue", action="append", default=[], help="Completed issue ref that must not remain active.")
    p.add_argument("--completed-pr", action="append", default=[], help="Completed PR ref that must not remain active.")
    p.add_argument("--completed-branch", action="append", default=[], help="Completed branch that must not remain active.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_handoff_check)

    p = sub.add_parser("compact-target-upgrade-check", help="Check a compact-governance target-upgrade manifest.")
    p.add_argument("--manifest", required=True, help="Compact target-upgrade manifest JSON file.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_compact_target_upgrade_check)

    p = sub.add_parser("policy-gate", help="Run PR-body policy gate checks.")
    p.add_argument("--pr-body", help="Path to a PR body markdown file.")
    p.add_argument("--github-event", help="Path to a GitHub Actions event payload JSON file.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_policy_gate)

    p = sub.add_parser("check-pr", help="Check GitHub PR status and checkable merge gates.")
    p.add_argument("--pr", help="GitHub pull request number for live gh lookup.")
    p.add_argument("--json-file", help="Fixture or captured gh pr view JSON payload.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_check_pr)

    p = sub.add_parser("work-unit-check", help="Check live work-unit authority against changed paths.")
    p.add_argument("--issue", help="GitHub issue number for live gh REST lookup.")
    p.add_argument("--pr", help="GitHub pull request number for live gh REST lookup.")
    p.add_argument("--json-file", help="Fixture or captured issue/PR JSON payload.")
    p.add_argument("--paths-file", help="Newline-delimited changed-path list.")
    p.add_argument("--git-base", help="Base revision for git diff --name-only.")
    p.add_argument("--git-head", help="Head revision for git diff --name-only.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_work_unit_check)

    p = sub.add_parser("workspace-state-check", help="Report local workspace hygiene without inferring merge readiness.")
    p.add_argument("--json-file", help="Fixture or captured workspace-state JSON payload.")
    p.add_argument("--main-branch", default="main", help="Main branch name used to identify non-work branches.")
    p.add_argument("--base-ref", default="origin/main", help="Base ref used for merged-branch checks.")
    p.add_argument("--strict", action="store_true", help="Return nonzero when warnings are present.")
    p.add_argument("--expect-warnings", action="store_true", help="Return nonzero unless at least one warning is present.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_workspace_state_check)

    p = sub.add_parser("status-check", help="Check docs/handoff/CURRENT_STATUS.md for compactness and stale markers.")
    p.add_argument("--file", default="docs/handoff/CURRENT_STATUS.md")
    p.add_argument("--max-lines", type=int, default=120)
    p.set_defaults(func=cmd_status_check)

    p = sub.add_parser("closeout-check", help="Check local closeout status against CURRENT_STATUS.md.")
    p.add_argument("--file", default="docs/handoff/CURRENT_STATUS.md")
    p.add_argument("--completed-issue", action="append", default=[])
    p.add_argument("--completed-pr", action="append", default=[])
    p.add_argument("--completed-branch", action="append", default=[])
    p.set_defaults(func=cmd_closeout_check)

    p = sub.add_parser("current-status-impact-check", help="Check PR current-status impact is post-merge-safe.")
    p.add_argument("--pr-body", required=True)
    p.add_argument("--changed-paths-file", required=True)
    p.add_argument("--file", default="docs/handoff/CURRENT_STATUS.md")
    p.add_argument("--this-pr", default="")
    p.add_argument("--closing-issue", action="append", default=[])
    p.add_argument("--this-branch", default="")
    p.set_defaults(func=cmd_current_status_impact_check)

    p = sub.add_parser("pr-body-check", help="Check PR body and Merge Decision Record.")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_pr_body_check)

    p = sub.add_parser("task-packet-check", help="Check required task packet fields.")
    p.add_argument("--file", required=True)
    p.set_defaults(func=cmd_task_packet_check)

    p = sub.add_parser("context-budget-measure", help="Estimate repo-context tokens from task packet files_to_inspect_first.")
    p.add_argument("--task-packet", required=True)
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_context_budget_measure)

    p = sub.add_parser("handoff-check", help="Check generic handoff packet completeness.")
    p.add_argument("--file", required=True)
    p.add_argument("--fail-on-todo", action="store_true", help="Fail if TODO or AI_TODO markers remain.")
    p.set_defaults(func=cmd_handoff_check)

    p = sub.add_parser("handoff-template", help="Print an AI-fillable handoff packet draft.")
    p.add_argument("--issue", default=None)
    p.add_argument("--pr", default=None)
    p.add_argument("--branch", default=None)
    p.add_argument("--objective", default=None)
    p.set_defaults(func=cmd_handoff_template)

    p = sub.add_parser("target-install-check", help="Read-only target ASGK installation check.")
    p.add_argument("--repo-root", default=str(ROOT), help="Repository root to inspect. Defaults to this repository.")
    p.add_argument("--strict", action="store_true", help="Return nonzero when warnings are present.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_target_install_check)

    p = sub.add_parser("target-install-plan", help="Emit a read-only ASGK target-install plan.")
    p.add_argument("--repo-root", default=str(ROOT), help="Target repository root to inspect. Defaults to this repository.")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    p.set_defaults(func=cmd_target_install_plan)

    p = sub.add_parser("release-state-check", help="Check post-release docs are not stale candidate/pending surfaces.")
    p.add_argument("--tag", required=True, help="Released tag, for example v1.2.0.")
    p.add_argument("--release-title", required=True, help="Released GitHub release title.")
    p.add_argument("--readme", default="README.md")
    p.add_argument("--roadmap", default="docs/bootstrap/10_roadmap.md")
    p.add_argument("--current-status", default="docs/handoff/CURRENT_STATUS.md")
    p.add_argument(
        "--release-policy",
        default="docs/control/SOURCE_ONLY_RELEASE_POLICY.md",
        help="Optional source-only release policy to scan for duplicated release ledgers when present.",
    )
    p.set_defaults(func=cmd_release_state_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
