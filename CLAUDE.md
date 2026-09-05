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
- **⚠️ Phiên Claude Code Remote (cloud) đính kèm NHIỀU repo (`medical-ebm-automation` + repo gốc EBM
  qua `add_repo`) — mọi lệnh `../tools/...` ở file này ĐỨNG YÊN dựa trên cấu trúc LỒNG NHAU thật
  trên OneDrive (repo gốc EBM ở ngoài, `medical-ebm-automation/` là thư mục con). Trong phiên cloud,
  `add_repo` nhân bản hai repo thành thư mục LIỀN KỀ PHẲNG dưới `/home/user/` (không lồng nhau) —
  đo được cụ thể: `python ../tools/audit_ebm_system.py` chạy từ đây ném `FileNotFoundError` vì
  `/home/user/tools` không tồn tại; đường đúng là `../<tên-thư-mục-repo-EBM-gốc>/tools/...` (thêm một
  khúc tên repo — dùng `ls /home/user/` để biết tên thật, đừng giả định). Cùng nguyên nhân, hook
  `SessionStart` của repo EBM gốc (khai `.claude/settings.json` bên đó) KHÔNG tự chạy khi repo đó
  không phải "primary" của phiên — phải chạy TAY
  `bash /home/user/<tên-thư-mục-repo-EBM-gốc>/.claude/hooks/session-start.sh` sau khi cả hai repo đã
  gắn. Chi tiết + bằng chứng đo được: xem BH99 trong `CLAUDE.md` của repo EBM gốc. Vấn đề này CHỈ ở
  phiên cloud nhiều-repo — không ảnh hưởng máy Mac/Windows.

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
