# Context Defogger

Context Defogger is a Codex skill for turning messy AI-user conversations into clear public thinking context.

It is not a chat transcript exporter, a project handoff writer, or a static blog generator. It reads a provided conversation and extracts article embryos: the real question, user intent, AI assumptions, user corrections, turning points, and retained design decisions.

## What It Produces

- Article embryos written as prose, not checklist summaries.
- Automatic article splitting by thinking tension.
- User-intent analysis: what held, what changed, and what did not survive.
- AI-proposal calibration: what the AI proposed, what the user modified or rejected, and why.
- Support notes with trigger lines, AI assumptions, and retained design choices.

## Why This Exists

AI conversations often contain useful reasoning, but the useful part is buried inside back-and-forth correction. Context Defogger helps turn that fog into reusable public thinking notes.

Tagline:

> Clear messy AI conversations into usable thinking context.

## Skill Location

```text
skills/context-defogger/
```

Use it with:

```text
Use $context-defogger to turn this conversation into public thinking-context article embryos.
```

## Repository Governance

This repository uses ASGK-style source governance:

- `AGENTS.md` is the agent operating guide.
- `docs/handoff/CURRENT_STATUS.md` is the compact current-state surface.
- `docs/DOCUMENT_MAP.md` and `docs/DOCUMENT_REGISTRY.md` route repo context.
- GitHub issues and PRs are the durable source of truth for work units.

## Non-Goals

- No Cloudflare/static blog publishing yet.
- No HTML renderer yet.
- No transcript exporter.
- No package-manager release yet.

## License

Apache-2.0. See `LICENSE` and `NOTICE`.
