# Document Map

Status: active target-project navigation router.

This file is the compact router for the Context Defogger repository. Keep full
registry rows in `docs/DOCUMENT_REGISTRY.md`.

## Default Startup Set

```yaml
default_startup_set:
  - AGENTS.md
  - README.md
  - docs/handoff/CURRENT_STATUS.md
  - current GitHub issue or PR
```

## Navigation

```yaml
navigation_surfaces:
  full_registry: docs/DOCUMENT_REGISTRY.md
  current_status: docs/handoff/CURRENT_STATUS.md
  context_read_sets: docs/control/CONTEXT_BUDGET_POLICY.md
  skill_entrypoint: skills/context-defogger/SKILL.md
```

## Task Routing

```yaml
task_routes:
  skill_behavior_or_output_style:
    read_first:
      - skills/context-defogger/SKILL.md
      - skills/context-defogger/references/extraction_schema.md
      - skills/context-defogger/references/test_cases.md
  repo_governance:
    read_first:
      - AGENTS.md
      - docs/control/CONTEXT_BUDGET_POLICY.md
      - current GitHub issue or PR
  status_or_handoff:
    read_first:
      - docs/handoff/CURRENT_STATUS.md
```

## Maintenance Rules

1. Keep this file short.
2. Add full document rows to `docs/DOCUMENT_REGISTRY.md`.
3. Do not copy ASGK source-repo maps or registries into this target repo.
