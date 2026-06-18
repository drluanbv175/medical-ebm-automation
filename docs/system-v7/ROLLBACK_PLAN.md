# Rollback Plan

## Rollback nhanh

- Tắt mọi flag V7 rủi ro trong `DEFAULT_FEATURE_FLAGS`.
- Không import V7 runtime vào dashboard production.
- Dùng pipeline hiện hữu như trước.

## Rollback code

V7 là module thêm mới, không đổi DB schema hiện hữu. Rollback code có thể thực hiện bằng revert các thư mục:

- `app/core`
- `app/evidence`
- `app/safety`
- `app/clinical_content`
- `app/research_os`
- `app/export_bridge`
- `app/patient_education`
- `app/dashboard/v7_registry.py`
- `tests/test_v7_*`
- `docs/system-v7`

## Điều kiện rollback bắt buộc

- Bất kỳ PII leakage thật.
- Clinical release không qua approval.
- Evidence thiếu truy nguyên xuất hiện ở dòng chính.
- Research official analysis chạy khi chưa data lock.
