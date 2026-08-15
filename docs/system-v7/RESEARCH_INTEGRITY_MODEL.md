# Research Integrity Model

## Bất biến

- Không phân tích chính thức trước khi khóa SAP và data.
- Không sửa biến chính sau data lock nếu không có amendment.
- Không báo cáo chọn lọc.
- Không gán tác giả nếu thiếu đóng góp thật.
- Không export dataset thô qua ChatGPT Project.

## Module thực thi

- `PolicyEngine`: chặn `research_official_analysis` khi `data_locked=False`.
- `sap_engine`: `can_run_official_analysis`.
- `data_lock`: hash manifest.
- `data_quality_firewall`: PII, missingness, data dictionary.
- `study_traceability_matrix`: nối câu hỏi - biến - phân tích - bảng.
