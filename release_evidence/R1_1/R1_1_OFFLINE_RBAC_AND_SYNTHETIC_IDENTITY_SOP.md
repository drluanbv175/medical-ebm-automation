# R1.1 Offline RBAC and Synthetic Identity — SOP

**Document:** R1_1_OFFLINE_RBAC_AND_SYNTHETIC_IDENTITY_SOP.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Mục đích

SOP này mô tả cách sử dụng R1.1 Offline RBAC Harness và Synthetic Identity Fixtures trong môi trường phát triển/kiểm thử. R1.1 là một **harness kiểm thử offline** — KHÔNG phải hạ tầng identity production.

---

## Phạm vi và giới hạn

### Trong phạm vi
- Kiểm thử RBAC policy offline với synthetic actors
- Kiểm thử SoD guards (8 prohibited scenarios)
- Kiểm thử delegation lifecycle (PROPOSED → ACTIVE → EXPIRED/REVOKED/REJECTED)
- Kiểm thử audit hash chain và tamper detection
- Tài liệu hóa RBAC schema cho R1.2 design review

### Ngoài phạm vi — TUYỆT ĐỐI KHÔNG
- Kết nối SSO, LDAP, OAuth, Google Workspace, Microsoft Entra, eHospital
- Tạo user thật, email thật, password thật, access token, session token, MFA secret, API key
- Dùng PII hoặc patient data hoặc dữ liệu nghiên cứu thật
- Tuyên bố synthetic actor là authenticated user thật
- Tuyên bố audit event hiện tại là audit trail production
- Tuyên bố electronic signature, ethics approval, PI approval, independent review
- Tích hợp EDC, eHospital hoặc dữ liệu thật

---

## Module và CLI

### Python modules (offline only)
| Module | Mục đích |
|--------|----------|
| `research_project/project_rbac_simulation.py` | SyntheticActor, RBAC policy, SoD guards |
| `research_project/project_delegation_registry.py` | Append-only delegation JSONL registry |
| `research_project/project_audit_attribution.py` | SHA-256 hash chain audit JSONL ledger |

### CLI commands (synthetic only)
| Command | Mục đích |
|---------|----------|
| `rbac-simulate` | Mô phỏng RBAC decision cho synthetic actor |
| `delegation-register` | Tạo delegation record trong append-only JSONL |
| `delegation-status` | Kiểm tra status của một delegation |
| `audit-attribution-verify` | Verify hash chain integrity của audit ledger |

---

## Quy trình sử dụng

### Bước 1 — Chạy test harness
```bash
MRAQ_OFFLINE_CI=1 pytest tests/test_r1_1_offline_rbac_synthetic_identity.py -v
```
Tất cả test phải PASS trước khi tiến sang B2.

### Bước 2 — RBAC simulation
```bash
researchctl rbac-simulate \
  --actor-id SYN-PI-001 \
  --action EDIT_DRAFT_ARTIFACT \
  --object-ref "ARTIFACT-PROTOCOL-001"
```
Output sẽ cho biết ALLOW hoặc BLOCK + reason_code.

### Bước 3 — Delegation lifecycle
```bash
# Tạo delegation
researchctl delegation-register \
  --principal-id SYN-PI-001 \
  --delegatee-id SYN-STAT-001 \
  --role CO_INVESTIGATOR \
  --actions EDIT_DRAFT_ARTIFACT VIEW_AUDIT_LOG \
  --from-utc 2026-06-28T00:00:00+00:00 \
  --until-utc 2026-12-31T00:00:00+00:00 \
  --reason "Dry run delegation" \
  --ledger /tmp/delegation_ledger.jsonl

# Kiểm tra status
researchctl delegation-status \
  --delegation-id DEL-<ID> \
  --ledger /tmp/delegation_ledger.jsonl
```

### Bước 4 — Audit attribution + verify
```bash
researchctl audit-attribution-verify \
  --ledger /tmp/audit_ledger.jsonl
```
Output: PASS (hash chain intact) hoặc FAIL (errors listed).

---

## Synthetic identity invariants (không được vi phạm)

| # | Invariant |
|---|-----------|
| I-01 | `is_synthetic=True` bắt buộc trên mọi actor |
| I-02 | `authentication_state='NOT_AUTHENTICATED'` bắt buộc |
| I-03 | `identity_assurance='SIMULATED_ONLY'` bắt buộc |
| I-04 | `production_valid=False` trên mọi audit event |
| I-05 | `synthetic_actor_id` phải theo format `SYN-ROLE-NNN` |
| I-06 | Không chứa email, phone, hoặc long numeric ID trong bất kỳ trường nào |
| I-07 | `FORBIDDEN_ACTIONS_ALL_ROLES` bị block trước mọi RBAC check |
| I-08 | Audit ledger: không có DELETE, không có UPDATE |

---

## Kết luận bắt buộc

```
RBAC harness:              IMPLEMENTED (R1.1)
Synthetic identity:        IMPLEMENTED (R1.1)
Delegation lifecycle:      IMPLEMENTED (R1.1)
Audit hash chain:          IMPLEMENTED (R1.1)
SSO integration:           NOT IMPLEMENTED
MFA enforcement:           NOT IMPLEMENTED
Authenticated audit:       NOT IMPLEMENTED
Production deployment:     NOT APPLICABLE (offline harness only)
Qualification:             NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
