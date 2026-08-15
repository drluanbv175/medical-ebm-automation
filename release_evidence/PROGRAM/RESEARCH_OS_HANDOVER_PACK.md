# Research OS — Handover Pack

**Document:** RESEARCH_OS_HANDOVER_PACK.md  
**Date:** 2026-06-28  
**Branch:** feat/r1-1-2-design-gap-remediation  
**Final commit:** bc52018 (R5.0+R6.0); PROGRAM commit: TBD  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## What is being handed over

A Pre-Production Research OS Readiness Package covering 7 phases (R1.2–R6.0). This package contains:

### Source modules (7 files)
| Module | Phase | Purpose |
|--------|-------|---------|
| `research_project/identity_adapter_contract.py` | R1.2 | Identity interface + synthetic stub |
| `research_project/audit_retention_contract.py` | R1.3 | WORM retention interface + fake stub |
| `research_project/synthetic_edc_core.py` | R2.0 | CRF registry, data dict, edit checks |
| `research_project/synthetic_edc_lifecycle.py` | R2.0 | Freeze, lock, export, audit, backup |
| `research_project/synthetic_edc_query.py` | R2.0 | Query lifecycle, corrections, deviations |
| `research_project/ehospital_boundary_contract.py` | R4.0 | eHospital read-only boundary + stub |

### Test files (5 phase-specific files)
| Test file | Phase | Tests |
|-----------|-------|-------|
| `tests/test_r1_2_identity_contract.py` | R1.2 | 29 |
| `tests/test_r1_3_audit_retention_contract.py` | R1.3 | 32 |
| `tests/test_r2_0_synthetic_edc_core.py` | R2.0 | 36 |
| `tests/test_r2_0_synthetic_edc_lifecycle.py` | R2.0 | 39 |
| `tests/test_r4_0_ehospital_boundary.py` | R4.0 | 46 |

**Total suite: 1049 passed / 0 failed / 5 skipped**

### Evidence tree
```
release_evidence/
├── PROGRAM/         6 files (control, status, gaps, go/no-go, traceability, this pack)
├── R1_2/            8 files
├── R1_3/            8 files
├── R2_0/            4 files
├── R3_0/            8 files
├── R4_0/            7 files
├── R5_0/            7 files
└── R6_0/            5 files
```

---

## How to run the test suite

```bash
# Activate venv (outside OneDrive)
source ~/.ebm-venv/bin/activate   # macOS/Linux
# or: source %USERPROFILE%\.ebm-venv\Scripts\activate  # Windows

# Run offline suite
cd medical-ebm-automation
MRAQ_OFFLINE_CI=1 pytest --tb=short -q

# Expected: 1049 passed / 0 failed / 5 skipped
```

---

## What to do next (priority order)

### Immediate (Dr Luân action required)

1. **Submit ethics/IRB application**
   - Prepare documents listed in `R3_0_ETHICS_AND_IRB_REQUIREMENTS.md`
   - Submit to institutional ethics committee
   - Reference: `R3_0_STUDY_ACTIVATION_GATE.md` condition SAG-01

2. **Engage institutional IT for infrastructure**
   - WORM storage: see `R1_3_WORM_SOLUTION_DESIGN.md` (AWS/Azure/GCP comparison)
   - SSO/MFA: see `R1_2_SESSION_AND_REVOCATION_REQUIREMENTS.md`
   - eHospital API: see `R4_0_INTEGRATION_GAP_REGISTER.md` GAP-R4-01 to GAP-R4-05

3. **Procure/configure production EDC**
   - REDCap, Castor, or equivalent validated system
   - CRF design: use `CRFVersionRegistry` and `DataDictionary` contracts as specification

4. **Engage independent qualification assessor**
   - Requirements: `R5_0_QUALIFICATION_FRAMEWORK.md` section 4
   - Test plan to execute: `R5_0_QUALIFICATION_TEST_PLAN.md`
   - Gaps to close: `R5_0_QUALIFICATION_GAP_REGISTER.md`

### When above are complete

5. **Record gate closures** — for each condition met, provide written evidence and update gate ledger
6. **Activate retrospective pilot** — after Pilot Activation Gate opens (36 conditions)

---

## Key invariants that must never be violated

1. **No real patient data** through the synthetic harness
2. **No write operations** to eHospital/HIS — boundary is read-only only
3. **Ethics gate** must be open before any participant contact or data access
4. **WORM audit trail** must be operational before locking any real dataset
5. **Independent assessor** must execute and sign qualification before go-live
6. **Dr Luân must approve** every gate transition — Claude Code cannot self-approve
7. **All outputs carry disclaimer:** "Cần bác sĩ kiểm chứng"

---

## Contacts and references

| Reference | Location |
|---------|---------|
| Open dependency register | `RESEARCH_OS_EXTERNAL_DEPENDENCY_REGISTER.md` |
| Production readiness gaps | `RESEARCH_OS_PRODUCTION_READINESS_GAP_REGISTER.csv` |
| Go/no-go master | `RESEARCH_OS_GO_NO_GO_MASTER_REGISTER.md` |
| Traceability matrix | `RESEARCH_OS_FINAL_TRACEABILITY_MATRIX.csv` |
| Executive summary | `RESEARCH_OS_COMPLETION_EXECUTIVE_SUMMARY.md` |
| Completion control | `RESEARCH_OS_COMPLETION_CONTROL.md` |

---

## Final statement

```
Research OS Pre-Production Readiness Package: COMPLETE
Program phases delivered: R1.2, R1.3, R2.0, R3.0, R4.0, R5.0, R6.0
Final test suite: 1049 passed / 0 failed
External dependencies: 18 OPEN
Production readiness gaps: 32+ OPEN
Qualification status: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

This handover pack is DRAFT and REQUIRES HUMAN REVIEW.
Cần bác sĩ kiểm chứng.
```
