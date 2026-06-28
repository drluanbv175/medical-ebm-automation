# R1.0 Delegation and Attestation Policy

**Document:** R1_0_DELEGATION_AND_ATTESTATION_POLICY.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Tuyên bố chính xác về ReviewLedger hiện tại

```
ReviewLedger hiện tại là:
  offline append-only manual-attestation mechanism;
  not an authenticated signature;
  not a legal, ethics, institutional or regulatory approval mechanism.
```

Đây là mô tả đúng, không phải chỉ trích. Hệ thống offline draft-only không
cần authenticated signature. Tuyên bố này chỉ đảm bảo không ai hiểu lầm rằng
ReviewLedger entry hiện tại tương đương chữ ký điện tử hay phê duyệt PI thật.

---

## Phân biệt 6 loại attestation / approval

### 1. Manual Attestation Record

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Người dùng khai báo họ đã xem xét artifact và ghi nhận nhận xét — trên hệ thống offline |
| **minimum_evidence** | Username (string) + timestamp + review note trong ReviewLedger |
| **technical_requirement** | Append-only JSONL; không cần authentication |
| **governance_requirement** | Không có yêu cầu governance bắt buộc trong offline baseline |
| **what_it_does_not_prove** | Không chứng minh danh tính thật; không chứng minh đọc kỹ; không có giá trị pháp lý; không phải institutional approval; không phải independent review |

**Trạng thái hiện tại:** ReviewLedger trong Research OS là loại này.

---

### 2. Authenticated Attestation

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Người dùng xác nhận đã review artifact, được xác thực bởi institutional identity provider |
| **minimum_evidence** | Authenticated actor ID từ identity provider + MFA completion + role at event time + timestamp trong tamper-evident audit log |
| **technical_requirement** | SSO authentication + MFA + session token verification + write-once audit event |
| **governance_requirement** | R1.3 Authenticated audit attribution phải implemented và tested |
| **what_it_does_not_prove** | Không chứng minh reviewer có đủ thẩm quyền chuyên môn; không phải ethics approval; không phải PI approval; không phải independent review nếu reviewer là co-author |

**Trạng thái hiện tại:** NOT IMPLEMENTED — required for production.

---

### 3. Electronic Signature

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Chữ ký điện tử gắn với danh tính pháp lý đã xác thực, có ràng buộc pháp lý |
| **minimum_evidence** | Authenticated identity + intent to sign + non-repudiation mechanism (timestamp authority, certificate) |
| **technical_requirement** | Identity verification đạt assurance level phù hợp; digital certificate hoặc equivalent; timestamp từ trusted authority; audit trail không thể chối bỏ |
| **governance_requirement** | E-signature policy phải được PI và institution ký; áp dụng per eIDAS (EU), CFR Part 11 (FDA), hoặc applicable regulation |
| **what_it_does_not_prove** | Không tự chứng minh nội dung được ký là đúng; không phải ethics approval; không phải independent review |

**Trạng thái hiện tại:** NOT IMPLEMENTED — policy phải được định nghĩa (ID-03).

---

### 4. Institutional Approval

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Phê duyệt chính thức từ tổ chức (bệnh viện, trường đại học) cho phép hoạt động nghiên cứu |
| **minimum_evidence** | Văn bản ký bởi đại diện có thẩm quyền của tổ chức; số tham chiếu; ngày hiệu lực |
| **technical_requirement** | Không cần hệ thống IT đặc biệt — nhưng phải được scan và lưu trong controlled document system |
| **governance_requirement** | Phải được cấp trước khi nghiên cứu bắt đầu; phải được review khi scope thay đổi |
| **what_it_does_not_prove** | Không phải ethics approval; không phải regulatory approval; không phải PI competency verification |

**Trạng thái hiện tại:** NOT IMPLEMENTED — required for any real study (GOV-01).

---

### 5. Ethics Approval

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Phê duyệt từ Institutional Review Board (IRB) / Independent Ethics Committee (IEC) cho phép nghiên cứu liên quan người |
| **minimum_evidence** | Văn bản phê duyệt từ ethics committee; approval number; protocol version được phê duyệt; ngày hiệu lực và ngày hết hạn |
| **technical_requirement** | Protocol phải được nộp đúng quy trình; ICF phải được phê duyệt (nếu applicable) |
| **governance_requirement** | Phải được cấp TRƯỚC KHI thu thập dữ liệu hoặc tuyển dụng người tham gia; amendment phải được phê duyệt trước khi implement |
| **what_it_does_not_prove** | Không phải institutional approval; không chứng minh hệ thống đủ điều kiện kỹ thuật; không phải regulatory approval |

**Trạng thái hiện tại:** NOT IMPLEMENTED — required for Level-A and above (R0 → R3).

---

### 6. Independent Review

| Thuộc tính | Nội dung |
|-----------|---------|
| **meaning** | Review bởi người có thẩm quyền KHÔNG có conflict of interest với artifact được review — có thể xác minh |
| **minimum_evidence** | Reviewer được xác thực danh tính; COI declaration signed; reviewer không phải co-author của artifact; review record với authenticated attribution |
| **technical_requirement** | SoD enforcement kỹ thuật: hệ thống ngăn chặn author review own artifact; reviewer authentication; COI declaration được ghi lại |
| **governance_requirement** | Reviewer independence phải được document và verifiable; COI declaration phải được PI và institution giữ |
| **what_it_does_not_prove** | Không chứng minh reviewer có đủ chuyên môn; không phải ethics approval; không phải institutional approval |

**Trạng thái hiện tại:** NOT IMPLEMENTED — role labels trong ReviewLedger không đủ chứng minh independence.

---

## Delegation Policy

### Nguyên tắc

1. **Delegation phải tồn tại TRƯỚC KHI action được thực hiện** — không retroactive
2. **Delegation phải cụ thể** — theo study, theo nhiệm vụ, theo thời gian
3. **Delegation phải có expiry** — không vô thời hạn
4. **Delegation phải được PI ký** — không implicit delegation
5. **Sub-delegation bị cấm** — trừ khi PI cho phép rõ ràng trong delegation gốc

### Delegation record bắt buộc

```yaml
delegation_id:          UUID
study_id:               mã nghiên cứu
delegator:
  authenticated_id:     ID từ identity provider
  role:                 PI
  signature:            authenticated e-signature
delegatee:
  authenticated_id:     ID từ identity provider
  role:                 CO_INVESTIGATOR / DATA_MANAGER / ...
permitted_activities:
  - "data_entry_crf_v1.2"
  - "query_resolution"
  # danh sách cụ thể — không dùng "all research tasks"
start_date:             YYYY-MM-DD
end_date:               YYYY-MM-DD (bắt buộc)
basis:                  "PI travel 2026-07-01..2026-07-14"
revocation:
  revoked:              false
  revocation_date:      null
  revocation_reason:    null
```

### Revocation

- PI có thể revoke bất kỳ lúc nào — có hiệu lực ngay lập tức
- Revocation được ghi vào delegation record và audit log
- Delegatee nhận thông báo ngay

---

## COI (Conflict of Interest) Declaration

Mọi reviewer phải ký COI declaration trước khi được assign role reviewer:

```
Tôi xác nhận:
- Không có lợi ích tài chính với kết quả nghiên cứu này
- Không phải co-author của artifact được review
- Không có quan hệ cá nhân ảnh hưởng đến tính độc lập
- Sẽ thông báo ngay nếu COI phát sinh trong quá trình review

Ký bởi: [authenticated electronic signature]
Ngày: [date]
```

COI declaration:
- Lưu trong controlled document system
- Gắn với reviewer authentication record
- Xem xét lại khi scope review thay đổi

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
