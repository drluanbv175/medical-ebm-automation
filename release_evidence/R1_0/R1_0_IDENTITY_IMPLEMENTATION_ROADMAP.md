# R1.0 Identity Implementation Roadmap

**Document:** R1_0_IDENTITY_IMPLEMENTATION_ROADMAP.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc lộ trình

- Mỗi phase là **tuần tự có cổng** — không bắt đầu R1.N+1 khi R1.N chưa PASS
- Không phase nào thay đổi research OS source code trong R1.0
- Mọi thay đổi production phải qua change control
- AI outputs vẫn là DRAFT trong mọi phase
- Independent security test (R1.5) phải do tester ngoài team thực hiện

---

## R1.1 — Offline RBAC and Synthetic Identity Test Harness

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Xây dựng harness kiểm thử RBAC offline với synthetic identities để validate SoD matrix và test plan trước khi kết nối identity provider thật |
| **scope** | Synthetic identity fixtures (không dùng PII, không dùng real credentials); RBAC schema definition; SoD matrix unit tests; test harness chạy trong MRAQ_OFFLINE_CI=1 |
| **out_of_scope** | SSO integration; real user accounts; MFA; production deployment; source code thay đổi runtime research OS |
| **dependencies** | V4.3.5 COMPLETED; R0 blueprint COMPLETED |
| **evidence_required** | RBAC schema document; SoD matrix test results; test harness passing trong CI; no PII in test fixtures |
| **acceptance_criteria** | CI suite passes với RBAC test harness; SoD matrix coverage 100% of roles × actions; no real credentials |
| **go_no_go_conditions** | Test harness passes; SoD matrix fully defined; no PII; Validation Lead sign-off on test design |
| **gaps_addressed** | ID-04 (design), ID-05 (design) |

---

## R1.2 — Institutional SSO and MFA Integration Design Approval

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Thiết kế kỹ thuật chi tiết và nhận phê duyệt từ IT và tổ chức cho SSO integration và MFA enforcement trước khi implementation |
| **scope** | SSO integration design document (SAML 2.0/OIDC); MFA requirement specification; identity provider selection guidance; session management design; break-glass design; authentication logging design |
| **out_of_scope** | Actual SSO integration (R1.3); MFA implementation (R1.3); user provisioning |
| **dependencies** | R1.1 PASS; IT Lead engaged; institution IT approval process initiated |
| **evidence_required** | SSO integration design document signed by IT Lead; MFA design approved by Security Administrator; institution IT approval; design review meeting minutes |
| **acceptance_criteria** | Design document approved by: IT Lead, Security Administrator, PI, Validation Lead; institution IT confirms feasibility; no unresolved design conflicts |
| **go_no_go_conditions** | Signed design approval; institution IT feasibility confirmed; MFA solution (non-SMS) identified; break-glass design approved |
| **gaps_addressed** | ID-01 (design approval), ID-02 (design approval), ID-11 (design) |

---

## R1.3 — Authenticated Audit Attribution Implementation

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Implement và validate authenticated audit attribution layer: mọi write operation mang authenticated_actor_id từ identity provider; write-once audit event store; hash chain hoặc WORM |
| **scope** | SSO integration implementation; MFA implementation; authenticated audit event schema; write-once audit store (hash chain hoặc WORM); audit log integrity verification procedure; RBAC persistence implementation |
| **out_of_scope** | Delegation register (R1.4); access review (R1.4); independent security test (R1.5); real patient data |
| **dependencies** | R1.2 PASS; IT Lead available for implementation; institution SSO available |
| **evidence_required** | SSO integration test report; MFA enforcement test; audit event samples with all required fields; immutability test (IQ-13); IQ-09 test evidence; RBAC service deployment test |
| **acceptance_criteria** | IQ-01, IQ-02, IQ-03, IQ-06, IQ-09, IQ-10, IQ-13, IQ-17 all PASS; authenticated_actor_id present in every audit event; MFA required with no bypass |
| **go_no_go_conditions** | MFA 100% enforced (IQ-10 PASS); audit attribution complete (IQ-09 PASS); audit immutable (IQ-13 PASS); SoD enforcement technical (IQ-03, IQ-04 PASS); RBAC role revocation (IQ-07 PASS) |
| **gaps_addressed** | ID-01, ID-02, ID-03, ID-04, ID-05, ID-07 |

---

## R1.4 — Delegation and Access-Review Operations

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Implement delegation register, access revocation workflow, joiner/mover/leaver process, periodic access review và privileged account management |
| **scope** | Delegation register service; delegation_id in audit events; delegation expiry enforcement; JML (joiner/mover/leaver) workflow; offboarding procedure với SLA; periodic access review procedure; PAM procedure; break-glass procedure |
| **out_of_scope** | Independent security test (R1.5); ethics (R3); eHospital integration (R4) |
| **dependencies** | R1.3 PASS; delegation policy (R1_0_DELEGATION_AND_ATTESTATION_POLICY.md) approved |
| **evidence_required** | Delegation register test; delegation expiry test (IQ-08); offboarding test (IQ-16); first quarterly access review; break-glass test (IQ-15); IdP outage simulation (IQ-18); admin access control test (IQ-14) |
| **acceptance_criteria** | IQ-05, IQ-08, IQ-11, IQ-12, IQ-14, IQ-15, IQ-16, IQ-18, IQ-19 all PASS; offboarding within 24h SLA demonstrated; delegation_id in audit events |
| **go_no_go_conditions** | Delegation register functional; offboarding SLA achieved; break-glass tested; PAM procedure in place; first periodic access review completed |
| **gaps_addressed** | ID-06, ID-08, ID-09, ID-10, ID-11 |

---

## R1.5 — Independent Security and Identity Qualification

| Thuộc tính | Nội dung |
|-----------|---------|
| **purpose** | Kiểm định độc lập toàn bộ identity và security controls bởi tester ngoài team; CAPA closed; qualification sign-off |
| **scope** | Independent penetration test covering IDT-01..IDT-12; validation review of identity implementation; CAPA management; identity IQ sign-off |
| **out_of_scope** | Pilot execution (R6); real patient data; ethics; eHospital |
| **dependencies** | R1.4 PASS; independent security tester engaged (credentials documented); CAPA process established |
| **evidence_required** | Signed penetration test report by independent tester (IQ-20); CAPA log with 0 critical open; identity qualification sign-off by Validation Lead; training records for all research personnel |
| **acceptance_criteria** | IQ-20 PASS; 0 critical security findings open; all high findings CAPA closed; Validation Lead sign-off |
| **go_no_go_conditions** | Independent penetration test complete and signed; all critical + high findings CAPA closed; Validation Lead signs identity qualification; GATE-R1 PASS |
| **gaps_addressed** | ID-12 |

---

## Tóm tắt lộ trình

```
V4.3.5 (DONE)
    │
    ▼
R0 Blueprint (DONE)
    │
    ▼
R1.1 — Offline RBAC + Synthetic Test Harness
    │ Go/No-Go: test harness PASS; SoD matrix complete
    ▼
R1.2 — SSO + MFA Design Approval
    │ Go/No-Go: design signed by IT Lead + institution
    ▼
R1.3 — Authenticated Audit Attribution Implementation
    │ Go/No-Go: MFA enforced; audit attributed; SoD technical
    ▼
R1.4 — Delegation + Access-Review Operations
    │ Go/No-Go: delegation register; JML SLA; break-glass tested
    ▼
R1.5 — Independent Security Qualification
    │ Go/No-Go: pentest signed; CAPA closed; Validation Lead sign-off
    ▼
GATE-R1 PASS → R2 (Validated EDC)
```

**Mỗi mũi tên là một Go/No-Go gate. Không có shortcut.**

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
