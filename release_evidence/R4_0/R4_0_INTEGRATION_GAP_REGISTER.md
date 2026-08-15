# R4.0 eHospital Integration Gap Register

**Document:** R4_0_INTEGRATION_GAP_REGISTER.md  
**Date:** 2026-06-28  
**Phase:** R4.0  
**Status:** GAP REGISTER — ALL GAPS OPEN  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Track every gap between the R4.0 eHospital boundary design and production readiness. All gaps are OPEN. None can be closed by Claude Code.

---

## Gap register

| Gap ID | Description | Owner | Status |
|--------|------------|-------|--------|
| GAP-R4-01 | No real eHospital API endpoint configured | Institutional IT | OPEN |
| GAP-R4-02 | No service account with read-only scope | Institutional IT + security | OPEN |
| GAP-R4-03 | No network/VPN path from Research OS to HIS | Institutional network | OPEN |
| GAP-R4-04 | No institutional pseudonymization key vault | IT + data governance | OPEN |
| GAP-R4-05 | No data access agreement (DAA) signed | Legal + research office | OPEN |
| GAP-R4-06 | No data transfer agreement (DTA) if cross-org | Legal + IRB | OPEN |
| GAP-R4-07 | Imaging DICOM extract not designed | Future phase | OPEN |
| GAP-R4-08 | Date shifting algorithm not specified | Biostatistician + ethics | OPEN |
| GAP-R4-09 | NLP de-identification for narrative text not built | NLP engineer | OPEN |
| GAP-R4-10 | Penetration test of boundary API not done | Security team | OPEN |

---

## Gap closure criteria

A gap is CLOSED only when:
1. The external party confirms completion in writing
2. Evidence is provided (contract signed, certificate, test report)
3. Dr Luân records the closure in the gate ledger

**GAP-R4-01 through GAP-R4-10: all OPEN — 0 of 10 closed.**

---

## Production readiness gate

eHospital boundary may go live ONLY when:
- All 10 gaps above are CLOSED
- Study Activation Gate (R3.0) is OPEN
- Ethics approval covers eHospital data access (SAG-10)
- Independent security assessment passed (SAG-11)

---

## Conclusion

```
eHospital integration gaps: 10 OPEN / 0 CLOSED
Production connection: NOT POSSIBLE until all gaps closed
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
