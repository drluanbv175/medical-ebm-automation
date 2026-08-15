# Công cụ tích hợp CAFÉ-S — hướng dẫn dùng cho bác sĩ

5 module ở `app/integrations/` đóng các trụ CAFÉ-S (kết nối dữ liệu chuẩn + đa phương thức +
an toàn thuốc). Có **2 cách dùng**:

**Cách 1 — Dashboard bấm-chạy (dễ nhất):** bấm đúp `Mở Công cụ tích hợp.command`
(hoặc `streamlit run app/dashboard/integrations_panel.py`). Trang 5 tab: tương tác thuốc ·
ambient SOAP · đọc ảnh · FHIR R4 · trích dẫn thang điểm — nhập/tải lên rồi bấm, không cần gõ lệnh.

**Cách 2 — Dòng lệnh (CLI), một cửa:**
```bash
python -m app.integrations.cli list          # xem tất cả công cụ
```

> Bất biến chung: **KHÔNG lưu PII**; đầu ra là **BẢN NHÁP** kèm "Cần bác sĩ kiểm chứng"; chỉ
> ĐỀ XUẤT — bác sĩ duyệt mới áp dụng. Công cụ nhạy cảm (ambient/đọc ảnh) có **cổng đồng thuận**.

| Lệnh | Làm gì | Trụ | Yêu cầu |
|------|--------|-----|---------|
| `cli drug <t1> <t2>…` | Sàng lọc tương tác/chống chỉ định thuốc qua nhãn openFDA (miễn phí) | 1.3 | mạng |
| `cli soap --transcript f.txt` | Hội thoại buổi khám → khử PII → bản nháp SOAP | 5.2 | STT cần `faster-whisper`; câu chữ cần LLM/skill |
| `cli image <file> --modality ecg --consent` | Ảnh ECG/CXR/CLS → khử EXIF → đọc có hệ thống | 2.3 | `Pillow` + `ANTHROPIC_API_KEY` (vision) |
| `cli fhir [--base URL]` | Kết nối FHIR R4 (EMR/HIS), đọc — **chặn ghi** mặc định | 2.2 | mặc định HAPI sandbox |

## 1. Tương tác thuốc (`drug`) — dùng được ngay, không cần key
```bash
python -m app.integrations.cli drug warfarin aspirin
python -m app.integrations.cli drug simvastatin amiodarone metformin
```
Trả cờ tương tác/CCĐ chéo + cảnh báo đóng khung từng thuốc, **kèm nguồn (openFDA set_id)**.
Giới hạn: sàng lọc theo "đề-cập" trên nhãn (US), **không** phân hạng nặng; **không-cờ ≠ an toàn**.
Bổ trợ agent `ke-don-an-toan` (Beers/STOPP-START, chỉnh liều thận/gan).

## 2. Ambient SOAP (`soap`) — ghi hồ sơ từ hội thoại
```bash
python -m app.integrations.cli soap --transcript buoi_kham.txt          # từ transcript có sẵn
python -m app.integrations.cli soap --audio ca.m4a --consent --model base  # từ audio (cần faster-whisper)
```
Luồng: (khử EXIF/PII) → khử định danh 2 lớp → prompt SOAP theo skill `giao-tiep-quyet-dinh-soap`
→ (LLM/skill) → bản nháp S/O/A/P có placeholder + safety-netting + disclaimer. **Không lưu** audio/transcript.
Cài STT cục bộ (tuỳ chọn): `pip install faster-whisper`. Viết câu chữ: đặt `ANTHROPIC_API_KEY`
hoặc dán prompt CLI in ra vào skill `giao-tiep-quyet-dinh-soap` trong Claude.

## 3. Đọc ảnh (`image`) — ECG/CXR/phiếu CLS
```bash
python -m app.integrations.cli image ecg.jpg --modality ecg --consent
# modality: ecg | cxr | lab | generic
```
Khử EXIF thật (Pillow) → prompt đọc có hệ thống (ECG / ABCDE CXR / panel) **buộc không chép định
danh + nêu cờ đỏ** → vision LLM → Mô tả/Gợi ý/Cờ đỏ. **Bác sĩ che chữ burned-in trước khi chụp.**
Chỉ hỗ trợ đọc sơ bộ — KHÔNG thay đọc ECG/chẩn đoán hình ảnh chính thức.

## 4. FHIR R4 (`fhir`) — kết nối EMR/HIS chuẩn
```bash
python -m app.integrations.cli fhir                       # smoke HAPI sandbox
FHIR_BASE_URL=https://emr-noi-bo/fhir python -m app.integrations.cli fhir
```
Đọc Patient/MedicationRequest, **khử PHI** (`deidentify_patient`), **chặn ghi** (allow_write=False).
Chỉ trỏ EMR thật khi được phép; để thử dùng HAPI public sandbox (dữ liệu giả).

## Kiểm thử
Tất cả module có test offline: `pytest tests/test_fhir_client.py tests/test_ambient_scribe.py
tests/test_drug_interactions.py tests/test_image_reading.py tests/test_pii_adversarial.py
tests/test_integrations_cli.py`. Nhật ký đánh giá CAFÉ-S: `docs/CAFE-S-eval.md`.
