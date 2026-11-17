# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-RCT-KHONG-KEM
> Tạo tự động: 2026-11-16 18:35 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-RCT-KHONG-KEM`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Tái khám qua điện thoại so với tái khám trực tiếp trong kiểm soát huyết áp sau 6 tháng ở người tăng huyết áp điều trị ngoại trú: thử nghiệm ngẫu nhiên không kém hơn
**Truy vấn PubMed:** `(telephone[tiab] OR telemedicine[tiab] OR "remote consultation"[tiab] OR telemonitoring[tiab]) AND (hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "blood pressure"[tiab]) AND (non-inferiority[tiab] OR noninferiority[tiab] OR follow-up[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 93 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 380 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 17 | RCT: 85 | Guideline: 1 | Quan sát: 105
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN — bác sĩ tự xác định khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
│     • Có 93 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-RCT-KHONG-KEM.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-16)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `(telephone[tiab] OR telemedicine[tiab] OR "remote consultation"[tiab] OR telemonitoring[tiab]) AND (hypertension[MeSH] OR hypertension[tiab]) AND ("blood pressure control"[tiab] OR "blood pressure"[tiab]) AND (non-inferiority[tiab] OR noninferiority[tiab] OR follow-up[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-RCT-KHONG-KEM.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~17 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Clinical effectiveness of telepharmacy services in patients with non-communicable diseases in ambulatory care settings.
     Sugita H, Sato MT, Yamaji N, Maeda M, Ichimura T (2026). The Cochrane database of systematic reviews
     PMID: 42283624 | URL: https://pubmed.ncbi.nlm.nih.gov/42283624/
  2. eHealth and Hypertensive Disorders of Pregnancy: Systematic Review.
     Hu H, Noori N, Lee V, Chow C, Cheung NW (2025). Journal of medical Internet research
     PMID: 40929717 | URL: https://pubmed.ncbi.nlm.nih.gov/40929717/
  3. Postpartum remote blood pressure monitoring and risk of hypertensive-related readmission: systematic review and meta-analysis of randomized controlled trials.
     Zullo F, Di Mascio D, Amro FH, Sorrenti S, D'Alberti E (2025). Journal of perinatal medicine
     PMID: 40123081 | URL: https://pubmed.ncbi.nlm.nih.gov/40123081/
  4. Remote blood pressure monitoring in women at risk of or with hypertensive disorders of pregnancy: A systematic review and meta-analysis.
     Rajkumar T, Hennessy A, Makris A (2025). International journal of gynaecology and obstetrics: the official organ of the International Federation of Gynaecology and Obstetrics
     PMID: 39611763 | URL: https://pubmed.ncbi.nlm.nih.gov/39611763/
  5. Managing cardiovascular risk factors with telemedicine in primary care: A systematic review and meta-analysis of patients with arterial hypertension and type 2 diabetes.
     Mihevc M, Virtič Potočnik T, Zavrnik Č, Klemenc-Ketiš Z, Poplas Susič A (2025). Chronic illness
     PMID: 39194352 | URL: https://pubmed.ncbi.nlm.nih.gov/39194352/
  6. Effectiveness of digital health interventions for telemedicine/telehealth for managing blood pressure in adults: a systematic review and meta-analysis.
     Sakima A, Akagi Y, Akasaki Y, Fujii T, Haze T (2025). Hypertension research : official journal of the Japanese Society of Hypertension
     PMID: 38977877 | URL: https://pubmed.ncbi.nlm.nih.gov/38977877/
  7. Effectiveness and compliance of telemedicine on blood pressure management in poststroke patients: a systematic review and meta-analysis of randomised controlled trials.
     Yang Y, Xu H, Chang W, Li C, Cao P (2024). BMJ open
     PMID: 39719284 | URL: https://pubmed.ncbi.nlm.nih.gov/39719284/
  8. Telemedical strategies for improving systolic blood pressure control in secondary prevention of cerebrovascular events-a systematic review and meta-analysis.
     Munir A, Farooqi HA, Nabi R, Hasnain U, Khan M (2024). Journal of stroke and cerebrovascular diseases : the official journal of National Stroke Association
     PMID: 39357612 | URL: https://pubmed.ncbi.nlm.nih.gov/39357612/
  9. Postpartum Home Blood Pressure Monitoring: A Systematic Review.
     Steele DW, Adam GP, Saldanha IJ, Kanaan G, Zahradnik ML (2023). Obstetrics and gynecology
     PMID: 37311173 | URL: https://pubmed.ncbi.nlm.nih.gov/37311173/
  10. Nurse-led Telehealth Intervention for Rehabilitation (Telerehabilitation) Among Community-Dwelling Patients With Chronic Diseases: Systematic Review and Meta-analysis.
     Lee AYL, Wong AKC, Hung TTM, Yan J, Yang S (2022). Journal of medical Internet research
     PMID: 36322107 | URL: https://pubmed.ncbi.nlm.nih.gov/36322107/
  11. Success factors in high-effect, low-cost eHealth programs for patients with hypertension: a systematic review and meta-analysis.
     Blok S, van der Linden EL, Somsen GA, Tulevski II, Winter MM (2021). European journal of preventive cardiology
     PMID: 34929044 | URL: https://pubmed.ncbi.nlm.nih.gov/34929044/
  12. Digital telemedicine interventions for patients with multimorbidity: a systematic review and meta-analysis.
     Kraef C, van der Meirschen M, Free C (2020). BMJ open
     PMID: 33051232 | URL: https://pubmed.ncbi.nlm.nih.gov/33051232/
  13. Understanding Moderators of Home Blood Pressure Telemonitoring Systems in Urban Hypertensive Patients: A Systematic Review and Meta-Analysis.
     Choi WS, Shin IS, Yang JS (2020). Telemedicine journal and e-health : the official journal of the American Telemedicine Association
     PMID: 31855113 | URL: https://pubmed.ncbi.nlm.nih.gov/31855113/
  14. [The Use of Telemedicine Interventions to Improve Hypertension Management Among Racial Ethnic Minorities: A Systematic Review].
     Li WW, Lai WS (2016). Hu li za zhi The journal of nursing
     PMID: 27492293 | URL: https://pubmed.ncbi.nlm.nih.gov/27492293/
  15. Interactive telemedicine: effects on professional practice and health care outcomes.
     Flodgren G, Rachas A, Farmer AJ, Inzitari M, Shepperd S (2015). The Cochrane database of systematic reviews
     PMID: 26343551 | URL: https://pubmed.ncbi.nlm.nih.gov/26343551/


### 3.2 Randomized Controlled Trials — ~85 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. A Remote Chronic Disease Management Program to Improve Cardiovascular and Metabolic Outcomes in a Diverse Community-Based Diabetic Population: Study Design of the TAMIS Trial.
     Barros RC, Stephanus A, Filho JAB, Mariana E, Botelho Y (2026). Journal of evaluation in clinical practice
     PMID: 42053330 | URL: https://pubmed.ncbi.nlm.nih.gov/42053330/
  2. A randomized controlled trial comparing remote blood pressure monitoring with office-based blood pressure monitoring for women at high risk of preeclampsia.
     Rajkumar T, Hennessy A, Shanmugalingam R, You W, Canty A (2026). American journal of obstetrics and gynecology
     PMID: 42025715 | URL: https://pubmed.ncbi.nlm.nih.gov/42025715/
  3. Women's Postpartum Experiences of Hypertensive Disorders of Pregnancy: A Qualitative Study of Barriers and Enablers to Healthy Lifestyle Behaviours.
     Roberts L, Rossiter C, Denney-Wilson E, Gow M, Henry A (2026). International journal of environmental research and public health
     PMID: 41595894 | URL: https://pubmed.ncbi.nlm.nih.gov/41595894/
  4. Targeting better hypertension control with the usage of the ESH smartphone application.
     Konstantinidis D, Siafi E, Iliakis P, Mihas C, Tatakis F (2026). European journal of preventive cardiology
     PMID: 40273398 | URL: https://pubmed.ncbi.nlm.nih.gov/40273398/
  5. Efficiency of remote monitoring and guidance in blood pressure management: a randomized controlled trial : The role of remote monitoring in improving hypertension management.
     Teng TQ, Sun GX, Yu ZY, Liu ZS, Wang T (2025). BMC medicine
     PMID: 40764960 | URL: https://pubmed.ncbi.nlm.nih.gov/40764960/
  6. A prospective cohort study of the SEARCH integrated HIV/hypertension community health worker-led intervention in rural Kenya and Uganda.
     Hickey MD, Owaraganise A, Ogachi S, Sunday H, Aoko C (2025). Journal of the International AIDS Society
     PMID: 40622370 | URL: https://pubmed.ncbi.nlm.nih.gov/40622370/
  7. Impact of 12-Month mHealth Home Telemonitoring on Clinical Outcomes in Older Individuals With Hypertension and Type 2 Diabetes: Multicenter Randomized Controlled Trial.
     Mihevc M, Mori Lukančič M, Zavrnik Č, Virtič Potočnik T, Ružić Gorenjec N (2025). JMIR mHealth and uHealth
     PMID: 40440692 | URL: https://pubmed.ncbi.nlm.nih.gov/40440692/
  8. Long-Term Effect of Intensive vs Standard Blood Pressure Control on Mild Cognitive Impairment and Probable Dementia in SPRINT.
     Reboussin DM, Gaussoin SA, Pajewski NM, Jaeger BC, Sachs B (2025). Neurology
     PMID: 39819096 | URL: https://pubmed.ncbi.nlm.nih.gov/39819096/
  9. Phone-based telemonitoring of arterial hypertension versus usual care: the HOROSCOPE study.
     Saafi M, Bel Haj Ali K, Dhaoui R, Toumia M, Sassi S (2025). Hypertension research : official journal of the Japanese Society of Hypertension
     PMID: 39695330 | URL: https://pubmed.ncbi.nlm.nih.gov/39695330/
  10. Home Blood Pressure Telemonitoring and Nurse Case Management in Black and Hispanic Patients With Stroke: A Randomized Clinical Trial.
     Ogedegbe G, Teresi JA, Williams SK, Ogunlade A, Izeogu C (2024). JAMA
     PMID: 38842799 | URL: https://pubmed.ncbi.nlm.nih.gov/38842799/
  11. Nurse-Led Strategy to Improve Blood Pressure and Cholesterol Level Among People With HIV: A Randomized Clinical Trial.
     Longenecker CT, Jones KA, Hileman CO, Okeke NL, Gripshover BM (2024). JAMA network open
     PMID: 38441897 | URL: https://pubmed.ncbi.nlm.nih.gov/38441897/
  12. Effect of Home Blood Pressure Telemonitoring Plus Additional Support on Blood Pressure Control: A Randomized Clinical Trial.
     Meng WW, Bai YY, Yan L, Zheng W, Zeng Q (2023). Biomedical and environmental sciences : BES
     PMID: 37424245 | URL: https://pubmed.ncbi.nlm.nih.gov/37424245/
  13. Urinary proteomics combined with home blood pressure telemonitoring for health care reform trial-First progress report.
     Chori BS, An DW, Martens DS, Yu YL, Gilis-Malinowska N (2023). Journal of clinical hypertension (Greenwich, Conn.)
     PMID: 37147930 | URL: https://pubmed.ncbi.nlm.nih.gov/37147930/
  14. Effect of a Multicomponent Intervention Delivered on a Web-Based Platform on Hypertension Control: A Cluster Randomized Clinical Trial.
     Zhou H, Wang X, Yang Y, Chen Z, Zhang L (2022). JAMA network open
     PMID: 36477479 | URL: https://pubmed.ncbi.nlm.nih.gov/36477479/
  15. Comparing Pharmacist-Led Telehealth Care and Clinic-Based Care for Uncontrolled High Blood Pressure: The Hyperlink 3 Pragmatic Cluster-Randomized Trial.
     Margolis KL, Bergdall AR, Crain AL, JaKa MM, Anderson JP (2022). Hypertension (Dallas, Tex. : 1979)
     PMID: 36281763 | URL: https://pubmed.ncbi.nlm.nih.gov/36281763/


### 3.3 Guideline / Khuyến cáo — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. [Optimizing blood pressure control through telemedicine in Primary Care in Spain (Iniciativa Óptima): Results from a Delphi study].
     Sánchez Peinador C, Torras Borrell J, Castillo Moraga MJ, Egocheaga Cabello MI, Rodríguez Villalón X (2022). Atencion primaria
     PMID: 35588550 | URL: https://pubmed.ncbi.nlm.nih.gov/35588550/

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~105 hit (số hit thật); liệt kê đủ 12 bài đã tải
  1. Outcomes Associated With a WhatsApp-Based Telehealth Education Program and Remote Follow-Up on Blood Pressure, Medication Adherence, and Self-Care: Formative Quasi-Experimental Pilot Study.
     Salhab D, AlALi NM, Al-Naamani ZY, AlJarrah A (2026). JMIR formative research
     PMID: 42970781 | URL: https://pubmed.ncbi.nlm.nih.gov/42970781/
  2. Health system competence and care continuity in patients with hypertension: electronic cohort in Uruguay.
     Guglielmino M, Roberti J, Mazzoni A, Prado C, Gutiérrez L (2026). Blood pressure
     PMID: 42560143 | URL: https://pubmed.ncbi.nlm.nih.gov/42560143/
  3. First population-based study on non-communicable diseases and risk factors in northeastern Iran: Sabzevar cohort profile.
     Ghorat F, Chaman R, Javadinia SA, Rad M, Mohammadzadeh M (2026). BMJ open
     PMID: 41927288 | URL: https://pubmed.ncbi.nlm.nih.gov/41927288/
  4. The association between pro-inflammatory diet and incidence of hypertension: a prospective cohort study.
     Nikpour A, Pourmontaseri H, Sepehrinia M, Vahid F, Farjam M (2026). Hypertension research : official journal of the Japanese Society of Hypertension
     PMID: 41741627 | URL: https://pubmed.ncbi.nlm.nih.gov/41741627/
  5. Dietary Patterns and Indicators of Cognitive Function.
     Chen H, Cortese M, Flores-Torres MH, Tessier AJ, Wang DD (2026). JAMA neurology
     PMID: 41729538 | URL: https://pubmed.ncbi.nlm.nih.gov/41729538/
  6. Home Blood Pressure Telemonitoring and Hypertension Management in Kenya: A Feasibility Study (HBPT-K).
     van Steenkiste J, Mbau L, Nguchu H, Okinda K, de Neef R (2026). Global heart
     PMID: 41541610 | URL: https://pubmed.ncbi.nlm.nih.gov/41541610/
  7. Development and internal validation of the goliat score to predict 48-hour complications after minor/moderate traumatic brain injury in the emergency department: a single-center cohort study.
     Yuguero O, López-Vena I, Martinez-Alonso M, Vena A, Bernal M (2025). BMC emergency medicine
     PMID: 41454226 | URL: https://pubmed.ncbi.nlm.nih.gov/41454226/
  8. Safety and impact of self-monitoring blood pressure through a digital platform in high-risk pregnancies in 11 hospitals: The multicenter before-after SAFE@home II study.
     Moes SL, Depmann M, Kvamme I, Schuit E, In 't Anker E (2025). Pregnancy hypertension
     PMID: 41197208 | URL: https://pubmed.ncbi.nlm.nih.gov/41197208/
  9. Factors influencing pregnant women's use of antenatal and emergency care services covered by social security: findings from the maternal eCohort in Mexico.
     Doubova SV, Cruz MP, Perez-Moran D, Cortes LRG, Anrubio GE (2025). BMC pregnancy and childbirth
     PMID: 41188792 | URL: https://pubmed.ncbi.nlm.nih.gov/41188792/
  10. Telecardiology Management of Hypertension in Brazilian Remote Populations.
     Accorsi TAD, Geovanini GR, Eduardo AA, Amaral BDR, Moreira FT (2026). Telemedicine journal and e-health : the official journal of the American Telemedicine Association
     PMID: 41022548 | URL: https://pubmed.ncbi.nlm.nih.gov/41022548/
  11. Telemedicine Booths for Screening Cardiovascular Risk Factors: Prospective Multicenter Study.
     Decambron M, Tchikladze Merand C (2025). JMIR human factors
     PMID: 40262175 | URL: https://pubmed.ncbi.nlm.nih.gov/40262175/
  12. Patient-specific multifactorial mortality risk assessment using classification and regression tree analysis in the context of ambulatory blood pressure monitoring.
     Çetin BT, Hasbal NB, Cevik E, Sahin OE, Akyol M (2025). Journal of nephrology
     PMID: 39503965 | URL: https://pubmed.ncbi.nlm.nih.gov/39503965/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 299 hit; trong 29 bản ghi lấy về có 16 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~105 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~39 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. 2021 Spanish Society of Hypertension position statement about telemedicine.
     Gijón-Conde T, Rubio E, Gorostidi M, Vinyoles E, Armario P (2021). Hipertension y riesgo vascular
     PMID: 33888438 | URL: https://pubmed.ncbi.nlm.nih.gov/33888438/
  2. [Optimizing blood pressure control through telemedicine in Primary Care in Spain (Iniciativa Óptima): Results from a Delphi study].
     Sánchez Peinador C, Torras Borrell J, Castillo Moraga MJ, Egocheaga Cabello MI, Rodríguez Villalón X (2022). Atencion primaria
     PMID: 35588550 | URL: https://pubmed.ncbi.nlm.nih.gov/35588550/
  3. Clinical effectiveness of telepharmacy services in patients with non-communicable diseases in ambulatory care settings.
     Sugita H, Sato MT, Yamaji N, Maeda M, Ichimura T (2026). The Cochrane database of systematic reviews
     PMID: 42283624 | URL: https://pubmed.ncbi.nlm.nih.gov/42283624/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [NOT_YET_RECRUITING] Nutrition Intervention Combined With Resmetirom for MASH
     NCT07680478 | Pha: PHASE4 | Cỡ mẫu dự kiến: 120 | Bắt đầu: 2026-10-01
     URL: https://clinicaltrials.gov/study/NCT07680478
  2. [UNKNOWN] Renal Sympathetic Denervation for Patients With Chronic Heart Failure
     NCT01790906 | Pha: NA | Cỡ mẫu dự kiến: 200 | Bắt đầu: 2013-01
     URL: https://clinicaltrials.gov/study/NCT01790906
  3. [COMPLETED] Groceries for Black Residents of Boston to Stop Hypertension Among Adults With Treated Hypertension
     NCT05393232 | Pha: NA | Cỡ mẫu dự kiến: 176 | Bắt đầu: 2022-10-13
     URL: https://clinicaltrials.gov/study/NCT05393232
  4. [COMPLETED] Evaluation of Quality of Care - Patient Empowerment Programme, HA
     NCT01935349 | Pha: — | Cỡ mẫu dự kiến: 2496 | Bắt đầu: 2010-09
     URL: https://clinicaltrials.gov/study/NCT01935349
  5. [NOT_YET_RECRUITING] Vertebrobasilar Dolichoectasia Treatment With Amiloride
     NCT07634068 | Pha: PHASE2 | Cỡ mẫu dự kiến: 6 | Bắt đầu: 2026-06
     URL: https://clinicaltrials.gov/study/NCT07634068

> **Đã tra ngày 2026-11-16: ~380 hồ sơ khớp, 93 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 44 bài từ 44 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN — bác sĩ tự xác định khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
• Có 93 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 93 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 380 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-RCT-KHONG-KEM.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 17 SR/MA · 85 RCT · 105 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (44 bài tải về / 44 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-RCT-KHONG-KEM --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-RCT-KHONG-KEM` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-RCT-KHONG-KEM --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
