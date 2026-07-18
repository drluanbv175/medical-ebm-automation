# Personal Production Hardening Report

- Generated: `2026-07-17T10:35:17+00:00`
- Overall status: `CONTROLLED_PERSONAL_READY_WITH_HUMAN_GATES`
- Fail count: `0`
- Human gates: `6`
- Evidence package: `NOT_PROVIDED`
- Clinical production allowed: `False`
- Real patient data allowed: `False`

| Domain | Status | Key findings | Required human action |
|---|---|---|---|
| P1 - Đóng 37 blocker production bằng bằng chứng thật, không tự gỡ | `HUMAN_GATE` | open_blocker_bullets=37<br>production remains blocked until a valid evidence package and independent signoffs exist. | Bác sĩ/quản trị viên chỉ đánh dấu blocker CLEARED sau khi có evidence package, 5 signoff độc lập, dossier hash, rollback và checklist hậu triển khai. |
| P2 - Xác thực actor thật cho PI/IRB/thống kê/phản biện | `HUMAN_GATE` | approval ledger binds role, artifact hash, timestamp and optional local HMAC signature. | Bác sĩ tự chạy setup_gate_approval_key.py ngoài phiên agent; mỗi approval thật phải do người đúng vai trò tự thực hiện, không nhờ agent chạy hộ. |
| P3 - Pipeline dữ liệu thật: PII → pseudonymization → cleaning → data lock | `HUMAN_GATE` | raw file is never overwritten; linkage map stays outside repo/OneDrive by default. | Trước dữ liệu thật: cần IRB/DMP, retention owner, mapping custody, data manager xác nhận no-PII và PI ký data-lock. |
| P4 - SOP cá nhân: khi dùng, khi dừng, ai duyệt | `HUMAN_GATE` | single personal SOP now binds the 7 hardening domains to daily operation. | Bác sĩ/quản trị viên đọc SOP, điền người phụ trách thật và lưu bản ký tại cơ sở trước khi chuyển từ synthetic/de-identified pilot sang dữ liệu thật. |
| P5 - UAT bằng dữ liệu giả lập và đã khử định danh trước dữ liệu thật | `HUMAN_GATE` | UAT artifacts exist but real clinic UAT signoff must remain an external human gate. | Chạy shadow/UAT với dữ liệu synthetic hoặc đã khử định danh; bác sĩ, điều dưỡng, quản trị dữ liệu ký biên bản trước khi bật bất kỳ workflow thật nào. |
| P6 - Backup, versioning, rollback, monitoring và incident response | `HUMAN_GATE` | repo has rollback and incident contracts; production still needs restore drill evidence. | Thực hiện restore drill có checksum, xác nhận RPO/RTO, tabletop incident drill và change ticket/rollback plan cho từng lần go-live. |
| P7 - Tách research_mode và clinical_support_mode, không auto-apply/EMR write | `PASS` | dangerous_flags_disabled=true | Chỉ bật research official analysis hoặc clinical release bằng change-control riêng, không bật chung với auto-apply hoặc EMR write khi chưa có go-live signoff. |

## Evidence Package

- Status: `NOT_PROVIDED`
- Valid evidence records: `0/7`
- Valid signoffs: `0/6`
- Missing domains: `P1, P2, P3, P4, P5, P6, P7`
- Missing signoffs: `security_owner, data_protection_owner, physician_lead, operations_owner, ai_governance_owner, pi_or_clinic_owner`

Cần bác sĩ kiểm chứng. Đây là cổng hardening kỹ thuật/offline; không thay IRB, PI, thống kê viên, phản biện độc lập, pháp lý, bảo mật bệnh viện, UAT hoặc quyết định lâm sàng.
