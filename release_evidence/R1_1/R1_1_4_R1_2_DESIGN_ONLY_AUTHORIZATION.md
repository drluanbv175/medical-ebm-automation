# R1.1.4 R1.2 Design-Only Authorization

**Document:** R1_1_4_R1_2_DESIGN_ONLY_AUTHORIZATION.md  
**Date:** 2026-06-28  
**Phase:** R1.1.4 — Phase C  
**Decision ID:** VL-GATE-R1.1-2026-002  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Authorization check — all 5 conditions required

| # | Condition | Status | Evidence |
|---|-----------|--------|---------|
| 1 | decision = ACCEPT_TECHNICAL_TEST_DESIGN OR ACCEPT_WITH_ACTIONS | **MET** | decision = ACCEPT_WITH_ACTIONS (VL-GATE-R1.1-2026-002) |
| 2 | R1.1 technical evidence = PASS | **MET** | 867 passed / 0 failed; commit e806e0e |
| 3 | PROD-AUD-01 remains explicitly OPEN | **MET** | ACT-R1-01 status = OPEN; `PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED"` in source |
| 4 | R1.2 scope remains DESIGN-ONLY | **MET** | ACT-R1-03 enforces design-only; scope lock in `R1_1_4_R1_2_SCOPE_LOCK.md` |
| 5 | No real identity / SSO / MFA / eHospital / EDC / PII / research data enabled | **MET** | None connected; ACT-R1-03 prohibits activation during R1.2 |

**All 5 conditions: MET**

---

## Authorization result

```
R1.2 entry: AUTHORIZED_FOR_DESIGN_ONLY
```

```
Authorized by:       Human governance decision VL-GATE-R1.1-2026-002
Authorized date:     2026-06-28T05:30:28Z
Signed by:           Dr Luân (SELF_REVIEW — independence not established)
Gate status:         GATE-R1.1 = ACCEPTED_WITH_ACTIONS
Authorization scope: DESIGN-ONLY (see R1_1_4_R1_2_SCOPE_LOCK.md)
Actions binding:     ACT-R1-01, ACT-R1-02, ACT-R1-03, ACT-R1-04, ACT-R1-05
```

---

## Authorization is contingent

This authorization remains valid only while all three human-defined conditions hold:

| Condition | If violated |
|-----------|------------|
| ACT-R1-01: PROD-AUD-01 explicitly OPEN | R1.2 must pause; new governance decision required |
| ACT-R1-02: No WORM/immutable labeling of local ledger | R1.2 document must be corrected before proceeding |
| ACT-R1-03: No real SSO/MFA/data/eHospital/EDC activated | R1.2 must pause immediately; scope violation documented |

---

## What this authorization covers

R1.2 is authorized to produce **design documents only**:

- Design future SSO/MFA integration requirements
- Design RBAC persistence model for production
- Design identity-provider interface specifications
- Design session management and access-revocation requirements
- Design authenticated audit-attribution contract
- Design WORM-capable retention solution for PROD-AUD-01 (ACT-R1-01/ACT-R1-04)
- Create test and validation plans for R1.3
- Create architecture diagrams, gap registers, dependency maps
- Engage institutional IT to begin SSO onboarding process (no credentials issued)

---

## What this authorization does NOT cover

```
No real SSO connection
No real Identity Provider connection (SAML/OIDC/LDAP/OAuth)
No real user account creation
No real session / token / password / MFA secret
No eHospital integration
No EDC production implementation
No PII or patient data processing
No research data access
No research activation
No change to qualification status
No closure of PROD-AUD-01
```

---

## Invariants unchanged by this authorization

| Item | Status |
|------|--------|
| PROD-AUD-01 | OPEN |
| SSO | NOT IMPLEMENTED |
| MFA | NOT IMPLEMENTED |
| Authenticated identity | NOT IMPLEMENTED |
| Production audit attribution | NOT IMPLEMENTED |
| Real research execution | BLOCKED |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
