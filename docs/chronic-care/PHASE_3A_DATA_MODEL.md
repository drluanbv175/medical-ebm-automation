# Phase 3A Data Model

Các model SQLAlchemy nằm ở `app/chronic_care/models.py`. Migration helper nằm ở `app/chronic_care/migration.py` và không tự chạy trong `init_db()`.

## Tables

- `chronic_care_enrollments`
- `chronic_care_reviews`
- `chronic_care_risk_drafts`
- `chronic_care_tasks`
- `chronic_care_plan_drafts`
- `chronic_care_timeline_events`
- `chronic_care_quality_metrics`

## Key principles

- `patient_reference_id` chỉ là synthetic ID như `SYN-HTN-001`.
- Không lưu họ tên, số điện thoại, địa chỉ, ngày sinh đầy đủ, mã bệnh án thật hoặc dữ liệu định danh.
- `environment` mặc định `synthetic_shadow`.
- `version` luôn có.
- Risk/care-plan chỉ là draft shadow; care-plan không có trạng thái active clinical plan.
