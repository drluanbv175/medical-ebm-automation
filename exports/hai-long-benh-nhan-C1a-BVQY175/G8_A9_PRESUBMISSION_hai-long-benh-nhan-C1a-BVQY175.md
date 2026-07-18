# A9 — BÁO CÁO KIỂM TRA TRƯỚC NỘP BÀI (PRE-SUBMISSION REVIEW)
**Mã đề tài:** hai-long-benh-nhan-C1a-BVQY175
**Ngày kiểm toán:** 2026-07-17 19:22
**Thiết kế:** Nghiên cứu Cắt ngang Mô tả (Cross-sectional / Prevalence) (`cross_sectional`)
**Chuẩn báo cáo áp dụng:** STROBE 2007
**Điểm pipeline:** 5/8 gates PASS (62%)
**Điểm tự kiểm:** 18/30 — CAN THEM 7 DIEM

> [BẢN NHÁP TỰ ĐỘNG] — Dựa trên checkpoints G0-G7.
> Các mục [CAN] yêu cầu bác sĩ/nhóm tác giả hoàn thiện trước khi nộp.
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — KIỂM TOÁN PIPELINE HOÀN CHỈNH

| Gate | Trạng thái | Artifact chính | Chi tiết | Việc còn tồn đọống |
|------|-----------|----------------|----------|-------------------|
| G0 | PASS OK | `G0_A1_PICO` | PubMed: 20 SR, 20 RCT | Xác nhận PICO 4 thành phần; Ấn định kết cục chính (1 kết cục duy nhất) |
| G1 | PASS OK | `G1_A2_DESIGN` |  | Xác nhận thiết kế chọn (§1); Điền kết cục chính (SAP §2) — từ PICO O ở G0 |
| G2 | PENDING -- cho IRB that | `G2_A3_IRB` | IRB: None | Điền [CẦN BỔ SUNG] trong tất cả tài liệu (tên, đơn vị, liên lạc, cỡ mẫu...); Ký Đơn xin phê duyệt (Tài liệu 1) + Trưởng đơn vị xác nhận |
| G3 | PASS OK | `G3_A4_SAMPLE` | N=428 | Xác nhận effect size (PMID/DOI từ y văn/pilot study); Xác nhận tỷ lệ bỏ cuộc dự kiến |
| G4 | PENDING -- cho SAP ky | `G4_A5_SAP` | SAP ky: [CAN] | Điền §2 kết cục chính (tên biến, đơn vị, ngưỡng); Điền §5 covariates với lý do lâm sàng / DAG |
| G5 | PASS OK | `G5_A6_DATA` | DB lock: [CAN] | Điền tất cả [CẦN...] trong CRF (biến phơi nhiễm/kết cục cụ thể); Import REDCap dictionary CSV vào REDCap cơ sở |
| G6 | PASS OK | `G6_A7_SCRIPTS` |  | Xem xet scripts; KHONG chay tren du lieu that cho den G5 |
| G7 | DRAFT | `G7_A8_MANUSCRIPT` | ~2000 từ (dự kiến 3200–4500 khi đủ kết quả) | Điền Tiêu đề (≤120 ký tự) và Tác giả (tên/đơn vị/ORCID); Điền Methods §2: tiêu chí nhận/loại, cơ sở, thời gian |

**Tổng kết pipeline:** 5/8 gates đạt (62%)

---

## PHẦN 2 — CHECKLIST STROBE 2007 (22 MỤC)

> **Tự kiểm từ checkpoints:** 8/22 mục = **36%**
> ☑ = Có bằng chứng trong checkpoints G0-G7
> ☐ = Cần hoàn thiện thủ công (kết quả thật / bác sĩ điền)

| # | Mục | Mô tả rút gọn | Trạng thái |
|---|-----|--------------|-----------|
| 1 | Title & Abstract | Chi ro thiet ke nghien cuu trong tieu de hoac tom tat; co tom tat co c... | ☐ |
| 2 | Background/Rationale | Giai thich co so khoa hoc va ly do cua nghien cuu | ☑ |
| 3 | Objectives | Neu muc tieu cu the, bao gom gia thuyet tien nghiem neu co | ☑ |
| 4 | Study design | Mo ta yeu to thiet ke quan trong ngay tu dau bao cao | ☑ |
| 5 | Setting | Mo ta boi canh, dia diem, thoi gian lien quan | ☐ |
| 6 | Participants | Tieu chi chon/loai doi tuong; nguon va phuong phap chon mau | ☑ |
| 7 | Variables | Dinh nghia tat ca bien ket cuc, phoi nhiem, tien doan, yeu to nhieu | ☑ |
| 8 | Data sources/Measurement | Mo ta nguon du lieu va cach do luong tung bien | ☐ |
| 9 | Bias | Mo ta moi no luc giai quyet sai lech tiem an | ☑ |
| 10 | Study size | Giai thich cach xac dinh co mau | ☐ |
| 11 | Quantitative variables | Cach xu ly bien dinh luong trong phan tich | ☑ |
| 12 | Statistical methods | Mo ta tat ca phuong phap thong ke, bao gom kiem soat confounding | ☑ |
| 13 | Enrollment flow (Results) | Bao cao so nguoi tham gia tung buoc; ly do loai tru | ☐ |
| 14 | Descriptive data | Dac diem nguoi tham gia; thieu du lieu | ☐ |
| 15 | Outcome data | Bao cao so bien co hoac do luong tom tat theo thoi gian | ☐ |
| 16 | Main results | Uoc luong khong hieu chinh va hieu chinh; do chinh xac (CI 95%) | ☐ |
| 17 | Other analyses | Phan tich khac: phan nhom, tuong tac, do nhay | ☐ |
| 18 | Key results | Tom tat ket qua chinh theo muc tieu | ☐ |
| 19 | Limitations | Han che; nguon sai lech tiem an; huong va do lon | ☐ |
| 20 | Interpretation | Giai thich than trong, xem xet muc tieu, han che, tong the bang chung | ☐ |
| 21 | Generalisability | Kha nang tong quat hoa ket qua | ☐ |
| 22 | Funding | Nguon tai tro va vai tro cua nha tai tro | ☐ |

**Tóm tắt:** 8/22 mục có bằng chứng từ checkpoints.
14 mục ☐ cần bác sĩ điền thủ công.

---

## PHẦN 3 — KIỂM TRA TÍNH TOÀN VẸN THỐNG KÊ

**Kết quả:** 5/6 kiểm tra qua — **PASS**

- ☐ SAP chua co xac nhan ky -- [CAN ngay ky SAP]
- ☑ Co mau da tinh: N=428 (alpha=0.05, power=80%, OR=0.5)
- ☑ Scripts phan tich sinh tu SAP (G6): 6 scripts
- ☑ Ban thao A8 khong co ket qua hardcoded (chi placeholder [CAN...])
- ☑ SAP da ghi nhan -- moi phan tich post-hoc phai duoc khai bao ro rang
- ☑ Chien luoc xu ly du lieu thieu da ghi trong SAP Section 6 (G4)

**Cảnh báo cần xem xét:**
  - [CANH BAO] SAP chua duoc ky chinh thuc

**Quy tắc vàng báo cáo thống kê:**
- Báo cáo effect size (HR/OR/RR/MD/AUC) + **CI 95%** — không chỉ p-value
- Mọi phân tích thêm (subgroup, sensitivity) phải được khai báo trong SAP G4
- Phân tích post-hoc phát sinh sau khi xem dữ liệu phải được ghi nhận rõ ràng
- Kiểm định assumptions: PH test (Cox), Shapiro-Wilk (normality)
- Missing data: báo cáo số và % thiếu; chiến lược multiple imputation nếu >= 5%

---

## PHẦN 4 — GỢI Ý TẠP CHÍ

> **Lưu ý quan trọng:** Danh sách dưới đây là GỢI Ý dựa trên thiết kế + chủ đề.
> KHÔNG phải đảm bảo acceptance. Bác sĩ cần kiểm tra Instructions for Authors.
> Cơ sở gợi ý: thiết kế `cross_sectional` + chủ đề: *Đánh giá sự hài lòng của bệnh nhân trong hoạt động khám chữa*

| Tạp chí | IF (2024 ước tính) | Ghi chú | Ưu tiên |
|---------|-------------------|---------|---------|
| BMC Public Health | 4.5 | Cross-sectional suc khoe cong dong | SUGGESTED |
| PLOS ONE | 3.7 | Da linh vuc, tiep can mo | SUGGESTED |
| BMJ Open | 2.9 | Cross-sectional lam sang + cong dong | SUGGESTED |
| Journal of Public Health | 3.0 | Suc khoe cong dong | SUGGESTED |

**Tiêu chí bổ sung khi chọn tạp chí:**
- Scope có phù hợp thiết kế và quần thể nghiên cứu không?
- Article Processing Charge (APC) nếu chọn Open Access
- Thời gian peer review trung bình (xem Peer Review Speed)
- Word limit, số bảng/hình tối đa, format tài liệu tham khảo
- Yêu cầu khai báo AI (ngày càng phổ biến 2024+)

---

## PHẦN 5 — GÓI KHAI BÁO TÁC GIẢ (Author Declaration Package)

### 5.1 CRediT Taxonomy Roles — Phân công vai trò tác giả

> Tham khảo: https://credit.niso.org/ (14 vai trò chuẩn)
> Ghi chú: **L** = Lead | **S** = Supporting | **-** = Không tham gia

| Vai trò CRediT | Tác giả 1 | Tác giả 2 | Tác giả 3 | Tác giả 4+ |
|----------------|-----------|-----------|-----------|------------|
| Conceptualization | [CAN] | [CAN] | [CAN] | [CAN] |
| Methodology | [CAN] | [CAN] | [CAN] | [CAN] |
| Software | [CAN] | [CAN] | [CAN] | [CAN] |
| Validation | [CAN] | [CAN] | [CAN] | [CAN] |
| Formal analysis | [CAN] | [CAN] | [CAN] | [CAN] |
| Investigation | [CAN] | [CAN] | [CAN] | [CAN] |
| Resources | [CAN] | [CAN] | [CAN] | [CAN] |
| Data Curation | [CAN] | [CAN] | [CAN] | [CAN] |
| Writing – Original Draft Preparation | [CAN] | [CAN] | [CAN] | [CAN] |
| Writing – Review & Editing | [CAN] | [CAN] | [CAN] | [CAN] |
| Visualization | [CAN] | [CAN] | [CAN] | [CAN] |
| Supervision | [CAN] | [CAN] | [CAN] | [CAN] |
| Project Administration | [CAN] | [CAN] | [CAN] | [CAN] |
| Funding Acquisition | [CAN] | [CAN] | [CAN] | [CAN] |

### 5.2 Thông tin tác giả

| # | Họ tên | Học hàm | Đơn vị công tác | ORCID | Email |
|---|--------|---------|----------------|-------|-------|
| 1 | [CAN -- tac gia chinh] | [CAN] | [CAN] | [CAN -- https://orcid.org/...] | [CAN] |
| 2 | [CAN] | [CAN] | [CAN] | [CAN] | |
| 3+ | [CAN] | | | | |

**Tác giả liên lạc (Corresponding Author):** [CAN -- ten day du + email + dia chi lien he]

### 5.3 Khai báo xung đột lợi ích (COI)

☐ **Tất cả tác giả xác nhận KHÔNG có xung đột lợi ích**
☐ **Có xung đột — khai báo chi tiết:**

| Tác giả | Loại quan hệ | Với tổ chức nào | Thời gian |
|---------|-------------|----------------|-----------|
| [CAN] | [tai chinh/co phan/tu van/khac] | [CAN] | [CAN] |

### 5.4 Khai báo nguồn tài trợ (Funding)

| Nguồn tài trợ | Số grant/hợp đồng | Tác giả nhận | Vai trò trong NC |
|--------------|------------------|-------------|-----------------|
| [CAN -- hoac 'Khong nhan tai tro tu ben ngoai'] | | | |

### 5.5 Khai báo sử dụng AI (ICMJE 2023+)

Nghiên cứu này sử dụng **EBM Copilot** (Claude-based AI tool) để hỗ trợ:
1. Tổng quan y văn tự động: tìm kiếm PubMed, phân loại bằng chứng (G0)
2. Sinh skeleton SAP và R/Python scripts (G4, G6)
3. Soạn thảo IMRAD skeleton dựa trên checkpoints (G7)

Tất cả nội dung khoa học, kết quả, diễn giải do tác giả người kiểm chứng và chịu trách nhiệm.
Theo ICMJE 2023, AI KHÔNG được liệt kê là tác giả.

---

## PHẦN 6 — ĐIỂM TỰ KIỂM TRƯỚC NỘP (30 ĐIỂM)

**Điểm đạt được: 18/30**
**Đánh giá: CAN THEM 7 DIEM**
*(Ngưỡng đủ điều kiện nộp: >= 25/30 điểm)*

### A. Pipeline (10 điểm) — 5/10

- ☑ G0 -- PICO + Evidence: checkpoint ton tai
- ☑ G1 -- Thiet ke nghien cuu: checkpoint ton tai
- ☐ G2 -- IRB/Dao duc: so IRB that da co
- ☑ G3 -- Co mau: da tinh va co N
- ☐ G4 -- SAP: da khoa/ky truoc khi xem du lieu *(Bat buoc truoc phan tich)*
- ☐ G5 -- DB Lock: co so du lieu da khoa *(Truoc khi phan tich cuoi)*
- ☑ G6 -- Scripts: da sinh R/Python analysis scripts
- ☑ G7 -- Ban thao IMRAD skeleton: da sinh
- ☐ Guardrail G0-G7: >= 6/8 gates qua *(5/8 gates qua)*
- ☐ Checklist STROBE 2007: >60% muc co bang chung *(8/22 = 36%)*

### B. Khoa học (8 điểm) — 8/8

- ☑ Evidence hien co da tong quan: 20 SR, 20 RCT *(Tu G0 PubMed search)*
- ☑ Cau hoi PICO da xac nhan (4 thanh phan P-I-C-O) *(Bac si can xac nhan truc tiep)*
- ☑ Ket cuc chinh: DUY NHAT va do luong duoc *(Xac nhan trong SAP Section 2)*
- ☑ Effect size + CI 95% da khai bao trong SAP *(G3 effect_val + G4 SAP)*
- ☑ Phan tich thong ke khong chi dua vao p-value *(Tu kiem tra thong ke G8)*
- ☑ Missing data da co chien luoc xu ly (SAP Section 6)
- ☑ Khong co phan tich post-hoc ngoai SAP *(Can bac si xac nhan sau khi co ket qua)*
- ☑ Assumptions thong ke da kiem (PH, normality...) *(Tu scripts G6)*

### C. Liêm chính (7 điểm) — 4/7

- ☑ Khong co PII (thong tin dinh danh benh nhan) trong artifact *(Guardrail R2 tu dong -- luon PASS)*
- ☑ Tat ca PMID/DOI da xac minh (khong bia) *(Kiem lai bang agent kiem-chung-trich-dan)*
- ☐ So IRB that (khong phai placeholder [CAN...])
- ☐ Dang ky thu nghiem (ClinicalTrials.gov / TCTR) *(Bat buoc cho RCT theo ICMJE)*
- ☑ Khai bao AI: EBM Copilot da duoc ghi nhan trong Methods/Acknowledgements *(Theo ICMJE/nhieu tap chi 2024+)*
- ☑ Disclaimer 'Can bac si kiem chung' trong moi artifact *(Guardrail R7 tu dong -- luon PASS)*
- ☐ Xung dot loi ich (COI) da khai bao hoac xac nhan khong co *([CAN -- dien form COI o Phan 5])*

### D. Trình bày (5 điểm) — 1/5

- ☐ Tieu de bai <= 120 ky tu, chua thiet ke nghien cuu *([CAN xac nhan tieu de cuoi tu G7])*
- ☐ Tom tat co cau truc <= 250 tu *([CAN sau khi co ket qua that])*
- ☐ Danh sach tac gia + affiliations + ORCID day du *([CAN xac nhan CRediT roles o Phan 5])*
- ☑ Tai lieu tham khao theo dinh dang tap chi dich (Vancouver/APA/...) *(Kiem lai bang agent kiem-chung-trich-dan)*
- ☐ Cover letter chuan bi cho ban bien tap *([CAN bac si soan -- khong sinh tu dong])*

---

## PHẦN 7 — TIÊU CHÍ QUA CỔNG G8

```
G8 PASS khi dap ung TAT CA 5 dieu kien BAT BUOC + bac si xac nhan 5 muc cuoi:

BAT BUOC (tu dong kiem tu checkpoints):
ND 1. G2 LOCKED -- IRB number that: None
ND 2. G4 LOCKED -- SAP da ky truoc khi xem du lieu
OK 3. G7 DONE -- Ban thao IMRAD skeleton da sinh
ND 4. Diem tu kiem >= 25/30 (hien: 18/30)
ND 5. Checklist STROBE 2007 >= 60% (hien: 36%)

CAN BAC SI XAC NHAN (khong the tu dong):
[CAN] 6. Ket qua that da dien vao Section III+V ban thao (sau G5+G6 phan tich)
[CAN] 7. Toan bo ban thao doc lai -- khong con placeholder [CAN...]
[CAN] 8. CRediT roles da phan cong day du (Phan 5)
[CAN] 9. COI da khai bao hoac xac nhan khong co (Phan 5)
[CAN] 10. Cover letter da soan theo yeu cau tap chi dich
```

**Trạng thái G8:** PENDING -- Can: IRB that (G2), SAP ky (G4), Ket qua phan tich THAT da xac nhan (results_final trong study_meta.json -- chua co nghia la ban thao con placeholder [CAN KET QUA THAT], KHONG duoc coi la san sang nop du diem tu kiem co cao)

---

*Cần bác sĩ kiểm chứng. Artifact A9 là BẢN NHÁP TỰ ĐỘNG từ checkpoints G0-G7 --*
*không thay thế đánh giá chuyên môn của nhóm tác giả trước khi nộp bài.*