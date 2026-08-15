# R1.0 Authentication and MFA Requirements

**Document:** R1_0_AUTHENTICATION_AND_MFA_REQUIREMENTS.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> Required for future production qualification.  
> Not implemented in current Research OS baseline.

---

## 1. Authentication Assurance Level

| Yêu cầu | Mô tả |
|---------|-------|
| **Minimum assurance level** | NIST SP 800-63B AAL2 hoặc tương đương — yêu cầu MFA và phishing-resistant authenticator cho privileged actions |
| **Privileged actions** | AAL3 được khuyến nghị: hardware authenticator cho database lock, export authorization, role assignment |
| **Basis** | NIST SP 800-63B; ICH E6(R2) GCP audit trail requirements; applicable institutional policy |
| **Rationale** | Nghiên cứu y khoa yêu cầu audit trail có giá trị pháp lý — authentication assurance là nền tảng |

---

## 2. Institutional SSO Requirement

| Yêu cầu | Mô tả |
|---------|-------|
| **Mandatory** | Tất cả production users phải authenticate qua institutional identity provider |
| **Protocols** | SAML 2.0 hoặc OpenID Connect (OIDC) — không chọn sản phẩm cụ thể |
| **Directory** | Institutional LDAP / Active Directory / Cloud Directory |
| **Local accounts** | Bị cấm cho production research use; chỉ dùng cho break-glass (xem mục 10) |
| **Status** | NOT IMPLEMENTED in current Research OS baseline |
| **Dependency** | R1.2: SSO integration design approval từ IT và tổ chức |

---

## 3. MFA Requirement

| Yêu cầu | Mô tả |
|---------|-------|
| **Enforcement** | Bắt buộc 100% — không có exception, bypass, hoặc fallback path không có MFA |
| **Scope** | Mọi production login; mọi privileged action; mọi API call từ research clients |
| **Second factor types** | TOTP app; hardware security key (FIDO2/WebAuthn); push notification — không chọn sản phẩm cụ thể |
| **Excluded factor types** | SMS OTP — không được dùng làm sole second factor (SIM swap risk) |
| **Recovery codes** | Phải được sinh, mã hóa, và stored off-device; usage tạo audit alert; recovery code không thay thế MFA |
| **MFA bypass test** | Mandatory — mọi auth path phải được test bởi independent security tester |
| **Status** | NOT IMPLEMENTED in current Research OS baseline |

---

## 4. Session Timeout

| Yêu cầu | Mô tả |
|---------|-------|
| **Idle timeout** | Tối đa 30 phút không hoạt động → session expired |
| **Absolute timeout** | Tối đa 8 giờ từ lúc authenticate → bắt buộc re-authenticate |
| **Privileged session** | Tối đa 1 giờ; kết thúc ngay khi privileged operation hoàn thành |
| **Re-authentication** | Bắt buộc trước mọi privileged action (database lock, export, role change) |
| **Session extension** | Không tự động extend; user phải re-authenticate |

---

## 5. Device and Session Management

| Yêu cầu | Mô tả |
|---------|-------|
| **Device registration** | Institutional managed devices được khuyến nghị; unmanaged device cần additional verification |
| **Concurrent sessions** | Tối đa số sessions đồng thời phải có policy; alert khi đăng nhập từ vị trí bất thường |
| **Session token** | Secure random token; HttpOnly; Secure flag; SameSite; không lưu trong URL |
| **Token binding** | Session token phải gắn với IP hoặc device fingerprint (theo institutional policy) |
| **Session listing** | User có thể xem và revoke active sessions |

---

## 6. Failed-Login Handling

| Yêu cầu | Mô tả |
|---------|-------|
| **Failed attempt logging** | Mọi failed login tạo audit event với timestamp, IP, username attempted |
| **Alert threshold** | Alert sau N failed attempts (N được xác định bởi institutional security policy) |
| **Account lockout** | Xem mục 7 |
| **Error message** | Generic — không tiết lộ nếu username tồn tại hay password sai |
| **Rate limiting** | Enforce rate limiting trên login endpoint |

---

## 7. Account Lockout

| Yêu cầu | Mô tả |
|---------|-------|
| **Lockout trigger** | Sau số lần thất bại do institutional policy quy định |
| **Lockout duration** | Tối thiểu: progressive delay (5 min → 30 min → 1h → manual unlock) |
| **Manual unlock** | Chỉ SYSTEM_ADMINISTRATOR được unlock; tạo audit event |
| **Lockout notification** | Alert đến PI và SECURITY_ADMINISTRATOR khi tài khoản research bị lock |
| **Break-glass exemption** | Break-glass account có lockout policy riêng — xem mục 10 |

---

## 8. Password Policy (Emergency Fallback Only)

> Password-only authentication KHÔNG được phép cho production research use.
> Mục này chỉ áp dụng cho break-glass emergency fallback accounts.

| Yêu cầu | Mô tả |
|---------|-------|
| **Minimum length** | Tối thiểu 16 ký tự |
| **Complexity** | Theo NIST SP 800-63B: không yêu cầu special characters bắt buộc nhưng cấm known-breached passwords |
| **Rotation** | Không bắt buộc rotate nếu không có breach indication (per NIST) |
| **Storage** | Salted bcrypt/argon2 — không plaintext, không MD5/SHA1 |
| **Breach check** | Check against known-breached password list (Have I Been Pwned hoặc tương đương) |
| **Break-glass only** | Password authentication dành riêng cho break-glass; tạo alert ngay khi dùng |

---

## 9. Service Account Policy

| Yêu cầu | Mô tả |
|---------|-------|
| **Service accounts** | Cho system-to-system integration; không dùng cho human login |
| **Credential rotation** | Automated rotation theo schedule |
| **Least privilege** | Service account chỉ có quyền tối thiểu cho chức năng cụ thể |
| **Secret management** | Credentials trong secret manager (vault), không hardcode, không trong config files |
| **Audit** | Mọi service account action tạo audit event |
| **Review** | Quarterly review — xóa service accounts không còn cần |

---

## 10. Break-Glass Access Policy

| Yêu cầu | Mô tả |
|---------|-------|
| **Trigger** | Chỉ khi identity provider hoàn toàn unavailable và research continuity yêu cầu |
| **Authorization** | Cần approval từ PI + SYSTEM_ADMINISTRATOR; logged ngay lập tức |
| **Alert** | Tự động alert đến SECURITY_ADMINISTRATOR và PI |
| **Duration** | Time-limited — kết thúc khi identity provider phục hồi hoặc hết thời gian được approve |
| **Post-use review** | Mandatory review sau mỗi lần dùng break-glass |
| **Audit** | Toàn bộ break-glass session được ghi lại trong separate audit trail |
| **MFA** | Break-glass account có MFA riêng — không dùng recovery code thông thường |

---

## 11. Access Revocation SLA

| Sự kiện | SLA |
|---------|-----|
| Leaver (rời tổ chức/nghiên cứu) | Trong vòng 24h — tài khoản deactivated, tất cả sessions terminated |
| Role change | Ngay lập tức — roles cũ bị revoke trước khi roles mới có hiệu lực |
| Security incident | Ngay lập tức — tài khoản bị suspend trong vòng 1h sau phát hiện |
| PI revokes delegation | Ngay lập tức |
| Emergency revocation | Trong vòng 1h cho SYSTEM_ADMINISTRATOR và SECURITY_ADMINISTRATOR |

---

## 12. Authentication Logging

Mọi authentication event phải được ghi với:

```
event_id
event_type (login_success / login_failure / logout / mfa_challenge / mfa_success / mfa_failure / session_expired / account_locked / break_glass_activated)
actor_username
authenticated_actor_id (từ identity provider — sau khi thành công)
session_id
timestamp_utc
ip_address
user_agent
authentication_method
mfa_method (nếu applicable)
failure_reason (nếu failure)
```

Authentication logs phải được:
- Lưu tách biệt với application logs
- Tamper-evident (hash chain hoặc write-once)
- Retain tối thiểu bằng thời gian giữ dữ liệu nghiên cứu
- Review hàng tháng bởi SECURITY_ADMINISTRATOR

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
