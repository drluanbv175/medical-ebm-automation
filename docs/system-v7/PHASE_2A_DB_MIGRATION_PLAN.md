# Phase 2A DB Migration Plan

Migration ID: `v7_phase_2a_governance_20260618`

## Schema Before

Database hiện hữu dùng SQLAlchemy + SQLite/dev database, `init_db()` tạo các bảng pipeline EBM cũ và một số migration nhẹ bằng `ALTER TABLE`. Chưa có Alembic.

## Schema After

Thêm governance schema V7, không sửa bảng cũ:

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

Trường tối thiểu trên mỗi bảng:

- `id`
- `version`
- `created_at`
- `updated_at`
- `created_by`
- `status`
- `environment`
- `run_id` khi record gắn với một run hoặc cần nối audit về run.

Nguyên tắc dữ liệu:

- Không lưu PII.
- Mọi mutation phải có `audit_events`.
- Transition `run_packets.state/status` đi qua validator `app/core/run_state_machine.py`.
- Release cần approval record; Phase 2A không bật release production.
- Rollback ghi `audit_events.event_type="rollback_event"`.
- Evidence superseded/retracted giữ record và history, không xóa.
- Citation verification ghi vào `citation_verification_records`.

## Dữ liệu bị ảnh hưởng

Không có dữ liệu cũ bị sửa. Phase 2A chỉ tạo bảng mới khi chạy explicit migration helper.

## Backup Strategy

1. Dừng dashboard/scheduler.
2. Sao lưu `data/medical_ebm.db` sang `data/archive/medical_ebm_pre_v7_phase_2a_<timestamp>.db`.
3. Chạy dry-run và lưu output SQL.
4. Chỉ chạy `--apply-dev` trên DB dev/test đã xác nhận.

## Dry-run Procedure

```bash
PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python scripts/phase_2a_governance_migration.py
```

Dry-run phải báo `destructive=False`.

## Apply Dev Procedure

Chỉ dùng trên DB dev/test:

```bash
DATABASE_URL=sqlite:////private/tmp/ebm_phase_2a.db PYTHONPYCACHEPREFIX=/private/tmp/ebm_pycache /Users/nguyenluan/.ebm-venv/bin/python scripts/phase_2a_governance_migration.py --apply-dev
```

## Test Migration

Test tự động:

- `tests/test_phase_2a_governance_persistence.py`

## Production Rule

Không chạy migration production trong Phase 2A nếu chưa có bác sĩ/system owner duyệt.
