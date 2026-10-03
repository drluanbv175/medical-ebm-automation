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
- **Test KHÔNG ghi vào `data/` thật (30/09/2026)**: `tests/conftest.py` trỏ `settings.data_dir` (raw/processed/reports/exports…) sang thư mục TẠM cho cả phiên và gắn chốt canh `tests/canh_ghi_du_lieu_that.py` — test nào mở tệp để ghi/đổi tên/xoá dưới `data/` của cây thì ĐỎ ngay ở test đó (miễn trừ duy nhất: `archive/`; tệp audit chronic care hết miễn trừ từ 01/10/2026 vì `app/chronic_care/audit.py` nay đi theo `settings.processed_dir`). Test connector không cần tự cô lập `data_dir` nữa; đừng trả `settings.data_dir` về thư mục thật; tiến trình CON của test không có fixture này — script con chạy mã ghi dữ liệu (vd import `app.dashboard.main`) phải tự trỏ `settings.data_dir` sang thư mục tạm; mã nguồn thêm hằng module chốt đường dẫn đầu ra lúc import ⇒ thêm vào `_HANG_CHOT_LUC_IMPORT`. Đo trước khi vá (clone sạch, 6.446 test): mỗi lượt pytest để lại 35 payload GIẢ trong `data/raw/{core,scopus,epistemonikos}/` + 5 `processed/pipeline_*.json` + 4 tệp `exports/` đè bản cùng ngày + một lô `tiktok/…-tuso` ⇒ payload ở ba thư mục `raw` đó ghi TRƯỚC ngày này LẪN payload của test — lọc (so nội dung với payload test, tên truy vấn kiểu `sglt2_ckd`/`query_hiếm`) trước khi dùng làm bằng chứng đo.
- **Agent source of truth**: sửa `.claude/agents/*.md` ở thư mục gốc OneDrive; không sửa tay `.Codex/agents/*.toml` hoặc `.codex/agents/*.toml`. Sau khi sửa/thêm agent, chạy sync ở thư mục gốc.
- **Plugin ownership**: owner/worker canonical nằm ở `../.claude/agents/_PLUGIN-ROUTING-CONTRACT.md`
  và `../tools/orchestrator/plugin_ownership_registry.json`. Repo này cung cấp runtime nghiên cứu
  sản xuất; ARS/Anthropic/BMAD/Bio không được thay `run_pipeline.py`, tự ghi approval ledger hoặc
  mở G2/G4/G5/G8/G9/G10. Kiểm từ workspace gốc bằng
  `python ../tools/verify_plugin_orchestration.py`.
- **Research assurance**: sáu cổng canonical là G2/G4/G5/G8/G9/G10. G2 phải chặn khi WHO TRDS v1.3.1 mục 13/14/19/20 thiếu dữ kiện PI đã pin hoặc tham chiếu Hội đồng chỉ là fallback; G9 phải chặn khi thiếu quyền truy cập dữ liệu/độc lập nhà tài trợ theo ICMJE 1/2026. Chạy `python ../tools/verify_controlled_research_automation.py`; Claude Code không tự điền các xác nhận đời thực.
- **Evidence surveillance deployment**: `weekly_safety.sh`/`monthly_update.sh` là owner thu thập duy nhất. `PARTIAL/FAIL` phải giữ watermark, chặn `bridge_to_ebm_master.py` và không gửi cảnh báo nội dung. Chạy `python tools/verify_evidence_surveillance_deployment.py --online`; chỉ `READY_FOR_CONTROLLED_DEPLOYMENT` mới cho phép candidate-only. Claude Code không tự điền UAT, alert/rollback/shadow evidence hoặc phê duyệt để làm xanh cổng. **Lượt chạy THÊM ngoài Mac (29/09/2026):** `weekly_safety.sh --chi-bao-cao <thư mục>` / `monthly_update.sh --chi-bao-cao <thư mục>` (cửa sổ 35 ngày) → `tools/bao_cao_giam_sat_chi_doc.py`: quét thật nhưng DB/watermark ở thư mục tạm, tắt cứng Consensus/SerpApi, KHÔNG cảnh báo/Hub/Antifacts/ghi sổ lượt; mã 0 PASS · 2 PARTIAL/FAIL · 3 tham số sai. Cờ `--bo-ebm-tuan` bỏ `ebm-tuan.md` (≈2 MB) khỏi thư mục ra, ghi `bo_co_y` trong tóm tắt. Routine Cloud «Giam sat tuan Cloud chi bao cao (phien co dinh)» (thứ Hai 06:56 giờ VN) đánh thức MỘT phiên cố định có gắn repo (phiên tạo mới mỗi lượt KHÔNG có quyền push — lượt thử 29/09 hỏng vì vậy) để mở PR nháp chỉ chứa `reports/giam-sat-cloud/<ngày>/` — không phải owner thứ hai, không bao giờ tự merge.
- **⚠️ Sau khi đồng bộ agent .md đã sửa vào `medical-ebm-automation/.claude/agents/` (bản in-repo dùng bởi `runtime/agent_registry.py` FULL_SCOPE_A):** BẮT BUỘC chạy `python3 scripts/regenerate_agent_manifest.py --write` rồi dán giá trị self-check SHA-256 in ra vào hằng số `MANIFEST_SELF_CHECK_SHA256` trong `runtime/agent_registry.py` — **kể cả khi số lượng agent KHÔNG đổi**, vì manifest khóa hash theo NỘI DUNG từng file, không chỉ số lượng. Quên bước này → hàng chục test `test_v4_*`/`test_offline_workflow_integration.py` fail với "agent hash mismatch" (đã xảy ra ≥2 lần, 2026-07-05). Chạy `pytest` sau mỗi lần sync để bắt sớm nếu quên.
- **Secrets**: live in `.env` outside OneDrive, symlinked into the repo if needed. Never commit or print them.
- **Nguồn chứng cứ & connector — LUẬT THƯỜNG TRỰC** (rút gọn 03/10/2026, PM-09). Lịch sử đo, số liệu theo ngày và bẫy đã gặp nằm
  NGUYÊN VĂN ở `docs/NGUON-CHUNG-CU-CHI-TIET.md` — đọc đúng mục liên quan TRƯỚC khi kết luận «nguồn X hỏng» hay sửa connector.
  Bài học mới về nguồn ghi vào tệp đó (hoặc `audit/`), KHÔNG nối vào đây; `tests/test_claude_md_ngan_sach_20261003.py` chặn tệp này
  vượt ngân sách ký tự.
  · **Phiên Cloud:** engine chạy thật khi môi trường Cloud có `USE_MOCK_SOURCES=false` + `NCBI_EMAIL` (đo 25/09). Đo bằng
    `python run.py test-live <nguồn>`, KHÔNG bằng `curl` (hook runtime chặn egress của Bash). Khoá qua «API credentials» của proxy +
    biến `KHOA_QUA_PROXY=<nguồn>`; SerpApi/NCBI/openFDA gửi khoá qua URL nên proxy không gắn được. Container Python 3.11 ⇒ venv
    `python3.12`. Proxy 403/407 ⇒ `HttpClient` bỏ ngay. Connector MCP đi qua máy chủ Anthropic. Mỗi `test-live consensus` tốn 1 lượt.
  · **Ghi chú thay vì PARTIAL** (bác sĩ chọn 29/09; mọi lỗi khác vẫn PARTIAL): MedWatch 401/403 khi openFDA + ≥ 1 feed an toàn khác
    khoẻ ⇒ `FEED_FDA_MEDWATCH_PROVIDER_BLOCKS_AUTOMATED_ACCESS_401_403`; `fda_recalls` do dự phòng chính thức phục vụ ⇒ degraded +
    `FEED_FDA_RECALLS_SERVED_BY_OFFICIAL_FALLBACK`; Scopus 403 là TRANG CHẶN của Cloudflare và PubMed + Europe PMC + Crossref đều «ok»
    ⇒ `SCOPUS_BLOCKED_BY_CLOUDFLARE_403_NETWORK_IP`; lane gốc bị chặn đường mạng mà đường thay khoẻ ⇒ ghi chú
    `<NGUỒN>_BLOCKED_ON_NETWORK_PATH_SERVED_BY_<ĐƯỜNG THAY>`.
  · **Cú pháp PubMed:** truy vấn có thẻ `[ta]/[pt]/[cn]/[ti]…` chỉ gửi tới nguồn `hieu_cu_phap_pubmed=True` (PubMed); nguồn khác ghi
    `skipped` (`bo_qua_cu_phap_pubmed:`), nguồn bắt buộc bị bỏ qua sạch ⇒ `REQUIRED_SOURCE_NOT_QUERIED`. Regex dùng chung:
    `app/sources/base.py::CU_PHAP_PUBMED_RE`.
  · **Mạng / VPN** (bác sĩ chốt VPN LUÔN BẬT 01/10): nguồn bị chặn phụ thuộc IP thoát LÚC ĐÓ. `HttpClient` gắn nhãn đầu `last_error`
    (`[cloudflare-chan]` · `[cloudfront-chan]` · `[ncbi-chan]` · `[proxy-chan]` · `[ket-noi-het-gio]` · `[ket-noi-hong]` ·
    `[dns-hong]` · `[tls-hong]`); `source_health["mang"]` là dấu vân đường mạng; `hong_keo_dai` = «unavailable» ≥ 3 lượt live liền
    trải ≥ 7 ngày; đo/so đường mạng: `python tools/do_mang_nguon.py [--so-sanh a.json b.json]`. Đường thay qua VPN (khai ở
    `ingestion._DUONG_THAY_KHI_CHAN_MANG`): WHO IRIS ⇒ `who_publications`; ECDC ⇒ `who_don` + `eurosurveillance`; EMA ⇒ sổ EC
    `ec_union_register.py`. `SCOPUS_BIND_INTERFACE` KHÔNG vượt được Kaspersky VPN (đo 20/09). Bật/tắt VPN là quyết định của bác sĩ.
  · **Connector** (khoá CHỈ ở `~/.ebm-secrets/medical-ebm-automation.env`, không qua chat; ngoài lõi miễn phí đều TẮT mặc định):
    lõi PubMed · Europe PMC · Crossref · OpenAlex · ClinicalTrials · openFDA (khoá `OPENFDA_API_KEY` tuỳ chọn; bị từ chối thì báo rõ và
    lùi về không khoá) · Semantic Scholar. Scopus (`ENABLE_SCOPUS`, key bắt buộc; không abstract) · CORE (`ENABLE_CORE`, key tuỳ chọn;
    nhịp riêng `CORE_MIN_INTERVAL_SECONDS`, chờ đúng mốc header rate-limit; `not_attempted` = truy vấn bị cầu dao cắt) ·
    Epistemonikos (token bắt buộc, phải email xin — chưa có) · Wiley TDM (tải toàn văn THEO DOI đã biết, không phải nguồn khám phá;
    truy cập theo IP; PDF có bản quyền ⇒ thư mục tải bị git ignore và client từ chối thư mục git thấy).
  · **Bậc thang dự phòng CÓ CỔNG** (Consensus → SerpApi Scholar): chỉ leo khi < `FALLBACK_MIN_TRUSTED` (3) bài đáng tin; nguồn lõi lỗi
    ⇒ KHÔNG leo; trần Consensus 10/tháng · 5/lượt, SerpApi 200/tháng · 8/lượt, đúng MỘT request mỗi search; MỌI bản ghi dự phòng phải
    xác minh Crossref/PubMed (tiêu đề ≥ 0,9 + token phân biệt + năm ± 1 + họ tác giả đầu); Scite công khai chỉ XÁC MINH (chặn bài rút),
    không chấm điểm. Phía MCP theo cùng cổng (`../.claude/agents/_CONNECTOR-CHUNG-CU.md` §2ter).
  · **Thuốc quốc tế:** `tools/tra_thuoc_quoc_te.py` — RxNorm (chuẩn hoá tên; `gan_dung` không bao giờ dùng tự động; API tương tác
    RxNav đã ngừng) + EMA (cấp phép tập trung, dự phòng sổ EC); lỗi mạng/bố cục = «KHÔNG BIẾT» (mã 2), không phải «không thấy».
  · **Feed & lane guideline:** feed tạp chí chế độ Crossref theo ISSN; mốc «bài mới» = ngày bản ghi XUẤT HIỆN trong chỉ mục
    (`from-created-date`) + sàn đầu năm trước — không dùng ngày công bố. Lane: Europe PMC (Practice Guideline · USPSTF · WHO · NICE
    `epmc_nice` cửa sổ 1095 ngày), WHO IRIS, Bộ Y tế `kcb.vn/phac-do`, Crossref theo tiêu đề cho 21 hội — lane KHÁM PHÁ theo tiêu đề,
    không phải nguồn đã duyệt.
  · **Toàn văn guideline:** GOLD · GINA · BTS · PMC qua `tools/toan_van_guideline.py` (cờ `ENABLE_*_FULLTEXT`; in metadata + `--tim`,
    không in toàn văn). ESC/ACC-AHA/IDSA/EULAR/ATS/AGS/ACP/ASH/AGA/ACG/AAN/ESMO/ASCO KHÔNG crawl (robots/điều khoản/thách thức bot);
    ERS chỉ đi đường PMC khi có PMCID. PDF chỉ là tham chiếu nội bộ — không hiển thị/đăng lại/phân phối nguyên văn.
  · **Đã gỡ / không nối:** DynaMed (MedsAPI cần ID tổ chức; điều khoản EBSCO cấm dùng nội dung với AI) · Cục Quản lý Dược
    `dav.gov.vn` (không tới được từ môi trường phiên — chưa viết connector) · NICE Syndication API (hợp đồng tổ chức) · Cochrane MCP
    chỉ dùng trong phiên tương tác (lịch nền dùng lane Crossref ISSN 1465-1858).
  · **Bất biến:** 0 kết quả ≠ «không có»; lỗi mạng/bố cục lạ = KHÔNG BIẾT; chỉ PubMed · Europe PMC · Retraction Watch nằm trong chuỗi
    rút bài 3 tầng; bản ghi khám phá (Scholar · Consensus · Scopus · CORE…) phải phân giải PMID/DOI qua PubMed/Crossref trước khi dùng
    lâm sàng.
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
