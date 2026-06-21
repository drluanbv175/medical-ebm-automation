# Sprint 2 Final Release Readiness Review

**Date:** 2026-06-21  
**Codebase:** `medical-ebm-automation`  
**Policy:** KHÔNG merge, KHÔNG bắt đầu Sprint 3 cho đến khi review này hoàn tất và blockers được giải quyết.  
**Phương pháp:** Chỉ dùng evidence từ code/test/file thực tế. Mỗi claim có file path + dòng code hoặc test name. Không có evidence → "Evidence not found" + NOT READY. Không verify được → `[CẦN KIỂM CHỨNG]`.

---

## TÓM TẮT ĐIỀU HÀNH

| Hạng mục | Kết quả |
|---|---|
| Tổng tests | 402 |
| PASSED | **402** ✅ (sau remediation 2026-06-21) |
| FAILED | **0** ✅ (was 1 — đã remediate) |
| Test FAILED thuộc Sprint 2 in-scope? | N/A — đã resolved |
| ADR-008/ADR-009 tìm thấy? | **Evidence not found** |
| "Consultation Workspace v1" tìm thấy? | **Evidence not found** |
| RBAC (main Python project) | **NOT IMPLEMENTED** |
| AuditEvent append-only (DB-level) | **Behavioral only — không có DDL enforcement** |
| Scope drift | YES — Tab 6 + research_os 15 modules shipped |
| TODO/FIXME/HACK trong app/ | 0 |

### 🔴 KHUYẾN NGHỊ: **NO-GO**

4 blockers phải được giải quyết trước khi release. Xem mục H.

---

## A. TEST SUITE RESULTS

### A.1 Grand Total

```
402 tests total — 401 PASSED, 1 FAILED
```

Source: `python3 -m pytest --tb=short -q` chạy 2026-06-21.

### A.2 Phân nhóm theo file

Kết quả chạy lệnh:
```
python3 -m pytest tests/test_phase_2a_*.py tests/test_phase_2b_*.py \
  tests/test_phase_2c_*.py tests/test_phase_2d_*.py \
  tests/test_v7_core_control_plane.py tests/test_v7_evidence_safety_research.py \
  tests/test_v7_export_bridge_and_clinical_runtime.py \
  tests/test_phase_3a_chronic_care_*.py \
  tests/test_pii_adversarial.py tests/test_group_a_safety.py tests/test_pipeline_db.py
```
Kết quả: **1 failed, 121 passed**

```
python3 -m pytest tests/test_research_os.py --tb=no -q
```
Kết quả: **89 passed** (OUT OF SCOPE)

| File | Tests | Status | Nhóm |
|---|---|---|---|
| test_phase_2a_governance_persistence.py | ~5 | ✅ PASS | Sprint 2 core |
| test_phase_2b_*.py | ~33 | ✅ PASS | Sprint 2 core |
| test_phase_2c_pack_selection_and_pathway.py | 2 | ✅ PASS | Sprint 2 core |
| test_phase_2c_shadow_and_vignettes.py | 2 | ✅ PASS | Sprint 2 core |
| test_phase_2d_evidence_readiness.py | 8 | ✅ PASS | Sprint 2 core |
| test_v7_core_control_plane.py | 6 | ✅ PASS | Sprint 2 core |
| **test_v7_evidence_safety_research.py** | **5** | **4 PASS / 1 FAIL** | Sprint 2 + OUT-OF-SCOPE mix |
| test_v7_export_bridge_and_clinical_runtime.py | 4 | ✅ PASS | Sprint 2 core |
| test_phase_3a_chronic_care_functional.py | 7 | ✅ PASS | Sprint 3 shadow |
| test_phase_3a_chronic_care_red_team.py | 7 | ✅ PASS | Sprint 3 safety |
| test_phase_3a_chronic_care_safety.py | 6 | ✅ PASS | Sprint 3 safety |
| test_pii_adversarial.py | 20 | ✅ PASS | Security |
| test_group_a_safety.py | 12 | ✅ PASS | Safety |
| test_pipeline_db.py | 4 | ✅ PASS | DB |
| **test_research_os.py** | **89** | ✅ PASS | **OUT OF SCOPE** |

### A.3 FAILED Test — Chi tiết

**File:** `tests/test_v7_evidence_safety_research.py`  
**Test:** `test_research_os_gates_design_protocol_sap_and_data_lock`  
**Line:** 103  

```
AssertionError: assert 'CONSORT 2010' == 'CONSORT'
  - CONSORT
  + CONSORT 2010
```

**Root cause:** `reporting_guideline_for_design()` trong `app/research_os/reporting_guideline_mapper.py` trả về chuỗi `'CONSORT 2010'` nhưng assertion mong đợi `'CONSORT'`.

**Đánh giá:**
- Module được test (`app.research_os.reporting_guideline_mapper`) thuộc research_os — **OUT OF SCOPE Sprint 2**
- Tuy nhiên test **NẰM TRONG** `tests/test_v7_evidence_safety_research.py` — file này chứa hỗn hợp in-scope và out-of-scope tests
- File này shipped cùng codebase; `pytest` chạy toàn bộ **SẼ FAIL**
- Đây là **BLOCKER #1**: clean `pytest` không thể pass

**Hướng sửa (2 lựa chọn):**
1. Chuyển test này sang `tests/test_research_os.py` (preferred)
2. Đánh dấu `@pytest.mark.xfail(reason="research_os out-of-scope; CONSORT version string TBD")`

---

## B. SCOPE RECONCILIATION

Sprint 2 Approved Scope — từng item đối chiếu với file thực tế.

### B.1 Persistence Foundation (ADR-008 / ADR-009)

| Claim | Evidence | Verdict |
|---|---|---|
| ADR-008 exists | `grep -r "ADR-008"` trong toàn bộ repo → 0 results | ❌ Evidence not found |
| ADR-009 exists | `grep -r "ADR-009"` trong toàn bộ repo → 0 results | ❌ Evidence not found |
| Governance schema (13 tables) | `app/models/governance_v7.py` (278+ lines) | ✅ EXISTS |
| SQLAlchemy ORM migration | `app/governance/migrations.py`: `MIGRATION_ID = "v7_phase_2a_governance_20260618"` | ✅ EXISTS |
| Persistence tests | `tests/test_phase_2a_governance_persistence.py` (5 tests: migration additive, no PII columns, audit INSERT, state transitions, evidence history) — PASS | ✅ VERIFIED |

**Verdict: PARTIAL — BLOCKER #2**  
Persistence infrastructure EXISTS và hoạt động. Tuy nhiên ADR-008/ADR-009 — hai tài liệu kiến trúc được Sprint 2 scope document tham chiếu như nền tảng — **không tìm thấy ở bất kỳ đâu trong codebase** (không phải docs/, không phải README, không phải comments). Không thể verify persistence architecture được design đúng theo specification đã khai báo. `[CẦN KIỂM CHỨNG]`

---

### B.2 Consultation Workspace v1

| Claim | Evidence | Verdict |
|---|---|---|
| File/class "Consultation Workspace" | `grep -ri "consultation_workspace\|ConsultationWorkspace\|consultation workspace"` → 0 results | ❌ Evidence not found |
| Docs về Consultation Workspace | `ls docs/` → không có file liên quan | ❌ Evidence not found |
| Closest match | `app/dashboard/v7_readonly.py` (164 lines) — V7 Shadow Governance read-only panel | Candidate [CẦN KIỂM CHỨNG] |

**Verdict: MISSING — BLOCKER #3**  
Tên "Consultation Workspace v1" không xuất hiện trong bất kỳ file Python, tài liệu, hay comment nào trong codebase. Không xác định được đây là scope item chưa implement hay đã implement dưới tên khác. `[CẦN KIỂM CHỨNG]` — cần PO xác nhận.

---

### B.3 Evidence Card Library v1

| Claim | Evidence | Verdict |
|---|---|---|
| Core dataclass | `app/clinical_content/recommendation_card.py` (21 lines): `ClinicalRecommendationCard` frozen dataclass | ✅ EXISTS |
| "Evidence Card Library" name | `grep -ri "evidence_card_library\|EvidenceCardLibrary\|evidence card library"` → 0 results | ❌ Name not found |
| Library/catalog infrastructure | Không có bulk ops, search, pagination | ❌ MISSING |

**Verdict: PARTIAL**  
Core dataclass tồn tại nhưng không có "library" infrastructure (catalog, search, bulk operations). Tên không khớp với scope document.

---

### B.4 Medication Safety Framework v1 (technical demo/test only)

| Claim | Evidence | Verdict |
|---|---|---|
| Implementation | `app/safety/medication_safety_engine.py` (38 lines) | ✅ EXISTS |
| 7 HIGH_RISK_PAIRS | Lines 10–20: warfarin/nsaid, anticoagulant/antiplatelet, acei/arb, nitrate/pde5, ckd/nsaid, liver_disease/hepatotoxic, pregnancy/teratogenic | ✅ VERIFIED |
| Test coverage | `tests/test_v7_evidence_safety_research.py::test_safety_kernel_checks_high_risk_drug_pairs` — PASS | ✅ VERIFIED |
| Demo scope (no Patient360) | Không có Patient360/CarePlan/lab/vital integration | ✅ CONFIRMED demo-only |
| CLINICALLY_APPROVED marker | Pure keyword matching; không có clinical decision integration | ✅ APPROPRIATE scope |

**Verdict: COMPLETE (within demo scope)**

---

### B.5 Clinical Content Governance

| Claim | Evidence | Verdict |
|---|---|---|
| PolicyEngine | `app/core/policy_engine.py` (169 lines) | ✅ EXISTS |
| Policy gates | EBM-V7-P001 (PII), P002 (traceability), P003 (recommendation), P004 (citation), P005 (grade), P006 (physician_approved), P007 (clinical_release) | ✅ VERIFIED |
| Evidence lifecycle | `app/evidence/evidence_lifecycle.py`: `verify_evidence()`, `retract_evidence()`, `supersede_evidence()` | ✅ EXISTS |
| Governance repository | `app/governance/repository.py` (228 lines): 13 GOVERNANCE_TABLES | ✅ EXISTS |
| Tests | `tests/test_v7_core_control_plane.py` (6 tests PASS), `tests/test_v7_evidence_safety_research.py` (4 in-scope PASS) | ✅ VERIFIED |

**Verdict: COMPLETE**

---

### B.6 RBAC

| Claim | Evidence | Verdict |
|---|---|---|
| User-role RBAC trong app/ | `grep -r "require_role\|@rbac\|user_role\|RoleCheck\|has_permission"` trong app/ → 0 results | ❌ NOT FOUND |
| Authentication layer trong app/ | `grep -r "login_required\|jwt_required\|session.user"` trong app/ → 0 results | ❌ NOT FOUND |
| PolicyEngine (content governance) | `app/core/policy_engine.py`: blocks by content policy, không phải user roles | ✅ Exists (khác concept) |
| RBAC trong chronic-care-clinic-os | `chronic-care-clinic-os/PRODUCTION_BLOCKERS.md`: "RBAC modeled but not wired to every route/action" | PARTIAL — NOT production-ready |

**Verdict: NOT READY — BLOCKER #4**  
User-role RBAC không implement trong main Python project. PolicyEngine là content-safety governance (một khái niệm khác, không thay thế RBAC). `chronic-care-clinic-os` có RBAC model nhưng chính `PRODUCTION_BLOCKERS.md` xác nhận: "not wired to every route/action", "authentication/MFA not implemented".

---

### B.7 AuditEvent Append-Only

| Layer | Evidence | Status |
|---|---|---|
| Application — JSONL file | `app/core/audit_logger.py` ~line 28: `self.path.open("a", encoding="utf-8")` | ✅ Behavioral append-only |
| Application — ORM INSERT | `app/governance/repository.py` `audit()`: `session.add()` only; no UPDATE/DELETE on audit_events | ✅ Behavioral insert-only |
| ORM model — schema gap | `app/models/governance_v7.py`: `AuditEventRecord.updated_at = mapped_column(DateTime, onupdate=_utcnow)` | ⚠️ RISK — SQLAlchemy CÓ THỂ update |
| Database layer — DDL enforcement | `grep -r "TRIGGER\|RULE\|ROW SECURITY\|immutable"` trong app/ → 0 results | ❌ NOT FOUND |

**Verdict: PARTIAL — MEDIUM RISK**  
Append-only hiện tại là **behavioral convention only**. `AuditEventRecord.updated_at` với `onupdate=_utcnow` tạo ra kẽ hở: nếu có bất kỳ code nào vô tình gọi ORM update trên audit record, timestamp sẽ thay đổi mà không có cảnh báo. Không có DDL trigger, Postgres RLS, hay view constraint ngăn chặn ở DB level.

**Chấp nhận được** trong shadow/demo mode. **Phải sửa** trước production.

---

### B.8 Versioning

| Claim | Evidence | Verdict |
|---|---|---|
| Schema version ID | `app/governance/migrations.py`: `MIGRATION_ID = "v7_phase_2a_governance_20260618"` | ✅ EXISTS |
| Record versioning | `app/models/governance_v7.py`: `version` column trên `AuditEventRecord` | ✅ EXISTS |

**Verdict: PARTIAL** — Versioning cơ bản tồn tại. Không có full version-diff hay rollback capability.

---

### B.9 Lifecycle (Evidence)

| Claim | Evidence | Verdict |
|---|---|---|
| 3 state transitions | `app/evidence/evidence_lifecycle.py`: `verify_evidence()`, `retract_evidence()`, `supersede_evidence()` | ✅ EXISTS |
| State machine | QUARANTINED → VERIFIED → RETRACTED/SUPERSEDED | ✅ VERIFIED |
| Tests | `tests/test_v7_evidence_safety_research.py::test_evidence_lifecycle_transitions` — PASS | ✅ VERIFIED |

**Verdict: COMPLETE**

---

### B.10 API

| Claim | Evidence | Verdict |
|---|---|---|
| CAFÉ-S CLI | `app/integrations/cli.py`: tools drug/soap/image/fhir | ✅ EXISTS |
| REST API server | `grep -r "FastAPI\|Flask\|APIRouter\|@app.route"` trong app/ | Evidence not found `[CẦN KIỂM CHỨNG]` |

**Verdict: PARTIAL** — CLI integration tồn tại. REST API không có evidence.

---

### B.11 UI Quản Trị

| Claim | Evidence | Verdict |
|---|---|---|
| V7 Shadow read-only panel | `app/dashboard/v7_readonly.py` (164 lines) | ✅ EXISTS |
| Tích hợp vào dashboard | `app/dashboard/main.py`: Tab 13 = `"🛡️ 13. V7 Shadow Read-only"` | ✅ VERIFIED |
| Write flags tắt | `v7_readonly.py`: tất cả clinical/write flags hardcoded OFF | ✅ VERIFIED |

**Verdict: COMPLETE** (read-only admin UI)

---

### B.12 Safety Gates

| Claim | Evidence | Verdict |
|---|---|---|
| Feature flags default OFF | `tests/test_v7_core_control_plane.py::test_v7_feature_flags_default_to_safe_off`: v7_auto_apply_recommendations=False, v7_clinical_release=False, v7_chatgpt_project_export=False — PASS | ✅ VERIFIED |
| Policy blocking gates | `app/core/policy_engine.py`: P001–P007 | ✅ EXISTS |
| Release requires approval + flag | `tests/test_v7_core_control_plane.py::test_release_requires_approval_and_enabled_flag` — PASS | ✅ VERIFIED |
| PII blocking | `tests/test_v7_core_control_plane.py::test_policy_engine_blocks_pii_missing_trace_and_unapproved_release` — PASS | ✅ VERIFIED |

**Verdict: COMPLETE**

---

### B.13 Tổng hợp Scope Reconciliation

| Sprint 2 Item | Verdict |
|---|---|
| Persistence foundation (ADR-008/ADR-009) | ⚠️ PARTIAL — infrastructure ✅, ADR docs ❌ |
| Consultation Workspace v1 | ❌ MISSING — Evidence not found `[CẦN KIỂM CHỨNG]` |
| Evidence Card Library v1 | ⚠️ PARTIAL — dataclass ✅, library ❌ |
| Medication Safety Framework v1 | ✅ COMPLETE (demo scope) |
| Clinical Content Governance | ✅ COMPLETE |
| RBAC | ❌ NOT READY — không implement trong main project |
| AuditEvent append-only | ⚠️ PARTIAL — behavioral only, no DB enforcement |
| Versioning | ⚠️ PARTIAL |
| Lifecycle | ✅ COMPLETE |
| API | ⚠️ PARTIAL — CLI ✅, REST API unverified |
| UI quản trị | ✅ COMPLETE (read-only) |
| Safety gates | ✅ COMPLETE |

---

## C. CLINICAL SAFETY VERIFICATION

### C.1 Clinical Mode Markers

| Module / Component | Mode | Evidence |
|---|---|---|
| Medication Safety Engine | **DEMO** — keyword matching only | `app/safety/medication_safety_engine.py` (38 lines): no Patient360, no lab integration |
| ClinicalRecommendationCard | Frozen dataclass — không auto-apply | `app/clinical_content/recommendation_card.py` |
| V7 Shadow UI (Tab 13) | **SHADOW READ-ONLY** — all write flags OFF | `app/dashboard/v7_readonly.py` |
| Chronic Care (Tab 14) | **SHADOW PILOT** — no clinical writes | `app/dashboard/main.py`: "🫀 14. Chronic Care Shadow Pilot" |
| ResearchOS (Tab 6) | **OUT OF SCOPE** — shipped với disclaimer | `app/dashboard/_research_os_panel.py`: "Không lưu dữ liệu bệnh nhân (PII). Không thay thế phán đoán chuyên môn." |

### C.2 Feature Flags — Tất cả DEFAULT OFF

Verified bằng test: `tests/test_v7_core_control_plane.py::test_v7_feature_flags_default_to_safe_off` — **PASS**

```python
v7_auto_apply_recommendations = False
v7_clinical_release = False
v7_chatgpt_project_export = False
```

### C.3 Medication Safety — Scope Boundary

Confirmed: kỹ thuật demo, 7 HIGH_RISK_PAIRS keyword matching chỉ. Không có:
- Patient360 integration
- Lab/vital data integration
- CarePlan integration
- Automatic clinical decision output

**Lưu ý:** Cần verify Tab 3 "Drug Safety" trong dashboard không truyền patient data thực vào medication_safety_engine. `[CẦN KIỂM CHỨNG]`

---

## D. SECURITY & PERSISTENCE VERIFICATION

### D.1 AuditEvent Append-Only — Gap Analysis

| Layer | Mechanism | Status |
|---|---|---|
| Application (JSONL write) | `open("a", encoding="utf-8")` — `app/core/audit_logger.py` line ~28 | ✅ Behavioral |
| Application (ORM) | `session.add()` only — `app/governance/repository.py` `audit()` | ✅ Behavioral |
| ORM schema | `AuditEventRecord.updated_at = mapped_column(DateTime, onupdate=_utcnow)` — `governance_v7.py` | ⚠️ SQLAlchemy CÓ THỂ update nếu có bug |
| Database DDL | DDL trigger / Postgres RLS / immutable view | ❌ Evidence not found |

**Khuyến nghị trước production:** Xóa `onupdate=_utcnow` khỏi `AuditEventRecord` HOẶC thêm DB-level constraint.

### D.2 RBAC / Authentication

| Item | Evidence | Status |
|---|---|---|
| User authentication | Không tìm thấy trong app/ | ❌ NOT IMPLEMENTED |
| Role-based access control | Không tìm thấy `require_role`, `@rbac` trong app/ | ❌ NOT IMPLEMENTED |
| Content policy enforcement | `app/core/policy_engine.py` P001–P007 | ✅ (khác với RBAC) |
| Session management | Streamlit default session state | Behavioral |

### D.3 PII Protection

| Item | Evidence | Status |
|---|---|---|
| Scrubbing patterns | `app/core/audit_logger.py`: patterns `_EMAIL`, `_PHONE`, `_MRN`, `_DOB` | ✅ EXISTS |
| Adversarial tests | `tests/test_pii_adversarial.py` 20 tests — ALL PASS | ✅ VERIFIED |
| No PII columns in governance tables | `tests/test_phase_2a_governance_persistence.py` — PASS | ✅ VERIFIED |
| PII block via PolicyEngine | EBM-V7-P001: PII detected → block | ✅ VERIFIED |

---

## E. SCOPE DRIFT AUDIT

### E.1 Out-of-Scope Items Shipped với Codebase

| Item | Location | Shipped? | Risk |
|---|---|---|---|
| research_os — 15 modules | `app/research_os/` (causal_inference, data_lock, design_router, sap_engine, ...) | ✅ YES | MEDIUM |
| Dashboard Tab 6 "Research" | `app/dashboard/main.py` line ~697 + `app/dashboard/_research_os_panel.py` | ✅ YES | LOW (has disclaimer) |
| Failing test trong in-scope file | `tests/test_v7_evidence_safety_research.py:103` tests `app.research_os.*` | ✅ YES | **HIGH — BLOCKER** |
| chronic-care-clinic-os (sub-project) | `chronic-care-clinic-os/` | ✅ YES (separate dir) | LOW |

### E.2 Dashboard Tab Count Discrepancy

| | Evidence |
|---|---|
| Comment trong `app/dashboard/main.py` | `"12 tab theo đề bài"` |
| Thực tế `st.tabs()` | 14 tabs |
| 2 tabs không được documentation | Tab 13 "V7 Shadow Read-only", Tab 14 "Chronic Care Shadow Pilot" |

Tabs thực tế:
```
"1. Executive", "2. Weekly EBM", "3. Drug Safety", "4. Antibiotics",
"5. Guidelines", "6. Research", "7. Clinical Scores", "8. Source Log", "9. Change Log",
"📱 10. TikTok", "📚 11. Tổng hợp RAG", "🧭 12. Evidence Workbench",
"🛡️ 13. V7 Shadow Read-only", "🫀 14. Chronic Care Shadow Pilot"
```

---

## F. TECHNICAL DEBT AUDIT

### F.1 TODO / FIXME / HACK

```
grep -r "TODO\|FIXME\|HACK" app/ → 0 results
```

**Verdict: Không có technical debt markers trong app/.**

### F.2 Code Quality Concerns

| File | Concern | Risk Level |
|---|---|---|
| `app/models/governance_v7.py` | `AuditEventRecord.updated_at` với `onupdate=_utcnow` | MEDIUM |
| `app/dashboard/main.py` | Comment "12 tab" vs 14 tabs thực tế | LOW |
| `tests/test_v7_evidence_safety_research.py` | Mix in-scope và out-of-scope tests trong cùng 1 file | HIGH (gây 1 failing test) |
| `app/safety/medication_safety_engine.py` | 38 lines — pure keyword matching, no input type validation | LOW (demo scope, acceptable) |
| `Plans.md` | Sử dụng Phase 0–4 terminology, không có "Sprint 2" terminology | LOW (documentation inconsistency) |

---

## G. ISSUES LOG

| # | Issue | Severity | File / Location | Status |
|---|---|---|---|---|
| 1 | 1 FAILING TEST — `'CONSORT 2010' != 'CONSORT'` | **BLOCKER** | `tests/test_v7_evidence_safety_research.py:103` | 🔴 OPEN |
| 2 | ADR-008/ADR-009 không tìm thấy trong codebase | **BLOCKER** | N/A — zero grep results | 🔴 OPEN |
| 3 | "Consultation Workspace v1" không tồn tại | **BLOCKER** | N/A — zero grep results | 🔴 OPEN |
| 4 | RBAC không implement trong main Python project | **BLOCKER** | `app/` | 🔴 OPEN |
| 5 | `AuditEventRecord.updated_at` với `onupdate` — không có DB-level immutability | MEDIUM | `app/models/governance_v7.py` | 🟡 OPEN |
| 6 | Dashboard comment "12 tab" vs 14 tabs thực tế | LOW | `app/dashboard/main.py` | 🟢 OPEN |
| 7 | Tab 6 "Research" + research_os shipped nhưng out-of-scope | LOW | `app/dashboard/main.py`, `app/research_os/` | 🟢 ACCEPTABLE (has disclaimer) |
| 8 | `Plans.md` dùng Phase 0–4, không có "Sprint" terminology | LOW | `Plans.md` | 🟢 OPEN |

---

## H. GO / NO-GO RECOMMENDATION

### H.1 Verdict: 🔴 NO-GO

**4 Blockers phải được giải quyết trước khi release:**

---

**BLOCKER 1 — 1 FAILING TEST (phải fix để pass clean `pytest`)**

File: `tests/test_v7_evidence_safety_research.py:103`  
Test: `test_research_os_gates_design_protocol_sap_and_data_lock`  
Error: `assert 'CONSORT 2010' == 'CONSORT'`

Test này nằm trong file sprint-2-core, import out-of-scope `app.research_os` module, và FAIL. Bất kỳ AI/human nào chạy `pytest` sẽ thấy build màu đỏ. Không thể release với failing test trong shipped code.

*Fix: chuyển sang `tests/test_research_os.py` HOẶC `@pytest.mark.xfail`*

---

**BLOCKER 2 — ADR-008/ADR-009 không tồn tại**

Sprint 2 scope document khai báo persistence foundation theo "ADR-008/ADR-009". Hai tài liệu này không tồn tại trong codebase. Không thể verify architecture đã được design theo specification.

*Fix: tạo `docs/adr/ADR-008-*.md` và `ADR-009-*.md` mô tả persistence design, HOẶC confirm ADR đã đổi tên/số và update scope document.*

---

**BLOCKER 3 — "Consultation Workspace v1" không tồn tại**

Sprint 2 scope item "Consultation Workspace v1" không tìm thấy ở bất kỳ đâu trong codebase. Không biết đây là scope chưa implement hay đã implement dưới tên khác.

*Fix: PO xác nhận item này = `v7_readonly.py` (đổi tên) HOẶC xác nhận deferred sang Sprint 3.*

---

**BLOCKER 4 — RBAC không implement trong main project**

Sprint 2 scope bao gồm RBAC. Main Python project không có user-role access control (không có `require_role`, `@rbac`, authentication layer). PolicyEngine là content-safety governance — đây là một khái niệm khác, không thay thế RBAC. `chronic-care-clinic-os` có RBAC model nhưng `PRODUCTION_BLOCKERS.md` xác nhận "not wired to every route/action."

*Fix: Document rõ ràng RBAC intent — nếu PolicyEngine là intentional substitute cho user-role RBAC trong shadow mode, cần có ADR giải thích; nếu RBAC thực sự missing, cần implement hoặc scope lại.*

---

### H.2 Điều kiện để CONDITIONAL GO

| # | Action | Priority | Owner |
|---|---|---|---|
| 1 | Fix/xfail `test_research_os_gates_design_protocol_sap_and_data_lock` | **MUST** ✅ RESOLVED 2026-06-21 | Dev |
| 2 | Tạo ADR-008/ADR-009 OR update scope document với đúng tham chiếu | **MUST** | Architect |
| 3 | Clarify "Consultation Workspace v1" — rename confirm OR scope deferred | **MUST** | PO |
| 4 | Document RBAC decision — PolicyEngine-as-governance đủ cho shadow mode, với ADR | **MUST** | Architect |
| 5 | Xóa `onupdate=_utcnow` khỏi `AuditEventRecord` OR thêm DB-level constraint | SHOULD | Dev |
| 6 | Tách file `test_v7_evidence_safety_research.py` — move research_os tests sang `test_research_os.py` | SHOULD | Dev |
| 7 | Sửa comment "12 tab" → "14 tab" trong `app/dashboard/main.py` | NICE-TO-HAVE | Dev |

---

### H.3 Những gì ĐÃ READY (strengths)

- ✅ Governance schema V7 đầy đủ (13 tables, migration helper)
- ✅ PolicyEngine với 7 content-safety gates (P001–P007)
- ✅ Evidence lifecycle hoàn chỉnh (QUARANTINED → VERIFIED → RETRACTED/SUPERSEDED)
- ✅ Medication Safety Framework v1 đúng demo scope (38 lines, keyword matching, không over-engineer)
- ✅ Feature flags tất cả DEFAULT OFF (safety-first architecture)
- ✅ PII protection đa lớp + 20 adversarial tests ALL PASS
- ✅ V7 Shadow read-only UI (Tab 13) với tất cả write flags OFF
- ✅ AuditEvent behavioral append-only (JSONL + INSERT-only ORM)
- ✅ **402/402 tests pass (100% pass rate)** — sau Single Test Failure Remediation 2026-06-21
- ✅ 0 TODO/FIXME/HACK trong app/
- ✅ Chronic care safety tests (20 tests PASS — shadow mode boundaries enforced)

---

---

## I. SINGLE TEST FAILURE REMEDIATION (2026-06-21)

### I.1 Test fail ban đầu

| Field | Giá trị |
|---|---|
| Test name | `test_research_os_gates_design_protocol_sap_and_data_lock` |
| File | `tests/test_v7_evidence_safety_research.py`, line 103 |
| Error | `AssertionError: assert 'CONSORT 2010' == 'CONSORT'` |
| Reproducible | YES — 3/3 lần chạy đều fail |

### I.2 Root Cause

`app/research_os/reporting_guideline_mapper.py` line 12 trả về `"CONSORT 2010"` thay vì `"CONSORT"`. Suffix `" 2010"` vi phạm contract test strict equality (`==`). Chuỗi `"CONSORT 2010"` chỉ xuất hiện tại **1 file duy nhất** trong toàn codebase. `"CONSORT 2010"` còn là outdated (CONSORT 2025 đã published tháng 5/2025).

### I.3 File đã sửa

| File | Dòng | Thay đổi |
|---|---|---|
| `app/research_os/reporting_guideline_mapper.py` | 12 | `"CONSORT 2010"` → `"CONSORT"` |

**Chỉ 1 file, 1 dòng. Không thêm chức năng mới.**

### I.4 Evidence trước/sau

**Trước fix:**
```
FAILED tests/test_v7_evidence_safety_research.py::test_research_os_gates_design_protocol_sap_and_data_lock
AssertionError: assert 'CONSORT 2010' == 'CONSORT'
402 tests: 401 passed, 1 failed
```

**Sau fix (verified 3/3 lần):**
```
PASSED tests/test_v7_evidence_safety_research.py::test_research_os_gates_design_protocol_sap_and_data_lock
402 tests: 402 passed, 0 failed — 7.20s
```

### I.5 Tổng test cuối

```
402 passed, 0 failed, 1 warning (urllib3/LibreSSL — pre-existing, unrelated)
```

### I.6 Xác nhận không skip/xóa/disable

- KHÔNG có test nào bị xóa
- KHÔNG có test nào bị skip hoặc xfail
- KHÔNG có test nào bị disable
- Kiểm chứng: `pytest --tb=short -q` → `402 passed` (không có `s` hay `x` trong output)

### I.7 Scope Impact

- Fix thuộc module `app/research_os/` — module này là **scope drift** đã ghi nhận trong mục B.5
- Fix **KHÔNG làm nặng thêm** drift: 1 dòng thay đổi giá trị chuỗi, không thêm module/chức năng mới
- `test_research_os.py` (89 tests out-of-scope) vẫn PASS sau fix (dùng `in` operator, tương thích cả hai)

### I.8 Tech Debt phát sinh

- Không có tech debt mới từ fix này
- Tech debt cũ còn lại: ruff 5 lỗi trong app/ (pre-existing, không trong file vừa sửa), mypy không cài trong venv

---

*Review hoàn tất: 2026-06-21*  
*Evidence-based: Mọi finding đều có file path + test name làm bằng chứng.*  
*Claims không verify được đánh dấu `[CẦN KIỂM CHỨNG]`.*  
*Policy: KHÔNG merge, KHÔNG bắt đầu Sprint 3 cho đến khi các blockers còn lại ở mục H (items 2–4) được giải quyết.*  
*Blocker #1 (test failure) ĐÃ RESOLVED — xem mục I.*
