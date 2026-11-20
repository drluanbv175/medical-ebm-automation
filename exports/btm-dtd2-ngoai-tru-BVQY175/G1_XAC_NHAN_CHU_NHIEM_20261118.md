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

## Chốt lại lần 2 (18/11/2026) — thêm mục tiêu chung (B5)

- **Câu hỏi đã trình:** B5 của phiếu đề xuất sau diễn tập — mục tiêu chung (`gate_params.G1.aim`). Mô tả phương án A ghi
  rõ: ghi câu vào G1.aim và đề cương 2.1, **chốt lại G1**.
- **Lựa chọn của bác sĩ (nguyên văn phương án đã chọn):** «A: dùng câu dựng từ tên đề tài».
- **Nội dung thay đổi so với lần chốt trước (dấu c9449332e89c9572):** máy so từng khoá — chỉ thêm khoá `aim` = «Đánh giá
  thực trạng phát hiện bệnh thận mạn và điều trị bảo vệ thận ở người bệnh đái tháo đường típ 2 điều trị ngoại trú tại
  Bệnh viện Quân y 175 năm 2026 theo KDIGO 2024 và ADA 2026.»
- **Đã ghi vào `gate_params.G1`:** `reviewed_at = "2026-11-18T07:28:26+07:00"`; `dau_van_tay_chot = "35669ac14fd0ecd1"` (khớp vân tay sống);
  `reviewed_by_role` và các cờ confirmed giữ nguyên.

## Chốt lại lần 3 (18/11/2026) — tên đề tài và quyết định không đăng ký công khai

- **Vì sao:** hai quyết định của chủ nhiệm cùng ngày làm đổi `gate_params.G1`:
  - tên đề tài nêu đủ ba hướng dẫn (xem `G0_XAC_NHAN_CHU_NHIEM_20261118.md`). Mục tiêu chung `aim` dựng từ tên đề tài
    (quyết định B5), nên đổi theo thành «… năm 2026 theo KDIGO 2022, KDIGO 2024 và ADA 2026.»;
  - không đăng ký công khai đề cương (nguyên văn bác sĩ: «Không đăng ký công khai»). Biện pháp của sai lệch «báo cáo và
    phân tích có chọn lọc» bỏ cụm «cân nhắc đăng ký công khai đề cương (quyết ở G2)», thay bằng «không đăng ký công khai
    đề cương».
- **Nội dung thay đổi so với lần chốt trước (dấu 35669ac14fd0ecd1):** chỉ hai khoá `aim` và
  `bias_controls[«Sai lệch báo cáo và phân tích có chọn lọc»].bien_phap`, đúng hai cụm nêu trên.
- **Đã ghi vào `gate_params.G1`:** `reviewed_at = "2026-11-18T11:40:57+07:00"`; `dau_van_tay_chot = "c504c4e6ea68bd69"`
  (khớp vân tay sống); `reviewed_by_role` và các cờ confirmed giữ nguyên.

## Chốt lại lần 4 (20/11/2026) — quyết định G1 ngày 20/11 (thu hẹp mục tiêu, kiểm định phiếu trích, lùi tiến độ)

- **Vì sao:** các quyết định của chủ nhiệm ngày 20/11/2026 (DP-G1-1 «Thu hẹp mục tiêu»; G1-T4 «Đưa vào đề cương»; Q1 «Chạy
  xong rồi mới nộp» + tiến độ «Lùi cả chuỗi»; Q5–Q7) làm đổi `gate_params.G1` (PR #342 của repo y khoa).
- **Nội dung thay đổi so với lần chốt trước (dấu c504c4e6ea68bd69):** máy so từng khoá — 9 khoá:
  `bias_controls`, `budget`, `critical_to_quality`, `data_collection_method`, `monitoring_plan`, `objectives`, `study_period`, `study_schema_timeline`, `team_roles`. Chi tiết từng cụm ở PR #342 và
  `G1_DE_XUAT_KIEM_DINH_PHIEU_TRICH_20261119_btm-dtd2-ngoai-tru-BVQY175.md`.
- **Câu hỏi đã trình:** «Bác sĩ chốt lại G1 với dấu vân tay aa132ca9bc229315?» (phiếu hỏi trong phiên Claude, 20/11/2026).
- **Lựa chọn của bác sĩ (nguyên văn):** «Chốt lại G1»
- **Đã ghi vào `gate_params.G1`:** `reviewed_at = "2026-11-20T06:35:38+07:00"`; `dau_van_tay_chot = "aa132ca9bc229315"` (máy đã kiểm khớp
  dấu vân tay đang sống trước khi ghi); `reviewed_by_role` và các cờ confirmed giữ nguyên.
