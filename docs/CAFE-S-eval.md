# CAFÉ-S — Nhật ký đánh giá Agent Y khoa

Chấm hệ EBM (đội agent + skill + dự án) theo rubric **CAFÉ-S** (Clinical Safety · Automation ·
Fidelity · Ethics · Scalability). Phân biệt: ✅ đạt(thiết kế) · 🧪 cần đo · 🔴 chưa đạt(cần xây) · ⚪ N/A.

## Đã ĐO (số thật)
| Ngày | Tiêu chí | Kết quả | Cách đo |
|------|----------|---------|---------|
| 2026-06-07 | **3.1 Citation Accuracy** | **100%** ID phân giải đúng (2/2 DOI qua Crossref); ~~độ phủ ID chỉ 6%~~ → **đã vá** (xem 2026-06-14) | Crossref API + quét `verified.py.source` |
| 2026-06-14 | **3.1 Độ phủ trích dẫn** | **6% → 90.6%** (29/32 thang có PMID/DOI đã xác minh PubMed/Crossref; 3 thang còn lại = báo cáo RCP/sách NYHA/báo cáo GOLD → KHÔNG tồn tại định danh, không bịa). Spot-check 6 mục trực tiếp PubMed = khớp 100% | 3 agent `thu-thu-tai-lieu` + PubMed E-utils + spot-check; cột `clinical_scores.pmid/doi`; 6 test |
| 2026-06-07 | **3.3 Recency** | ✅ Đạt — kéo được ESC 2024 AF theo yêu cầu (web thời gian thực) | WebSearch live |
| 2026-06-07 | **2.2 FHIR R4** | ✅ Đạt — `app/integrations/fhir_client.py`: kết nối HAPI R4 sandbox (4.0.1), đọc Patient/MedicationRequest, khử PHI, **chặn ghi mặc định**; 6 test offline xanh | Live smoke + pytest |
| 2026-06-14 | **1.3 Tương tác thuốc** | ✅ Đạt (sàng lọc) — `app/integrations/drug_interactions.py`: kéo nhãn openFDA (miễn phí, không key) → cờ tương tác/CCĐ chéo + cảnh báo đóng khung, kèm nguồn set_id. Live smoke: warfarin↔aspirin, simvastatin↔amiodarone (2 chiều) gắn cờ đúng. **Giới hạn:** sàng lọc theo đề-cập, không phân hạng nặng; không-cờ≠an toàn; bổ trợ `ke-don-an-toan` (Beers/STOPP-START) | 9 test offline + live smoke |
| 2026-06-14 | **4.1 Khử PII (adversarial)** | ✅ Đạt — bộ test đối kháng bịt rò: SĐT có dấu phân cách/+84, CCCD nhóm 3-3-3, ngày đầy đủ (HIPAA safe-harbor), email, nhiều "từ khóa dẫn" tên; số lâm sàng (140/90, eGFR) KHÔNG ẩn nhầm; FHIR `deidentify_patient` giữ đúng giới+năm. **Giới hạn ghi nhận:** tên đầu câu không có từ khóa dẫn vẫn lọt (cần NER) → còn lớp placeholder+bác sĩ | 20 test (`test_pii_adversarial.py`) |
| 2026-06-14 | **5.2 Ambient STT→SOAP** | ✅ Đạt (khung hạ tầng) — `app/integrations/ambient_scribe.py`: audio→STT (faster-whisper cục bộ, miễn phí) → **khử PII 2 lớp** → bản nháp SOAP nối skill `giao-tiep-quyet-dinh-soap`; cổng đồng thuận; KHÔNG lưu audio/transcript; 14 test offline xanh; demo end-to-end (stub STT+LLM) dựng SOAP có placeholder + safety-netting + disclaimer | pytest + demo |
| 2026-06-14 | **2.3 Đọc ảnh đa phương thức** | ✅ Đạt (khung hạ tầng) — `app/integrations/image_reading.py`: ảnh ECG/CXR/CLS → **khử EXIF thật (Pillow)** → prompt đọc CÓ HỆ THỐNG (ECG/ABCDE/panel) buộc KHÔNG chép định danh + nêu cờ đỏ → vision LLM (Claude opus, pluggable) → parse Mô tả/Gợi ý/Cờ đỏ; cổng đồng thuận; KHÔNG lưu ảnh; 9 test (gồm khử EXIF xóa định danh nhồi vào). **Giới hạn:** không xóa được chữ burned-in trên ảnh (bác sĩ che trước); chỉ hỗ trợ đọc sơ bộ | pytest (EXIF thật + stub vision) |

**~~Phát hiện vá được ngay~~ → ĐÃ VÁ (2026-06-14):** đã enrich PMID/DOI cho 29/32 thang `verified`
(cột mới `clinical_scores.pmid/doi` + `_VERIFIED_IDS` trong `verified.py`; helper `citation_links()`
sinh URL tự kiểm; độ phủ 6% → 90.6%). 3 thang còn lại không có định danh do là báo cáo/sách.

## Chương trình Phase 5 (3 workstream người dùng chọn)
1. **ĐO thực nghiệm Trụ 1 & 3** — bộ eval: 100 MCQ (ảo giác, cần answer-key + chuyên gia),
   20 ca/5 cấp cứu (red-flag sensitivity), cặp thuốc kinh điển (Rx), 50 trích dẫn.
   *Cần:* `ANTHROPIC_API_KEY` (chấm câu trả lời agent) + bộ dữ liệu có nguồn (không bịa).
2. **Vá điểm yếu thiết kế** — (a) ✅ enrich PMID/DOI cho 32 thang (3.1, 6%→90.6%);
   (b) ✅ tích hợp nguồn tương tác thuốc (openFDA) cho Rx checker (1.3); (c) ✅ bộ test adversarial PII (4.1).
3. **Xây hạ tầng** — (a) ✅ FHIR R4 client + test HAPI sandbox (2.2);
   (b) ✅ ambient STT→SOAP nối skill `giao-tiep-quyet-dinh-soap` (5.2);
   (c) ✅ đọc ảnh đa phương thức ECG/CXR/CLS (2.3). *Bộ ba hạ tầng đã xong khung.*

## Giới hạn trung thực
- 1.1 ảo giác / 1.2 cờ đỏ 100% / 3.2 Kappa>0.8 **không thể tự tuyên bố** — cần test có chuyên gia.
- 2.2 FHIR ✅ · 5.2 ambient ✅ · 2.3 đọc ảnh ✅ (đều là KHUNG hạ tầng, chạy cục bộ/pluggable LLM):
  chất lượng đầu ra còn phụ thuộc LLM + **bác sĩ duyệt**; STT/đọc ảnh tiếng Việt cần đo độ chính xác
  trên dữ liệu thật; khử PII không xử lý được chữ burned-in trên ảnh (bác sĩ che trước).
- **Còn lại (cần người dùng):** Workstream 1 (ĐO Trụ 1&3) cần `ANTHROPIC_API_KEY` + bộ dữ liệu có
  đáp án/chuyên gia; live STT/vision/SOAP cần key. Phần phần-mềm tự làm được đã xong.
- Trợ lý agent là DECISION-SUPPORT; một số trụ CAFÉ-S là cho SẢN PHẨM triển khai.
