# R1.1.4 R1.2 Scope Lock

**Document:** R1_1_4_R1_2_SCOPE_LOCK.md  
**Date:** 2026-06-28  
**Phase:** R1.1.4 — Phase E  
**Decision ID:** VL-GATE-R1.1-2026-002  
**Authorization:** AUTHORIZED_FOR_DESIGN_ONLY  
**Binding action:** ACT-R1-03 (Dr Luân, due R1.2 completion)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> This scope lock is binding for all R1.2 work products.  
> It is enforced by ACT-R1-03 (VL-GATE-R1.1-2026-002).  
> Any activity not listed under "Permitted" is prohibited by default.  
> A scope violation requires immediate pause and a new governance decision.

---

## R1.2 permitted activities (design documents only)

| Activity | Output type | Binding constraint |
|---------|------------|-------------------|
| Design SSO/MFA integration requirements | Specification document | No live config; no credentials; ACT-R1-03 |
| Design RBAC persistence model | Architecture document | No deployed service |
| Design identity-provider interface | Interface specification | No real IdP connection |
| Design session management requirements | Requirements document | No real sessions |
| Design access-revocation requirements | Requirements document | No real tokens |
| Design authenticated audit-attribution contract | Design document | No live audit trail |
| Design WORM-capable retention solution | Requirements document | Closes ACT-R1-01/ACT-R1-04 in R1.3; not R1.2 |
| Create test and validation plans for R1.3 | Test plan documents | No test execution on real systems |
| Create architecture diagrams | Diagrams | No live infrastructure |
| Create gap registers and dependency maps | Analysis documents | Documentation only |
| Engage institutional IT for SSO onboarding | Communication log | No credentials or accounts issued |
| Define R1.2 gate criteria | Design document | For GATE-R1.2 review; not self-closing |

---

## R1.2 prohibited activities (hard boundaries from ACT-R1-03)

```
PROHIBITED — Real SSO connection of any kind
PROHIBITED — Real Identity Provider connection (no SAML, OIDC, LDAP, OAuth)
PROHIBITED — Real user account creation
PROHIBITED — Real session, token, password, or MFA secret
PROHIBITED — eHospital integration (development or production)
PROHIBITED — EDC production implementation
PROHIBITED — PII (personally identifiable information) processing
PROHIBITED — Patient data processing
PROHIBITED — Real research data access
PROHIBITED — Research activation or research workflow execution
PROHIBITED — Qualification status change
PROHIBITED — Claiming GATE-R1.1 ACCEPTED_WITH_ACTIONS = production ready
PROHIBITED — Describing local hash-chain as WORM or immutable (ACT-R1-02)
PROHIBITED — Closing PROD-AUD-01 via R1.2 design document (ACT-R1-01)
PROHIBITED — Claiming independent review (SELF_REVIEW only)
PROHIBITED — Deploying R1.1 test harness as a production service
```

---

## Scope violation protocol

If any prohibited activity occurs during R1.2:

1. R1.2 work pauses immediately
2. Scope violation documented with description, date, and responsible party
3. New human governance decision required before R1.2 resumes
4. Claude Code does not restart R1.2 without explicit human instruction

---

## Expected R1.2 deliverables (design only)

| Artifact | Purpose | Required for |
|---------|---------|-------------|
| SSO integration specification | Document SAML/OIDC requirements | R1.3 production SSO |
| MFA enrollment flow design | Define MFA steps and recovery | R1.3 MFA activation |
| WORM retention solution design | Define PROD-AUD-01 solution | ACT-R1-01, ACT-R1-04; R1.3 |
| RBAC production enforcement design | Map R1.1 policy engine to production API | R1.3 RBAC service |
| Institutional IT onboarding record | SSO onboarding communication log | R1.3 IdP connection |
| Role mapping specification | Institutional identity → research role | R1.3 binding |
| GATE-R1.2 criteria definition | What R1.2 must achieve for gate review | GATE-R1.2 review |

---

## ACT-R1-03 closure criterion

ACT-R1-03 closes when:
- GATE-R1.2 review confirms all R1.2 work products are design documents only
- No real system was connected during R1.2
- Dr Luân or designated reviewer signs off

Until closure: ACT-R1-03 status = OPEN and GATE-R1.1 remains ACCEPTED_WITH_ACTIONS (not PASS).

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
