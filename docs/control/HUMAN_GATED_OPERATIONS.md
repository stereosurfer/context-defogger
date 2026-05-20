# Human-Gated Operations

Human approval is required before:

- destructive git actions;
- force push;
- deleting branches;
- security boundary changes;
- storage boundary changes;
- schema major version changes;
- database migrations;
- new dependency;
- new parser/model dependency;
- new cloud egress;
- Google Drive API integration;
- MCP tool or MCP write capability;
- externalized responsibility moved into repo;
- raw source retention;
- publication/export/release decision;
- milestone closure;
- high-risk merge.

## Required human-gate record

```yaml
human_gate:
  operation:
  reason:
  risks:
  rollback_plan:
  approval_source:
  approved_by:
  approved_at:
```
