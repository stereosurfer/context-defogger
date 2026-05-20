from __future__ import annotations

import json
from pathlib import Path

from asgk_lib.common import normalize_repo_path, rel

COMPACT_TARGET_UPGRADE_CLASSIFICATIONS = {
    "recent_asgk",
    "older_asgk_without_skills",
    "customized_asgk",
    "partial_asgk",
}
COMPACT_TARGET_UPGRADE_NEVER_OVERWRITE_PATHS = [
    "docs/handoff/CURRENT_STATUS.md",
    "docs/DOCUMENT_MAP.md",
    "docs/DOCUMENT_REGISTRY.md",
    "docs/bootstrap/00_project_brief.md",
    "docs/bootstrap/01_physical_boundaries.md",
    "docs/bootstrap/02_storage_roots.md",
    "docs/bootstrap/03_tech_stack.md",
    "LICENSE",
]


def manifest_string_list(manifest: dict[str, object], field: str) -> list[str]:
    value = manifest.get(field)
    if not isinstance(value, list):
        return []
    return [
        normalize_repo_path(str(item))
        for item in value
        if normalize_repo_path(str(item))
    ]


def nested_string_list(manifest: dict[str, object], section: str, field: str) -> list[str]:
    value = manifest.get(section)
    if not isinstance(value, dict):
        return []
    return manifest_string_list(value, field)


def compact_target_upgrade_check(manifest_file: str | Path) -> tuple[str, dict[str, object]]:
    manifest_path = rel(manifest_file)
    findings: list[dict[str, str]] = []

    if not manifest_path.exists():
        return "fail", {
            "result": "fail",
            "low_risk_inferred": False,
            "manifest": normalize_repo_path(str(manifest_file)),
            "findings": [{
                "field": "manifest",
                "reason": f"compact target-upgrade manifest does not exist: {manifest_file}",
            }],
        }

    try:
        loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return "fail", {
            "result": "fail",
            "low_risk_inferred": False,
            "manifest": normalize_repo_path(str(manifest_file)),
            "findings": [{
                "field": "manifest",
                "reason": f"invalid JSON: {exc}",
            }],
        }

    if not isinstance(loaded, dict):
        findings.append({
            "field": "manifest",
            "reason": "compact target-upgrade manifest must be a JSON object",
        })
        manifest: dict[str, object] = {}
    else:
        manifest = loaded

    if manifest.get("version") != "asgk.compact_target_upgrade.v1":
        findings.append({
            "field": "version",
            "reason": "version must be asgk.compact_target_upgrade.v1",
        })

    for field in ["target_repository", "source_asgk_reference", "upgrade_mode", "classification"]:
        value = str(manifest.get(field) or "").strip()
        if not value:
            findings.append({
                "field": field,
                "reason": "manifest is missing required scalar field",
            })

    classification = str(manifest.get("classification") or "").strip()
    if classification and classification not in COMPACT_TARGET_UPGRADE_CLASSIFICATIONS:
        findings.append({
            "field": "classification",
            "reason": "classification must be recent_asgk, older_asgk_without_skills, customized_asgk, or partial_asgk",
        })

    if str(manifest.get("upgrade_mode") or "").strip() != "audit_and_plan":
        findings.append({
            "field": "upgrade_mode",
            "reason": "compact target upgrade check is audit_and_plan only; it is not an installer or target writer",
        })

    if manifest.get("target_repository_writes_performed") is not False:
        findings.append({
            "field": "target_repository_writes_performed",
            "reason": "manifest must confirm no target repository writes were performed by this check",
        })

    if manifest.get("durable_upgrade_issue_required") is not True:
        findings.append({
            "field": "durable_upgrade_issue_required",
            "reason": "target upgrade must require a bounded durable issue before target file changes",
        })

    compact_governance = manifest.get("compact_governance")
    if not isinstance(compact_governance, dict):
        findings.append({
            "field": "compact_governance",
            "reason": "manifest must include compact_governance object",
        })
    elif compact_governance.get("default_enabled") is not False:
        findings.append({
            "field": "compact_governance.default_enabled",
            "reason": "compact governance must not be enabled by default during target upgrade",
        })

    license_notice = manifest.get("license_notice_handling")
    if not isinstance(license_notice, dict):
        findings.append({
            "field": "license_notice_handling",
            "reason": "manifest must include license_notice_handling object",
        })
    else:
        if license_notice.get("asgk_apache_2_notice_preserved") is not True:
            findings.append({
                "field": "license_notice_handling.asgk_apache_2_notice_preserved",
                "reason": "ASGK Apache-2.0 notice preservation must be confirmed",
            })
        if license_notice.get("target_license_replaced") is not False:
            findings.append({
                "field": "license_notice_handling.target_license_replaced",
                "reason": "target repository LICENSE must not be replaced by upgrade planning",
            })
        if not str(license_notice.get("notice_surface") or "").strip():
            findings.append({
                "field": "license_notice_handling.notice_surface",
                "reason": "manifest must name the target notice/license surface",
            })

    preserved = nested_string_list(manifest, "target_owned_state", "preserved")
    overwritten = nested_string_list(manifest, "target_owned_state", "overwritten_paths")
    for path in COMPACT_TARGET_UPGRADE_NEVER_OVERWRITE_PATHS:
        if path not in preserved:
            findings.append({
                "field": "target_owned_state.preserved",
                "reason": f"target-owned path must be preserved: {path}",
            })
        if path in overwritten:
            findings.append({
                "field": "target_owned_state.overwritten_paths",
                "reason": f"target-owned path must not be overwritten: {path}",
            })

    copy_as_is = nested_string_list(manifest, "surface_plan", "copy_as_is")
    manual_merge_required = nested_string_list(manifest, "surface_plan", "manual_merge_required")
    never_overwrite = nested_string_list(manifest, "surface_plan", "never_overwrite")
    for path in COMPACT_TARGET_UPGRADE_NEVER_OVERWRITE_PATHS:
        if path in copy_as_is:
            findings.append({
                "field": "surface_plan.copy_as_is",
                "reason": f"target-owned path cannot be copied as-is: {path}",
            })
        if path not in never_overwrite and path not in manual_merge_required:
            findings.append({
                "field": "surface_plan.never_overwrite",
                "reason": f"target-owned path must be named in never_overwrite or manual_merge_required: {path}",
            })

    validation_commands = nested_string_list(manifest, "validation", "commands")
    if not validation_commands:
        findings.append({
            "field": "validation.commands",
            "reason": "manifest must include target validation commands",
        })

    human_gates = manifest_string_list(manifest, "human_gates")
    if not human_gates:
        findings.append({
            "field": "human_gates",
            "reason": "manifest must name human gates that remain outside compact artifacts",
        })

    result = "fail" if findings else "pass"
    return result, {
        "result": result,
        "low_risk_inferred": False,
        "manifest": normalize_repo_path(str(manifest_file)),
        "target_repository": manifest.get("target_repository"),
        "classification": manifest.get("classification"),
        "findings": findings,
    }
