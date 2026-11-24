# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-CAT-NGANG-PLS-SEM
> Tạo tự động: 2026-11-23 19:32 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-CAT-NGANG-PLS-SEM`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Giao tiếp bác sĩ – người bệnh, hiểu biết về bệnh, niềm tin vào điều trị và tuân thủ điều trị ở người tăng huyết áp điều trị ngoại trú: nghiên cứu cắt ngang phân tích bằng mô hình PLS-SEM
**Truy vấn PubMed:** `(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])`

```
═══════════════════════════════════════════════════════
CÂU HỎI NGHIÊN CỨU (dự thảo — bác sĩ điều chỉnh):
"Ở [P — điền], [I/E — điền] có liên quan đến / dẫn đến
 [C — điền] về [O — điền] không?"
═══════════════════════════════════════════════════════

┌─────────────────────────────────────────────────────────┐
│ P — POPULATION (Dân số/Bệnh nhân)                      │
│   Đặc điểm: [CẦN BÁC SĨ VIẾT — hệ KHÔNG suy từ topic]    │
│   Tiêu chí chọn: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Tiêu chí loại: [CẦN BÁC SĨ XÁC NHẬN]               │
│   Bối cảnh: Ngoại trú / Nội trú / Cộng đồng           │
├─────────────────────────────────────────────────────────┤
│ I — INTERVENTION / E — EXPOSURE                         │
│   Can thiệp/Phơi nhiễm: [CẦN BÁC SĨ VIẾT]             │
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
│   Evidence level hiện có: YẾU — mới 1 RCT (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)
│   → Cơ hội tốt cho RCT mới hoặc cohort tiến cứu
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 0 | RCT: 1 | Guideline: 0 | Quan sát: 11
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy SR/MA trong PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
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

> Nơi hệ ĐỌC: `gate_params.G0.finer_feasible/_interesting/_novel/_ethical/_relevant` — MỖI khoá một câu
> «ĐẠT — <lý do>» (cờ true trơn KHÔNG đủ — G0-HUMAN-05). F và E chỉ PI đánh giá được.

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-CAT-NGANG-PLS-SEM.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-23)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-CAT-NGANG-PLS-SEM.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.2 Randomized Controlled Trials — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Factors influencing health behaviour, blood pressure control, and disability in hypertensive ischaemic stroke patients after a comprehensive reminder intervention.
     Zhang XP, Pan JH, Wan LH, Liu ZY, Mo MM (2020). Journal of advanced nursing
     PMID: 32128865 | URL: https://pubmed.ncbi.nlm.nih.gov/32128865/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~11 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Factors associated with COVID-19 preventive behaviors among patients with hypertension and type 2 diabetes in southern Iran: a structural equation modeling study.
     Shamsnia SA, Mobasheri N, Kaveh MH, Nazari M, Karimi M (2026). BMC public health
     PMID: 42337710 | URL: https://pubmed.ncbi.nlm.nih.gov/42337710/
  2. Predicting Medication Adherence Using Psychosocial Factors: A Comprehensive Analysis through Regression and Path Models.
     Saggah AMA (2026). La Clinica terapeutica
     PMID: 42047149 | URL: https://pubmed.ncbi.nlm.nih.gov/42047149/
  3. Exploring the impact of three-dimensional patient satisfaction structure on adherence to medication and non-pharmaceutical treatment: a cross-sectional study among patients with hypertension in rural 
     Zhang M, Chen W, Xu Y, Fang J, Liu Y (2025). BMC primary care
     PMID: 39987031 | URL: https://pubmed.ncbi.nlm.nih.gov/39987031/
  4. Knowledge, attitudes and practices of healthcare professionals in the management of patients with hypertension and concurrent bronchial asthma: a cross-sectional study in the Yellow River Delta region
     Yu F, Xu W, Ma X, Yang Y, Gao J (2025). BMJ open
     PMID: 39842923 | URL: https://pubmed.ncbi.nlm.nih.gov/39842923/
  5. Impact of health literacy and social support on medication adherence in patients with hypertension: a cross-sectional community-based study.
     Guo A, Jin H, Mao J, Zhu W, Zhou Y (2023). BMC cardiovascular disorders
     PMID: 36803662 | URL: https://pubmed.ncbi.nlm.nih.gov/36803662/
  6. Analyzing the effects of barriers to and facilitators of medication adherence among patients with cardiometabolic diseases: a structural equation modeling approach.
     Quaschning K, Koerner M, Wirtz MA (2022). BMC health services research
     PMID: 35501793 | URL: https://pubmed.ncbi.nlm.nih.gov/35501793/
  7. Effects of the Two-Dimensional Structure of Trust on Patient Adherence to Medication and Non-pharmaceutical Treatment: A Cross-Sectional Study of Rural Patients With Essential Hypertension in China.
     Feng Y, Guan S, Xu Y, Chen W, Huang X (2022). Frontiers in public health
     PMID: 35309202 | URL: https://pubmed.ncbi.nlm.nih.gov/35309202/
  8. The effect of high blood pressure-health literacy, self-management behavior, self-efficacy and social support on the health-related quality of life of Kazakh hypertension patients in a low-income rura
     Zhang Q, Huang F, Zhang L, Li S, Zhang J (2021). BMC public health
     PMID: 34112122 | URL: https://pubmed.ncbi.nlm.nih.gov/34112122/
  9. The influence of value reference point and risk preference on adherence in hypertensive patients in a low-income area of China.
     Wang C, Wang P, Dong H, Zhang L, Wu T (2020). Postgraduate medicine
     PMID: 31900018 | URL: https://pubmed.ncbi.nlm.nih.gov/31900018/
  10. Determinants of antihypertensive adherence among patients in Beijing: Application of the health belief model.
     Yang S, He C, Zhang X, Sun K, Wu S (2016). Patient education and counseling
     PMID: 27378081 | URL: https://pubmed.ncbi.nlm.nih.gov/27378081/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 21 hit; trong 21 bản ghi lấy về có 10 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~11 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  → Không có hồ sơ đăng ký nào khớp truy vấn

> **Đã tra ngày 2026-11-23: ~0 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 11 bài từ 11 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** YẾU — mới 1 RCT (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy SR/MA trong PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("medication adherence"[MeSH] OR adherence[tiab]) AND ("physician-patient relations"[MeSH] OR communication[tiab] OR "health literacy"[tiab] OR knowledge[tiab]) AND ("structural equation"[tiab] OR "path analysis"[tiab] OR "partial least squares"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Không có SR/MA, RCT hay guideline mới trong 5 năm gần đây (2021-2026) — nhánh này KHÔNG soi nghiên cứu quan sát

**Đối chiếu đăng ký:** ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn (chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-CAT-NGANG-PLS-SEM.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   RCT HOẶC Cohort tiến cứu đa trung tâm
│   Lý do: suy từ 0 SR/MA · 1 RCT · 11 quan sát (số hit, chưa sàng lọc)
│   Hạn chế: [CẦN BÁC SĨ NÊU — khả thi tại đơn vị?]         │
├─────────────────────────────────────────────────────────────┤
│ Ưu tiên 2 (phương án thay thế): [CẦN BÁC SĨ ẤN ĐỊNH]     │
│   Lý do: [CẦN BÁC SĨ NÊU]                                 │
│   Hạn chế: [CẦN BÁC SĨ NÊU]                               │
└─────────────────────────────────────────────────────────────┘
```

**Chuẩn báo cáo DỰ KIẾN** (theo ưu tiên 1; G1 chốt lại theo thiết kế thật):
- Mã thiết kế suy được: `[chưa suy được từ gợi ý]`
- Chuẩn báo cáo: [CẦN XÁC ĐỊNH Ở G1] — tra EQUATOR Network theo thiết kế thật
- Chuẩn đề cương: [CẦN XÁC ĐỊNH Ở G1]

*(Chuyển `thiet-ke-nghien-cuu` quyết định chi tiết ở G1)*

---

## PHẦN 6 — TIÊU CHÍ QUA CỔNG G0

Hệ chấm bằng `tools/g0_quality_gate.py`; báo cáo đầy đủ ở `G0_QUALITY_REPORT.md`.
**Ô tick dưới đây chỉ để đọc — nơi hệ ĐỌC THẬT là `study_meta.json → gate_params.G0`.**

```
PHẦN MÁY LÀM ĐƯỢC (tự động)
☑ Topic đề tài đã có
☑ Truy vấn PubMed đã chạy (11 bài tải về / 11 PMID duy nhất)
☑ Khoảng trống nghiên cứu đã phân tích
☑ Đã tra đăng ký nghiên cứu đang tiến hành

PHẦN CHỈ BÁC SĨ QUYẾT ĐƯỢC (hệ KHÔNG tự điền; ☑ = ĐÃ GHI trong gate_params — đạt hay không do bộ chấm quyết)
☐ PICO/PECO 4 thành phần            → gate_params.G0.population/intervention/comparison/outcomes
☐ Kết cục CHÍNH duy nhất + thang đo + thời điểm → .primary_outcome{,_measure,_timepoint}
☐ Giả thuyết H0/H1 + chiều kỳ vọng  → .hypothesis_h0/.hypothesis_h1/.expected_direction
☐ Loại câu hỏi + loại kiểm định     → .question_type/.test_type
☐ FINER 5 tiêu chí, MỖI khoá một câu «ĐẠT — <lý do>» → .finer_feasible/_interesting/_novel/_ethical/_relevant
☐ Đã đọc lại bằng chứng + biện minh tính mới (bỏ nhãn [DỰ THẢO …]) → .evidence_reviewed_confirmed/.novelty_justification
☐ Tự tra WHO ICTRP, ghi NGÀY tra  → .registry_manual_checked = {"ictrp": "YYYY-MM-DD"}
☐ Chốt PICO (vai trò + thời điểm + dấu nội dung) → .pico_confirmed/.reviewed_by_role/.reviewed_at/.dau_van_tay_chot
```

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-CAT-NGANG-PLS-SEM --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-CAT-NGANG-PLS-SEM` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-CAT-NGANG-PLS-SEM --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
