# R1.0 Identity Threat Model

**Document:** R1_0_IDENTITY_THREAT_MODEL.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Phạm vi

Mô hình mối đe dọa này áp dụng cho **hệ thống production tương lai** khi được
triển khai cho nghiên cứu y khoa thật. Nó KHÔNG mô tả hệ thống offline hiện tại
(Research OS hiện tại không có real user identity nên không có attack surface này).

---

## IDT-01 — Shared Account

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-01 |
| **threat_description** | Nhiều người dùng đăng nhập bằng một tài khoản dùng chung; không thể phân biệt người thực hiện hành động |
| **affected_research_stage** | Tất cả giai đoạn từ data entry đến review và approval |
| **impact** | Audit trail không có giá trị; không thể quy trách nhiệm; vi phạm GCP Principle of Accountability |
| **likelihood** | Cao nếu không có kiểm soát kỹ thuật |
| **risk_level** | CRITICAL |
| **required_control** | Mỗi người dùng phải có tài khoản riêng; tài khoản dùng chung bị cấm kỹ thuật; shared-account attempt triggers alert |
| **verification_evidence** | Penetration test IQ-01; audit log review showing unique actor per session |
| **go_no_go_effect** | BLOCKED nếu shared account possible |

---

## IDT-02 — Impersonation

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-02 |
| **threat_description** | Người dùng A sử dụng credential của B để thực hiện hành động dưới danh nghĩa B; hoặc tạo tài khoản giả danh |
| **affected_research_stage** | Reviewer attestation, PI approval, delegation authorization |
| **impact** | Quyết định nghiên cứu bị gán cho người không thực sự ra quyết định; integrity của audit trail bị phá vỡ |
| **likelihood** | Trung bình nếu không có MFA |
| **risk_level** | CRITICAL |
| **required_control** | MFA bắt buộc; institutional identity verification; session binding; anomaly detection |
| **verification_evidence** | IQ-10 MFA for privileged action; IQ-03 least privilege; penetration test TP-SEC-01 |
| **go_no_go_effect** | BLOCKED nếu MFA không bắt buộc |

---

## IDT-03 — Reviewer Role Escalation

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-03 |
| **threat_description** | Người dùng với role thấp tự nâng quyền lên role reviewer hoặc PI; hoặc admin gán role không được phê duyệt |
| **affected_research_stage** | Role assignment, review decisions |
| **impact** | Người không đủ thẩm quyền ra quyết định về protocol/evidence/claim |
| **likelihood** | Trung bình |
| **risk_level** | HIGH |
| **required_control** | Role assignment phải được PI phê duyệt; RBAC không cho phép self-escalation; role change tạo audit event |
| **verification_evidence** | IQ-02 role assignment approval; IQ-06 role escalation prevention |
| **go_no_go_effect** | HOLD nếu role escalation possible |

---

## IDT-04 — PI Self-Approval Presented as Independent Review

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-04 |
| **threat_description** | PI phê duyệt protocol/evidence của chính mình và trình bày như đánh giá độc lập; hoặc hệ thống không tách biệt author với reviewer |
| **affected_research_stage** | Protocol review, evidence review, final approval |
| **impact** | Nghiên cứu thiếu independent oversight thật sự; vi phạm yêu cầu peer review và good research practice |
| **likelihood** | Cao nếu không có SoD enforcement kỹ thuật |
| **risk_level** | CRITICAL |
| **required_control** | Hệ thống phải enforce author ≠ approver; PI không thể tự approve protocol của mình; SOD được kiểm chứng kỹ thuật không chỉ là policy |
| **verification_evidence** | IQ-04 PI self-review disclosure; IQ-05 reviewer independence disclosure; SoD matrix |
| **go_no_go_effect** | BLOCKED nếu PI có thể self-approve |

---

## IDT-05 — Audit Event Attribution Failure

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-05 |
| **threat_description** | Audit event không có authenticated actor ID; chỉ có username string không có identity verification; actor có thể bị giả mạo |
| **affected_research_stage** | Tất cả stages — mọi write operation |
| **impact** | Audit trail không đáp ứng GCP Principle of Traceability; không thể điều tra sự kiện bất thường; không thể chứng minh accountability |
| **likelihood** | Chắc chắn trong trạng thái hiện tại (offline baseline không có authenticated actor) |
| **risk_level** | CRITICAL |
| **required_control** | Mọi audit event phải có authenticated_actor_id từ identity provider; session token verified; role at event time recorded |
| **verification_evidence** | IQ-09 delegated action audit attribution; IQ-13 audit immutability; TP-SEC-02 |
| **go_no_go_effect** | BLOCKED nếu audit attribution không có authenticated actor |

---

## IDT-06 — Access Not Revoked After Staff Departure

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-06 |
| **threat_description** | Nhân viên rời đề tài/tổ chức vẫn giữ quyền truy cập; có thể tiếp tục đọc/sửa dữ liệu sau khi không còn được phép |
| **affected_research_stage** | Data access, review decisions, audit trail |
| **impact** | Unauthorized access to research data; breach of data governance; potential GCP violation |
| **likelihood** | Cao nếu không có joiner/mover/leaver process |
| **risk_level** | HIGH |
| **required_control** | Offboarding procedure với SLA rõ; access revocation trong 24h; identity provider deactivation tự động |
| **verification_evidence** | IQ-07 role revocation; IQ-16 staff offboarding revocation |
| **go_no_go_effect** | HOLD nếu revocation SLA chưa được test |

---

## IDT-07 — Weak Password or Session Compromise

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-07 |
| **threat_description** | Tài khoản bị xâm phạm qua password yếu, credential stuffing, session hijacking, hoặc token theft |
| **affected_research_stage** | Tất cả stages yêu cầu authentication |
| **impact** | Unauthorized access; impersonation; data exfiltration |
| **likelihood** | Trung bình — phụ thuộc vào password policy và session management |
| **risk_level** | HIGH |
| **required_control** | MFA; strong password policy; session timeout; secure session management; TLS enforced |
| **verification_evidence** | IQ-11 failed login lockout; IQ-12 session expiration; TP-SEC-01 |
| **go_no_go_effect** | HOLD nếu session management không được test |

---

## IDT-08 — MFA Bypass

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-08 |
| **threat_description** | MFA bị bypass qua fallback paths (email OTP, recovery codes không kiểm soát, admin override, API path không enforce MFA) |
| **affected_research_stage** | Authentication — mọi production login |
| **impact** | MFA không còn là kiểm soát thật sự; tất cả threats phụ thuộc MFA đều mở lại |
| **likelihood** | Trung bình — phổ biến nếu không test kỹ toàn bộ auth paths |
| **risk_level** | CRITICAL |
| **required_control** | MFA bắt buộc không có exception path; mọi API endpoint kiểm tra MFA completion; recovery code policy có audit |
| **verification_evidence** | IQ-10 MFA for privileged action; penetration test TP-SEC-01 — MFA bypass attempt |
| **go_no_go_effect** | BLOCKED nếu MFA bypassable trên bất kỳ path nào |

---

## IDT-09 — Unauthorized Data Export

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-09 |
| **threat_description** | Người dùng export dữ liệu nghiên cứu (bao gồm cả pseudonymized) vượt scope được phép; exfiltration to external location |
| **affected_research_stage** | Data access, controlled export |
| **impact** | Breach of data governance agreement; potential re-identification risk; regulatory violation |
| **likelihood** | Trung bình |
| **risk_level** | HIGH |
| **required_control** | RBAC hạn chế export; mọi export cần PI authorization; export tạo audit event với file hash; DLP controls |
| **verification_evidence** | IQ-03 least privilege; TP-SEC-03 data exfiltration |
| **go_no_go_effect** | HOLD nếu export không có PI authorization |

---

## IDT-10 — Privileged Administrator Override

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-10 |
| **threat_description** | SYSTEM_ADMINISTRATOR dùng quyền admin để modify research artifacts, bypass review workflows, hoặc alter audit logs |
| **affected_research_stage** | Tất cả stages — research data, audit trail, role assignment |
| **impact** | Separation of duties bị phá vỡ; audit trail có thể bị giả mạo; research integrity bị đe dọa |
| **likelihood** | Thấp với technical controls; cao nếu không có privileged access management |
| **risk_level** | HIGH |
| **required_control** | Admin role không có research content access; privileged action cần second approval; admin audit trail riêng biệt không thể tự xóa; PAM solution |
| **verification_evidence** | IQ-14 administrator access review; IQ-15 break-glass access logging |
| **go_no_go_effect** | HOLD nếu admin có thể modify research artifacts |

---

## IDT-11 — Delegation Without Documented Authorization

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-11 |
| **threat_description** | Co-I thực hiện nhiệm vụ không được PI ủy quyền; ủy quyền không có ngày hết hạn hoặc phạm vi rõ ràng; delegation không được ghi lại |
| **affected_research_stage** | Protocol execution, data review, evidence attestation |
| **impact** | GCP violation; không thể truy xuất người chịu trách nhiệm; delegation log không đầy đủ |
| **likelihood** | Cao nếu không có delegation register |
| **risk_level** | HIGH |
| **required_control** | Delegation register bắt buộc trước khi Co-I thực hiện nhiệm vụ; delegation có start/end date; revocation procedure |
| **verification_evidence** | IQ-08 delegation expiry; IQ-09 delegated action audit attribution |
| **go_no_go_effect** | HOLD nếu delegation register không functional |

---

## IDT-12 — Identity Provider Outage

| Thuộc tính | Nội dung |
|-----------|---------|
| **risk_id** | IDT-12 |
| **threat_description** | Institutional identity provider unavailable; mọi người dùng bị lock out; hoặc fallback authentication bypass MFA |
| **affected_research_stage** | Tất cả stages yêu cầu authentication |
| **impact** | Nghiên cứu bị gián đoạn; hoặc nếu fallback không an toàn → security compromise |
| **likelihood** | Thấp nhưng hệ quả cao |
| **risk_level** | MEDIUM |
| **required_control** | Break-glass procedure với audit; fallback authentication vẫn enforce MFA; RTO plan cho identity provider |
| **verification_evidence** | IQ-18 identity-provider outage handling; IQ-15 break-glass access logging |
| **go_no_go_effect** | HOLD nếu break-glass chưa được test |

---

## Tóm tắt risk levels

| Risk level | Số threats |
|-----------|-----------|
| CRITICAL | IDT-01, IDT-02, IDT-04, IDT-05, IDT-08 — 5 threats |
| HIGH | IDT-03, IDT-06, IDT-07, IDT-09, IDT-10, IDT-11 — 6 threats |
| MEDIUM | IDT-12 — 1 threat |

**Tất cả 5 CRITICAL threats phải được resolved trước Level-A pilot.**

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
