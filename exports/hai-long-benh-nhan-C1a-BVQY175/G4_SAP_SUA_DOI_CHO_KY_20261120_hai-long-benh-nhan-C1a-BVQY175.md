# C1a — Các mục sửa đổi kế hoạch phân tích thống kê chờ thống kê viên ký (20/11/2026)

**Đề tài:** `hai-long-benh-nhan-C1a-BVQY175` · **SAP hiện hành:** `G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md`
(phiên bản 1.5, đã ký khoá ngày 19/11/2026).

Đo lại chi tiết cỡ mẫu, chọn mẫu và biến số ngày 20/11/2026 (tính lại độc lập 56 con số của đề cương nộp: 52 khớp, 4 lệch
làm tròn hoặc diễn đạt). Chủ nhiệm đã quyết các điểm 1–3 ngày 20/11/2026 và điểm 4 ngày 21/11/2026. Đề cương nộp đã sửa theo quyết định. SAP
đã khoá nên CHƯA sửa; thống kê viên đưa các mục này vào lần sửa đổi SAP kế tiếp theo thủ tục ở Phụ lục A của đề cương:
ghi lý do, ngày, người phê duyệt, ký trước khi tiếp cận số liệu mẫu chính.

| # | Mục SAP | Hiện ghi | Sửa thành | Căn cứ |
|---|---|---|---|---|
| 1 | §12, «Lực cho mục tiêu phụ» — độ nhạy CV 1,0 | OR nhỏ nhất phát hiện được 1.10–1.23 | 1.10–1.22 | Tính lại công thức Whitehead ở n hiệu dụng 850 ÷ 1,78 ≈ 478: cận trên 1,2248 (làm tròn 1,22); chiều giảm 0,82–0,91 đã khớp 1,22. Chủ nhiệm chọn «Sửa ở lần sửa SAP kế tiếp». |
| 2 | §5, biến điều chỉnh bắt buộc `suckhoe_tudanhgia` | Chưa nói đưa dạng số hay phân loại | Đưa vào mô hình dạng SỐ (thang 1–5, 1 tham số, giả định tuyến tính) | Chủ nhiệm chọn «Dạng số» 20/11/2026 (đặc tả G6 đề xuất cùng phương án). Đề cương 4.10 nay ghi «tự đánh giá sức khỏe (dạng số, thang 1–5)». |
| 3 | §5, biến điều chỉnh bắt buộc `ngay_trong_tuan` | Bộ biến có 7 mức (thứ Hai … Chủ nhật) | Mô hình dùng năm ngày làm việc (thứ Hai đến thứ Sáu, 4 tham số); mã 6–7 không phát sinh | Chủ nhiệm xác nhận Khoa C1a chỉ khám thứ Hai–thứ Sáu (20/11/2026). Đề cương 4.4.2 nay ghi 20 tầng (5 ngày × 4 khung giờ). |
| 4 | §2 «Kết cục phụ 2» (`SHLNBChung_TinhToan` — đối chiếu hội tụ với G1) và mục «Đặc tính đo lường của bộ câu hỏi trong mẫu» (thêm điểm 5) | «đối chiếu hội tụ với G1», không nêu giả thuyết | Giả thuyết định trước: điểm hài lòng tổng hợp tương quan thuận với G1, hệ số tương quan hạng Spearman ρ > 0,50; báo ρ kèm khoảng tin cậy 95% (thống kê viên ghi phương pháp ước lượng khoảng tin cậy có tính đến gom cụm theo bàn khám); giả thuyết không đạt thì vẫn báo đủ và bàn luận nguyên nhân | Chủ nhiệm chọn «Thêm giả thuyết» 21/11/2026 sau khi K17 báo thiếu COSMIN ConV3; ngưỡng > 0,50 theo Abma 2016 (PMID 27094345, đã đọc toàn văn); giả thuyết nêu trước theo COSMIN (Terwee 2007, PMID 17161752). Đề cương nộp đã sửa: mục 2.6.1.2 và điểm 5 của mục 2.6.1.3 |

Hệ quả đã kiểm: mô hình chính còn 19 tham số (trước đây đề cương ghi «khoảng 24»). Kết luận về hồi quy nhị phân thứ cấp
không đổi: 150 trường hợp chưa hài lòng chỉ đủ khoảng 15 tham số ở mức 10 biến cố mỗi tham số.

Đặc tả máy `G6_DAC_TA_SAP.json` chưa có người duyệt. Thống kê viên duyệt đặc tả sau khi ký SAP sửa đổi:
`python3 tools/chay_sap_g6.py kiem --study hai-long-benh-nhan-C1a-BVQY175`, rồi `duyet`.

Cần bác sĩ kiểm chứng.
