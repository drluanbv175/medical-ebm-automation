# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày sinh:** 2026-10-07 | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN

---

## PHẦN 1 — THÔNG SỐ ĐẦU VÀO

| Thông số | Giá trị | Nguồn |
|---|---|---|
| Khung cỡ mẫu | Ước lượng theo ĐỘ CHÍNH XÁC (không kiểm định giả thuyết) | ghim trong study_meta |
| Độ tin cậy | 95% (α = 0.05, hai phía) | Quy ước |
| Tỷ lệ không trả lời dự kiến | 15% | [CẦN BÁC SĨ XÁC NHẬN] |
| Tỷ lệ ước lượng p | 0.50 | ghim trong study_meta; nguồn: Quy ước thận trọng p = 0,50 — giá trị làm phương sai p(1-p) lớn nhất nên cho cỡ mẫu lớn nhất; dùng khi chưa có ước lượng tỷ lệ hài lòng tại chính Khoa C1a. Nguồn công thức: Lwanga SK, Lemeshow S. Sample size determination in health studies: a practical manual. WHO, 1991 (mục 4.4.1 đề cương) |
| Sai số tuyệt đối cho phép d | ±5% | ghim trong study_meta |

> **Thiết kế:** Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)  
> **Công thức:** Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05 Đã áp design effect cụm (DE=1+(m-1)×ICC=1.38, m=20, ICC=0.02): n 385→532 (~27 cụm).

---

## PHẦN 2 — KẾT QUẢ TÍNH TOÁN

| Chỉ số | Kết quả |
|---|---|
| N cần (chưa bù không trả lời) | **532** |
| N điều chỉnh (15%) | **626** |

**KẾT LUẬN:** Nghiên cứu cần tuyển **626 người tham gia**.

## PHẦN 2b — CỠ MẪU THỰC TẾ ĐÃ CHỐT (bác sĩ/chủ nhiệm quyết định)

**N thực tế đã chốt:** **1000** người tham gia — quyết định của bác sĩ/chủ nhiệm đề tài (vd theo khả năng thu thập/thời gian/hành chính), KHÔNG thay thế công thức tính N tối thiểu ở PHẦN 2, chỉ ghi SONG SONG để đối chiếu.

✅ **ĐẠT** — N chốt (1000) ≥ N tối thiểu tính theo thống kê (626), đủ hoặc dư lực thống kê/độ chính xác so với yêu cầu tối thiểu. Với N=1000 (giả định p=0.50, xấu nhất), sai số biên (margin of error) 95% CI ước lượng tỷ lệ ≈ ±3.1 điểm phần trăm — chặt hơn mức tối thiểu PHẦN 2 (N tối thiểu cho ±5%).

---

## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)

Bảng: tỷ lệ ước lượng p × sai số cho phép d → N tối thiểu (TRƯỚC khi bù 15% không trả lời)

| p ước lượng | d = ±2.5% | d = ±5% | d = ±10% |
|---|---|---|---|
| 0.10 | 554 | 139 | 35 |
| 0.30 | 1291 | 323 | 81 |
| 0.50 (cơ sở) | 1537 | 385 | 97 |

> *p = 0,50 cho N lớn nhất vì phương sai p(1−p) đạt cực đại tại đó; đây là lựa chọn thận trọng khi chưa biết tỷ lệ thật. Thu hẹp d làm N tăng nhanh theo bình phương.*


---

## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)

```
Cỡ mẫu được tính theo Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05 Đã áp design effect cụm (DE=1+(m-1)×ICC=1.38, m=20, ICC=0.02): n 385→532 (~27 cụm)..
Với độ tin cậy 95% (α = 0.05) và sai số tuyệt đối cho phép d = ±5%,
với tỷ lệ ước lượng p = 0.50 (Quy ước thận trọng p = 0,50 — giá trị làm phương sai p(1-p) lớn nhất nên cho cỡ mẫu lớn nhất; dùng khi chưa có ước lượng tỷ lệ hài lòng tại chính Khoa C1a. Nguồn công thức: Lwanga SK, Lemeshow S. Sample size determination in health studies: a practical manual. WHO, 1991 (mục 4.4.1 đề cương)),
cần 532 người.
Tính thêm 15% không trả lời dự kiến, cỡ mẫu cuối = 626 người.
N THỰC TẾ đã được bác sĩ/chủ nhiệm CHỐT = 1000 người (≥ N tối thiểu tính toán).
```

> Trình bày cỡ mẫu theo mục cỡ mẫu của **STROBE** khi đưa vào đề cương/bản thảo (vd CONSORT 2025 mục 16a, SPIRIT 2025 mục 19, STROBE mục 10, STARD 2015 mục 18, TRIPOD+AI mục 10 — tùy thiết kế).

---

## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3

- [ ] Bác sĩ xác nhận effect size (nguồn: PMID/DOI) [CẦN BÁC SĨ]
- [ ] Bác sĩ xác nhận tỷ lệ dropout [CẦN BÁC SĨ]
- [ ] Bác sĩ xác nhận tỷ lệ biến cố nền (với thiết kế sống còn) [CẦN BÁC SĨ]
- [ ] Cập nhật G3_checkpoint.json với N đã duyệt
- [ ] Copy khối cỡ mẫu vào đề cương (PHẦN 4)

---
*Cần bác sĩ kiểm chứng. Mọi số liệu cỡ mẫu phải được bác sĩ duyệt trước khi đưa vào đề cương chính thức.*