# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-DOI-CHUNG-QFT
> Tạo tự động: 2026-11-23 19:32 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-DOI-CHUNG-QFT`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Tỷ lệ nhiễm lao tiềm ẩn chẩn đoán bằng QuantiFERON-TB Gold Plus và yếu tố liên quan ở người lớn tiếp xúc gần với người bệnh lao phổi tại Kampala, Uganda: phân tích thứ cấp bộ dữ liệu cắt ngang công khai
**Truy vấn PubMed:** `("Interferon-gamma Release Tests"[MeSH] OR QuantiFERON[tiab] OR "interferon gamma release"[tiab]) AND ("Contact Tracing"[MeSH] OR contacts[tiab] OR "household contacts"[tiab]) AND ("Latent Tuberculosis"[MeSH] OR "latent tuberculosis"[tiab] OR "tuberculosis infection"[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 5 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 21 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 10 | RCT: 8 | Guideline: 2 | Quan sát: 173
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN — bác sĩ tự xác định khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
│     • Có 5 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-DOI-CHUNG-QFT.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-23)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Interferon-gamma Release Tests"[MeSH] OR QuantiFERON[tiab] OR "interferon gamma release"[tiab]) AND ("Contact Tracing"[MeSH] OR contacts[tiab] OR "household contacts"[tiab]) AND ("Latent Tuberculosis"[MeSH] OR "latent tuberculosis"[tiab] OR "tuberculosis infection"[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-DOI-CHUNG-QFT.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~10 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Prevalence of latent tuberculosis infection in Malaysia: the first systematic review and meta-analysis.
     Wada Y, Afolabi HA, Irekeola AA, Bello KE, Yean CY (2026). BMC infectious diseases
     PMID: 42021170 | URL: https://pubmed.ncbi.nlm.nih.gov/42021170/
  2. Effect of BCG vaccination on the progression of latent tuberculosis infection to active disease in contacts: a systematic review and meta-analysis.
     Cai S, Yan T, Yang Y, Guo X, Li X (2025). BMC infectious diseases
     PMID: 41444517 | URL: https://pubmed.ncbi.nlm.nih.gov/41444517/
  3. Performance of QuantiFERON tests for detecting latent tuberculosis infections: A Meta-analysis.
     Weyesa JB, Legesse M, Gumi B, Medhin G, Tolossa K (2025). Immunologic research
     PMID: 41144091 | URL: https://pubmed.ncbi.nlm.nih.gov/41144091/
  4. Effectiveness of the primary Bacillus Calmette-Guérin vaccine against the risk of Mycobacterium tuberculosis infection and tuberculosis disease: a meta-analysis of individual participant data.
     Pelzer PT, Stuck L, Martinez L, Richards AS, Acuña-Villaorduña C (2025). The Lancet. Microbe
     PMID: 39709975 | URL: https://pubmed.ncbi.nlm.nih.gov/39709975/
  5. Mycobacterium tuberculosis Infection in School Contacts of Tuberculosis Cases: A Systematic Review and Meta-Analysis.
     Wang W, Liu A, Liu X, You N, Wang Z (2024). The American journal of tropical medicine and hygiene
     PMID: 38653232 | URL: https://pubmed.ncbi.nlm.nih.gov/38653232/
  6. Economic Evaluation of Screening Strategy for Latent Tuberculosis Infection (LTBI) in Contacts of Tuberculosis Patients: Systematic Review and Quality Assessment.
     Yoopetch P, Chitpim N, Jittikoon J, Udomsinprasert W, Thavorncharoensap M (2022). International journal of environmental research and public health
     PMID: 36294107 | URL: https://pubmed.ncbi.nlm.nih.gov/36294107/
  7. Absolute risk of tuberculosis among untreated populations with a positive tuberculin skin test or interferon-gamma release assay result: systematic review and meta-analysis.
     Campbell JR, Winters N, Menzies D (2020). BMJ (Clinical research ed.)
     PMID: 32156698 | URL: https://pubmed.ncbi.nlm.nih.gov/32156698/
  8. Cost Effectiveness of Preventive Treatment for Tuberculosis in Special High-Risk Populations.
     Diel R, Lampenius N, Nienhaus A (2015). PharmacoEconomics
     PMID: 25774015 | URL: https://pubmed.ncbi.nlm.nih.gov/25774015/
  9. Systematic review of cost and cost-effectiveness of different TB-screening strategies.
     Nienhaus A, Schablon A, Costa JT, Diel R (2011). BMC health services research
     PMID: 21961888 | URL: https://pubmed.ncbi.nlm.nih.gov/21961888/
  10. [Mantoux versus immunoferon-gamma test for diagnosis of latent tuberculosis infection in TB patient contacts].
     Fernández Arias A (2011). Atencion primaria
     PMID: 20381206 | URL: https://pubmed.ncbi.nlm.nih.gov/20381206/


### 3.2 Randomized Controlled Trials — ~8 hit (số hit thật); liệt kê đủ 8 bài đã tải
  1. Risk of Tuberculosis Infection in Young Children Exposed to Multidrug-resistant Tuberculosis in the TB-CHAMP Multi-site Randomized Controlled Trial.
     Purchase SE, Brigden J, Seddon JA, Martinson NA, Fairlie L (2025). Clinical infectious diseases : an official publication of the Infectious Diseases Society of America
     PMID: 40440402 | URL: https://pubmed.ncbi.nlm.nih.gov/40440402/
  2. Tuberculosis infection among close contacts of patients with pulmonary tuberculosis in China: a population-based, multicentered study.
     Zhang C, Liu Y, Yao Y, Gong D, Lei R (2024). Clinical microbiology and infection : the official publication of the European Society of Clinical Microbiology and Infectious Diseases
     PMID: 38851427 | URL: https://pubmed.ncbi.nlm.nih.gov/38851427/
  3. Interpretation of serial interferon-gamma test results to measure new tuberculosis infection among household contacts in Zambia and South Africa.
     Sloot R, Shanaube K, Claassens M, Telisinghe L, Schaap A (2020). BMC infectious diseases
     PMID: 33059620 | URL: https://pubmed.ncbi.nlm.nih.gov/33059620/
  4. C-Tb skin test to diagnose Mycobacterium tuberculosis infection in children and HIV-infected adults: A phase 3 trial.
     Aggerbeck H, Ruhwald M, Hoff ST, Borregaard B, Hellstrom E (2018). PloS one
     PMID: 30248152 | URL: https://pubmed.ncbi.nlm.nih.gov/30248152/
  5. Safety and efficacy of the C-Tb skin test to diagnose Mycobacterium tuberculosis infection, compared with an interferon γ release assay and the tuberculin skin test: a phase 3, double-blind, randomise
     Ruhwald M, Aggerbeck H, Gallardo RV, Hoff ST, Villate JI (2017). The Lancet. Respiratory medicine
     PMID: 28159608 | URL: https://pubmed.ncbi.nlm.nih.gov/28159608/
  6. A prospective cohort study of latent tuberculosis in adult close contacts of active pulmonary tuberculosis patients in Korea.
     Park SH, Lee SJ, Cho YJ, Jeong YY, Kim HC (2016). The Korean journal of internal medicine
     PMID: 27052266 | URL: https://pubmed.ncbi.nlm.nih.gov/27052266/
  7. Effect of isoniazid preventive therapy on immune responses to mycobacterium tuberculosis: an open label randomised, controlled, exploratory study.
     Biraro IA, Egesa M, Kimuda S, Smith SG, Toulza F (2015). BMC infectious diseases
     PMID: 26493989 | URL: https://pubmed.ncbi.nlm.nih.gov/26493989/
  8. QuantiFERON-TB Gold In-Tube as a Confirmatory Test for Tuberculin Skin Test in Tuberculosis Contact Tracing: A Noninferiority Clinical Trial.
     Muñoz L, Santin M, Alcaide F, Ruíz-Serrano MJ, Gijón P (2018). Clinical infectious diseases : an official publication of the Infectious Diseases Society of America
     PMID: 29020191 | URL: https://pubmed.ncbi.nlm.nih.gov/29020191/


### 3.3 Guideline / Khuyến cáo — ~2 hit (số hit thật); liệt kê đủ 2 bài đã tải
  1. [Practice recommendations for the use and interpretation of interferon gamma release assays in the diagnosis of latent and active tuberculosis].
     Bergot E, Abiteboul D, Andréjak C, Antoun F, Barras E (2018). Revue des maladies respiratoires
     PMID: 30224215 | URL: https://pubmed.ncbi.nlm.nih.gov/30224215/
  2. Executive Summary of the Guidelines for the Use of interferon-gamma Release Assays in the Diagnosis of Tuberculosis Infection.
     Santin M, García-García JM, Rigau D, Altet N, Anibarro L (2016). Archivos de bronconeumologia
     PMID: 27424071 | URL: https://pubmed.ncbi.nlm.nih.gov/27424071/

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~173 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Association between immune-response magnitude to tuberculosis infection tests and short-term disease risk: a prospective cohort study.
     Ratovoson R, Donkeng V, Ranaivomanana P, Tagnouokam-Ngoupo PA, Tchatchueng J (2026). Clinical microbiology and infection : the official publication of the European Society of Clinical Microbiology and Infectious Diseases
     PMID: 42320712 | URL: https://pubmed.ncbi.nlm.nih.gov/42320712/
  2. Risk of tuberculosis infection according to exposure time and other factors of contacts and their index cases.
     Godoy S, Alsedà M, Parrón I, Millet JP, Caylà JA (2026). Enfermedades infecciosas y microbiologia clinica (English ed.)
     PMID: 42264594 | URL: https://pubmed.ncbi.nlm.nih.gov/42264594/
  3. Mycobacterium tuberculosis transmission from tuberculosis patients with and without recognized symptoms: a case-contact study in eastern China.
     Chen C, Hu X, Horsburgh CR, Wu W, Chen C (2026). Nature communications
     PMID: 42248852 | URL: https://pubmed.ncbi.nlm.nih.gov/42248852/
  4. A Novel Therapy With a One-Month Ultrashort Regimen to Halt Progression From Latent Infection to Active Tuberculosis Among Close Contacts (The TB‑YOUTH Study): Protocol for a Cluster Randomized Contro
     Yang Y, Zhou F, Ren Y, Li F, Yang Q (2026). JMIR research protocols
     PMID: 42247627 | URL: https://pubmed.ncbi.nlm.nih.gov/42247627/
  5. Comparative agreement between tuberculin skin test and QuantiFERON-TB Gold In-Tube across different levels of exposure in a college-based tuberculosis outbreak.
     Sun Z, Wu Y, Ding X, Liu Q, Shao Y (2026). Frontiers in public health
     PMID: 42205449 | URL: https://pubmed.ncbi.nlm.nih.gov/42205449/
  6. Diagnostic accuracy and safety of Cy-Tb for detection of tuberculosis infection: A multicentric study from India.
     Singh M, Hussain T, Modi B, Nair S, Kumar S (2026). The Indian journal of medical research
     PMID: 42024911 | URL: https://pubmed.ncbi.nlm.nih.gov/42024911/
  7. Incidence of latent TB infection among hospital contacts in an intermediate-burden country.
     Ryu SH, Lee JJ, Lim YJ, Kim J, Jung J (2026). American journal of infection control
     PMID: 41999988 | URL: https://pubmed.ncbi.nlm.nih.gov/41999988/
  8. Characterising progression and regression patterns across the spectrum of tuberculosis: a multistate modelling approach.
     Larsson L, Calderwood CJ, Marambire ET, Gupta RK, Banze D (2026). The Lancet. Global health
     PMID: 41713438 | URL: https://pubmed.ncbi.nlm.nih.gov/41713438/
  9. Performance evaluation of the AFIAS IGRA-TB (IFN-gamma) test versus QuantiFERON®-TB gold plus (QFT®-Plus) ELISA in the Barrio Obrero hospital network, Asunción-Paraguay, 2025.
     Céspedes C, Riveros J, Villalba A, Gutierrez S, Ocampo R (2025). Frontiers in public health
     PMID: 41607885 | URL: https://pubmed.ncbi.nlm.nih.gov/41607885/
  10. Screening of close contacts of pulmonary tuberculosis in an urban area in Shanghai, China: a cross-sectional study.
     Zhang S, Li F, Chen J, Wu Z, Ning C (2025). BMC infectious diseases
     PMID: 41444872 | URL: https://pubmed.ncbi.nlm.nih.gov/41444872/
  11. Mycobacterium tuberculosis transmission among child and adolescent contacts of people with pulmonary tuberculosis in Brazil: a multi-center prospective cohort study.
     Sobral L, Arriaga MB, Souza AB, Barreto-Duarte B, Garcia-Rosa BS (2025). BMC infectious diseases
     PMID: 41430120 | URL: https://pubmed.ncbi.nlm.nih.gov/41430120/
  12. Prevalent and incident latent tuberculosis infection among healthcare workers in Taiwan: A multi-center observational study.
     Wu CJ, Lee SS, Shu CC, Lin SM, Lee CC (2026). Journal of microbiology, immunology, and infection = Wei mian yu gan ran za zhi
     PMID: 41309403 | URL: https://pubmed.ncbi.nlm.nih.gov/41309403/
  13. Diagnostic Accuracy of the STANDARD F TB-Feron FIA Assay for Tuberculosis Infection in Vietnam: A Cross-Sectional Study.
     Nguyen HT, Vo LNQ, Codlin AJ, Forse R, Wingfield T (2026). Clinical infectious diseases : an official publication of the Infectious Diseases Society of America
     PMID: 41294359 | URL: https://pubmed.ncbi.nlm.nih.gov/41294359/
  14. Current tuberculosis status and challenges among dialysis patients in Japan: A nationwide cross-sectional survey.
     Yoshifuji A, Kikuchi K, Ando R, Uehara Y, Kanno Y (2025). Medicine
     PMID: 41261656 | URL: https://pubmed.ncbi.nlm.nih.gov/41261656/
  15. Detect early TB infection, evaluate contacts for TB (DETEC-TB) - a protocol for a prospective cohort study on active case finding for tuberculosis disease and tuberculosis infection source tracing.
     Amour M, Joseph P, Ngowi J, Issa A, Moshiro C (2025). BMC infectious diseases
     PMID: 41239243 | URL: https://pubmed.ncbi.nlm.nih.gov/41239243/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 444 hit; trong 30 bản ghi lấy về có 15 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~173 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~8 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Recommendations on the Diagnosis and Treatment of Tuberculosis Infection: SEPAR/SEIMC/Spanish Ministry of Health Consensus Statement.
     Caminero JA, Anibarro L, Tabernero E, Alcaide F, Pérez-Mendoza G (2026). Archivos de bronconeumologia
     PMID: 41545280 | URL: https://pubmed.ncbi.nlm.nih.gov/41545280/
  2. Recommendations on the Diagnosis and Treatment of Tuberculosis Infection: SEPAR/SEIMC/Spanish Ministry of Health Consensus Statement.
     Caminero JA, Anibarro L, Tabernero E, Alcaide F, Pérez-Mendoza G (2026). Enfermedades infecciosas y microbiologia clinica (English ed.)
     PMID: 42264591 | URL: https://pubmed.ncbi.nlm.nih.gov/42264591/
  3. Prevalence of latent tuberculosis infection in Malaysia: the first systematic review and meta-analysis.
     Wada Y, Afolabi HA, Irekeola AA, Bello KE, Yean CY (2026). BMC infectious diseases
     PMID: 42021170 | URL: https://pubmed.ncbi.nlm.nih.gov/42021170/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [UNKNOWN] The Role of a Mycobacterium Growth Inhibition Assay to Quantify Host Immune Control of M. Tuberculosis
     NCT06580639 | Pha: — | Cỡ mẫu dự kiến: 280 | Bắt đầu: 2020-08-01
     URL: https://clinicaltrials.gov/study/NCT06580639
  2. [UNKNOWN] Toward a Safe and Reachable Preventive Therapy for LTBI: a Multicenter Randomized Controlled Study in Taiwan
     NCT02208427 | Pha: PHASE3 | Cỡ mẫu dự kiến: 283 | Bắt đầu: 2014-08
     URL: https://clinicaltrials.gov/study/NCT02208427
  3. [COMPLETED] QuantiFERON®-TB Gold In-Tube for the Diagnosis of Tuberculosis Infection in Contact Tracing Study.
     NCT01223534 | Pha: PHASE4 | Cỡ mẫu dự kiến: 871 | Bắt đầu: 2010-07
     URL: https://clinicaltrials.gov/study/NCT01223534
  4. [UNKNOWN] Comparing Two Preventive Regimens for Latent Tuberculosis Infection (LTBI)
     NCT01398618 | Pha: PHASE3 | Cỡ mẫu dự kiến: 300 | Bắt đầu: 2011-05
     URL: https://clinicaltrials.gov/study/NCT01398618
  5. [UNKNOWN] IGRA and Mantoux Response in Children With Suspected Latent or Active TB Infection
     NCT02653404 | Pha: — | Cỡ mẫu dự kiến: 50 | Bắt đầu: 2015-04
     URL: https://clinicaltrials.gov/study/NCT02653404

> **Đã tra ngày 2026-11-23: ~21 hồ sơ khớp, 5 đang/sắp tuyển.**
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
• KHÔNG phát hiện khoảng trống nào từ dữ liệu PubMed đã tra (đã có SR/MA, RCT, guideline và nghiên cứu mới) — [CẦN — bác sĩ tự xác định khoảng trống, ví dụ quần thể/bối cảnh chưa được phủ; hệ KHÔNG suy ra được]
• Có 5 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 5 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 21 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-DOI-CHUNG-QFT.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 10 SR/MA · 8 RCT · 173 quan sát (số hit, chưa sàng lọc)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-DOI-CHUNG-QFT --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-DOI-CHUNG-QFT` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-DOI-CHUNG-QFT --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
