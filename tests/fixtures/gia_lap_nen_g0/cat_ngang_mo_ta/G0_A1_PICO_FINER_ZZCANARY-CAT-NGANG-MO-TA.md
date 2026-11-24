# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-CAT-NGANG-MO-TA
> Tạo tự động: 2026-11-15 19:53 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-CAT-NGANG-MO-TA`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Tỷ lệ kiểm soát huyết áp ở người tăng huyết áp điều trị ngoại trú: nghiên cứu cắt ngang mô tả
**Truy vấn PubMed:** `(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "controlled hypertension"[tiab] OR "hypertension control"[tiab]) AND (outpatient*[tiab] OR "primary care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])`

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
│   Evidence level hiện có: CÓ HẠN — có RCT nhưng chưa có SR (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)
│   → Có thể làm SR/MA tổng hợp các RCT này | ⚠ ClinicalTrials.gov: 4 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 20 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 0 | RCT: 19 | Guideline: 2 | Quan sát: 302
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy SR/MA trong PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "controlled hypertension"[tiab] OR "hypertension control"[tiab]) AND (outpatient*[tiab] OR "primary care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
│     • Có 4 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-CAT-NGANG-MO-TA.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "controlled hypertension"[tiab] OR "hypertension control"[tiab]) AND (outpatient*[tiab] OR "primary care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-CAT-NGANG-MO-TA.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed


### 3.2 Randomized Controlled Trials — ~19 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Barriers to Medication Adherence and Mild Cognitive Impairment Among African Americans with Persistently Uncontrolled Hypertension: A Cross-sectional Analysis from the Southeastern Collaboration Trial
     Singh S, Ringel JB, Baquero E, Cummings DM, Halladay J (2026). Journal of general internal medicine
     PMID: 42082844 | URL: https://pubmed.ncbi.nlm.nih.gov/42082844/
  2. Factors associated with blood pressure control in Swedish primary care patients with hypertension: a cross-sectional study.
     Brodin N, Wolff M, Borgström Bolmsjö B, Milos Nymberg V, Nymberg P (2026). Scandinavian journal of primary health care
     PMID: 40583484 | URL: https://pubmed.ncbi.nlm.nih.gov/40583484/
  3. A prospective cohort study of the SEARCH integrated HIV/hypertension community health worker-led intervention in rural Kenya and Uganda.
     Hickey MD, Owaraganise A, Ogachi S, Sunday H, Aoko C (2025). Journal of the International AIDS Society
     PMID: 40622370 | URL: https://pubmed.ncbi.nlm.nih.gov/40622370/
  4. A randomized trial of postpartum ibuprofen in severe hypertensive disorders of pregnancy.
     Penfield CA, Oakes MC, Caballero D, Marty LN, Berger DS (2025). American journal of obstetrics and gynecology
     PMID: 39938855 | URL: https://pubmed.ncbi.nlm.nih.gov/39938855/
  5. Patient Perceptions of Provider Race Concordance and Quality of Chronic Illness Care.
     Grant B, Soroka O, Baquero E, Ringel JB, Cherrington A (2025). Journal of general internal medicine
     PMID: 39843675 | URL: https://pubmed.ncbi.nlm.nih.gov/39843675/
  6. Effect of a Peer Health Coaching Intervention on Clinical Outcomes Among US Veterans With Cardiovascular Risks: The Vet-COACH Randomized Clinical Trial.
     Nelson KM, Taylor L, Williams JL, Rao M, Gray KE (2023). JAMA network open
     PMID: 37278999 | URL: https://pubmed.ncbi.nlm.nih.gov/37278999/
  7. Effect of eTansiyon smartphone application on hypertension control.
     Yilmaz E, Uzuner A, Bajgora M, Dogan B, Altikardes ZA (2022). Primary health care research & development
     PMID: 36259143 | URL: https://pubmed.ncbi.nlm.nih.gov/36259143/
  8. A village doctor-led multifaceted intervention for blood pressure control in rural China: an open, cluster randomised trial.
     Sun Y, Mu J, Wang DW, Ouyang N, Xing L (2022). Lancet (London, England)
     PMID: 35500594 | URL: https://pubmed.ncbi.nlm.nih.gov/35500594/
  9. Quality of Cardiovascular Disease Care in Small Urban Practices.
     Shelley D, Blechter B, Siman N, Jiang N, Cleland C (2018). Annals of family medicine
     PMID: 29632222 | URL: https://pubmed.ncbi.nlm.nih.gov/29632222/
  10. Patient education and follow-up as an intervention for hypertensive patients discharged from an emergency department: a randomized control trial study protocol.
     Gleason-Comstock J, Streater A, Ager J, Goodman A, Brody A (2015). BMC emergency medicine
     PMID: 26691646 | URL: https://pubmed.ncbi.nlm.nih.gov/26691646/
  11. Characteristics, drug combinations and dosages of primary care patients with uncontrolled ambulatory blood pressure and high medication adherence.
     Grigoryan L, Pavlik VN, Hyman DJ (2013). Journal of the American Society of Hypertension : JASH
     PMID: 23890931 | URL: https://pubmed.ncbi.nlm.nih.gov/23890931/
  12. Risk-adjusted versus overall blood pressure control rate for identifying the need for intensified cardiovascular risk reduction: lessons from a cross-sectional study.
     In der Schmitten J, Wegscheider K, Abholz HH, Mortsiefer A (2013). European journal of preventive cardiology
     PMID: 23253744 | URL: https://pubmed.ncbi.nlm.nih.gov/23253744/
  13. Factors associated with non-adherence to three hypertension self-management behaviors: preliminary data for a new instrument.
     Crowley MJ, Grubber JM, Olsen MK, Bosworth HB (2013). Journal of general internal medicine
     PMID: 22926634 | URL: https://pubmed.ncbi.nlm.nih.gov/22926634/
  14. Predictors of medication adherence for African American patients diagnosed with hypertension.
     Braverman J, Dedier J (2009). Ethnicity & disease
     PMID: 20073139 | URL: https://pubmed.ncbi.nlm.nih.gov/20073139/
  15. The effect of patient race and blood pressure control on patient-physician communication.
     Cené CW, Roter D, Carson KA, Miller ER, Cooper LA (2009). Journal of general internal medicine
     PMID: 19575270 | URL: https://pubmed.ncbi.nlm.nih.gov/19575270/


### 3.3 Guideline / Khuyến cáo — ~2 hit (số hit thật); liệt kê đủ 2 bài đã tải
  1. Resistant hypertension: diagnosis, evaluation, and treatment: a scientific statement from the American Heart Association Professional Education Committee of the Council for High Blood Pressure Researc
     Calhoun DA, Jones D, Textor S, Goff DC, Murphy TP (2008). Circulation
     PMID: 18574054 | URL: https://pubmed.ncbi.nlm.nih.gov/18574054/
  2. Resistant hypertension: diagnosis, evaluation, and treatment. A scientific statement from the American Heart Association Professional Education Committee of the Council for High Blood Pressure Researc
     Calhoun DA, Jones D, Textor S, Goff DC, Murphy TP (2008). Hypertension (Dallas, Tex. : 1979)
     PMID: 18391085 | URL: https://pubmed.ncbi.nlm.nih.gov/18391085/

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~302 hit (số hit thật); liệt kê đủ 14 bài đã tải
  1. Serial cross-sectional assessment of glycaemic and blood pressure profiles at a KwaZulu-Natal tertiary hospital: A 5-year analysis (2021-2025).
     Pillay S (2026). South African family practice : official journal of the South African Academy of Family Practice/Primary Care
     PMID: 43000718 | URL: https://pubmed.ncbi.nlm.nih.gov/43000718/
  2. Vascular risk factors after stroke in the older people: a population-based study.
     Iza Achutegui M, Rizzo F, Olive-Gadea M, Brunet J, Colangelo G (2026). BMC geriatrics
     PMID: 42907775 | URL: https://pubmed.ncbi.nlm.nih.gov/42907775/
  3. Hypertension epidemiology and primary care indicators in Portugal: a contemporary nationwide analysis.
     de Pinho R, Nogueira-Silva L, Lima Nogueira J, Abecasis F, Varela V (2026). Blood pressure
     PMID: 42822005 | URL: https://pubmed.ncbi.nlm.nih.gov/42822005/
  4. Hypertension Control in Bangladesh: Changes, Sociodemographic Variation, and Socioeconomic Inequality from the 2017-18 to 2022 Bangladesh Demographic and Health Surveys.
     Monower MM, Al Abid SU, Jubayer S, Bhuiyan MR, Al Mamun MA (2026). Global heart
     PMID: 42540706 | URL: https://pubmed.ncbi.nlm.nih.gov/42540706/
  5. Comparing the Documentation of Phosphatidylethanol and Alcohol History in Hypertension Management in Primary Care: A Cross-Sectional Study.
     Norrman A, Thurfjell Å, Hagströmer M, Adami J, Lundh L (2026). Journal of primary care & community health
     PMID: 42390343 | URL: https://pubmed.ncbi.nlm.nih.gov/42390343/
  6. Knowledge of Hypertension and Self-Blood Pressure Measurement Skills in Spain.
     Sitjar Suñer M, Pericot Mozo X, Noell Boix R, Aguilar Mas N, Masià Plana A (2026). Journal of primary care & community health
     PMID: 42348444 | URL: https://pubmed.ncbi.nlm.nih.gov/42348444/
  7. Hypertension management profiles in Chinese adults aged 60 years and older.
     Xia J, Chen Y, Pu D, Jiang X, Liu Y (2026). Frontiers in public health
     PMID: 42239000 | URL: https://pubmed.ncbi.nlm.nih.gov/42239000/
  8. [Epidemiological, clinical and therapeutic aspects of arterial hypertension in young adults at the Abidjan heart institute].
     Boka B, Djoma AH, Ateba N, Tano M, Oné J (2026). Annales de cardiologie et d'angeiologie
     PMID: 42191433 | URL: https://pubmed.ncbi.nlm.nih.gov/42191433/
  9. Factors impacting poor hypertension control in young urban adults in a Malaysian primary care clinic.
     Ibrahim AN, Jamil TR, Kamaludin R (2026). BMC primary care
     PMID: 42121043 | URL: https://pubmed.ncbi.nlm.nih.gov/42121043/
  10. Neighborhood level social determinants of health and loss of blood pressure control.
     Le JN, Huang TY, Botting PG, Albertson E, Bello NA (2026). American journal of hypertension
     PMID: 42108551 | URL: https://pubmed.ncbi.nlm.nih.gov/42108551/
  11. Prevalence and clinical correlates of hypertension among patients with type 2 diabetes in Spanish primary care: a cross-sectional study.
     Díaz Vera AS, Abellán Alemán J, Golac Rabanal MDS, Astudillo Astudillo MA, Zhuzhingo Vásquez CJ (2026). BMC primary care
     PMID: 42069528 | URL: https://pubmed.ncbi.nlm.nih.gov/42069528/
  12. Current postpartum management of hypertension: A survey of obstetricians, general practitioners, and midwives in the UK.
     Tucker K, Edmundson H, Stevens R, Chisholm A, Lavallee L (2026). Pregnancy hypertension
     PMID: 42013748 | URL: https://pubmed.ncbi.nlm.nih.gov/42013748/
  13. Remote Patient Monitoring Program Components and Short-Term Hypertension Control: Retrospective Cohort Study.
     LaPointe S, Merrill M (2026). JMIR mHealth and uHealth
     PMID: 41875030 | URL: https://pubmed.ncbi.nlm.nih.gov/41875030/
  14. Impact of Obesity on Patients with Resistant and Refractory Arterial Hypertension: A Cross-Sectional Study.
     Costa BVPLD, Bulhões F, Macedo C, Improta-Caria AC, Aras Júnior R (2026). Arquivos brasileiros de cardiologia
     PMID: 41849457 | URL: https://pubmed.ncbi.nlm.nih.gov/41849457/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 507 hit; trong 30 bản ghi lấy về có 18 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~302 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~8 hit (số hit thật); liệt kê đủ 8 bài đã tải
  1. Barriers to Medication Adherence and Mild Cognitive Impairment Among African Americans with Persistently Uncontrolled Hypertension: A Cross-sectional Analysis from the Southeastern Collaboration Trial
     Singh S, Ringel JB, Baquero E, Cummings DM, Halladay J (2026). Journal of general internal medicine
     PMID: 42082844 | URL: https://pubmed.ncbi.nlm.nih.gov/42082844/
  2. Factors associated with blood pressure control in Swedish primary care patients with hypertension: a cross-sectional study.
     Brodin N, Wolff M, Borgström Bolmsjö B, Milos Nymberg V, Nymberg P (2026). Scandinavian journal of primary health care
     PMID: 40583484 | URL: https://pubmed.ncbi.nlm.nih.gov/40583484/
  3. A prospective cohort study of the SEARCH integrated HIV/hypertension community health worker-led intervention in rural Kenya and Uganda.
     Hickey MD, Owaraganise A, Ogachi S, Sunday H, Aoko C (2025). Journal of the International AIDS Society
     PMID: 40622370 | URL: https://pubmed.ncbi.nlm.nih.gov/40622370/
  ... và 5 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [ACTIVE_NOT_RECRUITING] Implementing a Multi-component Hypertension Control Strategy in Rural Pakistan
     NCT06726057 | Pha: NA | Cỡ mẫu dự kiến: 3459 | Bắt đầu: 2024-12-01
     URL: https://clinicaltrials.gov/study/NCT06726057
  2. [COMPLETED] Resistant Hypertension in Patients With Type-II-Diabetes Mellitus
     NCT01056367 | Pha: — | Cỡ mẫu dự kiến: 180 | Bắt đầu: 2009-06
     URL: https://clinicaltrials.gov/study/NCT01056367
  3. [COMPLETED] Improving BP Control in Diverse Populations Using BP MAP
     NCT03818659 | Pha: NA | Cỡ mẫu dự kiến: 1238835 | Bắt đầu: 2019-07-01
     URL: https://clinicaltrials.gov/study/NCT03818659
  4. [COMPLETED] OPTImizing Precision of Hypertension Care to Maximize Blood Pressure Control Pilot (OPTI-BP Pilot)
     NCT02814552 | Pha: NA | Cỡ mẫu dự kiến: 47 | Bắt đầu: 2016-06-18
     URL: https://clinicaltrials.gov/study/NCT02814552
  5. [UNKNOWN] Potential Associated Factors of Uncontrolled Hypertension
     NCT02723643 | Pha: — | Cỡ mẫu dự kiến: 2000 | Bắt đầu: 2016-01
     URL: https://clinicaltrials.gov/study/NCT02723643

> **Đã tra ngày 2026-11-15: ~20 hồ sơ khớp, 4 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 31 bài từ 31 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** CÓ HẠN — có RCT nhưng chưa có SR (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy SR/MA trong PubMed, truy vấn G0 «(hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "controlled hypertension"[tiab] OR "hypertension control"[tiab]) AND (outpatient*[tiab] OR "primary care"[tiab]) AND (prevalence[tiab] OR "cross-sectional"[tiab])» — chỉ trong phạm vi một truy vấn, KHÔNG phải kết luận «chưa có tổng quan»
• Có 4 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 4 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 20 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-CAT-NGANG-MO-TA.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   SR/Meta-analysis (tổng hợp RCT hiện có) — ⚠ NHƯNG có 4...
│   Lý do: suy từ 0 SR/MA · 19 RCT · 302 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (31 bài tải về / 31 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-CAT-NGANG-MO-TA --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-CAT-NGANG-MO-TA` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-CAT-NGANG-MO-TA --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
