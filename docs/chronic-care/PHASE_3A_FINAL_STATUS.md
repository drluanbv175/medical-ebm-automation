# Phase 3A Final Status

Ngày: 2026-06-18.

## Đã hoàn thành

- Rà soát baseline V7 và ghi `PHASE_3A_BASELINE_REVIEW.md`.
- Tạo kiến trúc, ranh giới scope, data model, test plan và risk register.
- Tạo module `app/chronic_care/`.
- Tạo SQLAlchemy models và migration helper không phá hủy.
- Tạo synthetic case pack 30 cases theo đúng phân bố.
- Tạo workflow engine synthetic cho enrollment, review, task, escalation, risk draft, care-plan draft, quality metrics và aggregate export.
- Tích hợp V7 `RunPacket`, `AuditLogger`, `ApprovalCenter`, `PolicyEngine`, `FeatureFlags`.
- Tạo rule catalog CC-001 đến CC-005.
- Tạo dashboard read-only adapter và nối tab `Chronic Care Shadow Pilot` vào Streamlit dashboard.
- Tạo docs user/operator/data dictionary/rule/synthetic/approval/limitations/GO-NO-GO/blockers.
- Tạo tests functional, safety, red-team và eval docs.

## Chưa hoàn thành

- Chưa chạy production migration.
- Chưa có persistent production chronic-care data.
- Chưa có real EMR/HIS integration.
- Chưa có patient communication policy implementation.
- Chưa có UAT với cơ sở thật.
- Chưa có legal/DPIA/clinical safety sign-off.
- Chưa có approved clinical knowledge pack cho production.

## Module bị chặn

- Patient-facing messaging: blocked.
- Patient education export: blocked.
- Medication change/prescription workflow: blocked.
- EMR/HIS write-back: blocked.
- Clinical release/auto-apply/production pathway: blocked.

## Feature flags hiện tại

Risky flags vẫn phải `False`:

- `v7_clinical_release`
- `v7_patient_education_export`
- `v7_emr_write`
- `v7_production_pathway`
- `v7_auto_apply_recommendations`

Phase 3A không thêm UI để bật các flag này.

## Kết quả test

- Focused Phase 3A: `20 passed`.
- Full pytest: `313 passed, 1 warning`.
- Ruff: `PASS`.
- Compileall: `PASS`.
- EBM audit: `PASS`.

## Kết quả red-team

- Prompt injection success: 0.
- PII export: 0 in normal path; PII-like export probe blocked.
- Approval bypass: 0 in normal path; non-physician approval probe blocked.
- Clinical release flag bypass: 0.
- Patient-facing output without approval: 0 in normal path; output attempt blocked.
- Unverified evidence released: 0.
- Recommendation without claim ID released: 0.
- Audit event missing: 0.

## Các migration đã tạo

- Migration helper only: `app/chronic_care/migration.py`.
- Migration ID: `phase_3a_chronic_care_shadow_20260618`.
- Tables planned: `chronic_care_enrollments`, `chronic_care_reviews`, `chronic_care_risk_drafts`, `chronic_care_tasks`, `chronic_care_plan_drafts`, `chronic_care_timeline_events`, `chronic_care_quality_metrics`.
- Không tự chạy production migration.

## Các files đã thêm/sửa

- Added `app/chronic_care/`.
- Modified `app/dashboard/main.py` to add read-only tab 14.
- Added `docs/chronic-care/` Phase 3A docs.
- Added `tests/test_phase_3a_chronic_care_*.py`.
- Added `tests/evals/chronic_care/PHASE_3A_EVAL.md`.
- Added `tests/evals/red_team/PHASE_3A_CHRONIC_CARE_RED_TEAM.md`.

## Rủi ro còn lại

- Synthetic-only behavior có thể bị hiểu nhầm nếu người vận hành bỏ qua limitations.
- Migration chưa được duyệt/chạy trên DB thật.
- Dashboard tab tạo snapshot in-memory, chưa đọc persisted chronic-care tables.
- Audit JSONL/in-memory test path cần production persistence nếu pilot thật.
- Evidence/claim gate trong Phase 3A kiểm theo references synthetic, chưa nối live evidence registry persisted.

## Production blockers

Xem `PHASE_3A_PRODUCTION_BLOCKERS.md`. Tóm tắt: chưa có legal assessment, DPIA, infra production, penetration test, backup/restore production validation, UAT, clinical safety sign-off, approved clinical knowledge pack, EMR/HIS integration, patient communication policy, training/competency assessment.

## Điều cần bác sĩ/system owner duyệt

- Duyệt scope synthetic shadow pilot.
- Duyệt migration dry-run nếu muốn persisted test database.
- Duyệt chronic-care rule catalog CC-001..CC-005 cho shadow mode.
- Duyệt dashboard read-only nội bộ.
- Duyệt tiêu chí GO/NO-GO trước pilot ngoài môi trường dev.

## Khuyến nghị bước tiếp theo

1. System owner review Phase 3A docs and blockers.
2. Run migration helper only on a test database.
3. Wire dashboard to persisted synthetic test DB if needed.
4. Conduct UAT with synthetic cases.
5. Keep all risky flags false until formal Phase 3B approval.
