# R1.0 Audit Attribution Requirements

**Document:** R1_0_AUDIT_ATTRIBUTION_REQUIREMENTS.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Phân biệt bắt buộc

```
Current offline audit event
≠
Authenticated production audit event
```

| Thuộc tính | Offline (hiện tại) | Production (tương lai) |
|-----------|-------------------|----------------------|
| Actor source | String do user cung cấp | Authenticated ID từ identity provider |
| Identity verification | Không có | MFA + SSO verified |
| Role at event time | Không có | Ghi từ RBAC service tại thời điểm event |
| Tamper protection | Append-only JSONL | Write-once với hash chain / integrity seal |
| Legal / GCP value | Offline draft only | Verifiable audit trail |
| Delegation reference | Không có | delegation_id nếu action là delegated |

---

## Cấu trúc audit event bắt buộc cho production

Mỗi production audit event phải chứa tất cả các trường sau:

```yaml
event_id:                         UUID v4 — unique, không tái sử dụng
authenticated_actor_id:           ID từ institutional identity provider (không phải username string)
actor_display_name:               tên hiển thị — chỉ để đọc, không dùng cho lookup
actor_role_at_event_time:         role trong RBAC service tại thời điểm event
delegation_reference_if_any:      delegation_id nếu action được thực hiện theo delegation; null nếu PI direct
session_or_authentication_context_reference:
                                  session_id gắn với authentication event; cho phép cross-reference với auth log
action_type:                      enum — xem danh sách action types bên dưới
object_id:                        ID của artifact/record bị tác động
object_type:                      loại artifact (PROJECT | EVIDENCE_SOURCE | CLAIM | REVIEW | EXPORT | ROLE | ...)
object_version:                   version của artifact tại thời điểm action
before_state_hash_if_applicable:  SHA-256 của state trước khi thay đổi; null cho create events
after_state_hash_if_applicable:   SHA-256 của state sau khi thay đổi; null cho read/view events
timestamp_utc:                    ISO 8601 với timezone UTC — từ trusted time source
reason:                           mô tả ngắn lý do action (bắt buộc cho privileged actions)
network_context_policy:           IP address handling per institutional data privacy policy
integrity_protection_method:      phương pháp bảo vệ tính toàn vẹn của event này
```

---

## Danh sách action_type

```
PROJECT_CREATED
PROJECT_MODIFIED
PROJECT_ARCHIVED

EVIDENCE_SOURCE_ADDED
EVIDENCE_SOURCE_VERIFIED_HUMAN
EVIDENCE_SOURCE_MARKED_RETRACTED
EVIDENCE_SOURCE_EXCLUDED

CLAIM_REGISTERED
CLAIM_STATUS_CHANGED

REVIEW_CREATED
REVIEW_DECISION_RECORDED
REVIEW_ATTESTATION_SIGNED

ROLE_ASSIGNED
ROLE_REVOKED
ROLE_ESCALATION_ATTEMPTED (alert)

DELEGATION_CREATED
DELEGATION_REVOKED

DATABASE_LOCKED
DATABASE_UNLOCK_REQUESTED
DATABASE_UNLOCKED

EXPORT_AUTHORIZED
EXPORT_EXECUTED
EXPORT_HASH_VERIFIED

ACCESS_GRANTED
ACCESS_REVOKED
ACCESS_REVIEWED

BREAK_GLASS_ACTIVATED
BREAK_GLASS_DEACTIVATED

AUDIT_LOG_INTEGRITY_VERIFIED
AUDIT_LOG_EXPORT

SYSTEM_CONFIG_CHANGED
USER_PROVISIONED
USER_DEPROVISIONED
```

---

## Integrity Protection Methods

### Option A: Hash Chain

Mỗi event chứa hash của event trước đó:

```
event_n.integrity_hash = SHA-256(event_n.content + event_{n-1}.integrity_hash)
```

- Bất kỳ sửa đổi nào trong chain sẽ làm vỡ tất cả hash sau đó
- Có thể verify offline
- Phải lưu genesis hash (hash của event đầu tiên) ở nơi tách biệt

### Option B: Write-Once Sink

Audit events được ghi vào write-once storage (WORM — Write Once Read Many):
- Cloud storage với object lock
- Append-only database với revoke permissions sau khi write
- External audit log service với tamper-evident guarantee

### Option C: Periodic Integrity Seal

Periodic batch seal bằng trusted timestamp authority:
- Mỗi N events, tạo seal = Sign(hash_of_batch, timestamp_authority_key)
- Seal được ghi vào separate tamper-evident record

**Tổ chức phải chọn và implement ít nhất một trong các phương pháp trên.**  
Lựa chọn phải được document trong Validation Package (EDC-04).

---

## Network Context Policy

IP address của actor là thông tin nhạy cảm theo một số quy định bảo vệ dữ liệu.

```
Institutional data privacy policy phải quy định:
- IP address có được ghi vào audit log không
- Nếu có: retention period
- Nếu không: alternative network context (subnet level, VPN indicator)
- Cho phép hay không cho phép cross-reference với identity
```

Tổ chức phải xác nhận policy trước khi implement audit log.

---

## Immutability Requirements

1. **Không có DELETE** — không event nào được xóa bởi bất kỳ role nào kể cả SYSTEM_ADMINISTRATOR
2. **Không có UPDATE** — mọi "correction" phải là event mới với reference đến event cũ cần được đính chính
3. **Admin không thể bypass** — kỹ thuật phải đảm bảo, không chỉ policy
4. **Backup phải include audit log** — và backup phải read-only
5. **Integrity verification** — phải chạy định kỳ và tạo verification event

---

## Retention

- Audit log phải được retain ít nhất bằng thời gian giữ dữ liệu nghiên cứu
- Đối với nghiên cứu lâm sàng GCP: tối thiểu 15 năm (xác nhận với tổ chức)
- Authentication logs: tối thiểu 2 năm hoặc per institutional policy
- Decommission procedure phải bao gồm audit log export và archive trước khi xóa

---

## Yêu cầu review định kỳ

| Review | Frequency | Owner |
|--------|-----------|-------|
| Audit log integrity check | Monthly | SECURITY_ADMINISTRATOR |
| Anomalous event review | Weekly | DATA_GOVERNANCE_QA_REVIEWER |
| Privileged action review | Monthly | PI + SECURITY_ADMINISTRATOR |
| Full audit trail review | Per monitoring visit | MONITOR |
| Annual audit log archive integrity | Annual | Validation Lead |

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
