# R1.3 Immutable Retention Provider Contract

**Document:** R1_3_IMMUTABLE_RETENTION_PROVIDER_CONTRACT.md  
**Date:** 2026-06-28  
**Phase:** R1.3 — Audit Retention Architecture  
**Status:** CONTRACT DESIGN — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Define the interface contract that any WORM retention provider adapter must fulfill. The `WormRetentionProviderInterface` in `audit_retention_contract.py` is the canonical source. This document is the human-readable specification.

---

## 1. Required interface methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `write_event` | `(event: dict) → WriteReceipt` | Write one audit event to WORM storage; returns a receipt |
| `read_event` | `(event_id: str) → dict` | Read one event by ID |
| `verify_event` | `(event_id: str, expected_hash: str) → bool` | Verify event hash against stored value |
| `create_legal_hold` | `(hold_id: str, scope: str) → None` | Create a legal hold on a set of events |
| `release_legal_hold` | `(hold_id: str, authority: str) → None` | Release a legal hold (requires explicit authority) |
| `list_events_in_range` | `(from_utc: str, to_utc: str) → list[str]` | List event IDs in a time range |
| `get_retention_policy` | `() → RetentionPolicy` | Return current retention policy object |
| `provider_health_check` | `() → bool` | Verify connectivity and writability of provider |

---

## 2. WriteReceipt contract

Each successful `write_event()` call must return a `WriteReceipt`:

| Field | Type | Requirement |
|-------|------|-------------|
| `provider_id` | str | Provider-assigned unique object ID |
| `provider_timestamp_utc` | str | ISO 8601; server-side timestamp from provider |
| `immutability_expiry_utc` | str | Calculated from retention policy; NULL if legal hold active |
| `etag` | str | Provider content hash/fingerprint |
| `provider_name` | str | e.g., "AWS_S3_OBJECT_LOCK" |
| `region` | str | Storage region |
| `is_worm_confirmed` | bool | True only when provider returns WORM confirmation |
| `disclaimer` | str | "Production WORM — requires human verification" OR "Synthetic simulation — NOT WORM" |

---

## 3. RetentionPolicy contract

| Field | Type | Value |
|-------|------|-------|
| `default_retention_years` | int | 7 (minimum for research audit) |
| `clinical_retention_years` | int | 10 |
| `ethics_retention_years` | int | 15 |
| `legal_hold_indefinite` | bool | True |
| `compliance_mode` | str | "GOVERNANCE" or "COMPLIANCE" — COMPLIANCE required for production |
| `cross_region_backup` | bool | Required True for production |

---

## 4. Forbidden behaviors

Any adapter implementing `WormRetentionProviderInterface` MUST NOT:

| Forbidden behavior | Reason |
|-------------------|--------|
| Return `is_worm_confirmed = True` without real WORM storage | Fraudulent claim |
| Allow `write_event()` to overwrite an existing event | Violates immutability |
| Allow `delete_event()` during retention or legal hold | Violates PROD-AUD-01 |
| Return fake provider timestamps | Breaks non-repudiation |
| Accept PII in event payloads without PII flag | Privacy violation |

The fake adapter (`FakeWormRetentionAdapter`) MUST set `is_worm_confirmed = False` and `disclaimer = "Synthetic simulation — NOT WORM"`.

---

## 5. FakeWormRetentionAdapter (offline harness)

The `FakeWormRetentionAdapter` in `audit_retention_contract.py` is the offline test implementation:
- Stores events in memory only (no persistence)
- `is_worm_confirmed` always False
- `provider_name` = `"FAKE_WORM_OFFLINE_SIMULATION"`
- `disclaimer` always = `"Synthetic simulation — NOT WORM — not for production audit trail"`
- All methods return valid-shaped objects with correct disclaimer

This adapter is ONLY for contract test verification. It MUST NOT be used in production.

---

## Conclusion

```
WORM provider contract design: COMPLETE
Real WORM provider implementation: NOT IMPLEMENTED
Fake adapter: OFFLINE SIMULATION ONLY
PROD-AUD-01: OPEN until real provider connected and verified
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
