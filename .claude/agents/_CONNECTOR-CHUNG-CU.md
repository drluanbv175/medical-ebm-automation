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

## 2. PHÂN TẦNG THẨM QUYỀN NGUỒN (nối vào rubric Q7 `_CHUAN-CHAT-LUONG-MEDPALM.md` + R7)

| Tầng | Connector | Được làm gì |
|---|---|---|
| **Cấp 1 — TRÍCH DẪN được** | PubMed (bài bình duyệt); ClinicalTrials.gov *(có ghi `status`)*; bioRxiv/medRxiv *(có nhãn preprint "chưa bình duyệt")* | Vào bảng nguồn chính kèm PMID/DOI/NCT-ID; làm nền khuyến cáo (theo thứ bậc chứng cứ) |
| **Chỉ KHÁM PHÁ** | Consensus | Định hướng tìm; **mọi khẳng định phải truy ngược PMID/DOI gốc** qua PubMed + `kiem-chung-trich-dan` rồi mới trích |
| **Bối cảnh NGHIÊN CỨU (không lâm sàng)** | ChEMBL | Làm rõ cơ chế/dược lý tiền lâm sàng; **KHÔNG** làm chỗ dựa cho khuyến cáo lâm sàng/cảnh báo kê đơn |
| **Công cụ mã hóa** | ICD-10 | Chuẩn hóa mã — không phải nguồn bằng chứng |

**Quy tắc đọc nguồn ClinicalTrials.gov:** trial **registry record ≠ kết quả công bố**. Luôn ghi rõ
`status` (recruiting / active / completed / results-posted). Thử nghiệm đang chạy/chưa có kết quả →
**KHÔNG** dùng làm bằng chứng hiệu quả, chỉ ghi nhận "đang nghiên cứu"; ưu tiên ấn phẩm bình duyệt khi đã có.

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
