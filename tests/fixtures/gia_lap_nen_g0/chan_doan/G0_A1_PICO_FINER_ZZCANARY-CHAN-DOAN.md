# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-CHAN-DOAN
> Tạo tự động: 2026-11-15 19:59 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-CHAN-DOAN`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Giá trị chẩn đoán của chỉ số FIB-4 trong phát hiện xơ hoá gan tiến triển ở người bệnh gan nhiễm mỡ liên quan chuyển hoá điều trị ngoại trú
**Truy vấn PubMed:** `("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR NAFLD[tiab] OR MASLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR elastography[tiab]) AND ("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])`

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
│   → ⚠ Chủ đề đã có nhiều SR/MA → cần biện minh tính mới rõ ràng | ⚠ ClinicalTrials.gov: 6 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 18 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.
│   Sau sàng lọc (G0-T3): [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]
├─────────────────────────────────────────────────────────────┤
│ N — NOVEL (Tính mới) — DỰA TRÊN PUBMED THẬT              │
│   SR/MA: 10 | RCT: 1 | Guideline: 0 | Quan sát: 100
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR NAFLD[tiab] OR MASLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR elastography[tiab]) AND ("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-CHAN-DOAN.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR NAFLD[tiab] OR MASLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR elastography[tiab]) AND ("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-CHAN-DOAN.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~10 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Non-Invasive Fibrosis Testing in Adults With Obesity and MASLD: A Systematic Review and Meta-Analysis.
     Ortega PM, Sabatella L, Manousou P, Arregui A, Ahmed AR (2026). Diabetes, obesity & metabolism
     PMID: 42755179 | URL: https://pubmed.ncbi.nlm.nih.gov/42755179/
  2. Imaging-Based Modalities for Identifying At Risk MASH. A Diagnostic Test Meta-Analysis.
     Gunalan SZ, Law MSN, Kua YX, Yu Z, Lim RYZ (2026). The American journal of gastroenterology
     PMID: 41533456 | URL: https://pubmed.ncbi.nlm.nih.gov/41533456/
  3. Diagnostic accuracy of Agile-4 score for liver cirrhosis in patients with metabolic dysfunction-associated steatotic liver disease. A systematic review and meta-analysis of diagnostic test accuracy st
     Malandris K, Katsoula A, Liakos A, Karagiannis T, Sinakos E (2025). Diabetes, obesity & metabolism
     PMID: 39703127 | URL: https://pubmed.ncbi.nlm.nih.gov/39703127/
  4. Diagnostic accuracy of non-invasive tests to screen for at-risk MASH-An individual participant data meta-analysis.
     Mózes FE, Lee JA, Vali Y, Selvaraj EA, Jayaswal ANA (2024). Liver international : official journal of the International Association for the Study of the Liver
     PMID: 38573034 | URL: https://pubmed.ncbi.nlm.nih.gov/38573034/
  5. Diagnostic role of transient elastography in patients with autoimmune liver diseases: A systematic review and meta-analysis.
     Chen H, Shen Y, Wu SD, Zhu Q, Weng CZ (2023). World journal of gastroenterology
     PMID: 37900994 | URL: https://pubmed.ncbi.nlm.nih.gov/37900994/
  6. Performance of non-invasive tests and histology for the prediction of clinical outcomes in patients with non-alcoholic fatty liver disease: an individual participant data meta-analysis.
     Mózes FE, Lee JA, Vali Y, Alzoubi O, Staufer K (2023). The lancet. Gastroenterology & hepatology
     PMID: 37290471 | URL: https://pubmed.ncbi.nlm.nih.gov/37290471/
  7. Noninvasive assessment of liver disease severity in patients with nonalcoholic fatty liver disease (NAFLD) and type 2 diabetes.
     Pennisi G, Enea M, Falco V, Aithal GP, Palaniyappan N (2023). Hepatology (Baltimore, Md.)
     PMID: 36924031 | URL: https://pubmed.ncbi.nlm.nih.gov/36924031/
  8. Diagnostic accuracy of non-invasive tests for advanced fibrosis in patients with NAFLD: an individual patient data meta-analysis.
     Mózes FE, Lee JA, Selvaraj EA, Jayaswal ANA, Trauner M (2022). Gut
     PMID: 34001645 | URL: https://pubmed.ncbi.nlm.nih.gov/34001645/
  9. Identifying Advanced Fibrosis in NAFLD Using Noninvasive Tests: A Systematic Review of Sequential Algorithms.
     Noorian S, Patel A, Ashkar C, Saab S (2022). Journal of clinical gastroenterology
     PMID: 33780219 | URL: https://pubmed.ncbi.nlm.nih.gov/33780219/
  10. Comparison of laboratory tests, ultrasound, or magnetic resonance elastography to detect fibrosis in patients with nonalcoholic fatty liver disease: A meta-analysis.
     Xiao G, Zhu S, Xiao X, Yan L, Yang J (2017). Hepatology (Baltimore, Md.)
     PMID: 28586172 | URL: https://pubmed.ncbi.nlm.nih.gov/28586172/


### 3.2 Randomized Controlled Trials — ~1 hit (số hit thật); liệt kê đủ 1 bài đã tải
  1. Magnetic resonance elastography-based prediction model for hepatic decompensation in NAFLD: A multicenter cohort study.
     Kim BK, Bergstrom J, Loomba R, Tamaki N, Izumi N (2023). Hepatology (Baltimore, Md.)
     PMID: 37203233 | URL: https://pubmed.ncbi.nlm.nih.gov/37203233/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~100 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Comprehensive Approach to Detect Liver Fibrosis by Indirect Serum Biomarkers.
     Garg H, Sharma D, Tiwari H, Bishnoi D (2026). The Journal of the Association of Physicians of India
     PMID: 42902667 | URL: https://pubmed.ncbi.nlm.nih.gov/42902667/
  2. Diagnostic Performance of Non-Invasive Tests in Assessing Liver Fibrosis Among Type 2 Diabetes Mellitus.
     Mufida AZ, Hidayat AA, Alfaray RI, Kholili U, Wibisono S (2026). Acta medica Indonesiana
     PMID: 42845069 | URL: https://pubmed.ncbi.nlm.nih.gov/42845069/
  3. Diagnostic performance of FIB-6 for identifying FibroScan-defined advanced fibrosis in Metabolic Dysfunction-Associated Steatotic Liver Disease (MASLD): a cross-sectional diagnostic accuracy study.
     Bagheri H, Seighali N, Gholami-Chahkand MS, Bakhtiyari M, Seighali F (2026). BMC gastroenterology
     PMID: 42827235 | URL: https://pubmed.ncbi.nlm.nih.gov/42827235/
  4. [Noninvasive scores for predicting liver-related events in patients with metabolic dysfunction-associated fatty liver disease].
     Gao YK, Chen SY, Han X, Sun CL, Wu XN (2026). Zhonghua gan zang bing za zhi = Zhonghua ganzangbing zazhi = Chinese journal of hepatology
     PMID: 42802126 | URL: https://pubmed.ncbi.nlm.nih.gov/42802126/
  5. Noninvasive Detection of Clinically Significant Fibrosis in Biopsy-Proven MASLD: A Retrospective Cross-Sectional Diagnostic Accuracy Study.
     Eksi O, Atay K, Eskazan T, Abishov E, Canbakan M (2026). Medicina (Kaunas, Lithuania)
     PMID: 42654424 | URL: https://pubmed.ncbi.nlm.nih.gov/42654424/
  6. Emerging Indices Outperform Traditional Fibrosis Scores in Young Metabolic Dysfunction-Associated Steatotic Liver Disease Across Divergent Screening Goals.
     Lee A, Han CI, Yang K, Yang H, Sung PS (2026). Journal of gastroenterology and hepatology
     PMID: 42581304 | URL: https://pubmed.ncbi.nlm.nih.gov/42581304/
  7. Simplified definition and imaging-based stratification of at-risk MASH using magnetic resonance elastography.
     Li J, Wu H, Glaser KJ, Ou FS, Manduca A (2026). Hepatology communications
     PMID: 42579768 | URL: https://pubmed.ncbi.nlm.nih.gov/42579768/
  8. Sequential FIB-4-based testing limits detection of fibrotic MASLD despite optimized ELF thresholds.
     Allen AM, Bobek OJ, Canning RE, Eslami M, Benson J (2026). Hepatology communications
     PMID: 42566274 | URL: https://pubmed.ncbi.nlm.nih.gov/42566274/
  9. Metabolic-dysfunction associated steatotic liver disease: clinical features and noninvasive methods of detection in young adults with obesity.
     Sommese P, Boccia F, Mugione P, De Rosa I, Guerriero L (2026). European journal of gastroenterology & hepatology
     PMID: 42467953 | URL: https://pubmed.ncbi.nlm.nih.gov/42467953/
  10. Enhanced Liver Fibrosis Test, FIB-4 and FibroScan: Real-World Prognostic Accuracy for MASLD in a Biopsy-Controlled Cohort.
     Liguori A, D'Ambrosio F, Angelini G, Cefalo C, Galletti S (2026). Liver international : official journal of the International Association for the Study of the Liver
     PMID: 42394207 | URL: https://pubmed.ncbi.nlm.nih.gov/42394207/
  11. Evaluating performance of non-invasive tests for fibrosis detection in MASLD with Type 2 Diabetes Mellitus: Insights from VCTE-Based assessment.
     Kagzi Y, Asif A, Wang Y, Fischer J, Dhillon S (2026). Clinics and research in hepatology and gastroenterology
     PMID: 42392311 | URL: https://pubmed.ncbi.nlm.nih.gov/42392311/
  12. Two-step clinical care pathway to predict MASLD-related advanced fibrosis and long-term outcomes in type 2 diabetes.
     Chen Y, Dong B, Jin X, Liu C, Zheng MH (2026). Gut
     PMID: 41911049 | URL: https://pubmed.ncbi.nlm.nih.gov/41911049/
  13. Diagnostic and prognostic performance of the fibrotic nonalcoholic steatohepatitis index in patients with metabolic dysfunction-associated steatotic liver disease.
     Zhang W, Li M, Luo Y, Wen Z, Huang J (2026). European journal of gastroenterology & hepatology
     PMID: 41870956 | URL: https://pubmed.ncbi.nlm.nih.gov/41870956/
  14. SAFE vs. FIB-4: diagnostic accuracy for clinically significant fibrosis in U.S. adults with cardiometabolic risk factors - a NHANES 2017-2020 analysis.
     Aydin A, Aydin Y, Borz-Baba CI (2026). European journal of gastroenterology & hepatology
     PMID: 41784418 | URL: https://pubmed.ncbi.nlm.nih.gov/41784418/
  15. Metabolic dysfunction-associated steatotic liver disease is associated with vascular dysfunction in type 1 diabetes.
     Mertens J, Stoop T, Dirinck E, Francque S, Heuten H (2026). Cardiovascular diabetology
     PMID: 41742207 | URL: https://pubmed.ncbi.nlm.nih.gov/41742207/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 213 hit; trong 30 bản ghi lấy về có 14 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~100 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~10 hit (số hit thật); liệt kê đủ 10 bài đã tải
  1. Non-Invasive Fibrosis Testing in Adults With Obesity and MASLD: A Systematic Review and Meta-Analysis.
     Ortega PM, Sabatella L, Manousou P, Arregui A, Ahmed AR (2026). Diabetes, obesity & metabolism
     PMID: 42755179 | URL: https://pubmed.ncbi.nlm.nih.gov/42755179/
  2. Imaging-Based Modalities for Identifying At Risk MASH. A Diagnostic Test Meta-Analysis.
     Gunalan SZ, Law MSN, Kua YX, Yu Z, Lim RYZ (2026). The American journal of gastroenterology
     PMID: 41533456 | URL: https://pubmed.ncbi.nlm.nih.gov/41533456/
  3. Diagnostic accuracy of Agile-4 score for liver cirrhosis in patients with metabolic dysfunction-associated steatotic liver disease. A systematic review and meta-analysis of diagnostic test accuracy st
     Malandris K, Katsoula A, Liakos A, Karagiannis T, Sinakos E (2025). Diabetes, obesity & metabolism
     PMID: 39703127 | URL: https://pubmed.ncbi.nlm.nih.gov/39703127/
  ... và 7 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  1. [COMPLETED] Digital Pathology and AI for Liver Outcomes in MASLD
     NCT06344364 | Pha: — | Cỡ mẫu dự kiến: 1241 | Bắt đầu: 2025-09-01
     URL: https://clinicaltrials.gov/study/NCT06344364
  2. [UNKNOWN] Liver Steatosis and Stiffness in HIV
     NCT03599882 | Pha: — | Cỡ mẫu dự kiến: 200 | Bắt đầu: 2018-08-01
     URL: https://clinicaltrials.gov/study/NCT03599882
  3. [COMPLETED] Accuracy of Imaging Techniques in Diagnosing Steatohepatitis and Fibrosis in NAFLD Patients
     NCT04785937 | Pha: NA | Cỡ mẫu dự kiến: 28 | Bắt đầu: 2019-01-01
     URL: https://clinicaltrials.gov/study/NCT04785937
  4. [COMPLETED] NASH Patient's Itinerary: Comparison of Strategies for Screening, Referring and Management of Diabetic Patients
     NCT06688149 | Pha: NA | Cỡ mẫu dự kiến: 536 | Bắt đầu: 2021-01-31
     URL: https://clinicaltrials.gov/study/NCT06688149
  5. [UNKNOWN] Prevalence, Incidence and Characteristics of NAFLD/NASH in Type 1 Diabetes Mellitus
     NCT04664036 | Pha: — | Cỡ mẫu dự kiến: 700 | Bắt đầu: 2018-09-17
     URL: https://clinicaltrials.gov/study/NCT04664036

> **Đã tra ngày 2026-11-15: ~18 hồ sơ khớp, 6 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 26 bài từ 26 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("FIB-4"[tiab] OR "fibrosis-4"[tiab]) AND ("Non-alcoholic Fatty Liver Disease"[MeSH] OR NAFLD[tiab] OR MASLD[tiab]) AND ("Elasticity Imaging Techniques"[MeSH] OR elastography[tiab]) AND ("Sensitivity and Specificity"[MeSH] OR "diagnostic accuracy"[tiab] OR AUROC[tiab])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
• Có 6 nghiên cứu đang/sắp tuyển trên ClinicalTrials.gov — cần đối chiếu để tránh trùng lặp (xem §3.6 của G0_A1)

**Đối chiếu đăng ký:** ⚠ ClinicalTrials.gov: 6 nghiên cứu ĐANG/SẮP TUYỂN cho truy vấn này (tổng 18 hồ sơ đăng ký). 'Chưa công bố' KHÔNG có nghĩa 'chưa ai làm' — đọc các hồ sơ ở §3.6 trước khi biện minh tính mới; nguy cơ trùng đề tài thật.

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-CHAN-DOAN.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 10 SR/MA · 1 RCT · 100 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (26 bài tải về / 26 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-CHAN-DOAN --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-CHAN-DOAN` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-CHAN-DOAN --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
