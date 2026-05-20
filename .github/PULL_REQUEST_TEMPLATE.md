## Summary

## Task Reference

## Context Read Set

```yaml
context_read_set:
  selected:
  files_read:
    - path or durable pseudo-reference
  expansion_reason: none | reason
  limits: "Context read set records bounded repository context only. It is not a runtime profile, behavior profile, or proof that external documentation was current."
```

## Changed Files

## Validation

For each validation claim, state both the result and the evidence source. Do
not write only `passed` when the check was not freshly rerun in this work unit.
Structured fields do not replace free-text judgment. Each validation entry
should name both concrete evidence and limits; a merge decision is incomplete if
the evidence, limits, or reason only restate enum values such as `passed`,
`none`, `n/a`, `all good`, or `merge_allowed`.

```yaml
validation_evidence:
  local_commands:
    - command:
      status: passed | failed | not_run | not_applicable
      source: freshly_rerun | recorded_in_pr_body | existing_durable_record | not_run
      evidence: command output summary, PR comment, commit, or reason not run
      limits: what this evidence does not prove
  ci_checks:
    - name:
      status: passed | failed | pending | not_applicable
      source: github_actions | external_ci | not_run
      evidence: check name, run URL, or reason not applicable
      limits: what this check does not prove
  inferred_or_prior_evidence:
    - claim:
      source: merged_pr | issue_comment | repo_file | none
      evidence:
      limits:
      current_work_unit_rerun: true | false
  project_specific_tests:
    - command:
      status: passed | failed | not_run | not_applicable
      source: freshly_rerun | github_actions | existing_durable_record | not_run
      evidence: behavior, typecheck, smoke test, or reason not run
      limits: what this does not prove about code semantics, API freshness, security, privacy, or production readiness
```

## Evidence Of Completion

## Scope Boundaries

## Current Status Impact

Default to `not_applicable` when this PR does not change active work, next safe
action, release/public/license/milestone gates, or handoff recovery state.
Update `docs/handoff/CURRENT_STATUS.md` only when leaving it unchanged would
mislead the next session. If the PR updates `CURRENT_STATUS.md`, make it
post-merge-safe; do not point active work at the PR that is about to merge.
Use `deferred` only when a bounded follow-up path is necessary.

```yaml
current_status_impact:
  status: updated | not_applicable | deferred
  reason:
  current_status_updated_in_this_pr: true | false
  post_merge_safe: true | false | not_applicable
  follow_up_issue: none | "#<number>"
```

Use `docs/control/CURRENT_STATUS_POLICY.md`.

## Runtime Output Status

## Merge Decision

```yaml
merge_decision:
  issue:
  lane:
  intelligence_level:
  durable_source_of_truth:
  checks_passed:
  allowed_paths_checked:
  expected_output_checked:
  contracts_checked:
  schemas_checked:
  storage_boundary:
  runtime_artifact_boundary:
  safety_review:
  human_gates_checked:
  validation_evidence_checked:
  validation_claim_source:
    local_doctor: freshly_rerun | recorded_in_pr_body | existing_durable_record | not_run | not_applicable
    ci: github_actions | external_ci | not_run | not_applicable
  result: merge_allowed | merge_blocked
  reason:
```

## Known Gaps

## Handoff Report
