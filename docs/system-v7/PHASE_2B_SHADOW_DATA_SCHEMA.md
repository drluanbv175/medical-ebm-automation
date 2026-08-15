# Phase 2B Shadow Data Schema

Ngày: 2026-06-18.

## Module

- `app/clinical_content/shadow_pilot.py`

## Allowed non-PII fields

- `shadow_case_id`
- `pathway_id`
- `environment`
- `question_type`
- `clinical_domain`
- `data_completeness`
- `red_flag_screen`
- `comorbidity_flags`
- `medication_context`
- `evidence_snapshot_id`
- `physician_review_required`

## Forbidden fields

- Tên người bệnh.
- Ngày sinh.
- Số điện thoại.
- Mã bệnh án.
- Địa chỉ.
- Ngày khám cụ thể.
- Ảnh hồ sơ.
- Dữ liệu nhận diện.

## Physician override log

- `override_id`
- `shadow_case_id`
- `recommendation_status`
- `physician_action`
- `override_reason_category`
- `free_text_reason_sanitized`
- `reviewer_role`
- `timestamp`

Override reason free text bị chặn nếu chứa PII-like text.
