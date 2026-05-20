#!/usr/bin/env python3
"""Validate bootstrap governance scaffold.

Dependency-light by design: no PyYAML/jsonschema required. This catches common
AI-over-simplification failures: missing files, missing required sections,
missing durable source fields, thin templates, invalid JSON, and storage-boundary
regressions.
"""
from __future__ import annotations
import json, re, sys
from pathlib import Path

REQUIRED_FILES = [
 'README.md','AGENTS.md',
 'docs/bootstrap/00_project_brief.md','docs/bootstrap/01_physical_boundaries.md','docs/bootstrap/02_storage_roots.md','docs/bootstrap/03_tech_stack.md','docs/bootstrap/04_file_structure.md','docs/bootstrap/05_context_budget.md','docs/bootstrap/06_naming_versioning.md','docs/bootstrap/07_contract_first.md','docs/bootstrap/08_acceptance_criteria.md','docs/bootstrap/09_safety_checks.md','docs/bootstrap/10_roadmap.md','docs/bootstrap/11_auto_merge_policy.md','docs/bootstrap/12_productization_notes.md','docs/bootstrap/13_artifact_promotion_policy.md','docs/bootstrap/14_execution_lanes.md','docs/bootstrap/15_source_or_input_class_matrix.md','docs/bootstrap/16_downstream_promotion_matrix.md','docs/bootstrap/17_readiness_audit_policy.md',
 'docs/architecture/BOUNDARY_SPLIT.md','docs/architecture/EXTERNALIZED_RESPONSIBILITY_BOUNDARY.md','docs/architecture/STORAGE_PROFILE.md','docs/architecture/WORKSPACE_LOCK_POLICY.md','docs/architecture/CACHE_AND_STATE_POLICY.md','docs/architecture/RUNTIME_ARTIFACT_POLICY.md',
 'docs/control/CONTROL_LAYER_V0.md','docs/control/WORK_UNIT_STATE_MODEL.md','docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md','docs/control/HUMAN_GATED_OPERATIONS.md','docs/control/ISSUE_HYGIENE_GATE.md','docs/control/TASK_PACKET_FORMAT.md','docs/control/AGENT_REPORT_FORMAT.md','docs/control/MERGE_DECISION_RECORD.md','docs/control/FAILURE_THRESHOLDS.md','docs/control/PHASE_0_ACCEPTANCE_CHECKLIST.md',
 'docs/handoff/CURRENT_STATUS.md','docs/handoff/DECISIONS.md','docs/handoff/AGENT_LOG.md',
 'templates/task_packet.template.yaml',
 'contracts/storage_profile.contract.yaml','contracts/artifact_contract.yaml','contracts/validation_result.contract.yaml','contracts/promotion_gate.contract.yaml','contracts/execution_lane.contract.yaml',
 'schemas/validation_result.schema.json','schemas/storage_profile.schema.json','schemas/task_packet.schema.json','schemas/merge_decision.schema.json','schemas/promotion_gate.schema.json','schemas/execution_lane.schema.json','schemas/agent_report.schema.json',
 'scripts/check_project.py','scripts/validate_bootstrap.py','scripts/governance_hygiene.py',
 '.github/ISSUE_TEMPLATE/agent_task.yml','.github/ISSUE_TEMPLATE/workbench_task.md','.github/PULL_REQUEST_TEMPLATE.md','.github/workflows/bootstrap-validation.yml',
 'examples/storage_profile.local.json','examples/task_packet.example.yaml','examples/merge_decision.example.json','examples/promotion_gate.example.json','examples/execution_lane.example.json','examples/agent_report.example.md'
]

REQUIRED_TERMS = {
 'AGENTS.md':['see chat','Issue Hygiene Gate','Stop conditions','Low-risk merge boundary'],
 'docs/bootstrap/01_physical_boundaries.md':['writable_paths','protected_paths','forbidden_actions','Artifact Root','Local State Root'],
 'docs/bootstrap/02_storage_roots.md':['code_repo','artifact_root','local_state_root','app_managed_drive_api','local_only'],
 'docs/bootstrap/11_auto_merge_policy.md':['auto_merge_allowed_when','auto_merge_forbidden_when','Merge Decision Record','durable source of truth'],
 'docs/bootstrap/13_artifact_promotion_policy.md':['Traceability is required, but traceability alone is not enough','blocked_thin_context','blocked_class_use_mismatch'],
 'docs/bootstrap/14_execution_lanes.md':['deterministic','codex_operated','api_provider','requires_allow_live_call_flag'],
 'docs/control/CONTROL_LAYER_V0.md':['Durable Control Surfaces','Work Unit State Model','Task Packet Format','Agent Report Format','Anti-drift Rules','Human Gates','Definition of Done'],
 'docs/control/LOW_RISK_AUTONOMOUS_MERGE_POLICY.md':['Necessary operations allowed','Prohibited without human approval','Low-risk merge gates','After merge'],
 'docs/architecture/EXTERNALIZED_RESPONSIBILITY_BOUNDARY.md':['External Preparation App','Closed gates','raw PDF ingestion','OCR','prepared input'],
}

CONTROL_REQUIRED_SECTIONS = ['Purpose','Durable Control Surfaces','Work Unit State Model','Task Packet Format','Agent Report Format','Operating Loop','Anti-drift Rules','Human Gates','Definition of Done']
TASK_PACKET_FIELDS = ['task_id','lane','intelligence_level','durable_source_of_truth','objective','allowed_paths','expected_output','plan','checklist','acceptance_sheet','stop_conditions','rollback_expectations']
PR_HEADINGS = ['Summary','Task Reference','Changed Files','Validation','Evidence Of Completion','Scope Boundaries','Current Status Impact','Runtime Output Status','Merge Decision','Known Gaps','Handoff Report']
ISSUE_FIELDS = ['objective','durable_source_of_truth','lane','intelligence_level','allowed_paths','expected_output','acceptance_sheet','stop_conditions']

def fail(msg):
    print(f'FAIL: {msg}')
    sys.exit(1)

def read(root, path):
    return (root/path).read_text(encoding='utf-8')

def check_terms(root):
    for path, terms in REQUIRED_TERMS.items():
        text = read(root, path)
        for term in terms:
            if term not in text:
                fail(f'{path} missing required term: {term}')

def check_json(root):
    for p in list((root/'schemas').glob('*.json')) + list((root/'examples').glob('*.json')):
        try:
            json.loads(p.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            fail(f'{p.relative_to(root)} invalid JSON: {e}')

def check_yaml_like_fields(root):
    packet = read(root,'templates/task_packet.template.yaml')
    for field in TASK_PACKET_FIELDS:
        if not re.search(rf'^{re.escape(field)}\s*:', packet, re.M):
            fail(f'templates/task_packet.template.yaml missing field: {field}')

def check_templates(root):
    pr = read(root,'.github/PULL_REQUEST_TEMPLATE.md')
    for h in PR_HEADINGS:
        if f'## {h}' not in pr:
            fail(f'PR template missing heading: {h}')
    issue = read(root,'.github/ISSUE_TEMPLATE/agent_task.yml')
    for field in ISSUE_FIELDS:
        if field not in issue:
            fail(f'agent_task.yml missing field/token: {field}')

def check_control_sections(root):
    text = read(root,'docs/control/CONTROL_LAYER_V0.md')
    for section in CONTROL_REQUIRED_SECTIONS:
        if f'## {section}' not in text:
            fail(f'CONTROL_LAYER_V0.md missing section: {section}')

def check_storage_profile(root):
    profile = json.loads(read(root,'examples/storage_profile.local.json'))
    if profile['artifact_root'] == profile['local_state_root']:
        fail('artifact_root and local_state_root must differ')
    if profile['sync_policy'].get('app_managed_drive_api') is not False:
        fail('app_managed_drive_api must be false')
    for key in ['page_renders','model_cache','sqlite_live_db','temporary_jobs']:
        if profile['cache_policy'].get(key) != 'local_only':
            fail(f'{key} cache policy must be local_only')

def main():
    root = Path.cwd()
    missing = [p for p in REQUIRED_FILES if not (root/p).exists()]
    if missing:
        for p in missing: print(f'Missing required file: {p}')
        fail(f'{len(missing)} required files missing')
    check_terms(root)
    check_json(root)
    check_yaml_like_fields(root)
    check_templates(root)
    check_control_sections(root)
    check_storage_profile(root)
    print('Bootstrap validation passed.')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
