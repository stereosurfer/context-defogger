# Merge Decision Record

Each merge-eligible PR must include a Merge Decision Record.

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

A missing or blocked Merge Decision Record blocks autonomous merge.
A Merge Decision Record is also incomplete when structured fields replace
judgment. The `reason` field must be free text that names the relevant evidence,
limits, and any unverified items. It must not only repeat enum values such as
`passed`, `none`, `n/a`, `all good`, or `merge_allowed`.

## Validation Evidence Source

Validation claims must say where the evidence came from. Do not collapse
different evidence sources into a generic `passed` statement.
Structured validation fields are attribution aids, not a substitute for
judgment. Reviewers should treat empty or generic evidence, limits, or reason
text as merge-blocking until clarified.

Validation claims must stay inside their evidence boundary. `doctor` and ASGK
policy checks prove governance-surface behavior, not application semantics,
security correctness, privacy safety, dependency health, or current third-party
API usage. Code-changing PRs should name the project-specific tests that cover
the changed behavior and explicitly state any coverage limits.

Use this vocabulary when practical:

```yaml
validation_evidence_source:
  freshly_rerun: "The command was run in the current work unit."
  recorded_in_pr_body: "The PR body records the result, but the current reviewer did not rerun it."
  github_actions: "The result was observed from GitHub Actions or another named CI check."
  existing_durable_record: "The result comes from a merged PR, issue comment, repo file, or other durable record."
  inferred_from_merged_pr: "The result is inferred from the fact that a merged PR recorded or required it."
  not_run: "The check was not run."
  not_applicable: "The check does not apply to this work unit."
```

If a final report says a command passed, it should distinguish:

```yaml
validation:
  local_doctor:
    status: passed | failed | not_run | not_applicable
    source: freshly_rerun | recorded_in_pr_body | existing_durable_record | not_run | not_applicable
    evidence: "Concrete command output summary, PR body reference, issue comment, or durable record."
    limits: "What this validation does not prove."
  github_actions:
    status: passed | failed | pending | not_applicable
    source: github_actions | external_ci | not_run | not_applicable
    evidence: "Named check, run URL, or reason not applicable."
    limits: "What CI does not prove."
  project_specific_tests:
    status: passed | failed | not_run | not_applicable
    source: freshly_rerun | github_actions | existing_durable_record | not_run | not_applicable
    evidence: "Named test, typecheck, smoke test, or reason not applicable."
    limits: "What changed behavior, API freshness, security, or privacy claims this does not prove."
```

Examples of invalid validation summaries:

```yaml
invalid_validation_summaries:
  - evidence: "passed"
  - limits: "none"
  - limits: "n/a"
  - reason: "all good"
  - reason: "merge_allowed"
```
