# R1.1.4 R1.2 Scope Lock

**Document:** R1_1_4_R1_2_SCOPE_LOCK.md  
**Date:** 2026-06-28  
**Phase:** R1.1.4 — Phase E  
**Decision ID:** VL-GATE-R1.1-2026-001  
**Authorization:** AUTHORIZED_FOR_DESIGN_ONLY  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> This scope lock is binding for all R1.2 work products.  
> Any activity not listed under "Permitted" is prohibited by default.  
> Violations require a new governance decision before work can resume.

---

## R1.2 permitted activities (design documents only)

| Activity | Output type | Notes |
|---------|------------|-------|
| Design future SSO/MFA integration | Specification document | No live configuration; no credentials |
| Design RBAC persistence model | Architecture document | No deployed service |
| Design identity-provider interface | Interface specification | No real IdP connection |
| Design session management requirements | Requirements document | No real sessions |
| Design access-revocation requirements | Requirements document | No real tokens |
| Design authenticated audit-attribution contract | Design document | No live audit trail |
| Create test and validation plans for R1.3 | Test plan documents | No test execution against real systems |
| Create architecture diagrams | Diagrams | No live infrastructure |
| Create gap registers and dependency maps | Gap analysis documents | Documentation only |
| Engage institutional IT for SSO onboarding process | Communication only | No credentials or accounts issued |
| Scope PROD-AUD-01 solution requirements | Requirements document | No WORM implementation |
| Define R1.3 entry criteria | Design document | No R1.3 execution |

---

## R1.2 prohibited activities (hard boundaries)

```
PROHIBITED — No real SSO connection of any kind
PROHIBITED — No real Identity Provider connection (no SAML, OIDC, LDAP, OAuth)
PROHIBITED — No real user account creation
PROHIBITED — No real session, token, password, or MFA secret
PROHIBITED — No eHospital integration (development or production)
PROHIBITED — No EDC production implementation
PROHIBITED — No PII (personally identifiable information) processing
PROHIBITED — No patient data processing
PROHIBITED — No real research data access
PROHIBITED — No research activation or research workflow execution
PROHIBITED — No change to qualification status
PROHIBITED — No claim that GATE-R1.1 ACCEPTED = production ready
PROHIBITED — No claim that local hash-chain is WORM or immutable
PROHIBITED — No closure of PROD-AUD-01
PROHIBITED — No claim of independent review
PROHIBITED — No electronic signature claim
PROHIBITED — No deployment of R1.1 test harness as production service
```

---

## Boundary conditions

**If during R1.2 any of the following occurs:**
- A real identity provider is connected (even for "testing")
- A real user account is created
- Real patient or research data is accessed
- A production service is deployed

**Then:**
1. R1.2 work must pause immediately
2. The activity must be documented as a scope violation
3. A new human governance decision is required before any R1.2 work resumes
4. Claude Code must not restart R1.2 work without explicit human instruction

---

## Relationship to PROD-AUD-01

PROD-AUD-01 (production WORM retention) remains OPEN throughout R1.2.  
R1.2 may produce a **design** for a WORM-capable solution.  
R1.2 must NOT claim that PROD-AUD-01 is closed or that WORM retention is implemented.  
PROD-AUD-01 closes only when R1.3 implements, deploys, and verifies a WORM-capable retention solution.

---

## Expected R1.2 artifacts (design only)

| Artifact | Purpose | Required for |
|---------|---------|-------------|
| SSO integration specification | Document SAML/OIDC requirements | R1.3 production SSO deployment |
| MFA enrollment flow design | Define MFA steps and recovery | R1.3 MFA activation |
| WORM retention solution design | Define PROD-AUD-01 solution | R1.3 closing PROD-AUD-01 |
| RBAC production enforcement design | How R1.1 policy engine maps to prod API | R1.3 production RBAC service |
| Institutional IT onboarding record | SSO onboarding communication log | R1.3 IdP connection |
| Role mapping specification | Institutional identity → research role | R1.3 identity-to-role binding |
| R1.2 GATE criteria definition | What R1.2 must achieve before GATE-R1.2 | GATE-R1.2 review |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
