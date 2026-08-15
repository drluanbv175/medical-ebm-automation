# R-GOV.1 Hospital Authorization Gate Go/No-Go Register

**Document:** R_GOV_1_HOSPITAL_AUTHORIZATION_GO_NO_GO_REGISTER.md  
**Date:** 2026-06-28  
**Gate:** HOSP-01 — Hospital Authorization Gate  
**Decision ID:** HOSP-GOV-01  
**Status:** NO-GO  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **This register is a preparation document.**  
> **Hospital authorization: NOT GRANTED.**  
> **No data access or system connection may commence until this gate is PASS.**

---

## Gate HOSP-01 — Verdict

```
HOSP-01: NO-GO
Hospital authorization status: NOT GRANTED
eHospital data access: BLOCKED
eHospital integration: NOT IMPLEMENTED
Real patient-data processing: BLOCKED
```

---

## Pre-conditions matrix

| # | Pre-condition | Required? | Current status | Notes |
|---|-------------|---------|---------------|-------|
| 1 | Ethics approval obtained (ETH-01 PASS) | YES — prerequisite | ETH-01: NO-GO | Hospital authorization requires ethics approval first |
| 2 | Data access agreement (DAA) prepared | YES | NOT PREPARED | Legal involvement required |
| 3 | DAA signed by hospital authority and PI | YES | NOT SIGNED | External authority action |
| 4 | SSO / institutional identity connected | YES | NOT IMPLEMENTED | Hospital IT + R1.3 |
| 5 | MFA implemented and enrolled | YES | NOT IMPLEMENTED | Hospital IT + R1.3 |
| 6 | Production RBAC deployed | YES | NOT IMPLEMENTED | R1.3 |
| 7 | WORM audit trail confirmed (PROD-AUD-01) | YES | OPEN | ACT-R1-01/ACT-R1-04 |
| 8 | Encryption at rest confirmed | YES | NOT CONFIRMED | Before any data access |
| 9 | DPIA completed and approved | YES | NOT COMPLETED | Legal / DPO |
| 10 | Hospital IT security review passed | YES | NOT DONE | IT Security Officer |
| 11 | Pseudonymization service confirmed | YES | NOT CONFIRMED | Hospital IT |
| 12 | Hospital formal authorization issued | YES | NOT OBTAINED | External authority action |
| 13 | PI confirms authenticity of authorization | YES | NOT CONFIRMED | After receipt |
| 14 | Authorization recorded in evidence index | YES | NOT RECORDED | After PI confirmation |
| 15 | Independent penetration test (ACT-R1-05) | RECOMMENDED | NOT CONDUCTED | External tester required |

---

## Conditions for gate transition to PASS

HOSP-01 transitions from NO-GO → PASS ONLY when ALL of the following are human-confirmed:

| Condition | How confirmed |
|----------|--------------|
| ETH-01 is PASS (ethics approval in hand) | ETH-GOV-01 status = APPROVED_EXTERNALLY |
| Written hospital authorization received from designated authority | PI provides document; Claude Code records |
| DAA signed by both parties | PI provides signed copy |
| SSO/MFA operational | Hospital IT + PI sign-off |
| Production RBAC deployed | R1.3 gate PASS |
| PROD-AUD-01 closed | ACT-R1-01/ACT-R1-04 closed |
| DPIA completed | DPO sign-off |
| IT security review passed | IT Security Officer sign-off |
| Pseudonymization service confirmed | Hospital IT attestation |
| All pre-conditions 1–14 above MET | PI confirms each item |

---

## What does NOT qualify as hospital authorization

| Item | Reason it is not authorization |
|------|-------------------------------|
| Ethics approval | Ethics approval ≠ hospital data access authorization |
| This dossier | Preparation document |
| Technical test evidence | Technical evidence — not institutional decision |
| Any AI-generated document | AI cannot grant hospital authorization |
| Verbal agreement | Written formal authorization required |
| Department head informal consent | Institutional authority at Director / Research Management level required |

---

## Gate history

| Date | Event | Status |
|------|-------|--------|
| 2026-06-28 | R-GOV.1 dossier prepared; gate initialized | NO-GO |
| [Future] | Ethics approval obtained (ETH-01 PASS) | NO-GO (pre-condition met) |
| [Future] | Hospital submission made | NO-GO (SUBMITTED_EXTERNALLY) |
| [Future] | Hospital formal authorization issued | NO-GO → PASS if approved and all technical controls confirmed |

---

*Hospital authorization: NOT GRANTED*  
*eHospital integration: NOT IMPLEMENTED*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
