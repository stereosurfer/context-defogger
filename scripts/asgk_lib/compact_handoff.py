"""Compact handoff validation helpers."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from asgk_lib.common import (
    ROOT,
    field_block_text,
    field_value,
    has_see_chat,
    has_unresolved_todo,
    line_field_exists,
    list_field_has_material_item,
    markdown_section,
    normalize_repo_path,
    normalized_field_value,
    rel,
)
from asgk_lib.status_policy import (
    CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS,
    CURRENT_STATUS_IMPACT_ALLOWED_VALUES,
    CURRENT_STATUS_IMPACT_REQUIRED_FIELDS,
    EMPTY_FOLLOWUP_VALUES,
    TRUE_VALUES,
)


def compact_handoff_check(
    handoff_file: str | Path,
    current_status_file: str | Path,
    *,
    completed_issues: list[str],
    completed_prs: list[str],
    completed_branches: list[str],
) -> tuple[str, dict[str, object]]:
    handoff_path = rel(handoff_file)
    status_path = rel(current_status_file)
    findings: list[dict[str, str]] = []

    if not handoff_path.exists():
        findings.append({
            "field": "file",
            "reason": f"compact handoff file does not exist: {handoff_file}",
        })
        handoff_text = ""
    else:
        handoff_text = handoff_path.read_text(encoding="utf-8")

    if not status_path.exists():
        findings.append({
            "field": "current_status",
            "reason": f"current-status file does not exist: {current_status_file}",
        })
        status_text = ""
    else:
        status_text = status_path.read_text(encoding="utf-8")

    if handoff_text:
        if has_see_chat(handoff_text):
            findings.append({
                "field": "handoff",
                "reason": "compact handoff contains forbidden chat-only authority phrase: see chat",
            })
        if has_unresolved_todo(handoff_text):
            findings.append({
                "field": "handoff",
                "reason": "compact handoff contains unresolved TODO or AI_TODO marker",
            })

        required_scalar_fields = [
            "active_issue",
            "active_pr",
            "branch",
            "objective",
            "state",
            "next_safe_action",
            "durable_source_of_truth",
        ]
        for field in required_scalar_fields:
            value = field_value(handoff_text, field)
            if value is None:
                findings.append({
                    "field": field,
                    "reason": "compact handoff is missing required field",
                })
            elif not value:
                findings.append({
                    "field": field,
                    "reason": "compact handoff required field is empty",
                })

        if not list_field_has_material_item(handoff_text, "allowed_paths"):
            findings.append({
                "field": "allowed_paths",
                "reason": "compact handoff must include at least one material allowed path",
            })

        validation_status = field_block_text(handoff_text, "validation_status")
        if not validation_status:
            findings.append({
                "field": "validation_status",
                "reason": "compact handoff is missing validation_status block",
            })
        else:
            validation_value = normalized_field_value(validation_status, "status")
            if validation_value in {"", "unknown"}:
                findings.append({
                    "field": "validation_status.status",
                    "reason": "validation status must be pass, fail, blocked, or not_run; unknown is not allowed",
                })

    current_status_impact = field_block_text(handoff_text, "current_status_impact")
    if not current_status_impact:
        findings.append({
            "field": "current_status_impact",
            "reason": "compact handoff is missing current_status_impact block",
        })
    else:
        for field in CURRENT_STATUS_IMPACT_REQUIRED_FIELDS:
            if not line_field_exists(current_status_impact, field):
                findings.append({
                    "field": f"current_status_impact.{field}",
                    "reason": "compact handoff current_status_impact is missing required field",
                })

        impact_status = normalized_field_value(current_status_impact, "status")
        if impact_status not in CURRENT_STATUS_IMPACT_ALLOWED_VALUES:
            findings.append({
                "field": "current_status_impact.status",
                "reason": "status must be updated, not_applicable, or deferred",
            })

        reason = normalized_field_value(current_status_impact, "reason")
        if reason in {"", "pending", "unknown", "none", "tbd", "todo"}:
            findings.append({
                "field": "current_status_impact.reason",
                "reason": "reason is missing or non-specific",
            })

        updated = normalized_field_value(current_status_impact, "current_status_updated_in_this_pr")
        post_merge_safe = normalized_field_value(current_status_impact, "post_merge_safe")
        follow_up = normalized_field_value(current_status_impact, "follow_up_issue")

        if impact_status == "updated":
            if updated not in TRUE_VALUES:
                findings.append({
                    "field": "current_status_impact.current_status_updated_in_this_pr",
                    "reason": "status is updated but current_status_updated_in_this_pr is not true",
                })
            if post_merge_safe not in TRUE_VALUES:
                findings.append({
                    "field": "current_status_impact.post_merge_safe",
                    "reason": "status is updated but post_merge_safe is not true",
                })
        elif impact_status in {"not_applicable", "deferred"} and updated in TRUE_VALUES:
            findings.append({
                "field": "current_status_impact.current_status_updated_in_this_pr",
                "reason": f"status is {impact_status} but current_status_updated_in_this_pr is true",
            })

        if impact_status == "deferred":
            next_safe_action = normalized_field_value(handoff_text, "next_safe_action")
            if follow_up in EMPTY_FOLLOWUP_VALUES and next_safe_action in EMPTY_FOLLOWUP_VALUES:
                findings.append({
                    "field": "current_status_impact.follow_up_issue",
                    "reason": "deferred status needs follow_up_issue or a material next_safe_action",
                })

    if status_text:
        status_result = subprocess.run(
            ["python3", "scripts/asgk.py", "status-check", "--file", str(status_path)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        if status_result.returncode != 0:
            findings.append({
                "field": "current_status",
                "reason": "current-status file failed status-check",
            })

        active_work = markdown_section(status_text, "Active work")
        next_safe_action_section = markdown_section(status_text, "Next safe action")
        for issue in completed_issues:
            if issue and issue in active_work:
                findings.append({
                    "field": "current_status.active_work",
                    "reason": f"completed issue still appears in active work: {issue}",
                })
        for pr in completed_prs:
            if pr and pr in active_work:
                findings.append({
                    "field": "current_status.active_work",
                    "reason": f"completed PR still appears in active work: {pr}",
                })
        for branch in completed_branches:
            if branch and branch in active_work:
                findings.append({
                    "field": "current_status.active_work",
                    "reason": f"completed branch still appears in active work: {branch}",
                })
        if not next_safe_action_section:
            findings.append({
                "field": "current_status.next_safe_action",
                "reason": "current status next safe action is empty",
            })
        else:
            for pattern in CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS:
                if re.search(pattern, next_safe_action_section, flags=re.IGNORECASE):
                    findings.append({
                        "field": "current_status.next_safe_action",
                        "reason": f"next safe action appears to describe pre-merge closeout work: {pattern}",
                    })

    result = "fail" if findings else "pass"
    return result, {
        "result": result,
        "low_risk_inferred": False,
        "handoff_file": normalize_repo_path(str(handoff_file)),
        "current_status": normalize_repo_path(str(current_status_file)),
        "completed_refs_checked": {
            "issues": completed_issues,
            "prs": completed_prs,
            "branches": completed_branches,
        },
        "findings": findings,
    }
