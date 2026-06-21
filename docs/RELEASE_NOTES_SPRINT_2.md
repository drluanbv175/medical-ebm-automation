# Release Notes — Sprint 2 Internal Demo

**Release:** `sprint-2-internal-demo`  
**Tag:** `65b891b`  
**Date:** 2026-06-21  
**Type:** Internal MVP/Demo — Controlled Environment Only  

> **⚠️ NOT FOR CLINICAL USE. NOT FOR PRODUCTION DEPLOYMENT.**  
> Không có dữ liệu bệnh nhân thật. Không có nội dung lâm sàng được phê duyệt.  
> Research OS không thuộc release này — xem `feat/research-os`.

---

## Scope

Sprint 2 hoàn thành 6 hạng mục được PO phê duyệt:

### 1. Persistence Foundation
- SQLAlchemy ORM với 13 governance tables (v7_phase_2a_governance_20260618)
- `app/models/governance_v7.py`: RunPacket, ApprovalRecord, AuditEventRecord, IncidentRecord, EvidenceRecordV2, ClaimRecord, RecommendationCard, ClinicalDecisionRecord, ResearchLockRecord, ReleaseManifest, ExportManifest, FeatureFlagAudit, CitationVerificationRecord
- Migration helper an toàn (`app/governance/migrations.py`) — dry-run trước khi apply
- PostgreSQL-ready config (`app/config.py`, `app/database.py`)

### 2. Consultation Workspace v1
- Python: `app/chronic_care/` — service, models, audit, rules, dashboard, synthetic_cases
- Next.js: `chronic-care-clinic-os/` — full app router với care plan, patient education, appointment, overdue task workflows
- Guarded preview contracts cho tất cả write actions (6 commits: appointment, care plan, education template, patient registration, overdue claim, admin write)

### 3. Evidence Card Library v1
- `app/evidence/`: evidence_registry.py, document_provenance.py, citation_verification.py, citation_cache.py, delta_report.py, pathway_impact_analysis.py, hypertension_local_adaptation.py
- Live adapters: registry_adapters.py
- Evidence mock flag (`app/models/evidence.py`) — tách bản ghi DEMO khỏi dữ liệu thật

### 4. Medication Safety Framework (Demo)
- `app/safety/medication_safety_engine.py`: screen HIGH_RISK_PAIRS (warfarin+NSAID, ACEi+ARB, nitrate+PDE5, CKD+NSAID, gan+hepatotoxic, thai+teratogenic, anticoagulant+antiplatelet)
- Tất cả cảnh báo ghi rõ "cần bác sĩ kiểm chứng" — không thay thế phán đoán lâm sàng
- `app/safety/red_team.py`: adversarial safety checks

### 5. Clinical Content Governance
- `app/core/policy_engine.py`: PolicyEngine — blocks PII, unapproved release, missing citation trace
- `app/models/governance_v7.py`: full governance model hierarchy
- `app/core/release_manager.py`: release approval workflow
- `app/clinical_content/clinical_runtime.py`: red-flag-first runtime
- Feature flags: `v7_clinical_release` default OFF

### 6. RBAC, AuditEvent append-only, CSRF/CORS, Auth, Safety Gates
- `app/core/audit_logger.py`: AuditEvent `@frozen dataclass`, JSONL append-only (`open("a")`), PII scrubbing trước khi ghi
- `app/core/approval_service.py`: reviewer_role gate (physician / principal_investigator / system_owner)
- `chronic-care-clinic-os/lib/audit-storage-contract.ts`: sequence/previousHash/eventHash/immutableAfterAppend hash chain
- Write action registry với guarded-preview contracts
- Dashboard DEMO banner (line 687) active khi USE_MOCK_SOURCES=true

---

## Research OS — Excluded

Research OS được tách ra `feat/research-os` (HEAD: `f3f6da6`) theo quyết định PO.  
16 module files, dashboard panel, test file và CLI wiring đã được xóa khỏi `main` tại commit `245cc8b`.

**Không cherry-pick, không merge `feat/research-os` vào `main` cho đến khi có PO approval Sprint riêng.**

---

## Quality Gate Summary

| Gate | Result |
|---|---|
| ruff lint | ✅ ALL CHECKS PASSED |
| pytest — 311 tests | ✅ **311 PASSED** (7.52s) |
| PII scan | ✅ No raw PII |
| Secret scan | ✅ No hardcoded secrets |
| Research OS exclusion | ✅ Fully excluded |
| Clinical safety | ✅ Confirmed |
| mypy | ⚠️ 79 errors — TD Sprint 3 |
| pip-audit | ⚠️ 36 vulns (pillow HIGH) — TD Sprint 3 |

---

## Technical Debt for Sprint 3

| ID | Item | Priority |
|---|---|---|
| TD-01 | mypy 79 type errors | Medium |
| TD-02 | pip-audit 36 vulns (upgrade pillow, streamlit, requests, urllib3) | **High** |
| TD-03 | DB-level append-only DDL trigger cho AuditEventRecord | **High** |
| TD-04 | E2E / Playwright tests | Medium |
| TD-05 | Accessibility tests | Low |
| TD-06 | Python-layer auth/RBAC tests | Medium |
| TD-07 | Review `AuditEventRecord.updated_at` — risk của update path | Medium |
| TD-08 | Anthropic model literal update trong integrations | Low |

---

## Constraints for Sprint 3

- ❌ Không bắt đầu Sprint 3 trước khi tag `sprint-2-internal-demo` được tạo và xác nhận
- ❌ Không cherry-pick Research OS vào `main`
- ❌ Không force-push hoặc rewrite Git history
- ❌ Không thêm chức năng mới vào `main` khi chưa có Sprint 3 kickoff

---

## Artifacts

| File | Description |
|---|---|
| `docs/SPRINT_2_POST_MERGE_RELEASE_VERIFICATION.md` | Full post-merge verification report (Parts A–I) |
| `docs/SPRINT_2_FINAL_RELEASE_READINESS.md` | Pre-merge readiness + Post-Merge Verification section |
| `docs/RELEASE_NOTES_SPRINT_2.md` | This file |
| `docs/SPRINT_2_SCOPE_CONTAINMENT_AND_SEMANTIC_VERIFICATION.md` | Scope containment detail |
| Git tag `sprint-2-internal-demo` | Annotated tag @ `65b891b` |

---

*Sprint 2 Release Notes — 2026-06-21*  
*Verification: Claude (Cowork automation)*
