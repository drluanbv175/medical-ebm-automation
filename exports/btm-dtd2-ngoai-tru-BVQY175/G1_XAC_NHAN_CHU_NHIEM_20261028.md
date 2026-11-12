# Xác nhận G1 của chủ nhiệm — đề tài btm-dtd2-ngoai-tru-BVQY175 (mục 2.3 · G1-HUMAN-01/06/07/08)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Nơi chốt chính thức là `study_meta.json → gate_params.G1`;
> tệp này giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

- **Nội dung trình cho chủ nhiệm đọc (28/10/2026):** các tệp sau, gửi vào khung chat:
  - `G1_BAN_DOC_DE_CHOT_20261028.md` — chép nguyên văn `gate_params.G1`;
  - `G1_A2_PROTOCOL_DESIGN_…` (.md và .docx);
  - `G1_A13_IMPLEMENTATION_PLAN_…`;
  - `G1_A13b_RISK_REGISTER_…`;
  - mục lục đề cương nộp dự kiến.
- **Nội dung được chốt:**
  - thiết kế cắt ngang (`cross_sectional`), báo cáo theo STROBE + RECORD;
  - 3 mục tiêu; kết cục chính XN_DU (UACR dạng tỷ số + creatinin trong năm 2026);
  - chọn mẫu ngẫu nhiên đơn theo người bệnh, từ danh sách lấy trên eHospital;
  - chủ nhiệm mở từng hồ sơ để trích, người thứ hai trích lại 10%;
  - 11 sai lệch, 9 rủi ro, kinh phí tự túc.
- **Câu mẫu Claude đề xuất:** «Tôi, vai trò chủ nhiệm, đã rà đề cương lõi G1 (thiết kế cắt ngang, chọn mẫu ngẫu nhiên
  từ eHospital, bảng 11 sai lệch, tính khả thi) và nội dung nguồn, khoảng trống; xác nhận thiết kế và chốt G1 theo dấu
  vân tay 91fc5cdaaa5a689c.»
- **Nguyên văn trả lời của bác sĩ (28/10/2026, khoảng 15:54):** «Chốt G1»
- **Đã ghi vào `gate_params.G1`** (sao lưu trước khi ghi: `study_meta.bak-20261028-truoc-chot-g1.json`):
  - `design_confirmed`, `protocol_core_confirmed`, `bias_controls_confirmed`, `feasibility_confirmed`, `evidence_review_confirmed` đều = `true`;
  - `reviewed_by_role = "chủ nhiệm"`;
  - `reviewed_at = "2026-10-28T15:54:00+07:00"`;
  - `dau_van_tay_chot = "91fc5cdaaa5a689c"`.
  
  Máy đã kiểm dấu vân tay đang sống khớp câu mẫu trước khi ghi.
- **Cổng sau khi ghi:** `tools/g1_quality_gate.py --ghi` → `PASS_G1_CONFIRMED`, 14/14 tiêu chí tự động, 8/8 tiêu chí người.
  G0 vẫn ở `PASS_G0_CONFIRMED` (dấu 858fd91d6edbd8eb).
- **Lưu ý:** sửa bất kỳ nội dung nào trong `gate_params.G1` (kể cả kinh phí, sổ rủi ro) sẽ làm đổi dấu vân tay, và xác nhận
  này hết hiệu lực.
