# Phase 2A DB Rollback Plan

Migration ID: `v7_phase_2a_governance_20260618`

## Rollback nhanh

Vì Phase 2A không tự bật production migration, rollback vận hành là:

1. Không chạy `scripts/phase_2a_governance_migration.py --apply-dev`.
2. Giữ `v7_clinical_release=false`, `v7_patient_education_export=false`, `v7_emr_write=false`, `v7_production_pathway=false`.
3. Không import repository governance trong runtime production.

## Nếu đã apply trên DB dev/test

Dev/test rollback có thể xóa DB test hoặc restore backup. Không dùng `DROP TABLE` trên production trong Phase 2A.

Mọi rollback nghiệp vụ phải ghi audit event:

- `audit_events.event_type = "rollback_event"`
- `run_id` nếu rollback gắn với một run.
- `actor` là người/hệ thống yêu cầu rollback.
- `payload_json.reason` không chứa PII.

Không xóa `evidence_records_v2`, `citation_verification_records`, `approval_records`, hoặc `release_manifests` để "làm sạch" lịch sử. Nếu evidence lỗi, chuyển `status/lifecycle_status` sang `superseded`, `retracted`, hoặc `quarantined` và giữ `history_json`.

## Restore production

Nếu system owner đã tự chạy migration lên DB thật sau này:

1. Dừng scheduler/dashboard.
2. Restore file backup `medical_ebm_pre_v7_phase_2a_*.db`.
3. Chạy `python3 ../tools/audit_ebm_system.py`.
4. Chạy `pytest` và `ruff check`.

## Rollback trigger

- PII leakage.
- Approval bypass.
- Clinical release flag bật nhầm.
- Export manifest `safe_to_upload=false`.
- Bất kỳ critical red-flag miss trong eval suite.
- Citation adapter trả lỗi nhưng record vẫn bị đánh dấu `VERIFIED`.
- Recommendation card thiếu claim ID, stale source, hoặc chưa có approval nhưng vẫn release.
