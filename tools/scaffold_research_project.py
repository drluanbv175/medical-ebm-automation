"""
scaffold_research_project.py — Khởi tạo CẤU TRÚC THỬ MỤC 20-file chuẩn cho một đề tài mới.

Sinh cả file .md (nội dung placeholder) LẪN file .docx (template) cùng lúc.

Sử dụng:
    python tools/scaffold_research_project.py --study "PCOS-MET-2026"
    python tools/scaffold_research_project.py --study "My-Study-2026" --base-dir "exports"

Đầu ra:
    exports/<TEN-DE-TAI>/
    ├── 00_Research_Intake_Feasibility_Audit.md + .docx
    ├── 01_Project_Charter.md + .docx
    ├── ...
    └── 20_Final_Readiness_Report.md + .docx
    + STUDY_INDEX.md   (chỉ mục nội bộ, trạng thái từng file)
    + Makefile.md      (gợi ý lệnh cho từng cổng G)
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import gate_contract as _GC  # noqa: E402

# Import generator nếu có python-docx
try:
    from gen_research_docx import ARTIFACT_MAP, ResearchDocxGenerator
    HAS_DOCX = True
except ImportError:
    try:
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        from gen_research_docx import ARTIFACT_MAP, ResearchDocxGenerator
        HAS_DOCX = True
    except ImportError:
        HAS_DOCX = False
# ── 20 file theo §7 _CROSSWALK-NGHIEN-CUU.md ──────────────────────────────

SCAFFOLD_FILES = [
    ("00", "Research_Intake_Feasibility_Audit",
     "G0", "intake", "Research Intake & Feasibility Audit",
     """## Hướng dẫn điền

File này là sản phẩm BƯỚC 0 của `dieu-phoi-nghien-cuu`.
Điền theo template §5 `_CROSSWALK-NGHIEN-CUU.md`.

```
RESEARCH INTAKE & FEASIBILITY AUDIT — <tên đề tài> — <ngày>
[1] Vấn đề & khoảng trống ............ [NOT VERIFIED]
[2] Câu hỏi (PICO/PECO) .............. [NOT VERIFIED]
[3] Kết cục chính / phụ + giả thuyết . [NOT VERIFIED]
[4] Giả định loại thiết kế (1 dòng): ___
[5] Tính mới · ý nghĩa · khả thi (FINER) [NOT VERIFIED]
[6] Dữ liệu: chưa có / pilot / thật / thứ cấp / đã khóa
[7] Rủi ro đạo đức–dữ liệu: ___
[8] Cổng hiện tại: G__ — RESUME: không (đề tài mới)
[9] Sản phẩm cần tạo: 20 file theo scaffold
[10] 🚩 Cờ liêm chính: KHÔNG PII; KHÔNG bịa dữ liệu
KẾT: cổng kế tiếp = G0; cần chủ nhiệm: xác nhận PICO + kết cục chính
```

> Cần bác sĩ kiểm chứng.
"""),

    ("01", "Project_Charter",
     "G1", "charter", "Project Charter — Phạm vi & Quản trị",
     """## Nội dung cần điền

- Tên đề tài chính thức:
- Chủ nhiệm đề tài:
- Đơn vị thực hiện:
- Câu hỏi nghiên cứu (từ A1):
- Mục tiêu SMART (1–3 mục tiêu):
- Phạm vi không làm (out of scope):
- Cột mốc (milestone) chính: G0 · G1 · G2 · G3 · G4 · G5 · G6 · G7 · G8 · G9
- Governance (ai quyết định gì):
- Nguồn tài trợ / COI:

[CẦN CHỦ NHIỆM ẤN ĐỊNH — KHÔNG bịa số văn bản/quyết định]
"""),

    ("02", "Research_Question_and_PICO",
     "G0", "pico", "Câu hỏi nghiên cứu — PICO/PECO/FINER",
     """## Khung PICO / PECO

| Thành phần | Nội dung |
|-----------|---------|
| P — Population | [CẦN BỔ SUNG] |
| I/E — Intervention / Exposure | [CẦN BỔ SUNG] |
| C — Comparator | [CẦN BỔ SUNG] |
| O — Outcome chính | [CẦN BỔ SUNG] |
| O — Outcome phụ | [CẦN BỔ SUNG] |
| T — Time | [CẦN BỔ SUNG] |
| S — Setting | [CẦN BỔ SUNG] |

## Câu hỏi nghiên cứu (văn xuôi)
[CẦN BỔ SUNG]

## Giả thuyết H₀ / H₁
- H₀: [CẦN BỔ SUNG]
- H₁: [CẦN BỔ SUNG]

## FINER
- Feasible: [CẦN BỔ SUNG]
- Interesting: [CẦN BỔ SUNG]
- Novel: [CẦN BỔ SUNG]
- Ethical: [CẦN BỔ SUNG]
- Relevant: [CẦN BỔ SUNG]

> Cần bác sĩ kiểm chứng.
"""),

    ("03", "Evidence_Ledger",
     "G0-G1", "literature", "Evidence Ledger — Tổng quan bằng chứng",
     """## Chiến lược tìm kiếm

- Nguồn: PubMed · Cochrane · Europe PMC · guideline (WHO/ADA/ESC…)
- Từ khóa MeSH: [CẦN BỔ SUNG]
- Lọc: RCT · SR/meta-analysis · Cohort (2015–2026)
- Loại trừ: case report · editorials không data

## Bảng Evidence Ledger

| # | Tác giả (năm) | Tạp chí | Thiết kế | N | PICO | Hiệu ứng chính | RoB | GRADE | PMID/DOI |
|---|--------------|---------|---------|---|------|---------------|-----|-------|---------|
| 1 | [CẦN KIỂM CHỨNG] | | | | | | | | |

## Khoảng trống nghiên cứu (gap)
[CẦN BỔ SUNG sau tổng quan]

> CẢNH BÁO: KHÔNG liệt kê PMID/DOI chưa xác minh. Cần bác sĩ kiểm chứng.
"""),

    ("04", "Literature_Review",
     "G0-G1", "literature", "Tổng quan y văn — Cơ sở lý luận",
     """## 1. Đặt vấn đề & cơ sở lý luận
[CẦN BỔ SUNG]

## 2. Tổng quan tài liệu theo chủ đề
[CẦN BỔ SUNG]

## 3. Khoảng trống nghiên cứu
[CẦN BỔ SUNG]

## 4. Tài liệu tham khảo chính
(Vancouver format — ghi PMID/DOI thật, đã xác minh)
1. [CẦN KIỂM CHỨNG]

> Cần bác sĩ kiểm chứng.
"""),

    ("05", "Protocol",
     "G1", "protocol", "Đề cương & Thiết kế nghiên cứu",
     """## 1. Đặt vấn đề & cơ sở lý luận
[CẦN BỔ SUNG]

## 2. Mục tiêu nghiên cứu
[CẦN BỔ SUNG — đã chốt tại G0]

## 3. Thiết kế nghiên cứu
- Loại thiết kế: [CẦN BỔ SUNG]
- Đơn vị phân tích: [CẦN BỔ SUNG]
- Thời gian thực hiện: [CẦN BỔ SUNG]

## 4. Dân số nghiên cứu
- Quần thể đích: [CẦN BỔ SUNG]
- Tiêu chuẩn nhận: [CẦN BỔ SUNG]
- Tiêu chuẩn loại: [CẦN BỔ SUNG]

## 5. Cỡ mẫu (tóm tắt — chi tiết ở file 10)
[CẦN BỔ SUNG]

## 6. Can thiệp / Phơi nhiễm
[CẦN BỔ SUNG]

## 7. Thu thập dữ liệu & Kết cục
[CẦN BỔ SUNG]

## 8. Phân tích thống kê (tóm tắt — chi tiết ở file 11)
[CẦN BỔ SUNG]

## 9. Đạo đức
[CẦN BỔ SUNG]

## Tài liệu tham khảo
[CẦN KIỂM CHỨNG]

> Cần bác sĩ kiểm chứng.
"""),

    ("06", "Ethics_Package_Checklist",
     "G2", "ethics", "Hồ sơ đạo đức (IRB) + ICF",
     """⚠️ CỔNG CỨNG G2: File này chỉ là SOẠN THẢO.
Phê duyệt IRB thật phải do Hội đồng đạo đức bệnh viện/trường cấp.
AI KHÔNG tự phê duyệt đạo đức.

## Checklist hồ sơ IRB
- [ ] Đơn xin phê duyệt IRB
- [ ] Tóm tắt đề cương (lay summary)
- [ ] Phiếu đồng ý tham gia (ICF)
- [ ] Bộ công cụ thu thập (CRF)
- [ ] CV chủ nhiệm
- [ ] Khai báo xung đột lợi ích (COI)
- [ ] Phê duyệt IRB [🔴 CHƯA CÓ — do bác sĩ nộp]
- [ ] Đăng ký nghiên cứu (nếu can thiệp) [CẦN XÁC NHẬN]

## Dự thảo ICF
[CẦN SOẠN — mô tả nghiên cứu, quyền lợi/rủi ro, tính tự nguyện, bảo mật]

[CẦN CHỦ NHIỆM NỘP IRB — KHÔNG PII]

> Cần bác sĩ kiểm chứng.
"""),

    ("07", "CRF_or_Questionnaire",
     "G3", "crf", "Công cụ thu thập (CRF / Phiếu khảo sát)",
     """## Thông tin CRF / Phiếu khảo sát

- Loại công cụ: [CẦN BỔ SUNG — tự thiết kế / có sẵn / thích nghi]
- Tổng số item: [CẦN BỔ SUNG]
- Thang điểm: [CẦN BỔ SUNG]
- Phiên bản: Draft v1.0 — [CẦN PILOT]

## Cấu trúc phần
| Phần | Tiêu đề | Số item | Ghi chú |
|-----|---------|---------|---------|
| A | Thông tin nhân khẩu | [CẦN] | |
| B | Lâm sàng | [CẦN] | |
| C | Kết cục chính | [CẦN] | |

## Item (dự thảo)
[CẦN BỔ SUNG — ghi rõ nguồn từng item đã kiểm định]

[CẦN PILOT trước khi dùng — xem A16]

> Cần bác sĩ kiểm chứng. KHÔNG PII.
"""),

    ("08", "SOP_Data_Collection",
     "G5", "sop", "SOP Thu thập số liệu",
     """## 1. Mục đích & phạm vi
[CẦN BỔ SUNG]

## 2. Phân công nhân sự
[CẦN BỔ SUNG]

## 3. Quy trình thu thập từng bước
[CẦN BỔ SUNG]

## 4. Kiểm soát chất lượng trong thu thập
[CẦN BỔ SUNG]

## 5. Bảo mật & khử định danh
[CẦN BỔ SUNG — KHÔNG PII]

> Cần bác sĩ kiểm chứng.
"""),

    ("09", "Data_Dictionary",
     "G3-G5", "variables", "Biến số & Data Dictionary (Codebook)",
     """## Bảng Data Dictionary

| Tên biến | Nhãn | Loại | Dạng đo | Đơn vị/Thang | Thời điểm | Vai trò | Nguồn |
|---------|------|------|---------|--------------|---------|---------|------|
| id | Mã nghiên cứu | Số | Danh nghĩa | string | Nhập viện | Định danh | Hệ thống |
| [CẦN BỔ SUNG] | | | | | | | |

## Nhóm biến
- Biến phụ thuộc (kết cục chính): [CẦN BỔ SUNG]
- Biến độc lập chính: [CẦN BỔ SUNG]
- Biến gây nhiễu / điều chỉnh: [CẦN BỔ SUNG]
- Biến nền nhân khẩu: [CẦN BỔ SUNG]

> Cần bác sĩ kiểm chứng. KHÔNG PII.
"""),

    ("10", "Sample_Size_Calculation",
     "G3", "samplesize", "Tính cỡ mẫu & Power",
     """## Loại thiết kế & công thức
[CẦN BỔ SUNG]

## Tham số đầu vào
- Alpha (α): 0,05 (hai phía)
- Power (1-β): 0,80
- Effect size / tỷ lệ nền: [CẦN NGUỒN — PMID/DOI]
- Tỷ lệ bỏ cuộc: 10–15%

## Tính toán
n = [CẦN BỔ SUNG — KHÔNG bịa kết quả]

## Cỡ mẫu chính thức
n = [CẦN BỔ SUNG]

## Kiểm tra EPV (nếu đa biến)
EPV = sự kiện / số biến dự báo ≥ 10 [CẦN KIỂM]

## Tài liệu tham khảo effect size
[CẦN KIỂM CHỨNG PMID/DOI]

> Cần bác sĩ kiểm chứng.
"""),

    ("11", "Statistical_Analysis_Plan",
     "G4", "sap", "Kế hoạch phân tích thống kê (SAP) — 🔒 KHÓA TRƯỚC PHÂN TÍCH",
     """⚠️ CỔNG CỨNG G4: SAP PHẢI ĐƯỢC KHÓA TRƯỚC KHI MỞ DỮ LIỆU.
KHÔNG sửa kết cục chính / phương pháp sau khi đã xem dữ liệu.

## Quần thể phân tích
[CẦN BỔ SUNG — ITT / PP / Completers]

## Phân tích mô tả
[CẦN BỔ SUNG]

## Phân tích chính (Mục tiêu 1)
[CẦN BỔ SUNG]

## Phân tích đa biến (Mục tiêu 2)
[CẦN BỔ SUNG]
- Kiểm tra giả định:
  - Phân phối chuẩn / biến đổi biến:
  - VIF < 5 (đa cộng tuyến):
  - Hosmer-Lemeshow (nếu logistic):

## Xử lý dữ liệu thiếu
[CẦN BỔ SUNG — complete-case / MICE / single imputation]

## Phần mềm
[CẦN BỔ SUNG — SPSS/R/Stata + phiên bản]

## Khung bảng kết quả (Dummy Tables)
[CẦN BỔ SUNG]

## Xác nhận khóa SAP
| Người xác nhận | Chức danh | Ngày | Chữ ký |
|--------------|---------|------|--------|
| [CẦN CHỦ NHIỆM KÝ] | Chủ nhiệm | | |

> Cần bác sĩ kiểm chứng.
"""),

    ("12", "Data_Cleaning_Plan",
     "G5", "dmp", "Kế hoạch quản lý & làm sạch dữ liệu (DMP)",
     """## 1. Mô tả dữ liệu & định dạng
[CẦN BỔ SUNG]

## 2. Nhập liệu & kiểm tra kép
[CẦN BỔ SUNG]

## 3. Quy tắc kiểm tra (range · logic · consistency)
[CẦN BỔ SUNG]

## 4. Khử định danh
[CẦN BỔ SUNG — mã giả danh; KHÔNG PII]

## 5. Lưu trữ & bảo mật
[CẦN BỔ SUNG]

## 6. Quy trình khóa dữ liệu
[CẦN BỔ SUNG]

> Cần bác sĩ kiểm chứng. KHÔNG PII.
"""),

    ("13", "Data_Lock_Memo",
     "G5-G6", "datalock", "Biên bản khóa dữ liệu (Data Lock Memo)",
     """⚠️ File này điền SAU khi dữ liệu thật đã sẵn sàng.

## Biên bản khóa dữ liệu

- Tên đề tài:
- Ngày khóa dữ liệu: [CẦN CHỦ NHIỆM XÁC NHẬN]
- Số bản ghi: [CẦN]
- Tỷ lệ bỏ cuộc thực tế: [CẦN]
- Người khóa: [CẦN CHỦ NHIỆM KÝ]
- Cơ sở dữ liệu: [tên file / phiên bản]
- Hash checksum: [CẦN]

## Kiểm tra QC hậu-khóa
- [ ] Phân phối biến chính: bình thường/phân phối skewed
- [ ] Dữ liệu thiếu (missing): n/% theo biến
- [ ] Outlier: đã kiểm và xử lý theo kế hoạch
- [ ] Khớp dummy tables (A10): ✅ / 🔴

> KHÔNG sửa dữ liệu sau khi khóa — mọi correction phải ghi biên bản.
> Cần bác sĩ kiểm chứng.
"""),

    ("14", "Analysis_Syntax",
     "G6", "analysis", "Cú pháp phân tích thống kê (Tái lập)",
     """# Syntax phân tích — [TÊN ĐỀ TÀI]

# QUAN TRỌNG: Chạy SAU khi dữ liệu đã khóa (G5) theo đúng SAP đã khóa (G4).

# 0. Môi trường & phiên bản
# R version: [CẦN BỔ SUNG]
# Packages: [CẦN BỔ SUNG]
# Seed: [CẦN BỔ SUNG]

# 1. Tải dữ liệu (bản đã khóa)
# data <- read.csv("data_locked.csv")  # [CẦN BỔ SUNG]

# 2. Phân tích mô tả
# [CẦN BỔ SUNG theo SAP §Descriptive]

# 3. Phân tích chính
# [CẦN BỔ SUNG theo SAP §Primary]

# 4. Phân tích đa biến
# [CẦN BỔ SUNG theo SAP §Multivariable]

# 5. Xuất kết quả → Table_Shells (file 15)
# [CẦN BỔ SUNG]

# Cần bác sĩ kiểm chứng. KHÔNG PII.
"""),

    ("15", "Table_Shells",
     "G4", "sap", "Khung bảng kết quả (Dummy Tables / Shell Tables)",
     """## Bảng 1. Đặc điểm nền của đối tượng nghiên cứu (N = [CẦN])

| Biến | [Nhóm/Tổng] | [Nhóm 1] | [Nhóm 2] | p |
|------|------------|----------|----------|---|
| Tuổi, TB±ĐLC | | | | |
| Giới tính (nữ), n(%) | | | | |
| [CẦN BỔ SUNG] | | | | |

## Bảng 2. Tỷ lệ / Tần suất kết cục chính

| Biến | n | % | 95% CI |
|------|---|---|--------|
| [CẦN BỔ SUNG] | | | |

## Bảng 3. Phân tích đa biến — Yếu tố liên quan (nếu có)

| Biến | OR đơn biến (95% CI) | p | OR đa biến (95% CI) | p |
|------|---------------------|---|---------------------|---|
| [CẦN BỔ SUNG] | | | | |

> Điền số thực tế sau khi chạy syntax phân tích (file 14).
> Cần bác sĩ kiểm chứng.
"""),

    ("16", "IMRAD_Manuscript",
     "G7", "manuscript", "Bản thảo khoa học (IMRAD)",
     """# [TÊN ĐỀ TÀI — TIÊU ĐỀ TIẾNG ANH]

**Tác giả:** [CẦN BỔ SUNG]
**Đơn vị:** [CẦN BỔ SUNG]
**Từ khóa:** [CẦN BỔ SUNG — 5–8 từ khóa MeSH]

---

## ABSTRACT (≤250 words)
**Background:** [CẦN BỔ SUNG]
**Methods:** [CẦN BỔ SUNG]
**Results:** [CẦN BỔ SUNG]
**Conclusions:** [CẦN BỔ SUNG]

---

## INTRODUCTION
[CẦN BỔ SUNG]

## METHODS
### Study Design
[CẦN BỔ SUNG]

### Participants
[CẦN BỔ SUNG]

### Outcomes
[CẦN BỔ SUNG]

### Statistical Analysis
[CẦN BỔ SUNG]

## RESULTS
[CẦN BỔ SUNG — điền sau phân tích]

## DISCUSSION
[CẦN BỔ SUNG]

## CONCLUSIONS
[CẦN BỔ SUNG]

## DECLARATIONS
- **Funding:** [CẦN BỔ SUNG]
- **COI:** [CẦN KHAI BÁO]
- **AI Use:** Hỗ trợ soạn thảo bằng EBM Copilot (Claude); nội dung do tác giả kiểm chứng.
- **Author contributions:** [CẦN BỔ SUNG theo ICMJE CRediT]

## REFERENCES
[CẦN KIỂM CHỨNG PMID/DOI — Vancouver format]

> Cần bác sĩ kiểm chứng.
"""),

    ("17", "Reporting_Checklist",
     "G7", "checklist", "Checklist chuẩn báo cáo",
     """## Xác định chuẩn báo cáo phù hợp

| Loại thiết kế | Chuẩn báo cáo |
|--------------|---------------|
| RCT | CONSORT 2010 (+TIDieR nếu có can thiệp phức tạp) |
| Cohort/Case-control/Cắt ngang | STROBE 2007 |
| Tổng quan hệ thống/Meta-analysis | PRISMA 2020 |
| Protocol | SPIRIT 2013 |
| Chẩn đoán | STARD 2015 |
| Mô hình dự báo | TRIPOD+AI 2024 |
| Định tính | COREQ / SRQR |
| QI | SQUIRE 2.0 |

## Checklist đã điền

**Chuẩn áp dụng:** [CẦN XÁC ĐỊNH dựa trên thiết kế]

| # | Mục checklist | Trang/Đoạn | ✅/🟡/🔴 |
|---|--------------|-----------|---------|
| 1 | [CẦN BỔ SUNG] | | |

> Đính kèm checklist đã điền đầy đủ khi nộp bài.
> Cần bác sĩ kiểm chứng.
"""),

    ("18", "Risk_Register",
     "G1+G7", "risk", "Risk Register sống — Rủi ro & CAPA",
     """## Danh mục rủi ro đề tài

| # | Loại rủi ro | Mô tả | Xác suất | Tác động | Mức | Hành động ngừa | CAPA nếu xảy ra | Chủ nhân | Trạng thái |
|---|------------|-------|----------|----------|-----|---------------|----------------|---------|-----------|
| R1 | Tiến độ | Tuyển mộ chậm | Trung bình | Cao | High | Tăng điểm tuyển mộ | Điều chỉnh timeline | Chủ nhiệm | 🟡 Đang theo dõi |
| R2 | Dữ liệu | Dữ liệu thiếu > 20% | Thấp | Cao | High | Kiểm tra hàng tuần | Multiple imputation | DM Lead | 🟡 |
| R3 | Đạo đức | Trì hoãn IRB | Trung bình | Cao | High | Nộp sớm 3 tháng trước thu thập | Đề nghị thủ tục nhanh | Chủ nhiệm | 🟡 |
| R4 | Nhân sự | Nghiên cứu viên rời dự án | Thấp | Trung bình | Medium | Backup + đào tạo chéo | Tuyển thay | PM | 🟢 |

## Cập nhật định kỳ
Rà sau mỗi cổng G (G2, G4, G6, G9) — điền ngày cập nhật gần nhất: ___

> Cần bác sĩ kiểm chứng.
"""),

    ("19", "Research_Integrity_Audit",
     "G7-G9", "checklist", "Kiểm toán liêm chính nghiên cứu",
     """## 1. Kiểm toán completeness A1–A18

| Mã | Artifact | Trạng thái | Ghi chú |
|----|---------|-----------|---------|
| A1 | Câu hỏi + PICO | 🟡 | |
| A1b | Project Charter | 🟡 | |
| A2 | Protocol | 🟡 | |
| A2b | Evidence Ledger | 🟡 | |
| A3 | Hồ sơ IRB + ICF | 🔴 | Cần phê duyệt thật |
| A4 | Đăng ký nghiên cứu | 🔴 | Nếu can thiệp |
| A5 | Cỡ mẫu + power | 🟡 | |
| A6 | Biến số + codebook | 🟡 | |
| A7 | CRF | 🟡 | |
| A8 | SAP (khóa) | 🔴 | Chưa khóa |
| A9 | DMP vận hành | 🟡 | |
| A9b | Data Lock Memo | 🔴 | Chưa tới G5 |
| A10 | Dummy Tables | 🟡 | |
| A11 | Chuẩn báo cáo | 🟡 | |
| A12 | Kiểm chứng trích dẫn | 🔴 | Cần chạy kiem-chung-trich-dan |
| A13 | Nhân lực·tiến độ·kinh phí | 🟡 | |
| A13b | Risk Register | 🟡 | |
| A14 | COI·tài trợ·khai báo AI | 🔴 | Cần chủ nhiệm khai báo |
| A15 | Bình duyệt nội bộ | 🔴 | Cần binh-duyet |
| A16 | Pilot công cụ | 🔴 | Cần thực hiện |
| A17a | SOP thu thập | 🟡 | |
| A17b | Syntax tái lập | 🔴 | Cần sau G6 |
| A18 | Hồ sơ nghiệm thu | 🔴 | Cần G9 |

## 2. Khai báo liêm chính
- COI: [CẦN CHỦ NHIỆM KHAI BÁO]
- Tài trợ: [CẦN CHỦ NHIỆM KHAI BÁO]
- Đóng góp tác giả (ICMJE CRediT): [CẦN CHỦ NHIỆM KHAI BÁO]
- Dùng AI: Có — EBM Copilot hỗ trợ soạn thảo; tác giả kiểm chứng

> Cần bác sĩ kiểm chứng.
"""),

    ("20", "Final_Readiness_Report",
     "G9", "readiness", "Báo cáo sẵn sàng nghiệm thu (Final Readiness Report)",
     """⚠️ CỔNG CỨNG G9 — Báo cáo này điền sau khi đã xong G7/G8.

## KẾT LUẬN NGHIỆM THU: [NOT READY — điền sau khi hoàn thiện]

## 14 Điểm Definition of Done

| # | Điểm DoD | Trạng thái | Ghi chú |
|---|---------|-----------|---------|
| 1 | Câu hỏi rõ + PICO | 🔴 | |
| 2 | Loại thiết kế phù hợp | 🔴 | |
| 3 | Đăng ký/đạo đức (G2) đã đóng | 🔴 | Cần số phê duyệt thật |
| 4 | Cỡ mẫu có nguồn effect size | 🔴 | |
| 5 | SAP đã khóa trước phân tích | 🔴 | |
| 6 | Dữ liệu khóa + QC sạch | 🔴 | |
| 7 | Phân tích đúng SAP | 🔴 | |
| 8 | Kết luận không vượt dữ liệu | 🔴 | |
| 9 | Chuẩn báo cáo đúng thiết kế | 🔴 | |
| 10 | Trích dẫn kiểm chứng (A12) | 🔴 | |
| 11 | Đề cương đồng bộ chéo | 🔴 | |
| 12 | Công cụ đã pilot (A16) | 🔴 | |
| 13 | SOP + syntax tái lập (A17) | 🔴 | |
| 14 | COI/tài trợ/AI khai báo (A14) | 🔴 | |

## Gap Register + CAPA
| # | Khoảng trống | Mức | Agent | CAPA | Hạn |
|---|-------------|-----|-------|------|-----|
| | [CẦN BỔ SUNG] | | | | |

> Cần bác sĩ kiểm chứng.
"""),
]


def _last_gate_token(gate_field: str) -> str:
    """Từ chuỗi cổng của 1 hàng SCAFFOLD_FILES (vd "G0-G1", "G1+G7", "G7-G9")
    lấy cổng SAU CÙNG (số lớn nhất) — coi artifact "xong" khi cổng đó có checkpoint.
    Chuỗi 1 cổng đơn (vd "G3") trả về chính nó."""
    tokens = re.findall(r"G(\d+)", gate_field)
    if not tokens:
        return gate_field
    return f"G{max(int(t) for t in tokens)}"


def _row_status(gate_field: str, out_dir: Path) -> str:
    """Trạng thái THẬT của 1 hàng STUDY_INDEX dựa trên checkpoint đã có — không
    suy từ tên file .md/.docx (những file đó có thể là scaffold placeholder
    chưa từng được điền lại)."""
    gate = _last_gate_token(gate_field)
    cp_path = out_dir / f"{gate}_checkpoint.json"
    if not cp_path.exists():
        return "🔴 Chưa có"
    try:
        cp = json.loads(cp_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return "🔴 Chưa có"
    if _GC.is_blocked(cp):
        return "🚧 Dự thảo — chờ input"
    return "✅ Xong"


def _index_table_lines(study_slug: str, out_dir: Path) -> list:
    lines = [
        "| # | File MD | File DOCX | Cổng | Artifact | Trạng thái |\n",
        "|---|---------|----------|------|---------|------------|\n",
    ]
    for num, fname, gate, artifact_key, _title, _body in SCAFFOLD_FILES:
        md_f = f"{num}_{fname}.md"
        docx_f = (f"{ARTIFACT_MAP.get(artifact_key, ('', '', ''))[0]}_"
                  f"{artifact_key.upper()}_{study_slug}.docx"
                  if artifact_key in ARTIFACT_MAP else "—")
        status = _row_status(gate, out_dir) if out_dir.exists() else "🔴 Chưa có"
        lines.append(f"| {num} | {md_f} | {docx_f} | {gate} | `{artifact_key}` | {status} |\n")
    return lines


def regenerate_study_index(study_name: str, out_dir: Path, study_slug: str | None = None) -> Path:
    """Sinh LẠI STUDY_INDEX.md với trạng thái THẬT (đọc checkpoint hiện có) —
    thay vì hàng cố định "🔴 Mới" chỉ đúng lúc scaffold. Gọi lại sau mỗi lần
    march (đặc biệt từ `run_g10_assemble.py`, bước capstone chạy sau mỗi lần
    tiến cổng) để chỉ mục KHÔNG bị lạc hậu so với tiến độ thật. CHỈ ĐỌC
    checkpoint, không ghi/sửa gì khác.
    """
    study_slug = study_slug or study_name.replace(" ", "-")
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# STUDY INDEX — {study_name}\n",
        f"> Cập nhật: {today} · trạng thái đọc TRỰC TIẾP từ checkpoint hiện có "
        f"(không phải cố định lúc scaffold)\n\n",
        "## 20 File chuẩn\n\n",
    ]
    lines += _index_table_lines(study_slug, out_dir)
    lines += [
        "\n## Lệnh xuất .docx từng cổng\n\n",
        "```bash\n",
        "cd medical-ebm-automation\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G0\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G1\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --artifact ethics\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G3\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --artifact sap\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G5\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G6\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --gate G7\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --artifact review\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --artifact readiness\n",
        "# Hoặc xuất tất cả cùng lúc:\n",
        f"python tools/gen_research_docx.py --study \"{study_name}\" --all\n",
        "```\n",
        "\n> Cần bác sĩ kiểm chứng. KHÔNG PII.\n",
    ]
    out_path = out_dir / "STUDY_INDEX.md"
    out_path.write_text("".join(lines), encoding="utf-8")
    return out_path


def scaffold(study_name: str, base_dir: str = None, with_docx: bool = True):
    """Tạo thư mục và 20 file scaffold cho đề tài mới."""
    study_slug = study_name.replace(" ", "-")
    today = datetime.now().strftime("%Y-%m-%d")

    if base_dir:
        out = Path(base_dir) / study_slug
    else:
        out = Path(__file__).parent.parent / "exports" / study_slug

    out.mkdir(parents=True, exist_ok=True)

    created_md  = []
    created_docx = []

    gen = None
    if with_docx and HAS_DOCX:
        gen = ResearchDocxGenerator(study_name, str(out))

    for num, fname, gate, artifact_key, title, body in SCAFFOLD_FILES:
        # ── Markdown file ────────────────────────────────────────────────
        md_fname = f"{num}_{fname}.md"
        md_path  = out / md_fname

        header = (
            f"# {num}. {title.upper()}\n\n"
            f"> **Đề tài:** {study_name}  |  **Cổng:** {gate}  |  "
            f"**Tạo:** {today}\n\n"
            f"---\n\n"
        )
        md_path.write_text(header + body, encoding="utf-8")
        created_md.append(md_fname)
        print(f"  [MD ] {md_fname}")

        # ── .docx file ───────────────────────────────────────────────────
        if gen and artifact_key in ARTIFACT_MAP:
            try:
                path = gen.generate(artifact_key)
                created_docx.append(Path(path).name)
                print(f"  [DOCX] {Path(path).name}")
            except Exception as e:
                print(f"  [WARN] Không sinh .docx cho {artifact_key}: {e}")

    # ── STUDY_INDEX.md — trạng thái đọc THẬT từ checkpoint (rỗng lúc scaffold
    # mới nên mọi hàng ra 🔴, y hệt hành vi cũ; nhưng dùng lại được để LÀM MỚI
    # sau khi pipeline chạy, xem regenerate_study_index()) ──────────────────
    regenerate_study_index(study_name, out, study_slug)
    print("  [IDX] STUDY_INDEX.md")

    # ── study_meta.json — PIN durable (gate_params + cờ bằng-chứng-đời-thực) ──
    # File này là NƠI bác sĩ pin effect size (G3), thiết kế, và các cờ đời-thực
    # (IRB/SAP-lock/data-lock/integrity). run_pipeline đọc nó để CHẠY LẠI không
    # mất input. Tạo non-destructive (không đè nếu bác sĩ đã điền).
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parent))
        import gate_contract as _GC
        _GC.ensure_study_meta(out, seed={"title": study_name, "topic": study_name})
        print("  [META] study_meta.json (PIN gate_params + cờ đời-thực)")
    except Exception as _e:  # noqa: BLE001
        print(f"  [WARN] Không tạo study_meta.json: {_e}")

    # ── Tóm tắt ────────────────────────────────────────────────────────
    print(f"\n✅ Scaffold hoàn tất: {out}")
    print(f"   {len(created_md)} file .md  |  {len(created_docx)} file .docx")
    print("\nBước tiếp:")
    print("  1. Mở STUDY_INDEX.md — xem trạng thái tổng")
    print(f"  2. Chạy dieu-phoi-nghien-cuu cho đề tài '{study_name}'")
    print("  3. Sau mỗi cổng G: chạy lệnh docx tương ứng (xem STUDY_INDEX.md)")

    return str(out)


def main():
    parser = argparse.ArgumentParser(
        description="Khởi tạo cấu trúc 20-file cho đề tài nghiên cứu y khoa")
    parser.add_argument("--study",   required=True, help="Tên đề tài")
    parser.add_argument("--base-dir", help="Thư mục gốc (mặc định: exports/)")
    parser.add_argument("--no-docx", action="store_true",
                        help="Bỏ qua tạo file .docx (chỉ tạo .md)")
    args = parser.parse_args()

    print(f"\n{'='*60}")
    print(f"  SCAFFOLD — {args.study}")
    print(f"{'='*60}\n")

    if args.no_docx:
        print("[INFO] Chỉ tạo file .md (--no-docx)\n")
    elif not HAS_DOCX:
        print("[CẢNH BÁO] python-docx chưa cài — chỉ tạo .md\n")
        print("  Cài: pip install python-docx\n")

    scaffold(
        study_name=args.study,
        base_dir=args.base_dir,
        with_docx=(not args.no_docx and HAS_DOCX),
    )


if __name__ == "__main__":
    main()
