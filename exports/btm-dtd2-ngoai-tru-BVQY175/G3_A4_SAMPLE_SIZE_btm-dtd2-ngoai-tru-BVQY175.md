# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)
**Đề tài:** Thực trạng phát hiện và điều trị bảo vệ thận ở bệnh nhân đái tháo đường típ 2 điều trị ngoại trú tại Bệnh viện Quân y 175 theo KDIGO 2024 và ADA 2026  
**Mã:** btm-dtd2-ngoai-tru-BVQY175 | **Ngày sinh:** 2026-10-28 | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN

---

## PHẦN 1 — THÔNG SỐ ĐẦU VÀO

| Thông số | Giá trị | Nguồn |
|---|---|---|
| Khung cỡ mẫu | Ước lượng theo ĐỘ CHÍNH XÁC (không kiểm định giả thuyết) | đặc tả thiết kế G1 (g1_khoa) |
| Độ tin cậy | 95% (α = 0.05, hai phía) | Quy ước |
| Tỷ lệ không trả lời dự kiến | 0% | [CẦN BÁC SĨ XÁC NHẬN] |
| Tỷ lệ ước lượng p | 0.50 | ghim trong study_meta; nguồn: Chủ nhiệm chọn p = 50% ngày 28/10/2026, nguyên văn «p 50%, d 5%» (mục 2.5): giả định thận trọng nhất — tích p(1−p) lớn nhất nên cho cỡ mẫu lớn nhất khi chưa biết tỷ lệ thật tại BVQY175. Y văn đã trình để tham khảo: PMID 38922613 (24,9% làm đủ UACR và creatinin), PMID 33722396 (43,3% có làm UACR). |
| Sai số tuyệt đối cho phép d | ±5% | ghim trong study_meta |

> **Thiết kế:** Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)  
> **Công thức:** Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05

---

## PHẦN 2 — KẾT QUẢ TÍNH TOÁN

| Chỉ số | Kết quả |
|---|---|
| N cần (chưa bù không trả lời) | **385** |
| N điều chỉnh (0%) | **385** |

**KẾT LUẬN:** Nghiên cứu cần tuyển **385 người tham gia**.

---

## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)

Bảng: tỷ lệ ước lượng p × sai số cho phép d → N tối thiểu (TRƯỚC khi bù 0% không trả lời)

| p ước lượng | d = ±2.5% | d = ±5% | d = ±10% |
|---|---|---|---|
| 0.10 | 554 | 139 | 35 |
| 0.30 | 1291 | 323 | 81 |
| 0.50 (cơ sở) | 1537 | 385 | 97 |

> *p = 0,50 cho N lớn nhất vì phương sai p(1−p) đạt cực đại tại đó; đây là lựa chọn thận trọng khi chưa biết tỷ lệ thật. Thu hẹp d làm N tăng nhanh theo bình phương.*


---

## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)

```
Cỡ mẫu được tính theo Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05.
Với độ tin cậy 95% (α = 0.05) và sai số tuyệt đối cho phép d = ±5%,
với tỷ lệ ước lượng p = 0.50 (Chủ nhiệm chọn p = 50% ngày 28/10/2026, nguyên văn «p 50%, d 5%» (mục 2.5): giả định thận trọng nhất — tích p(1−p) lớn nhất nên cho cỡ mẫu lớn nhất khi chưa biết tỷ lệ thật tại BVQY175. Y văn đã trình để tham khảo: PMID 38922613 (24,9% làm đủ UACR và creatinin), PMID 33722396 (43,3% có làm UACR).),
cần 385 người.
Tính thêm 0% không trả lời dự kiến, cỡ mẫu cuối = 385 người.
```

> Trình bày cỡ mẫu theo mục cỡ mẫu của **STROBE** khi đưa vào đề cương/bản thảo (vd CONSORT 2025 mục 16a, SPIRIT 2025 mục 19, STROBE mục 10, STARD 2015 mục 18, TRIPOD+AI mục 10 — tùy thiết kế).

---

## PHẦN 5 — TIÊU CHÍ QUA CỔNG G3

- [ ] Bác sĩ xác nhận tỷ lệ dự kiến p và sai số cho phép d (nguồn: PMID/DOI hoặc pilot) [CẦN BÁC SĨ]
- [ ] Bác sĩ xác nhận tỷ lệ dropout / không trả lời [CẦN BÁC SĨ]

Máy tự làm, không phải ô việc của người: khi thống kê viên chốt G3, `G3_checkpoint.json` ghi N đã duyệt (`confirmed_n`); khối cỡ mẫu ở PHẦN 4 dùng để dán vào đề cương.

---
*Cần bác sĩ kiểm chứng. Mọi số liệu cỡ mẫu phải được bác sĩ duyệt trước khi đưa vào đề cương chính thức.*