# Document Registry

Status: active target-project registry.

This is the complete document registry for Context Defogger.

```text
DOCUMENT_REGISTRY.md is repo-local.
```

## Entry And Startup Documents

| Document | Role | Canonical for | Read by default | Read when | Owned by lane |
|---|---|---|---:|---|---|
| `README.md` | summary | bilingual project positioning, public onboarding, and license summary | yes | all new sessions | skill_governance |
| `AGENTS.md` | canonical | agent operating guide and source-of-truth rule | yes | all agent sessions | repo_governance |
| `docs/handoff/CURRENT_STATUS.md` | status | compact current repo snapshot and next safe work | yes | all new sessions | repo_governance |
| current GitHub issue or PR | canonical | active task objective, allowed paths, acceptance, validation, merge state | yes | every work unit | active task lane |

## Skill Documents

| Document | Role | Canonical for | Read by default | Read when | Owned by lane |
|---|---|---|---:|---|---|
| `skills/context-defogger/SKILL.md` | canonical | Context Defogger extraction workflow and style rules | no | skill behavior, examples, output changes | skill_governance |
| `skills/context-defogger/references/extraction_schema.md` | contract | article embryo and support-note output structure | no | schema/output format changes | skill_governance |
| `skills/context-defogger/references/test_cases.md` | example | compact behavioral calibration cases | no | validation, regression, style calibration | skill_governance |
| `skills/context-defogger/agents/openai.yaml` | contract | UI metadata and default prompt | no | skill interface metadata changes | skill_governance |
| `CLAUDE.md` | summary | Claude Code project memory entrypoint | yes in Claude Code | Claude Code sessions | skill_governance |
| `.claude/commands/context-defogger.md` | template | Claude Code slash command for Context Defogger | no | Claude Code `/context-defogger` use or command changes | skill_governance |

## ASGK Governance Documents

| Document | Role | Canonical for | Read by default | Read when | Owned by lane |
|---|---|---|---:|---|---|
| `docs/DOCUMENT_MAP.md` | summary | compact context routing | no | document ownership or context expansion is unclear | repo_governance |
| `docs/control/CONTEXT_BUDGET_POLICY.md` | contract | read sets and context expansion | no | context selection or expansion changes | repo_governance |
| `docs/control/AGENT_CAPABILITY_MATRIX.md` | contract | agent capability boundaries | no | capability or delegation changes | repo_governance |
| `docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md` | contract | low-risk merge boundaries | no | merge policy changes | repo_governance |
| `docs/control/HUMAN_GATED_OPERATIONS.md` | contract | human-gated operations | no | protected or high-risk work | repo_governance |
| `docs/control/MERGE_DECISION_RECORD.md` | contract | merge-decision evidence format | no | merge decision updates | repo_governance |
| `docs/control/TASK_PACKET_FORMAT.md` | contract | task packet format | no | issue/task packet changes | repo_governance |
| `docs/control/AGENT_REPORT_FORMAT.md` | contract | agent report format | no | report template changes | repo_governance |

## Bootstrap And Status Documents

| Document | Role | Canonical for | Read by default | Read when | Owned by lane |
|---|---|---|---:|---|---|
| `docs/bootstrap/00_project_brief.md` | summary | target mission and non-goals | no | product boundary changes | skill_governance |
| `docs/bootstrap/01_physical_boundaries.md` | contract | writable/protected paths | no | path boundary changes | repo_governance |
| `docs/bootstrap/02_storage_roots.md` | contract | code/artifact/local-state roots | no | storage policy changes | repo_governance |
| `docs/bootstrap/03_tech_stack.md` | summary | runtime/tooling/dependency policy | no | toolchain changes | skill_governance |

## Scripts And Templates

| Document | Role | Canonical for | Read by default | Read when | Owned by lane |
|---|---|---|---:|---|---|
| `scripts/asgk.py` | script | ASGK validation wrapper | no | local validation and CI debugging | repo_governance |
| `scripts/asgk_lib/` | script | ASGK validation implementation modules | no | validator behavior changes | repo_governance |
| `.github/ISSUE_TEMPLATE/agent_task.yml` | template | bounded GitHub issue capture | no | issue template changes | repo_governance |
| `.github/PULL_REQUEST_TEMPLATE.md` | template | PR evidence and merge-decision format | no | PR template changes | repo_governance |
| `templates/task_packet.template.yaml` | template | repo-local task packet starter | no | task packet changes | repo_governance |

## Registry Rules

1. Do not add source-only ASGK history files as target authority.
2. Keep skill behavior canonical in `skills/context-defogger/SKILL.md`.
3. Keep this registry synchronized when adding public docs, scripts, schemas, or templates.
