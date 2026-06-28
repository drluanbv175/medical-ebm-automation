# R-GOV.1 Hospital Authorization Checklist

**Document:** R_GOV_1_HOSPITAL_AUTHORIZATION_CHECKLIST.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **This is a preparation checklist — not an authorization.**  
> All items must be confirmed before hospital authorization may be sought.

---

## Section 1 — Prerequisites before submission

| # | Requirement | Owner | Status |
|---|------------|-------|--------|
| 1 | Ethics approval obtained (ETH-GOV-01 APPROVED_EXTERNALLY) | PI | [NOT YET OBTAINED — prerequisite] |
| 2 | Study protocol finalized and approved by ethics committee | PI | [NOT PREPARED] |
| 3 | Data access agreement (DAA) template prepared with legal | PI + Legal | [NOT PREPARED] |
| 4 | SSO / MFA implemented and tested | Hospital IT + PI | [NOT IMPLEMENTED] |
| 5 | Production RBAC deployed and tested | PI | [NOT IMPLEMENTED] |
| 6 | WORM-capable audit trail confirmed (PROD-AUD-01 closed) | PI | [NOT IMPLEMENTED — ACT-R1-01 OPEN] |
| 7 | Encryption at rest confirmed | PI + Hospital IT | [NOT CONFIRMED] |
| 8 | Encryption in transit confirmed | Hospital IT | [NOT CONFIRMED] |
| 9 | Data Protection Impact Assessment (DPIA) completed | PI + DPO | [NOT COMPLETED] |
| 10 | Delegation log prepared | PI | [NOT PREPARED] |
| 11 | Pseudonymization service confirmed with hospital IT | Hospital IT | [NOT CONFIRMED] |
| 12 | Secure data transfer channel confirmed | Hospital IT | [NOT CONFIRMED] |

---

## Section 2 — Submission package assembly

| # | Document | Status |
|---|---------|--------|
| 1 | Cover letter from PI | [NOT PREPARED] |
| 2 | Hospital authorization request form | [NOT PREPARED — obtain from Research Management Office] |
| 3 | Study protocol (ethics-approved) | [NOT PREPARED] |
| 4 | Data access request (R_GOV_1_HOSPITAL_DATA_ACCESS_AND_SYSTEM_USE_REQUEST.md) | PREPARED |
| 5 | eHospital read-only boundary proposal (R_GOV_1_EHOSPITAL_READ_ONLY_BOUNDARY_PROPOSAL.md) | PREPARED |
| 6 | Hospital role and approval matrix (R_GOV_1_HOSPITAL_ROLE_AND_APPROVAL_MATRIX.md) | PREPARED |
| 7 | Information security and incident plan (R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md) | PREPARED |
| 8 | Data access agreement (DAA) draft | [NOT PREPARED] |
| 9 | DPIA | [NOT COMPLETED] |
| 10 | Ethics approval certificate | [NOT YET OBTAINED] |
| 11 | PI CV and GCP training certificate | [NOT PREPARED] |
| 12 | COI declarations | [NOT PREPARED] |

---

## Section 3 — Mandatory technical controls (must be confirmed BEFORE access)

| Control | Confirmation method | Required by |
|---------|--------------------|-----------:|
| SSO working | Hospital IT test certificate | Before data access |
| MFA enrolled for all users | Hospital IT attestation | Before data access |
| RBAC enforced | Access control test report | Before data access |
| WORM audit trail active | System test evidence (ACT-R1-01 closed) | Before data access |
| Encryption confirmed | IT security review sign-off | Before data access |
| Independent penetration test | External tester report (ACT-R1-05) | Before or within R1.5 |

---

## Section 4 — Post-authorization tracking

| Event | Action |
|-------|--------|
| Hospital acknowledges receipt | Record reference in R_GOV_1_EXTERNAL_DECISION_REGISTER.csv |
| Hospital requests additional information | Update status to REVISION_REQUESTED |
| Hospital grants authorization | PI confirms authenticity; record in R_GOV_1_EXTERNAL_DECISION_EVIDENCE_INDEX.csv |
| Authorization received | Update HOSP-GOV-01 status to APPROVED_EXTERNALLY (human confirmation required) |
| Authorization expires | Update status to EXPIRED; renewal required before any data access |
| Protocol or system change | Update status to AMENDMENT_REQUIRED; re-seek authorization |

---

## Section 5 — Critical blockers (must be resolved first)

```
BLOCKER 1: Ethics approval (ETH-GOV-01) not obtained
BLOCKER 2: SSO / MFA not implemented
BLOCKER 3: WORM audit trail not implemented (PROD-AUD-01 OPEN)
BLOCKER 4: Production RBAC not implemented
BLOCKER 5: Encryption at rest not confirmed
BLOCKER 6: DPIA not completed

None of these may be waived without explicit institutional approval.
```

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
