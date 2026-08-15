# Phase 2D ResearchOS Metadata Readiness

Project: `Đánh giá sự hài lòng của người bệnh ngoại trú tại Khoa Khám bệnh C1a – Bệnh viện Quân y 175`

## Metadata Boundary

No raw dataset, patient-level records, identifiable questionnaire sheets, or PII are imported.

## Metadata Items

| Item | Status | Notes |
|---|---|---|
| Tên đề tài | documented | Metadata-only. |
| Mục tiêu | needs_pi_confirmation | Must be confirmed by PI. |
| Thiết kế | needs_pi_confirmation | Not analysis-ready. |
| Outcome | needs_variable_mapping | Outcome must map to measured variables. |
| Biến số | needs_data_dictionary | Data dictionary not locked. |
| Questionnaire mapping | needs_mapping | No raw questionnaire imported. |
| Data dictionary | not_locked | Must be versioned and synchronized. |
| SAP | not_locked | Must be locked before analysis-ready. |
| Syntax metadata | not_versioned | No syntax version confirmed. |
| Expected tables | draft | Must match SAP. |
| Reporting checklist | draft | Needs protocol/reporting guideline selection. |
| Data quality summary không PII | pending | No raw data imported. |

## Readiness Decision

`analysis_ready = false`

Reasons:

- SAP chưa lock.
- Data dictionary chưa đồng bộ.
- Outcome chưa có biến đo được xác nhận.
- Syntax chưa version.
- Dataset status chưa rõ.
- Data lock chưa được xác nhận.

Cần bác sĩ/PI kiểm chứng trước khi áp dụng nghiên cứu.
