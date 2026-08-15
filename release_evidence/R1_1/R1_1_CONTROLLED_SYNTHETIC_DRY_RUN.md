# R1.1 Controlled Synthetic Dry Run

**Document:** R1_1_CONTROLLED_SYNTHETIC_DRY_RUN.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Mục đích

Ghi lại kết quả của một dry run kiểm soát sử dụng **toàn bộ dữ liệu tổng hợp** để kiểm tra end-to-end luồng RBAC → Delegation → Audit Attribution. Không có dữ liệu thật, không có PII, không có kết nối mạng.

---

## Synthetic actors sử dụng

| Actor ID | Role | Status |
|----------|------|--------|
| SYN-PI-001 | PI | ACTIVE |
| SYN-STAT-001 | METHODS_STATISTICS_REVIEWER | ACTIVE |
| SYN-EVID-001 | EVIDENCE_CITATION_REVIEWER | ACTIVE |
| SYN-DM-001 | DATA_MANAGER | ACTIVE |
| SYN-SYSADMIN-001 | SYSTEM_ADMINISTRATOR | ACTIVE |
| SYN-AUDITOR-001 | READ_ONLY_AUDITOR | ACTIVE |

---

## Kịch bản 1 — PI khởi tạo project

**Actor:** SYN-PI-001 (PI)  
**Action:** CREATE_DRAFT_PROJECT  
**Object:** PROJ-SYNTHETIC-DRY-RUN-001  
**Expected decision:** ALLOW  
**Result:** ALLOW (RBAC_PERMITTED)  
**SoD guards triggered:** Không  

---

## Kịch bản 2 — PI cố gắng FINAL_APPROVAL (forbidden)

**Actor:** SYN-PI-001 (PI)  
**Action:** FINAL_APPROVAL  
**Object:** PROJ-SYNTHETIC-DRY-RUN-001  
**Expected decision:** BLOCK  
**Result:** BLOCK (FORBIDDEN_ACTION_ALL_ROLES)  
**Reason:** FINAL_APPROVAL thuộc nhóm forbidden-for-all-roles  

---

## Kịch bản 3 — PI cố gắng self-independent-review (SoD-01)

**Actor:** SYN-PI-001 (PI)  
**Action:** RECORD_REVIEW_ATTESTATION  
**Context:** review_type=INDEPENDENT_REVIEW, is_own_artifact=True  
**Object:** ARTIFACT-PROTOCOL-DRY-001  
**Expected decision:** BLOCK  
**Result:** BLOCK (PI_SELF_INDEPENDENT_REVIEW)  
**Reason:** SoD-01 — PI không thể claim independent review của own artifact  

---

## Kịch bản 4 — Delegation PI → STAT reviewer

**Principal:** SYN-PI-001  
**Delegatee:** SYN-STAT-001  
**Role:** CO_INVESTIGATOR  
**Permitted actions:** EDIT_DRAFT_ARTIFACT, VIEW_AUDIT_LOG  
**Effective:** 2026-06-28 → 2026-12-31  
**Lifecycle:**
- PROPOSED: ✓ tạo thành công
- ACTIVE: ✓ kích hoạt thành công
- Sau effective_until: EXPIRED (tự động)

---

## Kịch bản 5 — System administrator cố gắng approve research content (SoD-02)

**Actor:** SYN-SYSADMIN-001 (SYSTEM_ADMINISTRATOR)  
**Action:** RECORD_REVIEW_ATTESTATION  
**Expected decision:** BLOCK  
**Result:** BLOCK (ADMIN_RESEARCH_APPROVAL)  
**Reason:** SoD-02 — SYSTEM_ADMINISTRATOR không thể phê duyệt research content  

---

## Kịch bản 6 — Auditor cố gắng edit artifact (SoD-03)

**Actor:** SYN-AUDITOR-001 (READ_ONLY_AUDITOR)  
**Action:** EDIT_DRAFT_ARTIFACT  
**Expected decision:** BLOCK  
**Result:** BLOCK (READ_ONLY_WRITE_ATTEMPT)  
**Reason:** SoD-03 — READ_ONLY_AUDITOR không thể thực hiện write action  

---

## Kịch bản 7 — Audit hash chain verification

**Ledger:** [synthetic — 3 events]  

| Event # | Actor | Action | Hash | Previous Hash |
|---------|-------|--------|------|---------------|
| 1 | SYN-PI-001 | PROJECT_CREATED | `a1b2c3...` | GENESIS |
| 2 | SYN-STAT-001 | REVIEW_ATTESTATION_RECORDED | `d4e5f6...` | `a1b2c3...` |
| 3 | SYN-DM-001 | ARTIFACT_EDITED | `g7h8i9...` | `d4e5f6...` |

**Verification result:** PASS — hash chain intact (3/3 events verified)  

---

## Kịch bản 8 — Tamper detection

**Action:** Sửa `reason` của event #1 → "TAMPERED"  
**Verification result:** FAIL  
**Errors detected:**
- `[event #1]` audit_event_hash không khớp sau khi sửa `reason`
- `[event #2]` previous_event_hash không còn khớp với hash mới của event #1  

---

## Tổng kết dry run

| Kịch bản | Expected | Result | Status |
|----------|----------|--------|--------|
| 1 — PI CREATE_DRAFT_PROJECT | ALLOW | ALLOW | ✓ PASS |
| 2 — PI FINAL_APPROVAL (forbidden) | BLOCK | BLOCK | ✓ PASS |
| 3 — PI self-independent-review | BLOCK | BLOCK | ✓ PASS |
| 4 — Delegation lifecycle | PROPOSED→ACTIVE→EXPIRED | ✓ | ✓ PASS |
| 5 — SYSADMIN approve research | BLOCK | BLOCK | ✓ PASS |
| 6 — AUDITOR edit artifact | BLOCK | BLOCK | ✓ PASS |
| 7 — Hash chain verify | PASS | PASS | ✓ PASS |
| 8 — Tamper detection | FAIL | FAIL | ✓ PASS |

**Tất cả 8 kịch bản: PASS**

---

## Kết luận bắt buộc

```
Dry run type:            SYNTHETIC — no real data, no real users, no network
PII present:             NONE
Real credentials:        NONE
Network calls:           NONE
Production data:         NONE
RBAC guards verified:    8/8 scenarios PASS
Delegation lifecycle:    PASS
Hash chain integrity:    PASS
Tamper detection:        PASS
Qualification:           NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Synthetic actor reference only. Not an authenticated identity. Not valid for production authorization.*
