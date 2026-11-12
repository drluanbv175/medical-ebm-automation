# RISK REGISTER SỐNG (A13b) — btm-dtd2-ngoai-tru-BVQY175
> [DỰ THẢO] Mức xác suất/tác động phải được nhóm nghiên cứu hiệu chỉnh (thang Thấp · Trung bình · Cao).

| ID | Loại | Rủi ro | Xác suất | Tác động | Giảm thiểu trước | CAPA nếu xảy ra | Chủ nhân | Trạng thái | Ngày rà |
|---|---|---|---|---|---|---|---|---|---|
| R1 | Dữ liệu | eHospital không lập được danh sách khung mẫu, hoặc hồ sơ thiếu kết quả creatinin, UACR, mã ICD-10, đơn thuốc của cửa sổ 2026 | Trung bình (máy ước — chủ nhiệm chỉnh) | Cao | Chủ nhiệm thử tra cứu vài hồ sơ và thử lập danh sách trên eHospital trước khi nộp Hội đồng | Đổi cách chọn mẫu hoặc nguồn dữ liệu; sửa đề cương | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R2 | Đo lường | Xét nghiệm và đơn thuốc làm ngoài BVQY175 không có trong eHospital | Cao (máy ước — chủ nhiệm chỉnh) | Trung bình | Ghi riêng kết quả và thuốc ngoài viện nếu bệnh án có ghi; phân tích độ nhạy | Báo cáo như hạn chế, trình bày khoảng ước lượng | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R3 | Đo lường | Tên xét nghiệm albumin niệu trên eHospital không thống nhất (UACR, microalbumin niệu, que nhúng) | Cao (máy ước — chủ nhiệm chỉnh) | Cao | Quy tắc trích liệt kê trước các tên xét nghiệm tương ứng UACR và dạng khác | Trích lại các hồ sơ bị ảnh hưởng | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R4 | Chọn mẫu | Mã E11 ghi thiếu hoặc nhầm (dùng E14) | Trung bình (máy ước — chủ nhiệm chỉnh) | Trung bình | Đếm người chỉ có E14; phân tích độ nhạy E11 kèm thuốc hạ glucose | Nêu trong hạn chế | Nhà phương pháp/thống kê | Mở | [CẦN NGƯỜI RÀ] |
| R5 | Dữ liệu | Một người có nhiều mã hồ sơ trong eHospital | Trung bình (máy ước — chủ nhiệm chỉnh) | Trung bình | Gộp theo mã người bệnh khi lập khung mẫu; bảng nối mã giúp phát hiện trùng | Loại bản trùng, chuyển sang hồ sơ kế tiếp | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R6 | Bảo mật | Lộ thông tin định danh trong tệp trích xuất | Thấp (máy ước — chủ nhiệm chỉnh) | Cao | Phiếu chỉ mang mã nghiên cứu; bảng nối mã lưu riêng, mã hoá, chỉ chủ nhiệm giữ, huỷ sau khi khoá dữ liệu | Huỷ tệp lỗi, báo Hội đồng Đạo đức | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R7 | Tiến độ | Hội đồng xét duyệt chậm hơn dự kiến | Trung bình (máy ước — chủ nhiệm chỉnh) | Trung bình | Hỏi quy trình Hội đồng sớm (mục 1.10); nộp hồ sơ đủ ngay lần đầu | Dời mốc trích xuất; không trích trước khi được phê duyệt | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R8 | Tiến độ | Trích thủ công từng hồ sơ chậm hơn dự kiến (khối lượng theo cỡ mẫu G3) | Trung bình (máy ước — chủ nhiệm chỉnh) | Trung bình | Đo thời gian trích 10 hồ sơ đầu để ước tổng thời gian; cân nhắc khối lượng khi chốt cỡ mẫu G3 | Kéo dài giai đoạn trích; thêm người trích đã tập huấn cùng quy tắc | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |
| R9 | Đo lường | Đồng thuận giữa chủ nhiệm và người trích lại ở biến kết cục chính dưới 95% | Thấp (máy ước — chủ nhiệm chỉnh) | Cao | Hai người cùng tập trích trên 10 hồ sơ thử (không đưa vào mẫu) trước khi trích chính thức | Sửa quy tắc trích, trích lại các hồ sơ bị ảnh hưởng | Chủ nhiệm đề tài | Mở | [CẦN NGƯỜI RÀ] |

## Quy tắc cập nhật
- Rà sau mỗi cổng và khi có protocol amendment.
- Ghi mọi thay đổi vào `study_meta.json → gate_params.G1.risk_register` (giữ dòng cũ, cập nhật trạng thái, ngày rà,
  nguyên nhân và CAPA) rồi chạy lại G1 — tệp .md này được SINH LẠI, sửa tay sẽ bị ghi đè (bản sửa tay được sao lưu).

> Cần bác sĩ kiểm chứng.
