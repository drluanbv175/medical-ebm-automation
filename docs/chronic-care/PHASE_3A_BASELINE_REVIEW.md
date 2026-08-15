# Phase 3A Baseline Review

Ngày: 2026-06-18.

## Tài liệu và code đã rà soát

- `AGENTS.md`, `README.md`.
- `docs/system-v7/IMPLEMENTATION_REPORT.md`.
- `docs/system-v7/PHASE_2A_GO_NO_GO.md`.
- `docs/system-v7/PHASE_2B_GO_NO_GO.md`.
- `docs/system-v7/PHASE_2B_CLINICAL_SHADOW_PILOT_CHARTER.md`.
- `docs/system-v7/PHASE_2B_IMPLEMENTATION_REPORT.md`.
- `docs/system-v7/PHASE_2A_DASHBOARD_READONLY.md`.
- `docs/system-v7/04_MIGRATION_PLAN.md`.
- `app/core/`, `app/evidence/`, `app/safety/`, `app/clinical_content/`, `app/dashboard/`, `tests/`.

Một số file yêu cầu ở root thực tế nằm trong `docs/system-v7/`; Phase 3A dùng đúng vị trí hiện có.

## Module V7 có thể tái sử dụng

- `FeatureFlags`: giữ risky flags mặc định `False`.
- `RunPacket`: chuẩn hóa lane, run_id, feature flags, approval status.
- `PolicyEngine`: chặn PII, export unsafe, release clinical khi thiếu approval/flag.
- `AuditLogger`: JSONL audit với scrub PII-like text.
- `ApprovalCenter`: approval in-memory cho shadow/test.
- `ReleaseManager`: chỉ release khi approved + policy allowed.
- `EvidenceRegistry`, `ClaimRegistry`: traceability cho evidence/claim.
- `export_policy`: phân loại export và chặn PII/raw dataset.
- `shadow_mode`: comparator không ảnh hưởng production.
- `dashboard/v7_readonly.py`: pattern snapshot + render read-only.

## Bảng governance hiện có

Theo `app/governance/migrations.py`, governance V7 có 13 bảng: `run_packets`, `approval_records`, `audit_events`, `incident_records`, `evidence_records_v2`, `claim_records`, `recommendation_cards`, `clinical_decision_records`, `research_lock_records`, `release_manifests`, `export_manifests`, `feature_flag_audit`, `citation_verification_records`.

## Feature flags đang tồn tại

Risky flags mặc định `False`: `v7_clinical_release`, `v7_patient_education_export`, `v7_emr_write`, `v7_production_pathway`, `v7_auto_apply_recommendations`. Phase 3A không tạo UI bật các flag này.

## Safety gates đã có

- PII detection/scrub.
- Claim requires traceability.
- Recommendation requires claim ID.
- Citation verification required when requested.
- Clinical release requires physician approval and feature flag.
- Export blocks raw dataset and PII.
- Red-flag unresolved blocks clinical lane.

## Adapter/dashboard hiện có

- Dashboard Streamlit chính `app/dashboard/main.py`.
- Tab `V7 Shadow Read-only` ở `app/dashboard/v7_readonly.py`.
- Evidence Workbench và registry adapter hiện có, giữ nguyên.

## Phần phải giữ nguyên

- V7 governance/control plane.
- Evidence/claim/citation lifecycle.
- Safety modules.
- Dashboard V7 read-only.
- ResearchOS and clinical content modules.
- Existing tests and docs.

## Phần chưa được phép production

- Clinical release.
- Auto-apply.
- Patient education export.
- EMR/HIS write-back.
- Production pathway.
- Any real-patient chronic care workflow.

## Phần cần mở rộng cho chronic care

- Module `app/chronic_care/`.
- Synthetic registry/enrollment/task/review/risk-draft/care-plan-draft/timeline/quality metrics.
- Chronic-care migration helper không phá hủy.
- Read-only dashboard tab `Chronic Care Shadow Pilot`.
- Focused functional, safety and red-team tests.
