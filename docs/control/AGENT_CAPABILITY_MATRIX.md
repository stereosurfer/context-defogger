# Agent Capability Matrix

Status: active control policy.

This document classifies task risk and the minimum reasoning depth needed for
work under the generic ASGK governance flow. It does not assign agents or
authorize platform-native subagents.

## Purpose

Use this matrix to decide:

- whether the current issue or PR scope is still appropriate;
- whether a human gate applies;
- whether low-risk autonomous merge can even be considered;
- which context read set is required.

`lane` and `intelligence_level` are task metadata. They do not create a second
source of authority and do not bypass GitHub issue-first work.

## Related Sources

```yaml
context_read_sets: docs/control/CONTEXT_BUDGET_POLICY.md
low_risk_merge: docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md
human_gates: docs/control/HUMAN_GATED_OPERATIONS.md
document_ownership: docs/DOCUMENT_MAP.md
```

If these sources conflict, stop and report the conflict.

## Intelligence Levels

| Level | Intended use | Must not do |
|---|---|---|
| `fast_basic` | mechanical search, inventory, formatting checks, typo fixes | code changes, policy interpretation, security review |
| `standard` | narrow implementation, focused tests, bounded docs updates | cross-module design, dependency changes, security-boundary changes |
| `advanced` | multi-file implementation, tricky debugging, nontrivial tests, UX workflows | final policy authority, final security gate, high-risk merge authority |
| `frontier` | architecture review, security-sensitive analysis, merge-risk review, ambiguous tradeoffs | routine mechanical work when lower levels suffice |

## Capability Matrix

| Task type | Minimum level | Low-risk merge possible | Human gate required | Context read set | Notes |
|---|---:|---:|---:|---|---|
| typo / formatting in docs | `fast_basic` | yes | no | `docs_only` | Must stay inside allowed paths. |
| small docs extraction or inventory | `fast_basic` | no PR unless output committed | no | `docs_only` | Avoid policy interpretation. |
| handoff status update | `standard` | yes | no | `docs_only` | Update only named status files. |
| quickstart / onboarding docs | `standard` | yes | no | `docs_only` | No policy semantics change. |
| document map or registry update | `standard` | yes | maybe | `control_policy` | Canonical ownership changes may escalate. |
| context budget policy update | `standard` | maybe | maybe | `control_policy` | Loosening read limits requires review. |
| task packet example/template update | `standard` | yes | no | `docs_only` | Must match schema and task format. |
| issue or PR template wording update | `standard` | maybe | maybe | `tooling_or_validation` | Required-field or merge-field changes escalate. |
| report format update | `standard` | maybe | no if clarifying | `control_policy` | Removing required evidence escalates. |
| validation docs or negative-test plan | `standard` | yes if docs-only | no | `tooling_or_validation` | Executable fixtures are separate validation work. |
| validator or governance script change | `advanced` | maybe | maybe | `tooling_or_validation` | Must include test evidence. |
| GitHub Actions workflow change | `advanced` | maybe | maybe | `tooling_or_validation` | Permission or external action expansion is gated. |
| schema or contract clarification | `advanced` | maybe | no if non-semantic | `schema_or_contract` | Align examples and checks. |
| schema breaking change | `frontier` | no | yes | `schema_or_contract` | Migration and rollback required. |
| storage or runtime artifact policy change | `advanced` | maybe | maybe | `security_or_storage` | Boundary expansion is human-gated. |
| protected path, human-gate, or merge-policy change | `frontier` | no | yes | `merge_decision` | Never solo auto-merge. |
| dependency, cloud/API, MCP, or model-call enablement | `frontier` | no | yes | `promotion_or_output_readiness` | Requires explicit gate and rollback. |
| release/publication decision | `frontier` | no | yes | `promotion_or_output_readiness` | Human-gated. |

## Escalation Rules

Escalate or stop when the actual work:

- crosses unrelated top-level areas;
- changes validation behavior, merge authority, human gates, storage/security
  boundaries, schema semantics, dependencies, external actions, or runtime
  capabilities;
- needs context outside the issue or PR allowed scope;
- has ambiguous tradeoffs or missing rollback expectations.

Downscope instead when the risky portion is separable, and list deferred work in
the PR `Known Gaps`.

## Review Checklist

Before completion, verify:

1. The issue or PR authorized the actual files changed.
2. The minimum level still matches the work performed.
3. The required context read set was used or an override was recorded.
4. Human-gated operations are not being merged without approval.
5. Low-risk merge is allowed by this matrix and the merge policies.
