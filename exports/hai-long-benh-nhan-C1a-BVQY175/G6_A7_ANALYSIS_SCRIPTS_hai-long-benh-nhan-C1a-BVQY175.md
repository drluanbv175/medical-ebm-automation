# A7 — R ANALYSIS SCRIPTS + PYTHON CLI + SAP THỰC THI (DRAFT — SKELETON)
**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày sinh:** 2026-07-17 | **Phiên bản:** 2.0 (Nâng cấp 75%)
**Thiết kế:** cross_sectional | **Chuẩn báo cáo:** STROBE
**Phân tích chính:** Logistic regression (OR 95%CI) / Linear regression (β 95%CI)

> ⚠️ **QUAN TRỌNG (DRAFT — SKELETON):** Scripts là cấu trúc code với tên biến thật.
> Không thể chạy phân tích không có dữ liệu thật đã khóa DB (G5).
> R scripts: mọi lệnh đều comment (#) — uncomment khi có dữ liệu.
> Python: run_analysis_cli.py chạy được ngay khi cung cấp CSV thật.

---

## PHẦN 1 — BIẾN SỐ TỰ PHÁT HIỆN TỪ REDCAP DICTIONARY (G5)

| Vai trò | Tên biến | Ghi chú |
|---|---|---|
| Phơi nhiễm (exposure) | `exposure_var` | Từ G5 REDCap dictionary |
| Kết cục chính (outcome) | `primary_outcome` | 1=biến cố, 0=censored |
| Thời gian theo dõi | `follow_time_months` | Đơn vị: tháng |
| Covariates | `age, sex, bmi, education, ethnicity, bp_sys, bp_dia, heart_rate, dm, htn, comorbid_other` | Nhân khẩu + lab + bệnh nền |

**Log phát hiện biến:**
  - ✅ Phơi nhiễm (từ Section Header): exposure_var
  - ✅ Kết cục (từ Section Header 'Kết cục chính'): primary_outcome
  - ✅ Thời gian: follow_time_months
  - ✅ Covariates (11): age, sex, bmi, education, ethnicity, bp_sys, bp_dia, heart_rate, dm, htn, comorbid_other

> ⚠️ Kiểm tra lại tên biến với CRF thật trước khi chạy scripts.

---

## PHẦN 2 — ĐIỀU KIỆN CHẠY PHÂN TÍCH

- [ ] **G4 SAP đã LOCKED**: PENDING — CHỜ BÁC SĨ KÝ SAP
  ⚠️ SAP chưa LOCKED — KHÔNG được xem dữ liệu
- [ ] **DB đã khóa (G5)**: Biên bản khóa DB có chữ ký bác sĩ
- [ ] **Scripts versioned**: `git commit` trước khi chạy lần đầu
- [ ] **Seed đã ghi vào SAP**: `SEED = 2026` (hoặc theo SAP §10)
- [ ] **R ≥ 4.2 hoặc Python + venv ~/.ebm-venv** đã cài đặt

---

## PHẦN 3 — SCRIPTS ĐƯỢC SINH

Scripts tại: `exports/hai-long-benh-nhan-C1a-BVQY175/scripts/`

| Script | Mục đích | Biến dùng | Thư viện |
|---|---|---|---|
| `00_setup.R` | Cài packages R | — | tidyverse, survival, mice, gtsummary |
| `01_cleaning.R` | Làm sạch, recode biến | exposure_var, primary_outcome, follow_time_months | tidyverse, REDCapR |
| `02_tables.R` | Table 1 theo nhóm exposure_var | age, sex, bmi, education | gtsummary, flextable |
| `03_analysis.R` | Cox + KM + MI (m=20) | exposure_var/primary_outcome/follow_time_months | survival, survminer, mice |
| `run_analysis_cli.py` | **Python CLI đầy đủ** — chạy ngay với CSV | exposure_var/primary_outcome/follow_time_months | lifelines, pandas, matplotlib |
| `sensitivity_analysis.py` | CC vs MI, Subgroup, E-value | exposure_var/primary_outcome/follow_time_months | lifelines, pandas |

**Thứ tự chạy (R):**
```bash
Rscript scripts/00_setup.R
Rscript scripts/01_cleaning.R
Rscript scripts/02_tables.R
Rscript scripts/03_analysis.R
```

**Chạy Python CLI (khi có CSV thật):**
```bash
python scripts/run_analysis_cli.py \
    --data data/raw/export.csv \
    --exposure exposure_var \
    --outcome primary_outcome \
    --time follow_time_months \
    --covariates age,sex,bmi,education,ethnicity,bp_sys,bp_dia,heart_rate,dm,htn,comorbid_other

python scripts/sensitivity_analysis.py \
    --data data/raw/export.csv
```

---

## PHẦN 4 — BẢNG KẾT QUẢ DỰ KIẾN (Shell)

*(N dự kiến = 428, alpha = 0.05, power = 0.8, OR = 0.5)*


**Bảng 1 — Đặc điểm nền:**
| Biến | Phơi nhiễm+ (N=[CẦN]) | Phơi nhiễm- (N=[CẦN]) | SMD / p |
| ---|---|---|--- |
| Tuổi (năm), TB±SD | [chạy 02_tables.R] | [chạy 02_tables.R] | [chạy] |
| Giới nữ, n (%) | [chạy 02_tables.R] | [chạy 02_tables.R] | [chạy] |


**Bảng 2 — Kết cục chính (Logistic regression):**
| Phân tích | OR | 95%CI Lower | 95%CI Upper | p |
| ---|---|---|---|--- |
| Thô (univariable) | [chạy 03_analysis.R] | [chạy] | [chạy] | [chạy] |
| Hiệu chỉnh (multivariable) | [chạy 03_analysis.R] | [chạy] | [chạy] | [chạy] |

---

## PHẦN 5 — CHECKLIST TRƯỚC BÁO CÁO

- [ ] Mọi ước lượng kèm **95%CI** — KHÔNG báo p-value đơn độc
- [ ] Báo cáo **complete case** VÀ **MI (m=20)** — nhất quán
- [ ] Kiểm định **PH assumption**: `cox.zph()` p > 0.05
- [ ] **E-value** báo cáo kèm kết quả chính (sensitivity_analysis.py)
- [ ] **Subgroup** chỉ chạy nếu có trong SAP §7 đã khóa
- [ ] **KM curve** kèm bảng risk-at-risk và log-rank p

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G6

- [ ] **G4 = LOCKED** trước khi xem dữ liệu [CẦN BÁC SĨ XÁC NHẬN]
- [ ] **Chạy 01_cleaning.R** — log không lỗi [CẦN BÁC SĨ]
- [ ] **Table 1 hoàn chỉnh** theo nhóm `exposure_var` — SMD < 0.2 [CẦN]
- [ ] **Cox kết quả** HR + 95%CI `exposure_var/primary_outcome` điền Bảng 2 [CẦN]
- [ ] **Sensitivity** (CC vs MI + E-value) nhất quán [CẦN]
- [ ] **Bác sĩ duyệt** kết quả trước khi viết G7 [CẦN]

---

*Cần bác sĩ kiểm chứng. Scripts với tên biến thật từ REDCap — kiểm tra trước khi chạy.*  
*Mã: hai-long-benh-nhan-C1a-BVQY175 | Sinh: 2026-07-17 | Version: A7 v2.0 | Mức tự động: 75%*