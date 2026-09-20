---
_harness_template: "CLAUDE.md.template"
_harness_version: "4.3.3"
---

# CLAUDE.md - Claude Code Instructions

> **Project**: medical-ebm-automation
> **Created**: 2026-06-07
> **Setup locale**: vi

---

## Read This First

Read `AGENTS.md` before starting work (development flow, role boundaries, prohibited actions).
This file contains only Claude Code-specific instructions.

---

## 0. Project Context

- **Workspace mặc định dùng chung**: mở Claude Code tại `C:\Users\Admin\OneDrive\Claude AI` rồi vào `medical-ebm-automation/`; trên Mac mở thư mục OneDrive tương ứng chứa `Claude AI`.
- **Stack**: Python / Streamlit — pipeline EBM + research tracker + dashboard 12 tab, Evidence Workbench, EBM_MASTER hub, evidence RAG.
- **Run app**: `python run.py` (or "Mở Dashboard.command").
- **Tests**: `python -m compileall -q app scripts tests`; chạy thêm `pytest` và `ruff check` khi venv đã có dev dependencies.
- **Agent source of truth**: sửa `.claude/agents/*.md` ở thư mục gốc OneDrive; không sửa tay `.Codex/agents/*.toml` hoặc `.codex/agents/*.toml`. Sau khi sửa/thêm agent, chạy sync ở thư mục gốc.
- **Plugin ownership**: owner/worker canonical nằm ở `../.claude/agents/_PLUGIN-ROUTING-CONTRACT.md`
  và `../tools/orchestrator/plugin_ownership_registry.json`. Repo này cung cấp runtime nghiên cứu
  sản xuất; ARS/Anthropic/BMAD/Bio không được thay `run_pipeline.py`, tự ghi approval ledger hoặc
  mở G2/G4/G5/G8/G9/G10. Kiểm từ workspace gốc bằng
  `python ../tools/verify_plugin_orchestration.py`.
- **Research assurance**: sáu cổng canonical là G2/G4/G5/G8/G9/G10. G2 phải chặn khi WHO TRDS v1.3.1 mục 13/14/19/20 thiếu dữ kiện PI đã pin hoặc tham chiếu Hội đồng chỉ là fallback; G9 phải chặn khi thiếu quyền truy cập dữ liệu/độc lập nhà tài trợ theo ICMJE 1/2026. Chạy `python ../tools/verify_controlled_research_automation.py`; Claude Code không tự điền các xác nhận đời thực.
- **Evidence surveillance deployment**: `weekly_safety.sh`/`monthly_update.sh` là owner thu thập duy nhất. `PARTIAL/FAIL` phải giữ watermark, chặn `bridge_to_ebm_master.py` và không gửi cảnh báo nội dung. Chạy `python tools/verify_evidence_surveillance_deployment.py --online`; chỉ `READY_FOR_CONTROLLED_DEPLOYMENT` mới cho phép candidate-only. Claude Code không tự điền UAT, alert/rollback/shadow evidence hoặc phê duyệt để làm xanh cổng.
- **⚠️ Sau khi đồng bộ agent .md đã sửa vào `medical-ebm-automation/.claude/agents/` (bản in-repo dùng bởi `runtime/agent_registry.py` FULL_SCOPE_A):** BẮT BUỘC chạy `python3 scripts/regenerate_agent_manifest.py --write` rồi dán giá trị self-check SHA-256 in ra vào hằng số `MANIFEST_SELF_CHECK_SHA256` trong `runtime/agent_registry.py` — **kể cả khi số lượng agent KHÔNG đổi**, vì manifest khóa hash theo NỘI DUNG từng file, không chỉ số lượng. Quên bước này → hàng chục test `test_v4_*`/`test_offline_workflow_integration.py` fail với "agent hash mismatch" (đã xảy ra ≥2 lần, 2026-07-05). Chạy `pytest` sau mỗi lần sync để bắt sớm nếu quên.
- **Secrets**: live in `.env` outside OneDrive, symlinked into the repo if needed. Never commit or print them.
- **Nguồn dữ liệu** (`app/sources/`): PubMed/Europe PMC/Crossref/OpenAlex/ClinicalTrials/openFDA
  (miễn phí, không key, bật mặc định; **openFDA có khoá TUỲ CHỌN `OPENFDA_API_KEY` — thêm 19/09/2026**: không khoá 240 lượt/phút + 1.000 lượt/ngày theo IP, có khoá 120.000 lượt/ngày theo khoá; nối qua MỘT hàm dùng chung `app.sources.openfda.get_json_openfda()` cho cả 3 nơi gọi api.fda.gov (FAERS · tra nhãn thuốc · live adapter). Khoá bị FDA từ chối (401/403) ⇒ cảnh báo rõ + tự lùi về không khoá — KHÔNG để `OpenFDAClient.search()` nuốt lỗi thành `[]` im lặng. Kiểm khoá có THẬT SỰ được chấp nhận: `python run.py test-live openfda` → trường `khoa_api_openfda`; giá trị khoá không bao giờ được in) · Semantic Scholar (bật mặc định, chạy được không key nhưng
  QPS thấp hơn) · Zotero/NICE (tắt mặc định) · **Scopus (Elsevier) — thêm 13/09/2026**
  (`app/sources/scopus.py`) — TẮT mặc định, đòi `SCOPUS_API_KEY` **bắt buộc thật** trong
  `~/.ebm-secrets/medical-ebm-automation.env` (khác Semantic Scholar, Scopus không chạy được nếu
  thiếu key — `search()` tự chặn sớm bằng lỗi rõ ràng thay vì 401 mù mờ). Bật bằng
  `ENABLE_SCOPUS=true`. **Giới hạn đã biết:** Search API không trả abstract đầy đủ (`abstract=None`
  hầu hết trường hợp) và chỉ trả tác giả đầu; KHÔNG tham gia chuỗi 3 tầng kiểm rút bài của
  `retraction_chain.py` (giống OpenAlex/Crossref/Semantic Scholar — chỉ PubMed/Europe PMC/
  Retraction Watch offline mới ở trong chuỗi đó). Test nhanh sau khi có key:
  `python run.py test-live scopus "<từ khoá>"`. 14 test ở `tests/test_scopus.py`.
  **ĐÃ XÁC NHẬN CHẠY THẬT 13/09/2026** (key `EBM-Scopus-Research`, `count=5`, DOI/PMID thật,
  `is_mock:false`). ⚠️ **Bẫy đã gặp:** bật VPN cá nhân làm MỌI request bị chặn ngay từ Cloudflare
  (HTML "Attention Required!", HTTP 403 — chặn TRƯỚC khi tới logic xác thực của Elsevier, xác nhận
  bằng cách đọc thẳng response body chứ không chỉ mã trạng thái) — không phải lỗi key/code, đổi
  User-Agent/header không giúp gì. **Tắt VPN thì chạy được ngay**, không cần Institutional Token.
  Nếu gặp lại 403 dạng HTML Cloudflare (không phải JSON lỗi của Elsevier): việc đầu tiên cần hỏi là
  "có đang bật VPN không", trước khi nghi ngờ key hay IP tổ chức.
  ✅ **KHÔNG CÒN PHẢI CHỌN GIỮA VPN VÀ SCOPUS — thêm 17/09/2026.** Đo trực tiếp (bật/tắt/kiểm
  chứng lại VPN Kaspersky, có đối chứng) xác nhận thêm: **NCBI/PubMed chạy TỐT qua VPN**, chỉ riêng
  Scopus bị Cloudflare chặn theo IP thoát VPN — nghĩa là "tắt VPN" không phải lựa chọn DUY NHẤT, chỉ
  là lựa chọn ĐƠN GIẢN NHẤT lúc đó. `SCOPUS_BIND_INTERFACE` (env, macOS-only — xem `.env.example`)
  ép RIÊNG `ScopusClient` thoát qua một card mạng vật lý cụ thể (vd `en1`) bằng socket option
  `IP_BOUND_IF` (giá trị 25, xác minh trực tiếp từ `$(xcrun --show-sdk-path)/usr/include/netinet/
  in.h` — Python không định nghĩa hằng số này, đúng cơ chế `curl --interface` dùng trên macOS để
  bỏ qua bảng định tuyến của VPN mà không cần tắt VPN), bất kể route mặc định của hệ điều hành đang
  trỏ đi đâu. Cài đặt: `app/utils/http.py::HttpClient(bind_interface=...)` +
  `app/utils/http.py::_InterfaceBoundHTTPAdapter`, đọc từ `settings.scopus_bind_interface`
  (`app/config.py`). Rỗng (mặc định) = không đổi hành vi cũ; đặt sai tên card hoặc dùng trên
  Windows sẽ nổ `RuntimeError` rõ ràng ngay lúc khởi tạo, không âm thầm bỏ qua. 7 test hồi quy ở
  `tests/test_http_bind_interface_vpn_bypass_20260917.py` (mutation-tested 2 phép: tắt rào kiểm
  nền tảng · sai hằng số `IP_BOUND_IF` — cả hai đỏ đúng chỗ) + 2 test ở `tests/test_scopus.py`
  kiểm `ScopusClient` truyền đúng cấu hình.
  ⚠️ **Giới hạn trung thực, chưa đóng lúc viết:** bộ test trên chỉ xác nhận adapter được MOUNT ĐÚNG
  với `socket_options` đúng giá trị — **CHƯA xác minh bằng mạng thật** rằng gói tin thực sự thoát
  qua card đó khi VPN đang bật (lúc vá, VPN Kaspersky trên máy đang thử nghiệm không kết nối lại
  được — lỗi nội bộ phía Kaspersky, không liên quan đoạn mã này). Xác minh trước khi tin tưởng
  100%: bật VPN, thêm `SCOPUS_BIND_INTERFACE=<tên card vật lý>` vào
  `~/.ebm-secrets/medical-ebm-automation.env`, chạy `python run.py test-live scopus` — kỳ vọng
  `is_mock:false` và không còn 403, trong khi `python run.py test-live pubmed` (không cần đổi gì)
  vẫn chạy tốt qua VPN như trước.
  · **CORE API (core.ac.uk) — thêm 16/09/2026**, theo yêu cầu "nâng cấp trạng thái tự động" và
  khảo sát toàn hệ xác định đây là nguồn OA bổ sung cho Unpaywall (>452 triệu bản ghi, >16.000 kho
  lưu trữ, gồm cả luận văn/báo cáo xám mà Unpaywall không phủ). `app/sources/core_api.py`. TẮT mặc
  định (`ENABLE_CORE=true` để bật). **KHÁC Scopus: `CORE_API_KEY` KHÔNG bắt buộc** — trang chính
  thức `core.ac.uk/services/api` tự khai "free API access without registration" (nhịp thấp hơn:
  1 batch hoặc 5 request đơn/10 giây); có key chỉ tăng nhịp, `search()` không chặn cứng khi thiếu,
  chỉ cảnh báo. **Đăng ký key: chỉ nhập EMAIL, bấm "REGISTER NOW" trên trang trên — KHÔNG tài
  khoản/mật khẩu, KHÔNG chờ duyệt, key gửi thẳng qua email** (khác hẳn Epistemonikos/NICE, vốn cần
  đơn xin và chờ duyệt) — đã xác minh trực tiếp bằng Browser thật 16/09/2026 (Cloudflare chặn
  urllib/WebFetch headless, cùng lớp chặn đã gặp với ACC/AHA). Endpoint
  `GET https://api.core.ac.uk/v3/search/works`, xác thực `Authorization: Bearer <key>` (header,
  không lộ vào query string/log như NCBI). **Giới hạn CHƯA xác minh được (không có key thật để thử
  lúc viết):** tài liệu Redoc chính thức tự mâu thuẫn giữa camelCase (`yearPublished`, `fullText` —
  dùng trong cú pháp truy vấn) và snake_case (`published_date`, `document_type` — mẫu response của
  endpoint lấy 1 bản ghi `/v3/works/{id}`) — `core_api.py::_lay()` thử CẢ HAI dạng khoá nên không vỡ
  dù bên nào đúng, nhưng cần chạy `python run.py test-live core "<từ khoá>"` một lần sau khi có key
  thật để đối chiếu `raw`/log, xác nhận field nào các bản ghi TÌM KIẾM thật sự trả về. KHÔNG tham
  gia chuỗi 3 tầng kiểm rút bài (giống Scopus/OpenAlex/Crossref/Semantic Scholar). 15 test ở
  `tests/test_core_api.py`. **ĐÃ XÁC NHẬN CHẠY THẬT 16/09/2026** — `count=5`, DOI/PMID thật,
  `is_mock:false`; camelCase (`publishedDate`, `yearPublished`) là dạng THẬT SỰ dùng trong response
  (đã thấy trực tiếp trong `raw`), nhánh snake_case trong `_lay()` chỉ còn là dự phòng, chưa gỡ vì
  vô hại.
  · **Epistemonikos API — thêm 16/09/2026**, cùng đợt với CORE. `app/sources/epistemonikos.py`.
  TẮT mặc định. **KHÁC CORE: `EPISTEMONIKOS_API_TOKEN` BẮT BUỘC thật** (chặn cứng như Scopus) —
  và **KHÔNG tự đăng ký được**: tài liệu chính thức (`api.epistemonikos.org`, đọc trực tiếp — trang
  CHÍNH `epistemonikos.org` bị CloudFront 403 chặn từ mạng này, phải đọc qua subdomain API) ghi
  nguyên văn *"If you want to register your application and try our API, please contact us [dev at
  epistemonikos.org]"* — bác sĩ phải tự gửi email xin cấp token, KHÔNG có luồng tự-cấp như CORE.
  Endpoint `GET https://api.epistemonikos.org/v1/documents/search`, xác thực
  `Authorization: Token token="<token>"` (KHÁC Bearer của CORE/Scopus). **Giới hạn đã biết:** search
  không trả DOI/PMID trần — chỉ có `external_links.publisher`/`.pubmed` dạng URL, connector cố trích
  DOI/PMID từ URL (không đảm bảo, nhiều "publisher" không phải link doi.org); endpoint không hỗ trợ
  lọc theo năm phía server, `since_date` lọc PHÍA CLIENT; chỉ lấy trang đầu (tối đa 10 bản ghi/lần),
  chưa phân trang. 16 test ở `tests/test_epistemonikos.py`, dựng từ ĐÚNG ví dụ response thật trích
  nguyên văn tài liệu (query "adjuvant treatment", total_hits=205) — không bịa cấu trúc. **CHƯA xác
  nhận chạy thật** (bác sĩ chưa có token lúc viết) — chạy
  `python run.py test-live epistemonikos "<từ khoá>"` sau khi có token để đối chiếu.
  · **SerpApi Google Scholar — thêm 20/09/2026**, theo yêu cầu "tích hợp Google Scholar API qua
  SerpApi để hoàn thiện hệ thống". `app/sources/serpapi_scholar.py` (`SerpApiScholarClient`).
  Google Scholar KHÔNG có API chính thức; SerpApi là dịch vụ thương mại bóc kết quả Scholar thành
  JSON: `GET https://serpapi.com/search.json` với `engine=google_scholar`, `q`, `num` ≤ 20,
  `as_ylo` = năm của `since_date`, `api_key` là query param (tài liệu SerpApi không ghi header xác
  thực). Đây là nguồn KHÁM PHÁ, không phải nguồn xác minh. ⚠️ **CẬP NHẬT cùng ngày 20/09/2026 — KHÔNG
  còn nằm trong `get_enabled_sources()`**: bác sĩ yêu cầu chỉ dùng khi các nguồn khác chưa đủ chứng
  cứ đáng tin, nên nó là TẦNG DỰ PHÒNG số 2 của bậc thang có cổng (xem đoạn "Bậc thang dự phòng có
  cổng" ngay dưới); `get_fallback_sources()` mới dựng nó. Vẫn KHÔNG thuộc `_DISCOVERY_CORE` và KHÔNG có
  trong `authority.EVIDENCE_SOURCE_UNIVERSE`. TẮT mặc định
  (`ENABLE_SERPAPI_SCHOLAR=true` để bật). **`SERPAPI_API_KEY` BẮT BUỘC thật** trong
  `~/.ebm-secrets/medical-ebm-automation.env` — `search()` tự chặn sớm bằng `SerpApiLoi` (loại
  `thieu_key`, là `RuntimeError`), KHÔNG đặt trong `__init__` vì `get_enabled_sources()` dựng
  client ngoài `try`. **MỖI request là MỘT search SerpApi TÍNH PHÍ** (kết quả rỗng vẫn tính 1;
  lỗi/thất bại/trúng cache của SerpApi thì không tính): gói Free 250 search/tháng và 50 search/giờ —
  số đo từ trang giá `serpapi.com/pricing` đọc 20/09/2026 (qua công cụ tóm tắt, đối chiếu chéo với
  nguồn thứ ba, KHÔNG phải HTML thô); **CHƯA xác nhận từ nguồn chính** rằng Google Scholar nằm trong
  gói Free. Vì vậy có NGÂN SÁCH `SERPAPI_MAX_CALLS_PER_RUN` (mặc định **8**, `app/config.py`):
  bộ đếm theo TIẾN TRÌNH dùng chung mọi instance (ingestion, `research/manager.py`,
  `research/dossier.py` đều tạo instance riêng), tự về 0 khi sang NGÀY mới, `<= 0` = khoá hẳn. Tính:
  8 x ~22 ngày chạy/tháng = 176 search, chừa ~30% cho chạy tay. Chạm trần → NỔ TO (`SerpApiLoi` loại
  `het_ngan_sach`, không gửi thêm request), không trả rỗng im lặng; lượt trúng cache 24 giờ của
  `HttpClient` được hoàn lại ngân sách. **Đúng MỘT request HTTP cho mỗi `search()` trên MỌI đường**
  (thành công, 401/429/5xx, timeout, mất mạng, JSON hỏng — sửa 20/09/2026 sau khi đo thấy 429/5xx gửi 2
  request và timeout/mất mạng/JSON hỏng gửi 5, trong khi ngân sách chỉ đếm 1): connector dựng
  `HttpClient(max_retries=0)` — tham số MỚI `max_retries` theo TỪNG client ở `app/utils/http.py`
  (`None` = mặc định, dùng `settings.http_max_retries`, hành vi mọi nguồn khác KHÔNG đổi; `0` = không
  retry, không ngủ backoff vô ích). Key sai (401) và hết quota (429 "run out of searches") là lỗi
  CHỐT: dừng nguồn cho phần còn lại của lượt chạy. **Giới hạn đã biết:** (1) KHÔNG abstract —
  `snippet` của Scholar chỉ là đoạn trích ngắn, giữ ở `raw["snippet"]`, `abstract=None`; (2) KHÔNG
  DOI/PMID chắc chắn — chỉ trích khi `link` thật là doi.org / PubMed / PMC / Europe PMC hoặc URL nhà
  xuất bản chứa nguyên văn `/doi/10.xxxx/…`, còn lại `None` (không tra ngược từ tiêu đề) →
  **mọi bản ghi Scholar phải được phân giải qua PubMed/Crossref TRƯỚC khi dùng lâm sàng**;
  (3) ngày chỉ có NĂM (`publication_date="YYYY"` hoặc `None` + cờ `year_unknown`, không bịa
  tháng/ngày; `as_ylo` lọc phía server nên mỗi lượt vẫn trả kết quả chồng lấp); (4) `study_type` LUÔN
  `None` trừ tín hiệu preprint — đã chứng minh offline rằng suy từ tiêu đề đẩy bản ghi title-only lên
  tier A/actionable rồi vào cảnh báo email và EBM_MASTER; (5) KHÔNG tham gia chuỗi 3 tầng kiểm rút bài
  (`retraction_chain.py`) — bản ghi Scholar luôn "chưa kiểm rút bài", giống Scopus/OpenAlex/Crossref/
  Semantic Scholar; (6) tiêu đề Scholar hay bị cắt bằng "…" nên dedup KHÔNG gộp được với bản PubMed
  (cờ `title_truncated`); (7) truy vấn đi qua SerpApi tới Google và SerpApi lưu 31 ngày → connector
  TỪ CHỐI truy vấn có dấu hiệu PII/PHI (`contains_pii_text`), và BỎ QUA truy vấn mang thẻ PubMed
  (`[ta]`/`[pt]`/`[cn]`… — 8/53 truy vấn trong `CLINICAL_AREAS`, không gọi HTTP, Source Log hiện ok/0,
  số thật ở `client.stats`). `api_key` chỉ đi qua `params` nên `HttpClient._redact` che ở log/
  exception; payload trước `save_raw` và cache GET trên đĩa đều bị lược khoá. **Bật (đúng thứ tự):**
  (a) bác sĩ TỰ tạo tài khoản và lấy key trên serpapi.com; (b) thêm `SERPAPI_API_KEY=<key>` và
  `ENABLE_SERPAPI_SCHOLAR=true` vào `~/.ebm-secrets/medical-ebm-automation.env` (giữ
  `USE_MOCK_SOURCES=false` nếu muốn `ingest` chạy thật; chỉnh `SERPAPI_MAX_CALLS_PER_RUN` nếu cần) —
  không ghi key vào repo; (c) chạy MỘT lần `python run.py test-live serpapi_scholar "<từ khoá>"`
  (`test-live` tự ép chế độ thật, tốn đúng 1 search) rồi kiểm `is_mock:false`, `count`, `year`,
  `doi`/`pmid` (đa số sẽ `None`), `study_type:null`. **181 test offline** ở
  `tests/test_serpapi_scholar.py` (không gọi mạng, không cần key; dựng từ tài liệu SerpApi + mẫu tự
  dựng, không có phản hồi thật nào; gồm nhóm đếm số request thật qua `HttpClient` với session giả) +
  **21 test** ở `tests/test_http_per_client_max_retries.py` cho tham số `max_retries` của `HttpClient`. ✅ **ĐÃ XÁC NHẬN CHẠY THẬT 20/09/2026** (1 search tính phí, `run.py test-live serpapi_scholar`): khoá hợp lệ ⇒ `count=5`, `is_mock:false`, `year` 2019–2026, `pmid:null`, `study_type:null`, `tier C`, `watch_only`; trong 4 bản ghi đầu chỉ 1 có DOI (đúng dự đoán "đa số `None`"). ⚠️ **Bẫy đã gặp thật:** khoá bị DÁN ĐÔI (128 ký tự = 2 × 64 hex giống hệt nhau) ⇒ HTTP 401 "Invalid API key" (lỗi không tính phí) — nút `Nhap Khoa SerpApi.command` trước đó chỉ cảnh báo "dài 128, thường 64" rồi vẫn ghi; nay tự nhận và gộp khoá dán đôi (cả khoá đang lưu lẫn khoá vừa dán). Còn CHƯA đối chiếu: ý nghĩa `as_ylo` "bao gồm năm đó" và việc phản hồi có lặp lại `api_key` hay không. **Việc còn mở (chưa làm, cần bác sĩ quyết):** (i) `summarize_source_health`
  (`app/services/ingestion.py`) — nguồn NGOÀI lõi hỏng 100% vẫn ra `PASS` (đã chứng minh offline;
  Scopus/CORE/Epistemonikos cũng chịu lỗ hổng này), đổi luật sẽ đổi hành vi phát hành nên chưa sửa;
  (ii) [ĐÃ LỖI THỜI từ khi có bậc thang có cổng — giờ chỉ truy vấn THIẾU chứng cứ mới gọi Scholar, không còn
  quét tuần tự 53 truy vấn]; (iii) [ĐÃ XONG 20/09/2026 — `.env.example` đã có đủ dòng mẫu cho bậc thang dự phòng]; (iv) `research/manager.py` và
  `research/dossier.py` nuốt mọi exception bằng `logger.warning` nên lỗi thiếu key/hết quota không
  lên giao diện; (v) [ĐÃ XONG 20/09/2026 — trần THÁNG bền `SERPAPI_MAX_CALLS_PER_MONTH` (mặc định 200/250), tệp `data/raw/_state/serpapi_usage.json`, fail-closed, dùng chung giữa các tiến trình; SerpApi báo hết quota thì đánh dấu hết cả tháng; số đã dùng chưa đối chiếu với Account API]; (vi) tầng giám sát lâm sàng
  (`EBM-Dashboards/tools/surveillance_scan.py`) chưa có "làn" Scholar. Tắt được bằng cờ và không
  phụ thuộc duy nhất vào nguồn này (Google đang kiện SerpApi — theo báo chí/blog SerpApi, chưa có
  thông tin sau ~01/09/2026).
  · **Bậc thang dự phòng có cổng (Consensus → SerpApi Scholar) + lớp xác minh Scite — thêm 20/09/2026**,
  theo yêu cầu "chỉ khi các nguồn khác chưa đủ chứng cứ đáng tin cậy mới xác minh và tìm thêm".
  Mã: `app/services/evidence_sufficiency.py` (cổng), `fallback_ladder.py` (bậc thang),
  `fallback_verification.py` (xác minh), `app/sources/consensus_api.py`, `app/sources/scite_public.py`.
  **Cổng đủ-chứng-cứ:** một truy vấn chỉ leo thang khi có < `FALLBACK_MIN_TRUSTED` (mặc định 3) bài
  ĐÁNG TIN phân biệt — đáng tin = không phải Consensus/Scholar, không mock, có PMID/DOI, tier ≠ D, điểm
  chứng cứ ≥ `FALLBACK_MIN_EVIDENCE` (60); đếm cả bài đã có trong kho. Nguồn lõi sập ⇒ trạng thái
  "không rõ", KHÔNG leo thang (tránh đốt hạn mức khi lỗi nằm ở phía ta). Chế độ mock ⇒ bậc thang tắt.
  Thứ tự thử = `FALLBACK_ORDER` (mặc định `consensus,serpapi_scholar`; tên lạ ⇒ `ValueError`); chỉ tầng
  có cờ bật mới chạy. **Consensus** (`ENABLE_CONSENSUS`, `CONSENSUS_API_KEY` bắt buộc, key đi header
  `x-api-key`): gói Free 30 lượt/tháng dùng CHUNG với MCP nên có trần riêng — `CONSENSUS_MAX_CALLS_PER_MONTH`
  (mặc định **10**, bộ đếm bền ở `data/raw/_state/consensus_usage.json`) và `CONSENSUS_MAX_CALLS_PER_RUN`
  (mặc định **5**), cách nhau ≥ 1,1 giây, hết trần ⇒ nổ to chứ không trả rỗng. Consensus chỉ trả
  `takeaway` (KHÔNG phải abstract) và nhãn `study_type` của nó chỉ là gợi ý, chỉ được HẠ bậc. **Xác minh
  (bắt buộc, nghiêm ngặt):** mọi bản ghi do tầng dự phòng tìm ra phải khớp một bản ghi THẬT trong Crossref
  (DOI/tiêu đề) hoặc PubMed (PMID) — tiêu đề giống ≥ 0,9 VÀ cùng token phân biệt (số phần/giai đoạn,
  nhóm dân số), năm lệch ≤ 1, khớp họ tác giả đầu; bản ghi giữ lại là bản của registry, không phải bản
  của Consensus/Scholar. Không xác minh được ⇒ bỏ và đếm (`FALLBACK_KEEP_UNVERIFIED=true` để giữ kèm cờ
  `chua_xac_minh`). **Scite** (`ENABLE_SCITE_VERIFICATION`, mặc định bật, KHÔNG cần khoá): chỉ là lớp xác minh
  qua endpoint công khai `papers`/`tallies` — chặn bài bị rút/có thông báo biên tập (`bi_rut_bai`), tally chỉ
  GHI vào `raw`, không tham gia chấm điểm; KHÔNG phải tầng tìm kiếm vì Scite Search cần giấy phép.
  ⚠️ **TRẠNG THÁI TRUNG THỰC (cập nhật 20/09/2026):** 98 + 230 + 156 + 86 + 67 test offline đạt, và ĐÃ kiểm THẬT một phần: (a) **SerpApi** — xem đoạn trên; (b) **lớp xác minh Crossref + Scite công khai** — 5 ca có đáp án biết trước, 4/5 đúng: DOI + tiêu đề đúng ⇒ giữ, kèm tally Scite thật (DAPA-HF: 5953 trích dẫn, 169 ủng hộ, 9 mâu thuẫn — chỉ GHI, không chấm điểm) · DOI thật nhưng tiêu đề sai ⇒ loại · DOI không tồn tại ⇒ loại · bài Wakefield (Lancet 1998, Crossref ghi tiêu đề "RETRACTED: …") ⇒ `bi_rut_bai` — **lỗi đo được và vá cùng ngày**: trước đó bị xếp "không khớp" (vẫn loại nhưng sai nhãn, không được đếm là rút bài); ca thứ 5 (tiêu đề bị Scholar cắt "…", không DOI) KHÔNG được giữ vì Crossref tìm theo tiêu đề trả về một bản 2022 KHÁC bài và cổng năm chặn đúng — đây là bằng chứng thật rằng bỏ cổng năm sẽ nhận nhầm bài; (c) **đường PMID/PubMed** vẫn không kiểm được trên mạng này vì NCBI đang chặn misuse ⇒ trả `loi_xac_minh` (fail-closed); (d) **Consensus CHƯA kiểm thật** — chưa có `CONSENSUS_API_KEY` (kết nối MCP Consensus KHÔNG phải khoá REST API — phải tạo khoá riêng ở "API & MCP Dashboard"). Cả hai nguồn dự phòng vẫn TẮT mặc định. Kiểm thật Consensus tốn 1 trong 30 lượt Free/tháng. **Việc còn mở:**
  (i) [đã xong: `.env.example` có đủ dòng mẫu]; (ii) [ĐÃ XONG 20/09/2026 — bác sĩ chốt «MCP vẫn đi qua cổng»: Consensus/Scite ở phía MCP của tác nhân đi qua CÙNG cổng, khai ở `.claude/agents/_CONNECTOR-CHUNG-CU.md` §2ter (chỉ leo thang khi các tầng trước chưa đủ chứng cứ đáng tin; nguồn lõi lỗi ⇒ PARTIAL chứ không leo thang; tối đa 2 lời gọi MCP/câu hỏi vì hạn mức Free 30 lượt/tháng dùng CHUNG với REST; kết quả Consensus phải xác minh Crossref/PubMed; Scite chỉ XÁC MINH, bổ sung cho chuỗi rút bài 3 tầng), khoá bằng chốt BH104 ở repo gốc. Giới hạn trung thực: đây là luật văn bản cho agent, KHÔNG phải cổng máy — không đếm được lời gọi MCP của một phiên cụ thể].
  · **Feed tạp chí/guideline: chế độ Crossref theo ISSN — thêm 20/09/2026**, theo yêu cầu «phủ chứng cứ» sau đánh giá hệ.
  Đo 29 feed RSS: chỉ 15 trả mục thật; 14 feed trả 0 mục kể cả bằng CHÍNH client của hệ (giãn nhịp, UA/Accept chuẩn) — họ BMJ
  HTTP 429/timeout ~30 giây, 3 feed Springer HTTP 406, `bmj_recent` HTTP 403; nhật ký 14 ngày cũng lỗi/ok chập chờn. Đổi UA/nhịp
  không cứu được. `FeedConfig` nay có `issn` + `mode` ("rss" mặc định | "crossref"); `RSSFeedClient._search_crossref()` lấy bài MỚI
  NHẤT của tạp chí qua `api.crossref.org/works` (`filter=issn:…,from-pub-date:…`, không khoá, `mailto` polite pool; mặc định cửa sổ
  45 ngày). 14 feed lỗi được chuyển sang Crossref (ISSN đối chiếu từng cái bằng `api.crossref.org/journals/{issn}`; BMJ dùng
  ISSN điện tử 1756-1833, Cochrane 1465-1858 vì ISSN in không cho bài mới) và THÊM 17 tạp chí nơi hiệp hội đăng guideline
  (Circulation/AHA, Eur Heart J/ESC, Diabetes Care/ADA, CID/IDSA, Hepatology/AASLD, Gastroenterology/AGA, AJG/ACG, Kidney Int/KDIGO,
  AJRCCM/ATS, ERJ/ERS, JAGS/AGS, Ann Intern Med/ACP, Lancet, Cochrane, JCO/ASCO, Ann Oncol/ESMO, Blood Adv/ASH) — độc lập với NCBI
  và với RSS của nhà xuất bản. Đo thật: **31/31 feed Crossref trả bài thật** (DOI + ngày; SourceLog `ok`). Ngày tương lai của số
  phát hành (2026-10 cho bài đăng tháng 9) thay bằng ngày Crossref nhận bản ghi, không bịa ngày. **Giới hạn nói thẳng:** đây là
  lane KHÁM PHÁ theo TIÊU ĐỀ (guideline nhận qua `infer_study_type`), KHÔNG phải nguồn «đã duyệt»; không có abstract đầy đủ; NICE,
  USPSTF, WHO, GOLD, GINA… vẫn KHÔNG có connector trực tiếp (NICE API chỉ cấp cho tổ chức, có phí quốc tế — xem
  `docs/xin-cap-quyen-nguon-chung-cu.md`). 25 test ở `tests/test_rss_feed_crossref_mode.py` (mutation-tested 2 phép). CORE chạy được
  KHÔNG khoá (test-live 20/09/2026: 3 kết quả thật) — chỉ còn cờ `ENABLE_CORE`; Epistemonikos cần token (thư nháp ở docs).
  · **DynaMed/DynaMedex (EBSCO) — thêm 13/09/2026, GỠ BỎ cùng ngày sau khi xác minh.**
  Kiểm trực tiếp `developer.ebsco.com/dynamed` xác nhận: đăng ký app MedsAPI **bắt buộc** một
  Customer ID + Group ID mà tài liệu EBSCO nói rõ "received from your EBSCO representative" —
  hai ID này được quản trị qua EBSCOadmin (bảng điều khiển của TỔ CHỨC/thư viện), không có luồng
  tự-cấp cho tài khoản cá nhân, và gói DynaMedex cá nhân ($599/năm) không hề liệt kê API/integration
  trong danh mục tính năng. Vậy tài khoản DynaMed cá nhân của bác sĩ **không thể tự tạo được** thông
  tin cần để đăng ký app — không phải lỗi cấu hình, là giới hạn của loại tài khoản. Đã gỡ toàn bộ:
  `app/sources/dynamed.py`, `tests/test_dynamed.py`, các khóa `DYNAMED_*`/`ENABLE_DYNAMED` ở
  `app/config.py`/`.env.example`, mục "dynamed" ở `_SOURCE_MAP` (`app/main.py`) và
  `app/sources/__init__.py`, cùng `search_dynamed_lane()` ở tầng giám sát lâm sàng
  (`EBM-Dashboards/tools/surveillance_scan.py` và hai bản mirror `sync/skills/*/tools/
  surveillance_scan.py`) — **giữ nguyên** `search_scopus_lane()`/Scopus, không liên quan tới lý do
  gỡ DynaMed. Muốn nối lại sau này: cần xác nhận với EBSCO/đại diện bán hàng để được cấp Customer
  ID + Group ID theo một hợp đồng tổ chức, không phải việc tự làm được từ tài khoản cá nhân.

---

## 0.1 Current Active Subproject: Chronic Care Clinic OS

- **Folder**: `chronic-care-clinic-os`
- **Stack**: Next.js / TypeScript / Prisma schema / deterministic demo data.
- **Purpose**: chronic disease care coordination, not a legal EMR replacement and not production-ready.
- **Read before work**: `chronic-care-clinic-os/IMPLEMENTATION_STATUS.md` and `chronic-care-clinic-os/docs/deployment/claude-code-handoff.md`.
- **Core check**:

```bash
cd chronic-care-clinic-os
pnpm test
pnpm typecheck:app
pnpm sync:check
```

- **If pnpm is unavailable**:

```bash
node --test tests/*.test.mjs
node node_modules/typescript/bin/tsc -p tsconfig.check.json --noEmit
node scripts/sync-check.mjs
```

- **Current completed modules**: care orchestration, program registry, pre-visit packets, care-plan drafts, care-plan approval guardrails and approved patient education handouts.
- **Required safety invariant**: no automatic diagnosis, no automatic prescribing, no automatic treatment-message sending, physician confirmation for clinical decisions, and consent plus approved template before patient communication.

## 1. Claude Code Scope

### Work You Own
- Implement scoped changes, write/adjust tests, fix CI.
- Commit scoped changes.

### Work You Must Not Do
- Do not work outside the requested scope.
- Do not change security settings unless explicitly requested.
- Do not commit or read secrets in `.env`.

---

## 2. Commit Message Convention

```text
feat:     a new feature
fix:      a bug fix
docs:     documentation
refactor: code restructuring
test:     tests
chore:    maintenance
```

---

## 3. Session Routine

### At Session Start
```bash
git status -sb
cat Plans.md
head -50 AGENTS.md
python ../tools/audit_ebm_system.py
python ../tools/sync_agents_to_codex.py --check
```

### At Completion
```bash
python -m compileall -q app scripts tests
python ../tools/sync_agents_to_codex.py --check
python ../tools/check_claude_codex_sync_health.py
python ../tools/verify_claude_code_repo_alignment.py
python scripts/regenerate_agent_manifest.py --check
python tools/agent_gate_governance.py
python ../tools/audit_ebm_system.py
# If dev dependencies are installed:
pytest
ruff check
git add -A
git commit -m "feat: [change summary]"
```

If `pytest` or `ruff` is unavailable, report that explicitly and do not create a virtualenv inside OneDrive. Use `%USERPROFILE%\.ebm-venv` on Windows or `~/.ebm-venv` on macOS/Linux.

---

## 4. Available Harness Commands

| Command | Purpose |
|---------|---------|
| `/claude-code-harness:harness-plan` | Plan a sprint into `Plans.md` |
| `/claude-code-harness:harness-work` | Execute tasks and update status |
| `/claude-code-harness:harness-review` | Review changes |
| `/claude-code-harness:harness-sync` | Inspect status / propose next actions |

---

## 5. Troubleshooting

| Symptom | Action |
|---------|--------|
| Task not found | Check `Plans.md` |
| CI keeps failing | Try 3 fixes, then stop and report |
| Scope unclear | Ask before proceeding |

---

*Use this file together with `AGENTS.md`.*
