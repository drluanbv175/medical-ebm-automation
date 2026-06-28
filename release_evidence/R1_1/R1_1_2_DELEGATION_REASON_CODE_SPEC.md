# R1.1.2 Delegation Reason Code Specification

**Document:** R1_1_2_DELEGATION_REASON_CODE_SPEC.md  
**Date:** 2026-06-28  
**Phase:** R1.1.2 — Phase C + F  
**Source file:** `research_project/project_delegation_registry.py`  
**Branch:** feat/r1-1-2-design-gap-remediation  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## 1. Mục đích

Đặc tả `DelegationReasonCode` enum và `DelegationDecision` dataclass — cấu trúc kết quả
của `evaluate_delegation_action()`. Thay thế chuỗi plain-string trả về từ `get_status()`.

Nguồn gap: AC-05 (R1.1.1) + DEL-REASON (R1.1.2 Gap Baseline Table).

---

## 2. DelegationReasonCode — 9 giá trị

| Code | Giá trị chuỗi | Ý nghĩa | Khi nào trả về |
|------|--------------|---------|----------------|
| `DELEGATION_EXPIRED` | `"DELEGATION_EXPIRED"` | Delegation đã qua `effective_until_utc` | Status=ACTIVE nhưng `compute_status()` → EXPIRED |
| `DELEGATION_REVOKED` | `"DELEGATION_REVOKED"` | Delegation bị thu hồi | Status=REVOKED trong ledger |
| `DELEGATION_NOT_ACTIVE` | `"DELEGATION_NOT_ACTIVE"` | Delegation chưa activate (PROPOSED) hoặc bị reject | Status=PROPOSED hoặc REJECTED |
| `DELEGATION_SCOPE_EXCEEDED` | `"DELEGATION_SCOPE_EXCEEDED"` | Action không nằm trong `permitted_actions` | Action valid nhưng không trong scope |
| `DELEGATION_FORBIDDEN_AUTHORITY` | `"DELEGATION_FORBIDDEN_AUTHORITY"` | Action nằm trong `FORBIDDEN_ACTIONS_ALL_ROLES` | Action bị cấm toàn hệ thống |
| `DELEGATION_SELF_ASSIGNMENT` | `"DELEGATION_SELF_ASSIGNMENT"` | Principal và delegatee là cùng một actor | Trong `_validate_delegation()` của Registry |
| `DELEGATION_DISABLED_ACTOR` | `"DELEGATION_DISABLED_ACTOR"` | Actor bị vô hiệu hóa | Dành cho R1.3 production |
| `DELEGATION_PERMITTED` | `"DELEGATION_PERMITTED"` | Delegation hợp lệ, action được phép | Happy path |
| `DELEGATION_NOT_FOUND` | `"DELEGATION_NOT_FOUND"` | `delegation_id` không tồn tại trong ledger | Registry không tìm thấy |

### Phân loại theo chiều

| Chiều | Codes |
|-------|-------|
| BLOCK — Vòng đời | DELEGATION_EXPIRED · DELEGATION_REVOKED · DELEGATION_NOT_ACTIVE |
| BLOCK — Phạm vi | DELEGATION_SCOPE_EXCEEDED · DELEGATION_FORBIDDEN_AUTHORITY |
| BLOCK — Identity | DELEGATION_SELF_ASSIGNMENT · DELEGATION_DISABLED_ACTOR |
| BLOCK — Lookup | DELEGATION_NOT_FOUND |
| ALLOW | DELEGATION_PERMITTED |

---

## 3. DelegationDecision — 11 trường bắt buộc

| Trường | Kiểu | Mô tả |
|--------|------|-------|
| `decision` | `str` | `"ALLOW"` hoặc `"BLOCK"` |
| `reason_code` | `str` | Một trong 9 `DelegationReasonCode` values |
| `policy_reference` | `str` | Tham chiếu policy rule (vd `"DELEGATION_POLICY-EXPIRED"`) |
| `delegation_id` | `Optional[str]` | ID của delegation đang evaluate |
| `actor_reference` | `str` | Synthetic actor ID |
| `action` | `str` | Action đang request |
| `object_reference` | `str` | Object ID (mặc định `"UNSPECIFIED"` nếu không cung cấp) |
| `effective_until_utc` | `Optional[str]` | Thời hạn của delegation (ISO 8601) |
| `evaluated_at_utc` | `str` | Thời điểm đánh giá (ISO 8601) |
| `timestamp_utc` | `str` | Timestamp hiện tại (ISO 8601) |
| `disclaimer` | `str` | Inherited từ `_DELEGATION_DISCLAIMER` |

---

## 4. evaluate_delegation_action() — thứ tự kiểm tra

Hàm `evaluate_delegation_action(registry, delegation_id, actor_reference, action, object_reference, now_utc)` áp dụng các guard theo thứ tự sau:

```
1. Registry lookup         → NOT_FOUND nếu không tồn tại
2. REVOKED check           → DELEGATION_REVOKED
3. REJECTED check          → DELEGATION_NOT_ACTIVE
4. PROPOSED check          → DELEGATION_NOT_ACTIVE
5. Expiry check            → DELEGATION_EXPIRED
6. Forbidden authority     → DELEGATION_FORBIDDEN_AUTHORITY (action in FORBIDDEN_ACTIONS_ALL_ROLES)
7. Scope check             → DELEGATION_SCOPE_EXCEEDED (action not in permitted_actions)
8. Allow                   → DELEGATION_PERMITTED
```

---

## 5. Policy reference format

| Kịch bản | policy_reference |
|---------|-----------------|
| Not found | `"DELEGATION_POLICY-NOT_FOUND"` |
| Revoked | `"DELEGATION_POLICY-REVOKED"` |
| Rejected | `"DELEGATION_POLICY-REJECTED"` |
| Proposed/not activated | `"DELEGATION_POLICY-NOT_ACTIVATED"` |
| Expired | `"DELEGATION_POLICY-EXPIRED"` |
| Forbidden authority | `"DELEGATION_POLICY-FORBIDDEN_AUTHORITY"` |
| Scope exceeded | `"DELEGATION_POLICY-SCOPE_EXCEEDED"` |
| Permitted | `"DELEGATION_POLICY-PERMITTED"` |

---

## 6. Phân biệt với RBACDecision

| Thuộc tính | `RBACDecision` | `DelegationDecision` |
|-----------|---------------|---------------------|
| Nguồn gốc | `evaluate_rbac()` | `evaluate_delegation_action()` |
| Reason code enum | `SoDViolation` | `DelegationReasonCode` |
| Context | Role-based action check | Delegation lifecycle + scope |
| `policy_reference` | SoD policy ID (e.g. `"SOD-07-NO-ACTIVE-ROLE"`) | Delegation policy (e.g. `"DELEGATION_POLICY-EXPIRED"`) |

---

## 7. Giới hạn — offline simulation

- `DELEGATION_DISABLED_ACTOR` được định nghĩa nhưng chưa có production logic — reserved cho R1.3
- `evaluate_delegation_action()` không xác thực identity thật — synthetic actor IDs only
- Không gọi network, không truy cập SSO/MFA
- Mọi decision là simulation, không phải enforcement thật

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
