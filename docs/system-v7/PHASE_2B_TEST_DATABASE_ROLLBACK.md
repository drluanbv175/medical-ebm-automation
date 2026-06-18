# Phase 2B Test Database Rollback

Ngày: 2026-06-18.

## Script

- `scripts/phase_2b_rollback_test_db.py`

## Scope

Rollback chỉ chạy trên isolated test DB. Không dùng `DROP TABLE` trên production trong Phase 2B.

## Result

PASS:

- Governance tables dropped trên test DB.
- Không còn bảng governance sau rollback.
- Reapply migration thành công.
- `missing_after_reapply = []`.
- `production_database_touched = false`.

Rollback nghiệp vụ trong runtime vẫn phải ghi `audit_events.event_type="rollback_event"` và không xóa lịch sử evidence/citation/release.
