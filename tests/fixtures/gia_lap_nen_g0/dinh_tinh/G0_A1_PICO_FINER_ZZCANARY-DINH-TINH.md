# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-DINH-TINH
> Tạo tự động: 2026-11-15 20:07 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-DINH-TINH`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Trải nghiệm và rào cản khi bắt đầu tiêm insulin của người đái tháo đường típ 2 điều trị ngoại trú: nghiên cứu định tính
**Truy vấn PubMed:** `("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND (insulin[tiab]) AND ("psychological insulin resistance"[tiab] OR barrier*[tiab] OR experience*[tiab]) AND ("Qualitative Research"[MeSH] OR qualitative[tiab] OR interview*[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 19 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 67 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 7 | RCT: 13 | Guideline: 1 | Quan sát: 43
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN BÁC SĨ TỰ XÁC ĐỊNH khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
│     • Có 19 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-DINH-TINH.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Diabetes Mellitus, Type 2"[MeSH] OR "type 2 diabetes"[tiab]) AND (insulin[tiab]) AND ("psychological insulin resistance"[tiab] OR barrier*[tiab] OR experience*[tiab]) AND ("Qualitative Research"[MeSH] OR qualitative[tiab] OR interview*[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-DINH-TINH.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~7 hit (số hit thật); liệt kê đủ 9 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/
  3. Neuropathological links between T2DM and LOAD: systematic review and meta-analysis.
     Lemche E, Hortobágyi T, Kiecker C, Turkheimer F (2025). Physiological reviews
     PMID: 40062731 | URL: https://pubmed.ncbi.nlm.nih.gov/40062731/
  4. Patient experiences of continuous glucose monitoring and sensor-augmented insulin pump therapy for diabetes: A systematic review of qualitative studies.
     Natale P, Chen S, Chow CK, Cheung NW, Martinez-Martin D (2023). Journal of diabetes
     PMID: 37551735 | URL: https://pubmed.ncbi.nlm.nih.gov/37551735/
  5. The experiences of insulin use among older people with Type 2 diabetes mellitus: A thematic synthesis.
     Langerman C, Forbes A, Robert G (2022). Primary care diabetes
     PMID: 36089508 | URL: https://pubmed.ncbi.nlm.nih.gov/36089508/
  6. Individual, healthcare professional and system-level barriers and facilitators to initiation and adherence to injectable therapies for type 2 diabetes: A systematic review and meta-ethnography.
     Byrne J, Willis A, Dunkley A, Fitzpatrick C, Campbell S (2022). Diabetic medicine : a journal of the British Diabetic Association
     PMID: 34432914 | URL: https://pubmed.ncbi.nlm.nih.gov/34432914/
  7. Perceived Barriers, Benefits, Facilitators, and Attitudes of Health Professionals Towards Multidisciplinary Team Care in Type 2 Diabetes Management: A Systematic Review.
     Dankoly US, Vissers D, El Farkouch Z, Kolasa E, Ziyyat A (2021). Current diabetes reviews
     PMID: 33176659 | URL: https://pubmed.ncbi.nlm.nih.gov/33176659/
  8. Barriers to effective management of type 2 diabetes in primary care: qualitative systematic review.
     Rushforth B, McCrorie C, Glidewell L, Midgley E, Foy R (2016). The British journal of general practice : the journal of the Royal College of General Practitioners
     PMID: 26823263 | URL: https://pubmed.ncbi.nlm.nih.gov/26823263/
  9. Barriers and facilitators to starting insulin in patients with type 2 diabetes: a systematic review.
     Ng CJ, Lai PS, Lee YK, Azmi SA, Teo CH (2015). International journal of clinical practice
     PMID: 26147376 | URL: https://pubmed.ncbi.nlm.nih.gov/26147376/


### 3.2 Randomized Controlled Trials — ~13 hit (số hit thật); liệt kê đủ 13 bài đã tải
  1. Effects of a nurse-led diabetes self-management programme for people with type 2 diabetes receiving insulin injection therapy: A randomised controlled trial with qualitative process evaluation.
     Liang W, Chow KM, Ni X, Tola YO, Lo SHS (2025). International journal of nursing studies
     PMID: 40907093 | URL: https://pubmed.ncbi.nlm.nih.gov/40907093/
  2. A Randomised Controlled Trial Testing a Behavioural Intervention Program for the Prevention of Type 2 Diabetes Among American Indian Youth: The Tribal Turning Point Study.
     Cohen CC, Dabelea D, Sinha M, Delamater AM, Glueck DH (2025). Pediatric obesity
     PMID: 40884258 | URL: https://pubmed.ncbi.nlm.nih.gov/40884258/
  3. The Role of Social Support on Self-Management of Gestational Diabetes Mellitus: A Qualitative Analysis.
     Merchant T, DiTosto JD, Gomez-Roas M, Williams BR, Niznik CM (2025). Journal of midwifery & women's health
     PMID: 40576167 | URL: https://pubmed.ncbi.nlm.nih.gov/40576167/
  4. User Engagement Among Diverse Adults in a 12-Month Text Message-Delivered Diabetes Support Intervention: Results from a Randomized Controlled Trial.
     Nelson LA, Spieker A, Greevy R, LeStourgeon LM, Wallston KA (2020). JMIR mHealth and uHealth
     PMID: 32706738 | URL: https://pubmed.ncbi.nlm.nih.gov/32706738/
  5. A Delayed Morning and Earlier Evening Time-Restricted Feeding Protocol for Improving Glycemic Control and Dietary Adherence in Men with Overweight/Obesity: A Randomized Controlled Trial.
     Parr EB, Devlin BL, Radford BE, Hawley JA (2020). Nutrients
     PMID: 32079327 | URL: https://pubmed.ncbi.nlm.nih.gov/32079327/
  6. Managing with Learning Disability and Diabetes: OK-Diabetes - a case-finding study and feasibility randomised controlled trial.
     House A, Bryant L, Russell AM, Wright-Hughes A, Graham L (2018). Health technology assessment (Winchester, England)
     PMID: 29845932 | URL: https://pubmed.ncbi.nlm.nih.gov/29845932/
  7. A qualitative evaluation of a physician-delivered pedometer-based step count prescription strategy with insight from participants and treating physicians.
     Cooke AB, Pace R, Chan D, Rosenberg E, Dasgupta K (2018). Diabetes research and clinical practice
     PMID: 29530385 | URL: https://pubmed.ncbi.nlm.nih.gov/29530385/
  8. Study protocol: a pragmatic randomised controlled trial of a 12-week physical activity and nutritional education program for overweight Aboriginal and Torres Strait Islander women.
     Canuto KJ, McDermott RA, Cargo M, Esterman AJ (2011). BMC public health
     PMID: 21851643 | URL: https://pubmed.ncbi.nlm.nih.gov/21851643/
  9. Challenges of maintaining research protocol fidelity in a clinical care setting: a qualitative study of the experiences and views of patients and staff participating in a randomized controlled trial.
     Lawton J, Jenkins N, Darbyshire JL, Holman RR, Farmer AJ (2011). Trials
     PMID: 21542916 | URL: https://pubmed.ncbi.nlm.nih.gov/21542916/
  10. Initiating insulin as part of the Treating To Target in Type 2 Diabetes (4-T) trial: an interview study of patients' and health professionals' experiences.
     Jenkins N, Hallowell N, Farmer AJ, Holman RR, Lawton J (2010). Diabetes care
     PMID: 20592050 | URL: https://pubmed.ncbi.nlm.nih.gov/20592050/
  11. Community based yoga classes for type 2 diabetes: an exploratory randomised controlled trial.
     Skoro-Kondza L, Tai SS, Gadelrab R, Drincevic D, Greenhalgh T (2009). BMC health services research
     PMID: 19228402 | URL: https://pubmed.ncbi.nlm.nih.gov/19228402/
  12. Metabolic effects of pioglitazone and rosiglitazone in patients with diabetes and metabolic syndrome treated with glimepiride: a twelve-month, multicenter, double-blind, randomized, controlled, parall
     Derosa G, Cicero AF, Gaddi A, Ragonesi PD, Fogari E (2004). Clinical therapeutics
     PMID: 15220018 | URL: https://pubmed.ncbi.nlm.nih.gov/15220018/
  13. The influence of different insulin regimens on quality of life and metabolic control in insulin-dependent diabetics.
     Tallroth G, Karlson B, Nilsson A, Agardh CD (1989). Diabetes research and clinical practice
     PMID: 2649340 | URL: https://pubmed.ncbi.nlm.nih.gov/2649340/


### 3.3 Guideline / Khuyến cáo — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Position Statement on the management of continuous subcutaneous insulin infusion (CSII): The Italian Lazio experience.
     Maurizi AR, Suraci C, Pitocco D, Schiaffini R, Tubili C (2016). Journal of diabetes
     PMID: 26118939 | URL: https://pubmed.ncbi.nlm.nih.gov/26118939/

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~43 hit (số hit thật); liệt kê đủ 14 bài đã tải
  1. Barriers to glycemic control among youth with diabetes in Ghana: a mixed-methods cross-sectional study.
     Asafo-Agyei SB, Ameyaw E, Nguah SB, Kwarteng Owusu S, Adutwum LM (2026). BMC endocrine disorders
     PMID: 42387496 | URL: https://pubmed.ncbi.nlm.nih.gov/42387496/
  2. Quantifying the Basal Insulin Treatment Preferences of People Living in Canada With Type 2 Diabetes When Glycemic Management and Cost Are Held Constant: A Discrete Choice Experiment.
     Hallworth P, Tatlock S, Wallace S, Tute E, Bell B (2026). Canadian journal of diabetes
     PMID: 41638420 | URL: https://pubmed.ncbi.nlm.nih.gov/41638420/
  3. Level of physical activity and its predictors among adult diabetic men who were on follow-up at health facilities in Bale Zone, Southeast Ethiopia: institution-based cross-sectional study.
     Tadesse TM, Zenbaba D, Ejigu N, Sahiledengle B, Gomora D (2026). BMC research notes
     PMID: 41527077 | URL: https://pubmed.ncbi.nlm.nih.gov/41527077/
  4. Identifying interhospital variation in hyperosmolar hyperglycemic syndrome (HHS) care: development and outcomes of the DEKODE HHS model.
     Kew TM, Manta A, Sawlani JP, Ling Jie Yee A, Mann A (2025). BMJ open diabetes research & care
     PMID: 41360624 | URL: https://pubmed.ncbi.nlm.nih.gov/41360624/
  5. Understanding the benefits and psychological burdens of using continuous glucose monitoring for lifestyle change: A mixed-methods cross-sectional study.
     Richardson KM, Jospe MR, Somerville J, Felrice J, Schembre SM (2025). Obesity research & clinical practice
     PMID: 41102072 | URL: https://pubmed.ncbi.nlm.nih.gov/41102072/
  6. A Comparative Multicenter Cross-Sectional Study on Hypoglycemia in Young Adults and Older Adults With Type 2 Diabetes Mellitus in an Outpatient Setting in Sri Lanka.
     Jayasekera PT, Senaratne T, Lamabadusuriya D, Sathischandra H, Matthias AT (2025). Journal of diabetes research
     PMID: 40893590 | URL: https://pubmed.ncbi.nlm.nih.gov/40893590/
  7. Diabetes, obesity, and economic social exclusion (DOSE) syndemic among a nationally representative sample in the United States.
     Campbell J (2025). Social science & medicine (1982)
     PMID: 40712439 | URL: https://pubmed.ncbi.nlm.nih.gov/40712439/
  8. Insulin therapy adherence and its associated factors among diabetic patients in a Ghanaian primary care hospital.
     Sefah IA, Mensah M, Hutton-Nyameaye AA, Sarkodie E, Meyer JC (2025). PloS one
     PMID: 39854487 | URL: https://pubmed.ncbi.nlm.nih.gov/39854487/
  9. Factors Influencing Hypoglycemia in Type 2 Diabetes Mellitus Outpatients with State Health Insurance at Regional General Hospitals in Jakarta, Indonesia.
     Veryanti PR, Sauriasari R, Sartika RAD, Elya B (2024). Current diabetes reviews
     PMID: 38243951 | URL: https://pubmed.ncbi.nlm.nih.gov/38243951/
  10. [Assessment of the progression dynamics of chronic kidney disease in elderly patients with type 2 diabetes mellitus.].
     Pervyshin NA, Bulgakova SV, Komarova MV, Treneva EV, Kurmaev DP (2023). Advances in gerontology = Uspekhi gerontologii
     PMID: 37782644 | URL: https://pubmed.ncbi.nlm.nih.gov/37782644/
  11. The magnitude of chronic diabetes complications and its associated factors among diabetic patients attending the general hospitals in Tigray region, Northern Ethiopia.
     Berhe KK, Mselle LT, Gebru HB (2023). PloS one
     PMID: 37624794 | URL: https://pubmed.ncbi.nlm.nih.gov/37624794/
  12. Supporting self-management in women with pre-existing diabetes in pregnancy: a protocol for a mixed-methods sequential comparative case study.
     Sushko K, Sherifali D, Nerenberg K, Strachan PH, Butt M (2022). BMJ open
     PMID: 36253034 | URL: https://pubmed.ncbi.nlm.nih.gov/36253034/
  13. Major osteoporosis fracture prediction in type 2 diabetes: a derivation and comparison study.
     Kong XK, Zhao ZY, Zhang D, Xie R, Sun LH (2022). Osteoporosis international : a journal established as result of cooperation between the European Foundation for Osteoporosis and the National Osteoporosis Foundation of the USA
     PMID: 35583602 | URL: https://pubmed.ncbi.nlm.nih.gov/35583602/
  14. Investigating the day-to-day impact of hypoglycaemia in adults with type 1 or type 2 diabetes: design and validation protocol of the Hypo-METRICS application.
     Søholm U, Broadley M, Zaremba N, Divilly P, Nefs G (2022). BMJ open
     PMID: 35105572 | URL: https://pubmed.ncbi.nlm.nih.gov/35105572/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 281 hit; trong 30 bản ghi lấy về có 25 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~43 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~8 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. 2. Diagnosis and Classification of Diabetes: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358893 | URL: https://pubmed.ncbi.nlm.nih.gov/41358893/
  2. 9. Pharmacologic Approaches to Glycemic Treatment: Standards of Care in Diabetes-2026.
     tác giả: xem trang PubMed (2026). Diabetes care
     PMID: 41358900 | URL: https://pubmed.ncbi.nlm.nih.gov/41358900/
  3. Neuropathological links between T2DM and LOAD: systematic review and meta-analysis.
     Lemche E, Hortobágyi T, Kiecker C, Turkheimer F (2025). Physiological reviews
     PMID: 40062731 | URL: https://pubmed.ncbi.nlm.nih.gov/40062731/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [COMPLETED] Evaluation of a Physical Activity Referral Scheme
     NCT03490747 | Pha: NA | Cỡ mẫu dự kiến: 68 | Bắt đầu: 2018-03-12
     URL: https://clinicaltrials.gov/study/NCT03490747
  2. [COMPLETED] Treatment Adherence Intervention in Patients With Type 2 Diabetes and Comorbid Depression
     NCT04097483 | Pha: NA | Cỡ mẫu dự kiến: 428 | Bắt đầu: 2017-01
     URL: https://clinicaltrials.gov/study/NCT04097483
  3. [COMPLETED] i-Matter: Investigating an mHealth Texting Tool for Embedding Patient-reported Data Into Diabetes Management
     NCT03652389 | Pha: NA | Cỡ mẫu dự kiến: 246 | Bắt đầu: 2018-12-18
     URL: https://clinicaltrials.gov/study/NCT03652389
  4. [COMPLETED] Patients and Care Providers Perspectives and Experience With Decision Aid Tool for Self-monitoring of Blood Glucose
     NCT02553408 | Pha: NA | Cỡ mẫu dự kiến: 16 | Bắt đầu: 2015-09
     URL: https://clinicaltrials.gov/study/NCT02553408
  5. [COMPLETED] The Bennett Kids PowerUP Project
     NCT05858580 | Pha: NA | Cỡ mẫu dự kiến: 72 | Bắt đầu: 2024-03-01
     URL: https://clinicaltrials.gov/study/NCT05858580

> **Đã tra ngày 2026-11-15: ~67 hồ sơ khớp, 19 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 37 bài từ 37 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN BÁC SĨ TỰ XÁC ĐỊNH khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
• Có 19 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 19 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 67 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-DINH-TINH.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 7 SR/MA · 13 RCT · 43 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (37 bài tải về / 37 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-DINH-TINH --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-DINH-TINH` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-DINH-TINH --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
