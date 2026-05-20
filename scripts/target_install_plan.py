#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

COPY_AS_IS = [
    "LICENSE",
    "AGENTS.md",
    "docs/control/CONTEXT_BUDGET_POLICY.md",
    "docs/control/AGENT_CAPABILITY_MATRIX.md",
    "docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md",
    "docs/control/HUMAN_GATED_OPERATIONS.md",
    "docs/control/MERGE_DECISION_RECORD.md",
    "docs/control/TASK_PACKET_FORMAT.md",
    "docs/control/AGENT_REPORT_FORMAT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/agent_task.yml",
    "scripts/asgk.py",
    "scripts/asgk_lib",
    "scripts/check_project.py",
    "scripts/validate_bootstrap.py",
    "scripts/governance_hygiene.py",
    "scripts/compact_governance_red_team_check.py",
    "scripts/policy_gate_check.py",
    "scripts/pr_governance_preflight.py",
    "scripts/target_install_plan.py",
]

TEMPLATE_THEN_CUSTOMIZE = [
    {
        "source": "templates/DOCUMENT_MAP.template.md",
        "target": "docs/DOCUMENT_MAP.md",
        "required_action": "Create a compact repo-local router; do not place full registry tables here.",
    },
    {
        "source": "templates/DOCUMENT_REGISTRY.template.md",
        "target": "docs/DOCUMENT_REGISTRY.md",
        "required_action": "Replace placeholders with target-repository document rows.",
    },
]

CUSTOMIZE_REQUIRED = [
    {
        "path": "docs/bootstrap/00_project_brief.md",
        "required_review": "Replace ASGK/placeholder mission with target project mission and non-goals.",
    },
    {
        "path": "docs/bootstrap/01_physical_boundaries.md",
        "required_review": "Set actual writable paths, protected paths, and forbidden actions.",
    },
    {
        "path": "docs/bootstrap/02_storage_roots.md",
        "required_review": "Set target project Code Repo, Artifact Root, and Local State Root model.",
    },
    {
        "path": "docs/bootstrap/03_tech_stack.md",
        "required_review": "Declare target project runtime, language, dependencies, and dependency policy.",
    },
    {
        "path": "docs/handoff/CURRENT_STATUS.md",
        "required_review": "Create a fresh target-project current snapshot; do not copy ASGK current status.",
    },
    {
        "path": "templates/task_packet.template.yaml",
        "required_review": "Ensure lanes, allowed paths, and validation commands match the target repo.",
    },
]

DO_NOT_COPY = [
    {"path": "docs/DOCUMENT_MAP.md", "reason": "ASGK repo-local router; use templates/DOCUMENT_MAP.template.md instead."},
    {"path": "docs/DOCUMENT_REGISTRY.md", "reason": "ASGK repo-local registry; use templates/DOCUMENT_REGISTRY.template.md instead."},
    {"path": "docs/handoff/AGENT_LOG.md", "reason": "ASGK repository history, not target project state."},
    {"path": "docs/handoff/DECISIONS.md", "reason": "ASGK repository history, not target project state."},
    {"path": "docs/control/HISTORICAL_ASGK_STABILIZATION_EVIDENCE.md", "reason": "Archived ASGK maturity evidence, not target project readiness."},
    {"path": "docs/control/HISTORICAL_ASGK_READINESS_EVIDENCE.md", "reason": "Archived ASGK readiness evidence, not target project readiness."},
    {"path": "legacy docs/control/V1_1_STABILIZATION_PLAN.md", "reason": "Legacy ASGK repo-local path; block if found in target authority."},
    {"path": "legacy docs/control/V1_READINESS_AUDIT.md", "reason": "Legacy ASGK repo-local path; block if found in target authority."},
    {"path": "docs/control/UNCONTROLLED_DOCUMENT_AUDIT.md", "reason": "ASGK internal audit result."},
    {"path": "docs/EVOLUTION_MODEL.md", "reason": "ASGK self-governance evolution history, not target project policy."},
    {"path": "examples/negative/*", "reason": "Expected-failure fixtures; copy only for validation work."},
    {"path": "profiles/*", "reason": "Deferred v2 runtime-specific optimization surfaces."},
    {"path": "docs/adapters/*", "reason": "Deferred v2 runtime-specific optimization surfaces."},
]

POST_INSTALL_CHECKS = [
    "python3 scripts/asgk.py target-install-check --repo-root .",
    "python3 scripts/asgk.py doctor",
    "Create first governance smoke-test issue.",
]

LICENSE_HANDLING = {
    "source_license": "LICENSE",
    "license": "Apache-2.0",
    "target_action": "Preserve ASGK Apache-2.0 notices for copied or adapted ASGK-derived material.",
    "not_implied": "Copying ASGK's LICENSE does not automatically relicense the whole target repository.",
}


def path_status(repo_root: Path, path: str) -> str:
    return "present" if (repo_root / path).exists() else "missing"


def build_plan(repo_root: Path) -> dict[str, Any]:
    copy_as_is = [
        {"source": path, "target": path, "source_status": path_status(ROOT, path), "target_status": path_status(repo_root, path)}
        for path in COPY_AS_IS
    ]
    template_then_customize = [
        {
            **entry,
            "source_status": path_status(ROOT, entry["source"]),
            "target_status": path_status(repo_root, entry["target"]),
        }
        for entry in TEMPLATE_THEN_CUSTOMIZE
    ]
    customize_required = [
        {**entry, "target_status": path_status(repo_root, entry["path"])}
        for entry in CUSTOMIZE_REQUIRED
    ]
    do_not_copy = [
        {**entry, "target_status": path_status(repo_root, entry["path"].rstrip("*")) if "*" not in entry["path"] else "pattern"}
        for entry in DO_NOT_COPY
    ]
    return {
        "schema": "asgk.target_install_plan.v0",
        "repo_root": str(repo_root),
        "mode": "read_only_plan",
        "writes_files": False,
        "copy_as_is": copy_as_is,
        "template_then_customize": template_then_customize,
        "customize_required": customize_required,
        "do_not_copy": do_not_copy,
        "license_handling": LICENSE_HANDLING,
        "post_install_checks": POST_INSTALL_CHECKS,
        "next_layer": "target-install-scaffold may be implemented later, but only from an explicit reviewed plan.",
    }


def print_plan_text(plan: dict[str, Any]) -> None:
    print("Target install plan (read-only)")
    print(f"repo_root: {plan['repo_root']}")
    print(f"writes_files: {plan['writes_files']}")
    for section in ["copy_as_is", "template_then_customize", "customize_required", "do_not_copy", "license_handling", "post_install_checks"]:
        print(f"\n## {section}")
        items = plan[section]
        if isinstance(items, list):
            for item in items:
                if isinstance(item, dict):
                    label = item.get("target") or item.get("path") or item.get("source")
                    details = "; ".join(f"{k}={v}" for k, v in item.items() if k != "target")
                    print(f"- {label}: {details}")
                else:
                    print(f"- {item}")
        elif isinstance(items, dict):
            for key, value in items.items():
                print(f"- {key}: {value}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit a read-only ASGK target-install plan.")
    parser.add_argument("--repo-root", default=str(ROOT), help="Target repository root to inspect. Defaults to this repository.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output.")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    plan = build_plan(repo_root)
    if args.json:
        print(json.dumps(plan, indent=2, sort_keys=True))
    else:
        print_plan_text(plan)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
