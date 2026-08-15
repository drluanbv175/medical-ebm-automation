# R5.0 Independent Qualification Readiness — Framework

**Document:** R5_0_QUALIFICATION_FRAMEWORK.md  
**Date:** 2026-06-28  
**Phase:** R5.0 — Independent Qualification Readiness  
**Status:** FRAMEWORK DESIGN — NOT QUALIFIED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Critical statement

**The Research OS is NOT QUALIFIED for research workflow use.**  
Qualification requires an independent external assessor performing prospective qualification activities against a documented validation plan. This document defines the framework; it does NOT constitute qualification itself.

---

## 1. Qualification philosophy

The Research OS follows a qualification model analogous to computerized system validation (CSV) under:
- FDA 21 CFR Part 11 (electronic records / electronic signatures — for reference)
- EU Annex 11 (computerized systems in clinical trials — for reference)
- GAMP 5 (Good Automated Manufacturing Practice — principles adapted for research software)
- ICH E6 R2 §5.5 (computerized systems in clinical trials)

**Adaptation note:** The Research OS is not a regulated medical device or GxP-validated system. The above frameworks are adapted as a model for rigor, not as formal regulatory compliance claims.

---

## 2. Qualification levels

| Level | Name | Scope | Status |
|-------|------|-------|--------|
| IQ | Installation Qualification | Software installed correctly; dependencies met | NOT DONE |
| OQ | Operational Qualification | Functionality works as specified in requirements | PARTIAL (offline suite = OQ evidence for synthetic modules) |
| PQ | Performance Qualification | System performs correctly in intended environment | NOT DONE |
| SQ | Security Qualification | Access controls, audit trail, boundary controls verified | NOT DONE |

---

## 3. Qualification scope

| Component | IQ | OQ | PQ | SQ |
|----------|----|----|----|----|
| RBAC / identity adapter (R1.2) | — | Partial (offline) | NOT DONE | NOT DONE |
| Audit retention contract (R1.3) | — | Partial (offline) | NOT DONE | NOT DONE |
| Synthetic EDC harness (R2.0) | — | Partial (offline) | NOT DONE | NOT DONE |
| Ethics / consent / operations (R3.0) | N/A | N/A | NOT DONE | N/A |
| eHospital boundary (R4.0) | — | Partial (offline) | NOT DONE | NOT DONE |
| Production WORM (PROD-AUD-01) | NOT DONE | NOT DONE | NOT DONE | NOT DONE |
| Production SSO/MFA | NOT DONE | NOT DONE | NOT DONE | NOT DONE |
| Production EDC | NOT DONE | NOT DONE | NOT DONE | NOT DONE |

---

## 4. Independent assessor requirements

| Requirement | ID | Status |
|------------|-----|--------|
| Assessor has no conflict of interest with study team | IQ-01 | NOT ARRANGED |
| Assessor is qualified in CSV/clinical trial software | IQ-02 | NOT ARRANGED |
| Assessor has signed confidentiality agreement | IQ-03 | NOT ARRANGED |
| Assessor has access to all design documents | IQ-04 | NOT ARRANGED |
| Assessor produces written qualification report | IQ-05 | NOT DONE |
| Study team reviews and accepts report | IQ-06 | NOT DONE |
| Deficiencies from report are tracked to closure | IQ-07 | NOT DONE |
| Final qualification sign-off by PI | IQ-08 | NOT RECEIVED |

---

## Conclusion

```
Qualification framework: DESIGN COMPLETE
Independent qualification: NOT DONE — EXTERNAL ASSESSOR REQUIRED
Research OS qualification status: NO-GO — NOT QUALIFIED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
