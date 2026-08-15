# R4.0 Data Domain Whitelist and Blocklist

**Document:** R4_0_DATA_DOMAIN_WHITELIST.md  
**Date:** 2026-06-28  
**Phase:** R4.0  
**Status:** WHITELIST DESIGN — NOT ACTIVE  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Permitted read domains (whitelist)

Only these 8 domains may be included in an `ExtractRequest`. Any other domain is rejected by `ExtractRequest.__post_init__`.

| Domain key | Content | Notes |
|-----------|---------|-------|
| `demographics_pseudonymized` | Age group, sex, ethnicity (non-identifying) | No name, DOB, address |
| `diagnosis_codes` | ICD-10 / ICD-11 codes | Dates may be shifted |
| `procedure_codes` | Surgical / procedure codes | Dates may be shifted |
| `laboratory_results` | Lab values and reference ranges | No patient-linking PII |
| `vital_signs` | BP, HR, SpO2, temperature, weight | No patient-linking PII |
| `medication_orders` | Drug name, dose, route, duration | No prescriber PII |
| `discharge_summaries_deidentified` | De-identified narrative text | Must be NLP-de-identified |
| `imaging_reports_deidentified` | Radiology report text (no DICOM) | Must be NLP-de-identified |

---

## 2. Blocked domains (explicit blocklist)

These 8 domains are explicitly blocked. Any `ExtractRequest` that includes a blocked domain raises `ValueError` immediately.

| Domain key | Reason blocked |
|-----------|---------------|
| `patient_identifiers` | Contains PII: name, DOB, address, phone, NHI |
| `financial_records` | Contains sensitive billing/insurance PII |
| `staff_credentials` | Contains staff login/password/role — security breach risk |
| `audit_logs_production` | Production audit trail must not leave HIS |
| `imaging_raw` | DICOM contains embedded PII; requires separate approval |
| `genetic_data` | Heightened privacy protection; separate ethics required |
| `mental_health_notes` | Heightened privacy protection (stigma risk) |
| `hiv_records` | Heightened privacy protection (discrimination risk) |

---

## 3. Domain approval process (FUTURE)

Adding a domain to the whitelist requires:
1. Written justification (scientific necessity)
2. Ethics committee approval covering the new domain
3. IT security assessment of domain content
4. Data access agreement amendment
5. Re-registration of study if protocol changes

**Claude Code CANNOT add domains to the whitelist unilaterally.**

---

## Conclusion

```
Domain whitelist: 8 permitted / 8 blocked
Hardcoded in: PERMITTED_READ_DOMAINS / BLOCKED_READ_DOMAINS (frozenset)
Real data extract: BLOCKED — eHospital not connected
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
