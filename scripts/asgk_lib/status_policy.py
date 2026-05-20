"""Shared status-impact constants for ASGK validators."""

CURRENT_STATUS_IMPACT_REQUIRED_FIELDS = [
    "status",
    "reason",
    "current_status_updated_in_this_pr",
    "post_merge_safe",
    "follow_up_issue",
]

CLOSEOUT_PRE_MERGE_NEXT_ACTION_PATTERNS = [
    r"verify\s+github\s+actions",
    r"wait\s+for\s+github\s+actions",
    r"update\s+(?:the\s+)?merge\s+decision",
    r"merge\s+only\s+if",
    r"merge\s+pr\s+#?\d+",
    r"close\s+issue\s+#?\d+",
]

CURRENT_STATUS_IMPACT_ALLOWED_VALUES = {"updated", "not_applicable", "deferred"}
CANONICAL_CURRENT_STATUS_PATH = "docs/handoff/CURRENT_STATUS.md"
TRUE_VALUES = {"true", "yes"}
EMPTY_FOLLOWUP_VALUES = {"", "none", "null", "tbd", "todo"}
