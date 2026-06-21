# Sprint 2 — Scope Containment & Semantic Verification

**Date:** 2026-06-21  
**Branch:** `main` (Sprint 2 release)  
**Commit:** `245cc8b` — chore(scope): remove Research OS from Sprint 2 release  
**PO Authorization:** Sprint 2 Scope Containment (verbal + written authorization)

---

## 1. Decision Context

Product Owner (Dr. Luân) authorized formal scope containment per Sprint 2 release readiness review. Research OS was built ahead of PO approval, in violation of Sprint 2 boundary. Decision: extract Research OS to `feat/research-os`, preserve all work without deletion, then clean `main` to Sprint 2 boundary.

**Absolute rules enforced:**
- KHÔNG xóa vĩnh viễn bất kỳ công việc Research OS nào ✅
- Không force push ✅
- Không reset phá hủy lịch sử ✅
- Không merge Sprint 2 ✅
- Không bắt đầu Sprint 3 ✅
- Không thêm tính năng mới ✅

---

## 2. Baseline (Before Containment)

| Item | Value |
|------|-------|
| HEAD commit before | `95b0ff6` — feat: add persistent audit write contract |
| Research OS first commit | `ceafa3f` — feat: sync chronic care clinic OS |
| Branches | `main` only |
| Untracked Research OS files | `app/dashboard/_research_os_panel.py`, `tests/test_research_os.py` |
| Research OS in HEAD (tracked) | `app/research_os/` — 16 files |

---

## 3. Scope Containment Steps Executed

### Bước 1: Tạo feat/research-os branch
- Created `feat/research-os` from HEAD (`95b0ff6`) → captured all Research OS in working tree
- Committed: 16 `app/research_os/` files, `_research_os_panel.py`, `test_research_os.py`, wiring in `app/__init__.py`, `run.py`, `app/dashboard/main.py`, `RESEARCH_OS_README.md`, Sprint 2 docs
- Branch preserved intact with full PO disclaimer

### Bước 2: Làm sạch main
Files removed from Sprint 2 release:

| File | Action |
|------|--------|
| `app/research_os/` (16 files) | `git rm -r` |
| `app/dashboard/_research_os_panel.py` | `rm -f` (untracked) |
| `tests/test_research_os.py` | `rm -f` (untracked) |
| `app/__init__.py` | Auto-reverted (wiring was working-tree only) |
| `run.py` | Auto-reverted (CLI block was working-tree only) |
| `app/dashboard/main.py` | Auto-reverted (panel call was working-tree only) |
| `tests/test_v7_evidence_safety_research.py` | Removed 9 research_os imports + 1 test function |
| `app/dashboard/v7_registry.py` | Removed `DashboardSection("research_os", ...)` |
| `tests/test_phase_2b_shadow_research_red_team.py` | Removed research_os import + `test_researchos_pilot_*` function |
| `app/research_os/__pycache__/` | `rm -rf` |

### Bước 3: Commit
```
chore(scope): remove Research OS from Sprint 2 release

Research OS (app/research_os/, _research_os_panel.py, test_research_os.py,
CLI research-os) extracted to feat/research-os branch per PO authorization.

Sprint 2 scope: persistence foundation, consultation workspace,
evidence card library, medication safety demo, RBAC, audit, safety gates.

No clinical safety, RBAC, AuditEvent, or persistence changes.
```
**Commit hash:** `245cc8b` — 19 files changed, 512 deletions(-)

---

## 4. Semantic Verification

### 4.1 Research OS grep (Sprint 2 source .py files)
```
grep -r 'research_os' app/ tests/ --include='*.py'
→ CLEAN: no research_os refs in .py files
```

### 4.2 Sprint 2 scope integrity
Files NOT modified (confirmed via git log):
- `app/safety/` — all safety engines unchanged
- `app/clinical_content/` — unchanged  
- `app/evidence/` — unchanged
- `app/rbac/` — unchanged
- `app/audit/` — unchanged
- `app/persistence/` — unchanged

### 4.3 feat/research-os integrity
```
git show feat/research-os:app/research_os/__init__.py
→ """Research Operating System V7 — public API...
```
All 16 research_os modules present and intact on `feat/research-os`.

---

## 5. Sprint 2 Scope Boundary (Confirmed)

| Component | In Sprint 2 | Status |
|-----------|------------|--------|
| Persistence foundation (SQLAlchemy/SQLite) | ✅ | Retained |
| Consultation workspace | ✅ | Retained |
| Evidence card library | ✅ | Retained |
| Medication safety demo | ✅ | Retained |
| RBAC | ✅ | Retained |
| Audit trail (AuditEvent) | ✅ | Retained |
| Safety gates (red flag, referral, data sufficiency) | ✅ | Retained |
| Research OS (G0–G9, SAP engine, design router) | ❌ | Extracted to feat/research-os |

---

*Generated: 2026-06-21 | PO Sprint 2 Scope Containment Authorization*
