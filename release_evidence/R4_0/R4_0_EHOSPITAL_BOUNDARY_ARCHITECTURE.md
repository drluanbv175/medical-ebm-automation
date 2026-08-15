# R4.0 eHospital Read-Only Research Data Boundary — Architecture

**Document:** R4_0_EHOSPITAL_BOUNDARY_ARCHITECTURE.md  
**Date:** 2026-06-28  
**Phase:** R4.0 — eHospital Read-Only Research Data Boundary  
**Status:** DESIGN ONLY — NOT CONNECTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Critical constraints

- **NO real eHospital connection** exists in this harness
- **NO production HIS/EMR/LIS/PACS** is connected
- **NO SSO/OAuth/LDAP** authentication is wired
- **NO patient data** flows through this system
- All connection points are `NOT_IMPLEMENTED` stubs with explicit dependency constants

---

## 1. Architecture overview

```
Research OS (offline harness)
        ↕
EHospitalReadOnlyBoundaryInterface  ←── CONTRACT (this phase)
        ↕
[EXTERNAL: production eHospital API]  ←── NOT_IMPLEMENTED
        ↕
[EXTERNAL: HIS / EMR / LIS]          ←── NOT_CONNECTED
        ↕
[EXTERNAL: Pseudonymization service]  ←── NOT_IMPLEMENTED
```

The boundary enforces 3 invariants at the contract level:
1. **Read-only** — interface has no write/update/delete methods
2. **Ethics-gated** — every ExtractRequest requires non-empty `ethics_approval_ref`
3. **Pseudonymized** — ExtractRecord refuses data with PII keys; PseudonymizedSubject requires 64-char pseudo_id

---

## 2. Data flow (when real connection exists — FUTURE)

```
1. Ethics approval obtained (SAG-01)
2. Extract request submitted with ethics_approval_ref
3. Request approved by data manager (external step)
4. Pseudonymization service hashes real patient IDs with institutional salt
5. Pseudonymized extract returned to Research OS
6. Research OS ingests to synthetic EDC (SyntheticRecord)
7. Research OS never receives real patient identifiers
```

---

## 3. Security design principles

| Principle | Design decision |
|----------|----------------|
| Read-only | Interface has zero write methods (verified by test) |
| Minimum data | Domain whitelist with 8 approved domains; 8 blocked |
| PII-free transport | ExtractRecord.__post_init__ rejects PII key names |
| Ethics prerequisite | No extract without ethics_approval_ref |
| Pseudonymization | SHA-256 pseudo_id (64-char hex); real ID never stored |
| Offline by default | All production connectors are NOT_IMPLEMENTED constants |

---

## 4. External dependencies (all OPEN)

| Dependency | ID | Status |
|-----------|-----|--------|
| eHospital/HIS read-only API | DEP-11 | EXTERNAL — NOT PROVIDED |
| Service account credentials | DEP-12 | EXTERNAL — NOT PROVIDED |
| Pseudonymization key vault | DEP-13 | EXTERNAL — NOT PROVIDED |
| Network/VPN access to HIS | DEP-14 | EXTERNAL — NOT PROVIDED |
| Data access agreement (DAA) | DEP-15 | EXTERNAL — NOT PROVIDED |

---

## Conclusion

```
eHospital boundary contract: DESIGN COMPLETE (offline only)
Real HIS connection: NOT IMPLEMENTED — EXTERNAL
Patient data: BLOCKED
Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
