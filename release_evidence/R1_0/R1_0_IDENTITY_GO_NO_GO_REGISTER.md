# R1.0 Identity Go/No-Go Register

**Document:** R1_0_IDENTITY_GO_NO_GO_REGISTER.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc

Mỗi gate phải được đánh giá và sign-off bởi **người thật có thẩm quyền** — không phải AI.
Gate PASS chỉ được tuyên bố sau khi tất cả điều kiện bắt buộc được kiểm chứng.
AI system có thể hỗ trợ chuẩn bị checklist — nhưng quyết định Go/No-Go thuộc về PI, IT Lead,
Validation Lead và tổ chức.

---

## GATE-R1-PRECONDITION — R0 Baseline Verified

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1-PRE |
| **Phase** | R0 → R1.0 entry |
| **Decision** | Baseline đủ điều kiện để bắt đầu R1.0 design |
| **Reviewer** | PI (offline review) |
| **Status** | **PASS** — verified 2026-06-28 |

| # | Điều kiện | Kết quả |
|---|----------|---------|
| P1 | `git status --porcelain` clean | ✓ PASS |
| P2 | `v4.3.5-frozen` tag exists | ✓ PASS |
| P3 | `verify_manifest_registry.py` PASS | ✓ PASS |
| P4 | `MRAQ_OFFLINE_CI=1 pytest` → 797 passed / 0 failed | ✓ PASS |

---

## GATE-R1.1 — Offline RBAC Harness Ready

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1.1 |
| **Phase** | R1.1 |
| **Decision** | RBAC design và synthetic test harness đủ điều kiện để tiến sang SSO design |
| **Reviewer** | Validation Lead + PI |
| **Status** | **OPEN** — chưa thực hiện |

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| G1 | RBAC schema fully defined (all 10 roles; all permissions) | RBAC schema document |
| G2 | SoD matrix covers 100% roles × forbidden actions | SoD matrix test results |
| G3 | Synthetic test harness passes in MRAQ_OFFLINE_CI=1 | CI run log |
| G4 | No PII or real credentials in test fixtures | Code review + fixture audit |
| G5 | Validation Lead signs off on test design | Sign-off document |

**Blocking conditions:** Synthetic test harness fails → HOLD; Real credentials in fixtures → BLOCKED

---

## GATE-R1.2 — SSO and MFA Design Approved

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1.2 |
| **Phase** | R1.2 |
| **Decision** | SSO + MFA design approved by institution và IT trước khi implementation bắt đầu |
| **Reviewer** | IT Lead + Security Administrator + PI + Institution IT |
| **Status** | **OPEN** — chưa thực hiện |

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| G1 | SSO integration design document signed by IT Lead | Signed design document |
| G2 | MFA design approved (non-SMS second factor identified) | Signed MFA specification |
| G3 | Institution IT confirms SSO feasibility | Written confirmation |
| G4 | Break-glass design approved by Security Administrator | Break-glass design sign-off |
| G5 | Authentication logging design approved | Logging design document |
| G6 | Session management policy approved | Session policy document |

**Blocking conditions:** Institution IT not engaged → BLOCKED; SMS-only MFA → BLOCKED; No break-glass design → HOLD

---

## GATE-R1.3 — Authenticated Audit Attribution Implemented

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1.3 |
| **Phase** | R1.3 |
| **Decision** | SSO + MFA + RBAC + authenticated audit attribution implemented và tested |
| **Reviewer** | Validation Lead + Security Administrator + PI |
| **Status** | **OPEN** — chưa thực hiện |

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| G1 | IQ-01 PASS — shared account prevention | Test report |
| G2 | IQ-02 PASS — role assignment requires PI approval | Test report |
| G3 | IQ-03 PASS — least privilege enforced technically | Test matrix |
| G4 | IQ-04 PASS — PI cannot silently self-review | Test report |
| G5 | IQ-06 PASS — role escalation blocked | Test report |
| G6 | IQ-07 PASS — role revocation within SLA | Test report |
| G7 | IQ-09 PASS — delegated action has delegation_id in audit | Audit event sample |
| G8 | IQ-10 PASS — MFA required for privileged action; no bypass | Test report |
| G9 | IQ-13 PASS — audit log immutable | Immutability test report |
| G10 | IQ-17 PASS — READ_ONLY_AUDITOR cannot modify | Test report |
| G11 | Authenticated audit events present for all write operations | Audit log sample review |
| G12 | All required audit event fields present | Schema validation report |

**Blocking conditions:**
- MFA bypassable on any path → BLOCKED
- audit_attribution missing authenticated_actor_id → BLOCKED
- SoD not technically enforced → BLOCKED
- Audit log tamperable → BLOCKED

---

## GATE-R1.4 — Delegation and Access Governance Operational

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1.4 |
| **Phase** | R1.4 |
| **Decision** | Delegation register, JML workflow và access governance operational |
| **Reviewer** | PI + IT Lead + Validation Lead |
| **Status** | **OPEN** — chưa thực hiện |

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| G1 | IQ-05 PASS — reviewer COI declaration required | Test report |
| G2 | IQ-08 PASS — delegation expiry enforced | Test report |
| G3 | IQ-11 PASS — failed login lockout | Test report |
| G4 | IQ-12 PASS — session expiration | Test report |
| G5 | IQ-14 PASS — admin access review complete | Access review report |
| G6 | IQ-15 PASS — break-glass logging | Test report + alert evidence |
| G7 | IQ-16 PASS — offboarding revocation within 24h | SLA test report |
| G8 | IQ-18 PASS — IdP outage handling | Outage simulation report |
| G9 | IQ-19 PASS — backup audit log integrity | Backup integrity report |
| G10 | First quarterly access review completed | Review outcome report |
| G11 | PAM procedure in place | PAM procedure document |
| G12 | Delegation register functional with PI signature | Delegation test + sample record |

**Blocking conditions:**
- Offboarding SLA > 24h → BLOCKED
- Break-glass without alert → HOLD
- Delegation register not functional → HOLD

---

## GATE-R1 — Identity Qualification Complete (Entry to R2)

| Thuộc tính | Nội dung |
|-----------|---------|
| **Gate ID** | GATE-R1 |
| **Phase** | R1.5 — Final Identity Qualification |
| **Decision** | Identity and authentication infrastructure đủ điều kiện cho production research access |
| **Reviewer** | Independent Security Tester + Validation Lead + PI + Institution |
| **Status** | **OPEN** — chưa thực hiện |

| # | Điều kiện | Evidence required |
|---|----------|-------------------|
| G1 | IQ-20 PASS — independent penetration test by external tester | Signed pentest report (external tester) |
| G2 | 0 critical security findings open | CAPA log |
| G3 | 100% high security findings CAPA closed | CAPA log |
| G4 | Validation Lead signs identity qualification | Qualification sign-off document |
| G5 | GATE-R1.3 PASS | R1.3 gate sign-off |
| G6 | GATE-R1.4 PASS | R1.4 gate sign-off |
| G7 | COI declarations collected from all research personnel | Signed COI forms |
| G8 | Training completion records for all personnel | Training records |
| G9 | Institution authorizes production identity deployment | Authorization letter |
| G10 | Access control review procedure documented and scheduled | Review procedure |

**Blocking conditions:**
- Independent pentest not performed by external tester → BLOCKED (team self-pentest does NOT count)
- Any critical security finding open → BLOCKED
- Validation Lead sign-off absent → BLOCKED
- COI declarations incomplete → HOLD
- Training incomplete → HOLD

---

## Tóm tắt trạng thái

| Gate | Phase | Status |
|------|-------|--------|
| GATE-R1-PRE | R0 Baseline | **PASS** |
| GATE-R1.1 | R1.1 RBAC Harness | **OPEN** |
| GATE-R1.2 | R1.2 SSO+MFA Design | **OPEN** |
| GATE-R1.3 | R1.3 Audit Attribution | **OPEN** |
| GATE-R1.4 | R1.4 Delegation + JML | **OPEN** |
| GATE-R1 | R1.5 Final Qualification | **OPEN** |

**5 / 6 gates OPEN → Identity qualification: NOT STARTED → Real research execution: BLOCKED**

---

## Kết luận bắt buộc

```
Identity architecture:                    DESIGNED / HOLD
Institutional SSO:                        NOT IMPLEMENTED
MFA:                                      NOT IMPLEMENTED
RBAC persistence:                         NOT IMPLEMENTED
Separation of duties:                     DESIGN ONLY
Delegation control:                       NOT IMPLEMENTED
Authenticated audit attribution:          NOT IMPLEMENTED
Identity qualification:                   NOT STARTED
Level-A retrospective pilot readiness:    HOLD
Level-B prospective observational:        HOLD
Level-C interventional trial:             HOLD
Real research execution:                  BLOCKED
Qualification:                            NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
