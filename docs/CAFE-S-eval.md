# CAFÉ-S — Nhật ký đánh giá Agent Y khoa

Chấm hệ EBM (đội agent + skill + dự án) theo rubric **CAFÉ-S** (Clinical Safety · Automation ·
Fidelity · Ethics · Scalability). Phân biệt: ✅ đạt(thiết kế) · 🧪 cần đo · 🔴 chưa đạt(cần xây) · ⚪ N/A.

## Đã ĐO (số thật)
| Ngày | Tiêu chí | Kết quả | Cách đo |
|------|----------|---------|---------|
| 2026-06-07 | **3.1 Citation Accuracy** | **100%** ID phân giải đúng (2/2 DOI qua Crossref); **nhưng độ phủ ID chỉ 6%** (2/32 thang có PMID/DOI) | Crossref API + quét `verified.py.source` |
| 2026-06-07 | **3.3 Recency** | ✅ Đạt — kéo được ESC 2024 AF theo yêu cầu (web thời gian thực) | WebSearch live |
| 2026-06-07 | **2.2 FHIR R4** | ✅ Đạt — `app/integrations/fhir_client.py`: kết nối HAPI R4 sandbox (4.0.1), đọc Patient/MedicationRequest, khử PHI, **chặn ghi mặc định**; 6 test offline xanh | Live smoke + pytest |
| 2026-06-14 | **5.2 Ambient STT→SOAP** | ✅ Đạt (khung hạ tầng) — `app/integrations/ambient_scribe.py`: audio→STT (faster-whisper cục bộ, miễn phí) → **khử PII 2 lớp** → bản nháp SOAP nối skill `giao-tiep-quyet-dinh-soap`; cổng đồng thuận; KHÔNG lưu audio/transcript; 14 test offline xanh; demo end-to-end (stub STT+LLM) dựng SOAP có placeholder + safety-netting + disclaimer | pytest + demo |

**Phát hiện vá được ngay:** 30/32 thang điểm `verified` thiếu PMID/DOI trong `source` → cần enrich
để trích dẫn tự verify được (nâng độ phủ 6% → cao).

## Chương trình Phase 5 (3 workstream người dùng chọn)
1. **ĐO thực nghiệm Trụ 1 & 3** — bộ eval: 100 MCQ (ảo giác, cần answer-key + chuyên gia),
   20 ca/5 cấp cứu (red-flag sensitivity), cặp thuốc kinh điển (Rx), 50 trích dẫn.
   *Cần:* `ANTHROPIC_API_KEY` (chấm câu trả lời agent) + bộ dữ liệu có nguồn (không bịa).
2. **Vá điểm yếu thiết kế** — (a) enrich PMID/DOI cho 32 thang (3.1); (b) tích hợp CSDL/ API
   tương tác thuốc cho Rx checker (1.3); (c) bộ test adversarial PII (4.1).
3. **Xây hạ tầng** — (a) ✅ FHIR R4 client + test với HAPI public sandbox (2.2);
   (b) ✅ ambient STT→SOAP nối skill `giao-tiep-quyet-dinh-soap` (5.2). *Đã xong khung; còn (c) đa phương thức 2.3.*

## Giới hạn trung thực
- 1.1 ảo giác / 1.2 cờ đỏ 100% / 3.2 Kappa>0.8 **không thể tự tuyên bố** — cần test có chuyên gia.
- 2.2 FHIR ✅ · 5.2 ambient ✅ (khung hạ tầng, chạy cục bộ) — chất lượng câu chữ SOAP còn phụ
  thuộc LLM + bác sĩ duyệt; STT tiếng Việt cần đo độ chính xác trên audio thật. 2.3 đa phương thức = **chưa đạt**.
- Trợ lý agent là DECISION-SUPPORT; một số trụ CAFÉ-S là cho SẢN PHẨM triển khai.
