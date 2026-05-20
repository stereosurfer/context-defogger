# Context Defogger For Claude Code

This repository publishes the Context Defogger skill.

Canonical behavior lives in:

```text
skills/context-defogger/SKILL.md
```

When asked to use Context Defogger, follow that skill and its reference files:

- `skills/context-defogger/references/extraction_schema.md`
- `skills/context-defogger/references/test_cases.md`

The skill turns provided AI-user conversation logs into public thinking-context
article embryos. It is not a transcript exporter, project handoff writer, or
publishing pipeline.

For a reusable project command, use:

```text
/context-defogger
```

Do not duplicate or override the canonical skill rules here. Update this file
only when the Claude Code entrypoint itself changes.
