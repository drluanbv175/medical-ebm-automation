# Quyết định bộ biến số của chủ nhiệm — đề tài btm-dtd2-ngoai-tru-BVQY175 (mục 2.7)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Tệp này giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

- **Nội dung trình cho chủ nhiệm (28/10/2026):** codebook `G3_BO_BIEN_SO_btm-dtd2-ngoai-tru-BVQY175` (bản .md, .docx,
  .xlsx), đã gửi vào khung chat. Codebook gồm 73 trường REDCap trong 5 biểu mẫu và 23 biến phái sinh; mục 10 nêu 9 điểm
  cần quyết.
- **Nguyên văn trả lời của bác sĩ (28/10/2026):** «Áp dụng B1–B9»
- **Nghĩa là áp dụng đúng phương án máy đề xuất cho cả 9 điểm:**

| Mã | Quyết định |
|---|---|
| B1 | Mỗi người ghi tối đa 6 kết quả creatinin và 4 kết quả UACR. Có nhiều hơn thì ghi kết quả đầu tiên năm 2026 và các kết quả gần nhất |
| B2 | Tăng huyết áp = có mã I10–I15 ở ít nhất một lượt khám năm 2026. Không dùng «đang dùng thuốc hạ áp» |
| B3 | «BTM đã được ghi nhận» = mã N18, E11.2, N08.3. Phân tích độ nhạy thêm N19, I12, I13, R80 |
| B4 | Bệnh tim mạch do xơ vữa và suy tim theo danh mục mã ở codebook (mục 8), gộp thành một biến `tim_mach` |
| B5 | Chỉ định ACEi/ARB dùng albumin niệu đã xác nhận (2 lần UACR từ 30 mg/g, cách nhau từ 90 ngày). Phân tích độ nhạy: chỉ cần một lần |
| B6 | Phòng khám theo dõi chính = phòng có nhiều lượt khám nhất; bằng nhau thì lấy phòng của lượt khám cuối |
| B7 | Tuổi dùng cho eGFR = tuổi tại lượt khám đầu năm 2026 |
| B8 | Ghi ngày lượt khám và ngày xét nghiệm; đổi thành «ngày thứ trong năm 2026» trước khi chia sẻ tệp phân tích |
| B9 | Mã thiếu cấp dự án: KGHS (hồ sơ không ghi), KDD (không đọc được hoặc mâu thuẫn) |

- **Máy đã làm sau quyết định:**
  - ghi quyết định vào codebook (đầu tệp và mục 10) và vào cột nguồn của `_ma-thieu-theo-bien.csv`;
  - `_bo-bien-rieng.csv` và `_bien-phai-sinh.csv` không đổi nội dung, vì đã dựng theo đúng phương án này;
  - kiểm lại: bộ nạp của G5 đọc được 73 trường, không có biến định danh.
- **Còn mở:** bảng ánh xạ tên xét nghiệm trên eHospital (codebook mục 7). Chủ nhiệm điền tên xét nghiệm, hai người duyệt
  trước khi trích. Việc này làm cùng quy trình trích ở mục 2.8.
- **Chưa làm:** đánh giá chéo bộ biến bằng một agent độc lập (nhiệm vụ G3-T2, G3-T3 của hội đồng cổng). Việc này tốn token
  nên chỉ chạy khi bác sĩ yêu cầu.
