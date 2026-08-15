# R1.1 Audit Attribution Simulation Specification

**Document:** R1_1_AUDIT_ATTRIBUTION_SIMULATION_SPEC.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE  
**Source:** `research_project/project_audit_attribution.py`

---

## Nguyên tắc

- Ledger là **append-only JSONL** — không DELETE, không UPDATE
- Mỗi event mang `audit_event_hash` (SHA-256) và `previous_event_hash` (hash chain)
- `is_synthetic=True` và `production_valid=False` là bất biến không thể thay đổi
- Không chứa PII, không chứa credential thật, không kết nối SSO

---

## SyntheticAuditEvent — 17 trường bắt buộc

| # | Trường | Mô tả |
|---|--------|-------|
| 1 | `event_id` | AUD-{12 hex uppercase} |
| 2 | `synthetic_actor_id` | SYN-ROLE-NNN của actor |
| 3 | `actor_role_at_event_time` | Role của actor tại thời điểm event |
| 4 | `delegation_reference_if_any` | delegation_id nếu là delegated action (None nếu không) |
| 5 | `authentication_context` | `"SIMULATED_NOT_AUTHENTICATED"` (bất biến) |
| 6 | `action_type` | Loại action (enum AuditActionType) |
| 7 | `object_id` | ID của artifact/resource bị tác động |
| 8 | `object_version` | Version của object |
| 9 | `before_state_hash_if_applicable` | SHA-256 của state trước (None nếu không áp dụng) |
| 10 | `after_state_hash_if_applicable` | SHA-256 của state sau (None nếu không áp dụng) |
| 11 | `timestamp_utc` | ISO-8601 UTC |
| 12 | `reason` | Lý do action |
| 13 | `integrity_protection_method` | `"SHA256_HASH_CHAIN_SYNTHETIC"` |
| 14 | `is_synthetic` | `True` (bắt buộc, không thể False) |
| 15 | `production_valid` | `False` (bắt buộc, không thể True) |
| 16 | `audit_event_hash` | SHA-256(JSON của event không có trường này, sort_keys=True) |
| 17 | `previous_event_hash` | hash của event trước, hoặc `"GENESIS"` cho event đầu |

---

## Hash chain algorithm

```
Với event thứ n:
  content = json.dumps(event_dict_without_audit_event_hash, sort_keys=True, ensure_ascii=True)
  event_n.audit_event_hash = sha256(content.encode("ascii")).hexdigest()
  event_n.previous_event_hash = event_{n-1}.audit_event_hash  (hoặc "GENESIS" nếu n=0)

Verification:
  1. Recompute hash của mỗi event
  2. So sánh với stored audit_event_hash
  3. Kiểm tra previous_event_hash khớp với hash của event liền trước
  4. Nếu bất kỳ không khớp → tamper detected
```

---

## Immutability invariants

| Invariant | Mô tả |
|-----------|-------|
| Không có DELETE | `AuditAttributionLedger` không có method `.delete()`, `.remove()`, `.clear()` |
| Không có UPDATE | Không có method `.update()` hay ghi đè record |
| Append-only | Chỉ có `.record()` ghi thêm vào cuối file |
| Hash chain | Mọi sửa đổi sau khi ghi đều bị detect bởi `verify()` |

---

## Supported AuditActionType

| Nhóm | Actions |
|------|---------|
| Research workflow | PROJECT_CREATED · ARTIFACT_EDITED · ARTIFACT_LOCKED · ARTIFACT_UNLOCKED · REVIEW_ATTESTATION_RECORDED · EVIDENCE_ATTESTATION_RECORDED · CLAIM_REGISTERED · CLAIM_RETRACTED · REVISION_REQUESTED · EXPORT_REQUESTED |
| Identity/delegation | ROLE_ASSIGNED · ROLE_REVOKED · DELEGATION_PROPOSED · DELEGATION_ACTIVATED · DELEGATION_REVOKED · DELEGATION_REJECTED |
| Audit meta | AUDIT_VERIFICATION_RUN · RBAC_DECISION_BLOCK · RBAC_DECISION_ALLOW |
| Access | AUDIT_LOG_VIEWED · EVIDENCE_LEDGER_VIEWED · SYSTEM_CONFIG_VIEWED · SYSTEM_CONFIG_MODIFIED · DATA_LOCKED · DATA_UNLOCKED |

---

## Câu chữ bắt buộc

```
Simulated audit attribution only.
Not a production audit trail.
Not an authenticated event record.
```

Xuất hiện trong trường `disclaimer` của mỗi event dict và trong output của CLI `audit-attribution-verify`.

---

## Kết luận bắt buộc

```
Audit attribution:              SIMULATED (SHA-256 hash chain, JSONL)
Authenticated actor_id:         NOT PRESENT (synthetic only)
WORM storage:                   NOT IMPLEMENTED
Immutability (production):      NOT IMPLEMENTED
Audit trail (production):       NOT IMPLEMENTED (R1.3)
Qualification:                  NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
