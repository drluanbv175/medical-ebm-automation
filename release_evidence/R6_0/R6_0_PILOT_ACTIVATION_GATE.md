# R6.0 Pilot Activation Gate

**Document:** R6_0_PILOT_ACTIVATION_GATE.md  
**Date:** 2026-06-28  
**Phase:** R6.0  
**Status:** GATE — CLOSED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Gate purpose

The Pilot Activation Gate is the final hard stop before any real data (even retrospective/de-identified) enters the Research OS. It subsumes and re-confirms all prior gates.

**This gate CANNOT be opened by Claude Code.** Only Dr Luân, with written evidence for each condition, can open this gate.

---

## Compound gate conditions (ALL must be MET)

### Layer 1 — From R3.0 Study Activation Gate
| SAG condition | Status |
|---------------|--------|
| SAG-01: Ethics/IRB approval | NOT MET |
| SAG-02: Trial registered | NOT MET |
| SAG-03: Protocol version approved | NOT MET |
| SAG-04: ICF approved | NOT MET |
| SAG-05: Site qualified | NOT MET |
| SAG-06: Production EDC qualified | NOT MET |
| SAG-07: Investigators trained | NOT MET |
| SAG-08: WORM audit trail operational | NOT MET |
| SAG-09: SSO/MFA operational | NOT MET |
| SAG-10: eHospital boundary established | NOT MET |
| SAG-11: Independent security assessment | NOT MET |
| SAG-12: Dr Luân written confirmation | NOT RECEIVED |

### Layer 2 — R5.0 Qualification
| IQ gap | Status |
|--------|--------|
| IQ-20 through IQ-29 (all 10) | ALL OPEN |

### Layer 3 — R4.0 Integration
| HIS gap | Status |
|---------|--------|
| GAP-R4-01 through GAP-R4-10 (all 10) | ALL OPEN |

### Layer 4 — R6.0 specific
| PAG condition | Status |
|---------------|--------|
| PAG-01: Ethics covers retrospective pilot | NOT MET |
| PAG-07: Pilot sample size approved | NOT MET |
| PAG-09: Pilot monitoring plan active | NOT MET |
| PAG-10: Dr Luân pilot activation approval | NOT RECEIVED |

**Gate status: CLOSED — 0 of 36 total conditions met**

---

## Gate opening protocol

1. All 36 conditions achieved and evidenced
2. Dr Luân reviews and signs a pilot activation memo
3. Activation memo is stored in release_evidence/ with timestamp
4. Gate transitions to OPEN — this is a human governance decision
5. Claude Code records the governance decision in the ledger

---

## Conclusion

```
Pilot Activation Gate: CLOSED — 0 of 36 conditions met
Real data access: BLOCKED
Retrospective pilot: CANNOT START
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
