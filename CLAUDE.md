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
  (miễn phí, không key, bật mặc định) · Semantic Scholar (bật mặc định, chạy được không key nhưng
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
  · **DynaMed/DynaMedex (EBSCO) — thêm 13/09/2026**, theo yêu cầu bác sĩ sau khi xác nhận có tài
  khoản DynaMed (`app/sources/dynamed.py`) — TẮT mặc định, đòi `ENABLE_DYNAMED=true` +
  `DYNAMED_CLIENT_ID`/`DYNAMED_CLIENT_SECRET` **thật** trong `~/.ebm-secrets/
  medical-ebm-automation.env`. **KHÁC HẲN Scopus:** không phải API key đơn giản mà là OAuth2
  `client_credentials` (đã xác minh trực tiếp qua `developer.ebsco.com/dynamed`, không suy đoán) —
  đăng ký app tại `.../dynamed/register-app` đòi "Customer ID" + "Group ID" do **đại diện EBSCO
  cấp riêng**, nghĩa là KHÔNG PHẢI mọi tài khoản DynaMed cá nhân/website đều tự động có quyền gọi
  API này; **cần bác sĩ tự xác nhận với EBSCO/đơn vị chủ quản** trước khi mong đợi connector chạy
  được. `DYNAMED_PRODUCT` mặc định `dynamed`, đổi `dynamedex` nếu tài khoản có thêm Micromedex —
  sai giá trị sẽ bị từ chối cấp token dù client_id/secret đúng.
  **Giới hạn đã biết:** nguồn TỔNG HỢP THỨ CẤP tại điểm khám (Condition/Drug Monograph…), không có
  PMID/DOI cho từng mục nên KHÔNG tham gia chuỗi 3 tầng kiểm rút bài của `retraction_chain.py`
  (giống Scopus/OpenAlex); `fields` tìm kiếm CỐ Ý chỉ xin `title`+`pubType` (không xin nội dung đầy
  đủ) vì DynaMed có bản quyền EBSCO — kết quả chỉ mang tiêu đề + link, bác sĩ tự mở DynaMed đọc toàn
  văn, TUYỆT ĐỐI không lưu/chép toàn văn vào file git-tracked. Test nhanh sau khi có credential:
  `python run.py test-live dynamed "<từ khoá>"`. 19 test ở `tests/test_dynamed.py` (mutation-tested:
  đã kiểm bằng cách tắt tạm chốt fail-closed thiếu credential — gọi THẬT tới
  `apis.ebsco.com/medsapi-auth/v1/token` với credential rỗng, xác nhận endpoint có thật và trả 401,
  rồi khôi phục nguyên trạng). **Phạm vi bản đầu: mới nối tầng NGHIÊN CỨU** (`app/sources/`,
  `run.py test-live`) — CHƯA nối tầng giám sát lâm sàng (`EBM-Dashboards/tools/
  surveillance_scan.py`), khác Scopus đã có ở cả hai tầng; đó là bước tiếp theo nếu bác sĩ xác nhận
  connector chạy được thật với credential thật. **CHƯA XÁC NHẬN CHẠY THẬT** — đang chờ bác sĩ đăng
  ký app EBSCO và dán `DYNAMED_CLIENT_ID`/`DYNAMED_CLIENT_SECRET` thật.

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
