# RISK REGISTER SỐNG (A13b) — hai-long-benh-nhan-C1a-BVQY175
> [DỰ THẢO] Mức xác suất/tác động phải được nhóm nghiên cứu hiệu chỉnh.

| ID | Loại | Rủi ro | Xác suất | Tác động | Giảm thiểu trước | CAPA nếu xảy ra | Chủ nhân | Trạng thái | Ngày rà |
|---|---|---|---|---|---|---|---|---|---|
| G1-R01 | Thiết kế | Thiết kế không khớp câu hỏi/estimand | [CẦN] | Cao | Methodologist rà trước G2 | Sửa protocol có version; vô hiệu downstream cũ | PI/Methodologist | Mở | [CẦN NGƯỜI RÀ] |
| G1-R02 | Đạo đức | Hồ sơ không khớp phiên bản protocol | [CẦN] | Cao | Hash/version mọi artifact | Dừng tuyển; amendment IRB | PI | Mở | [CẦN NGƯỜI RÀ] |
| G1-R03 | Tuyển mẫu | Không đạt tốc độ tuyển dự kiến | [CẦN] | Cao | Feasibility log + nhiều điểm tuyển | CAPA tuyển mẫu; điều chỉnh timeline đã duyệt | Site lead | Mở | [CẦN NGƯỜI RÀ] |
| G1-R04 | Dữ liệu | Thiếu/sai dữ liệu kết cục chính | [CẦN] | Cao | CRF validation + pilot | Query/CAPA; không tự điền dữ liệu | Data Manager | Mở | [CẦN NGƯỜI RÀ] |
| G1-R05 | Thống kê | Outcome/SAP thay đổi sau xem dữ liệu | [CẦN] | Cao | Khóa SAP G4 | Ghi deviation; phân tích gắn nhãn thăm dò | Biostatistician | Mở | [CẦN NGƯỜI RÀ] |
| G1-R06 | Liêm chính | Trích dẫn ma/sai nội dung | [CẦN] | Cao | Evidence Ledger + A12 | Loại/sửa nguồn; chạy lại A12 | Evidence reviewer | Mở | [CẦN NGƯỜI RÀ] |

## Quy tắc cập nhật
- Rà sau mỗi cổng và khi có protocol amendment.
- Ghi mọi thay đổi vào `study_meta.json → gate_params.G1.risk_register` (giữ dòng cũ, cập nhật trạng thái, ngày rà,
  nguyên nhân và CAPA) rồi chạy lại G1 — tệp .md này được SINH LẠI, sửa tay sẽ bị ghi đè (bản sửa tay được sao lưu).

> Cần bác sĩ kiểm chứng.
