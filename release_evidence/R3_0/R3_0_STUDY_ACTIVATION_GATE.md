# R3.0 Study Activation Gate

**Document:** R3_0_STUDY_ACTIVATION_GATE.md  
**Date:** 2026-06-28  
**Phase:** R3.0  
**Status:** GATE — CLOSED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Gate purpose

The Study Activation Gate is a hard stop that prevents any real research activity from starting until ALL external prerequisites are met. This gate CANNOT be opened by Claude Code. It requires explicit written confirmation from Dr Luân with documentary evidence.

---

## Gate conditions (ALL must be MET before activation)

| Condition | ID | Status |
|----------|-----|--------|
| Ethics/IRB approval obtained (written letter, reference number) | SAG-01 | NOT MET |
| Trial registered in approved registry | SAG-02 | NOT MET |
| Protocol version locked and approved by ethics committee | SAG-03 | NOT MET |
| ICF version approved by ethics committee | SAG-04 | NOT MET |
| Site qualification assessment passed | SAG-05 | NOT MET |
| EDC (production) qualified and validated | SAG-06 | NOT MET |
| All investigators trained (GCP + protocol) | SAG-07 | NOT MET |
| WORM audit trail operational (PROD-AUD-01 closed) | SAG-08 | NOT MET |
| SSO/MFA authentication operational | SAG-09 | NOT MET |
| eHospital read-only boundary established (if R4.0) | SAG-10 | NOT MET |
| Independent security assessment complete (IQ-20) | SAG-11 | NOT MET |
| Dr Luân written confirmation of all above | SAG-12 | NOT RECEIVED |

**Gate status: CLOSED — 0 of 12 conditions met**

---

## What happens if this gate is bypassed

Bypassing this gate without meeting all conditions constitutes:
- Ethics violation (unauthorized human subjects research)
- GCP violation
- Potential regulatory breach
- Research integrity violation

No data collected before gate opening is valid for research purposes.

---

## Gate opening protocol

When Dr Luân confirms all 12 conditions are met:
1. Each condition must reference documentary evidence (approval letter ref, certificate, etc.)
2. Claude Code records the confirmation in the gate ledger
3. Gate transitions to OPEN
4. This is recorded as a human governance decision (same format as VL-GATE-R1.1)

**Claude Code must NOT self-assess any of conditions SAG-01 through SAG-11.**

---

## Conclusion

```
Study Activation Gate: CLOSED
Real participant enrollment: BLOCKED
Research data collection: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
