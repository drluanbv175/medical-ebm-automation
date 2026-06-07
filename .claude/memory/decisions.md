# Decisions (SSOT — Layer 2)

> Quyết định kiến trúc/sản phẩm quan trọng của `medical-ebm-automation`, thăng cấp (promote) từ auto-memory Layer 1.
> Mỗi mục là quyết định "WHY". Cách làm chi tiết "HOW" nằm ở `patterns.md`.
> Promote thêm bằng: `/memory sync`.

---

## D1: Không bao giờ fallback sang mock khi chạy live (liêm chính dữ liệu)

**Date**: 2026-06-06
**Tags**: #decision #data-integrity #ebm #guardrail
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
Ở chế độ live, mọi connector (pubmed/europepmc/crossref/openalex/clinicaltrials/openfda/semantic_scholar/rss_feed) khi gặp lỗi mạng/429 phải trả `[]` và ghi Source Log = error — TUYỆT ĐỐI không sinh dữ liệu mock vào kho thật. Nhánh mock chỉ chạy khi `self.use_mock` (chế độ demo).

### Background
Trước đây mọi connector fallback sang mock khi lỗi live → bịa dữ liệu giả vào kho thật. Đây là vi phạm nguyên tắc nền tảng của người dùng (bác sĩ EBM): không bịa dữ liệu, nguồn phải truy vết được.

### Options
1. Fallback mock khi lỗi: app luôn "có dữ liệu" nhưng dữ liệu giả lẫn vào kho thật — KHÔNG chấp nhận được về y khoa.
2. Trả `[]` khi lỗi live, mock chỉ ở chế độ demo: dữ liệu sạch, truy vết được — đã chọn.

### Adoption Reason
Người dùng là bác sĩ lâm sàng, ưu tiên tuyệt đối "không bịa dữ liệu". Một mục chứng cứ giả có thể dẫn tới khuyến cáo lâm sàng sai.

### Impact
Tất cả connector trong `app/sources/`. Khóa bằng test `tests/test_no_mock_fallback_live.py` (live error→[]; demo→mock).

### Review Conditions
Khi thêm connector mới — phải tuân pattern này, thêm test khóa tương ứng.

---

## D2: Đăng TikTok/video thủ công, không dùng TikTok API

**Date**: 2026-06-06
**Tags**: #decision #social #safety #human-in-the-loop
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
Module `app/social/` chỉ tạo GÓI nội dung (slide PNG + caption + hashtag + video) để bác sĩ DUYỆT rồi tự đăng tay. Không tích hợp TikTok Content Posting API ở giai đoạn hiện tại.

### Background
Nội dung y khoa công khai phải có người kiểm trước khi public; tự động đăng có rủi ro phát tán thông tin chưa duyệt.

### Options
1. Tự động đăng qua TikTok API: nhanh nhưng không có cổng kiểm duyệt người — rủi ro y khoa/uy tín.
2. Xuất gói để duyệt + đăng tay: an toàn, có human-in-the-loop — đã chọn.

### Adoption Reason
An toàn nội dung y khoa, giữ quyền kiểm soát cuối cùng cho bác sĩ.

### Impact
`app/social/content.py` còn gác độ tin: chỉ guideline/SR/RCT/cảnh báo chính thức (tier A/B) làm "CẬP NHẬT CHỨNG CỨ"; tài liệu yếu → "TIN NHANH·CHƯA KẾT LUẬN" (mặc định không đăng). Lịch nền TikTok là opt-in (`ENABLE_TIKTOK_AUTO` mặc định FALSE).

### Review Conditions
Khi cần tự đăng — chỉ làm sau khi có cơ chế duyệt rõ ràng và người dùng yêu cầu rõ.

---

## D3: Virtualenv đặt NGOÀI OneDrive (`~/.ebm-venv`)

**Date**: 2026-06-06
**Tags**: #decision #environment #onedrive #infra
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
Python venv đặt tại `~/.ebm-venv` (Mac) / `C:\ebm-venv` (Windows) — NGOÀI thư mục OneDrive. Code và data vẫn ở trong OneDrive.

### Background
Cloud sync của OneDrive làm rỗng/hỏng file binary trong venv.

### Options
1. venv trong OneDrive: tiện nhưng bị OneDrive làm hỏng file — không dùng.
2. venv ngoài OneDrive: ổn định — đã chọn.

### Adoption Reason
Tránh hỏng môi trường do cloud sync.

### Impact
Mọi launcher/script phải trỏ tới `~/.ebm-venv/bin/python`.

### Review Conditions
Nếu chuyển khỏi OneDrive sang git thuần thì có thể xem lại.

---

## D4: Dịch máy EN→VI nhưng luôn giữ kèm nguyên văn

**Date**: 2026-06-06
**Tags**: #decision #i18n #ebm #data-integrity
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
Dùng dịch máy (deep-translator GoogleTranslator) để hỗ trợ đọc, nhưng LUÔN giữ kèm nguyên văn EN với nhãn "dịch tham khảo". Mọi câu trích trên thẻ/slide phải là substring của nguồn gốc (không paraphrase).

### Background
Người dùng cần đọc tiếng Việt nhanh, nhưng dịch máy có thể sai/lặp rác; câu khuyến cáo y khoa không được bịa.

### Options
1. Chỉ hiển thị bản dịch: dễ đọc nhưng mất truy vết và rủi ro sai.
2. Giữ song song nguyên văn + dịch tham khảo: truy vết được, an toàn — đã chọn.

### Adoption Reason
Cân bằng dễ đọc và liêm chính chứng cứ.

### Impact
`app/services/translate.py` (cache `data/processed/_translations_vi.json`), `extraction.py`. Test đảm bảo câu trích là substring nguồn.

### Review Conditions
Khi đổi engine dịch — vẫn giữ ràng buộc "trích nguyên văn + nhãn dịch".

---

## D5: Mở rộng nguồn guideline — chỉ thêm feed đã verify, tránh nguồn chặn bot

**Date**: 2026-06-06
**Tags**: #decision #sources #rss #ebm
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
`GUIDELINE_FEEDS` chỉ chứa feed đã verify live (HTTP 200 + XML hợp lệ). Các nguồn chặn bot (403) — ESC/Eur Heart J, AHA Circulation, ATS, ERS, Lancet, WHO, EMA, NICE, Cochrane, ACP, Gastroenterology(AGA) — KHÔNG thêm vào feed (sẽ luôn lỗi); thay vào đó lấy qua PubMed bằng cụm văn bản thường trong `config.CLINICAL_AREAS`.

### Background
Nhiều hội lớn chặn bot RSS; thêm vào chỉ tạo lỗi liên tục và Source Log đỏ.

### Options
1. Thêm tất cả feed mong muốn: nhiều feed 403 vô dụng.
2. Chỉ feed verify + bù qua PubMed cho nguồn bị chặn: ổn định — đã chọn.

### Adoption Reason
Độ tin cậy của pipeline; tránh nhiễu lỗi.

### Impact
`app/sources/feeds.py`, `app/config.py`. Lưu ý: dùng cụm văn bản thường, KHÔNG dùng `[Corporate Author]` (cú pháp riêng PubMed gây nhiễu EuropePMC/Crossref/OpenAlex vì dùng chung query string).

### Review Conditions
Khi muốn thêm feed mới — phải verify live HTTP 200+XML trước; xem `patterns.md` P5 cho các pattern URL RSS đã chạy.

---

## D6: Quét nguồn chạy song song (đa luồng) thay vì tuần tự

**Date**: 2026-06-06
**Tags**: #decision #performance #ingestion
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
`app/services/ingestion.py` chạy song song: mỗi nguồn API 1 luồng (bên trong tuần tự để giữ rate limit NCBI), feed song song 4 luồng (`_FEED_WORKERS=4`). Source Log gom ghi DB 1 lần ở cuối để tránh khóa SQLite.

### Background
Quét tuần tự tổng ~238s. Người dùng chạy live là chính nên tốc độ quan trọng.

### Options
1. Tuần tự: đơn giản nhưng chậm (~238s).
2. Song song theo nguồn + 4 luồng feed: ~55–60s (~4x) — đã chọn.

### Adoption Reason
Tăng tốc ~4x mà vẫn tôn trọng rate limit (NCBI nội bộ tuần tự; feed 4 luồng tránh 429 do BMJ dùng chung host).

### Impact
`app/services/ingestion.py`. Để nhanh hơn: NCBI_API_KEY (3→10 req/s); chưa gộp OR theo area (rủi ro giảm chất lượng).

### Review Conditions
Khi đổi nguồn hoặc gặp 429 — chỉnh số luồng, giữ NCBI tuần tự.

---

## D7: Incremental "mới tuần này" qua watermark, idempotent

**Date**: 2026-06-06
**Tags**: #decision #pipeline #incremental #idempotent
**Observation ID**: memory/project-medical-ebm-automation.md

### Conclusion
Pipeline incremental mặc định (`incremental=True`): bảng `pipeline_runs` (watermark) + cột `first_seen_run_id`/`last_run_id` trên evidence_items. `run_state.py` tính `since_date` = mốc lần trước − 2 ngày đệm (lần đầu lùi 30 ngày). Bản ghi lần đầu vào kho = "mới". Chạy lại không tạo "mới" (idempotent).

### Background
Cần bản tin "mới tuần này" mà không quét lại toàn bộ và không tạo trùng.

### Options
1. Quét full mỗi lần + diff: tốn kém, dễ trùng.
2. Watermark + cột run id + upsert theo `(source+định danh)`: nhẹ, idempotent — đã chọn.

### Adoption Reason
Hiệu quả, ổn định, không bịa "mới" giả.

### Impact
`init_db` (`_ensure_columns` — ADD COLUMN không mất data), `app/services/run_state.py`, `app/reports/alert_digest.py`. Mỗi connector nhận `since_date` lọc ngày API thật. Khóa bằng test idempotent.

### Review Conditions
Khi đổi schema evidence_items — giữ migration nhẹ qua `_ensure_columns`.

---

## D8: Cảnh báo cơ quan quản lý (regulatory_alert) KHÔNG tự lên Tier A

**Date**: 2026-06-07
**Tags**: #decision #scoring #safety #phase4
**Observation ID**: phase4-group-C

### Conclusion
`regulatory_alert`: hạ EQ nền 80→60 và BỎ khỏi nhóm `strong_source` đủ điều kiện Tier A (`app/scoring/reliability.py`). Hệ quả: 1 tin FDA/feed 1 dòng tối đa **Tier B / need_full_text**, không tự vào "actionable".

### Background
Audit phát hiện 1 tin feed 1 dòng chứa "should" ⇒ EQ80/PC60 ⇒ Tier A actionable — rủi ro over-action khi chưa ai đọc nguyên văn.

### Adoption Reason
An toàn lâm sàng: cảnh báo quản lý cần đọc toàn văn trước khi đổi thực hành.

### Impact
`evidence_quality.py`, `reliability.py`; khóa bằng `tests/test_group_c_scoring.py`. Đã re-score dữ liệu cũ (`scripts/rescore.py`): actionable 56→49.

### Review Conditions
Nếu cần phân biệt cảnh báo "nặng" (black box/thu hồi) thì thêm tín hiệu cụ thể thay vì chỉ keyword.

---

## D9: Truy vết mock (cột is_mock) — không để dữ liệu demo lẫn khuyến cáo thật

**Date**: 2026-06-07
**Tags**: #decision #integrity #data-model #phase4
**Observation ID**: phase4-group-B

### Conclusion
Thêm cột `EvidenceItem.is_mock` (migration nhẹ), map từ `raw["_mock"]` trong `normalize()`. Báo cáo tuần LOẠI mock khỏi actionable khi chạy LIVE (demo mode giữ + banner DEMO). Dashboard có banner cảnh báo demo/lẫn-mock.

### Background
Mock và live nằm chung bảng; chạy mock (mặc định) rồi live có thể để bản ghi minh họa hiện như khuyến cáo thật.

### Adoption Reason
Liêm chính dữ liệu [[D1]]: phải truy vết được nguồn demo ở cấp bản ghi.

### Impact
`models/evidence.py`, `database.py` (`_ensure_columns`), `normalization.py`, `reports/weekly_ebm.py` (`exclude_mock`), `dashboard/main.py`. Khóa bằng `tests/test_group_b_mock_tracking.py`.

### Review Conditions
Nếu tách hẳn DB demo/live thì cột này thành dư.

---

## D10: HOÃN tách dashboard monolith (main.py 994 dòng)

**Date**: 2026-06-07
**Tags**: #decision #refactor #risk #phase4
**Observation ID**: phase4-group-D

### Conclusion
KHÔNG tách toàn bộ `app/dashboard/main.py` trong một lần. Chỉ tách phần logic giá trị cao (vd `is_antibiotic_text` → `services/filtering.py`) kèm test; phần còn lại tách DẦN, mỗi lần 1 tab + test.

### Background
App đang chạy phục vụ lâm sàng, chưa có test cho dashboard ⇒ rewrite lớn rủi ro vỡ thầm lặng.

### Adoption Reason
Lợi ích cận biên thấp so với rủi ro làm hỏng app đang dùng.

### Review Conditions
Khi đã có đủ test smoke cho dashboard thì mới tách sâu hơn.

---

## D11: An toàn nguồn ngoài — defusedxml + rate-limit NCBI + xác nhận gửi email

**Date**: 2026-06-07
**Tags**: #decision #security #phase4
**Observation ID**: phase4-group-A

### Conclusion
Parse XML ngoài (PubMed/RSS) qua `defusedxml` (chống XXE/billion-laughs). `HttpClient` giãn cách tối thiểu theo host (`HTTP_MIN_INTERVAL`, mặc định 0.34s ≈ etiquette NCBI). Lệnh gửi email thật (`notify-test`) yêu cầu xác nhận `[y/N]`; bỏ email hardcode → `settings.alert_email_to`. Export CSV/Excel chống formula injection (`_safe_cell`).

### Adoption Reason
Giảm rủi ro DoS/bị chặn IP/gửi nhầm/chạy công thức độc khi mở file.

### Impact
`sources/pubmed.py`, `sources/rss_feed.py`, `utils/http.py`, `config.py`, `run.py`, `reports/exporters.py`. Khóa bằng `tests/test_group_a_safety.py`.
