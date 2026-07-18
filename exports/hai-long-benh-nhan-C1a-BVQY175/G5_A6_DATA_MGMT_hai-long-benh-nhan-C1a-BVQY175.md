# A6 — KẾ HOẠCH QUẢN LÝ DỮ LIỆU (DRAFT)
**Đề tài:** Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh C1a, Trung tâm khám bệnh và điều trị theo yêu cầu C1, Bệnh viện Quân y 175  
**Mã:** hai-long-benh-nhan-C1a-BVQY175 | **Ngày:** 2026-07-17 | **Thiết kế:** cross_sectional | **N dự kiến:** 428  
**Trạng thái:** DRAFT — CHỜ BÁC SĨ ĐIỀN CÁC [CẦN...] VÀ XÁC NHẬN

> ⚠️ **BẢO MẬT:** KHÔNG xử lý PII hoặc dữ liệu thật qua hệ thống này.
> Dữ liệu thật chỉ được xử lý tại môi trường bảo mật của đơn vị (REDCap, server nội bộ).
> Tham chiếu: STROBE 2007 (PMID: 18064739), CONSORT 2025, ICH-GCP E6(R2).

> ℹ️ Chuyên khoa nhận diện từ chủ đề: **patient_satisfaction** — CRF dưới đây đã chọn field lâm sàng/thuốc/kết cục phù hợp chuyên khoa này. Vẫn cần bác sĩ xác nhận từng biến khớp đúng với PICO/SAP thực tế, đặc biệt khi đề tài có yếu tố khác biệt.

---

## PHẦN 1 — CẤU TRÚC CRF (Case Report Form)

Thiết kế: **cross_sectional** | Chuyên khoa: **patient_satisfaction** | Tổng biến CRF: **24 dòng** | N dự kiến: **428**

### Nhóm: Admin (5 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `record_id` | text | Mã tham gia (duy nhất, không PII) | ✓ | — |
| `consent_date` | text | Ngày đồng thuận | ✓ | — |
| `site_id` | text | Mã cơ sở / trung tâm | ✓ | — |
| `visit_date` | text | Ngày khám/thu thập dữ liệu |  | — |
| `complete_flag` | radio | Trạng thái hoàn thành phiếu |  | — |

### Nhóm: Demographics (5 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `age` | text | Tuổi (năm) | ✓ | 18–120 |
| `sex` | radio | Giới tính sinh học | ✓ | — |
| `bmi` | text | BMI (kg/m²) |  | 10–60 |
| `education` | dropdown | Trình độ học vấn |  | — |
| `ethnicity` | dropdown | Dân tộc |  | — |

### Nhóm: Clinical (4 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `visit_type` | radio | Loại lượt khám | ✓ | — |
| `payment_type` | dropdown | Hình thức chi trả | ✓ | — |
| `wait_time_min` | text | Thời gian chờ khám (phút, từ đăng ký đến khi được  |  | 0–600 |
| `visit_freq_year` | text | Số lần đến khám tại khoa trong 12 tháng qua |  | 1–365 |

### Nhóm: Exposure (2 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `occupation` | dropdown | Nghề nghiệp |  | — |
| `income_self_rated` | dropdown | Mức thu nhập tự đánh giá |  | — |

### Nhóm: Outcomes (8 biến)

| Biến | Loại | Nhãn | Bắt buộc | Phạm vi |
|------|------|------|----------|---------|
| `domain_access_score` | text | Điểm hài lòng — Khả năng tiếp cận dịch vụ | ✓ | 1–5 |
| `domain_transparency_score` | text | Điểm hài lòng — Minh bạch thông tin, thủ tục khám  | ✓ | 1–5 |
| `domain_facility_score` | text | Điểm hài lòng — Cơ sở vật chất, phương tiện phục v | ✓ | 1–5 |
| `domain_staff_attitude_score` | text | Điểm hài lòng — Thái độ ứng xử, năng lực chuyên mô | ✓ | 1–5 |
| `domain_service_result_score` | text | Điểm hài lòng — Kết quả cung cấp dịch vụ khám chữa | ✓ | 1–5 |
| `overall_satisfaction_score` | text | Điểm hài lòng chung (kết cục chính tổng hợp) | ✓ | 1–5 |
| `overall_satisfaction_binary` | radio | Hài lòng chung (nhị phân, theo ngưỡng cắt bộ công  | ✓ | — |
| `willing_to_return` | radio | Sẵn sàng quay lại khám/giới thiệu người khác |  | — |

---

## PHẦN 2 — REDCAP DATA DICTIONARY

File CSV: `G5_REDCap_dictionary_hai-long-benh-nhan-C1a-BVQY175.csv` (**24 dòng**)
Biến số (numeric): 10
Biến ngày: 2
Biến bắt buộc: 14

Tóm tắt 10 biến đầu:
| Variable | Form | Type | Label | Bắt buộc |
|----------|------|------|-------|----------|
| `record_id` | Admin | text | Mã tham gia (duy nhất, không PII) | ✓ |
| `consent_date` | Admin | text | Ngày đồng thuận | ✓ |
| `site_id` | Admin | text | Mã cơ sở / trung tâm | ✓ |
| `visit_date` | Admin | text | Ngày khám/thu thập dữ liệu |  |
| `age` | Demographics | text | Tuổi (năm) | ✓ |
| `sex` | Demographics | radio | Giới tính sinh học | ✓ |
| `bmi` | Demographics | text | BMI (kg/m²) |  |
| `education` | Demographics | dropdown | Trình độ học vấn |  |
| `ethnicity` | Demographics | dropdown | Dân tộc |  |
| `visit_type` | Clinical | radio | Loại lượt khám | ✓ |
| ... | ... | ... | ... | ... |
| *(+14 dòng — xem file CSV)* | | | | |

---

## PHẦN 3 — LUẬT KIỂM TRA DỮ LIỆU (Validation Rules)

| Biến | Loại | Phạm vi | Quy tắc | Hành động |
|------|------|---------|---------|-----------|
| `record_id` | text | Chuỗi | Duy nhất trong DB, không PII | Báo lỗi trùng ID — hệ thống REDCap tự phát hiện |
| `consent_date` | date | 2020-01-01→hôm nay | Ngày hợp lệ, không tương lai | Báo lỗi ngày |
| `age` | integer | 18–120 | Người lớn hợp lệ | Báo lỗi tuổi |
| `bmi` | number | 10–60 | Phạm vi sinh lý | Cảnh báo ngoài phạm vi |
| `lvef` | number | 20–85 | EF sinh lý, THẤP VÀO HFpEF nếu ≥50 | Gắn cờ nếu <50 (không phải HFpEF) |
| `bp_sys` | number | 60–250 | Huyết áp tâm thu | Cảnh báo ngoài phạm vi |
| `bp_dia` | number | 30–150 | Huyết áp tâm trương | Cảnh báo ngoài phạm vi |
| `heart_rate` | integer | 30–250 | Nhịp tim | Cảnh báo nhịp cực đoan |
| `egfr` | number | 0–200 | eGFR sinh lý | Cảnh báo eGFR<20 (CKD nặng, LOẠI TRỪ nếu theo protocol) |
| `nt_probnp` | number | 0–100000 | NT-proBNP pg/mL | Cảnh báo >35000 (cần xem lại) |
| `hba1c` | number | 4–15 | HbA1c — chỉ khi có ĐTĐ | Phân nhánh: bỏ qua nếu dm=0 |
| `hgb` | number | 3–20 | Hemoglobin g/dL | Cảnh báo thiếu máu nặng (hgb<7) |
| `creatinine` | number | 20–2000 | Creatinine µmol/L | Cảnh báo nếu >884 (eGFR có thể <15) |
| `k_serum` | number | 1.5–8 | Kali mmol/L | Cờ ĐỎ nếu <2.5 hoặc >6 (nguy cơ tim mạch) |
| `sglt2i_start_date` | date | ≥consent_date | Không trước ngày đồng thuận | Lỗi logic ngày |
| `hf_hosp_date` | date | ≥consent_date | Ngày nhập viện không trước tuyển | Lỗi logic ngày |
| `death_date` | date | ≥consent_date | Ngày tử vong không trước tuyển | Lỗi logic ngày; cần ≥hf_hosp_date nếu có |
| `follow_time_months` | number | 0–120 | Thời gian theo dõi (tháng) | Kiểm nhất quán vs censor_date |
| `qol_score_baseline` | number | 0–100 | Điểm QoL nền [CẦN CHỈ ĐỊNH THANG ĐO] | Kiểm phạm vi theo thang cụ thể |
| `ef_change_6m` | number | -50–50 | Thay đổi EF từ nền đến 6 tháng | Cảnh báo thay đổi >30 (kiểm lại) |
| `acr` | number | 0–20000 | Albumin/Creatinine niệu (ACR) mg/g | Cảnh báo >300 (albumin niệu nặng, macroalbumin) |
| `fev1_pct` | number | 10–150 | FEV1 % dự đoán | Cảnh báo <30 (COPD rất nặng — GOLD 4) |
| `fev1_fvc_ratio` | number | 20–100 | Tỷ số FEV1/FVC (%) | Cảnh báo <70 gợi ý tắc nghẽn |
| `cat_score` | integer | 0–40 | Điểm CAT (COPD Assessment Test) | Cảnh báo ≥20 (ảnh hưởng nặng) |
| `exacerbation_freq_prior` | integer | 0–50 | Số đợt cấp COPD/hen trong 12 tháng trước | Cảnh báo ≥2 (nguy cơ cao — nhóm E theo GOLD) |
| `nihss_baseline` | integer | 0–42 | Điểm NIHSS lúc nhập viện | Cảnh báo ≥21 (đột quỵ rất nặng) |
| `pain_nrs_baseline` | integer | 0–10 | Điểm đau NRS nền | Cảnh báo =10 (đau tối đa, cần xử trí ngay) |
| `pain_duration_months` | integer | 3–600 | Thời gian đau mạn (tháng) | Kiểm giá trị <3 (không đạt định nghĩa đau mạn) |
| `opioid_mme_per_day` | number | 0–2000 | Liều opioid quy đổi MME/ngày | Cờ ĐỎ nếu ≥90 MME/ngày (ngưỡng nguy cơ cao CDC) |
| `pain_nrs_change` | number | -10–10 | Thay đổi điểm đau NRS so với nền | Kiểm nhất quán chiều thay đổi vs đáp ứng lâm sàng |
| `phq9_baseline` | integer | 0–27 | Điểm PHQ-9 nền | Cờ ĐỎ nếu mục 9 (ý tưởng tự sát) >0 — xử trí an toàn ngay |
| `gad7_baseline` | integer | 0–21 | Điểm GAD-7 nền | Cảnh báo ≥15 (lo âu nặng) |
| `phq9_followup` | integer | 0–27 | Điểm PHQ-9 tại mốc theo dõi | So sánh với phq9_baseline để tính đáp ứng/thuyên giảm |

---

## PHẦN 4 — SƠ ĐỒ THAM GIA NGHIÊN CỨU (STROBE/CONSORT Flowchart)

```
┌─────────────────────────────────────────────────────────────────┐
│        BIỂU ĐỒ THAM GIA NGHIÊN CỨU (STROBE Flowchart)         │
│                      Đề tài: hai-long-benh-nhan-C1a-BVQY175     │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────────────────────────────────────┐
  │  Đánh giá đủ tiêu chuẩn (Assessed):     │
  │  N = [CẦN — BÁC SĨ ĐIỀN từ sổ bệnh]   │
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────▼──────────────────┐
        │  Loại trừ (Excluded):        │
        │  N = [CẦN]                   │
  │  • [CẦN — tiêu chí loại trừ theo PICO/SAP thật]  │
        │  • Không đồng thuận          │
        │  • [CẦN thêm lý do cụ thể]  │
        └─────────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  TUYỂN VÀO (Enrolled):                   │
  │  N = 428 (N dự kiến + 20% dự phòng)│
  └────────────────┬─────────────────────────┘
                   │
        ┌──────────┴──────────────────┐
        │                             │
        ▼                             ▼
  ┌───────────────┐           ┌───────────────┐
  │  CÓ PHƠI      │           │  KHÔNG PHƠI   │
  │  NHIỄM [CẦN — tên biến phơi nhiễm/can thiệp theo PICO]│          │  NHIỄM        │
  │  N ≈ 385          │           │  N ≈ 0            │
  └───────┬───────┘           └───────┬───────┘
          │                           │
          ▼                           ▼
  ┌──────────────────────────────────────────┐
  │  THEO DÕI (Follow-up):                  │
  │  Mất theo dõi / LTFU: N = [CẦN]        │
  │  Lý do: [CẦN — rút ĐT/tử vong/ltfu]   │
  └────────────────┬─────────────────────────┘
                   │
  ┌────────────────▼─────────────────────────┐
  │  PHÂN TÍCH (Analysed):                   │
  │  N = 428 → [CẦN điều chỉnh thực tế]│
  │  Phân tích chính: 385 (sau loại trừ)  │
  └──────────────────────────────────────────┘

  Ghi chú: Điền N=[CẦN] SAU khi thu thập dữ liệu thật.
  Tham chiếu: STROBE 2007 (PMID: 18064739). Cần bác sĩ kiểm chứng.

```

---

## PHẦN 5 — SCRIPTS TỰ ĐỘNG (Sinh từ CRF Dictionary)

**Thư mục:** `exports/hai-long-benh-nhan-C1a-BVQY175/scripts/`

| Script | Mô tả | Đầu vào | Đầu ra |
|--------|-------|---------|--------|
| `data_cleaning.py` | Làm sạch REDCap export; ép kiểu; kiểm range | `data/raw/redcap_export.csv` | `data/processed/df_clean.csv` |
| `data_quality_report.py` | Báo cáo N, % complete, vi phạm, trùng ID | `data/processed/df_clean.csv` | `data_quality_report.txt` |

Chạy theo thứ tự:
```bash
cd exports/hai-long-benh-nhan-C1a-BVQY175/
python scripts/data_cleaning.py --input data/raw/redcap_export.csv
python scripts/data_quality_report.py --input data/processed/df_clean.csv
```

---

## PHẦN 6 — KẾ HOẠCH DỮ LIỆU THIẾU

| Loại thiếu | Giả định | Chiến lược xử lý |
|------------|----------|-----------------|
| < 5% mỗi biến | MCAR | Complete case đủ |
| 5–30% | MAR | Multiple Imputation (m=20, package `mice`) |
| > 30% hoặc MNAR | MNAR | Pattern mixture models / Sensitivity analysis |
| [CẦN XEM XÉT THỰC TẾ từ bước thu thập] | | |

---

## PHẦN 7 — CẤU TRÚC GÓI TÁI LẶP

```
exports/hai-long-benh-nhan-C1a-BVQY175/
├── data/             # KHÔNG commit — chứa dữ liệu thật
│   ├── raw/          # dữ liệu thô từ REDCap export
│   └── processed/    # df_clean.csv + data_quality_report.txt
├── scripts/          # Python scripts tự động — có thể commit
│   ├── data_cleaning.py        # làm sạch REDCap export
│   └── data_quality_report.py  # báo cáo chất lượng
├── output/           # bảng kết quả, hình (generate — không commit binary)
├── docs/             # SAP, đề cương, các artifact G0-G4
│   ├── G4_A5_SAP_FINAL_hai-long-benh-nhan-C1a-BVQY175.md
│   └── G2_A3_ETHICS_PACKAGE_hai-long-benh-nhan-C1a-BVQY175.md
└── README.md         # Hướng dẫn tái lặp đầy đủ
```

**`.gitignore` bắt buộc:**
```
data/raw/
data/processed/
*.csv
*.xlsx
.env
```

---

## PHẦN 8 — CHECKLIST KHÓA CƠ SỞ DỮ LIỆU

Thực hiện TRƯỚC khi chạy phân tích chính (G6):
- [ ] Tất cả data queries đã được giải quyết (trả lời đủ)
- [ ] Tỷ lệ thiếu biến chính < 5%
- [ ] Audit trail REDCap đầy đủ (không có chỉnh sửa không có lý do)
- [ ] Backup database kiểm tra thành công (restore test OK)
- [ ] Dual-entry hoặc 10% spot-check xác nhận
- [ ] Script `data_quality_report.py` chạy PASS (không có lỗi đỏ)
- [ ] Ngày khóa DB: [CẦN BÁC SĨ ĐIỀN]
- [ ] Người khóa DB (chữ ký): [CẦN]
- [ ] Người chứng kiến (chữ ký): [CẦN]

---

## PHẦN 9 — TIÊU CHÍ QUA CỔNG G5

- [ ] **[CẦN BÁC SĨ]** Điền tất cả [CẦN...] trong CRF (biến phơi nhiễm/kết cục cụ thể)
- [ ] **[CẦN BÁC SĨ]** Import REDCap dictionary CSV vào REDCap cơ sở
- [ ] **[CẦN BÁC SĨ + ĐỘI NC]** Thu thập dữ liệu thật (chỉ sau G2 = LOCKED)
- [ ] **[CẦN BÁC SĨ]** Spot-check 10% phiếu CRF
- [ ] **[CẦN BÁC SĨ]** Chạy `data_cleaning.py` + `data_quality_report.py` → PASS
- [ ] **[CẦN BÁC SĨ]** Ký biên bản khóa DB

---

*Cần bác sĩ kiểm chứng. KHÔNG xử lý dữ liệu thật qua hệ thống này.*
*Script tự động ở PHẦN 5 chỉ chạy trên môi trường bảo mật nội bộ với dữ liệu thật.*