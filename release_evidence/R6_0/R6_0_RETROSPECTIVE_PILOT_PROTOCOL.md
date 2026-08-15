# R6.0 Level-A Retrospective Pilot — Protocol

**Document:** R6_0_RETROSPECTIVE_PILOT_PROTOCOL.md  
**Date:** 2026-06-28  
**Phase:** R6.0 — Level-A Retrospective Pilot Readiness  
**Status:** PROTOCOL DESIGN — NOT ACTIVATED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Critical statement

**The retrospective pilot CANNOT START until the Pilot Activation Gate is OPEN.** All 12 conditions of the Study Activation Gate (R3.0) plus all R5.0 qualification gaps must be closed before any retrospective data is accessed.

---

## 1. Pilot definition

**Level-A Retrospective Pilot:** A controlled, limited-scope retrospective review of de-identified/pseudonymized historical data to:
- Validate the eHospital data extraction pipeline (R4.0) end-to-end
- Confirm pseudonymization is working correctly
- Verify Research OS EDC modules (R2.0) can ingest and process real de-identified data
- Identify operational issues before full prospective study enrollment

**Level-A constraints:**
- Retrospective ONLY (historical data, no prospective enrollment)
- De-identified / pseudonymized data ONLY (no PII)
- Read-only extraction (no HIS write-back)
- Limited sample (N ≤ [TBD — to be set by ethics committee])
- Duration ≤ [TBD — to be set by ethics committee]

---

## 2. Pilot prerequisites (all OPEN)

| Prerequisite | ID | Status |
|-------------|-----|--------|
| Ethics approval covers retrospective pilot | PAG-01 | NOT MET |
| Study Activation Gate: all 12 conditions met | PAG-02 | NOT MET |
| All 10 R5.0 qualification gaps closed | PAG-03 | NOT MET |
| All 10 R4.0 integration gaps closed | PAG-04 | NOT MET |
| WORM audit trail operational (PROD-AUD-01) | PAG-05 | NOT MET |
| SSO/MFA authentication operational | PAG-06 | NOT MET |
| Pilot sample size approved by ethics | PAG-07 | NOT MET |
| Data access agreement covers pilot period | PAG-08 | NOT MET |
| Pilot monitoring plan in place | PAG-09 | NOT MET |
| Dr Luân written pilot activation approval | PAG-10 | NOT RECEIVED |

**Gate status: CLOSED — 0 of 10 prerequisites met**

---

## 3. Pilot data flow (when gate opens)

```
1. Obtain approved pseudonymized extract (eHospital boundary R4.0)
2. Ingest into Research OS EDC (R2.0 lifecycle modules)
3. Run data quality checks (DataDictionary.validate_record)
4. Apply edit checks (EditCheckEngine)
5. Resolve queries (QueryLifecycleManager)
6. Freeze pilot dataset (DataFreezeManager)
7. Lock pilot dataset (DataLockManager — PI authority required)
8. Create export manifest (ExportManager)
9. Log all steps in audit trail (EDCAuditLog → WORM production)
10. Pilot report to ethics committee
```

---

## 4. Pilot success criteria

| Criterion | Target |
|----------|--------|
| All records ingested without PII error | 100% |
| Data dictionary validation pass rate | ≥ 95% |
| Edit check violation rate within expected range | TBD by protocol |
| Audit trail complete for all events | 100% |
| Zero unresolved ethics/safety issues | Mandatory |
| Pilot report submitted to ethics within [TBD] days | Mandatory |

---

## Conclusion

```
Retrospective pilot protocol: DESIGN COMPLETE
Pilot activation: BLOCKED — gate CLOSED (0 of 10 met)
Real data access: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
