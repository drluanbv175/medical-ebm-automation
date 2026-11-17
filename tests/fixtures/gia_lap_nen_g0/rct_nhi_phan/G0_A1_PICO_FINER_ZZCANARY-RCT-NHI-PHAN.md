# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-RCT-NHI-PHAN
> Tạo tự động: 2026-11-15 19:51 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-RCT-NHI-PHAN`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Hiệu quả của tin nhắn nhắc uống thuốc so với chăm sóc thường quy lên tỷ lệ kiểm soát huyết áp sau 6 tháng ở người tăng huyết áp điều trị ngoại trú: thử nghiệm lâm sàng ngẫu nhiên có đối chứng
**Truy vấn PubMed:** `("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "short message"[tiab] OR "Text Messaging"[MeSH]) AND (hypertension[MeSH] OR hypertension[tiab] OR hypertensive[tiab]) AND (adherence[tiab] OR "Medication Adherence"[MeSH] OR "blood pressure control"[tiab] OR "blood pressure"[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 59 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 272 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 27 | RCT: 70 | Guideline: 0 | Quan sát: 31
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "short message"[tiab] OR "Text Messaging"[MeSH]) AND (hypertension[MeSH] OR hypertension[tiab] OR hypertensive[tiab]) AND (adherence[tiab] OR "Medication Adherence"[MeSH] OR "blood pressure control"[tiab] OR "blood pressure"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
│     • Có 59 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-RCT-NHI-PHAN.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "short message"[tiab] OR "Text Messaging"[MeSH]) AND (hypertension[MeSH] OR hypertension[tiab] OR hypertensive[tiab]) AND (adherence[tiab] OR "Medication Adherence"[MeSH] OR "blood pressure control"[tiab] OR "blood pressure"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-RCT-NHI-PHAN.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~27 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Effectiveness of Digital Health Interventions to Improve Self-Care in Patients With Chronic Diseases: Systematic Review and Meta-Analysis of Randomized Controlled Trials.
     Longhini J, Pedrotti D, Foladori F, Stedile M, Stefani F (2026). Journal of medical Internet research
     PMID: 42263266 | URL: https://pubmed.ncbi.nlm.nih.gov/42263266/
  2. Effectiveness of mobile health interventions on physical activity management in adults with hypertension: A systematic review and meta-analysis.
     Liu Y, Qin Y, Chen Q, Liu Y, Wang Z (2025). International journal of nursing studies
     PMID: 41101281 | URL: https://pubmed.ncbi.nlm.nih.gov/41101281/
  3. eHealth and Hypertensive Disorders of Pregnancy: Systematic Review.
     Hu H, Noori N, Lee V, Chow C, Cheung NW (2025). Journal of medical Internet research
     PMID: 40929717 | URL: https://pubmed.ncbi.nlm.nih.gov/40929717/
  4. A systematic review and meta-analysis of digital interventions targeting lifestyle factors in patients with hypertension.
     Lindsay-Perez A, Jurdon R, King T, Koffman L, Roberts N (2025). Journal of human hypertension
     PMID: 40764400 | URL: https://pubmed.ncbi.nlm.nih.gov/40764400/
  5. The effectiveness of the chronic disease management for hypertension: A systematic review and meta-analysis.
     Li Z, Wu J, Yuan W, Lan D, Chang R (2025). Medicine
     PMID: 40725928 | URL: https://pubmed.ncbi.nlm.nih.gov/40725928/
  6. The digital prescription: A systematic review and meta-analysis of smartphone apps for blood pressure control.
     Motta-Yanac E, Riley V, Ellis NJ, Mankoo A, Gidlow CJ (2025). International journal of medical informatics
     PMID: 39657401 | URL: https://pubmed.ncbi.nlm.nih.gov/39657401/
  7. The Effectiveness of Telemedicine in Hypertension Management of Adults in Rural Communities: A Systematic Review and Meta-Analysis.
     Dones V, Velasquez AAG, Dacuya MG, Ignacio KET, Cavite ETM (2025). Physiotherapy research international : the journal for researchers and clinicians in physical therapy
     PMID: 39635965 | URL: https://pubmed.ncbi.nlm.nih.gov/39635965/
  8. Mobile phone interventions to improve health outcomes among patients with chronic diseases: an umbrella review and evidence synthesis from 34 meta-analyses.
     Sun S, Simonsson O, McGarvey S, Torous J, Goldberg SB (2024). The Lancet. Digital health
     PMID: 39332937 | URL: https://pubmed.ncbi.nlm.nih.gov/39332937/
  9. Intervention strategies to improve adherence to treatment for selected chronic conditions in sub-Saharan Africa: a systematic review.
     Gumede SB, de Wit JBF, Venter WDF, Wensing AMJ, Lalla-Edward ST (2024). Journal of the International AIDS Society
     PMID: 38924296 | URL: https://pubmed.ncbi.nlm.nih.gov/38924296/
  10. The impact of non-pharmacological interventions on adherence to medication and persistence in dyslipidaemia and hypertension: a systematic review.
     Kengne AP, Brière JB, Gudiña IA, Jiang X, Kodjamanova P (2024). Expert review of pharmacoeconomics & outcomes research
     PMID: 38366854 | URL: https://pubmed.ncbi.nlm.nih.gov/38366854/
  11. Postpartum Home Blood Pressure Monitoring: A Systematic Review.
     Steele DW, Adam GP, Saldanha IJ, Kanaan G, Zahradnik ML (2023). Obstetrics and gynecology
     PMID: 37311173 | URL: https://pubmed.ncbi.nlm.nih.gov/37311173/
  12. Impact of mHealth Interventions on Supporting Dietary Adherence in Cardiovascular Disease: A Systematic Review.
     Thom SJM, Sivakumar B, Ayodele T, Tan MC, Brown JM (2023). Journal of nutrition education and behavior
     PMID: 37097263 | URL: https://pubmed.ncbi.nlm.nih.gov/37097263/
  13. Effectiveness, reach, uptake, and feasibility of digital health interventions for adults with hypertension: a systematic review and meta-analysis of randomised controlled trials.
     Siopis G, Moschonis G, Eweka E, Jung J, Kwasnicka D (2023). The Lancet. Digital health
     PMID: 36828607 | URL: https://pubmed.ncbi.nlm.nih.gov/36828607/
  14. Use of technology to prevent, detect, manage and control hypertension in sub-Saharan Africa: a systematic review.
     Stokes K, Oronti B, Cappuccio FP, Pecchia L (2022). BMJ open
     PMID: 35383086 | URL: https://pubmed.ncbi.nlm.nih.gov/35383086/
  15. Integration of text messaging interventions into hypertension management among older adults: A systematic review and meta-analysis.
     Tam HL, Leung LYL, Wong EML, Cheung K, Chan ASW (2022). Worldviews on evidence-based nursing
     PMID: 35014147 | URL: https://pubmed.ncbi.nlm.nih.gov/35014147/


### 3.2 Randomized Controlled Trials — ~70 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Health-Related Quality of Life in People Living with HIV andHypertension: Effects of a Short Message Service-Based Mobile HealthIntervention (MOPHADHIV Trial).
     Hongoro DJ, Kengne AP, Peer N, Nguyen K, Alaba OA (2026). AIDS and behavior
     PMID: 41975054 | URL: https://pubmed.ncbi.nlm.nih.gov/41975054/
  2. Effect of a mobile health intervention optimised with artificial intelligence on blood pressure and other cardiovascular risk factors in adults with high blood pressure: rationale and design of My Int
     Laranjo L, O'Hagan ET, Klimis H, Marschner S, Chow CK (2026). Open heart
     PMID: 41956556 | URL: https://pubmed.ncbi.nlm.nih.gov/41956556/
  3. Behavioral Economics and Medication Adherence for Hypertension: A Randomized Clinical Trial.
     Dodson JA, Adhikari S, Schoenthaler AM, Shimbo D, Berman AN (2026). Journal of the American College of Cardiology
     PMID: 41379039 | URL: https://pubmed.ncbi.nlm.nih.gov/41379039/
  4. Testing Optical Character Recognition of Home Blood Pressure Measurements, a Randomized Trial.
     Strom AJ, Khader E, Polgreen PM, Francis SL, Segre AM (2026). American journal of hypertension
     PMID: 41258999 | URL: https://pubmed.ncbi.nlm.nih.gov/41258999/
  5. Text Messaging and Video Stories to Support Hypertension Self-Management in Black Veterans: A Randomized Clinical Trial.
     Cutrona SL, McDannold SE, DeLaughter KL, Fix GM, Shimada SL (2025). JAMA network open
     PMID: 41191358 | URL: https://pubmed.ncbi.nlm.nih.gov/41191358/
  6. Impact of behavioral economics to improve antihypertensive therapy adherence, a pilot randomized controlled trial in Los Angeles.
     Linnemayr S, Ghai I, Palimaru A, Barajas D, Vallejo R (2025). Scientific reports
     PMID: 41188444 | URL: https://pubmed.ncbi.nlm.nih.gov/41188444/
  7. Behavioral Economic Framing for Enrollment and Retention of Patients in Remote Blood Pressure Monitoring: A Randomized Clinical Trial.
     Mehta SJ, Teel J, Okorie E, Reitz C, Purcell A (2025). JAMA network open
     PMID: 40892409 | URL: https://pubmed.ncbi.nlm.nih.gov/40892409/
  8. Efficacy of short message service (SMS) intervention on medication adherence and knowledge of stroke prevention among clinic attendees at risk of stroke: a randomized controlled trial.
     Aigbonoga D, Adewale B, Igwilo J, Adeyeye V, Olajide T (2025). BMC public health
     PMID: 40108568 | URL: https://pubmed.ncbi.nlm.nih.gov/40108568/
  9. Health-promoting text messages to patients with hypertension-A randomized controlled trial in Swedish primary healthcare.
     Borgström Bolmsjö B, Bredfelt J, Calling S, Glock H, Nymberg VM (2025). PloS one
     PMID: 39937817 | URL: https://pubmed.ncbi.nlm.nih.gov/39937817/
  10. Automated Text Message-Based Program to Improve Uncontrolled Blood Pressure in Primary Care Patients: A Randomized Clinical Trial.
     Bressman E, Profka K, Norton L, Clark K, Mahraj K (2025). Journal of general internal medicine
     PMID: 39633105 | URL: https://pubmed.ncbi.nlm.nih.gov/39633105/
  11. The Influence of Commonly-Encountered Participant Behaviors on Cardiovascular Indices During Testing.
     McLaurin NN, Alhalimi T, Ramos A, Trevino G, Tanaka H (2025). American journal of hypertension
     PMID: 39582112 | URL: https://pubmed.ncbi.nlm.nih.gov/39582112/
  12. Use of text messages to promote medication adherence and reduce blood pressure in patients with hypertension: the ESSENCE study.
     Canguçu E, Castro PR, Moreira PM, Bandeira P, Almeida K (2024). Cadernos de saude publica
     PMID: 39775770 | URL: https://pubmed.ncbi.nlm.nih.gov/39775770/
  13. Remote Blood Pressure Monitoring With Social Support for Patients With Hypertension: A Randomized Clinical Trial.
     Mehta SJ, Volpp KG, Troxel AB, Teel J, Reitz CR (2024). JAMA network open
     PMID: 38829618 | URL: https://pubmed.ncbi.nlm.nih.gov/38829618/
  14. Educational Program with Text Messaging for Community-Dwelling Patients with Hypertension: A Pilot Randomized Controlled Trial.
     Tam HL, Wong EML, Cheung K (2023). Asian nursing research
     PMID: 37295501 | URL: https://pubmed.ncbi.nlm.nih.gov/37295501/
  15. Reach Out Emergency Department: A Randomized Factorial Trial to Determine the Optimal Mobile Health Components to Reduce Blood Pressure.
     Skolarus LE, Dinh M, Kidwell KM, Lin CC, Buis LR (2023). Circulation. Cardiovascular quality and outcomes
     PMID: 37192282 | URL: https://pubmed.ncbi.nlm.nih.gov/37192282/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~31 hit (số hit thật); liệt kê đủ 14 bài đã tải
  1. Patient Empowerment and Digital Health Readiness for Diabetes and Hypertension Care in Rwanda.
     Ntakirutimana I, Uwase M, Kayiranga D, Mugisha E, Twizere C (2026). Studies in health technology and informatics
     PMID: 42394059 | URL: https://pubmed.ncbi.nlm.nih.gov/42394059/
  2. Effectiveness of text messaging intervention for blood pressure control and medication adherence among patients with uncontrolled hypertension in India: Design and rationale of the SMS4BP randomized c
     Longkumer I, Bhatia R, Subramanian SV, Sharma G, Singh MB (2026). Contemporary clinical trials
     PMID: 41980662 | URL: https://pubmed.ncbi.nlm.nih.gov/41980662/
  3. Intention to use mobile text message reminders for medication adherence among hypertensive patients in North West Ethiopia: a cross-sectional study.
     Zewdu EM, Demessie A, Nigatu AM, Baykemagn ND (2024). BMC health services research
     PMID: 39578837 | URL: https://pubmed.ncbi.nlm.nih.gov/39578837/
  4. Lipidomic studies revealing serological markers associated with the occurrence of retinopathy in type 2 diabetes.
     He M, Hou G, Liu M, Peng Z, Guo H (2024). Journal of translational medicine
     PMID: 38741137 | URL: https://pubmed.ncbi.nlm.nih.gov/38741137/
  5. Report from a text-based blood pressure monitoring prospective cohort trial among postpartum women with hypertensive disorders of pregnancy.
     Moustafa ASZ, Yimer W, Perry A, Solis L, Belk S (2024). BMC pregnancy and childbirth
     PMID: 38702619 | URL: https://pubmed.ncbi.nlm.nih.gov/38702619/
  6. Effect of Weekly Text Messaging Reminders on Medication Adherence in Hypertension and Type 2 Diabetes Mellitus at a Tertiary Care Center in Eastern Nepal.
     Sarraf DP, Rauniar GP, Gupta PP, Maskey R, Kattel V (2023). Kathmandu University medical journal (KUMJ)
     PMID: 38628013 | URL: https://pubmed.ncbi.nlm.nih.gov/38628013/
  7. Associations of Contemporary Screen Time Modalities With Early Adolescent Nutrition.
     Nagata JM, Weinstein S, Bashir A, Lee S, Al-Shoaibi AAA (2024). Academic pediatrics
     PMID: 38311068 | URL: https://pubmed.ncbi.nlm.nih.gov/38311068/
  8. Joint Modeling of Blood Pressure Measurements and Survival Time to Cardiovascular Disease Complication among Hypertension Patients Follow-up at DebreTabor Hospital, Ethiopia.
     Zelelew AN, Workie DL (2023). Vascular health and risk management
     PMID: 37753512 | URL: https://pubmed.ncbi.nlm.nih.gov/37753512/
  9. Quality Assessment of Hypertension Treatment-Related Information on WeChat: Cross-sectional Study.
     Yang Y, Hou M, Gong X, Guo R, Feng XL (2022). Journal of medical Internet research
     PMID: 36287598 | URL: https://pubmed.ncbi.nlm.nih.gov/36287598/
  10. Identifying Medication-Related Intents From a Bidirectional Text Messaging Platform for Hypertension Management Using an Unsupervised Learning Approach: Retrospective Observational Pilot Study.
     Davoudi A, Lee NS, Luong T, Delaney T, Asch E (2022). Journal of medical Internet research
     PMID: 35767327 | URL: https://pubmed.ncbi.nlm.nih.gov/35767327/
  11. Predictors of Smartphone and Tablet Use Among Patients With Hypertension: Secondary Analysis of Health Information National Trends Survey Data.
     Eze CE, West BT, Dorsch MP, Coe AB, Lester CA (2022). Journal of medical Internet research
     PMID: 35072647 | URL: https://pubmed.ncbi.nlm.nih.gov/35072647/
  12. Supplement study update for Reach Out: a multi-arm randomized trial of behavioral interventions for hypertension initiated in the emergency department: Reach Out Cognition.
     Skolarus LE, Dinh M, Kidwell KM, Farhan Z, Whitfield C (2021). Trials
     PMID: 34819115 | URL: https://pubmed.ncbi.nlm.nih.gov/34819115/
  13. Implementation of a text-based postpartum blood pressure monitoring program at 3 different academic sites.
     Janssen MK, Demers S, Srinivas SK, Bailey SC, Boggess KA (2021). American journal of obstetrics & gynecology MFM
     PMID: 34329800 | URL: https://pubmed.ncbi.nlm.nih.gov/34329800/
  14. Awareness Development and Usage of Mobile Health Technology Among Individuals With Hypertension in a Rural Community of Bangladesh: Randomized Controlled Trial.
     Jahan Y, Rahman MM, Faruque ASG, Chisti MJ, Kazawa K (2020). Journal of medical Internet research
     PMID: 33284129 | URL: https://pubmed.ncbi.nlm.nih.gov/33284129/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 280 hit; trong 29 bản ghi lấy về có 19 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~31 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~44 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Effectiveness of Digital Health Interventions to Improve Self-Care in Patients With Chronic Diseases: Systematic Review and Meta-Analysis of Randomized Controlled Trials.
     Longhini J, Pedrotti D, Foladori F, Stedile M, Stefani F (2026). Journal of medical Internet research
     PMID: 42263266 | URL: https://pubmed.ncbi.nlm.nih.gov/42263266/
  2. Effectiveness of mobile health interventions on physical activity management in adults with hypertension: A systematic review and meta-analysis.
     Liu Y, Qin Y, Chen Q, Liu Y, Wang Z (2025). International journal of nursing studies
     PMID: 41101281 | URL: https://pubmed.ncbi.nlm.nih.gov/41101281/
  3. eHealth and Hypertensive Disorders of Pregnancy: Systematic Review.
     Hu H, Noori N, Lee V, Chow C, Cheung NW (2025). Journal of medical Internet research
     PMID: 40929717 | URL: https://pubmed.ncbi.nlm.nih.gov/40929717/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [COMPLETED] Effect on the Adherence to Glaucoma Eye Drops by Improving Patient Understanding and Using a Tele-reminder System
     NCT04317573 | Pha: PHASE2 | Cỡ mẫu dự kiến: 59 | Bắt đầu: 2018-10-19
     URL: https://clinicaltrials.gov/study/NCT04317573
  2. [COMPLETED] Remote Surveillance of Postpartum Hypertension
     NCT03185455 | Pha: NA | Cỡ mẫu dự kiến: 206 | Bắt đầu: 2016-08-22
     URL: https://clinicaltrials.gov/study/NCT03185455
  3. [COMPLETED] Use of Low-cost mHealth Intervention to Enhance Outcomes of Noncommunicable Diseases Care in Rural and Refugee Settings
     NCT03580330 | Pha: NA | Cỡ mẫu dự kiến: 2359 | Bắt đầu: 2014-04-17
     URL: https://clinicaltrials.gov/study/NCT03580330
  4. [COMPLETED] Improving Adherence and Outcomes by Artificial Intelligence-Adapted Text Messages
     NCT02454660 | Pha: NA | Cỡ mẫu dự kiến: 49 | Bắt đầu: 2015-05
     URL: https://clinicaltrials.gov/study/NCT02454660
  5. [RECRUITING] Cardiovascular Risk Assessment and Dynamic Monitoring-based Prevention Trial
     NCT05919056 | Pha: NA | Cỡ mẫu dự kiến: 22032 | Bắt đầu: 2023-07-06
     URL: https://clinicaltrials.gov/study/NCT05919056

> **Đã tra ngày 2026-11-15: ~272 hồ sơ khớp, 59 đang/sắp tuyển.**
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
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("text messaging"[tiab] OR "text message"[tiab] OR SMS[tiab] OR "short message"[tiab] OR "Text Messaging"[MeSH]) AND (hypertension[MeSH] OR hypertension[tiab] OR hypertensive[tiab]) AND (adherence[tiab] OR "Medication Adherence"[MeSH] OR "blood pressure control"[tiab] OR "blood pressure"[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Có 59 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 59 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 272 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-RCT-NHI-PHAN.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 27 SR/MA · 70 RCT · 31 quan sát (số hit, chưa sàng lọc)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-RCT-NHI-PHAN --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-RCT-NHI-PHAN` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-RCT-NHI-PHAN --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
