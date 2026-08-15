# A1 — CÂU HỎI NGHIÊN CỨU & PICO | hai-long-benh-nhan-C1a-BVQY175
> Tạo tự động: 2026-07-31 20:39 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (§3) và chỉ ra khoảng trống (§5) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study hai-long-benh-nhan-C1a-BVQY175`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)

**Topic đề tài:** Sự hài lòng của bệnh nhân trong hoạt động khám chữa bệnh tại Khoa Khám bệnh theo yêu cầu, bệnh viện quân y tuyến cuối
**Truy vấn PubMed:** `patient satisfaction outpatient department Vietnam hospital`

```
═══════════════════════════════════════════════════════
CÂU HỎI NGHIÊN CỨU (dự thảo — bác sĩ điều chỉnh):
"Ở [P — điền], [I/E — điền] có liên quan đến / dẫn đến
 [C — điền] về [O — điền] không?"
═══════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ P — POPULATION (Dân số/Bệnh nhân)                      │
│   Đặc điểm: [suy ra từ topic: "Sự hài lòng của bệnh nhân trong hoạt..."]          │
│   Tiêu chí chọn: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Tiêu chí loại: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Bối cảnh: Ngoại trú / Nội trú / Cộng đồng           │
├─────────────────────────────────────────────────────────┤
│ I — INTERVENTION / E — EXPOSURE                         │
│   Can thiệp/Phơi nhiễm: [suy ra từ topic]             │
│   Liều/thời gian: [CẦN BÁC SĨ XÁC NHẬN]              │
├─────────────────────────────────────────────────────────┤
│ C — COMPARISON (So sánh)                               │
│   Từ evidence tìm được: [xem §3 bên dưới]             │
│   [CẦN BÁC SĨ XÁC NHẬN]                              │
├─────────────────────────────────────────────────────────┤
│ O — OUTCOMES (Kết cục)                                 │
│   Kết cục CHÍNH — CHỈ ĐƯỢC 1:                          │
│     Tên kết cục: [CẦN BÁC SĨ ẤN ĐỊNH]                │
│     Định nghĩa/công cụ đo: [CẦN BÁC SĨ ẤN ĐỊNH]      │
│     Đơn vị/thang đo: [CẦN BÁC SĨ ẤN ĐỊNH]            │
│     Thời điểm đo: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 1: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Kết cục PHỤ 2: [CẦN BÁC SĨ ẤN ĐỊNH]               │
│   Căn cứ chọn kết cục: PMIDs bên dưới                 │
└─────────────────────────────────────────────────────────┘
```

> Ba dòng "định nghĩa · đơn vị · thời điểm" của kết cục chính là bắt buộc: cổng G1
> sẽ CHẶN nếu thiếu, và cỡ mẫu ở G3 không tính được nếu không biết thang đo.

**Loại câu hỏi:** ☐ Điều trị  ☐ Chẩn đoán  ☐ Tiên lượng  ☐ Tác hại  ☐ Mô tả
**Loại kiểm định:** ☐ Superiority  ☐ Non-inferiority  ☐ Equivalence  ☐ Mô tả

> Ô tick ở trên chỉ để bác sĩ suy nghĩ. Giá trị được HỆ ĐỌC nằm ở
> `study_meta.json → gate_params.G0.question_type` và `.test_type` — ô tick trong
> file .md này không có mã nào đọc lại (đã kiểm 2026-07-28).

---

## PHẦN 1b — GIẢ THUYẾT (THÀNH PHẦN 3 của doctrine — trước đây THIẾU HẲN)

```
┌─────────────────────────────────────────────────────────────┐
│ H0 (giả thuyết vô hiệu): [CẦN BÁC SĨ ẤN ĐỊNH]            │
│ H1 (giả thuyết nghiên cứu): [CẦN BÁC SĨ ẤN ĐỊNH]         │
│ Chiều kỳ vọng: ☐ tăng ☐ giảm ☐ liên quan dương ☐ âm       │
│   Căn cứ chiều kỳ vọng: PMID/DOI ___ hoặc [CẦN KIỂM CHỨNG]│
│ Nghiên cứu MÔ TẢ thuần: ☐ đúng → không cần H0/H1           │
└─────────────────────────────────────────────────────────────┘
```
> Điền vào `gate_params.G0.hypothesis_h0/hypothesis_h1/expected_direction`.
> Không có giả thuyết định trước thì mọi kiểm định ở G6 đều là thăm dò.

---

## PHẦN 2 — KIỂM FINER (tự động + bác sĩ hoàn thiện)

```
┌─────────────────────────────────────────────────────────────┐
│ F — FEASIBLE (Khả thi) [CẦN BÁC SĨ XÁC NHẬN]            │
│   Cỡ mẫu đủ trong thời gian dự kiến? [CẦN XÁC NHẬN]     │
│   Nguồn lực đủ? [CẦN XÁC NHẬN]                           │
│   Chuyên môn nhóm NC phù hợp? [CẦN XÁC NHẬN]            │
├─────────────────────────────────────────────────────────────┤
│ I — INTERESTING (Có giá trị khoa học)                      │
│   Evidence level hiện có: CÓ NỀN QUAN SÁT — ~12 NC quan sát, chưa có RCT/SR
│   → Đã có nhiều nghiên cứu quan sát: KHÔNG phải khoảng trống. Cần đọc kỹ nhóm này trước khi biện minh tính mới; hướng khả dĩ là SR/MA tổng hợp chúng, hoặc nghiên cứu ở quần thể/bối cảnh chưa được phủ.
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 0 | RCT: 0 | Guideline: 0 | Quan sát: 12
│   (số hit THẬT từ PubMed)
│   Bằng chứng mới nhất: Không xác định
│   Khoảng trống:
│     • Chưa có systematic review tổng hợp bằng chứng
│     • Chưa có RCT kiểm định hiệu quả can thiệp
│     • Chưa có guideline/khuyến cáo chính thức cho vấn đề này
│     • Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát
│
├─────────────────────────────────────────────────────────────┤
│ E — ETHICAL (Đạo đức) [CẦN BÁC SĨ XÁC NHẬN]             │
│   Rủi ro người tham gia: ☐ Tối thiểu  ☐ Nhỏ  ☐ Lớn     │
│   Cần ICF: ☐ Có  ☐ Không                                 │
│   Nhóm dễ tổn thương: ☐ Có (biện pháp: ___)  ☐ Không    │
│   Cần đăng ký trước: ☐ Có (can thiệp)  ☐ Không           │
├─────────────────────────────────────────────────────────────┤
│ R — RELEVANT (Liên quan thực hành)                         │
│   Ảnh hưởng thực hành lâm sàng: [CẦN BÁC SĨ XÁC NHẬN] │
│   Phù hợp ưu tiên đơn vị/quốc gia: [CẦN XÁC NHẬN]      │
└─────────────────────────────────────────────────────────────┘
Đánh giá FINER: ☐ ĐẠT  ☐ CẦN SỬA [điểm: ___]  ☐ KHÔNG KHẢ THI
```

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-07-31)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities. PMIDs đã được xác minh.
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.

### 3.1 Systematic Review / Meta-analysis — ~0 hit (số hit thật); hiển thị 0/0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.2 Randomized Controlled Trials — ~0 hit (số hit thật); hiển thị 0/0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); hiển thị 0/0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Kết luận "chưa có guideline" ở §5 chỉ đúng trong phạm vi PubMed.

### 3.5 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang) — ~12 hit (số hit thật); hiển thị 5/12 bài đã tải
  1. Implementation and evaluation of clinical pharmacy services in elderly outpatients with poorly contr
     Dong PTX, Nguyen TT, Duong HTT, Nguyen TTT, Le AV (2025). BMC health services research
     PMID: 41162961 | URL: https://pubmed.ncbi.nlm.nih.gov/41162961/
  2. Counseling Preferences Among Patients With Type 2 Diabetes: Implications for Personalized Care.
     Nguyen TNP, Thi CN, Phuong TPT, Ngoc QN, Pham HT (2025). Journal of diabetes research
     PMID: 40771771 | URL: https://pubmed.ncbi.nlm.nih.gov/40771771/
  3. Temporal Trends in Patient Choice of Outpatient Care Provider Among Vietnam's Insured Rural Resident
     Sepehri A, Minh KN, Vu PH, Pham TM (2025). The International journal of health planning and management
     PMID: 40726017 | URL: https://pubmed.ncbi.nlm.nih.gov/40726017/
  4. Patient experience with cancer care in low- and middle-income Asian countries: a cross-sectional stu
     Andres EB, Poco L, Balasubramanian I, Chaudry I, Hapuarachchi T (2025). BMJ global health
     PMID: 40623792 | URL: https://pubmed.ncbi.nlm.nih.gov/40623792/
  5. An international observational study assessing conservative management in hemorrhoidal disease: resu
     Godeberge P, Csiki Z, Zakharash M, Opot EN, Shelygin YA (2024). Journal of comparative effectiveness research
     PMID: 39132755 | URL: https://pubmed.ncbi.nlm.nih.gov/39132755/
  ... và 7 bài khác

> ⚠️ Con số ~12 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (đo thật: ~13% ở một số chủ đề). Dùng để biết "lĩnh vực này đã có nền quan sát
> hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần.

### 3.4 SR/MA · RCT · guideline gần đây 2021-2026 — ~0 hit (số hit thật); hiển thị 0/0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  → Không có hồ sơ đăng ký nào khớp truy vấn

> **Đã tra ngày 2026-07-31: ~0 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP

**Tổng PMIDs thật tìm được:** 12 bài từ 12 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** CÓ NỀN QUAN SÁT — ~12 NC quan sát, chưa có RCT/SR

**Khoảng trống nghiên cứu cụ thể:**
• Chưa có systematic review tổng hợp bằng chứng
• Chưa có RCT kiểm định hiệu quả can thiệp
• Chưa có guideline/khuyến cáo chính thức cho vấn đề này
• Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát

**Đối chiếu đăng ký:** ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn (chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   RCT ngẫu nhiên có đối chứng HOẶC Cohort tiến cứu
│   Lý do: suy từ 0 SR/MA · 0 RCT · 12 quan sát
│   Hạn chế: [CẦN BÁC SĨ NÊU — khả thi tại đơn vị?]         │
├─────────────────────────────────────────────────────────────┤
│ Ưu tiên 2 (phương án thay thế): [CẦN BÁC SĨ ẤN ĐỊNH]     │
│   Lý do: [CẦN BÁC SĨ NÊU]                                 │
│   Hạn chế: [CẦN BÁC SĨ NÊU]                               │
└─────────────────────────────────────────────────────────────┘
```

**Chuẩn báo cáo DỰ KIẾN** (theo ưu tiên 1; G1 chốt lại theo thiết kế thật):
- Mã thiết kế suy được: `rct`
- Chuẩn báo cáo: CONSORT 2025
- Chuẩn đề cương: SPIRIT 2025; đăng ký trial TRƯỚC tuyển mẫu; ICH-GCP nếu áp dụng

*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G0

Hệ chấm bằng `tools/g0_quality_gate.py`; báo cáo đầy đủ ở `G0_QUALITY_REPORT.md`.
**Ô tick dưới đây chỉ để đọc — nơi hệ ĐỌC THẬT là `study_meta.json → gate_params.G0`.**

```
PHẦN MÁY LÀM ĐƯỢC (tự động)
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy (12 bài tải về / 12 PMID duy nhất)
☑ Khoảng trống nghiên cứu đã phân tích
☑ Đã tra đăng ký nghiên cứu đang tiến hành

PHẦN CHỈ BÁC SĨ QUYẾT ĐƯỢC (hệ KHÔNG tự điền)
☐ PICO/PECO 4 thành phần            → gate_params.G0.population/intervention/comparison/outcomes
☐ Kết cục CHÍNH duy nhất + thang đo + thời điểm → .primary_outcome{,_measure,_timepoint}
☐ Giả thuyết H0/H1 + chiều kỳ vọng  → .hypothesis_h0/.hypothesis_h1/.expected_direction
☐ Loại câu hỏi + loại kiểm định     → .question_type/.test_type
☐ FINER 5 tiêu chí                  → .finer_feasible/_interesting/_novel/_ethical/_relevant
☐ Đã đọc lại bằng chứng + biện minh tính mới → .evidence_reviewed_confirmed/.novelty_justification
☐ Chốt PICO (vai trò + thời điểm)   → .pico_confirmed/.reviewed_by_role/.reviewed_at
```

**Hành động tiếp theo của bác sĩ:**
1. Đọc danh sách bài ở §3 (click PMID) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study hai-long-benh-nhan-C1a-BVQY175` để xem còn thiếu gì
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
