# Context Budget Policy

Status: active control policy.

This policy defines the repository context an AI agent should read for one work
unit. It exists to reduce token use, prevent context overload, and keep agents
from merging similar-but-distinct governance rules into inaccurate summaries.

## Authority Boundary

```yaml
preferred_term: context_read_set
controls:
  - repository files and durable pseudo-references an agent reads for a work unit
  - when context expansion is allowed
  - how context use is reported in PRs or agent reports
does_not_control:
  - runtime profile
  - behavior profile
  - vendor adapter
  - platform-native subagent policy
  - goal workflow
  - allowed paths
  - merge authority
  - source-of-truth order
  - human gates
```

All repository work still uses the generic repo-agent governance core in
`AGENTS.md`. A context read set only decides which additional documents may be
read for a bounded work unit.

## Core Rules

```yaml
core_rules:
  - use_the_smallest_sufficient_context_set
  - do_not_read_the_whole_repository_by_default
  - choose_one_primary_context_read_set_before_editing
  - record_context_expansion_when_extra_files_are_read
  - treat_files_to_inspect_first_as_the_task_level_file_gate
  - keep_context_budget_notes_in_existing_PR_or_agent_report_surfaces
  - do_not_create_a_separate_context_pack_or_sidecar_context_artifact
```

Large context can make an agent spend tokens on irrelevant material, blur
summary and canonical documents, miss the active issue or PR, and flatten
distinct safety rules into one over-broad rule.

## Default Startup Context

Every new agent session starts with the smallest repo entry set:

```yaml
default_startup_context:
  always_read:
    - AGENTS.md
    - README.md
    - docs/handoff/CURRENT_STATUS.md
    - current GitHub issue or PR
  do_not_read_by_default:
    - all docs/bootstrap/*
    - all docs/control/*
    - all docs/architecture/*
    - all schemas/*
    - all contracts/*
    - all examples/*
    - docs/DOCUMENT_REGISTRY.md
    - docs/INSTALL_SURFACE.md
    - profiles/*
    - docs/adapters/*
```

Additional files are added only because the current issue, PR, handoff packet,
validation failure, `docs/DOCUMENT_MAP.md`, or an explicit human request points
to them.

## Selecting A Read Set

Before changing files, classify the work unit into one primary read set. If more
than one read set appears relevant, choose the narrowest one that covers the
risk and record any expansion reason.

```yaml
context_read_set_selection:
  required_inputs:
    - current_issue_or_pr
    - task_type
    - allowed_paths
    - expected_output
    - risk_level
  output:
    - selected_context_read_set
    - files_to_read
    - context_expansion_reason_when_applicable
  stop_if:
    - context_read_set_missing
    - issue_template_option_disagrees_with_this_policy
    - selected_read_set_would_hide_a_human_gate
    - selected_read_set_requires_files_outside_allowed_scope
```

These read sets are the canonical task-type guide. Do not add a second task-type
table that repeats them in different words.

## Read Sets

```yaml
read_sets:
  startup:
    use_when: "Orienting a new session without making changes."
    read:
      - AGENTS.md
      - README.md
      - docs/handoff/CURRENT_STATUS.md
      - open PRs or current issue when relevant
    max_initial_documents: 4
    expand_when:
      - current status points to a specific control document
      - active issue names a specific file

  handoff_recovery:
    use_when: "Resuming work after interruption, tool switch, model switch, or handoff."
    read:
      - AGENTS.md
      - docs/handoff/CURRENT_STATUS.md
      - active GitHub issue
      - active PR if one exists
      - docs/control/HANDOFF_PACKET.md
      - docs/DOCUMENT_MAP.md
    also_read_from_packet:
      - must_read
      - modified_files
      - allowed_paths
    expand_when:
      - handoff_packet.must_read names additional files
      - active PR changed files are outside the handoff packet modified_files list
      - validation_status is fail blocked or not_run
      - active issue and handoff packet disagree
      - next_safe_action references a specific canonical document
    stop_if:
      - active_issue_missing
      - active_issue_says_see_chat
      - next_safe_action_empty
      - validation_status_unknown
      - allowed_paths_missing
      - must_read_missing
      - handoff_packet_conflicts_with_active_pr
      - human_gate_detected_without_approval

  docs_only:
    use_when: "Bounded documentation changes that do not alter policy semantics, validators, schemas, dependencies, or workflows."
    read:
      - AGENTS.md
      - docs/handoff/CURRENT_STATUS.md
      - current GitHub issue or PR
      - target file
      - .github/PULL_REQUEST_TEMPLATE.md
    optional_read:
      - docs/DOCUMENT_MAP.md
    stop_if:
      - required_change_outside_allowed_paths
      - policy_semantics_change_detected
      - validation_script_change_required

  control_policy:
    use_when: "Governance or control documents such as work-unit state, low-risk merge, human gates, issue hygiene, context budget, or handoff packets."
    read:
      - AGENTS.md
      - docs/handoff/CURRENT_STATUS.md
      - docs/DOCUMENT_MAP.md
      - current GitHub issue or PR
      - target control document
      - related canonical control document named by DOCUMENT_MAP.md or DOCUMENT_REGISTRY.md
    expand_when:
      - canonical owner is unclear
      - target document references another control document
      - change affects merge, human gates, handoff, or stop conditions
    stop_if:
      - policy_conflict_detected
      - human_gated_operation_would_be_expanded
      - validation_behavior_change_required_but_not_scoped

  decision_point:
    use_when: "Authority, risk, scope, installation, release, external capability, or rollback expectations reach a major decision point."
    read:
      - AGENTS.md
      - docs/handoff/CURRENT_STATUS.md
      - current GitHub issue or PR
      - docs/control/DECISION_POINT_REGISTRY.md
      - templates/decision_packet.template.yaml when creating a packet
    optional_read:
      - docs/DOCUMENT_MAP.md
      - docs/DOCUMENT_REGISTRY.md
      - canonical documents named by DECISION_POINT_REGISTRY.md for the selected decision_type
    stop_if:
      - decision_type_unclear
      - durable_source_of_truth_missing
      - required_evidence_missing
      - human_gate_required_but_missing
      - rollback_plan_required_but_missing
      - authority_conflict_unresolved

  schema_or_contract:
    use_when: "Schema, contract, fixture, or validation-structure work."
    read:
      - AGENTS.md
      - docs/bootstrap/07_contract_first.md
      - current GitHub issue or PR
      - relevant contract
      - relevant schema
      - relevant examples or fixtures
      - docs/control/TASK_PACKET_FORMAT.md when task packets are involved
    stop_if:
      - schema_breaking_change_required
      - new_validator_dependency_required
      - contract_semantics_unclear

  security_or_storage:
    use_when: "Filesystem, protected-path, Artifact Root, Local State Root, cache, private material, or externalized responsibility boundaries."
    read:
      - AGENTS.md
      - docs/bootstrap/01_physical_boundaries.md
      - docs/architecture/STORAGE_PROFILE.md
      - docs/architecture/RUNTIME_ARTIFACT_POLICY.md
      - docs/control/HUMAN_GATED_OPERATIONS.md
      - current GitHub issue or PR
    optional_read:
      - docs/architecture/CACHE_AND_STATE_POLICY.md
      - docs/architecture/WORKSPACE_LOCK_POLICY.md
      - docs/architecture/EXTERNALIZED_RESPONSIBILITY_BOUNDARY.md
    stop_if:
      - broader_filesystem_permission_required
      - protected_path_change_required
      - cloud_or_external_api_gate_required
      - private_source_material_required

  merge_decision:
    use_when: "Marking a PR ready, checking low-risk merge, or merging."
    read:
      - current PR body
      - changed file list
      - current GitHub issue
      - docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md
      - docs/control/HUMAN_GATED_OPERATIONS.md
      - docs/control/MERGE_DECISION_RECORD.md
    optional_read:
      - docs/DOCUMENT_MAP.md
      - target files changed by the PR
    stop_if:
      - required_checks_missing_or_unknown
      - merge_decision_record_missing
      - human_gate_detected
      - changed_files_outside_allowed_paths
      - unresolved_review_comments

  parallel_issue_or_pr:
    use_when: "Coordinating multiple already-scoped GitHub issues or PRs with declared dependency or overlap."
    read:
      - AGENTS.md
      - current GitHub issue or PR
      - related issue or PR metadata when there is a declared dependency
    optional_read:
      - docs/control/FAILURE_THRESHOLDS.md
      - docs/control/WORK_UNIT_STATE_MODEL.md
      - changed file list for related open PRs
    stop_if:
      - issue_or_pr_dependency_unclear
      - allowed_path_overlap_without_authorization
      - failure_threshold_reached
      - current_work_unit_unclear

  promotion_or_output_readiness:
    use_when: "Artifact promotion, source/input class boundaries, downstream output, external calls, import/export, provider/model calls, or publication readiness."
    read:
      - AGENTS.md
      - docs/bootstrap/13_artifact_promotion_policy.md
      - docs/bootstrap/15_source_or_input_class_matrix.md
      - docs/bootstrap/16_downstream_promotion_matrix.md
      - docs/bootstrap/17_readiness_audit_policy.md
      - current GitHub issue or PR
    optional_read:
      - contracts/promotion_gate.contract.yaml
      - schemas/promotion_gate.schema.json
      - schemas/execution_lane.schema.json
    stop_if:
      - output_uses_unpromoted_artifact
      - deterministic_fallback_presented_as_production_success
      - live_external_call_without_explicit_gate
      - publication_or_release_gate_required

  tooling_or_validation:
    use_when: "Validation scripts, path hygiene, CI workflow, future CLI wrapper, or script behavior."
    read:
      - AGENTS.md
      - docs/control/VALIDATION_STRATEGY.md if it exists
      - current GitHub issue or PR
      - target script or workflow file
      - relevant examples or negative fixtures named by the issue
    optional_read:
      - docs/DOCUMENT_MAP.md
      - scripts/check_project.py
      - scripts/validate_bootstrap.py
      - scripts/governance_hygiene.py
    stop_if:
      - new_dependency_required
      - CI_permissions_expand
      - validator_scope_changes_without_issue_authorization
```

Selecting a read set is a context classification only. It never makes a
protected path safe to edit, never approves merge, and never replaces the
current issue or PR allowed paths.

## Context Expansion

```yaml
context_expansion_allowed_when:
  - target file references another canonical file
  - DOCUMENT_MAP.md routes to a relevant canonical source
  - DOCUMENT_REGISTRY.md says the related file is canonical for the current topic
  - DECISION_POINT_REGISTRY.md names canonical documents for the selected decision_type
  - validation failure points to a specific file
  - PR diff touches a file outside the expected group
  - issue acceptance criteria name an additional file
  - handoff packet must_read names an additional file
  - conflict exists between current issue PR body handoff packet and repository file
  - human or reviewer explicitly asks for a broader audit

context_expansion_record:
  original_read_set:
  added_files:
  reason:
  result:

hard_limits:
  max_unrelated_files: 0
  max_documents_without_reason: 0
  max_initial_documents_without_read_set: 4
  max_full_repository_scans: 0
```

Use targeted search, file lists, handoff packet fields, or scripts instead of
full repository scans.

## What Not To Load

Do not load these unless they are the direct target of the issue or a recorded
context-expansion reason applies:

```yaml
do_not_load_by_default:
  - every schema file
  - every contract file
  - every bootstrap document
  - every control document
  - every example
  - generated artifacts
  - runtime outputs
  - private source files
  - cache directories
  - local state directories
  - runtime-specific adapters before v2.0
  - docs/DOCUMENT_REGISTRY.md
  - docs/INSTALL_SURFACE.md
```

## Report Section

Every non-trivial PR or Agent Report should include this compact section in the
existing PR or report surface:

```md
## Context Budget

Context read set: <read-set-name>
Initial files read:
- <path>
Expanded files read:
- <path or none>
Expansion reason:
- <reason or none>
Estimated repo-context tokens: <integer or not_measured>
Measurement source: <command, fixture, or not_measured>
Actual model tokens: <integer or unavailable>
Actual model token source: <client_usage_log, provider_usage, or not_provided>
Files intentionally not read:
- <category or path>
```

Estimated repo-context tokens are a local, dependency-free approximation of repo
file text named by the work unit. They are not provider billing tokens and do not
include GitHub issue text, system/developer prompts, chat history, tool output,
retrieved web/app content, or model completion tokens. Record actual model token
usage only when a client or provider usage log is explicitly available.

For handoff recovery, include the handoff packet source and the next safe
action.

## Token-Saving Rules

1. Prefer task packets, issue bodies, handoff packets, and current-status
   documents over full conversation history.
2. Prefer canonical documents over summaries.
3. Prefer changed-file lists and validator output over reading unrelated docs.
4. Prefer scripts for mechanical checks.
5. Do not ask the AI to remember policy when a validator or template can enforce
   it.
6. When a policy is stable, move it from prompt text into a document, schema, or
   script.

## Relationship To Document Navigation

`docs/DOCUMENT_MAP.md` routes document-navigation decisions.
`docs/DOCUMENT_REGISTRY.md` defines full canonical ownership rows.
This policy defines how to consume those surfaces under a context budget.

If the document map, document registry, and this policy disagree:

1. Stop the task.
2. Open or update a docs/control issue.
3. Do not silently choose the larger context set.

## Maintenance Rules

```yaml
maintenance_rules:
  - add_or_rename_context_read_sets_only_in_this_file
  - update_the_GitHub_issue_template_when_a_read_set_name_changes
  - update_DOCUMENT_MAP_or_DOCUMENT_REGISTRY_only_when_navigation_wording_becomes_stale
  - do_not_duplicate_the_read_sets_as_a_second_task_type_guide
  - do_not_use_future_CLI_wrapper_plans_to_expand_current_startup_context
```

Runtime-specific profiles and adapters remain v2.0 planned/optional work and
must not be added to the v1.x default startup context.
