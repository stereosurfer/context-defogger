from __future__ import annotations

from dataclasses import dataclass

COMMANDS_PASS = "commands_pass"
EXPECTED_FAILURE = "expected_failure"
EXPECTED_SUCCESS = "expected_success"

ASGK = ("python3", "scripts/asgk.py")


@dataclass(frozen=True)
class NegativeCaseGroup:
    mode: str
    commands: tuple[tuple[str, ...], ...]


def _commands(prefix: tuple[str, ...], fixtures: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    return tuple((*prefix, fixture) for fixture in fixtures)


def _commands_with_suffix(
    prefix: tuple[str, ...],
    fixtures: tuple[str, ...],
    suffix: tuple[str, ...],
) -> tuple[tuple[str, ...], ...]:
    return tuple((*prefix, fixture, *suffix) for fixture in fixtures)


def _case_commands(prefix: tuple[str, ...], cases: tuple[tuple[str, ...], ...]) -> tuple[tuple[str, ...], ...]:
    return tuple((*prefix, *case) for case in cases)


TEXTUAL_EXPECTED_FAILURES = (
    (*ASGK, "pr-body-check", "--file", "examples/negative/pr_body.no-merge-decision.md"),
    (*ASGK, "pr-body-check", "--file", "examples/negative/pr_body.no-current-status-impact.md"),
    (*ASGK, "pr-body-check", "--file", "examples/negative/pr_body.see-chat.md"),
    (*ASGK, "task-packet-check", "--file", "examples/negative/task_packet.see-chat.yaml"),
    (*ASGK, "task-packet-check", "--file", "examples/negative/task_packet.no-stop.yaml"),
    (*ASGK, "task-packet-check", "--file", "examples/negative/task_packet.empty-list.yaml"),
    (*ASGK, "task-packet-check", "--file", "examples/negative/task_packet.overbroad-files-to-inspect.yaml"),
    (*ASGK, "task-packet-check", "--file", "examples/negative/task_packet.executable-no-github-issue.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.missing-active-issue.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.empty-next-safe-action.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.unknown-validation-status.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.missing-allowed-paths.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.missing-must-read.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.empty-required-lists.yaml"),
    (*ASGK, "handoff-check", "--file", "examples/negative/handoff.unresolved-todo.yaml", "--fail-on-todo"),
    (
        *ASGK, "closeout-check",
        "--file", "examples/negative/current_status.stale-closeout.md",
        "--completed-issue", "#52",
        "--completed-pr", "#53",
        "--completed-branch", "codex/positive-handoff-template-fixture",
    ),
    (
        *ASGK, "current-status-impact-check",
        "--pr-body", "examples/negative/current_status_impact/pr_body.updated-self-stale.md",
        "--changed-paths-file", "examples/negative/current_status_impact/changed_paths.current-status.txt",
        "--file", "examples/negative/current_status_impact/current_status.self-stale.md",
        "--this-pr", "#134",
        "--closing-issue", "#132",
        "--this-branch", "codex/public-readiness-audit-132",
    ),
    (
        *ASGK, "current-status-impact-check",
        "--pr-body", "examples/negative/current_status_impact/pr_body.not-applicable-status-changed.md",
        "--changed-paths-file", "examples/negative/current_status_impact/changed_paths.current-status.txt",
        "--file", "examples/negative/current_status_impact/current_status.self-stale.md",
    ),
    (
        *ASGK, "current-status-impact-check",
        "--pr-body", "examples/negative/current_status_impact/pr_body.deferred-status-changed.md",
        "--changed-paths-file", "examples/negative/current_status_impact/changed_paths.current-status.txt",
        "--file", "examples/negative/current_status_impact/current_status.self-stale.md",
    ),
    (
        *ASGK, "release-state-check",
        "--tag", "v1.2.0",
        "--release-title", "ASGK v1.2.0",
        "--readme", "examples/negative/release_state/README.stale-v1-2-candidate.md",
    ),
)

RELEASE_STATE_COMMANDS = (
    (*ASGK, "release-state-check", "--tag", "v1.2.0", "--release-title", "ASGK v1.2.0", "--readme", "examples/negative/release_state/README.stale-v1-2-candidate.md"),
    (*ASGK, "release-state-check", "--tag", "v1.6.0", "--release-title", "ASGK v1.6.0", "--release-policy", "examples/negative/release_state/SOURCE_ONLY_RELEASE_POLICY.ledger.md"),
)

WORK_UNIT_COMMANDS = (
    (*ASGK, "work-unit-check", "--json-file", "examples/negative/work_unit.merged-pr.json", "--paths-file", "examples/work_unit.changed-paths.valid.txt"),
    (*ASGK, "work-unit-check", "--json-file", "examples/work_unit.valid-issue.json", "--paths-file", "examples/negative/work_unit.changed-paths.outside-allowed.txt"),
    (*ASGK, "work-unit-check", "--json-file", "examples/negative/work_unit.missing-task-fields.json", "--paths-file", "examples/negative/work_unit.missing-task-fields.paths.txt"),
)

COMPACT_SCOPE_LOCK_CASES = (
    ("--json-file", "examples/negative/compact_governance/scope-lock.missing-allowed-paths.json"),
    ("--json-file", "examples/compact_governance/scope_lock.valid-issue.json", "--compare-file", "examples/negative/compact_governance/scope-lock.stale-capture.json"),
)

COMPACT_PR_BODY_CASES = (
    ("examples/negative/compact_governance/pr_body.compact.failed-report.md", "examples/negative/compact_governance/pr-report.metadata-unavailable.json"),
    ("examples/negative/compact_governance/pr_body.compact.requires-human-report.md", "examples/negative/compact_governance/reports/pr-report.requires-human-restricted-boundary.json"),
)

COMPACT_HANDOFF_CASES = (
    (
        "--file", "examples/negative/compact_governance/handoff.compact.hides-stale-current-status.yaml",
        "--current-status", "examples/negative/compact_governance/current_status.compact.stale-active.md",
        "--completed-issue", "#240",
        "--completed-pr", "#241",
        "--completed-branch", "codex/compact-pr-body-profile-240",
    ),
)

NEGATIVE_CASE_GROUPS = {
    "changed-paths": NegativeCaseGroup(COMMANDS_PASS, _commands_with_suffix(
        ("python3", "scripts/governance_hygiene.py", "--paths-file"),
        (
            "examples/negative/changed_paths.runtime-artifact.txt",
            "examples/negative/changed_paths.protected.txt",
            "examples/negative/changed_paths.private-binary.txt",
        ),
        ("--expect-blocked",),
    )),
    "textual": NegativeCaseGroup(EXPECTED_FAILURE, TEXTUAL_EXPECTED_FAILURES),
    "policy-gate": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        ("python3", "scripts/policy_gate_check.py", "--pr-body"),
        (
            "examples/negative/policy_gate/pr_body.missing-merge-decision.md",
            "examples/negative/policy_gate/pr_body.missing-current-status-impact.md",
            "examples/negative/policy_gate/pr_body.updated-missing-post-merge-safe.md",
            "examples/negative/policy_gate/pr_body.checks-pending.md",
            "examples/negative/policy_gate/pr_body.human-gates-pending.md",
            "examples/negative/policy_gate/pr_body.see-chat-authority.md",
        ),
    )),
    "pr-status": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "check-pr", "--json-file"),
        (
            "examples/negative/pr_status.draft-failing.json",
            "examples/negative/pr_status.missing-closing-reference.json",
            "examples/negative/pr_status.changed-path-outside-allowed.json",
        ),
    )),
    "target-install": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "target-install-check", "--repo-root"),
        (
            "examples/negative/target_install/missing_required_files",
            "examples/negative/target_install/repo_local_historical_evidence_surface",
        ),
    )),
    "release-state": NegativeCaseGroup(EXPECTED_FAILURE, RELEASE_STATE_COMMANDS),
    "work-unit": NegativeCaseGroup(EXPECTED_FAILURE, WORK_UNIT_COMMANDS),
    "workspace-state": NegativeCaseGroup(EXPECTED_SUCCESS, _commands_with_suffix(
        (*ASGK, "workspace-state-check", "--json-file"),
        ("examples/negative/workspace_state.stale-branch-untracked.json",),
        ("--expect-warnings",),
    )),
    "compact-governance": NegativeCaseGroup(COMMANDS_PASS, (("python3", "scripts/compact_governance_red_team_check.py"),)),
    "compact-issue-scope": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "compact-issue-scope", "--json-file"),
        ("examples/negative/compact_governance/issue-scope.missing-allowed-paths.json",),
    )),
    "compact-scope-lock": NegativeCaseGroup(EXPECTED_FAILURE, _case_commands((*ASGK, "compact-scope-lock"), COMPACT_SCOPE_LOCK_CASES)),
    "compact-pr-report": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "compact-pr-report", "--json-file"),
        (
            "examples/negative/compact_governance/pr-report.claim-conflicts-with-tool-state.json",
            "examples/negative/compact_governance/pr-report.metadata-unavailable.json",
            "examples/negative/compact_governance/pr-report.restricted-boundary-claimed-human-gate.json",
        ),
    )),
    "compact-task-packet": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "compact-task-packet-check", "--json-file"),
        ("examples/negative/compact_governance/task-packet-delta-expands-scope.json",),
    )),
    "compact-pr-body": NegativeCaseGroup(EXPECTED_FAILURE, tuple(
        (*ASGK, "compact-pr-body-check", "--body-file", body, "--report-json", report)
        for body, report in COMPACT_PR_BODY_CASES
    )),
    "compact-handoff": NegativeCaseGroup(EXPECTED_FAILURE, _case_commands((*ASGK, "compact-handoff-check"), COMPACT_HANDOFF_CASES)),
    "compact-target-upgrade": NegativeCaseGroup(EXPECTED_FAILURE, _commands(
        (*ASGK, "compact-target-upgrade-check", "--manifest"),
        (
            "examples/negative/compact_governance/target_upgrade/manifest.overwrites-current-status.json",
            "examples/negative/compact_governance/target_upgrade/manifest.default-enabled.json",
        ),
    )),
}

NEGATIVE_CASE_CHOICES = [*NEGATIVE_CASE_GROUPS, "all"]
