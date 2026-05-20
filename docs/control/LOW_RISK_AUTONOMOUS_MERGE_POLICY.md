# Low-Risk Autonomous Merge Policy

Agents may perform low-risk merge flow only when all explicit gates pass.

## Necessary operations allowed

When required for the active work unit:

- `git fetch`, branch creation, fast-forward sync;
- staging intended files;
- committing and pushing;
- opening/updating a PR;
- editing PR body;
- posting issue/PR comments;
- checking PR status;
- rerunning checks when supported and no scope changes occur;
- closing a completed issue only when current `main` or merged PR clearly satisfies it.

## Prohibited without human approval

- `git reset --hard`;
- force push;
- deleting branches;
- reverting user work;
- broad issue/label churn unrelated to the active work unit;
- closing milestone controller issues;
- source fetching, live web search, model/API calls, raw retention, publication, cloud, MCP write capability, or externalized responsibility changes.

## Low-risk merge gates

All must pass:

1. PR belongs to current authorized work unit.
2. PR is open, non-draft, mergeable, and current with base.
3. Required GitHub checks pass.
4. Required local checks pass, or PR is docs-only and CI proves repo gate is green.
5. No unresolved P1/P2 review comments, requested changes, merge conflicts, or human hold.
6. Scope is low-risk: docs-only, governance-only, test-only, issue/status hygiene, or narrow deterministic change with tests.
7. PR does not enable restricted capabilities.
8. Runtime artifact hygiene is clean.
9. PR includes scope-boundary disclosures and Merge Decision Record.
10. Handoff/state update is included when state changes.

After merge, update the linked issue/handoff and stop.
