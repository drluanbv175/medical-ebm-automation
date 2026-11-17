# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-TONG-QUAN-GOP
> Tạo tự động: 2026-11-15 20:04 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-TONG-QUAN-GOP`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Hiệu quả của thuốc ức chế SGLT2 lên nhập viện vì suy tim ở người đái tháo đường típ 2 không có suy tim lúc đầu: tổng quan hệ thống và phân tích gộp các thử nghiệm ngẫu nhiên
**Truy vấn PubMed:** `("Sodium-Glucose Transporter 2 Inhibitors"[MeSH] OR "SGLT2 inhibitor*"[tiab] OR empagliflozin[tiab] OR dapagliflozin[tiab] OR canagliflozin[tiab]) AND ("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND ("heart failure"[tiab] OR "Heart Failure"[MeSH]) AND ("randomized controlled trial"[pt] OR randomi*[tiab])`

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
│   Evidence level hiện có: MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 6 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 16 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 242 | RCT: 264 | Guideline: 1 | Quan sát: 106
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN BÁC SĨ TỰ XÁC ĐỊNH khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
│     • Có 6 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-TONG-QUAN-GOP.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Sodium-Glucose Transporter 2 Inhibitors"[MeSH] OR "SGLT2 inhibitor*"[tiab] OR empagliflozin[tiab] OR dapagliflozin[tiab] OR canagliflozin[tiab]) AND ("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND ("heart failure"[tiab] OR "Heart Failure"[MeSH]) AND ("randomized controlled trial"[pt] OR randomi*[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-TONG-QUAN-GOP.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~242 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/
  3. Network and pairwise meta-analysis of the effects of novel hypoglycemic agents on cardiorenal outcomes in patients with type 2 diabetes and heart failure.
     Ye X, Wu Q, Li L, Huang M, Wang S (2026). Frontiers in endocrinology
     PMID: 42952754 | URL: https://pubmed.ncbi.nlm.nih.gov/42952754/
  4. Efficacy of sodium-glucose cotransporter 2 inhibitors after acute myocardial infarction: Are the benefits limited to patients with diabetes? A systematic review and meta-analysis.
     Santos MCF, Mamede I, Bessa R, Carvalhal G, Leão LA (2026). Journal of diabetes and its complications
     PMID: 42659939 | URL: https://pubmed.ncbi.nlm.nih.gov/42659939/
  5. Combined use of SGLT2 inhibitor and GLP-1 receptor agonist versus either monotherapy for cardiorenal Outcomes: an exploratory network meta-analysis of 16 randomized trials.
     Banerjee M, Basu M, Mukhopadhyay P, Ghosh S (2026). Endocrine
     PMID: 42616235 | URL: https://pubmed.ncbi.nlm.nih.gov/42616235/
  6. Cardiovascular outcomes of SGLT2 inhibitors versus GLP-1 receptor agonists in patients with type 2 diabetes and a history of myocardial infarction: a systematic review and network meta-analysis of ran
     Ren Y, Yang H, Zhang S, Hu T, Tan Q (2026). Frontiers in endocrinology
     PMID: 42591121 | URL: https://pubmed.ncbi.nlm.nih.gov/42591121/
  7. SGLT2 inhibitors and secondary polycythemia: a systematic review and meta-analysis of hematologic effects in patients with type 2 diabetes.
     Ali EAH, Rabadi M, Aweer RA, Subahi E, Abdelmahmuod EA (2026). European journal of clinical pharmacology
     PMID: 42587114 | URL: https://pubmed.ncbi.nlm.nih.gov/42587114/
  8. Are SGLT2 inhibitors really associated with increased urinary tract infection risk? A trial-level meta-analysis across type 2 diabetes, heart failure, and chronic kidney disease.
     Matteucci A, Di Fusco SA, Bonanni M, Castello L, Aquilani S (2026). Daru : journal of Faculty of Pharmacy, Tehran University of Medical Sciences
     PMID: 42566081 | URL: https://pubmed.ncbi.nlm.nih.gov/42566081/
  9. Cardiovascular and renal outcomes of combined SGLT2 inhibitors and GLP-1 receptor agonists versus monotherapy in patients with type 2 diabetes mellitus: a network meta-analysis.
     Chuang MH, Ho CW, Wang HY, Pan HC, Wu VC (2026). CMAJ : Canadian Medical Association journal = journal de l'Association medicale canadienne
     PMID: 42442791 | URL: https://pubmed.ncbi.nlm.nih.gov/42442791/
  10. Efficacy and Safety of SGLT2 Inhibitors and GLP-1 Receptor Agonists on Ventricular Arrhythmias and Cardiovascular Events: A Disease-Stratified Network Meta-Analysis.
     Sun WT, Liu RX, Jiang YH, Zhao YK, Yi-Cai (2026). Diabetes, obesity & metabolism
     PMID: 42426564 | URL: https://pubmed.ncbi.nlm.nih.gov/42426564/
  11. Renal and cardiovascular outcomes and safety of SGLT2 inhibitors in patients aged ≥ 65 years with non-dialysis chronic kidney disease: a systematic review and meta-analysis of subgroup-level estimates
     Bao Z, Hu J, Sun Y, Li X, Lin R (2026). BMC cardiovascular disorders
     PMID: 42420866 | URL: https://pubmed.ncbi.nlm.nih.gov/42420866/
  12. Genetic Evidence for the Benefits and Risks of Glucose-Lowering Drugs on Cardiovascular-Kidney-Metabolic Syndrome: A Drug-Target Mendelian Randomization Study.
     Lu J, Sun S, Shang X, Jiang S, Deng Z (2026). International journal of medical sciences
     PMID: 42328113 | URL: https://pubmed.ncbi.nlm.nih.gov/42328113/
  13. Glucose cotransporter-2 inhibitors on mortality and hospitalization in heart failure patients: a comprehensive meta-analysis.
     Mao X, Liu W, Hu B, Xu E (2026). Frontiers in endocrinology
     PMID: 42211456 | URL: https://pubmed.ncbi.nlm.nih.gov/42211456/
  14. Safety evaluation of Sodium-glucose cotransporter 2 inhibitors for cancer risk in specific populations: systematic review and meta-analysis.
     Teng J, Li T, Tan Y, Tang H (2026). Frontiers in clinical diabetes and healthcare
     PMID: 42180672 | URL: https://pubmed.ncbi.nlm.nih.gov/42180672/
  15. Cardiovascular, limb, and kidney effects of SGLT2 inhibitors in patients with peripheral artery disease: a systematic review and meta-analysis of randomized controlled trial data.
     Hu C, Ernst M, Snelling R, Ye Q, Paneni F (2026). Cardiovascular diabetology
     PMID: 42144626 | URL: https://pubmed.ncbi.nlm.nih.gov/42144626/


### 3.2 Randomized Controlled Trials — ~264 hit (số hit thật); liệt kê đủ 13 bài đã tải
  1. Impact of sodium-glucose cotransporter 2 inhibitors on blood glucose levels in patients with heart failure with reduced ejection fraction without diabetes.
     Abd El Hady YA, Abd Elaziz AASA, Adly Mahmoud A (2026). Revista portuguesa de cardiologia : orgao oficial da Sociedade Portuguesa de Cardiologia = Portuguese journal of cardiology : an official journal of the Portuguese Society of Cardiology
     PMID: 42556782 | URL: https://pubmed.ncbi.nlm.nih.gov/42556782/
  2. Effect of empagliflozin on copeptin levels in patients with recent acute coronary syndrome and newly detected dysglycaemia: a post-hoc analysis of the SOCOGAMI randomized controlled trial.
     Fortin E, Melander O, Ferrannini G, Näsman P, Norhammar A (2026). Cardiovascular diabetology
     PMID: 42522027 | URL: https://pubmed.ncbi.nlm.nih.gov/42522027/
  3. Dapagliflozin in acute myocardial infarction with type 2 diabetes: a randomized clinical trial.
     Macías-Cervantes HE, Guardado-Mendoza R, González LJ, Bautista-López GR, Hernández-Tizapa K (2026). Current problems in cardiology
     PMID: 42471097 | URL: https://pubmed.ncbi.nlm.nih.gov/42471097/
  4. Effects of SGLT2 inhibition on incident heart failure in carriers of cardiomyopathy-associated genetic variants.
     Marston NA, Kany S, Melloni GEM, Jurgens SJ, Kamanu FK (2026). Nature medicine
     PMID: 42260102 | URL: https://pubmed.ncbi.nlm.nih.gov/42260102/
  5. The Effect of Canagliflozin Dose on Renal and Cardiovascular Outcomes in Type 2 Diabetes and High Cardiovascular Risk.
     Elenjickal EJ, Baroz F, Boileau P, Tsoukas MA, Sharma A (2026). Diabetes, obesity & metabolism
     PMID: 42219264 | URL: https://pubmed.ncbi.nlm.nih.gov/42219264/
  6. Effects of Dapagliflozin on Cardiovascular Outcomes in Patients With Type 2 Diabetes at Risk of Liver Fibrosis.
     Oscarsson J, Huhn M, Jiang Y, Gause-Nilsson I, Wiviott SD (2026). Diabetes, obesity & metabolism
     PMID: 42046405 | URL: https://pubmed.ncbi.nlm.nih.gov/42046405/
  7. The Effect of Empagliflozin on Left Ventricular Mass and Volumes in Older Adult Individuals With Overweight and High Risk of Heart Failure: The Empire Prevent Cardiac Trial.
     Larsen JH, Andersen CF, Hansen MC, Omar M, Jensen J (2026). Journal of cardiac failure
     PMID: 41831639 | URL: https://pubmed.ncbi.nlm.nih.gov/41831639/
  8. Impact of canagliflozin on the cardiorenal effects of dietary sodium intake in type 2 diabetes: a post hoc analysis of the CREDENCE trial.
     Chiriacò M, Tricò D, Giannoni A, Sacchetta L, Nesti L (2026). Diabetologia
     PMID: 41817689 | URL: https://pubmed.ncbi.nlm.nih.gov/41817689/
  9. Empagliflozin and functional aerobic capacity in individuals with increased risk of heart failure: The Empire Prevent Cardiac trial.
     Larsen JH, Andersen CF, Jessen MM, Hansen MC, Omar M (2026). American heart journal
     PMID: 41802526 | URL: https://pubmed.ncbi.nlm.nih.gov/41802526/
  10. Bridging Glycemic and Lipid Control: Effects of Dapagliflozin in Co-Morbid Diabetes and Heart Failure – A Randomized Controlled Trial.
     Bhaganagarapu LS, Sundararajan S, Munusamy V (2026). Endocrine, metabolic & immune disorders drug targets
     PMID: 41582387 | URL: https://pubmed.ncbi.nlm.nih.gov/41582387/
  11. Association Between the 2022 AHA/ACC/HFSA Heart Failure Staging and Cardiovascular and Kidney Outcomes in Patients With Diabetes and Kidney Disease: A Post Hoc Analysis of the SCORED Randomized Contro
     Odutayo A, Bhatt DL, Sridhar VS, Szarek M, Cannon CP (2026). Circulation. Heart failure
     PMID: 41569429 | URL: https://pubmed.ncbi.nlm.nih.gov/41569429/
  12. SGLT2 inhibitor or metformin as standard treatment in early-stage type 2 diabetes? Baseline data in SMARTEST, a novel, decentralised, register-based randomised trial on prevention of diabetic complica
     Eriksson JW, Fanni G, Lundqvist MH, Jansson S, Rådholm K (2026). Diabetes, obesity & metabolism
     PMID: 41311237 | URL: https://pubmed.ncbi.nlm.nih.gov/41311237/
  13. Use of the win ratio approach to assess outcomes in the DapaTAVI trial.
     Rossello X, Gonzalez-Manzanares R, Amat-Santos I, Peral Disdier V, Nieto Roca L (2026). Revista espanola de cardiologia (English ed.)
     PMID: 40976500 | URL: https://pubmed.ncbi.nlm.nih.gov/40976500/


### 3.3 Guideline / Khuyến cáo — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Cardiovascular, kidney related, and weight loss effects of therapeutics for type 2 diabetes: a living clinical practice guideline.
     Agarwal A, Mustafa R, Manja V, Agoritsas T, Macdonald H (2025). BMJ (Clinical research ed.)
     PMID: 40813129 | URL: https://pubmed.ncbi.nlm.nih.gov/40813129/

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~106 hit (số hit thật); liệt kê đủ 14 bài đã tải
  1. Dapagliflozin Alone or Combined With Semaglutide: Cardiovascular and Renal Outcomes Among Patients With Type 2 Diabetes Mellitus in a 6-Month Real-World Retrospective Cohort Study in Saudi Arabia.
     Alharajin R, AlTaweel M, AlSubaiee M, Al Makhloof S, Almusaad A (2026). Journal of the ASEAN Federation of Endocrine Societies
     PMID: 42802824 | URL: https://pubmed.ncbi.nlm.nih.gov/42802824/
  2. Effectiveness of Adding GLP-1 Receptor Agonists to SGLT2 Inhibitor Therapy in Chronic Kidney Disease: A Population Based Study.
     Salim H, Qureshi S, Gulsin GS, Khan HR, Waqas SA (2026). Diabetes, obesity & metabolism
     PMID: 42802242 | URL: https://pubmed.ncbi.nlm.nih.gov/42802242/
  3. Early Sodium-Glucose Cotransporter-2 Inhibitor Use After Acute Kidney Injury in Type 2 Diabetes.
     Chou YT, Chen JY, Jiang ZH, Lin LC, Wu VC (2026). JAMA network open
     PMID: 42658493 | URL: https://pubmed.ncbi.nlm.nih.gov/42658493/
  4. Glucagon-Like Peptide 1 Receptor Agonists, Mortality, and Cardiovascular Outcomes in Serious Mental Illness.
     McIntyre RS, Zhang-James Y, Kwan ATH (2026). JAMA psychiatry
     PMID: 42647034 | URL: https://pubmed.ncbi.nlm.nih.gov/42647034/
  5. Dapagliflozin is associated with a reduction in left atrial volume index in type 2 diabetes mellitus without established cardiovascular disease.
     Çakır B, Polat F, Karataş MB, Dayı ŞÜ, Öz A (2026). Acta diabetologica
     PMID: 42171707 | URL: https://pubmed.ncbi.nlm.nih.gov/42171707/
  6. Sodium-glucose cotransporter 2 inhibitor use and outcomes after surgical aortic valve replacement.
     Jacquemyn X, Hasan I, Ogami T, Serna-Gallegos D, Bonatti J (2026). The Journal of thoracic and cardiovascular surgery
     PMID: 41831709 | URL: https://pubmed.ncbi.nlm.nih.gov/41831709/
  7. Safety and Efficacy of Sodium Glucose Cotransporter-2 Inhibitors in Patients With Cancer and Diabetes.
     Gvili Perelman M, Brzezinski RY, Banai S, Wolf I, Laufer-Perl M (2026). Journal of the American Heart Association
     PMID: 41804881 | URL: https://pubmed.ncbi.nlm.nih.gov/41804881/
  8. Cardio-renal outcomes in type 2 diabetes patients with advanced chronic kidney disease on SGLT2 inhibitors or GLP-1 receptor agonists.
     Chen JJ, Tsai MH, Ho WY, Fang YW, Chen MT (2026). The American journal of medicine
     PMID: 41419094 | URL: https://pubmed.ncbi.nlm.nih.gov/41419094/
  9. Effectiveness and safety of combining SGLT2 inhibitors and GLP-1 receptor agonists in individuals with type 2 diabetes: a systematic review and meta-analysis of cohort studies.
     Colombijn JMT, de Leijer JF, Visseren FLJ, Verhaar MC, van Raalte DH (2026). Diabetologia
     PMID: 41117973 | URL: https://pubmed.ncbi.nlm.nih.gov/41117973/
  10. Cardiometabolic outcomes with dapagliflozin after myocardial infarction by baseline ejection fraction: DAPA-MI.
     Erlinge D, James S, Deanfield J, Eriksson N, de Belder M (2025). ESC heart failure
     PMID: 40958495 | URL: https://pubmed.ncbi.nlm.nih.gov/40958495/
  11. Galectin-3 and kidney function in type 2 diabetes treated with dapagliflozin: Analysis from DECLARE-TIMI 58.
     Haller PM, Wiviott SD, Berg DD, Jarolim P, Goodrich EL (2025). ESC heart failure
     PMID: 40952180 | URL: https://pubmed.ncbi.nlm.nih.gov/40952180/
  12. Empagliflozin after myocardial infarction with or without diabetes and chronic kidney disease: Insights from EMPACT-MI.
     Fioretti F, Butler J, Udell JA, Schuyler Jones W, Petrie MC (2025). ESC heart failure
     PMID: 40947857 | URL: https://pubmed.ncbi.nlm.nih.gov/40947857/
  13. Impact of SGLT2 inhibitors on myocardial fibrosis in diabetic HFpEF: a longitudinal study.
     Albulushi A, Askari KM, Al-Abedi AM, Al-Kulaibi MA, Hasan MS (2025). European journal of medical research
     PMID: 40624547 | URL: https://pubmed.ncbi.nlm.nih.gov/40624547/
  14. Effects of sodium-glucose cotransport-2 inhibitors treatment in patients with pulmonary hypertension.
     Obeidat M, Vignarajah A, Abdel-Razeq R, Nathir A, Vigneswaramoorthy NA (2025). Therapeutic advances in respiratory disease
     PMID: 40580026 | URL: https://pubmed.ncbi.nlm.nih.gov/40580026/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 875 hit; trong 30 bản ghi lấy về có 21 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~106 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~405 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/
  3. Cardiovascular, kidney related, and weight loss effects of therapeutics for type 2 diabetes: a living clinical practice guideline.
     Agarwal A, Mustafa R, Manja V, Agoritsas T, Macdonald H (2025). BMJ (Clinical research ed.)
     PMID: 40813129 | URL: https://pubmed.ncbi.nlm.nih.gov/40813129/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [COMPLETED] Dapagliflozin Effects on Coronary Calcium and Epicardial Fat Assessed by Cardiotomography
     NCT05998525 | Pha: PHASE3 | Cỡ mẫu dự kiến: 54 | Bắt đầu: 2021-06-21
     URL: https://clinicaltrials.gov/study/NCT05998525
  2. [NOT_YET_RECRUITING] Heart-Kidney-Diabetes Multidisciplinary Care MOdels for CardiovascuLar Health In Patients With Chronic Kidney DiSease and Diabetes: A PragmaTIC Cluster Randomized Controlled Trial 
     NCT07811427 | Pha: PHASE4 | Cỡ mẫu dự kiến: 570 | Bắt đầu: 2026-12
     URL: https://clinicaltrials.gov/study/NCT07811427
  3. [COMPLETED] SGLT2 Inhibitor or Metformin as Standard Treatment of Early Stage Type 2 Diabetes
     NCT03982381 | Pha: PHASE4 | Cỡ mẫu dự kiến: 2067 | Bắt đầu: 2019-09-05
     URL: https://clinicaltrials.gov/study/NCT03982381
  4. [UNKNOWN] Study of Left Ventricular Function of Patients With Type 2 Diabetes Without Cardiovascular Disease
     NCT03736668 | Pha: NA | Cỡ mẫu dự kiến: 200 | Bắt đầu: 2018-05-22
     URL: https://clinicaltrials.gov/study/NCT03736668
  5. [RECRUITING] Using Ultromics EchoGo HFpEF Algorithm to Identify and Treat High Heart Failure Risk in Patients With Type 2 Diabetes
     NCT06593314 | Pha: NA | Cỡ mẫu dự kiến: 800 | Bắt đầu: 2025-08-06
     URL: https://clinicaltrials.gov/study/NCT06593314

> **Đã tra ngày 2026-11-15: ~16 hồ sơ khớp, 6 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 46 bài từ 46 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN BÁC SĨ TỰ XÁC ĐỊNH khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
• Có 6 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 6 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 16 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-TONG-QUAN-GOP.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 242 SR/MA · 264 RCT · 106 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (46 bài tải về / 46 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-TONG-QUAN-GOP --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-TONG-QUAN-GOP` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-TONG-QUAN-GOP --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
