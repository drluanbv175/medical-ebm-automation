# R3.0 Study Operations SOP

**Document:** R3_0_STUDY_OPERATIONS_SOP.md  
**Date:** 2026-06-28  
**Phase:** R3.0  
**Status:** SOP DESIGN — NOT ACTIVE  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Scope

This SOP covers operational procedures for running a medical research study using the Medical Research OS. It must not be treated as active until the study activation gate is open.

---

## 1. Enrollment procedure

```
Step 1: Screen participant against eligibility criteria
    → Use: thang-diem-nguy-co + sang-loc-co-do agents
    → Record: screening log in EDC (CRFVersionRegistry current version)

Step 2: Confirm eligibility (inclusion/exclusion criteria all met)
    → Record: eligibility checklist (all items documented)

Step 3: Obtain informed consent
    → Provide ICF (approved version only)
    → Allow time for questions
    → Obtain signed consent
    → Store: ISF + EDC record

Step 4: Assign participant ID (pseudonymous)
    → No real name/DOB in EDC — pseudonymous ID only
    → Maintain participant identification log (separate, secure, off-EDC)

Step 5: Create EDC record (SyntheticRecord in production EDC)
    → CRF version = current version in CRFVersionRegistry
    → Record status = ACTIVE
    → Log audit entry
```

---

## 2. Data entry procedure

| Step | Action | System |
|------|--------|--------|
| 1 | Complete source document | Paper CRF / EHR extract |
| 2 | Enter data in EDC within 24h | Production EDC (not synthetic) |
| 3 | Run edit checks (automated) | EditCheckEngine |
| 4 | Resolve queries within 7 days | QueryLifecycleManager |
| 5 | All corrections require reason | CorrectionManager |
| 6 | Review for protocol deviations | DeviationRegistry |

---

## 3. Adverse event reporting procedure

| AE severity | Initial report | Full report | IRB notification |
|------------|----------------|-------------|-----------------|
| Non-serious AE | Within 24h to EDC | Within 7 days | Not required |
| Serious AE (SAE) | Within 24h to sponsor | Within 15 days | Within 7 days |
| SUSAR | Within 24h to sponsor + authority | Expedited | Immediate |

**All AE/SAE data must be entered in production EDC — NOT in synthetic harness.**

---

## 4. Protocol deviation handling

| Deviation type | Documentation | Reporting |
|---------------|--------------|----------|
| Minor | Record in deviation log | Next monitoring visit |
| Major | Record + CAPA + root cause | IRB within [TBD] days |
| Critical | Immediate stop if safety risk | IRB + sponsor immediately |

---

## 5. Study closure procedure

```
Step 1: Data freeze (all records) → DataFreezeManager.freeze() per record
Step 2: Query resolution (all queries CLOSED or CANCELLED)
Step 3: Database lock (authority required) → DataLockManager.lock()
Step 4: Export manifest creation → ExportManager.create_manifest()
Step 5: Statistical analysis (per locked SAP)
Step 6: CSR (Clinical Study Report) preparation
Step 7: Archival (7–15 years per retention policy)
```

---

## Conclusion

```
Study operations SOP: DESIGN COMPLETE
SOP active: NO — ethics gate must open first
Enrollment: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
