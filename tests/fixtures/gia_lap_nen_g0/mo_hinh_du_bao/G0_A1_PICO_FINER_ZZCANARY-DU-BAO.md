# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-DU-BAO
> Tạo tự động: 2026-11-15 20:02 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-DU-BAO`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Phát triển mô hình dự báo nguy cơ nhập viện trong 12 tháng ở người suy tim điều trị ngoại trú
**Truy vấn PubMed:** `("Heart Failure"[MeSH] OR "heart failure"[tiab]) AND (outpatient*[tiab] OR ambulatory[tiab]) AND ("prediction model"[tiab] OR "risk score"[tiab] OR "prognostic model"[tiab]) AND (hospitalization[tiab] OR hospitalisation[tiab] OR "Hospitalization"[MeSH])`

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
│   Evidence level hiện có: TRUNG BÌNH — có 1 SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)
│   → Có thể cập nhật SR/MA hiện có hoặc nghiên cứu quần thể cụ thể | ⚠ ClinicalTrials.gov: 11 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 31 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 2 | RCT: 9 | Guideline: 0 | Quan sát: 29
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Heart Failure"[MeSH] OR "heart failure"[tiab]) AND (outpatient*[tiab] OR ambulatory[tiab]) AND ("prediction model"[tiab] OR "risk score"[tiab] OR "prognostic model"[tiab]) AND (hospitalization[tiab] OR hospitalisation[tiab] OR "Hospitalization"[MeSH])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
│     • Có 11 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-DU-BAO.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Heart Failure"[MeSH] OR "heart failure"[tiab]) AND (outpatient*[tiab] OR ambulatory[tiab]) AND ("prediction model"[tiab] OR "risk score"[tiab] OR "prognostic model"[tiab]) AND (hospitalization[tiab] OR hospitalisation[tiab] OR "Hospitalization"[MeSH])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-DU-BAO.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~2 hit (số hit thật); liệt kê đủ 2 bài đã tải
  1. Prognostic significance of addition of electrocardiographic findings to the MAGGIC heart failure risk score.
     Ikitimur B, Barman HA, Dogan O, Atıcı A, Meriç BK (2022). Journal of electrocardiology
     PMID: 35427812 | URL: https://pubmed.ncbi.nlm.nih.gov/35427812/
  2. Mortality risk in dilated cardiomyopathy: the accuracy of heart failure prognostic models and dilated cardiomyopathy-tailored prognostic model.
     Dziewięcka E, Gliniak M, Winiarczyk M, Karapetyan A, Wiśniowska-Śmiałek S (2020). ESC heart failure
     PMID: 32853471 | URL: https://pubmed.ncbi.nlm.nih.gov/32853471/


### 3.2 Randomized Controlled Trials — ~9 hit (số hit thật); liệt kê đủ 9 bài đã tải
  1. Lactate Dehydrogenase and Outcomes in Patients With HF and Reduced Ejection Fraction: Insights From GALACTIC-HF.
     Ono R, Chimura M, Docherty KF, Jhund PS, Yang M (2026). JACC. Heart failure
     PMID: 41528277 | URL: https://pubmed.ncbi.nlm.nih.gov/41528277/
  2. Titration of Medications After Acute Heart Failure Is Safe, Tolerated, and Effective Regardless of Risk.
     Ambrosy AP, Chang AJ, Davison B, Voors A, Cohen-Solal A (2024). JACC. Heart failure
     PMID: 38739123 | URL: https://pubmed.ncbi.nlm.nih.gov/38739123/
  3. Baseline features of the VICTORIA (Vericiguat Global Study in Subjects with Heart Failure with Reduced Ejection Fraction) trial.
     Pieske B, Patel MJ, Westerhout CM, Anstrom KJ, Butler J (2019). European journal of heart failure
     PMID: 31820546 | URL: https://pubmed.ncbi.nlm.nih.gov/31820546/
  4. A novel algorithm to assess risk of heart failure exacerbation using ICD diagnostics: validation from RAFT.
     Gula LJ, Wells GA, Yee R, Koehler J, Sarkar S (2014). Heart rhythm
     PMID: 24846373 | URL: https://pubmed.ncbi.nlm.nih.gov/24846373/
  5. Anemia and associated clinical outcomes in patients with heart failure due to reduced left ventricular systolic function.
     McCullough PA, Barnard D, Clare R, Ellis SJ, Fleg JL (2013). Clinical cardiology
     PMID: 23929781 | URL: https://pubmed.ncbi.nlm.nih.gov/23929781/
  6. Characterization and prediction of natriuretic peptide "nonresponse" during heart failure management: results from the ProBNP Outpatient Tailored Chronic Heart Failure (PROTECT) and the NT-proBNP-Assi
     Gaggin HK, Truong QA, Rehman SU, Mohammed AA, Bhardwaj A (2013). Congestive heart failure (Greenwich, Conn.)
     PMID: 23279139 | URL: https://pubmed.ncbi.nlm.nih.gov/23279139/
  7. Factors related to morbidity and mortality in patients with chronic heart failure with systolic dysfunction: the HF-ACTION predictive risk score model.
     O'Connor CM, Whellan DJ, Wojdyla D, Leifer E, Clare RM (2012). Circulation. Heart failure
     PMID: 22114101 | URL: https://pubmed.ncbi.nlm.nih.gov/22114101/
  8. Benefit of exercise therapy for systolic heart failure in relation to disease severity and etiology-findings from the Heart Failure and A Controlled Trial Investigating Outcomes of Exercise Training s
     Whellan DJ, Nigam A, Arnold M, Starr AZ, Hill J (2011). American heart journal
     PMID: 22137073 | URL: https://pubmed.ncbi.nlm.nih.gov/22137073/
  9. Safety and feasibility of early hospital discharge in ST-segment elevation myocardial infarction--a prospective and randomized trial in low-risk primary percutaneous coronary intervention patients (th
     Kotowycz MA, Cosman TL, Tartaglia C, Afzal R, Syal RP (2010). American heart journal
     PMID: 20102876 | URL: https://pubmed.ncbi.nlm.nih.gov/20102876/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~29 hit (số hit thật); liệt kê đủ 13 bài đã tải
  1. Ambulatory outpatient management of acute decompensated heart failure in a heart failure specialist nurse delivered unit.
     Rasoul D, Essa H, Salmon T, Jackson C, Nyjo S (2026). Current problems in cardiology
     PMID: 42667938 | URL: https://pubmed.ncbi.nlm.nih.gov/42667938/
  2. Efficacy and workload implications of the Triage-HF™ algorithm in a nurse- and allied professional-led heart failure care pathway.
     Zwaenepoel BAC, Aslan U, Kirchhof B, Gelderblom S, De Jong van der Linden A (2026). European journal of cardiovascular nursing
     PMID: 41913566 | URL: https://pubmed.ncbi.nlm.nih.gov/41913566/
  3. The 2025 Echocardiographic Diastolic Function Algorithm is Associated with Improved Risk Stratification in Hospitalized Patients with Heart Failure.
     Kusunose K, Ooka S, Yamada H, Sata M (2026). Journal of the American Society of Echocardiography : official publication of the American Society of Echocardiography
     PMID: 41475581 | URL: https://pubmed.ncbi.nlm.nih.gov/41475581/
  4. Utilisation of ambulatory ECG monitoring for prediction of heart failure and stroke events and healthcare expenditure in treated and untreated patients: a retrospective cohort study.
     Schwennesen H, Li Z, Hammill BG, Clark AG, Pokorney SD (2025). BMJ open
     PMID: 40983571 | URL: https://pubmed.ncbi.nlm.nih.gov/40983571/
  5. Frailty, quality of life and nutritional status for the prediction of morbidity and mortality in individuals with chronic heart failure in southern Brazil (FPROHEART): a cohort study protocol.
     Nascimento DMD, Wolffenbüttel PI, Goldraich LA, Schaan B, Clausell N (2025). BMJ open
     PMID: 40812809 | URL: https://pubmed.ncbi.nlm.nih.gov/40812809/
  6. Development of the Anesthesia Risk Assessment Score (ARAS) for postoperative mortality and adverse discharge to a nursing facility.
     Khandaker R, Wongtangman K, Frank M, Borngaesser F, Smith RV (2025). Journal of clinical anesthesia
     PMID: 40592217 | URL: https://pubmed.ncbi.nlm.nih.gov/40592217/
  7. Echocardiographic Estimate of Pulmonary Capillary Wedge Pressure Improves Outcome Prediction in Heart Failure Patients With Reduced and Mildly Reduced Ejection Fraction.
     Bazan L, Gentile F, Sciarrone P, Buoncristiani F, Panichella G (2025). Journal of the American Society of Echocardiography : official publication of the American Society of Echocardiography
     PMID: 40228649 | URL: https://pubmed.ncbi.nlm.nih.gov/40228649/
  8. Identifying low-risk in patients with worsening heart failure with short hospital stay: A comparison of risk scores in predicting 30-day risk events.
     Burgos LM, Baro Vila RC, de Bortoli MA, Arias R, Malano D (2025). Current problems in cardiology
     PMID: 40023206 | URL: https://pubmed.ncbi.nlm.nih.gov/40023206/
  9. Prognostic value of liver fibrosis scores in ambulatory patients with heart failure.
     Varela-Cancelo A, Barge-Caballero E, Barge-Caballero G, Couto-Mallón D, Paniagua-Martín MJ (2025). Postgraduate medicine
     PMID: 39960078 | URL: https://pubmed.ncbi.nlm.nih.gov/39960078/
  10. Cardiovascular outcomes in Parkinson's disease patients from a retrospective cohort study.
     Lim S, Yum YJ, Kim JH, Lee CN, Joo HJ (2024). Scientific reports
     PMID: 39304675 | URL: https://pubmed.ncbi.nlm.nih.gov/39304675/
  11. WATCH-DM risk score predicts the prognosis of diabetic phenotype patients with heart failure and preserved ejection fraction.
     Zhang X, Lv X, Wang N, Yu S, Si J (2023). International journal of cardiology
     PMID: 37257517 | URL: https://pubmed.ncbi.nlm.nih.gov/37257517/
  12. Utilization of an Electronic Health Record Integrated Risk Score to Predict Hospitalization Among COVID-19 Patients.
     Nyman MA, Jose T, Croghan IT, Parkulo MA, Burger CD (2022). Journal of primary care & community health
     PMID: 35068257 | URL: https://pubmed.ncbi.nlm.nih.gov/35068257/
  13. Prognostic value of non-alcoholic fatty liver disease for predicting cardiovascular events in patients with diabetes mellitus with suspected coronary artery disease: a prospective cohort study.
     Ichikawa K, Miyoshi T, Osawa K, Miki T, Toda H (2021). Cardiovascular diabetology
     PMID: 33413363 | URL: https://pubmed.ncbi.nlm.nih.gov/33413363/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 53 hit; trong 30 bản ghi lấy về có 13 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~29 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~3 hit (số hit thật); liệt kê đủ 3 bài đã tải
  1. Prognostic significance of addition of electrocardiographic findings to the MAGGIC heart failure risk score.
     Ikitimur B, Barman HA, Dogan O, Atıcı A, Meriç BK (2022). Journal of electrocardiology
     PMID: 35427812 | URL: https://pubmed.ncbi.nlm.nih.gov/35427812/
  2. Lactate Dehydrogenase and Outcomes in Patients With HF and Reduced Ejection Fraction: Insights From GALACTIC-HF.
     Ono R, Chimura M, Docherty KF, Jhund PS, Yang M (2026). JACC. Heart failure
     PMID: 41528277 | URL: https://pubmed.ncbi.nlm.nih.gov/41528277/
  3. Titration of Medications After Acute Heart Failure Is Safe, Tolerated, and Effective Regardless of Risk.
     Ambrosy AP, Chang AJ, Davison B, Voors A, Cohen-Solal A (2024). JACC. Heart failure
     PMID: 38739123 | URL: https://pubmed.ncbi.nlm.nih.gov/38739123/

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [UNKNOWN] Effectiveness of an Interdisciplinary, Nurse-coordinated Atrial Fibrillation Expert Program for Primary Care Patients
     NCT01928121 | Pha: NA | Cỡ mẫu dự kiến: 450 | Bắt đầu: 2013-09
     URL: https://clinicaltrials.gov/study/NCT01928121
  2. [COMPLETED] Diagnostic Device Risk Management of Atrial Fibrillation and Heart Failure
     NCT01486316 | Pha: NA | Cỡ mẫu dự kiến: 24 | Bắt đầu: 2011-11
     URL: https://clinicaltrials.gov/study/NCT01486316
  3. [RECRUITING] Pacing Advancements With Cost and Experience VALuation for Unified Patient-Led Clinical Evidence - the PACEVALUE Study
     NCT07276139 | Pha: — | Cỡ mẫu dự kiến: 4500 | Bắt đầu: 2026-01-01
     URL: https://clinicaltrials.gov/study/NCT07276139
  4. [COMPLETED] Comparison of Outcomes and Access to Care for Heart Failure Trial
     NCT02674438 | Pha: PHASE3 | Cỡ mẫu dự kiến: 5452 | Bắt đầu: 2016-09
     URL: https://clinicaltrials.gov/study/NCT02674438
  5. [COMPLETED] Rural Hospital-Level Care at Home for Acutely Ill Adults
     NCT05256303 | Pha: NA | Cỡ mẫu dự kiến: 160 | Bắt đầu: 2022-02-16
     URL: https://clinicaltrials.gov/study/NCT05256303

> **Đã tra ngày 2026-11-15: ~31 hồ sơ khớp, 11 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 24 bài từ 24 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** TRUNG BÌNH — có 1 SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Heart Failure"[MeSH] OR "heart failure"[tiab]) AND (outpatient*[tiab] OR ambulatory[tiab]) AND ("prediction model"[tiab] OR "risk score"[tiab] OR "prognostic model"[tiab]) AND (hospitalization[tiab] OR hospitalisation[tiab] OR "Hospitalization"[MeSH])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Có 11 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 11 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 31 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-DU-BAO.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   RCT HOẶC Cohort tiến cứu đa trung tâm — ⚠ NHƯNG có 11...
│   Lý do: suy từ 2 SR/MA · 9 RCT · 29 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (24 bài tải về / 24 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-DU-BAO --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-DU-BAO` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-DU-BAO --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
