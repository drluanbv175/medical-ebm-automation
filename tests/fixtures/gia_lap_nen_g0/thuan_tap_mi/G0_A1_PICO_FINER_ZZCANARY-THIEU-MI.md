# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-THIEU-MI
> Tạo tự động: 2026-11-16 18:43 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-THIEU-MI`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Sử dụng thuốc ức chế bơm proton kéo dài và nguy cơ gãy xương ở người từ 60 tuổi điều trị ngoại trú khi hồ sơ thiếu dữ liệu hiệp biến: nghiên cứu thuần tập hồi cứu có gán đa trị
**Truy vấn PubMed:** `("Proton Pump Inhibitors"[MeSH] OR "proton pump inhibitor*"[tiab] OR omeprazole[tiab] OR esomeprazole[tiab] OR pantoprazole[tiab]) AND ("Fractures, Bone"[MeSH] OR fracture*[tiab]) AND (aged[MeSH] OR elderly[tiab] OR "older adults"[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 11 | RCT: 4 | Guideline: 0 | Quan sát: 109
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Proton Pump Inhibitors"[MeSH] OR "proton pump inhibitor*"[tiab] OR omeprazole[tiab] OR esomeprazole[tiab] OR pantoprazole[tiab]) AND ("Fractures, Bone"[MeSH] OR fracture*[tiab]) AND (aged[MeSH] OR elderly[tiab] OR "older adults"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-THIEU-MI.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-16)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Proton Pump Inhibitors"[MeSH] OR "proton pump inhibitor*"[tiab] OR omeprazole[tiab] OR esomeprazole[tiab] OR pantoprazole[tiab]) AND ("Fractures, Bone"[MeSH] OR fracture*[tiab]) AND (aged[MeSH] OR elderly[tiab] OR "older adults"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-THIEU-MI.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~11 hit (số hit thật); liệt kê đủ 11 bài đã tải
  1. Use of proton pump inhibitors and increased risk of fracture in type 2 DM and menopausal women: a systematic review and meta-analysis.
     Battula P, Sree PB, Latha YS, Poojitha KN, Reddy KVS (2026). African health sciences
     PMID: 42063912 | URL: https://pubmed.ncbi.nlm.nih.gov/42063912/
  2. Proton pump inhibitors and risk of fracture in older adults: a systematic review and meta-analysis.
     Robert V, Papailhau C, Lesclide E, Ben Romdhane Z, Vincentelli MB (2025). Geriatric nursing (New York, N.Y.)
     PMID: 40848405 | URL: https://pubmed.ncbi.nlm.nih.gov/40848405/
  3. SAFETY OF LONG-TERM PROTON PUMP INHIBITORS: FACTS AND MYTHS.
     Chinzon D, Domingues G, Tosetto N, Perrotti M (2022). Arquivos de gastroenterologia
     PMID: 35830032 | URL: https://pubmed.ncbi.nlm.nih.gov/35830032/
  4. Association of proton-pump inhibitor use with adverse health outcomes: A systematic umbrella review of meta-analyses of cohort studies and randomised controlled trials.
     Veettil SK, Sadoyu S, Bald EM, Chandran VP, Khuu SAT (2022). British journal of clinical pharmacology
     PMID: 34622475 | URL: https://pubmed.ncbi.nlm.nih.gov/34622475/
  5. Proton pump inhibitors' use and risk of hip fracture: a systematic review and meta-analysis.
     Hussain S, Siddiqui AN, Habib A, Hussain MS, Najmi AK (2018). Rheumatology international
     PMID: 30159775 | URL: https://pubmed.ncbi.nlm.nih.gov/30159775/
  6. What is the long term acid inhibitor treatment in gastroesophageal reflux disease? What are the potential problems related to long term acid inhibitor treatment in gastroesophageal reflux disease? How
     Hatemi İ, Esatoğlu SN (2017). The Turkish journal of gastroenterology : the official journal of Turkish Society of Gastroenterology
     PMID: 29199170 | URL: https://pubmed.ncbi.nlm.nih.gov/29199170/
  7. Deprescribing versus continuation of chronic proton pump inhibitor use in adults.
     Boghossian TA, Rashid FJ, Thompson W, Welch V, Moayyedi P (2017). The Cochrane database of systematic reviews
     PMID: 28301676 | URL: https://pubmed.ncbi.nlm.nih.gov/28301676/
  8. Vertebral fracture efficacy during risedronate therapy in patients using proton pump inhibitors.
     Roux C, Goldstein JL, Zhou X, Klemes A, Lindsay R (2012). Osteoporosis international : a journal established as result of cooperation between the European Foundation for Osteoporosis and the National Osteoporosis Foundation of the USA
     PMID: 21365461 | URL: https://pubmed.ncbi.nlm.nih.gov/21365461/
  9. Proton pump inhibitors therapy and risk of hip fracture: a systematic review and meta-analysis.
     Ye X, Liu H, Wu C, Qin Y, Zang J (2011). European journal of gastroenterology & hepatology
     PMID: 21701389 | URL: https://pubmed.ncbi.nlm.nih.gov/21701389/
  10. Proton pump inhibitors and risk of fractures: a meta-analysis of 11 international studies.
     Yu EW, Bauer SR, Bain PA, Bauer DC (2011). The American journal of medicine
     PMID: 21605729 | URL: https://pubmed.ncbi.nlm.nih.gov/21605729/
  11. Atypical fractures of the femur and bisphosphonate therapy: A systematic review of case/case series studies.
     Giusti A, Hamdy NA, Papapoulos SE (2010). Bone
     PMID: 20493982 | URL: https://pubmed.ncbi.nlm.nih.gov/20493982/


### 3.2 Randomized Controlled Trials — ~4 hit (số hit thật); liệt kê đủ 4 bài đã tải
  1. Safety of Proton Pump Inhibitors Based on a Large, Multi-Year, Randomized Trial of Patients Receiving Rivaroxaban or Aspirin.
     Moayyedi P, Eikelboom JW, Bosch J, Connolly SJ, Dyal L (2019). Gastroenterology
     PMID: 31152740 | URL: https://pubmed.ncbi.nlm.nih.gov/31152740/
  2. A phase III, multicenter, prospective, single-blinded, noninferiority, randomized controlled trial on the performance of a novel esophageal stent with an antireflux valve (with video).
     Dua KS, DeWitt JM, Kessler WR, Diehl DL, Draganov PV (2019). Gastrointestinal endoscopy
     PMID: 30684601 | URL: https://pubmed.ncbi.nlm.nih.gov/30684601/
  3. Dexlansoprazole and Esomeprazole Do Not Affect Bone Homeostasis in Healthy Postmenopausal Women.
     Hansen KE, Nieves JW, Nudurupati S, Metz DC, Perez MC (2019). Gastroenterology
     PMID: 30445008 | URL: https://pubmed.ncbi.nlm.nih.gov/30445008/
  4. Long-term proton pump inhibitor therapy and falls and fractures in elderly women: a prospective cohort study.
     Lewis JR, Barre D, Zhu K, Ivey KL, Lim EM (2014). Journal of bone and mineral research : the official journal of the American Society for Bone and Mineral Research
     PMID: 24825180 | URL: https://pubmed.ncbi.nlm.nih.gov/24825180/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~109 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Association of bone mineral-reducing medications with two-year complications following open reduction and internal fixation of ankle fractures: a propensity score-matched analysis.
     Horani K, Lawand J, Tsavaris N, Alsaidi A, Wang J (2026). European journal of orthopaedic surgery & traumatology : orthopedie traumatologie
     PMID: 42944786 | URL: https://pubmed.ncbi.nlm.nih.gov/42944786/
  2. Pre-operative proton pump inhibitor use and risk of adverse outcomes after total elbow arthroplasty: a propensity-matched analysis.
     Frappa N, Dillon MR, Fuller SI, Divasta A, Gamsarian V (2026). Journal of shoulder and elbow surgery
     PMID: 42191059 | URL: https://pubmed.ncbi.nlm.nih.gov/42191059/
  3. Population-based deprescribing strategy for proton pump inhibitors: health outcomes from a case-control study.
     Echeverría Gorriti A, Gorricho Mendívil J, Etxegia Apezetxea J, Tamayo Rodríguez I, Librero López J (2026). Medicina clinica
     PMID: 41832801 | URL: https://pubmed.ncbi.nlm.nih.gov/41832801/
  4. Prescribing of Medication to Prevent Glucocorticoid Harms in Patients With Polymyalgia Rheumatica: A Cross-Sectional Study and Two Emulated Target Trials in the Clinical Practice Research Datalink Aur
     Twohig H, Jenkinson D, Bailey J, Hider S, Scott IC (2026). Arthritis & rheumatology (Hoboken, N.J.)
     PMID: 41668463 | URL: https://pubmed.ncbi.nlm.nih.gov/41668463/
  5. One-year body weight loss and gain as independent predictors of frailty-related outcomes and mortality in an aging Japanese population.
     Fujii H, Kodani E, Kaneko T, Nakamura H, Tamura Y (2026). Scientific reports
     PMID: 41656326 | URL: https://pubmed.ncbi.nlm.nih.gov/41656326/
  6. Proton Pump Inhibitors Are Associated With Increased Risk of Site-Specific Nonunion After Open Reduction Internal Fixation.
     Romoff M, Kim MS, Spitzer C, Brunette M, Thomas H (2026). Journal of orthopaedic trauma
     PMID: 41364067 | URL: https://pubmed.ncbi.nlm.nih.gov/41364067/
  7. Regular Proton-Pump Inhibitor Intake is Associated with Deterioration of Peripheral Bone Mineral Density, Microarchitecture, and Strength in Older Patients as Assessed by High-Resolution Peripheral Qu
     Heilmeier U, Siegenthaler A, Meyer U, Boensch M, Kistler-Fischbacher M (2025). Calcified tissue international
     PMID: 41125947 | URL: https://pubmed.ncbi.nlm.nih.gov/41125947/
  8. Effects of Perioperative Proton Pump Inhibitor Use on Outcomes of Total Joint Arthroplasty Patients Who Have Osteoporosis and Osteopenia.
     Le A, Brennan JC, Johnson AH, MacDonald JH, King PJ (2026). The Journal of arthroplasty
     PMID: 40780490 | URL: https://pubmed.ncbi.nlm.nih.gov/40780490/
  9. Association of Pneumonia, Fracture, Metabolic, and Renal Events With Long-Term Proton Pump Inhibitor Use in Patients With Chronic Kidney Disease.
     Chien YF, Chen YY, Wu CK (2025). Pharmacotherapy
     PMID: 40678972 | URL: https://pubmed.ncbi.nlm.nih.gov/40678972/
  10. Bone health, renal outcomes, and iron deficiency anaemia in proton pump inhibitor versus histamine-2 receptor antagonist users: a retrospective cohort study based on TriNetX global collaborative netwo
     Chen TP, Wu MJ, Chen CH, Tsai SF (2025). BMJ open gastroenterology
     PMID: 40659386 | URL: https://pubmed.ncbi.nlm.nih.gov/40659386/
  11. The impact of proton pump inhibitor use on fusion rates following single-level lumbar spinal fusion surgery.
     Chang Y, Lin YS, Huang CY, Chuang MT, Chi KY (2025). European spine journal : official publication of the European Spine Society, the European Spinal Deformity Society, and the European Section of the Cervical Spine Research Society
     PMID: 40442516 | URL: https://pubmed.ncbi.nlm.nih.gov/40442516/
  12. Proton pump inhibitor exposure, trabecular bone score, and BMD: a registry-based cohort study.
     Zarzour F, Schousboe JT, Binkley N, Hans D, Leslie WD (2025). Journal of bone and mineral research : the official journal of the American Society for Bone and Mineral Research
     PMID: 40367346 | URL: https://pubmed.ncbi.nlm.nih.gov/40367346/
  13. Incidence of Osteopenia or Osteoporosis in Asian Patients With Chronic Hepatitis B.
     Lee HW, Kwon S, Moon YR, Ahn H, Lee J (2025). Journal of gastroenterology and hepatology
     PMID: 40312835 | URL: https://pubmed.ncbi.nlm.nih.gov/40312835/
  14. Fracture Risk Linked to Proton Pump Inhibitors Versus H2 Receptor Antagonists in Autoimmune Rheumatic and Gastrointestinal Disease Patients.
     Zeng M, Lee YH, Wang SI, Palmowski A, Chu WM (2025). International journal of rheumatic diseases
     PMID: 39932099 | URL: https://pubmed.ncbi.nlm.nih.gov/39932099/
  15. Routine Prescription of Proton Pump Inhibitors in the Perioperative Period is Associated With Decreased Rates of 2-Year Revision Surgery After Total Hip and Knee Arthroplasty.
     Harris AB, Agarwal AR, Hegde V, Oni JK, Khanuja HS (2025). The Journal of arthroplasty
     PMID: 39233100 | URL: https://pubmed.ncbi.nlm.nih.gov/39233100/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 196 hit; trong 30 bản ghi lấy về có 13 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~109 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~4 hit (số hit thật); liệt kê đủ 4 bài đã tải
  1. Use of proton pump inhibitors and increased risk of fracture in type 2 DM and menopausal women: a systematic review and meta-analysis.
     Battula P, Sree PB, Latha YS, Poojitha KN, Reddy KVS (2026). African health sciences
     PMID: 42063912 | URL: https://pubmed.ncbi.nlm.nih.gov/42063912/
  2. Proton pump inhibitors and risk of fracture in older adults: a systematic review and meta-analysis.
     Robert V, Papailhau C, Lesclide E, Ben Romdhane Z, Vincentelli MB (2025). Geriatric nursing (New York, N.Y.)
     PMID: 40848405 | URL: https://pubmed.ncbi.nlm.nih.gov/40848405/
  3. SAFETY OF LONG-TERM PROTON PUMP INHIBITORS: FACTS AND MYTHS.
     Chinzon D, Domingues G, Tosetto N, Perrotti M (2022). Arquivos de gastroenterologia
     PMID: 35830032 | URL: https://pubmed.ncbi.nlm.nih.gov/35830032/
  ... và 1 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [UNKNOWN] Vitamin D3 - Omega3 - Home Exercise - HeALTHy Aging and Longevity Cohort
     NCT05062018 | Pha: — | Cỡ mẫu dự kiến: 534 | Bắt đầu: 2019-11-26
     URL: https://clinicaltrials.gov/study/NCT05062018
  2. [COMPLETED] Should I Continue Taking My Acid Reflux Medication? Development and Pilot Testing of a Patient Decision Aid
     NCT02558049 | Pha: NA | Cỡ mẫu dự kiến: 12 | Bắt đầu: 2015-11
     URL: https://clinicaltrials.gov/study/NCT02558049
  3. [ACTIVE_NOT_RECRUITING] Clinical Study to Predict the Risk of Bone Fractures With the POROUS Ultrasound Device
     NCT06567054 | Pha: NA | Cỡ mẫu dự kiến: 1600 | Bắt đầu: 2025-03-03
     URL: https://clinicaltrials.gov/study/NCT06567054
  4. [COMPLETED] Models of Primary Osteoporosis Screening in Male Veterans
     NCT04079868 | Pha: NA | Cỡ mẫu dự kiến: 3512 | Bắt đầu: 2019-08-30
     URL: https://clinicaltrials.gov/study/NCT04079868
  5. [COMPLETED] Proton Pump Inhibitors (PPI): a Study to Improve Appropriate Prescriptions in the Elderly
     NCT04637750 | Pha: NA | Cỡ mẫu dự kiến: 800 | Bắt đầu: 2019-10-10
     URL: https://clinicaltrials.gov/study/NCT04637750

> **Đã tra ngày 2026-11-16: ~11 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 30 bài từ 30 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Proton Pump Inhibitors"[MeSH] OR "proton pump inhibitor*"[tiab] OR omeprazole[tiab] OR esomeprazole[tiab] OR pantoprazole[tiab]) AND ("Fractures, Bone"[MeSH] OR fracture*[tiab]) AND (aged[MeSH] OR elderly[tiab] OR "older adults"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»



> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-THIEU-MI.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 11 SR/MA · 4 RCT · 109 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (30 bài tải về / 30 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-THIEU-MI --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-THIEU-MI` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-THIEU-MI --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
