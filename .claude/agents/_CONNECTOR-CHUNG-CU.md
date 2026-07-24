# REGISTRY CONNECTOR CHỨNG CỨ SỐNG — bản đồ năng lực MCP cho tầng Agent EBM

> Sổ tham chiếu hạ tầng (`_*`) — **KHÔNG phải agent** (không tính vào bộ đếm agent). Tạo 2026-06-15.
> **MỤC ĐÍCH:** một nguồn-sự-thật duy nhất (SSOT) liệt kê các **connector MCP sống** mà tầng Agent
> được phép dùng để lấy **chứng cứ TỐT NHẤT + MỚI NHẤT**. Trước đây chỉ `tra-cuu-chung-cu` nối 1 tool
> PubMed; file này gom mọi connector về một chỗ để mọi agent trỏ tới bằng **1 dòng tham chiếu**.
> Luật nền: `_HIEN-PHAP-LIEM-CHINH.md` + `_NGUYEN-TAC-TRUNG-THUC-BAO-MAT-PHAP-LY-LIEM-CHINH.md`
> (4 trụ cột) + `_QUAN-TRI-DU-LIEU-PII.md` (§3 outbound). **"Cần bác sĩ kiểm chứng."**

---

## 0. NGUYÊN TẮC DÙNG CONNECTOR (không thương lượng)
1. **Connector là CÔNG CỤ, không phải kết luận.** Mọi con số/khẳng định kéo về vẫn phải qua kỷ luật
   self-RAG (đúng PICO? kết cục cứng hay surrogate? thiết kế đọc đúng chưa? bị rút chưa?) trước khi dùng.
2. **PARTIAL khi thiếu connector.** Connector MCP có thể KHÔNG có trong phiên (headless/cron, chưa nối,
   lỗi mạng). Thiếu → gắn cờ **⚠ PARTIAL**, ghi rõ nguồn nào CHƯA tra; **TUYỆT ĐỐI KHÔNG** kết luận
   "không có chứng cứ / không có cập nhật". Lùi về skill REST miễn phí (`paper-lookup`, `research-lookup`,
   `literature-review`, `citation-management`) hoặc kho RAG `medical-ebm-automation/evidence/`.
3. **Mọi định danh phải phân giải được.** Bài chỉ vào bảng nguồn chính sau khi có **PMID và/hoặc DOI thật**,
   metadata khớp, chưa bị rút. Trích từ trí nhớ chưa phân giải → `[CẦN KIỂM CHỨNG]`, KHÔNG đưa vào bảng chính.
4. **KHỬ PII Ở ĐIỂM GỌI (outbound).** Truy vấn gửi RA connector chỉ chứa **PICO/từ khóa y khoa** —
   KHÔNG tên/tuổi/ngày sinh/mã hồ sơ/địa danh hẹp/chi tiết hiếm có thể tái định danh. Đây là lớp phòng
   thủ chiều sâu, BỔ SUNG cho R2 (vốn chỉ chặn PII ở ĐẦU RA, chạy sau khi đã gọi). Xem `_QUAN-TRI-DU-LIEU-PII.md` §3.
5. **Phân tầng thẩm quyền nguồn (xem §2).** Không phải connector nào cũng là nguồn TRÍCH DẪN cấp 1.
6. **Agent chỉ ĐỀ XUẤT.** Chứng cứ kéo về là gợi ý cho bác sĩ duyệt (Cổng A/B/G) — không tự đổi thực hành.
7. **THỨ BẬC NGUỒN — nguồn CHÍNH THỐNG trước, PubMed là lớp ĐỐI CHIẾU.** Lấy chứng cứ TỪ nguồn chính thống cấp cao (§1bis: Cochrane/HTA · hiệp hội chuyên khoa/guideline · tạp chí đỉnh); **PubMed/Europe PMC dùng để LẤY PMID/DOI + ĐỐI CHIẾU/KHỬ TRÙNG** (khi chứng cứ đã có ở nguồn chính thống, tra PubMed để xác nhận trùng + gắn định danh). Chỉ khởi động tìm PubMed **sơ cấp độc lập** khi nguồn chính thống KHÔNG phủ (khoảng trống) → khi đó ghi rõ. Thứ tự chi tiết: **§2bis**. *Bất biến: mọi mục vẫn cần **PMID/DOI** (hoặc URL guideline chính thức + năm) để verify.*

---

## 1. BẢNG CONNECTOR SỐNG (ID chính xác + vai + khi ưu tiên)

| Connector | ID công cụ MCP (tiền tố) | Vai chứng cứ | Khi ưu tiên |
|---|---|---|---|
| **PubMed/MEDLINE** | `mcp__plugin_bio-research_pubmed__` → `search_articles` · `get_article_metadata` · `get_full_text_article` · `find_related_articles` · `convert_article_ids` (PMID↔DOI↔PMCID) · `lookup_article_by_citation` | **NỀN TẢNG** — tìm SR/MA, RCT, cohort; phân giải & kiểm metadata; lấy toàn văn PMC | Mọi câu hỏi điều trị/chẩn đoán/tiên lượng/tác hại; mọi lần xác minh PMID/DOI |
| **Consensus** | `mcp__plugin_bio-research_consensus__search` | **CHỈ KHÁM PHÁ** (discovery) — tổng hợp AI có trích dẫn để định hướng nhanh | Quét sơ bộ "bài nào nói gì"; **KHÔNG** dùng làm nguồn trích dẫn cấp 1 — xem ⚠ §3 |
| **ClinicalTrials.gov** | `mcp__plugin_bio-research_c-trials__` → `search_trials` · `get_trial_details` · `analyze_endpoints` · `search_by_eligibility` | Đăng ký & thiết kế thử nghiệm; endpoint benchmark; thử nghiệm đang chạy/đã có kết quả | Câu hỏi điều trị (xem có RCT đang/đã chạy); thiết kế NC (đối chiếu endpoint/cỡ mẫu/tiêu chí) |
| **bioRxiv/medRxiv** | `mcp__plugin_bio-research_biorxiv__` → `search_preprints` · `get_preprint` · `search_published_preprints` | Tiền ấn phẩm (**CHƯA bình duyệt**); kiểm preprint đã lên tạp chí chưa | Văn liệu xám cho SR; tín hiệu rất mới — **luôn ghi nhãn "CHƯA bình duyệt"** |
| **ChEMBL** | `mcp__plugin_bio-research_chembl__` → `drug_search` · `get_mechanism` · `get_admet` · `get_bioactivity` · `target_search` | Dược lý **TIỀN LÂM SÀNG** (cơ chế, IC50/Ki, ADMET dự đoán) | Bối cảnh cơ chế thuốc cho NGHIÊN CỨU — xem ⚠ §3 (KHÔNG dùng cho cảnh báo kê đơn) |
| **ICD-10-CM/PCS** | `mcp__bb740761-1dc3-44f5-a43c-4e9429d9ddc0__` → `search_codes` · `lookup_code` · `validate_code` · `get_hierarchy` | Mã hóa chẩn đoán/thủ thuật (bộ mã 2026) | Khi cần mã ICD-10 chuẩn cho chẩn đoán/biến số/báo cáo |

> Bộ mã ICD-10-CM là chuẩn Hoa Kỳ — đối chiếu danh mục **ICD-10 của Bộ Y tế VN** khi dùng cho hồ sơ
> trong nước (`[CẦN XÁC NHẬN TẠI ĐƠN VỊ]`).

---

## 1bis. NGUỒN CHÍNH THỐNG — HIỆP HỘI · GUIDELINE · HTA · TẠP CHÍ ĐỈNH (đã kiểm domain 2026-07-04)
> **ĐÂY LÀ NƠI LẤY CHỨNG CỨ TỐT NHẤT (nguồn của record).** Truy cập qua `WebFetch`/`WebSearch` trang chính thức + REST API khi có (Cochrane/Europe PMC/openFDA/DailyMed…). **PubMed/Europe PMC dùng để lấy PMID/DOI + đối chiếu/khử trùng** (§2bis). Toàn văn guideline/tạp chí có **BẢN QUYỀN** → chỉ **TRÍCH DẪN + link + PMID/DOI**, KHÔNG cào/tái bản PDF sau tường phí (luật bản quyền `_NGUON-GUIDELINE-TU-DONG.md` §4). Website tạp chí lớn hay chặn bot (HTTP 403) → lấy metadata/định danh qua **PubMed/Crossref/Europe PMC**, đọc toàn văn khi OA/qua PMC.

### (a) Tổng hợp chứng cứ & HTA — cấp cao nhất (SR/meta + aggregator guideline)
| Nguồn | Domain chính thức | Truy cập | Vai |
|---|---|---|---|
| **Cochrane Library (CDSR)** | cochranelibrary.com | Tóm tắt free mọi nơi; **TOÀN VĂN free tại VN** (one-click LMIC) + green OA sau 12 tháng; CDSR có index trên PubMed | SR/meta **chuẩn vàng** — ưu tiên #1 cho câu hỏi hiệu quả |
| **Epistemonikos** | epistemonikos.org (API: api.epistemonikos.org) | Free, có API | CSDL SR lớn nhất — tìm SR nhanh, bổ trợ Cochrane |
| **Europe PMC** | europepmc.org (Articles REST API) | Free, API phong phú | Khám phá y văn **RỘNG HƠN PubMed** (gồm preprint + guideline); lấy toàn văn OA + định danh |
| **NICE** (+ CKS + BNF) | nice.org.uk | Free đọc; Syndication API (đăng ký free) | Guideline + Clinical Knowledge Summaries + dược (BNF) — bối cảnh Anh, **bối cảnh hóa VN** |
| **USPSTF** | uspreventiveservicestaskforce.org *(taskforce, không gạch nối)* | Free | Khuyến cáo **dự phòng/tầm soát** (A/B/C/D/I) — CHỈ dự phòng, không điều trị |
| **TRIP Database** | tripdatabase.com | Free tier (search) | Cỗ máy trả lời lâm sàng gộp guideline+SR |
| **G-I-N** Int'l Guidelines Library | g-i-n.net (thư viện: guidelines.ebmportal.com) | Một phần free | Thư viện guideline quốc tế đa chuyên khoa |
| ⚠ ECRI Guidelines Trust | guidelines.ecri.org | **TẠM NGƯNG (offline 2026)** — kế thừa NGC (đóng 2018) | KHÔNG dùng làm nguồn sống; thay bằng NICE/G-I-N/hội chuyên khoa |

### (b) Hiệp hội chuyên khoa — GUIDELINE ĐIỀU TRỊ (nguồn của record theo chuyên khoa)
| Chuyên khoa | Hiệp hội (domain · tạp chí đăng toàn văn) | Ghi chú |
|---|---|---|
| **Tim mạch** | ESC (escardio.org/Guidelines · EHJ) · ACC (acc.org/guidelines · JACC) · AHA (professional.heart.org · Circulation) | ACC/AHA thường ra bản **ĐỒNG**; ESC theo năm hội nghị. **VN: Hội Tim mạch học VN (vnha.org.vn)** |
| **ĐTĐ/Nội tiết** | ADA Standards of Care (professional.diabetes.org/standards-of-care · Diabetes Care, **bản 2026**) · EASD (easd.org · Diabetologia) · Endocrine Society (endocrine.org · JCEM) · AACE (pro.aace.com) | ADA cập nhật tháng 1 hằng năm |
| **Thận** | KDIGO (kdigo.org/guidelines · Kidney Int) | PDF free; 2024 CKD · 2022 ĐTĐ-CKD |
| **Hô hấp** | GOLD (goldcopd.org — COPD **2026**) · GINA (ginasthma.org — hen) · ATS (thoracic.org) · ERS (ersnet.org · ERJ) · CHEST (journal.chestnet.org) | GOLD/GINA free PDF thường niên |
| **Nhiễm khuẩn** | IDSA (idsociety.org · CID) · WHO (who.int/publications) · CDC (cdc.gov) | Kháng sinh đối chiếu **WHO AWaRe** (mục d) |
| **Thấp khớp** | EULAR (eular.org · ARD) · ACR (**rheumatology.org** · A&R) | ACR domain = rheumatology.org (KHÔNG phải acr.org) |
| **Tiêu hóa** | ACG (**gi.org** · Am J Gastroenterol) · AGA (gastro.org · Gastroenterology) | ACG ≠ AGA (2 hội khác nhau); ACG = gi.org |
| **Thần kinh** | AAN (aan.com · Neurology) | |
| **Ung thư** | ASCO (asco.org · JCO) · ESMO (esmo.org · Annals of Oncology, OA) · NCCN (nccn.org — **cần đăng ký free**) | NCCN cấm sao chép/tái bản |
| **Tâm thần** | APA — **American PSYCHIATRIC Assoc** (psychiatry.org · psychiatryonline.org) | KHÔNG nhầm apa.org (American Psychological Association) |
| **Sản phụ khoa** | ACOG (acog.org · Obstetrics & Gynecology) | Nhiều bản chỉ hội viên |
| **🇻🇳 Việt Nam** | **Cục KCB — kcb.vn/phac-do** (kho phác đồ **QĐ-BYT CHÍNH THỨC**) · Bộ Y tế moh.gov.vn (văn bản) | **Ưu tiên kcb.vn** cho phác đồ; trích **số QĐ-BYT + ngày** |

### (c) Tạp chí y khoa độ tin cậy cao (toàn văn nghiên cứu gốc/đồng thuận)
NEJM (nejm.org) · The Lancet + specialty (thelancet.com) · JAMA + JAMA Network (jamanetwork.com; **JAMA Network Open OA hoàn toàn**) · The BMJ (bmj.com — **MỌI nghiên cứu gốc open access**) · Annals of Internal Medicine (acpjournals.org) · Nature Medicine (nature.com/nm) · Circulation (ahajournals.org) · JACC (jacc.org) · Diabetes Care (diabetesjournals.org/care) · Kidney International (kidney-international.org) · Blood (ashpublications.org — **free sau 12 tháng**) · Gut (gut.bmj.com) · CHEST (journal.chestnet.org).
> Luôn kèm **PMID/DOI**; đọc toàn văn khi OA hoặc qua PMC/Europe PMC. Bài "săn mồi" → loại (rubric Q7).

### (d) An toàn thuốc / dược lý — nguồn của record cho cảnh báo kê đơn (đồng bộ `ke-don-an-toan`)
| Nguồn | Domain | Truy cập | Vai |
|---|---|---|---|
| **openFDA** | open.fda.gov · api.fda.gov | Free API (key free nâng hạn) | Nhãn thuốc · biến cố bất lợi (FAERS) · thu hồi |
| **DailyMed** | dailymed.nlm.nih.gov | Free API (SPL) | Nhãn thuốc FDA đầy đủ |
| **Drugs@FDA** | accessdata.fda.gov/scripts/cder/daf · api.fda.gov/drug/drugsfda | Free | Thuốc đã phê duyệt (thị trường Mỹ) |
| **EMA** | ema.europa.eu/en/medicines | Free (EPAR) | Thuốc cấp phép EU + báo cáo thẩm định |
| **MHRA** | products.mhra.gov.uk | Free (web) | SmPC/PIL/PAR (Anh) |
| **LactMed** | ncbi.nlm.nih.gov/books/NBK501922 | Free (E-utilities db=books) | Thuốc & cho con bú (đã rời TOXNET 2019) |
| **WHO AWaRe 2023 + EML 23rd (2023)** | who.int/publications | Free (PDF/CSV) | Phân loại kháng sinh Access/Watch/Reserve + thuốc thiết yếu |
| **BNF** | bnf.nice.org.uk | Free (web); đầy đủ qua MedicinesComplete (NHS/HINARI free) | Cẩm nang kê đơn Anh |
> ⚠ Nhắc §3: cảnh báo kê đơn (tương tác/CCĐ/chỉnh liều) dựa **nhãn thuốc/openFDA/DailyMed + guideline + PMID/DOI**, **KHÔNG** dùng ChEMBL.

### (e) Đăng ký thử nghiệm
ClinicalTrials.gov (clinicaltrials.gov · REST API v2 free — cũng là MCP `c-trials`) · WHO ICTRP (trialsearch.who.int — gộp registry toàn cầu, web). Ghi `status`; **registry ≠ kết quả công bố**.

---

## 2. PHÂN TẦNG THẨM QUYỀN NGUỒN (nối vào rubric Q7 `_CHUAN-CHAT-LUONG-MEDPALM.md` + R7)

| Tầng | Connector/Nguồn | Được làm gì |
|---|---|---|
| **Cấp 0 — CHÍNH THỐNG (ưu tiên #1)** | §1bis(a)+(b): Cochrane/Epistemonikos/NICE/USPSTF + guideline **hiệp hội chuyên khoa** (ESC/ACC-AHA/ADA/KDIGO/GOLD/GINA/IDSA/EULAR-ACR/ASCO-ESMO/…) + **kcb.vn** (VN) | **NGUỒN CỦA RECORD** cho khuyến cáo; trích tên guideline + năm + mục + URL chính thức + PMID/DOI của bản công bố |
| **Cấp 0.5 — Tạp chí đỉnh** | §1bis(c): NEJM/Lancet/JAMA/BMJ/Annals/Nature Medicine + tạp chí chuyên khoa hàng đầu | Toàn văn nghiên cứu gốc/đồng thuận; **luôn kèm PMID/DOI** (metadata qua PubMed/Crossref/Europe PMC) |
| **Cấp 1 — Bình duyệt + ĐỐI CHIẾU** | PubMed/MEDLINE + Europe PMC (bài bình duyệt); ClinicalTrials.gov *(ghi `status`)*; bioRxiv/medRxiv *(nhãn "chưa bình duyệt")* | Lấy **PMID/DOI + đối chiếu/khử trùng** cho chứng cứ Cấp 0/0.5; tìm sơ cấp độc lập CHỈ khi Cấp 0/0.5 không phủ (khoảng trống → ghi rõ) |
| **Chỉ KHÁM PHÁ** | Consensus | Định hướng tìm; **mọi khẳng định phải truy ngược PMID/DOI gốc** qua PubMed + `kiem-chung-trich-dan` rồi mới trích |
| **Bối cảnh NGHIÊN CỨU (không lâm sàng)** | ChEMBL | Làm rõ cơ chế/dược lý tiền lâm sàng; **KHÔNG** làm chỗ dựa cho khuyến cáo lâm sàng/cảnh báo kê đơn |
| **Công cụ mã hóa** | ICD-10 | Chuẩn hóa mã — không phải nguồn bằng chứng |

**Quy tắc đọc nguồn ClinicalTrials.gov:** trial **registry record ≠ kết quả công bố**. Luôn ghi rõ
`status` (recruiting / active / completed / results-posted). Thử nghiệm đang chạy/chưa có kết quả →
**KHÔNG** dùng làm bằng chứng hiệu quả, chỉ ghi nhận "đang nghiên cứu"; ưu tiên ấn phẩm bình duyệt khi đã có.

---

## 2bis. THỨ TỰ TRA CỨU MẶC ĐỊNH (nguồn chính thống trước · PubMed là lớp đối chiếu)
> Thao tác hóa §0.7 cho mọi agent tra cứu/thẩm định/tổng quan. **Yêu cầu bác sĩ: ưu tiên nguồn chính thống; CHỈ lấy từ PubMed khi chứng cứ TRÙNG (đối chiếu/lấy định danh).**
1. **Kho nội bộ:** (a) **EBM_MASTER** (`EBM_MASTER/EBM_MASTER.json` — 744+ thẻ đã kiểm PMID/DOI, tra qua `Antifacts.html`/`EBM_WEBAPP.html`/`DANH_MUC.html`) — kho curated THẬT có nội dung, tra trước; (b) RAG `clinical-evidence-rag` trên `medical-ebm-automation/evidence/` — **SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 19, phát hiện HIGH — trước gọi đây là "đáng tin nhất" mà không nói rõ phần lớn thư mục còn TRỐNG):** chỉ đáng tin cho câu hỏi trùng 32 thang điểm nguy cơ đã review (`evidence/reviews/`); các thư mục `guidelines/`/`protocols/` gần như toàn "⬜ cần thả PDF" theo chính `evidence/index.md` — câu hỏi khác nhiều khả năng KHÔNG có gì ở đây (khác PARTIAL "connector lỗi", đây là "kho chưa có nội dung cho câu hỏi này" — ghi rõ, không lặng lẽ bỏ qua).
2. **Cấp 0 — nguồn CHÍNH THỐNG** (§1bis a+b): Cochrane/HTA + guideline hiệp hội chuyên khoa (+ **kcb.vn** cho VN). Đây là **nơi lấy khuyến cáo/kết luận**.
3. **Cấp 0.5 — tạp chí đỉnh** (§1bis c): lấy toàn văn nghiên cứu gốc/đồng thuận khi cần chi tiết.
4. **PubMed/Europe PMC — LỚP ĐỐI CHIẾU & KHỬ TRÙNG:** với mỗi chứng cứ từ bước 2–3, tra để (a) **lấy PMID/DOI** cho mọi mục (bất biến verify), và (b) **xác nhận trùng khớp** (cùng nghiên cứu/khuyến cáo, không phải 2 nguồn mâu thuẫn). **KHÔNG** dùng PubMed làm điểm khởi đầu tìm kiếm độc lập khi Cấp 0/0.5 đã trả lời.
5. **CHỈ mở rộng tìm PubMed/Europe PMC sơ cấp độc lập** khi nguồn chính thống **KHÔNG phủ** câu hỏi (khoảng trống thật) — khi đó nêu rõ "nguồn chính thống chưa phủ → bổ sung y văn sơ cấp".
> **Bất biến giữ nguyên:** mọi mục cần **PMID/DOI** (hoặc URL guideline chính thức + năm) để verify; nguồn thiếu → **PARTIAL** (không kết luận "không có"); **KHÔNG PII outbound**; **chỉ nguồn miễn phí** (loại Consensus upsell — §3); nguồn bậc cao mâu thuẫn → nêu mâu thuẫn, không chọn bài hợp ý.

---

## 3. ⚠ HẠNG MỤC CẦN BÁC SĨ QUYẾT trước khi mở rộng (KHÔNG tự bật)
- **Consensus có UPSELL TRẢ PHÍ.** Hướng dẫn MCP của Consensus buộc in nguyên văn thông điệp đăng ký/nâng
  cấp trả phí ở cuối kết quả — **xung đột** luật "CHỈ nguồn miễn phí, không backend trả phí" của gói nghiên cứu
  (`tong-quan-y-van` §Luật nền). Vì vậy hiện chốt: Consensus = **discovery-only**, KHÔNG trích cấp 1, KHÔNG
  dùng cho đầu ra SR/đề tài cho tới khi **[CẦN BÁC SĨ QUYẾT]** cách xử lý upsell.
- **ChEMBL cho `ke-don-an-toan`:** ChEMBL là CSDL bioactivity tiền lâm sàng (IC50/Ki/ADMET dự đoán) — KHÔNG
  cung cấp mức nặng tương tác (DDI), ngưỡng chỉnh liều theo thận, tiêu chí Beers/STOPP. Cảnh báo kê đơn vẫn
  dựa **nhãn thuốc/openFDA + guideline + PMID/DOI**. ChEMBL chỉ enrichment phía NGHIÊN CỨU. **[CẦN BÁC SĨ XÁC NHẬN]**.

---

## 4. BẢN ĐỒ AGENT ↔ CONNECTOR (agent trỏ về file này)

| Agent | Connector nên dùng |
|---|---|
| `tra-cuu-chung-cu` | PubMed (đủ bộ) · Consensus *(discovery)* · ClinicalTrials *(điều trị)* |
| `pico-lam-sang` · `chan-doan-xac-suat` | PubMed *(LR/độ nhạy-đặc hiệu, quy tắc dự đoán)* |
| `tham-dinh-grade-nnt` · `tham-dinh-phe-binh` | PubMed `get_full_text_article` *(đọc toàn văn để chấm RoB/GRADE)* |
| `dien-giai-can-lam-sang` | PubMed *(ngưỡng/giá trị tham chiếu)* · ICD-10 *(mã hóa)* |
| `ke-don-an-toan` | PubMed *(tương tác/cảnh báo có nguồn)* — **KHÔNG** ChEMBL cho cảnh báo kê đơn (xem §3) |
| `thu-thu-tai-lieu` | PubMed (`get_article_metadata`/`convert_article_ids`) · bioRxiv *(preprint)* |
| `tong-quan-y-van` | PubMed · bioRxiv *(văn liệu xám)* · ClinicalTrials *(đăng ký)* — **KHÔNG** Consensus (xem §3) |
| `trich-xuat-y-van` · `meta-phan-tich` | PubMed `get_full_text_article` *(trích số liệu/CI)* |
| `kiem-chung-trich-dan` | PubMed `convert_article_ids`/`lookup_article_by_citation`/`get_article_metadata` *(phân giải định danh)* |
| `cau-hoi-nghien-cuu` · `khoang-trong-nghien-cuu` | PubMed · ClinicalTrials *(đối chiếu đã làm chưa)* |
| `cap-nhat-guideline` · `huong-dan-lam-sang` | PubMed + `WebFetch`/`WebSearch` trang hội *(xem `_NGUON-GUIDELINE-TU-DONG.md`)* |
| `thiet-ke-nghien-cuu` · `co-mau-nghien-cuu` · `dao-duc-dang-ky` | ClinicalTrials `analyze_endpoints`/`get_trial_details` *(benchmark thiết kế)* |

> Engine Python `medical-ebm-automation` **KHÔNG** dùng connector MCP — nó là pipeline batch chạy theo
> lịch (không có phiên Agent) nên gọi HTTP trực tiếp tới 8 nguồn (pubmed/europepmc/crossref/clinicaltrials/
> openalex/semantic_scholar/openfda/unpaywall). Đó là kiến trúc đúng; MCP thuộc về tầng Agent này.

> **"Cần bác sĩ kiểm chứng."**
