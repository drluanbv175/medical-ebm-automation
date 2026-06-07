# Danh mục nguồn y văn (Clinical Evidence RAG)

> Kho nguồn **do bác sĩ kiểm soát** cho skill `clinical-evidence-rag`. Ưu tiên khi mâu thuẫn:
> **protocol cục bộ > guideline > review/meta-analysis > bài báo gốc**.
> Mỗi khi thêm tài liệu vào `evidence/`, thêm 1 dòng vào bảng. Khi 1 guideline bị thay thế:
> **KHÔNG xóa** — ghi chú "đã thay thế bởi #N".
>
> Trạng thái đường dẫn: `✅ đã có` = file/tài liệu có trong kho; `⬜ cần thả PDF` = đã biết
> nguồn (trích từ `verified.py`) nhưng **bạn cần tải bản chính thức** vào thư mục tương ứng.

| # | Tiêu đề | Loại | Tổ chức | Năm | Đường dẫn | Trạng thái | Thang điểm liên quan |
|---|---------|------|---------|-----|-----------|-----------|----------------------|
| 1 | Rà soát đối chiếu 30 thang điểm lâm sàng 2026-06 | review (nội bộ) | medical-ebm-automation | 2026 | `../docs/RA_SOAT_THANG_DIEM_2026-06.md` | ✅ đã có | (tất cả) |
| 1b | Tổng hợp chứng cứ 32 thang điểm (RAG, có trích dẫn) | review (nội bộ, tự sinh) | medical-ebm-automation | 2026 | `reviews/tong-hop-chung-cu-thang-diem-2026.md` | ✅ đã có | (tất cả 32) |
| 2 | ESC 2024 AF Guideline (AF-CARE, CHA2DS2-VA) | guideline | ESC | 2024 | `guidelines/esc_af_2024.pdf` | ⬜ cần thả PDF | cha2ds2_vasc, has_bled |
| 3 | AASLD MASLD Practice Guidance (FIB-4 <1.3) | guideline | AASLD | 2023 | `guidelines/aasld_masld_2023.pdf` | ⬜ cần thả PDF | fib4 |
| 4 | GOLD Report (ABE; eosinophil ≥300 cho ICS) | guideline | GOLD | 2025 | `guidelines/gold_2025.pdf` | ⬜ cần thả PDF | gold_abe |
| 5 | Surviving Sepsis Campaign (mạnh chống qSOFA đơn lẻ) | guideline | SSC/SCCM | 2021 | `guidelines/ssc_2021.pdf` | ⬜ cần thả PDF | qsofa, news2 |
| 6 | OPTN/UNOS policy — MELD 3.0 là chuẩn | guideline | OPTN/UNOS | 2023 | `guidelines/optn_meld3_2023.pdf` | ⬜ cần thả PDF | meld_na |
| 7 | ACC/AHA Cholesterol + AHA PREVENT | guideline | ACC/AHA | 2018/2023 | `guidelines/acc_aha_prevent_2023.pdf` | ⬜ cần thả PDF | ascvd_pce |
| 8 | USPSTF — sàng lọc lo âu người lớn (mức B) | guideline | USPSTF | 2023 | `guidelines/uspstf_anxiety_2023.pdf` | ⬜ cần thả PDF | gad7, phq9, audit_c |
| 9 | KDIGO CKD (CKD-EPI 2021 race-free) | guideline | KDIGO | 2024 | `guidelines/kdigo_ckd_2024.pdf` | ⬜ cần thả PDF | ckd_epi |
| 10 | AGS Beers Criteria® (bản chính thức) | guideline | AGS | 2023 | `guidelines/ags_beers_2023.pdf` | ⬜ cần thả PDF | beers |
| 11 | STOPP/START v3 | guideline | O'Mahony et al. | 2023 | `guidelines/stopp_start_v3_2023.pdf` | ⬜ cần thả PDF | stopp_start |
| 12 | ESC CVD trong ĐTĐ (SCORE2-Diabetes) | guideline | ESC | 2023 | `guidelines/esc_cvd_diabetes_2023.pdf` | ⬜ cần thả PDF | score2_diabetes |
| 13 | ESC Heart Failure; ACC/AHA/HFSA HF | guideline | ESC; ACC/AHA | 2021/2022 | `guidelines/esc_hf_2021.pdf` | ⬜ cần thả PDF | nyha |
| 14 | ESC ACS; ACC/AHA | guideline | ESC | 2023 | `guidelines/esc_acs_2023.pdf` | ⬜ cần thả PDF | timi |
| 15 | ESC CVD prevention (SCORE2) | guideline | ESC | 2021 | `guidelines/esc_cvd_prevention_2021.pdf` | ⬜ cần thả PDF | score2 |
| 16 | ESC Pulmonary Embolism; ACEP PE policy | guideline | ESC; ACEP | 2019 | `guidelines/esc_pe_2019.pdf` | ⬜ cần thả PDF | wells_pe, perc |
| 17 | NICE/ACCP/ASH VTE (Wells DVT) | guideline | NICE/ACCP/ASH | — | `guidelines/vte_dvt.pdf` | ⬜ cần thả PDF | wells_dvt |
| 18 | IDSA/ATS + BTS/NICE CAP (CURB-65) | guideline | IDSA/ATS; NICE | — | `guidelines/cap_idsa_nice.pdf` | ⬜ cần thả PDF | curb65 |
| 19 | IDSA pharyngitis; NICE sore throat | guideline | IDSA; NICE | — | `guidelines/pharyngitis.pdf` | ⬜ cần thả PDF | centor_mcisaac |
| 20 | AASLD/EASL cirrhosis & ALD | guideline | AASLD/EASL | — | `guidelines/aasld_easl_cirrhosis.pdf` | ⬜ cần thả PDF | child_pugh, maddrey_df |
| 21 | NICE CG141; ESGE UGIB (Blatchford) | guideline | NICE; ESGE | — | `guidelines/ugib_blatchford.pdf` | ⬜ cần thả PDF | blatchford |
| 22 | WHO viêm gan B/C (APRI) | guideline | WHO | — | `guidelines/who_hepatitis.pdf` | ⬜ cần thả PDF | apri |
| 23 | ADA Standards of Care; IDF (FINDRISC) | guideline | ADA; IDF | — | `guidelines/ada_idf.pdf` | ⬜ cần thả PDF | findrisc |
| 24 | RCP NEWS2; NICE NG51 sepsis | guideline | RCP; NICE | 2017 | `guidelines/news2_rcp.pdf` | ⬜ cần thả PDF | news2 |

## Hướng dẫn nhanh
- **Thả tài liệu**: lưu PDF/markdown vào `evidence/<loại>/`, đổi cột Trạng thái thành `✅ đã có`.
- **Protocol cục bộ** (phác đồ khoa/viện của bạn) đặt ở `evidence/protocols/` — ưu tiên cao nhất khi mâu thuẫn.
- Không lưu thông tin định danh bệnh nhân (PHI) vào kho dùng chung.
- Quy ước trích dẫn: xem `evidence/citation-format.md`.
