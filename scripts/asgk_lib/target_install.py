from __future__ import annotations

import json
from pathlib import Path

TARGET_INSTALL_LICENSE_NOTICE_PATHS = [
    "LICENSE",
    "LICENSE.md",
    "NOTICE",
    "NOTICE.md",
    "THIRD_PARTY_NOTICES.md",
    "docs/LICENSE.md",
    "docs/NOTICE.md",
]
TARGET_INSTALL_REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    "docs/DOCUMENT_MAP.md",
    "docs/DOCUMENT_REGISTRY.md",
    "docs/handoff/CURRENT_STATUS.md",
    "docs/control/CONTEXT_BUDGET_POLICY.md",
    "docs/control/AGENT_CAPABILITY_MATRIX.md",
    "docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md",
    "docs/control/HUMAN_GATED_OPERATIONS.md",
    "docs/control/MERGE_DECISION_RECORD.md",
    "docs/control/TASK_PACKET_FORMAT.md",
    "docs/control/AGENT_REPORT_FORMAT.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/agent_task.yml",
]
TARGET_INSTALL_FORBIDDEN_BLOCKING_PATHS = [
    "docs/control/HISTORICAL_ASGK_STABILIZATION_EVIDENCE.md",
    "docs/control/HISTORICAL_ASGK_READINESS_EVIDENCE.md",
    "docs/control/UNCONTROLLED_DOCUMENT_AUDIT.md",
    "docs/EVOLUTION_MODEL.md",
]
TARGET_INSTALL_FORBIDDEN_LEGACY_BLOCKING_PATHS = [
    "docs/control/V1_1_STABILIZATION_PLAN.md",
    "docs/control/V1_READINESS_AUDIT.md",
]
TARGET_INSTALL_FORBIDDEN_WARNING_PATHS = [
    "docs/handoff/AGENT_LOG.md",
    "docs/handoff/DECISIONS.md",
    "examples/negative",
    "profiles",
    "docs/adapters",
]
TARGET_INSTALL_DEFERRED_V2_SURFACES = ["profiles/", "docs/adapters/"]


def add_target_install_finding(
    findings: list[dict[str, str | bool]],
    severity: str,
    category: str,
    path: str,
    reason: str,
    recommended_fix: str,
    *,
    blocking: bool,
) -> None:
    findings.append(
        {
            "severity": severity,
            "category": category,
            "file": path,
            "reason": reason,
            "recommended_fix": recommended_fix,
            "blocking": blocking,
        }
    )


def repo_path(root: Path, path: str) -> Path:
    return root / path


def target_install_findings(root: Path) -> list[dict[str, str | bool]]:
    findings: list[dict[str, str | bool]] = []

    for required in TARGET_INSTALL_REQUIRED_FILES:
        if not repo_path(root, required).exists():
            add_target_install_finding(
                findings,
                "FAIL",
                "required_files",
                required,
                "required target-install file is missing",
                "Create the file from the ASGK install surface or explicitly document why it is not applicable.",
                blocking=True,
            )

    if not any(repo_path(root, path).exists() for path in TARGET_INSTALL_LICENSE_NOTICE_PATHS):
        add_target_install_finding(
            findings,
            "WARN",
            "license_handling",
            "LICENSE",
            "no visible license or notice handling surface found",
            "Add LICENSE/NOTICE handling or document how ASGK Apache-2.0 notices are preserved for copied or adapted ASGK-derived material.",
            blocking=False,
        )

    document_map_path = repo_path(root, "docs/DOCUMENT_MAP.md")
    if document_map_path.exists():
        text = document_map_path.read_text(encoding="utf-8")
        required_refs = ["docs/DOCUMENT_REGISTRY.md", "docs/control/CONTEXT_BUDGET_POLICY.md"]
        for ref in required_refs:
            if ref not in text:
                add_target_install_finding(
                    findings,
                    "FAIL",
                    "document_navigation_split",
                    "docs/DOCUMENT_MAP.md",
                    f"compact router does not reference {ref}",
                    f"Update docs/DOCUMENT_MAP.md to route readers to {ref}.",
                    blocking=True,
                )
        forbidden_markers = [
            "| Document | Role | Canonical for | Read by default | Read when | Owned by lane |",
            "## Task-type Reading Guide",
        ]
        for marker in forbidden_markers:
            if marker in text:
                add_target_install_finding(
                    findings,
                    "FAIL",
                    "document_navigation_split",
                    "docs/DOCUMENT_MAP.md",
                    f"document map still contains non-router marker: {marker}",
                    "Move full registry rows to docs/DOCUMENT_REGISTRY.md and task read sets to docs/control/CONTEXT_BUDGET_POLICY.md.",
                    blocking=True,
                )
        template_markers = ["target-project navigation router template", "<lane>", "<path>", "<topic>"]
        for marker in template_markers:
            if marker in text:
                add_target_install_finding(
                    findings,
                    "WARN",
                    "template_derived_files",
                    "docs/DOCUMENT_MAP.md",
                    f"document map still contains template marker: {marker}",
                    "Customize docs/DOCUMENT_MAP.md for the target repository.",
                    blocking=False,
                )

    document_registry_path = repo_path(root, "docs/DOCUMENT_REGISTRY.md")
    if document_registry_path.exists():
        text = document_registry_path.read_text(encoding="utf-8")
        for marker in ["# Document Registry", "DOCUMENT_REGISTRY.md is repo-local"]:
            if marker not in text:
                add_target_install_finding(
                    findings,
                    "FAIL",
                    "document_navigation_split",
                    "docs/DOCUMENT_REGISTRY.md",
                    f"document registry missing marker: {marker}",
                    "Create docs/DOCUMENT_REGISTRY.md from templates/DOCUMENT_REGISTRY.template.md and customize it.",
                    blocking=True,
                )
        if "| Document | Role | Canonical for | Read by default | Read when | Owned by lane |" not in text:
            add_target_install_finding(
                findings,
                "WARN",
                "document_navigation_split",
                "docs/DOCUMENT_REGISTRY.md",
                "document registry does not appear to contain registry rows",
                "Add target-repository document rows or document why the registry is intentionally minimal.",
                blocking=False,
            )
        for marker in ["target-project template", "<lane>", "<path>", "<topic>"]:
            if marker in text:
                add_target_install_finding(
                    findings,
                    "WARN",
                    "template_derived_files",
                    "docs/DOCUMENT_REGISTRY.md",
                    f"document registry still contains template marker: {marker}",
                    "Customize docs/DOCUMENT_REGISTRY.md for the target repository.",
                    blocking=False,
                )

    for forbidden in TARGET_INSTALL_FORBIDDEN_BLOCKING_PATHS:
        if repo_path(root, forbidden).exists():
            add_target_install_finding(
                findings,
                "FAIL",
                "forbidden_repo_local_surfaces",
                forbidden,
                "ASGK repo-local governance file is present in the target repository surface",
                "Remove this file from target authority or document an explicit adaptation issue.",
                blocking=True,
            )

    for forbidden in TARGET_INSTALL_FORBIDDEN_LEGACY_BLOCKING_PATHS:
        if repo_path(root, forbidden).exists():
            add_target_install_finding(
                findings,
                "FAIL",
                "forbidden_repo_local_surfaces",
                forbidden,
                "legacy ASGK repo-local governance file is present in the target repository surface",
                "Remove this legacy ASGK file from target authority or document an explicit adaptation issue.",
                blocking=True,
            )

    for forbidden in TARGET_INSTALL_FORBIDDEN_WARNING_PATHS:
        if repo_path(root, forbidden).exists():
            add_target_install_finding(
                findings,
                "WARN",
                "forbidden_repo_local_surfaces",
                forbidden,
                "ASGK repo-local or deferred surface is present",
                "Keep only if intentionally adapted; otherwise remove from the target install surface.",
                blocking=False,
            )

    for startup_path in ["AGENTS.md", "docs/DOCUMENT_MAP.md"]:
        path = repo_path(root, startup_path)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for surface in TARGET_INSTALL_DEFERRED_V2_SURFACES:
            if "default_startup_set" in text and surface in text:
                add_target_install_finding(
                    findings,
                    "FAIL",
                    "deferred_v2_guard",
                    startup_path,
                    f"default startup surface appears to reference deferred v2 path: {surface}",
                    "Remove runtime-specific profiles/adapters from the v1.x default startup path.",
                    blocking=True,
                )

    if not any(repo_path(root, candidate).exists() for candidate in ["scripts/asgk.py", ".github/workflows"]):
        add_target_install_finding(
            findings,
            "WARN",
            "validation_command_presence",
            ".",
            "no obvious validation command or workflow surface found",
            "Document the target repository validation command before relying on ASGK governance.",
            blocking=False,
        )

    return findings


def print_target_install_findings(
    findings: list[dict[str, str | bool]], *, as_json: bool, strict: bool = False
) -> int:
    blocking_count = sum(1 for finding in findings if bool(finding["blocking"]))
    warning_count = sum(1 for finding in findings if not bool(finding["blocking"]))
    result = "fail" if blocking_count or (strict and warning_count) else ("warning" if warning_count else "pass")
    if as_json:
        print(json.dumps({"result": result, "findings": findings, "strict": strict}, indent=2, sort_keys=True))
    else:
        for finding in findings:
            print(
                f"{finding['severity']}: [{finding['category']}] {finding['file']} - "
                f"{finding['reason']} Fix: {finding['recommended_fix']}"
            )
        if not findings:
            print("Target install check passed.")
        else:
            print(f"Target install check result: {result} ({blocking_count} blocking, {warning_count} warning).")
    return 1 if blocking_count or (strict and warning_count) else 0
