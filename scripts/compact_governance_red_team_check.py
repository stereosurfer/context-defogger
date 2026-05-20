#!/usr/bin/env python3
"""Run opt-in compact-governance red-team fixtures.

This checker models the proposed reference-first / delta-only migration before
ASGK changes any default PR template or operating rule. It treats fixture data as
captured GitHub/PR/tool state and verifies that compact artifacts cannot replace
tool-derived gates.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from fnmatch import fnmatchcase
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
POSITIVE_FIXTURE_DIR = ROOT / "examples" / "compact_governance"
NEGATIVE_FIXTURE_DIR = ROOT / "examples" / "negative" / "compact_governance"
RESULT_PRIORITY = {
    "pass": 0,
    "requires_human": 1,
    "blocked": 2,
    "fail": 3,
    "fail_closed": 4,
}
PASSING_CI_STATES = {"success", "passed", "not_applicable"}


@dataclass(frozen=True)
class Finding:
    category: str
    reason: str


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/").removeprefix("./")


def matches_allowed(path: str, allowed: str) -> bool:
    normalized = normalize_path(path)
    pattern = normalize_path(allowed)
    if pattern.endswith("/**"):
        prefix = pattern[:-3]
        return normalized == prefix or normalized.startswith(f"{prefix}/")
    if pattern.endswith("/"):
        prefix = pattern.rstrip("/")
        return normalized == prefix or normalized.startswith(f"{prefix}/")
    if any(char in pattern for char in "*?[]"):
        return fnmatchcase(normalized, pattern)
    return normalized == pattern or normalized.startswith(f"{pattern}/")


def outside_allowed(paths: Iterable[str], allowed_paths: Iterable[str]) -> list[str]:
    allowed = [normalize_path(path) for path in allowed_paths]
    outside: list[str] = []
    for path in paths:
        normalized = normalize_path(path)
        if not any(matches_allowed(normalized, allowed_path) for allowed_path in allowed):
            outside.append(normalized)
    return outside


def claims_merge_ready(agent_claims: dict[str, Any]) -> bool:
    return (
        str(agent_claims.get("merge_result", "")).lower() == "merge_allowed"
        or agent_claims.get("auto_merge_eligible") is True
        or agent_claims.get("checks_passed") is True
    )


def claims_human_gate(agent_claims: dict[str, Any]) -> bool:
    return agent_claims.get("human_gates_checked") is True


def result_from_findings(findings: list[Finding]) -> str:
    result = "pass"
    for finding in findings:
        if RESULT_PRIORITY[finding.category] > RESULT_PRIORITY[result]:
            result = finding.category
    return result


def evaluate_fixture(payload: dict[str, Any]) -> tuple[str, list[Finding]]:
    findings: list[Finding] = []
    issue_scope = payload.get("issue_scope") or {}
    scope_lock = payload.get("scope_lock") or {}
    pr_state = payload.get("pr") or {}
    task_packet = payload.get("task_packet") or {}
    agent_claims = payload.get("agent_claims") or {}

    if not isinstance(issue_scope, dict):
        findings.append(Finding("fail", "issue_scope must be an object"))
        issue_scope = {}
    if not isinstance(scope_lock, dict):
        findings.append(Finding("fail", "scope_lock must be an object"))
        scope_lock = {}
    if not isinstance(pr_state, dict):
        findings.append(Finding("fail", "pr must be an object"))
        pr_state = {}
    if not isinstance(task_packet, dict):
        findings.append(Finding("fail", "task_packet must be an object"))
        task_packet = {}
    if not isinstance(agent_claims, dict):
        findings.append(Finding("fail", "agent_claims must be an object"))
        agent_claims = {}

    if pr_state.get("metadata_available") is False:
        findings.append(Finding("fail_closed", "GitHub/PR metadata is unavailable"))
        return result_from_findings(findings), findings

    current_scope_hash = issue_scope.get("scope_hash")
    captured_scope_hash = scope_lock.get("scope_hash")
    if current_scope_hash and captured_scope_hash and current_scope_hash != captured_scope_hash:
        findings.append(Finding("fail", "captured scope lock does not match current issue scope"))

    issue_allowed_paths = issue_scope.get("allowed_paths") or []
    changed_paths = pr_state.get("changed_paths") or []
    if not issue_allowed_paths:
        findings.append(Finding("fail", "issue allowed_paths are missing"))
    else:
        for path in outside_allowed(changed_paths, issue_allowed_paths):
            findings.append(Finding("fail", f"changed path outside issue allowed_paths: {path}"))

    packet_allowed_paths = task_packet.get("allowed_paths") or []
    if packet_allowed_paths and issue_allowed_paths:
        for path in outside_allowed(packet_allowed_paths, issue_allowed_paths):
            findings.append(Finding("fail", f"task packet expands issue allowed_paths: {path}"))

    ci_status = str(pr_state.get("ci_status", "")).lower()
    if ci_status not in PASSING_CI_STATES:
        findings.append(Finding("blocked", f"CI status is not complete and passing: {ci_status or 'missing'}"))

    current_status_changed = bool(pr_state.get("current_status_changed"))
    current_status_impact = str(pr_state.get("current_status_impact", "")).lower()
    if current_status_changed and current_status_impact != "updated":
        findings.append(
            Finding("fail", "CURRENT_STATUS changed but Current Status Impact is not updated")
        )

    restricted_boundaries = pr_state.get("restricted_boundaries") or []
    if restricted_boundaries:
        boundaries = ", ".join(str(item) for item in restricted_boundaries)
        findings.append(Finding("requires_human", f"restricted boundary detected: {boundaries}"))

    derived_result = result_from_findings(findings)
    if derived_result != "pass" and claims_merge_ready(agent_claims):
        findings.append(
            Finding(
                "fail",
                "agent-authored merge/check claims conflict with tool-derived blocking state",
            )
        )
    if restricted_boundaries and claims_human_gate(agent_claims):
        findings.append(
            Finding(
                "fail",
                "agent-authored human-gate claim conflicts with tool-derived restricted-boundary state",
            )
        )

    return result_from_findings(findings), findings


def fixture_paths(paths: list[str]) -> list[Path]:
    if paths:
        return [Path(path) for path in paths]
    return sorted(POSITIVE_FIXTURE_DIR.glob("*.json")) + sorted(NEGATIVE_FIXTURE_DIR.glob("*.json"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fixtures", nargs="*", help="Optional fixture paths. Defaults to compact-governance fixture directories.")
    args = parser.parse_args()

    paths = fixture_paths(args.fixtures)
    if not paths:
        print("FAIL: no compact-governance red-team fixtures found")
        return 1

    failures: list[str] = []
    for path in paths:
        payload = load_json(path)
        expected = str(payload.get("expected_result", "")).lower()
        actual, findings = evaluate_fixture(payload)
        if actual != expected:
            failures.append(f"{path}: expected {expected or 'missing'}, got {actual}")
        finding_text = "; ".join(f"{finding.category}: {finding.reason}" for finding in findings) or "no findings"
        print(f"{path.relative_to(ROOT)} -> {actual} ({finding_text})")

    if failures:
        print("Compact governance red-team check failed:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print(f"Compact governance red-team check passed for {len(paths)} fixture(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
