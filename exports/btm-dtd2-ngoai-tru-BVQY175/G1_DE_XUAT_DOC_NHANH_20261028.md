# G1 — Bản đọc nhanh đề xuất thiết kế và kiểm soát sai lệch · btm-dtd2-ngoai-tru-BVQY175 (mục 2.1)

> ⚠ **ĐÃ LỖI THỜI (28/10/2026, sau khi bác sĩ quyết tự trích từng hồ sơ trên eHospital):** bản này còn ghi «lấy toàn bộ», «phòng CNTT trích xuất», 9 sai lệch. Đọc bản mới `G1_BAN_DOC_DE_CHOT_20261028.md`.

> Máy soạn ngày 28/10/2026 từ PICO đã chốt ở G0 (dấu vân tay b9638397b7403e29). **Chưa ghi gì vào `study_meta.json`.**
> Nội dung đầy đủ để chép: `DE-XUAT-GATE-PARAMS-G1_20261028.json`. Cần bác sĩ kiểm chứng.

## 1. Thiết kế

- **Cắt ngang mô tả có phân tích** trên dữ liệu HIS có sẵn (`cross_sectional`), cửa sổ hồi cứu 01/01–31/12/2026.
- Báo cáo theo **STROBE kèm RECORD** — phần mở rộng cho nghiên cứu dùng dữ liệu y tế thu thập thường quy
  (Benchimol 2015, PMID 26440803; đã kiểm trên PubMed, không bị rút bài).
- Phương án đã cân nhắc và loại:
  - đoàn hệ hồi cứu theo dõi kết cục thận: vượt nhu cầu câu hỏi;
  - cắt ngang thu mới bằng phỏng vấn/khám: tốn nguồn lực và không đo được việc xét nghiệm, kê đơn thực tế;
  - trích hồ sơ thủ công: giữ làm phương án dự phòng nếu HIS không xuất được dữ liệu.

## 2. Mục tiêu (gom từ 5 dòng kết cục của G0)

| Mục tiêu | Nội dung |
|---|---|
| MT1 | Thực trạng **phát hiện** bệnh thận mạn (BTM): tỷ lệ xét nghiệm đủ UACR + creatinin (**kết cục chính**), tỷ lệ BTM theo KDIGO 2024, tỷ lệ BTM chưa được ghi nhận chẩn đoán |
| MT2 | Thực trạng **điều trị bảo vệ thận** (ACEi/ARB, SGLT2i) ở người đủ chỉ định theo KDIGO 2022 |
| MT3 | **Yếu tố liên quan** với việc không được xét nghiệm đủ — phân tích thăm dò, Poisson phương sai vững, báo cáo PR |

**Kết cục chính (biến XN_DU):**
- Bằng 1 khi trong năm 2026 có ít nhất một UACR **dạng tỷ số** và ít nhất một creatinin huyết thanh.
- Nồng độ microalbumin niệu đơn thuần và que nhúng không được tính ở phân tích chính, chỉ dùng trong phân tích độ nhạy.
- Xét nghiệm làm ngoài viện không có trong HIS: tính là 0 ở phân tích chính, đánh giá bằng đối chiếu hồ sơ thủ công một mẫu ngẫu nhiên.

**Bệnh thận mạn:**
- Hai lần đo bất thường cách nhau từ 90 ngày; người chỉ có một lần đo xếp nhóm «nghi bệnh thận mạn», báo cáo riêng.
- eGFR tính bằng phương trình CKD-EPI 2021 không hệ số chủng tộc (PMID 34554658; đã kiểm, không bị rút bài).

## 3. Quần thể và cách chọn

- **Chọn vào:**
  - từ 18 tuổi;
  - có mã E11 ở ít nhất một lượt khám ngoại trú tại Khoa Khám bệnh;
  - có từ 2 lượt khám trong năm 2026.
- **Loại trừ:**
  - lọc máu hoặc ghép thận (ví dụ mã Z49, Z99.2, Z94.0 — danh sách đầy đủ chốt cùng codebook);
  - có thai (mã chương O, Z33);
  - có mã E10, E12, E13;
  - người chỉ có mã E14 không vào mẫu nhưng được đếm trong sơ đồ chọn.
- **Chọn mẫu (đề xuất):** lấy **toàn bộ** người đủ tiêu chuẩn trong HIS. Cỡ mẫu G3 dùng để kiểm xem số người này có đủ độ chính xác không.
- **Dữ liệu:**
  - phòng CNTT trích xuất và gộp các mã hồ sơ của cùng một người, rồi mới gán mã ẩn danh;
  - nhóm nghiên cứu chỉ nhận tệp không có trường định danh;
  - hai người đối chiếu độc lập hồ sơ của một mẫu ngẫu nhiên.

## 4. Kiểm soát sai lệch riêng của đề tài (9 dòng)

| Sai lệch | Chiều lệch | Biện pháp | Trạng thái |
|---|---|---|---|
| Chọn do tiêu chí từ 2 lượt khám | Ước lượng **cao** tỷ lệ xét nghiệm | Sơ đồ chọn đếm người chỉ 1 lượt khám, so sánh đặc điểm với mẫu | định lượng + hạn chế mở |
| Phân loại quần thể do mã ICD-10 | Không xác định trước | Loại E10/E12/E13, đếm E14; phân tích độ nhạy: E11 kèm đơn thuốc hạ glucose | khống chế |
| Xét nghiệm làm ngoài viện | Ước lượng **thấp** | Đối chiếu thủ công mẫu ngẫu nhiên, phân tích độ nhạy | định lượng + hạn chế mở |
| UACR lẫn với microalbumin/que nhúng | Đếm thiếu hoặc thừa | Bảng ánh xạ mã xét nghiệm do hai người duyệt | khống chế |
| BTM chỉ có 1 lần đo | Ước lượng **cao** tỷ lệ BTM | Xác nhận bằng 2 lần đo từ 90 ngày; nhóm nghi BTM báo riêng | khống chế |
| Thuốc kê hoặc mua ngoài viện | Ước lượng **thấp** tỷ lệ điều trị | Đối chiếu bệnh án mẫu kiểm chứng; nêu hạn chế | định lượng + hạn chế mở |
| Thời gian quan sát không đều | Ước lượng **thấp** | Phân tích độ nhạy: chỉ người có lượt khám đầu trước 01/07/2026 | định lượng |
| Nhiễu và cụm ở MT3 | Không xác định trước | Mô hình đa biến với biến đã chốt; sai số chuẩn vững; không diễn giải nhân quả | khống chế một phần |
| Báo cáo có chọn lọc | — | Khoá SAP ở G4 trước khi nhận dữ liệu; báo cáo theo STROBE + RECORD | khống chế |

Ngoài ra đề xuất có 7 rủi ro (R1–R7) cho sổ rủi ro A13b và các yếu tố quyết định chất lượng (CTQ). Kinh phí để trống cho mục 2.4.

## 5. Điều cần chủ nhiệm quyết

| Mã | Câu hỏi | Máy đề xuất | Lựa chọn khác |
|---|---|---|---|
| D1 | Thiết kế | Cắt ngang, STROBE + RECORD | — |
| D2 | Số mục tiêu | 3 mục tiêu như bảng trên | Giữ 5 mục tiêu tách như G0 |
| D3 | Chọn mẫu (mục 2.5) | Lấy toàn bộ | Ngẫu nhiên đơn, cỡ mẫu theo G3 |
| D4 | Tính gì là UACR (mục 2.2) | Chỉ dạng tỷ số; dạng khác đưa vào phân tích độ nhạy | Gộp mọi dạng albumin niệu |
| D5 | Xác nhận tính mạn của BTM (mục 2.2) | Chỉ dữ liệu năm 2026 như G0 | Tra lùi năm 2025 để xác nhận (đổi phạm vi trích xuất và hồ sơ đạo đức) |
| D6 | Ngưỡng đồng thuận khi đối chiếu thủ công | Từ 95% | Chủ nhiệm ấn định |
| D7 | Vai ghi khi chốt G1 | «chủ nhiệm» — cổng G1 chưa nhận chuỗi «chủ nhiệm đề tài» | «PI» |

## 6. Sau khi chủ nhiệm duyệt

1. Bác sĩ nói «áp dụng đề xuất G1» (kèm phần sửa nếu có). Máy sao lưu `study_meta.json`, chép nội dung vào `gate_params.G1`, rồi chạy lại G1.
2. Kết quả đo thử trên bản sao đã áp đề xuất:
   - 14/14 tiêu chí tự động đạt;
   - tiêu chí người G1-HUMAN-02/03/04/05 đạt;
   - còn lại 4 tiêu chí xác nhận của chủ nhiệm (thiết kế, đề cương lõi + sai lệch + khả thi, nguồn chứng cứ, vai/thời điểm/dấu vân tay) — mục 2.3.
3. Dấu vân tay G1 sẽ tính lại sau khi áp đề xuất. Mọi chỉnh sửa nội dung về sau đều làm đổi dấu này.
