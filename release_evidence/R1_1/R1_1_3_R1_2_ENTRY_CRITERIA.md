# R1.1.3 R1.2 Entry Criteria

**Document:** R1_1_3_R1_2_ENTRY_CRITERIA.md  
**Date:** 2026-06-28  
**Phase:** R1.1.3 — Phase E  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

This document defines the precise conditions that must be satisfied before R1.2 work may begin, and the explicit boundaries of R1.2 scope. R1.2 is the SSO/MFA design review phase — it is design-approval work only, not production implementation.

---

## Section 1 — Entry conditions (all six must be met)

R1.2 must not begin unless ALL of the following are satisfied and documented:

---

**EC-01: Technical evidence R1.1.2 = PASS**

```
Status: SATISFIED
Evidence: 867 passed / 0 failed (MRAQ_OFFLINE_CI=1 pytest, commit e806e0e)
Manifest: PASS (48 agents, all_hash_verified=True)
File: release_evidence/R1_1/R1_1_2_FRESH_ARCHIVE_ACCEPTANCE.json
```

---

**EC-02: Human Validation Lead decision recorded**

```
Status: PENDING
Required: Signed R1_1_3_VALIDATION_LEAD_DECISION_RECORD_TEMPLATE.md
          with a valid decision_id, decision_date_utc, reviewer_reference,
          and signature_or_external_attestation_reference.
Authorized by: Human Validation Lead only.
Claude Code action: None — Claude Code must not record or simulate this.
```

---

**EC-03: GATE-R1.1 is PASS or ACCEPTED_WITH_ACTIONS**

```
Status: OPEN (not yet satisfied)
Required gate states that authorize R1.2 entry:
  [ ] PASS                   (from ACCEPT_TECHNICAL_TEST_DESIGN)
  [ ] ACCEPTED_WITH_ACTIONS  (from ACCEPT_WITH_ACTIONS)

Gate states that block R1.2 entry:
  OPEN · REVISION_REQUIRED · REJECTED

Current: OPEN — R1.2 entry is NOT AUTHORIZED until VL decision is recorded
         and gate status is updated per R1_1_3_GATE_R1_1_STATUS_UPDATE_TEMPLATE.md
```

---

**EC-04: PROD-AUD-01 explicitly OPEN and tracked**

```
Status: SATISFIED (deferred marker is in place)
Required: PROD-AUD-01 is recorded as OPEN with R1.3 as target milestone.
Evidence: PROD_AUD_01_WORM_DEPENDENCY = "NOT_IMPLEMENTED" in source code;
          documented in R1_1_2_TAMPER_EVIDENCE_AND_WORM_BOUNDARY.md;
          carried forward in R1_1_3_GATE_R1_1_STATUS_UPDATE_TEMPLATE.md §5.
Note: PROD-AUD-01 must remain visible in R1.2 scope documentation.
      It does not close during R1.2.
```

---

**EC-05: R1.2 scope is explicitly limited to design approval**

```
Status: DEFINED IN THIS DOCUMENT (see Section 2)
Required: All R1.2 work products must be labeled as design documents.
          No implementation artifact (deployed code, live service, real credential)
          may be produced under R1.2.
Confirmation: Validation Lead or PI must confirm R1.2 scope in writing
              before R1.2 implementation work begins.
```

---

**EC-06: No real identity, SSO, MFA, eHospital, or real data is activated**

```
Status: SATISFIED (none is currently active)
Required ongoing: This condition must remain true throughout R1.2.
                  Any activation of a real identity system, even for testing,
                  must be treated as an R1.3 action requiring GATE-R1.3 review.
Verification: R1.2 lead must confirm at R1.2 kickoff that no real identity
              system will be activated during the R1.2 design phase.
```

---

## Section 2 — What R1.2 IS authorized to do

If all six entry conditions are met, R1.2 may proceed with the following activities:

| Authorized R1.2 activity | Description |
|--------------------------|-------------|
| SSO design review | Document requirements for SSO integration (SAML/OIDC/institutional provider); no live configuration |
| MFA design review | Define MFA requirements and enrollment flow; no live MFA activation |
| Institutional IT engagement | Contact IT department to begin SSO onboarding process; no credentials issued |
| Identity model design | Design the mapping from institutional identity to research roles; no live mapping |
| RBAC production design | Design how R1.1 policy engine will be enforced at the production API/service layer |
| Audit trail production design | Design the WORM-capable retention solution for PROD-AUD-01; not implementation |
| R1.3 prerequisite scoping | Define what R1.3 needs to implement; document dependencies |

---

## Section 3 — What R1.2 is PROHIBITED from doing

The following are out of scope for R1.2 regardless of GATE-R1.1 status:

| Prohibited R1.2 activity | Reason |
|--------------------------|--------|
| Implement production SSO | Requires GATE-R1.3; institutional IT approval process not yet started |
| Enable real user access to any system | Requires authenticated identity; NOT IMPLEMENTED in R1.2 |
| Process real research data | Requires GATE-R2 and ethics/IRB approval |
| Claim electronic signature | Requires production PKI/signing service; NOT IMPLEMENTED |
| Claim independent review has been established | Independence not formally documented in R1.1 |
| Enable research activation | Requires GATE-R1, GATE-R2, GATE-R3 — all currently OPEN |
| Close PROD-AUD-01 | Requires WORM-capable retention service; deferred to R1.3 |
| Claim GATE-R1.1 = production ready | GATE-R1.1 PASS ≠ production authorization |
| Deploy R1.1 harness code to production | R1.1 is a test harness; not a production service |

---

## Section 4 — R1.2 entry authorization statement template

The following statement must be completed and signed by the PI or Validation Lead before R1.2 implementation work begins:

```
R1.2 Entry Authorization

Date: [YYYY-MM-DD]

I confirm that:
  - GATE-R1.1 status is [PASS / ACCEPTED_WITH_ACTIONS] as of [date]
  - Decision record ID: [VL decision_id]
  - R1.2 scope is limited to design documents, IT engagement, and requirement definition
  - No production SSO, real identity, real data, or real credentials will be activated during R1.2
  - PROD-AUD-01 remains OPEN and is tracked for R1.3
  - Real research execution remains BLOCKED

Authorized by: [Name, role]
Signature: [Signature or reference]
```

---

## Section 5 — Prerequisites that R1.2 must establish for R1.3

R1.2 design work should produce the following artifacts as inputs to R1.3:

| R1.2 artifact | Required for R1.3 |
|--------------|------------------|
| SSO integration specification | R1.3 production SSO deployment |
| MFA enrollment flow design | R1.3 MFA activation |
| WORM retention solution design | R1.3 closing PROD-AUD-01 |
| RBAC production enforcement design | R1.3 production RBAC service |
| Institutional IT onboarding record | R1.3 identity provider connection |
| Role mapping specification | R1.3 identity-to-role binding |

R1.3 must not begin until R1.2 artifacts above are complete and GATE-R1.2 is reviewed.

---

## Section 6 — Summary of authorization state

| Item | Status |
|------|--------|
| EC-01 Technical evidence | SATISFIED |
| EC-02 VL decision recorded | **PENDING** |
| EC-03 GATE-R1.1 authorized state | **NOT YET MET** |
| EC-04 PROD-AUD-01 tracked | SATISFIED |
| EC-05 Scope defined | SATISFIED |
| EC-06 No real identity active | SATISFIED |
| **R1.2 entry** | **NOT AUTHORIZED** (pending EC-02 and EC-03) |

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
