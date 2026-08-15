# Phase 2B Clinical Shadow Pilot Charter

Ngày: 2026-06-18.

## Scope

Pilot chỉ phục vụ:

- Đánh giá luồng điều phối.
- Đánh giá safety gate.
- Đánh giá citation/evidence traceability.
- Đánh giá usability dashboard.
- Đánh giá physician override.

Không phục vụ clinical production, kê đơn, đổi thuốc, ghi EMR/HIS, gửi lời dặn người bệnh hoặc auto-apply pathway.

## Pathway selection

Chỉ chọn tối đa 3 pathway nếu có đủ scope, input requirements, red flags, safety rules, evidence manifest, claim traceability, approval record, test cases và không có stale/retracted source chưa xử lý.

Trạng thái hiện tại: chưa phát hiện pack thật đủ điều kiện trong repo, nên Phase 2B dùng `synthetic_generic_shadow_workflow`. Synthetic workflow không tự gán clinical content.

## Priority topics for later physician choice

- Hen phế quản ngoại trú.
- COPD ngoại trú.
- Tăng huyết áp ngoại trú.
- Đái tháo đường type 2.
- Suy tim mạn ổn định.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
