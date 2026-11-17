# A1 — CÂU HỎI NGHIÊN CỨU & PICO | ZZCANARY-BENH-CHUNG
> Tạo tự động: 2026-11-15 19:57 | Truy vấn PubMed thật
> **Hệ KHÔNG suy ra PICO.** Mọi ô P/I/C/O bên dưới là chỗ TRỐNG — bác sĩ phải tự viết.
> Thứ G0 làm được là dựng NỀN BẰNG CHỨNG (PHẦN 3) và chỉ ra khoảng trống (PHẦN 4) để bác sĩ
> viết PICO có căn cứ. (Câu cũ ở dòng này ghi "xác nhận hoặc chỉnh PICO, không điền
> lại từ đầu" — đã bỏ 2026-07-28 vì mô tả sai việc hệ thật sự làm.)
>
> ⚠️ **NƠI CHỐT chính thức KHÔNG phải file này** mà là `study_meta.json →
> gate_params.G0` (file .md này bị GHI ĐÈ mỗi lần chạy lại G0). Sau khi điền, chạy:
> `python tools/g0_quality_gate.py --study ZZCANARY-BENH-CHUNG`
> Cần bác sĩ kiểm chứng.

---

## PHẦN 1 — PICO / PECO (khung trống — bác sĩ tự viết)


**Topic đề tài:** Sử dụng thuốc chống viêm không steroid và xuất huyết tiêu hoá trên ở người từ 60 tuổi: nghiên cứu bệnh–chứng
**Truy vấn PubMed:** `("Anti-Inflammatory Agents, Non-Steroidal"[MeSH] OR NSAID*[tiab] OR "non-steroidal anti-inflammatory"[tiab]) AND ("Gastrointestinal Hemorrhage"[MeSH] OR "upper gastrointestinal bleeding"[tiab] OR "peptic ulcer bleeding"[tiab]) AND ("case-control"[tiab] OR "Case-Control Studies"[MeSH])`

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
│   SR/MA: 17 | RCT: 4 | Guideline: 0 | Quan sát: 425
│   (số hit THẬT từ PubMed)
│   Năm công bố mới nhất trong các bài đã tải (mọi nhánh): 2026
│   Khoảng trống:
│     • Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Anti-Inflammatory Agents, Non-Steroidal"[MeSH] OR NSAID*[tiab] OR "non-steroidal anti-inflammatory"[tiab]) AND ("Gastrointestinal Hemorrhage"[MeSH] OR "upper gastrointestinal bleeding"[tiab] OR "peptic ulcer bleeding"[tiab]) AND ("case-control"[tiab] OR "Case-Control Studies"[MeSH])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»
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

> Nháp lý do FINER: [CẦN `khoang-trong-nghien-cuu` soạn trong `G0_KHOANG_TRONG_ZZCANARY-BENH-CHUNG.json` → nhap_finer] — I/N/R rút từ bằng chứng; F/E chỉ nêu rủi ro để PI quyết.

---

## PHẦN 3 — BẰNG CHỨNG HIỆN CÓ (THẬT — từ PubMed — 2026-11-15)

> **Lưu ý:** Danh sách dưới đây là kết quả THẬT từ PubMed E-utilities — PMID được xác minh TỒN TẠI trên PubMed. Trạng thái rút bài KHÔNG được khẳng định ở đây: xem §3.0 (nếu agent đã kiểm) và guardrail R1C trong G0_checkpoint.json; không kiểm được là «chưa kiểm», không phải «chưa bị rút».
> Bác sĩ cần đọc toàn văn để kiểm chứng nội dung.
> Mỗi tiêu đề mục ghi RỜI hai con số: ~số hit (toàn kho PubMed) và số bài hệ đã tải
> về (bị chặn bởi `--max-results`) — trước 2026-07-28 hai số này bị trộn làm một.
> Phạm vi: MỘT truy vấn PubMed `("Anti-Inflammatory Agents, Non-Steroidal"[MeSH] OR NSAID*[tiab] OR "non-steroidal anti-inflammatory"[tiab]) AND ("Gastrointestinal Hemorrhage"[MeSH] OR "upper gastrointestinal bleeding"[tiab] OR "peptic ulcer bleeding"[tiab]) AND ("case-control"[tiab] OR "Case-Control Studies"[MeSH])`; xếp nhánh theo BỘ LỌC PubMed, không phải đọc bài —
> mức liên quan và thiết kế thật ở §3.0.

### 3.0 Sàng lọc mức liên quan và tóm lược (agent `tong-quan-y-van` đọc bài)
> [CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_ZZCANARY-BENH-CHUNG.json`] — sàng lọc mức liên quan ĐỦ mọi PMID dưới đây (thiết kế thật · trực tiếp/gián tiếp/không · tóm tắt), nguồn bổ sung kèm cách tìm, tóm lược có PMID, kiểm rút bài. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

### 3.1 Systematic Review / Meta-analysis — ~17 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Risk factors for rebleeding in acute lower gastrointestinal bleeding: a systematic review and meta-analysis.
     Lu Z, Zong D, Yang Z, Yue B (2026). International journal of colorectal disease
     PMID: 42287444 | URL: https://pubmed.ncbi.nlm.nih.gov/42287444/
  2. Risk of Gastrointestinal Bleeding with Concurrent Use of NSAID and SSRI: A Systematic Review and Network Meta-Analysis.
     Haghbin H, Zakirkhodjaev N, Husain FF, Lee-Smith W, Aziz M (2023). Digestive diseases and sciences
     PMID: 36526813 | URL: https://pubmed.ncbi.nlm.nih.gov/36526813/
  3. Selective serotonin reuptake inhibitors increase risk of upper gastrointestinal bleeding when used with NSAIDs: a systemic review and meta-analysis.
     Alam SM, Qasswal M, Ahsan MJ, Walters RW, Chandra S (2022). Scientific reports
     PMID: 36002638 | URL: https://pubmed.ncbi.nlm.nih.gov/36002638/
  4. Gastrointestinal safety of coxibs: systematic review and meta-analysis of observational studies on selective inhibitors of cyclo-oxygenase 2.
     Martín Arias LH, Martín González A, Sanz Fadrique R, Salgueiro Vázquez E (2019). Fundamental & clinical pharmacology
     PMID: 30383903 | URL: https://pubmed.ncbi.nlm.nih.gov/30383903/
  5. Safety of metamizole: a systematic review of the literature.
     Andrade S, Bartels DB, Lange R, Sandford L, Gurwitz J (2016). Journal of clinical pharmacy and therapeutics
     PMID: 27422768 | URL: https://pubmed.ncbi.nlm.nih.gov/27422768/
  6. Systematic review with meta-analysis: the association between the use of calcium channel blockers and gastrointestinal bleeding.
     He Y, Chan EW, Leung WK, Anand S, Wong IC (2015). Alimentary pharmacology & therapeutics
     PMID: 25898902 | URL: https://pubmed.ncbi.nlm.nih.gov/25898902/
  7. Risk of upper gastrointestinal bleeding with selective serotonin reuptake inhibitors with or without concurrent nonsteroidal anti-inflammatory use: a systematic review and meta-analysis.
     Anglin R, Yuan Y, Moayyedi P, Tse F, Armstrong D (2014). The American journal of gastroenterology
     PMID: 24777151 | URL: https://pubmed.ncbi.nlm.nih.gov/24777151/
  8. Aspirin and non-aspirin NSAIDs increase risk of colonic diverticular bleeding: a systematic review and meta-analysis.
     Yuhara H, Corley DA, Nakahara F, Nakajima T, Koike J (2014). Journal of gastroenterology
     PMID: 24221694 | URL: https://pubmed.ncbi.nlm.nih.gov/24221694/
  9. Individual NSAIDs and upper gastrointestinal complications: a systematic review and meta-analysis of observational studies (the SOS project).
     Castellsague J, Riera-Guardia N, Calingaert B, Varas-Lorenzo C, Fourrier-Reglat A (2012). Drug safety
     PMID: 23137151 | URL: https://pubmed.ncbi.nlm.nih.gov/23137151/
  10. Systematic review: Helicobacter pylori and the risk of upper gastrointestinal bleeding risk in patients taking aspirin.
     Fletcher EH, Johnston DE, Fisher CR, Koerner RJ, Newton JL (2010). Alimentary pharmacology & therapeutics
     PMID: 20659284 | URL: https://pubmed.ncbi.nlm.nih.gov/20659284/
  11. Systematic review: the lower gastrointestinal adverse effects of non-steroidal anti-inflammatory drugs.
     Laine L, Smith R, Min K, Chen C, Dubois RW (2006). Alimentary pharmacology & therapeutics
     PMID: 16918879 | URL: https://pubmed.ncbi.nlm.nih.gov/16918879/
  12. Upper gastrointestinal complications among users of paracetamol.
     González-Pérez A, Rodríguez LA (2006). Basic & clinical pharmacology & toxicology
     PMID: 16611205 | URL: https://pubmed.ncbi.nlm.nih.gov/16611205/
  13. Dose-response relationships between individual nonaspirin nonsteroidal anti-inflammatory drugs (NANSAIDs) and serious upper gastrointestinal bleeding: a meta-analysis based on individual patient data.
     Lewis SC, Langman MJ, Laporte JR, Matthews JN, Rawlins MD (2002). British journal of clinical pharmacology
     PMID: 12236853 | URL: https://pubmed.ncbi.nlm.nih.gov/12236853/
  14. A metaanalysis of severe upper gastrointestinal complications of nonsteroidal antiinflammatory drugs.
     Ofman JJ, MacLean CH, Straus WL, Morton SC, Berger ML (2002). The Journal of rheumatology
     PMID: 11950025 | URL: https://pubmed.ncbi.nlm.nih.gov/11950025/
  15. Role of Helicobacter pylori infection and non-steroidal anti-inflammatory drugs in peptic-ulcer disease: a meta-analysis.
     Huang JQ, Sridhar S, Hunt RH (2002). Lancet (London, England)
     PMID: 11809181 | URL: https://pubmed.ncbi.nlm.nih.gov/11809181/


### 3.2 Randomized Controlled Trials — ~4 hit (số hit thật); liệt kê đủ 4 bài đã tải
  1. Effect of a proton-pump inhibitor on intestinal microbiota in patients taking low-dose aspirin.
     Tsujimoto H, Hirata Y, Ueda Y, Kinoshita N, Tawa H (2021). European journal of clinical pharmacology
     PMID: 34085115 | URL: https://pubmed.ncbi.nlm.nih.gov/34085115/
  2. Risk of upper gastrointestinal tract bleeding associated with selective serotonin reuptake inhibitors and venlafaxine therapy: interaction with nonsteroidal anti-inflammatory drugs and effect of acid-
     de Abajo FJ, García-Rodríguez LA (2008). Archives of general psychiatry
     PMID: 18606952 | URL: https://pubmed.ncbi.nlm.nih.gov/18606952/
  3. Risk of upper gastrointestinal bleeding and perforation associated with low-dose aspirin as plain and enteric-coated formulations.
     de Abajo FJ, García Rodríguez LA (2001). BMC clinical pharmacology
     PMID: 11228592 | URL: https://pubmed.ncbi.nlm.nih.gov/11228592/
  4. Upper gastrointestinal bleeding in relation to previous use of analgesics and non-steroidal anti-inflammatory drugs. Catalan Countries Study on Upper Gastrointestinal Bleeding.
     Laporte JR, Carné X, Vidal X, Moreno V, Juan J (1991). Lancet (London, England)
     PMID: 1670734 | URL: https://pubmed.ncbi.nlm.nih.gov/1670734/


### 3.3 Guideline / Khuyến cáo — ~0 hit (số hit thật); liệt kê đủ 0 bài đã tải
  → Không tìm thấy bài nào trên PubMed

> ⚠️ Chỉ soi guideline được PubMed đánh chỉ mục. KHÔNG thay việc quét trang chính thống
> (WHO · NICE · USPSTF · hiệp hội chuyên khoa · Bộ Y tế) — nhiều khuyến cáo không nằm
> trên PubMed. Dòng «không thấy guideline» ở PHẦN 4 chỉ đúng trong phạm vi PubMed; văn bản quy phạm
> trong nước nằm ở bảng PHẦN 4b.

### 3.4 Nghiên cứu QUAN SÁT (cohort/bệnh-chứng/cắt ngang — theo bộ lọc PubMed) — ~425 hit (số hit thật); liệt kê đủ 15 bài đã tải
  1. Interpretable LightGBM model for predicting postoperative gastrointestinal hemorrhage in elderly hip fracture patients: leveraging systemic inflammation and medication exposures for personalized risk 
     Sai H, Ren J, Ma X, Yang K, Bai C (2026). BMC geriatrics
     PMID: 42070040 | URL: https://pubmed.ncbi.nlm.nih.gov/42070040/
  2. The use of prophylactic transcatheter arterial embolization in Forrest type II ulcer patients without attempted endoscopic hemostasis.
     Zhang X, Wang D, Zhu Q, Zhang H (2026). Medicine
     PMID: 41790684 | URL: https://pubmed.ncbi.nlm.nih.gov/41790684/
  3. Appropriateness of proton pump inhibitor prescription for prevention of gastrointestinal bleeding in patients receiving warfarin: a real world, database study.
     Manasirisuk P, Sawanyawisuth K, Manasirisuk W (2025). BMC pharmacology & toxicology
     PMID: 41373035 | URL: https://pubmed.ncbi.nlm.nih.gov/41373035/
  4. Esophagogastroduodenoscopy findings in patients with or without recent use of antiplatelets, anticoagulants, or NSAIDs and non-variceal upper gastrointestinal bleeding: A retrospective cohort study.
     Mpakogiannis K, Fousekis FS, Moshou P, Katsanos KH, Christodoulou DK (2025). Acta gastro-enterologica Belgica
     PMID: 41083165 | URL: https://pubmed.ncbi.nlm.nih.gov/41083165/
  5. Clinical and endoscopic analysis of gastrointestinal bleeding during COVID-19 full-blown pandemic: a retrospective cohort study.
     Liu JW, Sui Y, Lu JH, Ren JN, Gong JW (2025). Annals of medicine
     PMID: 40667956 | URL: https://pubmed.ncbi.nlm.nih.gov/40667956/
  6. Effects of antiplatelet, anticoagulant, and nonsteroidal anti-inflammatory drugs on upper gastrointestinal bleeding in geriatric patients.
     Onem S, Güven İE, Dolu S, Onem MGG, Akyol T (2025). Medicine
     PMID: 40441242 | URL: https://pubmed.ncbi.nlm.nih.gov/40441242/
  7. Comparative efficacy of gelatin sponge, microcoils, and nbca in arterial gastrointestinal bleeding: a retrospective study.
     Lai L, Liu X, Su J (2025). BMC gastroenterology
     PMID: 40426059 | URL: https://pubmed.ncbi.nlm.nih.gov/40426059/
  8. Emergent endoscopy is associated with lower mortality in hemodynamically unstable upper GI bleeding: Single-center experience with 24/7 endoscopy services.
     Pham TT, Quach DT, Le LT, Nguyen VN, Chung NM (2025). Clinics and research in hepatology and gastroenterology
     PMID: 40174780 | URL: https://pubmed.ncbi.nlm.nih.gov/40174780/
  9. Risk of cardiovascular diseases and gastrointestinal bleeding is comparable between celecoxib and non-selective non-steroidal anti-inflammatory drugs in patients with ankylosing spondylitis: a nationw
     Kim A, Kim SC, Kim J, So MW, Lee SG (2025). Scandinavian journal of rheumatology
     PMID: 40028763 | URL: https://pubmed.ncbi.nlm.nih.gov/40028763/
  10. Gastrointestinal Bleeds Are a Rare Event After Total Hip and Knee Arthroplasty.
     Ballard ET, Bergeson KS, Wisniewski SJ, Singh S, Ejub S (2025). The Journal of arthroplasty
     PMID: 39892621 | URL: https://pubmed.ncbi.nlm.nih.gov/39892621/
  11. Risk of Lower Gastrointestinal Bleeding in Nonsteroidal Anti-inflammatory Drug (NSAID) and Proton Pump Inhibitor Users Compared with NSAID-Only Users: A Common Data Model Analysis.
     Lee M, Kim M, Cha JM (2025). Gut and liver
     PMID: 39748650 | URL: https://pubmed.ncbi.nlm.nih.gov/39748650/
  12. Nonvitamin K Anticoagulants: Risk of Bleeding When Interacting With Other Medications: A Cohort Study From Medicare.
     Gomez-Lumbreras A, Brendle M, Moorman-Bishir K, Tan M, Malone DC (2024). Clinical cardiology
     PMID: 39360666 | URL: https://pubmed.ncbi.nlm.nih.gov/39360666/
  13. Comparison of gastrointestinal bleeding in patients with and without liver cirrhosis.
     Daðadóttir SM, Ingason AB, Hreinsson JP, Björnsson ES (2024). Scandinavian journal of gastroenterology
     PMID: 39105571 | URL: https://pubmed.ncbi.nlm.nih.gov/39105571/
  14. DA-9601 has protective effects comparable to those of proton pump inhibitor and rebamipide against nonsteroidal anti-inflammatory drugs-induced upper and lower gastrointestinal bleeding in patients wi
     So MW, Kim A, Lee SG (2024). Medicine
     PMID: 38968495 | URL: https://pubmed.ncbi.nlm.nih.gov/38968495/
  15. Continuous co-prescription of rebamipide prevents upper gastrointestinal bleeding in NSAID use for orthopaedic conditions: A nested case-control study using the LIFE Study database.
     Yamate S, Ishiguro C, Fukuda H, Hamai S, Nakashima Y (2024). PloS one
     PMID: 38861561 | URL: https://pubmed.ncbi.nlm.nih.gov/38861561/


> 🔎 Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 459 hit; trong 30 bản ghi lấy về có 12 bản ghi các nhánh có bộ lọc ở trên KHÔNG giữ — danh sách ở `G0_pubmed_raw.json` → `khong_loc`; PI rà xem có bài liên quan bị bộ lọc loại không.
> ⚠️ Con số ~425 là SỐ HIT của bộ lọc quan sát và CÓ CHỒNG LẤN
> với RCT/SR (mức chồng lấn tuỳ chủ đề — chưa đo cho truy vấn này). Dùng để biết "lĩnh vực
> này đã có nền quan sát hay chưa", KHÔNG dùng làm số nghiên cứu quan sát thuần, và CHƯA sàng
> lọc mức liên quan (xem §3.0).

### 3.5 SR/MA · RCT · guideline gần đây 2021-2026 — ~4 hit (số hit thật); liệt kê đủ 4 bài đã tải
  1. Risk factors for rebleeding in acute lower gastrointestinal bleeding: a systematic review and meta-analysis.
     Lu Z, Zong D, Yang Z, Yue B (2026). International journal of colorectal disease
     PMID: 42287444 | URL: https://pubmed.ncbi.nlm.nih.gov/42287444/
  2. Risk of Gastrointestinal Bleeding with Concurrent Use of NSAID and SSRI: A Systematic Review and Network Meta-Analysis.
     Haghbin H, Zakirkhodjaev N, Husain FF, Lee-Smith W, Aziz M (2023). Digestive diseases and sciences
     PMID: 36526813 | URL: https://pubmed.ncbi.nlm.nih.gov/36526813/
  3. Selective serotonin reuptake inhibitors increase risk of upper gastrointestinal bleeding when used with NSAIDs: a systemic review and meta-analysis.
     Alam SM, Qasswal M, Ahsan MJ, Walters RW, Chandra S (2022). Scientific reports
     PMID: 36002638 | URL: https://pubmed.ncbi.nlm.nih.gov/36002638/
  ... và 1 bài khác (đủ danh sách: G0_pubmed_raw.json)

> ⚠️ Nhánh này chạy với bộ lọc SR/MA·RCT·guideline, nên nó KHÔNG trả lời "có nghiên cứu
> nào mới không" nói chung — nghiên cứu quan sát mới không xuất hiện ở đây.

### 3.6 ĐĂNG KÝ NGHIÊN CỨU — đã có ai ĐANG LÀM chưa? (ClinicalTrials.gov)
  → Không có hồ sơ đăng ký nào khớp truy vấn

> **Đã tra ngày 2026-11-15: ~0 hồ sơ khớp, 0 đang/sắp tuyển.**
> PubMed chỉ biết cái ĐÃ CÔNG BỐ; mục này mới trả lời "đang có ai làm".
> ClinicalTrials.gov chủ yếu phủ THỬ NGHIỆM CAN THIỆP. Còn phải tự tra thủ công:
> · Tổng quan hệ thống → PROSPERO: https://www.crd.york.ac.uk/prospero/
> · Đăng ký quốc tế khác → WHO ICTRP: https://trialsearch.who.int/
> (hai nguồn này không có API mở miễn phí — hệ KHÔNG tra, đừng coi là đã tra)
> ☐ Bác sĩ đã tự tra PROSPERO   ☐ Bác sĩ đã tự tra WHO ICTRP
> Nơi hệ ĐỌC: `gate_params.G0.registry_manual_checked = {"ictrp": "YYYY-MM-DD"}`
> (ngày tự tra, không ở tương lai — G0-HUMAN-08); có thử nghiệm đang tuyển khớp ⇒ thêm `registry_overlap_assessment`.

**Tổng PMIDs thật tìm được:** 34 bài từ 34 PMID duy nhất

---

## PHẦN 4 — PHÂN TÍCH KHOẢNG TRỐNG (tự động từ evidence thật)

**Mức độ bằng chứng hiện có:** MẠNH — có SR/MA (theo số hit của bộ lọc, CHƯA sàng lọc mức liên quan)

**Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** [CẦN tong-quan-y-van NÊU trong G0_TONG_HOP]

**Khoảng trống nghiên cứu cụ thể:**
• Không thấy guideline được PubMed đánh chỉ mục (PubMed, truy vấn G0 «("Anti-Inflammatory Agents, Non-Steroidal"[MeSH] OR NSAID*[tiab] OR "non-steroidal anti-inflammatory"[tiab]) AND ("Gastrointestinal Hemorrhage"[MeSH] OR "upper gastrointestinal bleeding"[tiab] OR "peptic ulcer bleeding"[tiab]) AND ("case-control"[tiab] OR "Case-Control Studies"[MeSH])») — văn bản quy phạm trong nước (Bộ Y tế…) và trang hiệp hội KHÔNG nằm trên PubMed: phải rà trước khi kết luận «chưa có»

**Đối chiếu đăng ký:** ClinicalTrials.gov: 0 hồ sơ đăng ký khớp truy vấn (chỉ phủ thử nghiệm; nghiên cứu quan sát thường không đăng ký).

> Các dòng trên do MÁY suy từ số hit của một truy vấn — mỗi dòng phủ định đã ghi phạm vi. Phát biểu khoảng trống
> có đọc bài nằm ở PHẦN 4b; nơi chốt là `gate_params.G0.novelty_justification`.

## PHẦN 4b — ĐỐI CHIẾU GUIDELINE, PHÁT BIỂU KHOẢNG TRỐNG, TÍNH MỚI (agent `khoang-trong-nghien-cuu`)
> [CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_ZZCANARY-BENH-CHUNG.json`] — bảng guideline/văn bản quy phạm (kể cả văn bản trong nước không lập chỉ mục PubMed), phát biểu khoảng trống 1–2 câu + loại, mức tính mới + ý nghĩa, trạng thái từng nguồn tra, nháp lý do FINER. Khuôn và bộ kiểm: `tools/g0_tong_hop.py`.

---

## PHẦN 5 — THIẾT KẾ GỢI Ý SƠ BỘ (G1 quyết định chính thức)

```
┌─────────────────────────────────────────────────────────────┐
│ Ưu tiên 1 (hệ gợi ý từ bằng chứng thật):                   │
│   Nghiên cứu phân tích dưới nhóm / quần thể đặc thù /...
│   Lý do: suy từ 17 SR/MA · 4 RCT · 425 quan sát (số hit, chưa sàng lọc)
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
☑ Truy vấn PubMed đã chạy (34 bài tải về / 34 PMID duy nhất)
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

**Hành động tiếp theo của bác sĩ** (danh sách SỐNG luôn ở `python3 tools/hoi_dong_cong.py cham-song --study ZZCANARY-BENH-CHUNG --gate G0`):
1. Đọc ĐỦ danh sách bài ở PHẦN 3 (bảng sàng lọc §3.0 nếu có) và hồ sơ đăng ký ở §3.6
2. Mở `study_meta.json`, điền khối `gate_params.G0` theo bảng trên
3. Chạy `python tools/g0_quality_gate.py --study ZZCANARY-BENH-CHUNG` — bộ chấm in `dau_van_tay_chot` của nội dung HIỆN TẠI;
   xác nhận SAU CÙNG (sửa quyết định hay dựng lại A1 sau khi xác nhận làm dấu đổi ⇒ phải xác nhận lại)
4. Khi trạng thái đạt `PASS_G0_CONFIRMED` thì mới chạy G1 (`thiet-ke-nghien-cuu`)

Dựng lại A1 sau khi agent cập nhật hai tệp ở §3.0/PHẦN 4b (không tra lại PubMed):
`python3 tools/run_g0_auto.py --study ZZCANARY-BENH-CHUNG --dung-lai-a1`

> G0 KHÔNG tự kích hoạt G1. Bác sĩ tự chạy G1 sau khi chốt câu hỏi.

---

*Cần bác sĩ kiểm chứng. Artifact này [BẢN NHÁP TỰ ĐỘNG] — bác sĩ xác nhận trước khi tiến G1.*
