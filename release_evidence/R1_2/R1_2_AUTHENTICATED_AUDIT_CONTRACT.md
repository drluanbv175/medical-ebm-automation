# R1.2 Authenticated Audit Contract

**Document:** R1_2_AUTHENTICATED_AUDIT_CONTRACT.md  
**Date:** 2026-06-28  
**Phase:** R1.2 — Design Only  
**Status:** DESIGN CONTRACT — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define the contract that governs how authenticated identity is attributed to audit events when a real Identity Provider is connected in R1.3+.

The offline harness (R1.1.x) uses `attribution_mode = SYNTHETIC_OFFLINE`. This contract defines the target contract for production audit attribution, **which is NOT IMPLEMENTED in R1.2**.

---

## 1. Attribution modes

| Mode | When used | Audit validity |
|------|-----------|---------------|
| `AUTHENTICATED` | Production: IdP connected, MFA satisfied | Valid for production audit trail |
| `SYNTHETIC_OFFLINE` | Offline test harness (R1.1.x, R1.2) | Valid for test harness only; NOT a production audit record |

All current audit events (R1.1.x harness) use `SYNTHETIC_OFFLINE`.  
Production audit attribution requires an external IdP — deferred to R1.3.

---

## 2. Required audit event fields when AUTHENTICATED

When attribution_mode = AUTHENTICATED (future, not implemented), each audit event must include:

| Field | Source | Requirement |
|-------|--------|-------------|
| `actor_id` | AuthenticationContext | Pseudonymous; non-empty; verified by IdP |
| `session_id` | AuthenticationContext | Unique per session; from IdP |
| `attribution_mode` | AUTHENTICATED | Not synthetic |
| `mfa_satisfied` | AuthenticationContext | Must be True |
| `roles_at_event_time` | RBAC engine | Snapshot of roles at time of event |
| `event_id` | Audit ledger | Unique; sequential |
| `sequence_number` | Audit ledger | Monotonic; verified |
| `previous_event_hash` | Audit ledger | Chain link |
| `audit_event_hash` | Compute on content | SHA-256 |
| `timestamp_utc` | System | Trusted time source required |
| `local_ledger_classification` | Constant | TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM (R1.2); production WORM in R1.3 |
| `disclaimer` | Always | "Cần bác sĩ kiểm chứng" + scope |

---

## 3. Attribution contract violations (must be detected and logged)

| Violation | Detection | Response |
|-----------|-----------|---------|
| `attribution_mode = SYNTHETIC_OFFLINE` on production event | Audit validator | BLOCK event; alert |
| `mfa_satisfied = False` on authenticated event | Audit validator | BLOCK event; require MFA |
| `actor_id` empty or null | Audit validator | BLOCK event; log anonymous attempt |
| `session_id` revoked | Session validator | BLOCK event; log revocation |
| Hash chain break | verify_hash_chain() | Flag all events after break |
| sequence_number gap | verify_hash_chain() | Flag deleted events |

---

## 4. Non-repudiation requirements (design)

For production audit attribution (R1.3 target):
- Each audit event must be attributable to a specific authenticated actor
- No event may be generated without a valid AuthenticationContext
- Attribution must survive session expiry (actor_id persisted in event, not resolved at query time)
- Off-system retention required (PROD-AUD-01; OPEN)

**Current status:** Non-repudiation NOT implemented. Offline harness uses synthetic actor IDs.

---

## 5. PROD-AUD-01 dependency

This contract CANNOT be fully satisfied until PROD-AUD-01 is addressed:
- WORM-capable storage: NOT IMPLEMENTED
- Off-system backup: NOT IMPLEMENTED
- Restore verification: NOT IMPLEMENTED
- Legal hold: NOT IMPLEMENTED

**PROD-AUD-01 status:** OPEN — target R1.3

---

## Conclusion

```
Authenticated audit attribution (production): NOT IMPLEMENTED
Attribution contract design: COMPLETE
PROD-AUD-01: OPEN
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
