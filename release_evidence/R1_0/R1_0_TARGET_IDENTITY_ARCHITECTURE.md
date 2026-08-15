# R1.0 Target Identity Architecture

**Document:** R1_0_TARGET_IDENTITY_ARCHITECTURE.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc bắt buộc

```
No shared accounts.
No local password-only production deployment.
No reviewer independence claim based only on role labels.
No production review decision without authenticated actor attribution.
No identifiable-data access without least-privilege authorization.
```

---

## Sơ đồ tổng quan

```
┌────────────────────────────────────────────────────────────────────┐
│  ZONE 5: Access Governance Layer                                    │
│  (Joiner/Mover/Leaver · Periodic Review · Emergency · PAM)        │
└───────────────────────────┬────────────────────────────────────────┘
                            │ overlays all zones
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 4: Authenticated Audit Attribution Layer                      │
│  (actor_id · role_at_event · delegation_ref · object_hash · ts)   │
└───────────────────────────┬────────────────────────────────────────┘
                            │ write-once event stream
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 3: Delegation and Authority Register                          │
│  (PI delegation · start/end · permitted activities · revocation)   │
└───────────────────────────┬────────────────────────────────────────┘
                            │ delegation context
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 2: Research RBAC Service                                      │
│  (role assignment · least privilege · role expiry · SoD)          │
└───────────────────────────┬────────────────────────────────────────┘
                            │ authenticated token
┌───────────────────────────▼────────────────────────────────────────┐
│  ZONE 1: Institutional Identity Provider                            │
│  (SSO/directory · MFA · session · credential management)          │
│  → managed by institution IT, NOT by Research OS                   │
└────────────────────────────────────────────────────────────────────┘
```

**Quan trọng:** Research OS (dossier, evidence, claim) là Zone ngoài cấu
trúc này — nó tiêu thụ authenticated tokens từ Zone 1 và bị kiểm soát bởi
Zone 2-5. Không có zone nào ở trên viết trực tiếp vào Research OS mà không
qua Identity Provider authentication.

---

## ZONE 1: Institutional Identity Provider

**Phạm vi:** Quản lý danh tính thật do tổ chức (bệnh viện/trường đại học) vận hành.  
**Trạng thái hiện tại:** NOT IMPLEMENTED — chưa tích hợp trong baseline.

### Chức năng bắt buộc

| Chức năng | Mô tả |
|----------|-------|
| Directory service | LDAP / Active Directory / Cloud Directory do tổ chức quản lý |
| SSO integration | SAML 2.0 hoặc OIDC — single sign-on cho mọi research users |
| MFA enforcement | Bắt buộc cho 100% production users; không có bypass path |
| Credential lifecycle | Cấp, đổi, thu hồi credential theo joiner/mover/leaver |
| Session management | Session token với expiry; revocation on logout hoặc deactivation |
| Authentication event logging | Mọi login/logout/failure với timestamp và IP context |

### Ranh giới cứng

- KHÔNG tự xây identity provider riêng — phải dùng institutional directory
- KHÔNG local password-only — SSO bắt buộc; local account chỉ là break-glass
- KHÔNG chia sẻ account giữa người dùng — kỹ thuật cấm
- KHÔNG cho phép MFA bypass trên bất kỳ path nào

### Dependencies

- R1.2: SSO integration design approval từ IT và tổ chức

---

## ZONE 2: Research RBAC Service

**Phạm vi:** Quản lý phân quyền theo vai trò cho research workflows.  
**Trạng thái hiện tại:** DESIGN ONLY — chưa có persistence layer.

### Roles tối thiểu

```
PI
CO_INVESTIGATOR
METHODS_STATISTICS_REVIEWER
EVIDENCE_CITATION_REVIEWER
DATA_MANAGER
DATA_GOVERNANCE_QA_REVIEWER
MONITOR
SYSTEM_ADMINISTRATOR
SECURITY_ADMINISTRATOR
READ_ONLY_AUDITOR
```

### Nguyên tắc RBAC

| Nguyên tắc | Mô tả |
|-----------|-------|
| Least privilege | Mỗi role chỉ có quyền tối thiểu cần thiết |
| Need-to-know | Data access scope gắn với study và giai đoạn |
| Role expiry | Mọi role có ngày hết hạn — renewal phải explicit |
| Separation of duties | Author ≠ Approver; PI ≠ Independent Reviewer; Admin ≠ Research content approver |
| Role assignment audit | Mọi thay đổi role tạo audit event |
| No self-assignment | Không người dùng nào tự assign role cho mình |

### Ranh giới cứng

- `SYSTEM_ADMINISTRATOR` không được approve research content
- `PI` không được claim independent review của chính protocol mình viết
- `READ_ONLY_AUDITOR` không được modify bất kỳ artifact nào
- Role escalation kỹ thuật bị cấm (không phải chỉ policy)

---

## ZONE 3: Delegation and Authority Register

**Phạm vi:** Ghi nhận và kiểm soát ủy quyền từ PI sang Co-I và các role khác.  
**Trạng thái hiện tại:** NOT IMPLEMENTED.

### Cấu trúc delegation record

```
delegation_id:        unique identifier
delegator_id:         authenticated PI identity
delegatee_id:         authenticated Co-I/staff identity
study_id:             nghiên cứu áp dụng
permitted_activities: danh sách cụ thể nhiệm vụ được ủy quyền
start_date:           ngày hiệu lực
end_date:             ngày hết hạn bắt buộc
signed_by_pi:         authenticated signature của PI
delegation_basis:     lý do (travel, expertise, workload)
revocation_date:      điền khi thu hồi sớm
revocation_reason:    lý do thu hồi
```

### Nguyên tắc

- Delegation phải tồn tại và còn hiệu lực TRƯỚC khi delegatee thực hiện nhiệm vụ
- Mọi action của delegatee gắn delegation_id trong audit event
- PI có thể revoke delegation bất kỳ lúc nào với ngay lập tức hiệu lực
- Co-I không thể sub-delegate trừ khi PI cho phép rõ ràng

---

## ZONE 4: Authenticated Audit Attribution Layer

**Phạm vi:** Write-once immutable event store cho mọi research action.  
**Trạng thái hiện tại:** NOT IMPLEMENTED — audit log hiện tại là offline manual, không có authenticated actor.

### Phân biệt bắt buộc

```
Current offline audit event
≠
Authenticated production audit event
```

Audit log hiện tại (`review_ledger.jsonl`) ghi `reviewer_id` là **string do người dùng cung cấp** — không được xác thực bởi identity provider. Đây là **ghi nhận thủ công** phù hợp cho offline draft, nhưng KHÔNG đủ điều kiện cho production research.

### Yêu cầu audit event production

Xem chi tiết tại `R1_0_AUDIT_ATTRIBUTION_REQUIREMENTS.md`.

### Integrity protection

- Append-only store — không có DELETE, UPDATE
- Hash chain hoặc tamper-evident log (write-once sink)
- Audit log integrity test: TP-SEC-02
- Admin không được delete audit events ngay cả khi có quyền admin khác

---

## ZONE 5: Access Governance Layer

**Phạm vi:** Vòng đời quản trị quyền truy cập cho toàn bộ team nghiên cứu.  
**Trạng thái hiện tại:** NOT IMPLEMENTED.

### Joiner/Mover/Leaver process

| Sự kiện | Hành động bắt buộc | SLA |
|---------|-------------------|-----|
| Joiner (nhân sự mới) | Provision account, assign roles theo PI approval, training completion verify | Trước ngày làm việc đầu tiên |
| Mover (đổi role) | Update RBAC, revoke old roles, delegation update | Ngay ngày đổi role |
| Leaver (rời đề tài/tổ chức) | Deactivate account, revoke all roles, revoke delegation, transfer outstanding tasks | Trong 24h |

### Periodic access review

- Quarterly: PI review danh sách người có quyền truy cập study
- Quarterly: Admin review privileged accounts
- Monthly: Audit log integrity review
- Annual: Full access control audit

### Emergency access (Break-glass)

- Chỉ dùng khi identity provider unavailable
- Kích hoạt cần second approval
- Tạo alert tự động
- Audit với lý do và end-time
- Review ngay sau khi kết thúc

### Privileged Access Management

- Privileged action (admin changes, export, lock) cần just-in-time elevation
- Privileged session được ghi lại toàn bộ
- Periodic privileged account review

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
