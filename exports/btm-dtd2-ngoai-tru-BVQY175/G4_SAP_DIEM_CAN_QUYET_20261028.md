# SAP (mục 3.4) — điểm cần chủ nhiệm và thống kê viên quyết · btm-dtd2-ngoai-tru-BVQY175

> Máy soạn ngày 28/10/2026, đi kèm `G4_A5_SAP_FINAL_btm-dtd2-ngoai-tru-BVQY175` (bản dự thảo 1.0). Cần bác sĩ kiểm chứng.

## Tình trạng

- Bản SAP do `run_g4_auto` sinh từ khuôn mẫu chung **không dùng được**: mô hình chính là hồi quy logistic hoặc tuyến tính, kết cục chính và cách xử lý dữ liệu thiếu đều để trống. Bản này đã được lưu lại (`.bak-20261028-khuon-may`).
- Máy viết lại toàn bộ 12 mục cho riêng đề tài, từ G1, G3, codebook và quy trình trích đã chốt. Giữ nguyên khung mà cổng G4 kiểm, và các con số ký ở §1, §12, chứng chỉ khoá khớp G3 (N = 385, p = 0,5, d = 0,05, α = 0,05).
- Cổng G4 đo sống: **READY_FOR_SIGNATURE**, đạt 16/16 tiêu chí tự động. 8 tiêu chí người là việc ký khoá SAP ở mục 4.6, sau khi Hội đồng Đạo đức duyệt.
- Tài liệu phương pháp trích trong SAP đã xác minh qua PubMed/Crossref và kiểm rút bài (không bài nào bị rút):
  - Zou 2004 — PMID 15033648;
  - Barros và Hirakata 2003 — PMID 14567763;
  - Sterne 2009 — PMID 19564179;
  - White 2011 — PMID 21225900;
  - Ogundimu 2016 — PMID 26964707;
  - Brown, Cai, DasGupta 2001 — DOI 10.1214/ss/1009213286.

## Nội dung chính của SAP

| Mục | Nội dung |
|---|---|
| Kết cục chính | Tỷ lệ `xn_du` kèm KTC 95% Wilson, không kiểm định, không hiệu chỉnh quần thể hữu hạn (giống G3) |
| Kết cục phụ 1–3 | Tỷ lệ + KTC 95% trên đúng quần thể con; bảng chéo G × A theo KDIGO 2024 |
| MT3 | Poisson phương sai vững, báo PR thô và PR hiệu chỉnh, 12 biến giải thích G0 đưa vào toàn bộ, không stepwise |
| Dữ liệu thiếu | Kết cục không thể thiếu. Biến giải thích thiếu ⇒ gán đa trị m = 20 (MAR), complete case song song |
| Nhóm nhỏ | 3 nhóm định trước cho kết cục chính, chỉ mô tả |
| Đa so sánh | 1 kết cục chính, ước lượng; kết cục phụ và MT3 không hiệu chỉnh, nói rõ trong bài |
| Độ nhạy | 9 phân tích ĐN1–ĐN9, gồm mọi phân tích độ nhạy G1 đã cam kết |
| Phần mềm | Python 3.14.6, statsmodels 0.14.6; seed 20261028 |

## Điểm cần quyết

| Mã | Câu hỏi | Máy đề xuất (đã viết vào SAP) | Lựa chọn khác |
|---|---|---|---|
| S1 | KTC 95% của tỷ lệ | Wilson; không hiệu chỉnh quần thể hữu hạn ở phân tích chính | Clopper–Pearson (chính xác, rộng hơn) |
| S2 | HbA1c trong MT3 | 3 mức: không làm HbA1c / < 7% / ≥ 7%. Thiếu do không được xét nghiệm là thiếu có cấu trúc, không nên gán | HbA1c liên tục kèm biến chỉ báo; hoặc 4 mức thêm ngưỡng 9% (thêm 1 tham số) |
| S3 | Dữ liệu thiếu ở biến giải thích | Gán đa trị m = 20 là phân tích chính của MT3; complete case là độ nhạy | Complete case là chính nếu mọi biến thiếu dưới 5% |
| S4 | Khi số biến cố trên mỗi tham số (EPV) dưới 10 | Mô hình có 16 tham số; giảm theo thứ tự định trước: (1) nhóm đối tượng còn 2 mức; (2) phòng khám còn 2 mức; (3) bỏ số nhóm thuốc, giữ insulin | Giữ mô hình đầy đủ và nêu hạn chế |
| S5 | Nhóm nhỏ của kết cục chính | Phòng khám theo dõi chính; nhóm đối tượng; tuổi < 65 / ≥ 65 — chỉ mô tả | Bỏ phân tích nhóm nhỏ; hoặc thêm nhóm khác (ghi trước khi xem dữ liệu) |
| S6 | Độ nhạy ĐN4 «E11 kèm đơn thuốc hạ glucose» | G1 cam kết «có ít nhất một đơn thuốc hạ glucose **trong cửa sổ**», nhưng codebook chỉ ghi đơn ở lượt khám cuối. Đề xuất **thêm 1 trường** vào codebook: `don_ha_glucose_nam` = «Có ít nhất một đơn thuốc hạ glucose ở bất kỳ lượt khám nào năm 2026» (có/không). Việc này sửa nhỏ mục 2.7: 73 thành 74 trường; phiếu thu thập và SOP dựng lại | Dùng gần đúng «có thuốc hạ glucose trong đơn lượt khám cuối», không sửa codebook, nêu rõ là khác G1 |
| S7 | Dạng biến liên tục trong MT3 | Tuyến tính: tuổi mỗi 10 năm, thời gian mắc mỗi 5 năm, BMI mỗi 5 kg/m², số lượt khám mỗi lượt; chia nhóm chỉ ở độ nhạy ĐN9 nếu lệch | Chia nhóm ngay ở mô hình chính (thêm tham số) |

## Lưu ý cho bước phân tích (G6), không cần quyết bây giờ

`tools/run_stats_analysis.py` hiện có tỷ lệ kèm KTC Wilson và gán đa trị, nhưng **chưa có** hồi quy Poisson phương sai vững (công cụ chỉ chạy logistic). Trước G6 (năm 2027) cần thêm nhánh này hoặc một script phân tích riêng có kiểm thử. Việc này không chặn G4.

## Sau khi bác sĩ trả lời

- «Áp dụng S1–S7» (kèm phần sửa nếu có) ⇒ máy:
  - ghi quyết định vào SAP, và sửa ĐN4 theo S6;
  - nếu chọn thêm trường ở S6: thêm `don_ha_glucose_nam` vào codebook, dựng lại phiếu thu thập và bản Excel, kiểm lại bằng bộ nạp G5;
  - chấm lại G4, rồi đánh dấu mục 3.4 và 3.5 trong sổ tiến độ.
- Ký khoá SAP (`approve_gate.py --gate G4`) là việc của chủ nhiệm hoặc thống kê viên, làm ở mục 4.6 sau khi ký G2. Máy không ký thay.
