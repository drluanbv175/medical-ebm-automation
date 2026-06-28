# R4.0 Test Report

**Document:** R4_0_TEST_REPORT.md  
**Date:** 2026-06-28  
**Phase:** R4.0 — eHospital Read-Only Research Data Boundary  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

| Metric | Value |
|--------|-------|
| Post-R3.0 baseline | 1003 passed / 0 failed / 5 skipped |
| New R4.0 tests | 46 |
| Full suite post-R4.0 | **1049 passed / 0 failed / 5 skipped** |
| Regression failures | 0 |

**R4.0-specific breakdown (46 tests in `test_r4_0_ehospital_boundary.py`):**
- TestConstants (9): all 3 dependency constants, classification, whitelist/blocklist non-empty, no overlap, PII in blocked, disclaimer
- TestPseudonymizedSubject (6): valid, empty pseudo_id, short pseudo_id, invalid sex, is_pseudonymized=False, all valid sexes
- TestExtractRequest (8): valid, empty ethics_ref, blocked domain, unknown domain, empty domains, empty request_id, multiple permitted, mixed blocked+permitted
- TestExtractRecord (7): valid, PII name, PII dob, PII email, blocked domain, empty record_id, is_pseudonymized=False, non-PII keys allowed
- TestSyntheticEHospitalBoundary (16): interface subclass, submit, status pending, approve, retrieve approved, retrieve pending PermissionError, retrieve rejected PermissionError, unknown id KeyError, list permitted domains, validate pseudo valid/short/empty, health check, NOT_IMPLEMENTED constant, no write methods on interface

**Key contract invariants verified:**
- `EHospitalReadOnlyBoundaryInterface` has ZERO write/update/delete methods
- `ExtractRequest` without `ethics_approval_ref` raises ValueError
- `ExtractRecord` with PII key names raises ValueError
- `PERMITTED_READ_DOMAINS` ∩ `BLOCKED_READ_DOMAINS` = ∅
- Retrieve without APPROVED status raises PermissionError

```
eHospital boundary contract tests: COMPLETE
Real HIS connection: NOT TESTED (not available — EXTERNAL)
Patient data: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
