# Medical EBM Automation – Hệ thống tự động hoá cập nhật chứng cứ y khoa & quản lý nghiên cứu

Hệ thống tự động hoá phục vụ bác sĩ lâm sàng ngoại trú và nghiên cứu y khoa, với 2 trục:

1. **Cập nhật kiến thức y khoa (EBM)** mới nhất, đáng tin cậy, có khả năng thay đổi thực hành.
2. **Quản lý quy trình nghiên cứu y khoa** (đề cương, đạo đức, thu thập, phân tích, IMRAD).

> ⚠️ **Nguyên tắc cốt lõi:** không bịa dữ liệu, ưu tiên nguồn chính thống có thể truy vết,
> không biến preprint/FAERS/nghiên cứu nhỏ thành khuyến cáo thực hành.

---

## 1. Mục tiêu hệ thống

- Quét nhiều nguồn (PubMed, Europe PMC, Crossref, ClinicalTrials.gov, OpenAlex, Semantic Scholar, openFDA…).
- Chuẩn hoá, loại trùng, **chấm điểm chứng cứ** và **phân tầng độ tin cậy** bằng luật minh bạch.
- Tách rõ phần **actionable** (đáng thay đổi thực hành) và phần **chưa đủ bằng chứng**.
- Sinh **báo cáo EBM tuần** (Markdown/HTML/Word), xuất Excel/CSV/BibTeX.
- **Dashboard web** 9 tab + **scheduler** chạy định kỳ.
- Lưu **lịch sử cập nhật** (raw, processed, change log) – không mất dữ liệu cũ.

## 2. Cài đặt

Yêu cầu Python 3.10+ (khuyến nghị 3.12). Hệ thống đã được kiểm thử trên 3.9 nhờ
`from __future__ import annotations`, nhưng nên dùng 3.12 cho production.

> ⚠️ **QUAN TRỌNG:** TẠO MÔI TRƯỜNG PYTHON (venv) NGOÀI thư mục đồng bộ đám mây
> (OneDrive/iCloud/Dropbox). Cloud sync hay "làm rỗng" (online-only) file biên dịch
> của numpy/pandas → gây lỗi `ImportError: ...import numpy from its source directory`.
> Code/dữ liệu vẫn để trong OneDrive được; chỉ riêng **venv phải ở ổ máy**.

```bash
# Tạo venv ở HOME (ngoài OneDrive), cài thư viện từ requirements trong dự án:
python3 -m venv ~/.ebm-venv
~/.ebm-venv/bin/pip install -r "<đường-dẫn>/medical-ebm-automation/requirements.txt"

# Mỗi lần chạy: kích hoạt venv rồi vào thư mục dự án
source ~/.ebm-venv/bin/activate
cd "<đường-dẫn>/medical-ebm-automation"
# (Windows: tạo venv tại C:\ebm-venv — xem docs/HUONG_DAN_WINDOWS.md)
```

## 3. Cấu hình `.env`

```bash
cp .env.example .env
```

Mở `.env` và điền (mọi key đều tùy chọn – thiếu key thì nguồn chạy ở chế độ **mock**):

| Biến | Ý nghĩa |
|------|---------|
| `USE_MOCK_SOURCES` | `true` = chạy offline bằng dữ liệu mẫu; `false` = gọi API thật |
| `NCBI_EMAIL`, `NCBI_API_KEY` | PubMed E-utilities (email bắt buộc khi gọi thật) |
| `OPENALEX_EMAIL`, `UNPAYWALL_EMAIL` | "polite pool" của OpenAlex/Unpaywall |
| `SEMANTIC_SCHOLAR_API_KEY` | tăng rate limit Semantic Scholar |
| `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_ID` | đẩy tài liệu vào Zotero (bật `ENABLE_ZOTERO=true`) |
| `MIN_EVIDENCE_SCORE`, `MIN_PRACTICE_CHANGE_SCORE` | ngưỡng để 1 mục được coi là *actionable* |
| `ENABLE_*` | bật/tắt từng nguồn |

> **Không bao giờ hard-code API key trong code.** Tất cả nạp từ `.env`.

## 4. Chạy lần đầu

```bash
python run.py
```

Lệnh này sẽ: tạo database → seed 45 thang điểm + 2 đề tài nghiên cứu mẫu →
chạy pipeline (mock) → xuất báo cáo tuần. Sau đó:

```bash
python run.py dashboard      # mở dashboard tại http://localhost:8501
```

## 5. Chạy dashboard

```bash
python run.py dashboard
# hoặc: streamlit run app/dashboard/app.py
```

Dashboard có 9 tab: Executive, Weekly EBM, Drug Safety, Antibiotics, Guidelines,
Research, Clinical Scores, Source Log, Change Log. Nút bên trái cho phép **seed**,
**chạy lại pipeline**, và **xuất báo cáo**.

## 6. Chạy cập nhật tuần

```bash
python run.py report     # chạy pipeline + xuất EBM_Weekly_Update_YYYYMMDD.{md,html,docx}
python run.py export     # xuất Dashboard/Research/Source Log/BibTeX
```

Tự động hoá định kỳ:

```bash
python run.py schedule   # APScheduler: daily / weekly / monthly / quarterly
```

## 7. Cách thêm API mới

1. Tạo `app/sources/my_source.py`, kế thừa `SourceClient` (xem `app/sources/base.py`).
2. Triển khai `search()` (gọi thật) và `mock_search()`/fallback mock.
3. Đăng ký trong `app/sources/__init__.py:get_enabled_sources()` kèm flag `ENABLE_*`.
4. Nguồn trả về `RawRecord`; phần normalize/score/filter tự động áp dụng.

## 8. Cách thêm guideline source mới

- Nếu có API/RSS: viết connector như mục 7.
- Nếu **không** có API (đa số tổ chức): dùng **manual import** trong
  `app/sources/guidelines.py` → `ManualGuideline(...)` rồi `manual_import([...])`.
  Hệ thống lưu metadata + `verification_status` mà **không tự crawl vi phạm ToS**.

## 9. Cách thêm đề tài & dùng module nghiên cứu

```python
from app.research import add_project
add_project({
    "project_id": "RES-2026-010",
    "project_title": "…",
    "study_design": "Cohort tiến cứu",
    "ethics_status": "in_progress",
    # … xem schema trong app/models/research.py
})
```

**Hồ sơ nghiên cứu tự động** (đề cương rút gọn + tài liệu nền EBM + gợi ý biến số +
gợi ý thống kê theo thiết kế + checklist hội đồng đạo đức + checklist nghiệm thu +
trích dẫn Vancouver/NLM):

```bash
python run.py dossier RES-2026-001     # xuất Research_Dossier_<id>_YYYYMMDD.md
```

Ở chế độ **live**, phần "Tài liệu nền" tự tìm guideline/SR/MA/RCT đúng chủ đề từ API
thật. Gợi ý thống kê bám thiết kế: cohort → Kaplan-Meier/Cox/STROBE; RCT → ITT/CONSORT/
NNT; case-control → OR/logistic. **Không tự chạy số liệu, không bịa kết quả.**

**Đẩy tài liệu vào Zotero** (cần `ENABLE_ZOTERO=true` + key): `python run.py zotero-push`
— đẩy các mục actionable/need_full_text kèm tag chuyên khoa + tier + phân loại.

## 10. Cách xuất báo cáo

| Hàm | File |
|-----|------|
| `export_weekly_ebm_markdown()` | `EBM_Weekly_Update_YYYYMMDD.md` |
| `export_weekly_ebm_html()` | `EBM_Weekly_Update_YYYYMMDD.html` |
| `export_weekly_ebm_docx()` | `EBM_Weekly_Update_YYYYMMDD.docx` |
| `export_dashboard_excel()` | `Dashboard_Master_EBM_YYYYMMDD.xlsx` |
| `export_research_tracker_excel()` | `Research_Tracker_YYYYMMDD.xlsx` |
| `export_source_log_csv()` | `Source_Log_YYYYMMDD.csv` |
| `export_zotero_bibtex()` | `Zotero_Export_YYYYMMDD.bib` |

Báo cáo lưu ở `data/reports/`, dữ liệu xuất ở `data/exports/`.

## 11. Giới hạn của hệ thống

- Scoring là **rule-based vận hành**, KHÔNG thay thế thẩm định GRADE chính thức.
- Dữ liệu mock chỉ để demo pipeline – **không dùng làm khuyến cáo lâm sàng**.
- Nhiều guideline phải nhập tay (không có API công khai).
- Hệ thống **hỗ trợ quyết định**, không tự ra quyết định lâm sàng.
- Công thức thang điểm để trống (`needs_verification`) cho tới khi được nhập kèm nguồn.

## 12. Nguyên tắc không bịa đặt & kiểm soát chứng cứ

1. Không tạo DOI/PMID/guideline giả.
2. Không tự gán GRADE nếu nguồn không có – nếu ước lượng thì ghi rõ *operational estimate*.
3. Không kết luận thay đổi thực hành khi chưa đủ nguồn.
4. Không dùng abstract đơn lẻ để khuyến cáo mạnh khi cần full-text.
5. Không dùng **preprint** để thay đổi thực hành.
6. Không dùng **FAERS** để kết luận nhân quả (chỉ là tín hiệu).
7. Không đưa quảng cáo thuốc vào báo cáo.
8. Không bịa số liệu hiệu quả/chi phí/NNT khi không có dữ liệu thật.
9. **Mỗi mục actionable có lý do** *vì sao actionable*; mỗi mục không actionable có lý do *vì sao chưa*.
10. **Mỗi khuyến nghị có nguồn truy vết** (DOI/PMID/NCT/URL).

---

## Cấu trúc thư mục

```
medical-ebm-automation/
├── app/
│   ├── main.py            # CLI nội bộ
│   ├── config.py          # cấu hình từ .env (CLINICAL_AREAS, ngưỡng…)
│   ├── scheduler.py       # job daily/weekly/monthly/quarterly
│   ├── database.py        # engine/session SQLAlchemy (SQLite→Postgres)
│   ├── models/            # EvidenceItem, ResearchProject, ClinicalScore, ChangeLog, SourceLog
│   ├── services/          # ingestion, normalization, deduplication, filtering, synthesis, pipeline
│   ├── sources/           # PubMed, EuropePMC, Crossref, ClinicalTrials, openFDA, OpenAlex, S2, Unpaywall, Zotero, guidelines
│   ├── scoring/           # evidence_quality, practice_change, reliability, operational_level
│   ├── reports/           # weekly_ebm, exporters
│   ├── research/          # quản lý đề tài + tích hợp EBM
│   ├── clinical_scores/   # danh mục ~45 thang điểm
│   ├── dashboard/         # Streamlit app (9 tab)
│   └── utils/             # logging, http (retry/backoff/cache), seed
├── data/ (raw/ processed/ reports/ exports/ archive/)
├── templates/  tests/  docs/
├── .env.example  requirements.txt  run.py  README.md
```

## Lệnh CLI

| Lệnh | Mô tả |
|------|-------|
| `python run.py` | init + seed + báo cáo tuần (mặc định) |
| `python run.py init` | chỉ tạo database |
| `python run.py seed` | nạp dữ liệu mẫu |
| `python run.py pipeline` | chạy pipeline EBM |
| `python run.py report` | pipeline + xuất báo cáo tuần |
| `python run.py live-update` | **QUÉT API THẬT (chỉ bài MỚI)** + bản tin cảnh báo + đủ báo cáo |
| `python run.py alert [N]` | bản tin **"Cảnh báo mới trong N ngày"** (mặc định 7) |
| `python run.py notify [N]` | **gửi** cảnh báo email/webhook nếu có mục mới ưu tiên cao |
| `python run.py export` | xuất Excel/CSV/BibTeX |
| `python run.py safety` | xuất báo cáo An toàn thuốc + Kháng sinh tuần (riêng) |
| `python run.py dossier <project_id>` | xuất Hồ sơ nghiên cứu (đề cương + tài liệu nền + checklist) |
| `python run.py zotero-push` | đẩy tài liệu actionable vào Zotero (cần cấu hình) |
| `python run.py test-live [nguồn] [từ khoá]` | gọi 1 nguồn **API thật** để kiểm chứng kết nối + scoring |
| `python run.py dashboard` | mở dashboard Streamlit |
| `python run.py schedule` | chạy scheduler định kỳ |

### Dùng cho thực hành thật (chế độ live)

```bash
# 1. Cấu hình email (gọi API lịch sự) trong .env:
#    NCBI_EMAIL=ban@email.com   OPENALEX_EMAIL=...   UNPAYWALL_EMAIL=...
#    USE_MOCK_SOURCES=false
# 2. Cập nhật tuần thực tế (quét PubMed/Europe PMC/Crossref/ClinicalTrials thật):
python run.py live-update
```

Chế độ live phân loại chứng cứ trên metadata thật: guideline/SR/MA/RCT được nhận diện
từ tiêu đề + tạp chí; **preprint tự động bị loại (tier D)**; nguồn từ tổ chức chính thống
(ESC/AHA/NICE/KDIGO/NEJM/Lancet…) được cộng điểm. Nguồn lỗi/thiếu key tự fallback mock.

### "Mới tuần này" – cập nhật incremental (đúng nghĩa tự động cảnh báo)

Hệ thống ghi **watermark** mỗi lần chạy (bảng `pipeline_runs`). Lần chạy sau:
1. Chỉ **lấy bài MỚI từ API** kể từ mốc lần trước (lọc ngày: PubMed `mindate`, Europe PMC
   `FIRST_PDATE`, Crossref `from-pub-date`, OpenAlex `from_publication_date`, CT.gov
   `LastUpdatePostDate`) — đệm chồng lấp 2 ngày để không sót bài index trễ.
2. Mỗi bản ghi **lần đầu** vào kho được gắn `first_seen_run_id` → đó là "mới".
3. **Bản tin cảnh báo** `Alert_Digest_*.md/html` chỉ liệt kê cái mới, ưu tiên:
   cảnh báo an toàn thuốc chính thức → guideline mới → actionable mới → cần đọc toàn văn.
4. Chạy lại khi không có gì mới → bản tin ghi **"Không có cập nhật mới"** (không bịa tin).

Scheduler: job **daily** tự quét incremental + xuất alert (cửa sổ 1 ngày); job **weekly**
xuất alert 7 ngày. Báo cáo EBM tuần có thêm mục **"🆕 Mới từ lần cập nhật trước"**.

### Nguồn an toàn thuốc & guideline THẬT (RSS/Atom – tự động)

Hệ thống đọc trực tiếp các feed CHÍNH THỐNG công khai (đã kiểm tra hoạt động):

| Feed | Tổ chức | Loại |
|------|---------|------|
| MedWatch Safety Alerts | FDA | An toàn thuốc/thiết bị |
| Recalls & Safety Alerts | FDA | Thu hồi (thuốc/thiết bị/thực phẩm) |
| Drug Safety Update | MHRA (GOV.UK) | An toàn thuốc |
| MMWR Recommendations | CDC | Khuyến cáo/guideline |
| Current Issue | NEJM | Tạp chí chất lượng cao |

- Bật/tắt: `ENABLE_DRUG_SAFETY_FEEDS`, `ENABLE_GUIDELINE_FEEDS`.
- Cảnh báo cơ quan quản lý (FDA/MHRA) gắn `regulatory_alert` → **trọng số cao**, lên đầu bản tin.
- Feed có lọc theo `since_date` (chỉ mục mới). Feed lỗi → ghi Source Log + bỏ qua (không bịa).
- **Lưu ý:** feed FDA Recalls khá rộng (gồm cả thiết bị/thực phẩm); MHRA DSU là feed thuốc gọn nhất.
  Sửa/thêm feed tại `app/sources/feeds.py` (đã đánh dấu URL cần kiểm chứng định kỳ).

### Gửi cảnh báo tự động (email + webhook)

```bash
python run.py notify        # gửi nếu có mục mới ưu tiên cao (an toàn thuốc/guideline/actionable)
```

Cấu hình trong `.env`: `ENABLE_EMAIL_ALERTS=true` + `SMTP_HOST/PORT/USER/PASSWORD/SMTP_FROM/
ALERT_EMAIL_TO`, và/hoặc `ALERT_WEBHOOK_URL` (Slack/Telegram/n8n). **Chỉ gửi khi thật sự có
mục ưu tiên cao mới** — không có gì mới thì không gửi (không spam). Chưa cấu hình → tự bỏ qua.
Scheduler daily/weekly tự gọi `notify` sau mỗi lần quét.

### Test một nguồn ở chế độ API thật

Không cần đổi `.env`; lệnh ép riêng 1 connector gọi thật (khuyến nghị nguồn không cần key):

```bash
python run.py test-live europepmc "tenecteplase ischemic stroke"
python run.py test-live crossref "KDIGO chronic kidney disease 2024"
python run.py test-live clinicaltrials "SGLT2 inhibitor heart failure"
```

Kết quả in DOI/PMID thật + điểm chứng cứ + phân loại (preprint tự động bị loại tier D).

## Thang điểm đã xác minh

**30 công cụ** có **công thức + cut-off + nguồn gốc** (`update_status=verified`) — xem
`app/clinical_scores/verified.py`:
- Tim mạch: CHA2DS2-VASc, HAS-BLED, Wells DVT/PE, NYHA, TIMI, ASCVD-PCE, SCORE2
- Hô hấp: CURB-65, PERC, NEWS2, GOLD ABE
- Thận: CKD-EPI/eGFR + KDIGO grid, Anion Gap
- Gan mật: Child-Pugh, MELD-Na, FIB-4, APRI, Maddrey DF, Glasgow-Blatchford
- Lão khoa/chuyển hoá/khác: FRAIL, FINDRISC, HOMA-IR, qSOFA, Centor/McIsaac, PHQ-9, GAD-7, AUDIT-C

> Với công cụ độc quyền/phức tạp (ASCVD-PCE, SCORE2, MELD-Na/MELD 3.0): hệ thống **không
> tự nhập hệ số tay** mà ghi rõ phải dùng calculator chính thức + nêu ngưỡng & nguồn.
> Các công cụ còn lại để `needs_verification` (chưa điền công thức, **không bịa**). Khi
> guideline đổi cách dùng → ghi vào change log.

## Kiểm thử

```bash
pytest -q      # 49 test: scoring, dedup, filtering, mock+live classify, pipeline/DB,
               # reports, clinical scores (verified), drug safety/antibiotic,
               # research dossier/checklists/stats, incremental "mới tuần này",
               # RSS feed parsing + gửi cảnh báo
```

Xem thêm `docs/OPERATIONS.md` để biết hướng dẫn vận hành chi tiết.
