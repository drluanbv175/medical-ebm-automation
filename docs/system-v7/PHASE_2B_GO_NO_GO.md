# Phase 2B GO / NO-GO

## Kết luận

GO FOR LIMITED SHADOW PILOT

## Phạm vi GO

Chỉ GO cho limited shadow pilot/read-only/draft-review có bác sĩ giám sát.

Không GO cho clinical production. Không GO cho auto-apply. Không GO cho kê đơn, đổi thuốc, gửi lời dặn người bệnh, ghi EMR/HIS hoặc export raw/restricted dataset.

## Điều kiện đã đạt

- Persistent migration test database: PASS.
- Rollback test database: PASS.
- Live adapters trả trạng thái an toàn: PASS.
- Live smoke: DNS/network unavailable -> `SOURCE_UNAVAILABLE`, không VERIFIED giả.
- Citation spoofing release: 0.
- PII export: 0.
- Approval bypass: 0.
- Clinical release flag bypass: 0.
- Clinical safety tests: PASS.
- Red-team tests: PASS.
- Dashboard giữ read-only.
- Risky clinical flags vẫn false.
- Synthetic pilot workflow đủ điều kiện khi chưa có pathway thật được duyệt.
- ResearchOS pilot traceability synthetic metadata: PASS.
- Full pytest: 276 passed, 1 warning.
- Ruff: PASS.
- Compileall: PASS.

## Feature flags

Vẫn false:

- `v7_clinical_release`
- `v7_patient_education_export`
- `v7_emr_write`
- `v7_production_pathway`
- `v7_auto_apply_recommendations`

Chỉ được bật sau bác sĩ/system owner duyệt:

- `v7_read_only_dashboard`
- `v7_shadow_mode`

Không có flag nào được bật thông qua dashboard.

## Rủi ro còn lại

- Môi trường hiện tại không phân giải được DNS tới phần lớn live sources, nên live validation mới xác nhận fail-safe behavior, chưa xác nhận source availability thực tế.
- Guideline/RSS cần version/date trước khi được xem là verified.
- Chưa apply migration production.
- Clinical shadow pilot hiện dùng synthetic workflow, chưa có pathway thật được bác sĩ duyệt.
- ResearchOS pilot mới là metadata/synthetic traceability, không xác nhận dataset thật analysis-ready.

## Cần bác sĩ/system owner duyệt

- Bật `v7_read_only_dashboard` và `v7_shadow_mode` nếu muốn chạy pilot thật.
- Chọn pathway thật hoặc chấp nhận synthetic workflow cho vòng pilot đầu.
- Duyệt tập shadow cases không PII.
- Duyệt manifest export trước khi đưa sang ChatGPT Project.
- Duyệt ResearchOS pilot topic và xác nhận không có raw/PII.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
