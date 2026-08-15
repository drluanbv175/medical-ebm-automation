# R1.3 Retention Policy Requirements

**Document:** R1_3_RETENTION_POLICY_REQUIREMENTS.md  
**Date:** 2026-06-28  
**Phase:** R1.3 — Audit Retention Architecture  
**Status:** REQUIREMENTS — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Retention period requirements by record type

| Record type | Min retention | Regulatory basis | Notes |
|------------|--------------|-----------------|-------|
| Research audit events | 7 years | Circular 44/2014/TT-BYT | From last event date |
| Clinical research audit events | 10 years | Circular 44/2014/TT-BYT | From last patient contact |
| Ethics and consent records | 15 years | ICH-GCP E6 R2 §8 | Or life of study + 3, whichever is longer |
| Adverse event / safety records | 15 years | ICH-GCP E6 R2 §5.5 | From study completion |
| Protocol and amendments | 15 years | ICH-GCP E6 R2 §8 | |
| Data lock and freeze records | 10 years | GCP + local | |
| Authorization and delegation records | 7 years | RBAC governance policy | |

---

## 2. Legal hold requirements

| Requirement | ID | Priority |
|------------|-----|---------|
| Legal hold overrides retention expiry | LH-01 | MUST |
| Hold created with: hold_id, scope, created_by, justification | LH-02 | MUST |
| Hold release requires explicit authority record | LH-03 | MUST |
| Hold release logged as audit event | LH-04 | MUST |
| No deletion permitted while any hold is active | LH-05 | MUST |
| Multiple simultaneous holds on same event allowed | LH-06 | MUST |

---

## 3. Compliance mode requirements

| Mode | Description | Requirement |
|------|-------------|-------------|
| GOVERNANCE | Admin/owner CAN delete before expiry | NOT acceptable for research audit |
| COMPLIANCE | Even admin CANNOT delete before expiry | REQUIRED for research audit |

**Requirement:** Production WORM storage MUST use COMPLIANCE mode (or equivalent).

---

## 4. Deletion policy

Deletion is only permitted when ALL of the following are true:
1. Retention period has expired
2. No legal holds are active on the record
3. Institutional records officer has authorized deletion in writing
4. Deletion is logged as an audit event on a separate, retained deletion log

**Auto-deletion:** NOT PERMITTED. All deletions must be explicit and authorized.

---

## 5. Backup requirements

| Requirement | ID | Priority |
|------------|-----|---------|
| Primary WORM store has off-system backup | BR-01 | MUST |
| Backup is in separate account/region from primary | BR-02 | MUST |
| Backup has same or longer retention than primary | BR-03 | MUST |
| Backup restore test run ≥ quarterly | BR-04 | MUST |
| Restore verification uses hash comparison against write receipts | BR-05 | MUST |
| Backup access credentials are separate from primary | BR-06 | MUST |

---

## 6. Implementation status

| Requirement set | Status |
|----------------|--------|
| Retention periods (design) | COMPLETE |
| Legal hold design | COMPLETE |
| Compliance mode requirement | COMPLETE |
| Deletion policy | COMPLETE |
| Backup requirements | COMPLETE |
| Implementation of any of the above | NOT IMPLEMENTED |

---

## Conclusion

```
Retention policy design: COMPLETE
Retention enforcement implementation: NOT IMPLEMENTED
PROD-AUD-01: OPEN
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
