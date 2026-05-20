# Task Packet Format

Use this format for all agent-executable work.

```yaml
task_id:
lane:
intelligence_level:
intelligence_level_reason:
durable_source_of_truth:
objective:
product_context:
current_repository_context:
files_to_inspect_first:
allowed_paths:
expected_changes:
expected_output:
non_goals:
constraints:
plan:
checklist:
acceptance_sheet:
validation_commands:
stop_conditions:
rollback_expectations:
```

No field may say `see chat`.

## Issue-First Authority

When GitHub is available, an executable task packet must name a GitHub issue or
pull request in `durable_source_of_truth`.

Task packets refine executable scope. They do not replace the GitHub issue or PR
that authorizes file edits.

## Delta-Only Compact Mode

Compact governance may use a delta-only task packet only when a separate check
compares it against the source issue's canonical scope:

```bash
python3 scripts/asgk.py compact-task-packet-check --issue <number> --file <task-packet>
```

In this mode, `allowed_paths` may narrow the issue scope but must not add any
path outside the issue's `allowed_paths`. The packet remains a refinement and
routing artifact; the GitHub issue or PR remains the durable authorization.

Use this field when a task packet cannot point at a GitHub issue yet:

```yaml
github_issue_status: pending_unavailable
```

The agent must retry issue creation before PR creation or merge. Repo documents
or task packets may be primary authority only for explicitly docs-only planning
or control work whose `allowed_paths` stay inside planning/control docs, marked
with:

```yaml
work_unit_kind: docs_only_planning
```

or:

```yaml
work_unit_kind: docs_only_control
```

## Context Read Gate

`files_to_inspect_first` is the task-level context read gate. It must name the
smallest specific files or durable pseudo-reference needed before work starts.

Allowed examples:

```yaml
files_to_inspect_first:
  - AGENTS.md
  - docs/handoff/CURRENT_STATUS.md
  - current GitHub issue or PR
  - docs/control/TASK_PACKET_FORMAT.md
```

Blocked examples:

```yaml
files_to_inspect_first:
  - whole repo
  - all docs
  - docs/**
  - .
  - "*"
```

Use `context_read_set` in the GitHub issue, PR Context Budget section, or Agent
Report when the task type needs read-set reporting. Do not create a separate
context protocol or sidecar context artifact.
