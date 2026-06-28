# R1.0 Identity Qualification Test Plan

**Document:** R1_0_IDENTITY_QUALIFICATION_TEST_PLAN.md  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc

- Mỗi test phải được thực hiện bởi người **không phải** người implement
- Kết quả PASS chỉ được tuyên bố sau khi test được thực thi và evidence được ký
- Mọi test FAIL phải tạo CAPA; CAPA phải closed trước Go/No-Go
- Tests IQ-19 và IQ-20 phải do **independent tester** thực hiện — không phải team development

---

## IQ-01 — Shared Account Prevention

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | SSO configured; user accounts provisioned |
| **test_steps** | 1. Attempt to create shared account (generic name, shared password). 2. Attempt to log in with two users simultaneously using same credentials. 3. Verify system prevents or alerts on concurrent session from different IPs with same account. |
| **expected_result** | Shared account creation blocked or flagged; concurrent same-account login triggers alert |
| **evidence_required** | Test report with screenshots/logs; system response documented |
| **pass_fail_criteria** | PASS: System enforces one-account-per-person; FAIL: Shared account usable without alert |
| **blocking_effect** | BLOCKED — Level-A pilot cannot proceed |

---

## IQ-02 — Role Assignment Approval

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | RBAC service deployed; PI account active |
| **test_steps** | 1. Attempt to assign role without PI approval. 2. Complete PI approval workflow. 3. Verify role active only after PI approval. 4. Verify role assignment creates audit event with approver identity. |
| **expected_result** | Self-assignment or unauthorized assignment rejected; audit event created on approval |
| **evidence_required** | Audit log excerpt showing approval event; rejection log for unauthorized attempt |
| **pass_fail_criteria** | PASS: Role active only after PI approval + audit event present; FAIL: Role assignable without approval |
| **blocking_effect** | BLOCKED |

---

## IQ-03 — Least Privilege Enforcement

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | RBAC roles deployed; test users with each role assigned |
| **test_steps** | For each role: 1. List permitted actions per SoD matrix. 2. Attempt each FORBIDDEN action in SoD matrix. 3. Verify forbidden actions are blocked technically. 4. Verify no data access beyond role scope. |
| **expected_result** | Every forbidden action returns permission denied; no data leakage beyond role scope |
| **evidence_required** | Test matrix with role × action × result; error logs |
| **pass_fail_criteria** | PASS: 100% forbidden actions blocked; FAIL: Any forbidden action succeeds |
| **blocking_effect** | BLOCKED |

---

## IQ-04 — PI Self-Review Disclosure

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | PI account; review workflow deployed |
| **test_steps** | 1. PI creates protocol artifact. 2. PI attempts to assign themselves as independent reviewer for same artifact. 3. Verify system prevents or prominently flags SoD conflict. |
| **expected_result** | System blocks PI from being independent reviewer of own artifact OR prominently warns with mandatory disclosure |
| **evidence_required** | UI/API response showing block or disclosure; test log |
| **pass_fail_criteria** | PASS: PI cannot silently self-review; FAIL: PI can complete independent review of own artifact without disclosure |
| **blocking_effect** | BLOCKED |

---

## IQ-05 — Reviewer Independence Disclosure

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Review workflow; COI declaration process |
| **test_steps** | 1. Assign reviewer who has not signed COI declaration. 2. Verify review cannot be completed without COI. 3. Sign COI with false information. 4. Verify COI is stored and auditable. |
| **expected_result** | Review blocked until COI signed; COI stored with reviewer identity attribution |
| **evidence_required** | Workflow screenshots; COI record with attributed signature |
| **pass_fail_criteria** | PASS: Review requires COI; FAIL: Review completable without COI |
| **blocking_effect** | HOLD |

---

## IQ-06 — Role Escalation Prevention

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | RBAC deployed; test user with low-privilege role |
| **test_steps** | 1. Attempt direct API call to assign self higher role. 2. Attempt parameter manipulation in role assignment workflow. 3. Attempt to access higher-privilege endpoints directly. |
| **expected_result** | All escalation attempts rejected with 403/permission denied; alert generated |
| **evidence_required** | API response logs; alert evidence |
| **pass_fail_criteria** | PASS: No escalation path succeeds; FAIL: Any escalation path succeeds |
| **blocking_effect** | BLOCKED |

---

## IQ-07 — Role Revocation

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | User with active role; revocation workflow |
| **test_steps** | 1. Record active sessions for user. 2. PI initiates role revocation. 3. Verify role revoked immediately. 4. Verify existing sessions terminated. 5. Verify user cannot access previously permitted resources. |
| **expected_result** | Role revoked within defined SLA; sessions terminated; access denied immediately |
| **evidence_required** | Revocation timestamp vs access-denied timestamp; session termination log |
| **pass_fail_criteria** | PASS: Access denied within SLA after revocation; FAIL: Access persists after revocation |
| **blocking_effect** | BLOCKED |

---

## IQ-08 — Delegation Expiry

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Delegation register; delegatee with active delegation |
| **test_steps** | 1. Create delegation with end_date = today. 2. At end_date + 1 minute, attempt delegated action. 3. Verify action blocked. 4. Verify audit event records expiry block. |
| **expected_result** | Delegated action blocked after end_date; audit event records block |
| **evidence_required** | Action denial log with timestamp; delegation record showing expired status |
| **pass_fail_criteria** | PASS: Action blocked after expiry; FAIL: Action succeeds after expiry |
| **blocking_effect** | HOLD |

---

## IQ-09 — Delegated Action Audit Attribution

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Active delegation; delegatee performs action |
| **test_steps** | 1. Co-I performs data entry under delegation. 2. Retrieve audit event for that action. 3. Verify event contains: authenticated_actor_id of Co-I; actor_role = CO_INVESTIGATOR; delegation_reference = delegation_id. |
| **expected_result** | Audit event unambiguously shows delegatee identity + delegation reference |
| **evidence_required** | Audit event JSON with all required fields |
| **pass_fail_criteria** | PASS: All attribution fields present and correct; FAIL: delegation_reference missing or actor_id wrong |
| **blocking_effect** | BLOCKED |

---

## IQ-10 — MFA for Privileged Action

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | MFA deployed; user with PI role |
| **test_steps** | 1. Login with password only (without MFA). 2. Attempt privileged action (database lock). 3. Verify MFA challenge issued before action. 4. Complete MFA. 5. Verify action proceeds. 6. Attempt to bypass MFA via API. |
| **expected_result** | Privileged action requires MFA completion; API bypass rejected |
| **evidence_required** | Auth log showing MFA challenge and completion; rejection log for bypass attempt |
| **pass_fail_criteria** | PASS: MFA required for ALL privileged actions with no bypass; FAIL: Any privileged action proceeds without MFA |
| **blocking_effect** | BLOCKED |

---

## IQ-11 — Failed Login Lockout

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Login configured with lockout policy |
| **test_steps** | 1. Attempt login with wrong password N times. 2. Verify lockout triggered at threshold. 3. Verify alert sent to SECURITY_ADMINISTRATOR. 4. Verify manual unlock required. 5. Verify unlock creates audit event. |
| **expected_result** | Account locked at threshold; alert generated; manual unlock required |
| **evidence_required** | Auth log; alert evidence; unlock audit event |
| **pass_fail_criteria** | PASS: Lockout at threshold + alert + manual unlock; FAIL: No lockout or auto-unlock |
| **blocking_effect** | HOLD |

---

## IQ-12 — Session Expiration

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Session management deployed with configured timeouts |
| **test_steps** | 1. Login and obtain session token. 2. Wait for idle timeout period without action. 3. Attempt action with expired session token. 4. Verify rejection. 5. Test absolute session timeout independently. |
| **expected_result** | Session token rejected after idle timeout; absolute timeout enforced |
| **evidence_required** | Session expiry log; action rejection with expired token |
| **pass_fail_criteria** | PASS: Both idle and absolute timeouts enforced; FAIL: Either timeout not enforced |
| **blocking_effect** | HOLD |

---

## IQ-13 — Audit Immutability

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Audit log with integrity protection deployed |
| **test_steps** | 1. Record existing audit events and compute expected hash. 2. Attempt to delete an audit event (as SYSTEM_ADMINISTRATOR). 3. Attempt to modify an audit event. 4. Run integrity verification after attempts. 5. Verify integrity check detects any modification. |
| **expected_result** | Delete and modify rejected at technical level; integrity verification passes without tampering |
| **evidence_required** | Rejection logs; integrity verification report |
| **pass_fail_criteria** | PASS: No delete/modify possible; integrity check passes; FAIL: Any modification succeeds undetected |
| **blocking_effect** | BLOCKED |

---

## IQ-14 — Administrator Access Review

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Admin accounts active; privileged access review procedure |
| **test_steps** | 1. List all accounts with SYSTEM_ADMINISTRATOR or SECURITY_ADMINISTRATOR role. 2. Verify each has current justification. 3. Attempt admin access to research content. 4. Verify access denied. 5. Verify admin actions in separate audit trail. |
| **expected_result** | Admin roles justified; admin cannot access research content; admin audit trail separate |
| **evidence_required** | Access review report; denied-access log; admin audit trail sample |
| **pass_fail_criteria** | PASS: Admin access to research content denied; admin audit trail separate; FAIL: Admin can read/modify research content |
| **blocking_effect** | HOLD |

---

## IQ-15 — Break-Glass Access Logging

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Break-glass procedure defined; break-glass account exists |
| **test_steps** | 1. Activate break-glass procedure with second approval. 2. Verify alert sent to PI and SECURITY_ADMINISTRATOR. 3. Perform action under break-glass. 4. Deactivate break-glass. 5. Verify full session logged including all actions. |
| **expected_result** | Break-glass activation triggers alert; all actions logged; deactivation logged |
| **evidence_required** | Alert evidence; break-glass session audit log; deactivation event |
| **pass_fail_criteria** | PASS: Alert sent + full logging; FAIL: Break-glass usable without alert or without logging |
| **blocking_effect** | HOLD |

---

## IQ-16 — Staff Offboarding Revocation

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Active user account; offboarding procedure |
| **test_steps** | 1. Initiate offboarding for test user account. 2. Record start timestamp. 3. Verify account deactivated within SLA (24h). 4. Verify all active sessions terminated. 5. Verify all role assignments revoked. 6. Verify outstanding delegations revoked. |
| **expected_result** | All access revoked within 24h SLA |
| **evidence_required** | Revocation timestamps; session termination log; role revocation log |
| **pass_fail_criteria** | PASS: All access revoked within 24h; FAIL: Any access persists after SLA |
| **blocking_effect** | BLOCKED |

---

## IQ-17 — Read-Only Auditor Isolation

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | READ_ONLY_AUDITOR account; research artifacts and audit logs present |
| **test_steps** | 1. Login as READ_ONLY_AUDITOR. 2. Attempt to modify any research artifact. 3. Attempt to delete any audit event. 4. Attempt to approve any decision. 5. Verify read access to audit logs. |
| **expected_result** | All modifications and approvals rejected; read access to audit logs granted |
| **evidence_required** | Rejection logs for all modify attempts; successful audit log read |
| **pass_fail_criteria** | PASS: No modify possible; read access works; FAIL: Any modify succeeds |
| **blocking_effect** | BLOCKED |

---

## IQ-18 — Identity Provider Outage Handling

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | SSO deployed; break-glass procedure defined |
| **test_steps** | 1. Simulate identity provider unavailability. 2. Verify normal login fails gracefully (not silently bypassed). 3. Activate break-glass procedure. 4. Verify break-glass still enforces MFA. 5. Verify alert sent. 6. Restore identity provider. 7. Verify normal login resumes. |
| **expected_result** | IdP outage does not bypass authentication; break-glass with MFA available; alert sent |
| **evidence_required** | Outage simulation log; break-glass audit; alert evidence; restoration log |
| **pass_fail_criteria** | PASS: No auth bypass on IdP outage; FAIL: Authentication silently bypassed |
| **blocking_effect** | HOLD |

---

## IQ-19 — Backup Audit Log Integrity

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | Backup procedure running; audit log backup available |
| **test_steps** | 1. Trigger backup of audit log. 2. Compute hash of backup. 3. Verify hash matches expected. 4. Restore from backup to test environment. 5. Run integrity verification on restored audit log. |
| **expected_result** | Backup integrity verified; restored audit log passes integrity check |
| **evidence_required** | Backup hash comparison; integrity verification report on restored data |
| **pass_fail_criteria** | PASS: Backup verified and restore passes integrity check; FAIL: Hash mismatch or integrity failure |
| **blocking_effect** | HOLD |

---

## IQ-20 — Independent Security Test Evidence

| Thuộc tính | Nội dung |
|-----------|---------|
| **precondition** | System deployed; independent security tester engaged (not development team) |
| **test_steps** | Independent security tester performs: 1. Authentication bypass attempt (IDT-02, IDT-08). 2. Privilege escalation attempt (IDT-03). 3. Audit log tampering attempt (IDT-05). 4. Unauthorized data export (IDT-09). 5. Write-back to eHospital simulation. |
| **expected_result** | All attacks fail; findings documented; CAPA for any finding |
| **evidence_required** | Signed penetration test report by independent tester; CAPA log with findings closed |
| **pass_fail_criteria** | PASS: 0 critical findings open; all high findings CAPA closed; report signed by independent tester; FAIL: Critical finding open or test not performed by independent tester |
| **blocking_effect** | BLOCKED — cannot proceed to Level-A without this |

---

## Tóm tắt blocking effect

| Blocking level | Tests |
|---------------|-------|
| BLOCKED (Level-A) | IQ-01, IQ-02, IQ-03, IQ-04, IQ-06, IQ-07, IQ-09, IQ-10, IQ-13, IQ-16, IQ-17, IQ-20 |
| HOLD (Level-A) | IQ-05, IQ-08, IQ-11, IQ-12, IQ-14, IQ-15, IQ-18, IQ-19 |

---

*Required for future production qualification.*  
*Not implemented in current Research OS baseline.*

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
