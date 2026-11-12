# Xác nhận G0 của chủ nhiệm — đề tài btm-dtd2-ngoai-tru-BVQY175 (mục 1.7 · G0-HUMAN-06/07)

> Claude chỉ chép lời chủ nhiệm — không tự đánh giá thay. Nơi chốt chính thức là
> `study_meta.json → gate_params.G0`; tệp này giữ nguyên văn để truy vết. Cần bác sĩ kiểm chứng.

- **Nội dung trình cho chủ nhiệm đọc (28/10/2026):** PICO trong `gate_params.G0`; 67 nguồn ở §3 của
  `G0_A1_PICO_FINER_btm-dtd2-ngoai-tru-BVQY175.md` (30 PMID nền PubMed, 23 PMID bổ sung, 14 DOI trong nước);
  kiểm rút bài 25/10/2026 cho 56 PMID, 14 DOI trong nước chưa kiểm; ba lưu ý: phụ 4 là phân tích thăm dò
  (không có H0/H1), phụ 3 dùng KDIGO 2022 trong khi tên đề tài ghi KDIGO 2024, sửa PICO sau khi chốt làm đổi dấu vân tay.
- **Câu mẫu Claude đề xuất:** «Tôi, vai trò chủ nhiệm đề tài, đã đọc danh sách PMID ở §3 của A1 và xác nhận
  chứng cứ; chốt PICO G0 theo dấu vân tay b9638397b7403e29.»
- **Nguyên văn trả lời của bác sĩ (28/10/2026, khoảng 11:25):** «Chốt theo câu mẫu»
- **Đã ghi vào `gate_params.G0`** (sao lưu trước khi ghi: `study_meta.bak-20261028-truoc-chot-g0.json`):
  `evidence_reviewed_confirmed = true` · `pico_confirmed = true` · `reviewed_by_role = "chủ nhiệm đề tài"` ·
  `reviewed_at = "2026-10-28T11:25:00+07:00"` · `dau_van_tay_chot = "b9638397b7403e29"`.
- **Cổng sau khi ghi:** `tools/g0_quality_gate.py` → `PASS_G0_CONFIRMED`, 8/8 tiêu chí người đạt.

## Chốt lại G0 sau khi sửa đoạn khả thi (28/10/2026, khoảng 15:29)

- **Lý do sửa:** chủ nhiệm quyết «Vì là hồi cứu nên dữ liệu tôi sẽ tự lấy trên phần mềm Ehospital» và chọn «Mở từng hồ sơ»
  ⇒ `finer_feasible` bỏ điều kiện «phòng CNTT xác nhận», thay bằng điều kiện chủ nhiệm tự trích trên eHospital và lập được
  danh sách khung mẫu (nội dung trong `DE-XUAT-SUA-G1-TU-TRICH_20261028.json`). Dấu vân tay G0 đổi b9638397b7403e29 → 858fd91d6edbd8eb.
- **Câu Claude đề xuất:** «Áp dụng cả hai và chốt lại G0 theo dấu vân tay 858fd91d6edbd8eb».
- **Nguyên văn trả lời của bác sĩ:** «Áp dụng + chốt G0»
- **Đã ghi** (sao lưu trước: `study_meta.bak-20261028-truoc-sua-tu-trich.json`): `finer_feasible` mới ·
  `reviewed_at = "2026-10-28T15:29:00+07:00"` · `dau_van_tay_chot = "858fd91d6edbd8eb"`; `pico_confirmed`,
  `evidence_reviewed_confirmed`, `reviewed_by_role = "chủ nhiệm đề tài"` giữ nguyên. Máy kiểm dấu vân tay sau khi áp đúng
  bằng dấu bác sĩ chốt rồi mới ghi.
- **Cổng sau khi ghi:** `tools/g0_quality_gate.py` → `PASS_G0_CONFIRMED`.
