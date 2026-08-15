# Clinical Safety Model

## Cổng chặn

- PII: `PolicyEngine` và `AuditLogger`.
- Cờ đỏ: `red_flag_engine`.
- Thiếu dữ liệu: `data_sufficiency_engine`.
- Thuốc nguy cơ: `medication_safety_engine`.
- Chống chỉ định: `contraindication_engine`.
- Bất định cao: `uncertainty_escalation_engine`.
- Chưa duyệt: `ApprovalCenter` và `ReleaseManager`.

## Mức hiện tại

Safety model hiện là deterministic scaffold để chặn tình huống rõ ràng trong workflow agent. Nó không thay thế đánh giá cấp cứu, kê đơn, tương tác thuốc chuyên sâu, hoặc guideline chính thức.

## Disclaimer bắt buộc

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
