# A4 — KẾ HOẠCH CỠ MẪU (DRAFT)
**Đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày sinh:** 2026-10-17 | **Trạng thái:** DRAFT — CHỜ BÁC SĨ XÁC NHẬN

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
> **Công thức:** Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05 Đã áp design effect cụm (DE=1+((CV²+1)m-1)×ICC, CV=1 — Eldridge 2006=1.78, m=20, ICC=0.02): n 385→686 (~35 cụm).

---

## PHẦN 2 — KẾT QUẢ TÍNH TOÁN

| Chỉ số | Kết quả |
|---|---|
| N cần (chưa bù không trả lời) | **686** |
| N điều chỉnh (15%) | **808** |

**KẾT LUẬN:** Nghiên cứu cần tuyển **808 người tham gia**.

## PHẦN 2b — CỠ MẪU THỰC TẾ ĐÃ CHỐT (bác sĩ/chủ nhiệm quyết định)

**N thực tế đã chốt:** **1000** người tham gia — quyết định của bác sĩ/chủ nhiệm đề tài (vd theo khả năng thu thập/thời gian/hành chính), KHÔNG thay thế công thức tính N tối thiểu ở PHẦN 2, chỉ ghi SONG SONG để đối chiếu.

✅ **ĐẠT** — N chốt (1000) ≥ N tối thiểu tính theo thống kê (808), đủ hoặc dư lực thống kê/độ chính xác so với yêu cầu tối thiểu. Với N=1000 (giả định p=0.50, xấu nhất), sai số biên (margin of error) 95% CI ước lượng tỷ lệ ≈ ±3.1 điểm phần trăm — chặt hơn mức tối thiểu PHẦN 2 (N tối thiểu cho ±5%).

---

## PHẦN 2c — LỰC CHO MỤC TIÊU PHỤ (không đổi N của PHẦN 2/2b)

N ở PHẦN 2/2b tính cho kết cục chính. Mục này cho biết, với N đó, mô hình của **Mục tiêu 2** (hồi quy logistic thứ tự (tỷ số chênh tương xứng) — Whitehead 1993) phát hiện được tỷ số chênh (OR) nhỏ nhất bao nhiêu cho mỗi 15 phút thời gian chờ (α = 0.05 hai phía, lực 80%, R² của thời gian chờ theo biến hiệu chỉnh = 0.2).

Công thức: β² = 3·(z₁₋α/₂ + z₁₋β)² / [n·(1 − Σpᵢ³)·(ĐLC/bước)²·(1 − R²)], OR = e^β (Whitehead 1993, PMID 8134732, doi:10.1002/sim.4780122404).

| Phân bố G1 | 1 − Σpᵢ³ | ĐLC thời gian chờ | OR — n = 1000, chưa gom cụm | OR — n hiệu dụng ≈ 478 (thận trọng) |
|---|---|---|---|---|
| Lệch về phía hài lòng mạnh (1/3/11/40/45%) | 0.844 | 20 phút | 1.150 | 1.225 |
| Lệch về phía hài lòng mạnh (1/3/11/40/45%) | 0.844 | 30 phút | 1.098 | 1.145 |
| Lệch về phía hài lòng mạnh (1/3/11/40/45%) | 0.844 | 40 phút | 1.073 | 1.107 |
| Lệch vừa (2/5/18/45/30%) | 0.876 | 20 phút | 1.147 | 1.220 |
| Lệch vừa (2/5/18/45/30%) | 0.876 | 30 phút | 1.096 | 1.142 |
| Lệch vừa (2/5/18/45/30%) | 0.876 | 40 phút | 1.071 | 1.105 |
| Lệch nhẹ (3/7/25/42/23%) | 0.898 | 20 phút | 1.145 | 1.217 |
| Lệch nhẹ (3/7/25/42/23%) | 0.898 | 30 phút | 1.095 | 1.140 |
| Lệch nhẹ (3/7/25/42/23%) | 0.898 | 40 phút | 1.070 | 1.103 |

**Thận trọng:** OR nhỏ nhất phát hiện được 1.10–1.23 cho mỗi 15 phút (chiều giảm 0.82–0.91).

n hiệu dụng = 1000 × (1 − dự phòng phiếu hỏng) = 850, chia DE 1.78 của kết cục chính. DE này là CHẶN TRÊN: với phơi nhiễm đo ở cấp cá nhân, phương sai của hệ số hồi quy phóng đại khoảng 1 + (m − 1)·ρₓ·ρᵧ ≤ DE (Scott & Holt 1982, doi:10.1080/01621459.1982.10477897); ICC thật của phơi nhiễm ước lượng từ dữ liệu.

Nguồn giả định: Đề cương nộp Hội đồng §4.4.1 Bảng 4.2 — giả định lập kế hoạch của nhóm nghiên cứu (phân bố G1, ĐLC thời gian chờ 20/30/40 phút, R² 0,20); đưa vào G3 theo biên bản hội đồng G0 DP-G0-1 (G0-TB-20261017T100650-107f4acb); thống kê viên kiểm, PI quyết khi chốt G3/G4. [CẦN THỐNG KÊ VIÊN KIỂM] — tính lại khi có số liệu khảo sát thử và HIS; thay đổi sau khi khoá SAP ghi «SAP AMENDMENT».

---

## PHẦN 3 — PHÂN TÍCH ĐỘ NHẠY (Sensitivity Analysis)

Bảng: tỷ lệ ước lượng p × sai số cho phép d → N tối thiểu (TRƯỚC khi bù 15% không trả lời; đã nhân hiệu ứng thiết kế cụm DE = 1.78 (= 1+(m−1)×ICC, m = 20, ICC = 0.02))

| p ước lượng | d = ±2.5% | d = ±5% | d = ±10% |
|---|---|---|---|
| 0.10 | 987 | 248 | 63 |
| 0.30 | 2298 | 575 | 145 |
| 0.50 (cơ sở) | 2736 | 686 | 173 |

> *p = 0,50 cho N lớn nhất vì phương sai p(1−p) đạt cực đại tại đó; đây là lựa chọn thận trọng khi chưa biết tỷ lệ thật. Thu hẹp d làm N tăng nhanh theo bình phương.*


---

## PHẦN 4 — KHỐI CỠ MẪU (dán vào đề cương)

```
Cỡ mẫu được tính theo Cỡ mẫu ước lượng một tỷ lệ theo độ chính xác (Lwanga & Lemeshow/Cochran, xấp xỉ chuẩn): tỷ lệ hiện mắc ước lượng p=0.50, sai số cho phép d=0.05, alpha=0.05 Đã áp design effect cụm (DE=1+((CV²+1)m-1)×ICC, CV=1 — Eldridge 2006=1.78, m=20, ICC=0.02): n 385→686 (~35 cụm)..
Với độ tin cậy 95% (α = 0.05) và sai số tuyệt đối cho phép d = ±5%,
với tỷ lệ ước lượng p = 0.50 (Quy ước thận trọng p = 0,50 — giá trị làm phương sai p(1-p) lớn nhất nên cho cỡ mẫu lớn nhất; dùng khi chưa có ước lượng tỷ lệ hài lòng tại chính Khoa C1a. Nguồn công thức: Lwanga SK, Lemeshow S. Sample size determination in health studies: a practical manual. WHO, 1991 (mục 4.4.1 đề cương)),
cần 686 người.
Tính thêm 15% không trả lời dự kiến, cỡ mẫu cuối = 808 người.
N THỰC TẾ đã được bác sĩ/chủ nhiệm CHỐT = 1000 người (≥ N tối thiểu tính toán).
Lực cho Mục tiêu 2 (hồi quy logistic thứ tự (tỷ số chênh tương xứng) — Whitehead 1993): với N = 1000, α = 0.05 hai phía, lực 80%, OR nhỏ nhất phát hiện được cho mỗi 15 phút thời gian chờ là 1.10–1.23 (chiều giảm 0.82–0.91) ở n hiệu dụng ≈ 478 (sau 150 phiếu dự phòng hỏng, ÷ DE 1.78); chưa gom cụm 1.07–1.15. Giả định phân bố kết cục, ĐLC phơi nhiễm và R² tính lại khi có số liệu khảo sát thử và HIS.
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