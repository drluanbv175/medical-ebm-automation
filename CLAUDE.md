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
- **Nguồn chứng cứ TRÊN PHIÊN CLOUD — đo thật 24/09/2026, đọc TRƯỚC khi kết luận «nguồn X hỏng»**
  (báo cáo đầy đủ: `audit/15-…` ở repo gốc). Môi trường Cloud «Default — **Trusted** network access»:
  proxy thoát mạng TỪ CHỐI (CONNECT 403, chính sách) MỌI host API y văn — NCBI, `www.ebi.ac.uk`,
  `api.crossref.org`, OpenAlex, ClinicalTrials.gov, openFDA, Semantic Scholar, CORE, WHO IRIS,
  `kcb.vn`, GOLD/GINA, RSS hội/tạp chí ⇒ `test-live` 0/8 nguồn miễn phí, feed/lane guideline 0/111.
  Container không có `~/.ebm-secrets` ⇒ `USE_MOCK_SOURCES=true`, không `NCBI_EMAIL` ⇒ PubMed trả
  MOCK kể cả `test-live` (nay `test-live` ghi `live:false` + `canh_bao`; lỗi mạng bị nuốt thành `[]`
  nay hiện ở `loi_goi_mang`). **Chạy THẬT được trên Cloud:** PMC toàn văn qua S3 (`*.amazonaws.com`
  thuộc Trusted — SRC-046 trả 200.000 ký tự PMC13555224) · nền Retraction Watch qua **gương GitLab
  chính thức của Crossref** (`python tools/tai_retraction_watch.py` tự lùi sang đó khi thiếu email/
  Crossref bị chặn — tải 72.606 dòng, 31.511 PMID; chuỗi rút bài bắt đúng Wakefield + Choi R&R) ·
  MỌI connector **MCP** (đi qua máy chủ Anthropic, không qua allowlist): PubMed, ClinicalTrials,
  Scite, Wiley, Amass… (bioRxiv MCP lỗi phía máy chủ 24/09). Python mặc định của container là 3.11
  mà `requirements.lock.txt` cần ≥3.12 (scipy 1.18.0) ⇒ tạo venv bằng `python3.12 -m venv`. Proxy
  403/407 nay bị `HttpClient` bỏ NGAY (trước: retry ≈48 s/lần gọi). Muốn engine chạy thật trên Cloud
  là việc CỦA BÁC SĨ ở cài đặt môi trường: Network access → Custom (giữ danh sách mặc định) + thêm
  host; biến môi trường `USE_MOCK_SOURCES=false`, `NCBI_EMAIL`; khoá API — connector hiện đòi THẤY
  khoá trong biến môi trường (tính năng «API credentials» giấu khoá chưa dùng được với connector).
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
  ⛔ **ĐÃ KIỂM BẰNG MẠNG THẬT 20/09/2026 — `SCOPUS_BIND_INTERFACE` KHÔNG vượt được Kaspersky VPN, câu «kỳ vọng
  không còn 403» ở trên là SAI với VPN này.** Bật VPN + `SCOPUS_BIND_INTERFACE=en1`: `test-live scopus` vẫn HTTP 403 HTML Cloudflare
  (cả khi đi route mặc định lẫn khi ép card). Nguyên nhân đo được, không đoán: mở socket có `IP_BOUND_IF`=en1 rồi đọc
  `getsockname()` — địa chỉ nguồn vẫn là `172.21.39.127` (đường hầm VPN), KHÔNG phải `192.168.1.11` (IP của en1). Kaspersky VPN chặn
  gói tin ở tầng cao hơn tuỳ chọn socket này, nên cơ chế ép card không có tác dụng với nó (có thể vẫn hữu dụng với VPN khác — chưa thử).
  Cùng lượt đo, VPN BẬT: PubMed E-utilities HTTP 200 (hết chặn misuse, `test-live pubmed` count=5 thật), 33/33 lane guideline trả mục,
  SerpApi + Consensus test-live thật đều `is_mock:false`. **Hệ quả thực tế: VPN bật ⇒ PubMed trực tiếp chạy, Scopus bị chặn; VPN tắt ⇒
  ngược lại.** Việc bù: Europe PMC + Crossref phủ dữ liệu PubMed khi NCBI chặn, còn Scopus chỉ là nguồn bổ sung — nên chạy Scopus lúc
  VPN tắt. **Đã kiểm 20/09/2026 (tài liệu chính thức + nhìn trực tiếp ứng dụng): KHÔNG thể loại trừ riêng `api.elsevier.com`.**
  Kaspersky VPN cho Mac chỉ có «Phân tách kênh truyền tải» kiểu **ĐẢO CHIỀU so với Windows**: tick «Chỉ bật VPN cho các ứng dụng được chọn»
  ⇒ chỉ ứng dụng trong danh sách đi qua VPN, mọi ứng dụng khác đi thẳng — theo **ỨNG DỤNG**, không có ô nhập tên miền/địa chỉ IP; chỉ áp
  cho ứng dụng ngoài hệ thống nằm trong thư mục Applications và chỉ có ở bản Unlimited (support.kaspersky.com/us/ksec-for-mac/240287). Mà
  Scopus và PubMed cùng chạy trong MỘT tiến trình Python nên không tách được theo tên miền; các lựa chọn khả dĩ: (a) chạy Scopus lúc
  VPN tắt (đơn giản nhất); (b) tách hai tiến trình/ứng dụng riêng — chưa thử, và Python trong venv không nằm ở thư mục Applications nên
  chưa chắc chọn được. Tab này bị khoá khi VPN đang bật («Hãy tắt VPN để quản lý thiết lập Phân tách kênh truyền tải»); danh sách hiện
  trống (mọi ứng dụng đi qua VPN).
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
  ✅ **ĐÃ BẬT VỚI KHOÁ THẬT 22/09/2026 (máy Mac của bác sĩ).** Xác nhận 16/09 ở trên chạy ở chế độ
  KHÔNG khoá (nhịp thấp) — trên máy này `ENABLE_CORE` và `CORE_API_KEY` vẫn TẮT/rỗng cho tới hôm
  nay. Bác sĩ tự nhập khoá qua nút bấm đúp `Nhap Khoa CORE.command` (khoá KHÔNG đi qua khung chat,
  đúng quy ước "★ CHỈ BÁC SĨ TỰ BẤM" ghi ngay trong script) rồi bật bằng `Bat Tat SerpApi Du Phong.command`
  → gõ `bo`. Kiểm lại: `settings.enable_core=True`, có `core_api_key`; `run.py test-live core
  "heart failure guideline"` trả `live:true, count:5`, cả 5 bản ghi `is_mock:false` (3/5 có DOI thật,
  vd `10.1186/1472-6963-9-74`; 2/5 CORE không trả DOI — đúng giới hạn siêu dữ liệu đã ghi ở trên).
  CORE nay là nguồn PHỦ RỘNG đang chạy thật cùng lõi miễn phí + Scopus/SerpApi/Consensus.
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
  ⚠️ **TRẠNG THÁI TRUNG THỰC (cập nhật 20/09/2026):** 98 + 230 + 156 + 86 + 67 test offline đạt, và ĐÃ kiểm THẬT một phần: (a) **SerpApi** — xem đoạn trên; (b) **lớp xác minh Crossref + Scite công khai** — 5 ca có đáp án biết trước, 4/5 đúng: DOI + tiêu đề đúng ⇒ giữ, kèm tally Scite thật (DAPA-HF: 5953 trích dẫn, 169 ủng hộ, 9 mâu thuẫn — chỉ GHI, không chấm điểm) · DOI thật nhưng tiêu đề sai ⇒ loại · DOI không tồn tại ⇒ loại · bài Wakefield (Lancet 1998, Crossref ghi tiêu đề "RETRACTED: …") ⇒ `bi_rut_bai` — **lỗi đo được và vá cùng ngày**: trước đó bị xếp "không khớp" (vẫn loại nhưng sai nhãn, không được đếm là rút bài); ca thứ 5 (tiêu đề bị Scholar cắt "…", không DOI) KHÔNG được giữ vì Crossref tìm theo tiêu đề trả về một bản 2022 KHÁC bài và cổng năm chặn đúng — đây là bằng chứng thật rằng bỏ cổng năm sẽ nhận nhầm bài; (c) **đường PMID/PubMed** vẫn không kiểm được trên mạng này vì NCBI đang chặn misuse ⇒ trả `loi_xac_minh` (fail-closed); (d) **Consensus — ✅ ĐÃ KIỂM THẬT 20/09/2026** (1 lượt Free): `run.py test-live consensus` trả `live:true`, `count=5`, `is_mock:false`, DOI thật, `pmid:null` (đúng dự đoán: Consensus không trả PMID), `study_type:null`, tier C `watch_only`; khoá REST 35 ký tự (kết nối MCP Consensus KHÔNG phải khoá REST API — khoá riêng tạo ở "API & MCP Dashboard"). **Trạng thái BẬT (máy Mac của bác sĩ, 20/09/2026):** bác sĩ đã bật cả hai tầng dự phòng bằng nút `Bat Tat SerpApi Du Phong.command` (`ENABLE_CONSENSUS=true`, `ENABLE_SERPAPI_SCHOLAR=true` trong kho bí mật ngoài git — mặc định trong mã vẫn TẮT); `get_fallback_sources()` dựng đúng `['consensus','serpapi_scholar']`, hai tầng KHÔNG lẫn vào `get_enabled_sources()`. Đã kiểm cổng đủ-chứng-cứ bằng bài thật từ nguồn chính, không tốn hạn mức dự phòng: truy vấn phủ tốt («sacubitril valsartan heart failure guideline») → 20 bài đáng tin/ngưỡng 3 ⇒ `du` (cổng ĐÓNG); truy vấn vô nghĩa → 0/3 ⇒ `thieu` (cổng MỞ). Hạn mức còn lại sau các lần kiểm thật: SerpApi 197/200 tháng, Consensus 9/10 (trần hệ; gói Free là 30 lượt dùng chung với MCP). **Việc còn mở:**
  (i) [đã xong: `.env.example` có đủ dòng mẫu]; (ii) [ĐÃ XONG 20/09/2026 — bác sĩ chốt «MCP vẫn đi qua cổng»: Consensus/Scite ở phía MCP của tác nhân đi qua CÙNG cổng, khai ở `.claude/agents/_CONNECTOR-CHUNG-CU.md` §2ter (chỉ leo thang khi các tầng trước chưa đủ chứng cứ đáng tin; nguồn lõi lỗi ⇒ PARTIAL chứ không leo thang; tối đa 2 lời gọi MCP/câu hỏi vì hạn mức Free 30 lượt/tháng dùng CHUNG với REST; kết quả Consensus phải xác minh Crossref/PubMed; Scite chỉ XÁC MINH, bổ sung cho chuỗi rút bài 3 tầng), khoá bằng chốt BH107 ở repo gốc. Giới hạn trung thực: đây là luật văn bản cho agent, KHÔNG phải cổng máy — không đếm được lời gọi MCP của một phiên cụ thể]. **CẬP NHẬT 20/09/2026 (chiều) — bác sĩ yêu cầu «cập nhật Scite như một nguồn dự phòng» và «có kết nối Cochrane»:** (1) **Scite `search_literature` = tầng tìm dự phòng số 2 của phía MCP** (sau Consensus, VẪN qua cổng §2ter); đo thật 5 kết quả ≈ 65 KB nên doctrine đòi `limit ≤ 3`, tổng lời gọi tìm dự phòng ≤ 3 mỗi câu hỏi, chỉ `grep` doi/title/year khi kết quả bị lưu ra tệp; kết quả có DOI nhưng KHÔNG có PMID ⇒ phải phân giải Crossref/PubMed; vai xác minh (rút bài/tally) giữ nguyên. (2) **Cochrane MCP (`cochrane_search/get_details/suggest_terms`) = Cấp 0, KHÔNG qua cổng** (chính nguồn thẩm quyền); §2quater ghi các bẫy đo được: `date-desc` cho kết quả lạc đề, `typeCounts.central` ≠ số tổng quan, `review: 0` ≠ «không có chứng cứ», lỗi điều hướng thoáng qua phải thử lại một lần, `pico` có thể rỗng, không chép email tác giả. Cả hai chỉ ở tầng Agent — **engine Python không gọi được MCP** (engine phủ Cochrane bằng lane Crossref ISSN 1465-1858, còn Scite chỉ ở vai xác minh công khai `scite_public.py`); doctrine ở `.claude/agents/_CONNECTOR-CHUNG-CU.md`, khoá bằng BH107 (5 phép đột biến đều đỏ đúng chỗ). Giới hạn: vẫn là luật văn bản, không đếm được lời gọi MCP thật của một phiên.
  · **RxNorm + danh mục EMA — thêm 20/09/2026, chọn lọc từ `JamesANZ/medical-mcp`** (`app/sources/rxnorm.py`, `app/sources/ema_medicines.py`, CLI `tools/tra_thuoc_quoc_te.py`). Bác sĩ yêu cầu «chọn lọc phù hợp»; đánh giá 16 công cụ của repo (MIT, Node.js, còn bảo trì) cho quyết định **KHÔNG cài máy chủ MCP bên thứ ba** (chạy mã ngoài với quyền mạng, không chọn được tập con, 11/16 công cụ trùng thứ đã có) mà lấy đúng **hai khoảng trống thật** bằng mã của ta gọi THẲNG API công khai — ma trận đầy đủ chọn/bỏ + lý do ở `.claude/agents/_CONNECTOR-CHUNG-CU.md` §1ter. (1) **RxNorm** (NLM RxNav, không khoá): chuẩn hoá biệt dược → hoạt chất, bốn trạng thái `khop_chinh_xac`/`gan_dung`/`khong_thay`/`loi` không được gộp; đo thật «Glucophage» → metformin ✔, nhưng «metfromin» (gõ sai) → **merbromin**, một thuốc sát khuẩn khác hẳn ⇒ `gan_dung` không bao giờ dùng tự động; «Coversyl» → toàn mã `Obsolete` (thuộc tính rỗng, gắn cờ `hieu_luc:false`); **API tương tác của RxNav đã ngừng (HTTP 404)** nên công cụ KHÔNG kiểm tương tác/liều. (2) **EMA** (báo cáo JSON công khai, 0,7 MB nén/6,8 MB giải nén, 2.746 bản ghi, cache 7 ngày): trạng thái cấp phép TẬP TRUNG, giám sát bổ sung, cấp phép có điều kiện (rosiglitazone: Avandia `Expired`, Avaglim `Withdrawn`); **chỉ có thuốc cấp phép tập trung** (không thấy ≠ chưa cấp phép ở EU) và trạng thái **không kèm lý do**. Cả hai: lỗi mạng/bố cục lạ = `loi` («KHÔNG BIẾT», mã thoát 2) chứ không phải «không thấy»; đầu vào chỉ là TÊN ngắn (≤100 ký tự, chặn PII). Lỗi thật gặp khi kiểm sống: tham số `tty=IN+MIN+PIN` truyền thô bị mã hoá `%2B` ⇒ RxNav HTTP 400 (phải cách nhau bằng dấu cách) — adapter đã chuyển thành `loi` thay vì «không thấy», đúng thiết kế. Nối vào agent: `ke-don-an-toan` mục 8 (BH41 — công cụ phải có agent gọi) và `khoang-trong-nghien-cuu` mục 5 (WHO GHO làm bối cảnh gánh nặng bệnh, **không làm p0**; tài liệu đã có ở `sync/skills/database-lookup/references/who.md`). 37 test offline ở `tests/test_rxnorm_ema_medicines.py` (10 phép đột biến ở adapter + 10 ở chốt **BH108**, đều đỏ đúng chỗ; một phép sống sót lần đầu — «giữ hạng tốt nhất khi gộp trùng» — đã bổ sung ca kiểm). Đo lại trọn: 5.713 test đạt · 15 bỏ qua · 0 lỗi; ruff sạch. **Đã loại có chủ ý:** FAERS/recall/shortage/PubMed/ClinicalTrials/journals/guidelines (trùng), Google Scholar (cào web qua dịch vụ trả phí bên thứ ba), nhi khoa (ngoài phạm vi, hoãn), TGA/Health Canada (không phải cơ quan bác sĩ VN dùng để ra quyết định).
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
  · **LANE guideline nối trực tiếp, miễn phí, không khoá — thêm 20/09/2026** (`app/sources/guideline_lanes.py`, cấu hình ở
  `feeds.py::GUIDELINE_LANES`), theo yêu cầu «kết nối các nguồn guideline chưa có connector». Đo 20/09/2026: RSS chính thức chỉ có ở
  GOLD · GINA · KDIGO · EASL · AASLD · CDC MMWR (đã nối); IDSA/ESC/EULAR/ADA/ACC/SIGN/BTS/ASH/AAN đều 404, WHO 403, NICE 403, USPSTF không
  có RSS. Nên phủ qua đường công khai khác, đều đã đo chạy thật (**33/33 lane trả mục thật**, SourceLog `ok`): (1) **Europe PMC**
  (độc lập NCBI, có PMID): loại xuất bản «Practice Guideline» toàn cầu (127 bài từ 01/08), USPSTF, WHO, CDC MMWR R&R; (2) **WHO IRIS**
  OAI-PMH (`iris.who.int/oai/request`, set Headquarters; `from` của OAI lọc theo ngày SỬA bản ghi nên chỉ giữ bản ghi có `dc:date` mới
  và tiêu đề có tính khuyến cáo); (3) **Bộ Y tế VN** `kcb.vn/phac-do` (danh sách Quyết định ban hành hướng dẫn chẩn đoán, điều trị;
  robots.txt cho phép; 1 GET/lượt; tiêu đề lấy từ thuộc tính `title`, bỏ đuôi `?categoryId=`; HTML có thể đổi bố cục — parser trả [] chứ
  không bịa); (4) **Crossref theo tiêu đề** cho 21 hiệp hội trên tạp chí của họ (ACC/AHA ×3, ESC, ADA, IDSA, EULAR, AASLD, KDIGO, ATS,
  ERS, BTS, AGS, ACP, ASCO, ESMO, ASH, AGA, ACG, AAN, ACR): lọc nhiều ISSN + cụm tiêu đề + regex tổ chức + tính khuyến cáo, loại
  đính chính/thư/bình luận; (5) RSS trực tiếp GOLD/GINA/KDIGO/EASL/AASLD/CDC MMWR weekly. `authority.py::FEED_TO_AUTHORITY` ánh xạ
  feed → tên tổ chức; coverage báo phủ gián tiếp ở khoá riêng `healthy_via_lane` (KHÔNG gộp vào `healthy`) và liệt kê `not_connected`.
  **Giới hạn nói thẳng:** đây là lane KHÁM PHÁ theo TIÊU ĐỀ (guideline nhận qua tiêu đề/loại xuất bản, có thể lẫn bài bình luận về
  guideline), KHÔNG phải nguồn «đã duyệt» và KHÔNG thay việc đọc guideline gốc; còn CHƯA có kết nối nào cho **NICE** (API chỉ cấp cho
  tổ chức, có phí quốc tế) và **USPSTF API** (phải xin duyệt qua email; lane MEDLINE thay thế đã có) — thư nháp ở
  `docs/xin-cap-quyen-nguon-chung-cu.md`. Chi phí: +33 lượt gọi/lần quét (cache 1 giờ). 42 test ở `tests/test_guideline_lanes.py`
  (4 phép đột biến đều đỏ đúng chỗ).
  ✅ **ĐÃ ĐÓNG khoảng trống NICE — thêm 22/09/2026, theo yêu cầu bác sĩ "không đăng ký cá nhân
  được thì đóng khoảng trống bằng cách khác".** Dòng "chưa có kết nối nào cho NICE" ở trên nay
  chỉ còn đúng cho NICE Syndication API CHÍNH THỨC (vẫn cần hợp đồng tổ chức, không đổi). Thêm
  lane `epmc_nice` (cùng khuôn `epmc_uspstf`): AFF="National Institute for Health and Care
  Excellence" AND PUB_TYPE="Practice Guideline" qua Europe PMC — không cần khoá, không cần đăng
  ký. **Đo sống trước khi chốt tham số:** nguồn ra bài THƯA (giống USPSTF) — 0 hit ở
  window_days=365/545/730, phải **1095 (3 năm)** mới có hit thật; đặt 365 như USPSTF ban đầu
  từng bị sẽ luôn trả rỗng, không phải lỗi mạng. Kiểm qua `RSSFeedClient` thật (không phải script
  tự viết): 5 bản ghi, PMID thật (vd 38889923, "Recognition, diagnosis, and early management of
  suspected sepsis: summary of updated NICE guideline", 2024). Đăng ký `SRC-037` trong
  `data/sources.json`, nối `feed_epmc_nice→"nice"` vào `authority.py::FEED_TO_AUTHORITY`. 2 test
  mới ở `tests/test_guideline_lanes.py`, mutation-tested (đột biến `window_days=365` → đỏ đúng
  chỗ, khớp con số đã đo sống).
  ✅ **ĐÍNH CHÍNH cùng ngày — SRC-020 (Bộ Y tế VN) "not-covered" trong `data/sources.json` là SỔ
  LỖI THỜI, không phải khoảng trống thật.** `kcb_vn_lane()` mô tả ở đoạn trên đã tồn tại và chạy
  từ 20/09/2026 — sổ đăng ký nguồn chỉ chưa được cập nhật theo mã sống (đúng họ lỗi "tài liệu nói
  một đằng, mã sống chạy một nẻo" lặp lại nhiều lần trong file này). Đã sửa `status: active`,
  thêm `SRC-020` vào `DIEM_THAM` của `tools/sources_health.py` (đã kiểm reachability riêng: HTTP
  200 thật từ chính môi trường chạy chốt, khác hẳn ca DAV dưới đây).
  ⛔ **Cục Quản lý Dược VN (SRC-021) — THỬ nối cùng ngày, KHÔNG xác minh được, KHÔNG viết
  connector.** Định thêm `dav_vn_lane()` cùng khuôn `kcb_vn_lane()` (đích
  `dav.gov.vn/canh-bao-va-thu-hoi-cn81.html`) nhưng `dav.gov.vn` **không tới được** từ môi trường
  phiên qua CẢ BA phương pháp độc lập: `urllib` timeout, trình duyệt Claude báo "denied/failed",
  `WebFetch` trả thẳng `ECONNREFUSED 103.124.60.65:443` (từ chối kết nối tầng TCP — tín hiệu mạnh
  nhất, không phải chặn bot ở tầng ứng dụng như kiểu NICE 403). **Cố ý KHÔNG viết connector** —
  sẽ phải khẳng định "robots.txt cho phép" mà không kiểm chứng được, đúng loại bịa mà toàn bộ
  kỷ luật của repo này chống lại. **Việc cần bác sĩ:** tự mở hai URL trên từ mạng Việt Nam
  (`dav.gov.vn/canh-bao-va-thu-hoi-cn81.html` + `dav.gov.vn/robots.txt`) — tải được thì báo lại,
  lúc đó viết connector đúng khuôn `kcb_vn_lane()` mới có căn cứ thật.
  ⛔ **Epistemonikos (SRC-036) — VẪN mở, không có đường vòng hợp lệ.** Khác NICE (bị chặn TRUY
  CẬP TỰ ĐỘNG, có thể lách bằng nguồn thay thế công khai), Epistemonikos chặn ở tầng NỘI DUNG —
  họ tự khai *"contact us to register your application"*, không có API công khai song song để đi
  vòng. Đã đối chiếu 22/09/2026: SR/MA vẫn được phủ đáng kể qua PubMed/Europe PMC tầng SR/MA +
  Cochrane MCP (Cấp 0) — mất Epistemonikos là mất lớp TỔNG HỢP/phân loại chéo nhiều CSDL riêng
  của họ, không phải mất trắng khả năng tìm SR/MA.
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
  · **Cochrane MCP (Cấp 0) — đăng ký `SRC-038` 22/09/2026, kiểm sống 2 lần trong cùng ngày (một
  lần bị Cloudflare chặn hoàn toàn qua CẢ 3 phương pháp, một lần chạy tốt sau 1 lần thử lại).**
  Đây là connector MCP (`mcp__plugin_cochrane_cochrane__cochrane_search/get_details/suggest_terms`)
  bác sĩ tự cài từ marketplace `cochrane-marketplace` — doctrine dùng nó đã được viết đầy đủ ở
  `.claude/agents/_CONNECTOR-CHUNG-CU.md` §1bis + §2quater từ 20/09/2026 (trình tự gọi, cạm bẫy
  `orderBy`, xử lý `review:0`, giao thức thử-lại-1-lần khi lỗi điều hướng). **Ranh giới CỐ Ý,
  đừng nhầm lẫn khi bác sĩ hỏi "cài vào hệ thống cho vòng quét tuần":** đây là công cụ MCP chỉ
  gọi được TỪ TRONG một phiên Claude Code tương tác (cần trình duyệt CDP nền của chính plugin) —
  KHÔNG phải HTTP endpoint mà `weekly_safety.sh`/`surveillance_scan.py` (chạy qua cron/scheduled
  task, không có phiên Claude nào đứng sau) có thể gọi. Vòng quét tuần TỰ ĐỘNG vẫn dùng lane
  Crossref theo ISSN 1465-1858 (`app/sources/feeds.py::cochrane_cdsr`, đã có từ trước) — phủ được
  review CDSR mới nhưng KHÔNG có abstract có cấu trúc/PICO/mức chắc chắn GRADE như MCP. Cochrane
  MCP chỉ hữu dụng khi một AGENT (`tra-cuu-chung-cu`/`tong-quan-y-van`/`cap-nhat-guideline`/
  `huong-dan-lam-sang`) đang chạy TRONG phiên tương tác chủ động gọi để trả lời MỘT câu hỏi cụ
  thể — không có cách "cài đặt" để nó tự chạy định kỳ không người giám sát.
  · **Wiley Text and Data Mining (TDM) API — xây 23/09/2026, theo yêu cầu bác sĩ sau khi đã có
  token thật từ tài khoản Wiley Online Library (WOL) của bác sĩ.** `app/sources/wiley_tdm.py`
  (`WileyTdmClient`), thư viện nền là gói PyPI chính thức `wiley-tdm`
  (github.com/WileyLabs/tdm-client). **KHÁC HOÀN TOÀN** `SRC-041` (MCP `plugin:bio-research:wiley`
  — claude.ai connector, vẫn "not-covered", cần bác sĩ tự cấp quyền OAuth qua cài đặt connector,
  agent KHÔNG được làm hộ) — đây là API REST tải TOÀN VĂN PDF THEO DOI ĐÃ BIẾT TRƯỚC, KHÔNG phải
  nguồn tìm kiếm/khám phá. Đăng ký `SRC-042` trong `data/sources.json` (workspace gốc).
  **Kiến trúc cố ý khác mọi connector khác:** `WileyTdmClient` KHÔNG kế thừa `SourceClient`, KHÔNG
  có `.search()`, và KHÔNG có trong `get_enabled_sources()`/`get_fallback_sources()` — chỉ dựng
  khi một quy trình/agent ĐÃ CÓ DOI (từ PubMed/Crossref/Scopus/Europe PMC…) và cần lấy toàn văn.
  Nạp qua `_nap_client` (như mọi connector khác) nên thiếu gói `wiley-tdm` không kéo sập cả
  `app.sources`. `ENABLE_WILEY_TDM` mặc định TẮT, `WILEY_TDM_API_TOKEN` **bắt buộc thật** (chặn
  cứng như Scopus/Epistemonikos — `WileyTdmClient()` tự chặn sớm bằng lỗi tiếng Việt rõ ràng thay
  vì để lọt `ValueError` tiếng Anh mù mờ của thư viện gốc). Token là UUID lấy từ trang "Text and
  Data Mining" trong tài khoản WOL — **KHÔNG BAO GIỜ nhập/dán qua Claude Code**; bác sĩ tự thêm
  `WILEY_TDM_API_TOKEN=<token>` và `ENABLE_WILEY_TDM=true` vào
  `~/.ebm-secrets/medical-ebm-automation.env`.
  ⚠️ **GIỚI HẠN QUAN TRỌNG NHẤT, CHƯA xác nhận chạy thật lúc viết module này** — README chính thức
  của WileyLabs/tdm-client, mục Known Limitations, ghi nguyên văn *"Access is IP address based
  only"*: dù token hợp lệ, IP gọi request phải nằm trong dải IP mà tài khoản WOL của bác sĩ được
  cấp quyền (thường là mạng bệnh viện/tổ chức đã mua gói Wiley Online Library) — gọi từ mạng khác
  (nhà, VPN, máy này) có thể nhận `ACCESS_DENIED` cho bài KHÔNG PHẢI Open Access dù token đúng.
  Chỉ bài Open Access chắc chắn tải được từ mọi IP. **Kiểm sau khi có token:**
  `python run.py wiley-tdm-test <DOI Open Access>` rồi một DOI KHÔNG Open Access để biết đúng
  ranh giới thật của tài khoản — lệnh RIÊNG (không dùng `test-live`, vì Wiley TDM không có
  `.search()` để khớp khuôn chung). Trần nhịp Wiley công bố: ~3 bài/giây, 60 request/10 phút;
  `WILEY_TDM_RATE_LIMIT_SECONDS` mặc định 10.0 (thư viện gốc mặc định 5.0, README khuyến nghị
  10.0 cho việc dùng liên tục). **KHÔNG tham gia chuỗi 3 tầng kiểm rút bài** — tải được PDF không
  xác nhận bài chưa bị rút; phải kiểm rút bài qua kênh hiện có (PubMed/Europe PMC/Retraction Watch
  offline) TRƯỚC khi dùng nội dung PDF cho việc gì. 15 test offline ở `tests/test_wiley_tdm.py`
  (thư viện `wiley_tdm` được GIẢ LẬP qua `sys.modules`, không phụ thuộc mạng thật hay việc gói có
  cài trong venv chạy test hay không).
  · **Connector TẢI TOÀN VĂN guideline trực tiếp từ website hiệp hội chuyên ngành (GOLD/GINA/
  BTS/PMC) — xây 23/09/2026, theo yêu cầu bác sĩ "đảm bảo chứng cứ ESC/ADA/GOLD/GINA... luôn
  được đọc toàn văn".** Trước khi viết bất kỳ dòng code nào, đã khảo sát ĐỘC LẬP robots.txt +
  điều khoản sử dụng của TỪNG tổ chức (đúng kỷ luật "không crawl khi chưa kiểm trước" của dự án)
  — 18 tổ chức được khảo sát (ESC, ADA, GOLD, GINA + 14 hội khác: ACC/AHA, IDSA, EULAR, ATS, ERS,
  BTS, AGS, ACP, ASCO, ESMO, ASH, AGA, ACG, AAN), kết quả:
  **KHẢ THI** (robots.txt cho phép THẬT + toàn văn miễn phí công khai, đã đọc trực tiếp không
  suy đoán): **GOLD, GINA, BTS**. **ADA**: crawl trực tiếp `diabetesjournals.org` KHÔNG khả thi
  (robots.txt của domain đó **không đọc được** — 403/lỗi DNS ở mọi lần thử, "chưa đọc được"
  TUYỆT ĐỐI không được hiểu là "cho phép ngầm") — nhưng ADA nộp lưu toàn bộ "Standards of Care"
  lên **PMC** (PubMed Central, hạ tầng công khai của NIH, robots.txt kiểu allowlist có
  `Allow: /articles/` tường minh), nên đi đường PMC thay vì crawl trực tiếp. **KHÔNG khả thi**
  (robots.txt chặn AI-crawler toàn site, hoặc toàn văn thật nằm ở nhà xuất bản thứ ba có
  paywall/bot-detection đã xác nhận, hoặc cả hai): **ESC** (chặn `ClaudeBot`/`GPTBot`/
  `Google-Extended` toàn site; toàn văn nằm ở European Heart Journal/Oxford Academic), ACC/AHA,
  IDSA, EULAR, ATS, AGS, ACP, ASH, AGA, ACG, AAN. **Cần khảo sát thêm** trước khi kết luận: ERS,
  ASCO, ESMO (môi trường khảo sát bị chặn/lỗi mạng, chưa đủ dữ kiện — KHÔNG suy đoán thành
  "khả thi" hay "không khả thi").
  **Kiến trúc:** 4 module mới trong `app/sources/` (`gold_copd.py`, `gina_asthma.py`,
  `bts_guidelines.py`, `pmc_guideline_fulltext.py`), tất cả theo khuôn (B) của
  `wiley_tdm.py::WileyTdmClient` — KHÔNG kế thừa `SourceClient`, KHÔNG có `.search()`, KHÔNG
  tham gia `get_enabled_sources()`/vòng quét song song (không phải nguồn khám phá). Hạ tầng
  dùng chung ở `app/sources/guideline_fulltext_common.py`: dataclass `KetQuaToanVanGuideline` +
  hàm `trich_van_ban_tu_pdf()` (thư viện mới `pypdf`, nạp trễ qua `_nap_client`). `HttpClient`
  được thêm phương thức `get_bytes()` (tải nhị phân, KHÔNG cache — định dạng cache cũ là JSON,
  không hợp với PDF) — vẫn hưởng đủ retry/backoff/throttle/phát hiện chặn NCBI sẵn có.
  **RANH GIỚI BẢN QUYỀN, ÁP DỤNG CHO CẢ 4 CONNECTOR, KHÔNG NGOẠI LỆ** (cả GOLD/GINA/BTS đều có
  điều khoản cấm sao chép/phân phối lại/đăng công khai khi chưa có phép bằng văn bản; ADA qua
  PMC là license CC BY-NC-ND, cấm bản phái sinh): PDF tải về CHỈ dùng làm **nguồn tham chiếu nội
  bộ** để trích câu chữ khuyến cáo cụ thể kèm PMID/DOI/URL gốc — TUYỆT ĐỐI KHÔNG hiển thị nguyên
  văn PDF trên dashboard công khai, KHÔNG đăng lại toàn văn, KHÔNG phân phối file cho bên thứ ba.
  **Giới hạn kỹ thuật đã đo, PHẢI tôn trọng khi bảo trì:**
  — GOLD/GINA: tên slug trang landing + tên file PDF đổi MỖI NĂM, không có mẫu cố định
  ⇒ `tim_url_bao_cao_moi_nhat()` LUÔN dò qua trang mục lục ổn định (`archived-reports/` cho
  GOLD, `reports/` cho GINA), fail-closed (`None` + cảnh báo) khi không tìm thấy link khớp mẫu —
  TUYỆT ĐỐI không đoán/ghép URL theo công thức năm.
  — GINA: robots.txt đòi `Crawl-delay: 10` ⇒ `GinaAsthmaFullTextClient` BẮT BUỘC dùng
  `HttpClient(min_interval=10.0)`. GINA từng TẠM ĐÓNG truy cập miễn phí 07→11/2025 (lý do tài
  chính) — connector phân biệt "phản hồi không phải PDF thật" (thiếu chữ ký `%PDF`, nghi đổi
  chính sách) với lỗi mạng thường, báo hai thông điệp KHÁC NHAU, không được gộp.
  — PMC: robots.txt đòi `Crawl-delay: 1` ⇒ `min_interval=1.0`. `PmcGuidelineFullTextClient` CHỈ
  nhận PMCID đã biết (tra qua `pubmed.py`/Europe PMC trước) — KHÔNG tự tìm PMCID.
  — BTS: KHÔNG có trang mục lục ổn định (mỗi bệnh một slug riêng, không đổi theo năm cập nhật)
  ⇒ `BtsGuidelineFullTextClient` KHÔNG có `tim_url_bao_cao_moi_nhat()` tự động, chỉ nhận URL PDF
  ĐÃ BIẾT. Một số hướng dẫn BTS đồng xuất bản với NICE/SIGN và toàn văn thật nằm ở domain khác
  (đã xác nhận với hướng dẫn Hen 11/2024 trỏ sang `nice.org.uk`) — connector TỪ CHỐI tải (không
  gọi mạng) nếu URL không thuộc `brit-thoracic.org.uk`, vì domain khác chưa được khảo sát riêng.
  **CHƯA XÁC NHẬN CHẠY THẬT LÚC VIẾT** — cả 4 module chỉ có 31 test offline PASS (mock
  `HttpClient`/`trich_van_ban_tu_pdf`, không gọi mạng thật), CHƯA gọi mạng thật lần nào tới
  goldcopd.org/ginasthma.org/brit-thoracic.org.uk/pmc.ncbi.nlm.nih.gov. Đăng ký `SRC-043`
  (GOLD) · `SRC-044` (GINA) · `SRC-045` (BTS) · `SRC-046` (PMC) trong `data/sources.json`,
  `status: "not-covered"` cho tới khi kiểm sống. Cả 4 mặc định TẮT (`ENABLE_GOLD_COPD_FULLTEXT`
  / `ENABLE_GINA_ASTHMA_FULLTEXT` / `ENABLE_BTS_GUIDELINES_FULLTEXT` /
  `ENABLE_PMC_GUIDELINE_FULLTEXT`, không cần API key).
  **Việc CHƯA làm, có chủ ý** (ghi rõ để không ai suy nhầm là đã xong): (1) chưa nối vào bất kỳ
  agent/pipeline nào (chỉ là hạ tầng CÓ SẴN, gọi thủ công) — nối vào `tra-cuu-chung-cu`/
  `cap-nhat-guideline` là việc SAU KHI kiểm sống; (2) chưa khảo sát ERS/ASCO/ESMO (kết quả
  "can_kiem_them", không đủ dữ kiện); (3) ESC/ACC-AHA/IDSA/EULAR/ATS/AGS/ACP/ASH/AGA/ACG/AAN
  CỐ Ý không có connector crawl — với các tổ chức này, đầu ra hệ thống vẫn chỉ là link + tóm
  tắt (đúng cách `tra-cuu-chung-cu` đang hoạt động), bác sĩ tự mở link đọc toàn văn qua quyền
  truy cập của mình; (4) chưa đọc lại nguyên văn tiếng Anh đầy đủ (chữ-đối-chữ) các trang điều
  khoản sử dụng đã khảo sát — bản khảo sát đi qua công cụ tóm tắt AI (WebFetch), nên trước khi
  coi đây là căn cứ pháp lý chính thức, nên đọc lại bằng trình duyệt thật.

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
