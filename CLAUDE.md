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
  · **Consensus API (consensus.app) — thêm 19/09/2026**, bác sĩ đã có khoá gói Free. `app/sources/consensus_api.py`
  (`GET https://api.consensus.app/v1/search`, header `x-api-key`; endpoint cũ `/v1/quick_search` deprecated,
  dự kiến gỡ 2027-02-07). TẮT mặc định, `ENABLE_CONSENSUS=true` + `CONSENSUS_API_KEY` (bắt buộc thật, chặn cứng
  như Scopus). **KHÁC kênh MCP của claude.ai** (`tong-thuat-chung-cu`, `/tra-consensus` — không chia sẻ mã) nhưng
  CHIA SẺ CHUNG hạn mức lượt gọi tháng của tài khoản. **Không nhầm với nhãn `design:'Consensus'`** (= đồng thuận
  chuyên gia trong cổng `verify_dashboard`, hoàn toàn khác).
  **Vai trò: KHÁM PHÁ** (doctrine `_CONNECTOR-CHUNG-CU.md`): bản ghi vào kho như ứng viên, dedup theo DOI với
  PubMed/Scopus…; muốn TRÍCH phải truy ngược DOI gốc + `kiem-chung-trich-dan`/`verify_dashboard --online`. Connector
  không nâng/gán mức chứng cứ (bỏ qua `study_type` do Consensus tự gán — chỉ suy từ tiêu đề/tạp chí, R4).
  **Giới hạn đã biết:** (1) kết quả **KHÔNG có PMID**, chỉ DOI ⇒ chỉ kiểm rút bài qua đường DOI (Crossref
  `updated-by`, BH33), KHÔNG vào chuỗi 3 tầng PMID của `retraction_chain.py`; (2) gói Free: 30 lượt/tháng (1 lượt =
  100 bài), ≤20 bài/yêu cầu, không phân trang, không `study_type`/`takeaway`/toàn văn, 1 yêu cầu/giây; (3) lọc
  theo NĂM (`year_min`) không có ngày/tháng; (4) tham số `medical_mode`/`exclude_preprints` lấy từ README + PR bên
  thứ ba, chưa có đặc tả OpenAPI gốc (docs.consensus.app/reference trả 403 lúc tra) — sai tham số ⇒ 400/422 nổ to.
  **Quyết định LƯU TRỮ của bác sĩ (19/09/2026):** điều khoản Consensus về lưu cache/kết quả API KHÔNG tìm thấy ⇒
  chọn thận trọng: KHÔNG ghi payload ra đĩa (không `save_raw`, `HttpClient(cache_ttl=0)` — cache HTTP mặc định của
  repo GHI JSON đầy đủ xuống `data/raw/_http_cache/`), KHÔNG lưu `abstract`/`takeaway`/`full_text_chunks` vào bản
  ghi; chỉ giữ tiêu đề·tác giả·tạp chí·năm·DOI·url·số trích dẫn·tứ phân vị SJR; cache CHỈ trong bộ nhớ (TTL 6 giờ).
  **HẠN MỨC NỘI BỘ fail-closed:** sổ đếm bền `data/state/consensus_quota.json` (tháng UTC) + trần
  `CONSENSUS_MONTHLY_CALL_CAP` (mặc định 20, chừa dư cho MCP dùng chung; gói trả phí tự nâng). Chạm trần / sổ hỏng /
  trần ≤ 0 ⇒ `RuntimeError` ⇒ Source Log `error`, KHÔNG im lặng trả `[]` (BH27/BH08). Nguồn tùy chọn không nằm
  trong `_DISCOVERY_CORE` nên KHÔNG làm `source_health` PARTIAL/FAIL.
  **CHƯA làm, có chủ ý:** làn giám sát tuần `search_consensus_lane` trong `surveillance_scan.py` (3 bản đồng bộ) —
  quét định kỳ ~40+ truy vấn/lượt sẽ ăn hết 30 lượt Free ngay lượt đầu; làm khi có gói trả phí. **Doctrine còn lời cũ:**
  `.claude/agents/_CONNECTOR-CHUNG-CU.md` §3 và `tools/orchestrator/knowledge.py:52` ghi «loại Consensus vì có
  upsell» — nói về kênh MCP; API gói Free thì miễn phí nên không trái luật «chỉ nguồn miễn phí», nhưng chưa đồng bộ
  lại câu chữ (chờ bác sĩ quyết vì đụng doctrine 2 repo). 65 test ở `tests/test_consensus_api_20260919.py`; kiểm đột
  biến 22 phép trên mã sống, cả 22 đều đỏ đúng chỗ (gồm giữ chỗ hạn mức, khoá luồng, không ghi đĩa, không lưu
  abstract/takeaway). **CHƯA xác nhận chạy thật** — bác sĩ nạp khoá rồi chạy
  `python run.py test-live consensus "<từ khoá>"`; dòng `consensus_chan_doan` chỉ cho TÊN trường + số đếm
  (đặc biệt `so_ban_ghi_co_doi`) để biết gói Free có trả DOI hay không, không lộ khoá/nội dung.
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
