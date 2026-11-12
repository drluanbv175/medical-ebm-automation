# Xác nhận G3 của chủ nhiệm — đề tài btm-dtd2-ngoai-tru-BVQY175 (mục 2.6 · G3-HUMAN-01/02/03/05/06)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Nơi chốt chính thức là `study_meta.json → gate_params.G3`;
> tệp này giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

- **Lựa chọn tham số của chủ nhiệm (mục 2.5, 28/10/2026):** «p 50%, d 5%».
- **Nội dung trình cho chủ nhiệm đọc:** kế hoạch cỡ mẫu `G3_A4_SAMPLE_SIZE_btm-dtd2-ngoai-tru-BVQY175` (bản .md và .docx),
  đã gửi vào khung chat.
- **Nội dung được chốt:**
  - phép tính: ước lượng một tỷ lệ theo độ chính xác (`descriptive_precision`), công thức Cochran
    n = 1,96²·p(1−p)/d²;
  - p = 0,5 (giả định thận trọng nhất), d = 0,05, α = 0,05;
  - y văn tham khảo: PMID 38922613 (24,9%), PMID 33722396 (43,3%);
  - không cộng hồ sơ dự phòng: hồ sơ không đủ tiêu chuẩn được thay bằng hồ sơ kế tiếp trong danh sách ngẫu nhiên;
  - chưa hiệu chỉnh quần thể hữu hạn (chưa có số người trong khung mẫu);
  - **N = 385** người bệnh đưa vào phân tích, tính cho kết cục chính XN_DU.
- **Câu mẫu Claude đề xuất:** «Tôi, vai trò chủ nhiệm đề tài, đã rà bảng tham số A4 (p 50%, d 5%, α 0,05, không bù vì
  thay hồ sơ kế tiếp), xác nhận phép tính ước lượng tỷ lệ theo độ chính xác, cỡ mẫu 385 khả thi trong thời gian thu thập;
  chốt G3 theo dấu vân tay e86410f1846a5b43.»
- **Nguyên văn trả lời của bác sĩ (28/10/2026, khoảng 17:10):** «Chốt G3 với 385»
- **Đã ghi vào `gate_params.G3`** (sao lưu trước khi ghi: `study_meta.bak-20261028-truoc-chot-g3.json`):
  - `effect_source_confirmed`, `assumptions_confirmed`, `hypothesis_confirmed`, `recruitment_feasibility_confirmed`
    đều = `true`;
  - `reviewed_by_role = "chủ nhiệm đề tài"`;
  - `reviewed_at = "2026-10-28T17:10:00+07:00"`;
  - `dau_van_tay_chot = "e86410f1846a5b43"`;
  - ghi chú nguồn của tỷ lệ bù (`dropout_source`) đổi từ «chờ xác nhận» thành «chủ nhiệm xác nhận khi chốt G3».

  Máy đã kiểm dấu vân tay đang sống khớp câu mẫu trước khi ghi. Không ghi `confirmed_n`: N do chủ nhiệm chốt trùng N
  tính được (385), và các bước sau (SAP G4, kiểm nhất quán, đề cương nộp) tự lấy N này.
- **Cổng sau khi ghi:** `tools/g3_quality_gate.py` → `PASS_G3_CONFIRMED`, 19/19 tiêu chí tự động, 7/7 tiêu chí người.
  G0 vẫn `PASS_G0_CONFIRMED`, G1 vẫn `PASS_G1_CONFIRMED`.
- **Lưu ý:**
  - đổi p, d, tỷ lệ bù, hoặc thêm số người trong khung mẫu sẽ làm đổi dấu vân tay, và xác nhận này hết hiệu lực;
  - khối lượng trích: 385 hồ sơ đưa vào phân tích, cộng các hồ sơ bị loại, cộng khoảng 39 hồ sơ người thứ hai trích lại
    (10%). Sổ rủi ro R8 đã có biện pháp: đo thời gian trích 10 hồ sơ đầu.
