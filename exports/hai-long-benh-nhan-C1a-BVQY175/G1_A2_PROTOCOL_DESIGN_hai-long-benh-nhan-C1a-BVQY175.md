# A2 — THIẾT KẾ NGHIÊN CỨU & SAP SKELETON | hai-long-benh-nhan-C1a-BVQY175
> Tạo tự động: 2026-07-17 19:12 | Rule-based + PubMed effect size thật
> [BẢN NHÁP TỰ ĐỘNG] — Bác sĩ xác nhận thiết kế chọn + điền [CẦN...] trước khi tiến G2/G4
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — BẢNG THIẾT KẾ ỨNG VIÊN

| Thiết kế | Phù hợp câu hỏi | Kiểm soát sai lệch | Khả thi | Lực | Chọn/Loại |
|---|---|---|---|---|---|
| **Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)** | ✅ Phù hợp nhất (Mô tả (cross-sectional)) | Cao (xem §2) | [CẦN BÁC SĨ] | [CẦN cỡ mẫu] | **→ ƯU TIÊN** |
| Khảo sát dựa cộng đồng (nếu muốn ngoại suy toàn dân số) | Phù hợp thay thế | Trung bình | [CẦN] | [CẦN] | Phương án 2 |
| Registry / Audit lâm sàng (nếu muốn dữ liệu thực hành) | Phù hợp trong điều kiện đặc biệt | Thấp hơn | [CẦN] | [CẦN] | Phương án 3 |

**Lý do chọn ưu tiên `Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)`:**
Câu hỏi mô tả (tỷ lệ/đặc điểm) → cắt ngang là tiêu chuẩn. Không suy nhân quả từ thiết kế này.

**Chuẩn báo cáo:** STROBE

---

## PHẦN 2 — KIỂM SOÁT 7 SAI LỆCH CHÍNH

| Sai lệch | Biện pháp kiểm soát cho `Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)` |
|---|---|
| Selection bias | Sampling ngẫu nhiên hoặc liên tiếp; tránh tự chọn |
| Information bias | Đo phơi nhiễm + kết cục cùng thời điểm → không suy nhân quả |
| Confounding | Đa biến; hạn chế: cùng thời điểm → không loại trừ causal confounders |
| Prevalence-incidence bias | Thiết kế chỉ ước lượng hiện mắc; bàn luận giới hạn này |
| Non-response bias | So sánh người trả lời vs không trả lời (nếu có thể) |
| Social desirability | Tự báo cáo → có thể underreport hành vi tiêu cực |
| Reporting bias | Đăng ký nghiên cứu + tiền định phân tích |

---

## PHẦN 3 — EFFECT SIZE ƯỚC LƯỢNG (từ PubMed thật — dùng tính cỡ mẫu G3)

> **Quan trọng:** Đây là ước lượng TỰ ĐỘNG từ abstracts.
> Bác sĩ PHẢI đọc toàn văn để xác minh trước khi dùng tính cỡ mẫu.
> Nếu không có nghiên cứu phù hợp → dùng pilot data hoặc MCID lâm sàng.

  (Tự động trích từ abstracts PubMed — cần bác sĩ kiểm chứng toàn văn)

  • MD = 0.91 — PMID:42136107 (2026) Effects of Decision Aids on Decision Knowledge, Conflict, an  ⚠️ [THÔ — không có 95%CI đi kèm, có thể lẫn ARR/RR, PHẢI đọc toàn văn xác nhận]

**Evidence landscape từ G0:**
- SR/MA hiện có: 20
- RCT hiện có: 20
- Năm gần nhất: 2026
- Mức độ evidence: MẠNH — có SR/MA

---

## PHẦN 4 — KHỐI THIẾT KẾ (dán vào §Phương pháp của Đề cương)

```
═══════════════════════════════════════════════════════════════
KHỐI THIẾT KẾ — hai-long-benh-nhan-C1a-BVQY175
Loại thiết kế: Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence)
Bố trí: ☐ Song song  ☐ Bắt chéo  ☐ Factorial  ☐ Thích nghi
Ngẫu nhiên hóa: ☐ Không  ☐ Đơn giản  ☐ Phân tầng: [theo ___]  ☐ Cụm
Làm mù: ☐ Mở  ☐ Đơn mù  ☐ Đôi mù  ☐ Tam mù
Estimand chính (can thiệp): [CẦN XÁC NHẬN — xem §Estimand bên trên]
Kiểm soát biến nhiễu chính: [từ §2 Bias Control]
Thời gian theo dõi: [CẦN BÁC SĨ XÁC NHẬN]
Cỡ mẫu dự kiến: [CẦN → chạy run_g3_auto.py sau khi xác nhận effect size]
Giả định effect size (nguồn): [CẦN — xem §3 hoặc pilot data]
Chuẩn báo cáo: STROBE
═══════════════════════════════════════════════════════════════
```

---

## PHẦN 5 — SAP SKELETON (12 MỤC — bác sĩ điền [CẦN...])

> SAP phải hoàn chỉnh và KHÓA TRƯỚC KHI XEM DỮ LIỆU THẬT (Cổng G4).
> [CẦN...] = cần bác sĩ điền; mọi mục này KHÔNG thay đổi sau khi khóa.

### SAP §1 — Quần thể phân tích
```
Toàn bộ người đủ tiêu chí (Complete case)
Tiêu chí chọn vào: [CẦN — từ PICO P]
Tiêu chí loại trừ: [CẦN BÁC SĨ ẤN ĐỊNH]
Quần thể CHÍNH dùng báo cáo: [CẦN XÁC NHẬN]
```

### SAP §2 — Biến kết cục (định nghĩa vận hành)
```
KẾT CỤC CHÍNH (chỉ 1):
  Tên: [CẦN — từ PICO O, kết cục chính BÁC SĨ ĐÃ ẤN ĐỊNH ở G0]
  Định nghĩa vận hành: [CẦN — rõ ràng, đo được, cụ thể]
  Đơn vị đo: [CẦN]
  Thời điểm đo: [CẦN]
  Thước đo: ☐ Liên tục  ☐ Nhị phân  ☐ Thứ tự  ☐ Thời gian đến sự kiện

KẾT CỤC PHỤ (tối đa 3–5):
  1. ___ | thời điểm: ___
  2. ___ | thời điểm: ___
  3. ___ | thời điểm: ___
```

### SAP §3 — Thống kê mô tả (Table 1)
```
Biến liên tục: kiểm phân phối → Shapiro-Wilk (n<50) hoặc histogram (n≥50)
  Chuẩn: TB ± ĐLC  |  Lệch: Trung vị [IQR Q1–Q3]
Biến phân loại: n (%)
So sánh nền (Table 1): t-test/Mann-Whitney + chi²/Fisher (CHỈ MÔ TẢ, không p-value chính)
```

### SAP §4 — Phân tích chính (Mục tiêu 1)
```
Phân tích chính: Logistic regression → OR (95%CI)
Hoặc: Linear regression → β (95%CI) nếu kết cục liên tục
VIF < 5 (kiểm đa cộng tuyến); Hosmer-Lemeshow (logistic)
α (hai đuôi): 0.05
Hiệu ứng trình bày: [OR/HR/RR/MD + 95%CI] — KHÔNG chỉ p-value
Phần mềm: ☐ R  ☐ Stata  ☐ SPSS  | Seed ngẫu nhiên: 20260717 [CẦN BÁC SĨ XÁC NHẬN — gợi ý tự sinh từ ngày chạy]
```

### SAP §5 — Phân tích đa biến (Mục tiêu 2 — nếu có)
```
Mô hình: ☐ Logistic  ☐ Linear  ☐ Cox  ☐ Mixed-effects  ☐ GEE
Covariates (định trước — KHÔNG thêm sau khi xem dữ liệu):
  - [CẦN BÁC SĨ LIỆT KÊ với lý do cho từng biến + DAG nếu có]
EPV ≥ 10 cho mô hình đa biến
Kiểm đa cộng tuyến: VIF < 5 cho mọi biến
Kiểm mức phù hợp: ☐ Hosmer-Lemeshow  ☐ Calibration plot
```

### SAP §6 — Dữ liệu thiếu
```
Giả định: ☐ MCAR  ☐ MAR  ☐ MNAR (phân tích pattern thiếu trước khi chọn)
  MCAR → Complete-case (báo cáo tỷ lệ thiếu)
  MAR  → Multiple Imputation: m=20, phương pháp PMM/logistic
  MNAR → Sensitivity (tilt parameter / pattern mixture)
Ngưỡng chấp nhận: < [CẦN ẤN ĐỊNH]% (ví dụ: <20%)
```

### SAP §7 — Phân tích nhóm nhỏ (định trước — KHÔNG thêm sau)
```
Nhóm nhỏ 1: [CẦN — tiêu chí: ___] | Giả thuyết tương tác: ___
Nhóm nhỏ 2: [CẦN]
Kiểm định tương tác: interaction test (p < 0.05 = subgroup effect có ý nghĩa)
Kết quả nhóm nhỏ là THĂM DÒ nếu không có giả thuyết định trước
```

### SAP §8 — Kiểm soát đa so sánh
```
Số kết cục phụ / nhóm / thời điểm: [CẦN ẤN ĐỊNH]
Chiến lược:
  ☐ Không điều chỉnh (1 kết cục chính rõ, phụ là thăm dò)
  ☐ Bonferroni: α = 0.05 / n_so_sánh
  ☐ Holm-Bonferroni
  ☐ FDR Benjamini-Hochberg
Khớp với α dùng khi tính cỡ mẫu (G3): ✓
```

### SAP §9 — Phân tích nhạy cảm
```
1. [CẦN — lý do: ___] → kỳ vọng: kết quả ổn định
2. [CẦN — lý do: ___] → kỳ vọng: ___
3. Per-protocol sensitivity (nếu ITT là chính) → kiểm tính vững chắc
```

### SAP §10 — Phần mềm và seed
```
Phần mềm chính: ☐ R v___  ☐ Stata v___  ☐ SPSS v___
R packages dự kiến: tableone, car [CẦN BÁC SĨ XÁC NHẬN — gợi ý theo thiết kế cross_sectional]
Random seed: 20260717 [CẦN BÁC SĨ XÁC NHẬN — gợi ý tự sinh từ ngày chạy, có thể đổi]
Script phân tích: lưu tại exports/hai-long-benh-nhan-C1a-BVQY175/scripts/ — versioned cùng protocol
```

### SAP §11 — Dummy Tables (Shells — điền sau khi có kết quả thật)

```
BẢNG 1 — ĐẶC ĐIỂM NỀN
| Biến | Nhóm A (n=___) | Nhóm B (n=___) | p |
|------|----------------|----------------|---|
| Tuổi, TB±ĐLC (năm) | | | |
| Giới nữ, n (%) | | | |
| [Bệnh kèm], n (%) | | | |
| [Biến nền theo PICO P] | | | |
| [Biến lâm sàng chính] | | | |

BẢNG 2 — KẾT CỤC CHÍNH
| Kết cục | Nhóm A (n=___) | Nhóm B (n=___) | Hiệu ứng (95%CI) | p |
|---------|----------------|----------------|-------------------|---|
| [Tên kết cục chính] | | | [OR/HR/MD]=___ | |

BẢNG 3 — KẾT CỤC PHỤ
| Kết cục phụ | Nhóm A | Nhóm B | Hiệu ứng (95%CI) | p |
|-------------|--------|--------|-------------------|---|
| [Kết cục phụ 1] | | | | |
| [Kết cục phụ 2] | | | | |
| [Kết cục phụ 3] | | | | |

BẢNG 4 — PHÂN TÍCH ĐA BIẾN
| Biến | OR/HR (thô) | 95%CI | OR/HR (hiệu chỉnh) | 95%CI | p |
|------|-------------|-------|---------------------|-------|---|
| [Can thiệp/Phơi nhiễm chính] | | | | | |
| [Covariate 1] | | | | | |
| [Covariate 2] | | | | | |
```

### SAP §12 — Ngưỡng ý nghĩa và power
```
α (hai đuôi): 0.05
Power mục tiêu: ___% (thường 80% hoặc 90%)
→ Khớp với tính cỡ mẫu (G3) — KHÔNG đổi sau khi chốt.
```

---

## PHẦN 6 — SAP LOCK CERTIFICATE (CHỜ BÁC SĨ KÝ → MỞ G4)

```
╔══════════════════════════════════════════════════════════════╗
║    BIÊN BẢN KHÓA KẾ HOẠCH PHÂN TÍCH THỐNG KÊ (SAP)        ║
╠══════════════════════════════════════════════════════════════╣
║  Đề tài: hai-long-benh-nhan-C1a-BVQY175                        ║
║  Phiên bản SAP: 1.0                                         ║
║  Ngày soạn SAP: 2026-07-17                                    ║
║  Trạng thái dữ liệu lúc khóa: CHƯA CÓ / CHƯA XEM          ║
║                                                              ║
║  Kết cục chính (KHÔNG đổi sau khóa):                        ║
║    [CẦN BÁC SĨ ĐIỀN — từ PICO O đã xác nhận ở G0]          ║
║  Quần thể phân tích chính:                                  ║
║    [CẦN BÁC SĨ ĐIỀN — từ SAP §1]                           ║
║  Phương pháp phân tích chính:                               ║
║    [CẦN BÁC SĨ ĐIỀN — từ SAP §4]                           ║
║  α: 0.05 (hai đuôi)  |  Power: [CẦN]%                      ║
╠══════════════════════════════════════════════════════════════╣
║  Người xác nhận: ___ (Chủ nhiệm đề tài)                     ║
║  Ngày khóa chính thức: [CẦN ĐIỀN + KÝ TÊN]                 ║
║                                                              ║
║  Chữ ký: _______________  Ngày: ___/___/20__                ║
╠══════════════════════════════════════════════════════════════╣
║  SAU KHI KÝ: KHÔNG đổi kết cục chính / mô hình chính.      ║
║  Phân tích bổ sung sau khi xem dữ liệu → ghi THĂM DÒ.     ║
╚══════════════════════════════════════════════════════════════╝
```

**→ Để mở G4:** Bác sĩ xác nhận "SAP đã khóa ngày [DD/MM/YYYY]"
  Agent ghi: G4_STATUS=LOCKED | G4_SAP_VERSION=1.0 | G4_LOCK_DATE=[date]

---

## PHẦN 7 — TIÊU CHÍ QUA CỔNG G1

```
☑ Loại thiết kế đã suy luận từ PICO + evidence landscape
☑ 2-3 thiết kế ứng viên đã so sánh
☑ 7 sai lệch đã phân tích với biện pháp kiểm soát
☑ SAP skeleton 12 mục đã sinh
☑ Dummy tables 4 bảng đã tạo shell
☑ Effect size ước lượng từ PubMed thật (xem §3)
☐ Bác sĩ xác nhận thiết kế chọn [CHỜ BÁC SĨ]
☐ PICO O (kết cục) điền vào SAP §2 [CHỜ BÁC SĨ]
☐ Covariates SAP §5 liệt kê với lý do [CHỜ BÁC SĨ]
☐ Effect size thật + cỡ mẫu → G3 (co-mau-nghien-cuu) [BƯỚC TIẾP]
☐ SAP Lock Certificate ký → G4 [CHỜ SAU G3]
```

**Bước tiếp theo:**
1. Bác sĩ xem §3 (effect size) → chọn ước lượng phù hợp
2. Chạy G3: `python tools/run_g3_auto.py --study hai-long-benh-nhan-C1a-BVQY175`
3. Sau khi có cỡ mẫu, ký SAP → mở G4

---

*[BẢN NHÁP TỰ ĐỘNG] — Cần bác sĩ kiểm chứng. PMID/DOI trong §3 là THẬT từ PubMed.*
