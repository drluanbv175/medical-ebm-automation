# Phase 2A Persistence Model

Ngày: 2026-06-18.

## Mục tiêu

Phase 2A thêm persistent governance cho shadow/review mode. Mục tiêu là truy nguyên run, approval, citation verification, export, rollback, incident và release staging. Không bật clinical production.

## Bảng governance

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

## Trường tối thiểu

Mỗi bảng có:

- `id`
- `version`
- `created_at`
- `updated_at`
- `created_by`
- `status`
- `environment`

Các record gắn với một lần chạy hoặc cần audit theo run có `run_id`.

## Quy tắc bất biến

- Không lưu PII.
- Mọi mutation ghi `audit_events`.
- State transition dùng `app/core/run_state_machine.py`.
- Rollback ghi `rollback_event`, không xóa lịch sử.
- Evidence superseded/retracted giữ record cũ và ghi `history_json`.
- Citation verification được lưu vào `citation_verification_records`; `SOURCE_UNAVAILABLE` không được nâng thành `VERIFIED`.
- Release manifest chỉ là staging trong Phase 2A và cần approval; không tự phát hành lâm sàng.

## Shadow mode boundary

Được phép:

- Draft/review-only run.
- Read-only dashboard.
- Synthetic clinical safety eval.
- ChatGPT context export nếu manifest hợp lệ và không có PII/raw dataset.

Không được phép:

- Auto apply recommendation.
- Kê đơn hoặc đổi thuốc.
- Gửi lời dặn bệnh nhân.
- Ghi EMR/HIS.
- Export raw dataset.
- Production pathway.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
