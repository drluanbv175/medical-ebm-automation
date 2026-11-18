# Chốt lại G1 của chủ nhiệm — đề tài btm-dtd2-ngoai-tru-BVQY175 (G1-HUMAN-08)

> Claude chỉ chép lời chủ nhiệm, không đánh giá thay. Nơi chốt chính thức là `study_meta.json → gate_params.G1`;
> tệp này giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

- **Vì sao phải chốt lại:** chủ nhiệm đồng ý bỏ câu «hiệu chỉnh quần thể hữu hạn theo kích thước khung mẫu» ở phương
  pháp chọn mẫu (`G3_BO_BIEN_SO_QUYET_DINH_20261118.md`, nguyên văn «đồng ý bỏ Hiệu chỉnh quần thể hữu hạn; ĐN4 (B10)
  cho a»). Sửa `gate_params.G1.recruitment_strategy` làm đổi dấu vân tay, nên xác nhận «Chốt G1» ngày 28/10/2026 (dấu
  91fc5cdaaa5a689c) hết hiệu lực.
- **Nội dung thay đổi so với bản đã chốt 28/10:** máy so từng khoá của `gate_params.G1` — chỉ khoá
  `recruitment_strategy` khác, đúng một cụm:
  - cũ: «cho tới khi đủ cỡ mẫu tính ở G3 (hiệu chỉnh quần thể hữu hạn theo kích thước khung mẫu)»;
  - mới: «cho tới khi đủ cỡ mẫu tính ở G3 (385 hồ sơ đủ tiêu chuẩn; không hiệu chỉnh quần thể hữu hạn)».
- **Nguyên văn trả lời của bác sĩ (18/11/2026):** «Chốt lại G1»
- **Đã ghi vào `gate_params.G1`:**
  - `reviewed_by_role = "chủ nhiệm"` (giữ nguyên);
  - `reviewed_at = "2026-11-18T07:14:52+07:00"`;
  - `dau_van_tay_chot = "c9449332e89c9572"` (máy đã kiểm khớp dấu vân tay đang sống trước khi ghi).
  Các cờ `design_confirmed`, `protocol_core_confirmed`, `bias_controls_confirmed`, `feasibility_confirmed`,
  `evidence_review_confirmed` giữ nguyên `true`.
- **Lưu ý:** sửa bất kỳ nội dung nào trong `gate_params.G1` sẽ làm đổi dấu vân tay, và xác nhận này hết hiệu lực.
