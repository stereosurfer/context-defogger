# Tech Stack

Status: active target tech summary.

```yaml
primary_artifact: "Codex skill"
formats:
  - Markdown
  - YAML
runtime_required_for_skill: "none"
agent_entrypoints:
  codex: "skills/context-defogger/SKILL.md"
  claude_code_project_memory: "CLAUDE.md"
  claude_code_project_command: ".claude/commands/context-defogger.md"
validation:
  - "python3 scripts/asgk.py target-install-check --repo-root ."
  - "python3 scripts/asgk.py doctor (source-repo validator; may report target-repo non-applicable source fixture gaps)"
  - "python3 <skill-creator>/scripts/quick_validate.py skills/context-defogger"
dependency_policy: "avoid runtime dependencies unless a later issue explicitly requires tooling"
```

The initial public version is source-only. Publishing, rendering, and package
distribution are future work.
