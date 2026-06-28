# R5.0 System Qualification Scope

**Document:** R5_0_SYSTEM_QUALIFICATION_SCOPE.md  
**Date:** 2026-06-28  
**Phase:** R5.0  
**Status:** SCOPE DESIGN — NOT EXECUTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. In-scope modules (require qualification before production use)

| Module | Phase | Current OQ evidence | PQ/SQ needed |
|--------|-------|-------------------|--------------|
| identity_adapter_contract.py | R1.2 | 29 offline tests | Production IdP test |
| audit_retention_contract.py | R1.3 | 32 offline tests | Production WORM test |
| synthetic_edc_core.py | R2.0 | 36 offline tests | Production EDC integration test |
| synthetic_edc_lifecycle.py | R2.0 | 39 offline tests | Production lifecycle test |
| synthetic_edc_query.py | R2.0 | Included in R2.0 | Production query test |
| ehospital_boundary_contract.py | R4.0 | 46 offline tests | Production HIS integration test |

**Total offline test evidence: 1049 passed / 0 failed** (OQ partial evidence only)

---

## 2. Out of scope (operational but not part of Research OS core)

| Component | Reason out of scope |
|----------|---------------------|
| Production SSO/MFA provider | External institutional system |
| Production WORM storage | External cloud/on-prem service |
| Production EDC (REDCap/Castor) | Vendor-validated system |
| eHospital/HIS | Institutional system under separate validation |
| Institutional network infrastructure | Out of research team control |

---

## 3. Offline test suite as partial OQ evidence

The 1049 offline tests constitute **partial OQ evidence** for synthetic harness behavior. They do NOT constitute:
- Evidence that production dependencies work correctly
- Evidence that integration between modules and production systems works
- PQ or SQ evidence
- Independent qualification (tests were written and run by the development team)

**An independent assessor must re-execute critical test scripts** in the target environment to generate valid OQ evidence.

---

## 4. Change control boundary

After qualification, ANY change to in-scope modules requires:
1. Impact assessment (does it affect qualified behavior?)
2. Regression test execution
3. Independent assessor review if in-scope behavior changes
4. Updated qualification documentation
5. Dr Luân approval before re-deployment

---

## Conclusion

```
System qualification scope: DEFINED
Independent qualification: NOT DONE
Offline OQ evidence: 1049 tests (partial, not independent)
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
