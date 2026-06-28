# R-GOV.2 Cross-Pack Consistency Audit

**Document:** R_GOV_2_CROSS_PACK_CONSISTENCY_AUDIT.md  
**Date:** 2026-06-28  
**Pack:** R-GOV.2 — Phase E  
**Scope:** Consistency check across ethics / hospital authorization / independent qualification packs  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> A consistency HOLD has been identified (Dimension 19 — IQ status terminology).  
> Per R-GOV.2 protocol, the cross-pack consistency audit result is HOLD.  
> The HOLD report is: R_GOV_2_CROSS_PACK_CONSISTENCY_HOLD_REPORT.md  
> All three packs individually have status READY_PENDING_HUMAN_INPUT.  
> The cross-pack consistency result does not itself block PI action on individual packs.

---

## Audit scope

20 consistency dimensions checked across:
- Ethics pack: 5 documents (R_GOV_1_ETHICS_*)
- Hospital pack: 6 documents (R_GOV_1_HOSPITAL_*)
- IQ pack: 6 documents (R_GOV_1_INDEPENDENT_QUALIFICATION_* + R_GOV_1_INDEPENDENCE_* + R_GOV_1_VALIDATION_*)
- Cross-pack documents: 8 documents (R_GOV_1_EXTERNAL_*, R_GOV_1_GOVERNANCE_*, R_GOV_1_CROSS_*, R_GOV_1_FREEZE_*, R_GOV_1_TECHNICAL_*)
- R1.1 documents: 5 files

---

## Dimension-by-dimension audit

| # | Dimension | Ethics pack | Hospital pack | IQ pack | Cross-pack docs | Result |
|---|-----------|------------|---------------|---------|-----------------|--------|
| D-01 | Project / study title | `[TITLE: TO BE CONFIRMED BY PI]` | `[TITLE: TO BE CONFIRMED BY PI]` | `[TITLE: TO BE CONFIRMED BY PI]` | `[TITLE: TO BE CONFIRMED BY PI]` | CONSISTENT — uniform placeholder |
| D-02 | Study classification | "retrospective observational secondary data analysis" or placeholder | Same | Same | Same | CONSISTENT |
| D-03 | Protocol version | Not yet assigned; placeholder | Not yet assigned | Not yet assigned | Not yet assigned | CONSISTENT |
| D-04 | PI reference | Dr Luân / bsluanbv175@gmail.com | Dr Luân / bsluanbv175@gmail.com | Dr Luân / bsluanbv175@gmail.com | Dr Luân / bsluanbv175@gmail.com | CONSISTENT |
| D-05 | System intended use | EBM automation; outpatient; DESIGN_ONLY | EBM automation; outpatient; DESIGN_ONLY | EBM automation; outpatient; DESIGN_ONLY | EBM automation; outpatient; DESIGN_ONLY | CONSISTENT |
| D-06 | AI-use limitation statement | Present in Ethics Dossier Part 10 | Referenced from ethics | Present in IQ Dossier §2 | Cross-referenced in handover pack | CONSISTENT |
| D-07 | Data source boundary | eHospital read-only; 8 permitted domains; 8 blocked domains | Same boundary referenced | Same boundary referenced | Same boundary in master register | CONSISTENT |
| D-08 | Privacy plan (pseudonymization) | SHA-256(real_id ‖ salt) → 64-char; hospital holds key | Same | Same | Same | CONSISTENT |
| D-09 | Consent / waiver wording | "TO BE DETERMINED BY COMPETENT ETHICS BODY" | Not applicable (hospital pack) | Not applicable (IQ pack) | Referenced in cross-pack | CONSISTENT — wording is uniform where applicable |
| D-10 | eHospital boundary | NOT_IMPLEMENTED; design only; zero-write | NOT_IMPLEMENTED; design only | NOT_IMPLEMENTED; design only | NOT_IMPLEMENTED | CONSISTENT |
| D-11 | Data retention wording | 7–15 year tiers; RETENTION_TIERS constant | 7–15 year tiers referenced | 7–15 year tiers referenced | 7–15 year tiers | CONSISTENT |
| D-12 | Audit trail wording | TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM | TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM | TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM | TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM | CONSISTENT |
| D-13 | WORM limitation (PROD-AUD-01) | PROD-AUD-01 OPEN; ACT-R1-01 | PROD-AUD-01 OPEN | PROD-AUD-01 OPEN | PROD-AUD-01 OPEN | CONSISTENT |
| D-14 | Identity / MFA limitation | SSO=NOT_IMPLEMENTED; MFA=NOT_IMPLEMENTED | Same | Same | Same | CONSISTENT |
| D-15 | Validated EDC limitation | Synthetic/R2.0 only; not production | Not EDC-specific | Synthetic only noted | Synthetic only noted | CONSISTENT |
| D-16 | Real-data activation status | BLOCKED | BLOCKED | BLOCKED | BLOCKED | CONSISTENT |
| D-17 | Ethics status | NOT GRANTED | NOT GRANTED (prerequisite reference) | NOT GRANTED (prerequisite reference) | NOT GRANTED | CONSISTENT |
| D-18 | Hospital authorization status | NOT GRANTED (dependency for IQ) | NOT GRANTED | NOT GRANTED (prerequisite reference) | NOT GRANTED | CONSISTENT |
| D-19 | **Independent qualification status** | **NOT STARTED (in R_GOV_1 executive summary and freeze summary)** | **NOT STARTED** | **NOT COMPLETED (in R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7 row 11)** | **Freeze summary: NOT STARTED; Technical Baseline: NOT COMPLETED** | **MINOR_INCONSISTENCY — see HOLD report** |
| D-20 | Invariants (BLOCKED / NO-GO) | NO-GO; real data BLOCKED; study BLOCKED | NO-GO; real data BLOCKED | NO-GO; qualification NO-GO | NO-GO; all BLOCKED | CONSISTENT |

---

## Summary

| Result | Count | Dimensions |
|--------|-------|-----------|
| CONSISTENT | 19 | D-01 through D-18; D-20 |
| MINOR_INCONSISTENCY | 1 | D-19 (IQ status terminology) |
| INCONSISTENT (major) | 0 | — |

---

## Description of inconsistency (D-19)

**Dimension:** Independent qualification status  
**Inconsistency type:** Terminology — minor  
**Documents using "NOT STARTED":**
- R_GOV_1_GOVERNANCE_READINESS_EXECUTIVE_SUMMARY.md (line ~67)
- R_GOV_1_FREEZE_SUMMARY.md (mandatory conclusion block)
- R_GOV_1_INDEPENDENT_QUALIFICATION_GO_NO_GO_REGISTER.md

**Documents using "NOT COMPLETED":**
- R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7 (row: Independent qualification = NOT_COMPLETED)

**Analysis:** Both terms describe the same factual state — no assessor has been designated and no qualification assessment has taken place. "NOT STARTED" is technically more accurate (the process has not started, not merely "not completed"). "NOT COMPLETED" could incorrectly imply that the process is in progress.

**Recommended resolution:** Standardize to "NOT STARTED" across all documents. This requires a minor update to R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7.

**Impact:** This terminology inconsistency does not affect the substantive governance position. The qualification state is unambiguously NO-GO in all documents. However, it triggers a cross-pack consistency HOLD per R-GOV.2 protocol.

---

## Cross-pack consistency audit verdict

**Cross-pack consistency:** HOLD — 1 minor terminology inconsistency (D-19)

Per R-GOV.2 protocol: cannot declare cross-pack submission-ready while HOLD is active.

**Resolution path:**
1. PI reviews HOLD report (R_GOV_2_CROSS_PACK_CONSISTENCY_HOLD_REPORT.md).
2. PI confirms preferred terminology ("NOT STARTED" recommended).
3. Update R_GOV_1_TECHNICAL_BASELINE_CONFIRMATION.md §7 to standardize terminology.
4. Re-run consistency audit (manually or via R-GOV.3 if applicable).
5. After resolution: cross-pack consistency result → PASS.

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs DRAFT — REQUIRE HUMAN REVIEW.*
