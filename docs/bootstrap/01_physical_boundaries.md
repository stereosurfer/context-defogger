# Physical Boundaries

Status: active target boundary.

## Writable Paths For Normal Work

```yaml
writable_paths:
  - skills/context-defogger/**
  - README.md
  - docs/**
  - templates/**
  - scripts/**
  - .github/**
```

## Protected Or Human-Gated Paths

```yaml
human_gated_paths:
  - AGENTS.md
  - LICENSE
  - NOTICE
  - .github/**
  - docs/control/**
  - scripts/asgk.py
  - scripts/asgk_lib/**
```

Changes to protected paths require a GitHub issue or PR that explicitly names
the path and the reason.

## Forbidden By Default

```yaml
forbidden_by_default:
  - private conversation exports
  - local Codex session JSONL files
  - generated test-runs or exports
  - credentials or tokens
  - destructive git operations
```
