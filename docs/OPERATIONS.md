# Hướng dẫn vận hành (Operations Guide)

## Luồng pipeline (7 bước)

1. **Ingestion** (`services/ingestion.py`): gọi nguồn theo `CLINICAL_AREAS` (config),
   lưu raw payload vào `data/raw/<source>/`, ghi `SourceLog`.
2. **Normalization** (`services/normalization.py`): map `RawRecord` → schema chuẩn.
3. **Deduplication** (`services/deduplication.py`): gộp trùng theo DOI/PMID/PMCID/NCT/
   tương đồng tiêu đề/(org+title+version). Bản trùng được liên kết qua `DuplicateLink`,
   **không xóa**. Trước đó pipeline gộp các bản trùng *cùng nguồn* để mỗi hàng DB là duy nhất.
4. **Scoring** (`scoring/`): Evidence Quality (0–100), Practice Change (0–100),
   Reliability Tier (A/B/C/D), Operational Evidence Level (High/Moderate/Low).
5. **Filtering** (`services/filtering.py`): phân loại
   `actionable | need_full_text | watch_only | excluded` + lý do.
6. **Synthesis** (`services/synthesis.py`): tóm tắt lâm sàng theo mẫu cố định.
7. **Persist + Changelog + Archive**: upsert idempotent theo `(source + định danh)`,
   ghi `ChangeLogEntry`, lưu snapshot `data/processed/pipeline_<ts>.json`.

## Kiểm tra log

- Log ứng dụng: `data/archive/app.log` (xoay vòng 2MB × 5 file).
- Nhật ký nguồn: bảng `source_log` (Tab 8 dashboard) hoặc `Source_Log_*.csv`.
- Change log: bảng `change_log` (Tab 9 dashboard).
- Raw payload từng lần gọi: `data/raw/<source>/<timestamp>_<query>.json`.
- Snapshot processed: `data/processed/pipeline_<timestamp>.json`.

```bash
tail -f data/archive/app.log
sqlite3 data/medical_ebm.db "SELECT source, status, COUNT(*) FROM source_log GROUP BY source, status;"
```

## Chuyển từ mock sang API thật

1. Đặt `USE_MOCK_SOURCES=false` trong `.env`.
2. Điền tối thiểu `NCBI_EMAIL` (PubMed), `OPENALEX_EMAIL`, `UNPAYWALL_EMAIL`.
3. Chạy `python run.py pipeline`. Nếu 1 nguồn lỗi/thiếu key, nó tự fallback mock
   và ghi trạng thái vào Source Log – pipeline không dừng.

## Nâng cấp SQLite → PostgreSQL

1. Đổi `DATABASE_URL=postgresql+psycopg://user:pass@host/db` trong `.env`.
2. `pip install "psycopg[binary]"`.
3. `python run.py init` để tạo schema. Mọi model dùng SQLAlchemy nên không đổi code.

## Lịch scheduler

| Job | Lịch mặc định | Việc làm |
|-----|---------------|----------|
| daily | 07:00 | quét nhanh an toàn thuốc/guideline + kiểm lỗi |
| weekly | Thứ 2, 07:30 | báo cáo EBM tuần + cập nhật exports |
| monthly | ngày 1, 08:00 | Practice Change Monthly Review |
| quarterly | 1/1,4,7,10, 09:00 | rà soát thang điểm/nguồn/guideline nền |

Đổi lịch trong `app/scheduler.py:build_scheduler()`.

## An toàn dữ liệu

- Pipeline **chỉ thêm/cập nhật**, không xóa. Chạy lại nhiều lần là idempotent
  (kiểm thử `tests/test_pipeline_db.py::test_rerun_does_not_lose_data`).
- Mỗi lần chạy lưu raw + processed snapshot riêng (có timestamp).
