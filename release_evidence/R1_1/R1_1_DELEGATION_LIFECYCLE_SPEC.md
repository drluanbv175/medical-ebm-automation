# R1.1 Delegation Lifecycle Specification

**Document:** R1_1_DELEGATION_LIFECYCLE_SPEC.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE  
**Source:** `research_project/project_delegation_registry.py`

---

## Nguyên tắc

- Registry là **append-only JSONL** — không DELETE, không UPDATE trực tiếp
- Mỗi thay đổi trạng thái tạo ra một dòng mới trong JSONL
- State của một delegation = dòng JSONL cuối có cùng `delegation_id`
- Không có e-signature, không kết nối SSO, không có approval thật

---

## Vòng đời (State Machine)

```
                    ┌──────────┐
              Tạo   │ PROPOSED │
            ─────►  └────┬─────┘
                         │
              ┌──────────┼──────────┐
              │ activate()│reject()  │
              ▼          │           ▼
        ┌────────┐       │     ┌──────────┐
        │ ACTIVE │       │     │ REJECTED │  (terminal)
        └───┬────┘       │     └──────────┘
            │            ▼
            │       (REJECTED = terminal)
            │
     ┌──────┴────────┐
     │               │
     │ revoke()   expires (auto)
     ▼               ▼
┌─────────┐    ┌─────────┐
│ REVOKED │    │ EXPIRED │  (cả hai terminal)
└─────────┘    └─────────┘
```

---

## Trạng thái

| Status | Ý nghĩa | Terminal? |
|--------|---------|-----------|
| `PROPOSED` | Đã tạo, chờ kích hoạt | Không |
| `ACTIVE` | Đang hiệu lực trong date window | Không |
| `EXPIRED` | Qua `effective_until_utc` | Có |
| `REVOKED` | PI thu hồi trước hạn | Có |
| `REJECTED` | PI từ chối đề xuất | Có |

---

## DelegationRecord schema

| Trường | Bắt buộc | Mô tả |
|--------|----------|-------|
| `delegation_id` | ✓ | DEL-{12 hex ký tự uppercase} |
| `principal_synthetic_actor_id` | ✓ | Người ủy quyền (thường PI) |
| `delegatee_synthetic_actor_id` | ✓ | Người nhận ủy quyền |
| `delegated_role` | ✓ | Role được ủy thác |
| `permitted_actions` | ✓ | Danh sách action được phép (không chứa forbidden actions) |
| `effective_from_utc` | ✓ | Ngày bắt đầu (ISO-8601) |
| `effective_until_utc` | ✓ | Ngày kết thúc (ISO-8601) |
| `reason` | ✓ | Lý do ủy quyền |
| `status` | ✓ | Trạng thái hiện tại |
| `created_at_utc` | ✓ | Thời điểm tạo record |
| `revoked_at_utc` | Không | Thời điểm thu hồi (nếu có) |
| `revocation_reason` | Không | Lý do thu hồi/từ chối |
| `disclaimer` | ✓ | "Manual attestation reference only…" |

---

## Validation guards

| Guard | Điều kiện bị block |
|-------|--------------------|
| Self-delegation | `principal_id == delegatee_id` → `DelegationError` |
| Forbidden action | `permitted_actions` chứa bất kỳ action trong `FORBIDDEN_ACTIONS_ALL_ROLES` → `DelegationError` |
| Empty actions | `permitted_actions` rỗng → `DelegationError` |
| Invalid date window | `effective_until_utc <= effective_from_utc` → `DelegationError` |
| Invalid state transition | Activate/revoke từ terminal state → `DelegationError` |

---

## Audit trail

Mỗi lần thay đổi state (propose, activate, revoke, reject) tạo ra 1 dòng JSONL mới.
Để tra cứu, đọc toàn bộ file và lấy dòng cuối cùng có cùng `delegation_id`.

---

## Câu chữ bắt buộc

```
Manual attestation reference only.
Not an authenticated delegation mechanism.
Not an electronic signature or legal authorization.
```

Câu này PHẢI xuất hiện trong mọi `DelegationRecord.to_dict()` dưới trường `disclaimer`.

---

## Kết luận bắt buộc

```
Delegation lifecycle:            IMPLEMENTED (offline append-only JSONL)
Authenticated delegation:        NOT IMPLEMENTED
PI authenticated signature:      NOT IMPLEMENTED
Institutional approval:          NOT APPLICABLE
Electronic signature:            NOT APPLICABLE
Delegation_id in audit events:   SIMULATED (R1.1 only)
Production delegation register:  NOT IMPLEMENTED (R1.4)
Qualification:                   NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
