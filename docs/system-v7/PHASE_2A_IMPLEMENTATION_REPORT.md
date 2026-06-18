# Phase 2A Implementation Report

Ngày: 2026-06-18.

## File chính đã thêm/sửa

- Persistent governance: `app/models/governance_v7.py`, `app/governance/migrations.py`, `app/governance/repository.py`.
- Migration helper: `scripts/phase_2a_governance_migration.py`.
- Citation verification: `app/evidence/citation_verification.py`.
- Export safety: `app/core/export_policy.py`, `app/export_bridge/chatgpt_project_bridge.py`.
- Safety eval: `app/safety/evaluation_suite.py`, `tests/evals/clinical_safety/*`, `tests/evals/clinical_safety/evidence_integrity/`.
- Dashboard read-only: `app/dashboard/v7_readonly.py`, `app/dashboard/main.py`.
- Feature flags: `app/core/feature_flags.py`.
- Tests Phase 2A: `tests/test_phase_2a_*.py`, `tests/evals/clinical_safety/test_phase_2a_clinical_safety_eval.py`.
- Docs Phase 2A: `PHASE_2A_PERSISTENCE_MODEL.md`, `PHASE_2A_SOURCE_VERIFICATION_POLICY.md`, `PHASE_2A_CHATGPT_BRIDGE_GUIDE.md`.

## Migration status

Không chạy destructive migration. Dry-run migration in 13 bảng governance mới và báo `destructive=False`.

Các bảng governance:

- `run_packets`
- `approval_records`
- `audit_events`
- `incident_records`
- `evidence_records_v2`
- `claim_records`
- `recommendation_cards`
- `clinical_decision_records`
- `research_lock_records`
- `release_manifests`
- `export_manifests`
- `feature_flag_audit`
- `citation_verification_records`

Mỗi bảng có tối thiểu: `id`, `version`, `created_at`, `updated_at`, `created_by`, `status`, `environment`; các bảng cần truy nguyên run có `run_id`.

## Clinical production

Không bật clinical production. Các flag rủi ro vẫn mặc định `False`:

- `v7_clinical_release`
- `v7_patient_education_export`
- `v7_emr_write`
- `v7_production_pathway`
- `v7_auto_apply_recommendations`

## Test cuối cùng

- Phase 2A focused tests: 31 passed.
- Full pytest: 268 passed, 1 warning.
- Full ruff: PASS.
- Full compileall: PASS.
- Migration dry-run: 13 missing governance tables, `destructive=False`.
- Agent guardrail enforcement: PASS, 48 agents checked, 0 changed.
- Agent sync check: PASS, 48 source agents, 48 Codex TOML.
- EBM audit: PASS.
- ChatGPT manifest stage: 34 files, `safe_to_upload=true`.

## Giới hạn

Phase 2A đủ điều kiện kỹ thuật ban đầu cho shadow mode có giám sát nếu full test/audit cuối PASS. Không đủ để tự áp dụng lâm sàng.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
