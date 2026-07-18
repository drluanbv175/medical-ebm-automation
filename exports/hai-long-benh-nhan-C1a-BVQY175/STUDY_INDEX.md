# STUDY INDEX — hai-long-benh-nhan-C1a-BVQY175
> Cập nhật: 2026-07-18 · trạng thái đọc TRỰC TIẾP từ checkpoint hiện có (không phải cố định lúc scaffold)

## 20 File chuẩn

| # | File MD | File DOCX | Cổng | Artifact | Trạng thái |
|---|---------|----------|------|---------|------------|
| 00 | 00_Research_Intake_Feasibility_Audit.md | G0a_INTAKE_hai-long-benh-nhan-C1a-BVQY175.docx | G0 | `intake` | ✅ Xong |
| 01 | 01_Project_Charter.md | G1b_CHARTER_hai-long-benh-nhan-C1a-BVQY175.docx | G1 | `charter` | ✅ Xong |
| 02 | 02_Research_Question_and_PICO.md | G0b_PICO_hai-long-benh-nhan-C1a-BVQY175.docx | G0 | `pico` | ✅ Xong |
| 03 | 03_Evidence_Ledger.md | G0c_LITERATURE_hai-long-benh-nhan-C1a-BVQY175.docx | G0-G1 | `literature` | ✅ Xong |
| 04 | 04_Literature_Review.md | G0c_LITERATURE_hai-long-benh-nhan-C1a-BVQY175.docx | G0-G1 | `literature` | ✅ Xong |
| 05 | 05_Protocol.md | G1a_PROTOCOL_hai-long-benh-nhan-C1a-BVQY175.docx | G1 | `protocol` | ✅ Xong |
| 06 | 06_Ethics_Package_Checklist.md | G2_ETHICS_hai-long-benh-nhan-C1a-BVQY175.docx | G2 | `ethics` | ✅ Xong |
| 07 | 07_CRF_or_Questionnaire.md | G3c_CRF_hai-long-benh-nhan-C1a-BVQY175.docx | G3 | `crf` | ✅ Xong |
| 08 | 08_SOP_Data_Collection.md | G5a_SOP_hai-long-benh-nhan-C1a-BVQY175.docx | G5 | `sop` | ✅ Xong |
| 09 | 09_Data_Dictionary.md | G3b_VARIABLES_hai-long-benh-nhan-C1a-BVQY175.docx | G3-G5 | `variables` | ✅ Xong |
| 10 | 10_Sample_Size_Calculation.md | G3a_SAMPLESIZE_hai-long-benh-nhan-C1a-BVQY175.docx | G3 | `samplesize` | ✅ Xong |
| 11 | 11_Statistical_Analysis_Plan.md | G4_SAP_hai-long-benh-nhan-C1a-BVQY175.docx | G4 | `sap` | ✅ Xong |
| 12 | 12_Data_Cleaning_Plan.md | G5b_DMP_hai-long-benh-nhan-C1a-BVQY175.docx | G5 | `dmp` | ✅ Xong |
| 13 | 13_Data_Lock_Memo.md | G5c_DATALOCK_hai-long-benh-nhan-C1a-BVQY175.docx | G5-G6 | `datalock` | ✅ Xong |
| 14 | 14_Analysis_Syntax.md | G6a_ANALYSIS_hai-long-benh-nhan-C1a-BVQY175.docx | G6 | `analysis` | ✅ Xong |
| 15 | 15_Table_Shells.md | G4_SAP_hai-long-benh-nhan-C1a-BVQY175.docx | G4 | `sap` | ✅ Xong |
| 16 | 16_IMRAD_Manuscript.md | G7a_MANUSCRIPT_hai-long-benh-nhan-C1a-BVQY175.docx | G7 | `manuscript` | ✅ Xong |
| 17 | 17_Reporting_Checklist.md | G7b_CHECKLIST_hai-long-benh-nhan-C1a-BVQY175.docx | G7 | `checklist` | ✅ Xong |
| 18 | 18_Risk_Register.md | G1d_RISK_hai-long-benh-nhan-C1a-BVQY175.docx | G1+G7 | `risk` | ✅ Xong |
| 19 | 19_Research_Integrity_Audit.md | G7b_CHECKLIST_hai-long-benh-nhan-C1a-BVQY175.docx | G7-G9 | `checklist` | ✅ Xong |
| 20 | 20_Final_Readiness_Report.md | G9_READINESS_hai-long-benh-nhan-C1a-BVQY175.docx | G9 | `readiness` | ✅ Xong |

## Lệnh xuất .docx từng cổng

```bash
cd medical-ebm-automation
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G0
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G1
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --artifact ethics
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G3
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --artifact sap
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G5
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G6
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --gate G7
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --artifact review
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --artifact readiness
# Hoặc xuất tất cả cùng lúc:
python tools/gen_research_docx.py --study "hai-long-benh-nhan-C1a-BVQY175" --all
```

> Cần bác sĩ kiểm chứng. KHÔNG PII.
