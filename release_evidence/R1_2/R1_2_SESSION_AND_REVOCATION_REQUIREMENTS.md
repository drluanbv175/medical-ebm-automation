# R1.2 Session and Revocation Requirements

**Document:** R1_2_SESSION_AND_REVOCATION_REQUIREMENTS.md  
**Date:** 2026-06-28  
**Phase:** R1.2 — Design Only  
**Status:** REQUIREMENTS ONLY — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define requirements for session management and session revocation when the Medical Research OS is connected to a production Identity Provider.

**Current state:** No session management is implemented. The offline harness uses synthetic actor IDs with no real sessions. All requirements in this document are targets for R1.3+ implementation.

---

## 1. Session creation requirements

| Requirement | Requirement ID | Priority |
|------------|---------------|---------|
| Session created only after successful authentication AND MFA | SR-01 | MUST |
| session_id is globally unique (UUID v4 minimum) | SR-02 | MUST |
| Session has a defined expiry time (max 8 hours for research workflows) | SR-03 | MUST |
| Session issued_at recorded in UTC | SR-04 | MUST |
| Session binds to a single authenticated actor_id | SR-05 | MUST |
| Session records MFA method used | SR-06 | SHOULD |
| No session created in offline/synthetic mode | SR-07 | MUST |

---

## 2. Session validation requirements

| Requirement | Requirement ID | Priority |
|------------|---------------|---------|
| Every research action validates session before executing | SV-01 | MUST |
| Validation checks: session exists, not expired, not revoked | SV-02 | MUST |
| Expired sessions rejected; user must re-authenticate | SV-03 | MUST |
| Revoked sessions rejected; user must re-authenticate | SV-04 | MUST |
| Session validation failure logged as audit event | SV-05 | MUST |
| Session validation result is not cached beyond per-request lifetime | SV-06 | SHOULD |

---

## 3. Session revocation requirements

| Requirement | Requirement ID | Priority |
|------------|---------------|---------|
| Sessions revocable at any time by: user logout, admin action, security event | RV-01 | MUST |
| Revocation takes effect immediately (no delay) | RV-02 | MUST |
| All subsequent actions with revoked session_id DENIED | RV-03 | MUST |
| Revocation event logged to audit trail with actor_id and reason | RV-04 | MUST |
| Revocation does not delete prior audit events (audit immutability) | RV-05 | MUST |
| Bulk revocation (e.g., all sessions for an actor) supported | RV-06 | SHOULD |

---

## 4. Session store requirements

| Requirement | Requirement ID | Priority |
|------------|---------------|---------|
| Session store is external to the Research OS codebase | SS-01 | MUST |
| Session store persists across process restarts | SS-02 | MUST |
| Session store supports atomic read-validate-revoke | SS-03 | MUST |
| Session store access is authenticated (service credentials, NOT hardcoded) | SS-04 | MUST |
| Session store does not store plaintext credentials | SS-05 | MUST |

**Session store options (design only):**
- Redis with AUTH + TLS (recommended for session TTL management)
- PostgreSQL sessions table with row-level locking
- External IdP session registry (if IdP manages sessions natively)

**Implementation status:** EXTERNAL — NOT PROVIDED

---

## 5. Revocation trigger events

The following events MUST trigger immediate session revocation:

| Event | Trigger |
|-------|---------|
| User logs out | User action |
| Account disabled by admin | Admin action |
| Password change | Security action |
| MFA secret reset | Security action |
| Suspected credential compromise | Security alert |
| Role assignment revoked | RBAC action |
| SoD violation detected | Security action |
| Session idle timeout exceeded | Policy enforcement |

---

## 6. Connection to R1.1 delegation system

Session revocation must interact with the delegation system from R1.1:
- When an actor's session is revoked, all delegations where that actor is the delegatee must be reviewed for immediate suspension
- Delegations created during a revoked session should be flagged for audit review
- `DelegationReasonCode.DELEGATION_REVOKED` must be issued for any delegation suspended due to session revocation

---

## 7. Open dependencies

| Dependency | Status |
|-----------|--------|
| Production IdP (session issuance) | EXTERNAL — NOT PROVIDED |
| Session store | EXTERNAL — NOT PROVIDED |
| Security event bus (for revocation triggers) | EXTERNAL — NOT PROVIDED |

---

## Conclusion

```
Session management: REQUIREMENTS ONLY — NOT IMPLEMENTED
Session revocation: REQUIREMENTS ONLY — NOT IMPLEMENTED
Target: R1.3+
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
