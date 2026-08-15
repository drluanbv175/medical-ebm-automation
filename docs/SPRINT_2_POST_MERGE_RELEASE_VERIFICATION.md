# Sprint 2 — Post-Merge Release Verification

**Date:** 2026-06-21  
**Verification performed by:** Claude (Cowork automation)  
**Branch:** `main`  
**HEAD commit verified:** `65b891b`  
**Codebase:** `medical-ebm-automation` (OneDrive-Personal(2)/Claude AI/)  
**Status:** ✅ SPRINT 2 CLOSED

---

## Part A — Git and Branch Verification

| Check | Result |
|---|---|
| Current branch | `main` ✅ |
| HEAD commit | `65b891b` — docs(sprint2): add scope containment verification and final release readiness report ✅ |
| Working tree | Clean — nothing to commit ✅ |
| Stash list | Empty ✅ |
| `feat/research-os` branch | EXISTS at `f3f6da6` ✅ |

### Sprint 2 merge/release commits (recent 10):

```
65b891b docs(sprint2): add scope containment verification and final release readiness report
245cc8b chore(scope): remove Research OS from Sprint 2 release
95b0ff6 feat: add persistent audit write contract
74f5121 feat: guard remaining admin write actions
2b38214 feat: guard patient registration action
dcb86bf feat: guard education template draft action
51bb10b feat: guard care plan draft action
ef12e82 feat: guard appointment creation action
b9dd832 feat: guard overdue task claim action
eb69cde feat: track write action readiness
```

### Key commits:
- **Scope containment:** `245cc8b` — `chore(scope): remove Research OS from Sprint 2 release`
- **Research OS branch tip:** `f3f6da6` — `docs(research-os): add PO disclaimer and module inventory README`
- **Files only on `feat/research-os`:** `app/research_os/` (16 files), `app/dashboard/_research_os_panel.py`, `tests/test_research_os.py`, CLI `research-os`

---

## Part B — Research OS Exclusion Verification: ✅ PASS

| Check | Command | Result |
|---|---|---|
| `app/research_os/` absent | `ls app/research_os/` | **OK: no research_os** ✅ |
| `_research_os_panel.py` absent | `ls app/dashboard/_research_os_panel.py` | **OK: no panel** ✅ |
| No imports/wiring | `grep -r "research_os" app/ --include="*.py"` | **OK: no imports** ✅ |
| No CLI `research-os` in run.py | `grep research_os run.py` | **OK: not present** ✅ |
| No `test_research_os.py` | `ls tests/test_research_os.py` | **OK: no test file** ✅ |
| `feat/research-os` branch exists | `git show feat/research-os` | **EXISTS** at `f3f6da6` ✅ |

**Evidence commit `245cc8b`:**
> "Research OS (app/research_os/, _research_os_panel.py, test_research_os.py, CLI research-os) extracted to feat/research-os branch per PO authorization."

**Verdict: Research OS EXCLUDED from main.** All 16 module files, panel, tests, and CLI wiring confirmed absent.

---

## Part C — Sprint 2 Scope Reconciliation

| # | Authorized Scope Item | Files/Evidence | Status |
|---|---|---|---|
| 1 | **Persistence foundation** — migrations, models, PostgreSQL config | `app/models/` (8 files), `app/database.py`, `app/config.py`, `app/governance/migrations.py` (MIGRATION_ID: v7_phase_2a_governance_20260618, 13 governance tables) | ✅ PRESENT |
| 2 | **Consultation Workspace v1** | Implemented as `app/chronic_care/` (service.py, models.py, dashboard.py, audit.py, rules.py, synthetic_cases.py) + `chronic-care-clinic-os/` Next.js app (full `/app` router with RBAC, care plan, patient education) | ✅ PRESENT (named `chronic_care` in Python, `chronic-care-clinic-os` in Next.js) |
| 3 | **Evidence Card Library v1** | `app/evidence/` — evidence_registry.py, document_provenance.py, citation_verification.py, citation_cache.py, delta_report.py, pathway_impact_analysis.py, hypertension_local_adaptation.py, `app/models/evidence.py` | ✅ PRESENT |
| 4 | **Medication Safety Framework demo** | `app/safety/medication_safety_engine.py` — HIGH_RISK_PAIRS screen, docstring: "không thay thế kiểm tra của bác sĩ/dược sĩ"; `app/safety/red_team.py` | ✅ PRESENT |
| 5 | **Clinical Content Governance** | `app/core/policy_engine.py` (PolicyEngine, PolicyViolation, PolicyDecision), `app/models/governance_v7.py` (13 governance models), `app/core/release_manager.py`, `app/clinical_content/clinical_runtime.py`, `app/export_bridge/chatgpt_project_bridge.py` | ✅ PRESENT |
| 6 | **RBAC, AuditEvent, CSRF/CORS, auth, safety gates** | `app/core/audit_logger.py` (AuditEvent frozen dataclass, JSONL append-only), `app/core/approval_service.py` (reviewer_role: physician/PI/system_owner), `app/models/governance_v7.py` (AuditEventRecord), `chronic-care-clinic-os/lib/audit-storage-contract.ts` (sequence/previousHash/eventHash/immutableAfterAppend), RBAC/CSRF/CORS in Next.js layer | ✅ PRESENT |

**Note on item 6:** CSRF/CORS enforcement là trách nhiệm của lớp Next.js (`chronic-care-clinic-os`); Python layer (`app/`) không expose HTTP server riêng — đây là thiết kế đúng cho monorepo này.

**Note on AuditEvent append-only:** `AuditLogger.log()` chỉ dùng `fh.open("a")` (append), `AuditEvent` là `@dataclass(frozen=True)` — không thể mutate sau khi tạo. `AuditEventRecord` DB model có `updated_at` field (không có DDL-level constraint `immutable`) — cần ghi nhận là **technical debt: DB-level append-only chưa được enforce bằng trigger/DDL**.

---

## Part D — Clinical Safety Verification: ✅ CONFIRMED

| Check | Result |
|---|---|
| `CLINICALLY_APPROVED` seed data | **ABSENT** — không tìm thấy trong toàn bộ `app/` ✅ |
| Demo/mock labels | `app/models/evidence.py`: mock flag field với comment "KHÔNG dùng lâm sàng"; `app/dashboard/main.py` line 687: banner ⚠️ "CHẾ ĐỘ DEMO (USE_MOCK_SOURCES=true)" ✅ |
| Real patient PII | `patient_name` chỉ xuất hiện trong danh sách BLOCKED FIELDS (`shadow_pilot`, `phase_2c_shadow`, `hypertension_pilot_pathway_validator`); `scrub_pii()` function active trong `ambient_scribe.py` ✅ |
| HIS/eHospital integration | Không có integration code. Các hit (`ETHICS_SUBMISSION_CHECKLIST`, `ACCEPTANCE_CHECKLIST`) là chuỗi checklist văn bản, không phải API call ✅ |
| HL7/FHIR | `tests/test_fhir_client.py` — test file cho stub/mock, không có production FHIR client trong `app/` ✅ |

**Clinical safety declaration:**
- Hệ thống là **internal MVP/demo có kiểm soát**
- Không có dữ liệu bệnh nhân thật
- Không có nội dung lâm sàng được phê duyệt lâm sàng
- Các safety gate đang ACTIVE: PolicyEngine blocks PII, unapproved release, missing citation
- Medication Safety Framework ghi rõ "không thay thế bác sĩ/dược sĩ"

---

## Part E — Full Quality Gate Results

| Gate | Tool/Command | Result | Notes |
|---|---|---|---|
| E1 | `git diff --check HEAD` | ✅ PASS | Không có whitespace error |
| E2 | `ruff check app/ tests/` | ✅ PASS — "All checks passed!" | ruff 0.15.x |
| E3 | `mypy app/ --ignore-missing-imports` | ⚠️ 79 errors / 28 files | Xem chi tiết bên dưới |
| E4 | Build step | N/A | Không có `Makefile` / `pyproject.toml` build step — CLI tool, không phải package |
| E5 | `pytest --tb=short -q` | ✅ **311 passed**, 1 warning, 7.52s | |
| E6 | `-k "integration or postgres"` | ✅ **10 passed** | CLI + panel integration tests |
| E7 | `-k "auth or rbac or csrf or cors"` | ⚠️ 0 selected | Python layer không có HTTP auth — RBAC là Next.js layer |
| E8 | `-k "audit"` | ✅ **3 passed** | governance_persistence, chronic_care_safety, v7_control_plane |
| E9 | E2E / Playwright | N/A | Không có `tests/e2e/` directory |
| E10 | `-k "accessibility or axe or a11y"` | N/A | Không có accessibility tests |
| E11 | PII scan | ✅ PASS | `patient_name` chỉ là BLOCKED field list, không phải raw PII |
| E12 | Secret scan | ✅ PASS | Không có hardcoded password/key |
| E13 | `pip-audit` | ⚠️ **36 vulnerabilities** | Xem chi tiết bên dưới |

### E3 — mypy errors detail (technical debt, không block internal demo):

Files với errors chính:
- `app/services/pipeline.py` — 6 errors (type operand `object + int`)
- `app/social/video.py` — 2 errors (Optional IO attribute)
- `app/integrations/image_reading.py` — 3 errors (untyped var, Anthropic model literal)
- `app/integrations/ambient_scribe.py` — 2 errors (untyped sections dict, model literal)
- `app/main.py` — 1 error (untyped `_SOURCE_MAP`)
- `app/dashboard/main.py` — 3 errors (Optional str arg, missing attr, type assignment)
- `app/services/notify.py` — 2 errors (missing stubs: requests, markdown)

**Đánh giá:** Các lỗi mypy chủ yếu là type annotation thiếu và stubs không có — không ảnh hưởng runtime của internal demo. Cần giải quyết trước bất kỳ production release nào.

### E13 — pip-audit vulnerabilities (36 total):

| Package | Current | Advisory | Fix version |
|---|---|---|---|
| pillow | 11.3.0 | 5 CVEs (GHSA-cfh3, GHSA-whj4, GHSA-5xmw, GHSA-r73j, GHSA-pwv6) | 12.2.0 |
| pip | 26.0.1 | 3 (PYSEC-2026-196, GHSA-58qw, GHSA-jp4c) | 26.1.2 |
| pyarrow | 21.0.0 | PYSEC-2026-113 | 23.0.1 |
| pytest | 8.4.2 | GHSA-6w46-j5rx-g56g | 9.0.3 |
| python-dotenv | 1.2.1 | GHSA-mf9w-mj56-hr94 | 1.2.2 |
| requests | 2.32.5 | GHSA-gc5v-m9x4-r6x2 | 2.33.0 |
| setuptools | 58.0.4 | 3 CVEs | 78.1.1 |
| streamlit | 1.50.0 | 2 CVEs | 1.54.0 |
| tornado | 6.5.6 | GHSA-pw6j-qg29-8w7f | 6.5.7 |
| urllib3 | 2.6.3 | 2 CVEs | 2.7.0 |

**Đánh giá:** Pillow CVEs là HIGH severity (image parsing). Tất cả cần được upgrade trước Sprint 3. Không block internal demo vì hệ thống không expose public endpoints.

---

## Part F — Release Declaration

Sprint 2 release được tuyên bố với các điều kiện sau:

- ✅ Sprint 2 là **internal MVP/demo có kiểm soát** — KHÔNG phải production clinical system
- ✅ Không có dữ liệu bệnh nhân thật trong codebase hoặc database seed
- ✅ Không có nội dung lâm sàng được phê duyệt bởi hội đồng lâm sàng
- ✅ Research OS KHÔNG thuộc Sprint 2 release — đang được bảo tồn trên `feat/research-os` (HEAD: `f3f6da6`)
- ✅ Tất cả safety gate (PolicyEngine, AuditLogger, ApprovalService) đang hoạt động
- ✅ Demo banner hiển thị rõ ràng khi USE_MOCK_SOURCES=true
- ⚠️ Mypy: 79 type errors → technical debt Sprint 3
- ⚠️ pip-audit: 36 vulns (pillow HIGH) → upgrade dependencies Sprint 3
- ⚠️ DB-level AuditEvent append-only chưa có DDL trigger → technical debt Sprint 3
- ⚠️ Không có E2E / a11y / auth Python tests → scope gap Sprint 3

---

## Part G — Test Totals by Group

| Group | Tests | Result |
|---|---|---|
| Full suite | 311 | ✅ 311 passed |
| phase_2 (governance, persistence, live source, migration, citation, export, dashboard) | 51 | ✅ 51 passed |
| phase_3 (chronic care functional, red team, safety) | 20 | ✅ 20 passed |
| Integration (CLI + panel) | 10 | ✅ 10 passed |
| Audit | 3 | ✅ 3 passed |
| Safety/governance/PII/v7 | 78 | ✅ 78 passed |
| Auth/RBAC/CSRF (Python layer) | 0 selected | ⚠️ N/A — implemented in Next.js |
| E2E Playwright | N/A | No `tests/e2e/` |
| Accessibility | N/A | No a11y tests |

---

## Part H — Technical Debt Còn Lại

| # | Item | Severity | Owner Sprint 3 |
|---|---|---|---|
| TD-01 | mypy: 79 type errors (pipeline, video, integrations, dashboard) | Medium | Dev |
| TD-02 | pip-audit: 36 vulnerabilities — pillow HIGH, streamlit, requests, urllib3 | High | DevOps |
| TD-03 | AuditEventRecord: không có DB-level DDL constraint append-only (chỉ có application-level) | High (pre-production) | Dev |
| TD-04 | Không có E2E / Playwright tests | Medium | QA |
| TD-05 | Không có accessibility tests | Low | QA |
| TD-06 | Không có Python-layer auth/RBAC/CSRF tests (Next.js có nhưng không chạy qua pytest) | Medium | Dev |
| TD-07 | `AuditEventRecord.updated_at` tồn tại — cần review xem có path nào update record không | Medium | Dev |
| TD-08 | `app/integrations/image_reading.py`: Anthropic model literal type mismatch (cần cập nhật model string) | Low | Dev |

---

## Part I — Final Status

```
╔══════════════════════════════════════════════════════════╗
║           SPRINT 2 CLOSED — INTERNAL DEMO READY         ║
║                                                          ║
║  Branch:    main @ 65b891b                               ║
║  Tests:     311 / 311 PASSED                             ║
║  Ruff:      ALL CHECKS PASSED                            ║
║  Research OS: EXCLUDED (on feat/research-os)             ║
║  Clinical Safety: CONFIRMED                              ║
║                                                          ║
║  INTERNAL MVP/DEMO ONLY — NOT FOR CLINICAL USE           ║
║  Pending TD-01..TD-08 before any production gate         ║
╚══════════════════════════════════════════════════════════╝
```

**Release tag:** `sprint-2-internal-demo` → `65b891b`
