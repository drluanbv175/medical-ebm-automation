# R1.1.1 Negative Test and Abuse-Case Review

**Document:** R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md  
**Date:** 2026-06-28  
**Phase:** R1.1.1 — Validation Evidence Pack  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Nguyên tắc

Mỗi abuse case được đánh giá theo:
- **threat** — mối đe dọa hoặc vi phạm chính sách nếu không có guard
- **expected_system_response** — phản ứng đúng của hệ thống
- **test_evidence** — test ID và tên test chứng minh guard hoạt động
- **observed_result** — kết quả thực tế trong fresh archive
- **residual_risk** — rủi ro còn lại sau khi guard được xác minh
- **validation_lead_review_required** — quyết định Validation Lead cần đưa ra

---

## AC-01 — PI attempts independent review of own artifact

| Trường | Nội dung |
|--------|----------|
| **threat** | Kết quả nghiên cứu được "xác nhận" bởi chính tác giả mà không có independent reviewer; vi phạm SoD-01 |
| **expected_system_response** | BLOCK với reason_code=PI_SELF_INDEPENDENT_REVIEW; policy_reference=SOD-01-PI-SELF-INDEPENDENT-REVIEW |
| **test_evidence** | T07: `test_pi_cannot_independent_review_own_artifact` (TestT07_SoD01_PIIndependentReview) |
| **observed_result** | PASS — decision=BLOCK, reason_code=PI_SELF_INDEPENDENT_REVIEW đúng |
| **residual_risk** | LOW — guard hoạt động trong offline harness; không có SSO nên không thể kiểm chứng enforcement trong production context; guard này phải được tái kiểm trong R1.3 khi có authenticated identity |
| **validation_lead_review_required** | Có — confirm guard logic đủ cho test design; note limitation: production enforcement cần R1.3 |

---

## AC-02 — SYSTEM_ADMINISTRATOR attempts research-content approval

| Trường | Nội dung |
|--------|----------|
| **threat** | System admin phê duyệt protocol/evidence/SAP thay vì người có chuyên môn khoa học; vi phạm SoD-02 |
| **expected_system_response** | BLOCK với reason_code=ADMIN_RESEARCH_APPROVAL; policy_reference=SOD-02-SYSADMIN-RESEARCH-APPROVAL |
| **test_evidence** | T08: `test_sysadmin_cannot_record_review_attestation` (TestT08_SoD02_AdminResearchApproval) |
| **observed_result** | PASS — decision=BLOCK, reason_code=ADMIN_RESEARCH_APPROVAL đúng |
| **residual_risk** | LOW — offline guard verified; residual: production RBAC service (R1.3) cần tái-enforce rule này |
| **validation_lead_review_required** | Có — confirm scope của _RESEARCH_CONTENT_APPROVAL_ACTIONS đủ không có action nào bị thiếu |

---

## AC-03 — READ_ONLY_AUDITOR attempts write action

| Trường | Nội dung |
|--------|----------|
| **threat** | Auditor sửa research record làm mất tính toàn vẹn audit trail; vi phạm SoD-03 |
| **expected_system_response** | BLOCK với reason_code=READ_ONLY_WRITE_ATTEMPT; policy_reference=SOD-03-READ-ONLY-AUDITOR |
| **test_evidence** | T09: `test_auditor_cannot_edit_artifact` (TestT09_SoD03_ReadOnlyAuditor) |
| **observed_result** | PASS — decision=BLOCK, reason_code=READ_ONLY_WRITE_ATTEMPT đúng |
| **residual_risk** | LOW — guard tested for EDIT_DRAFT_ARTIFACT; _WRITE_ACTIONS set includes 12 actions; Validation Lead to confirm set completeness |
| **validation_lead_review_required** | Có — confirm _WRITE_ACTIONS set không bỏ sót action nào cần block |

---

## AC-04 — Disabled actor attempts protected action

| Trường | Nội dung |
|--------|----------|
| **threat** | Actor bị thu hồi quyền vẫn tiếp tục thực hiện action; vi phạm offboarding/revocation requirement (IQ-16) |
| **expected_system_response** | BLOCK với reason_code=DISABLED_ACTOR trước khi kiểm tra RBAC policy |
| **test_evidence** | T13: `test_disabled_actor_blocked_for_any_action` (TestT13_DisabledActor) |
| **observed_result** | PASS — disabled actor blocked ngay tại guard đầu tiên |
| **residual_risk** | LOW — offline; residual: production requires session termination (IQ-07, IQ-16) không chỉ RBAC block |
| **validation_lead_review_required** | Không — guard clear; note production limitation documented |

---

## AC-05 — Expired role attempts protected action

| Trường | Nội dung |
|--------|----------|
| **threat** | Role assignment đã hết hạn tiếp tục cho phép action; vi phạm IQ-08 (delegation expiry) |
| **expected_system_response** | BLOCK với reason_code=EXPIRED_ROLE hoặc ROLE_NOT_PERMITTED khi không còn active role nào |
| **test_evidence** | T14: `test_expired_role_is_blocked` (TestT14_ExpiredRole) |
| **observed_result** | PASS — decision=BLOCK với reason_code trong (EXPIRED_ROLE, ROLE_NOT_PERMITTED) |
| **residual_risk** | MEDIUM — test allows either reason_code; Validation Lead to confirm both codes are acceptable outcomes, or if EXPIRED_ROLE specifically is required |
| **validation_lead_review_required** | Có — confirm whether ROLE_NOT_PERMITTED alone is acceptable or EXPIRED_ROLE specifically required |

---

## AC-06 — Self-delegation attempt

| Trường | Nội dung |
|--------|----------|
| **threat** | Actor ủy quyền cho chính mình để bypass approval workflow |
| **expected_system_response** | DelegationError raised với message "Self-delegation" tại thời điểm propose() |
| **test_evidence** | T19: `test_t19_self_delegation_rejected` (TestT19T20_DelegationValidation) |
| **observed_result** | PASS — DelegationError raised với match "Self-delegation" |
| **residual_risk** | LOW — guard at construction; clear |
| **validation_lead_review_required** | Không |

---

## AC-07 — Delegation beyond authority (forbidden action)

| Trường | Nội dung |
|--------|----------|
| **threat** | Delegation gán forbidden actions (FINAL_APPROVAL, ETHICS_APPROVAL…) cho delegatee, tạo backdoor approval |
| **expected_system_response** | DelegationError raised với message "forbidden" khi permitted_actions chứa forbidden action |
| **test_evidence** | T20: `test_t20_delegation_with_forbidden_action_rejected` (TestT19T20_DelegationValidation) |
| **observed_result** | PASS — DelegationError raised với match "forbidden" |
| **residual_risk** | LOW — guard explicit; chỉ FINAL_APPROVAL được test trực tiếp; residual: other forbidden actions (ETHICS_APPROVAL, EXTERNAL_SUBMISSION, CLINICAL_RELEASE) share same guard path |
| **validation_lead_review_required** | Có — confirm that testing FINAL_APPROVAL in the set is sufficient evidence for the shared guard, or request separate tests per forbidden action |

---

## AC-08 — Expired delegation use

| Trường | Nội dung |
|--------|----------|
| **threat** | Delegatee tiếp tục dùng delegation đã quá effective_until_utc |
| **expected_system_response** | get_status() returns EXPIRED; list_active() không trả về delegation này |
| **test_evidence** | T22: `test_delegation_expired_after_effective_until` (TestT22_ExpiredDelegation) |
| **observed_result** | PASS — status returned EXPIRED khi effective_until_utc trong quá khứ |
| **residual_risk** | LOW — auto-expiry tested; note: in production this must be enforced at API layer (R1.4), not only RBAC check |
| **validation_lead_review_required** | Không — limitation documented |

---

## AC-09 — Revoked delegation use

| Trường | Nội dung |
|--------|----------|
| **threat** | Delegatee tiếp tục dùng delegation đã bị PI thu hồi |
| **expected_system_response** | get_status() returns REVOKED sau khi revoke() được gọi |
| **test_evidence** | T21: `test_delegation_lifecycle` — includes REVOKED state verification |
| **observed_result** | PASS — REVOKED status returned correctly in T21 lifecycle test |
| **residual_risk** | LOW — revocation tested as part of lifecycle; status persisted in JSONL |
| **validation_lead_review_required** | Không |

---

## AC-10 — Rejected delegation attempted activation

| Trường | Nội dung |
|--------|----------|
| **threat** | REJECTED delegation được activate lại tạo unauthorized delegation |
| **expected_system_response** | DelegationError raised khi activate() được gọi trên REJECTED delegation |
| **test_evidence** | T28: `test_rejected_delegation_cannot_activate` (TestT28_RejectedDelegationCannotActivate) |
| **observed_result** | PASS — DelegationError raised với match "PROPOSED" (state machine enforcement) |
| **residual_risk** | LOW — terminal state enforced |
| **validation_lead_review_required** | Không |

---

## AC-11 — Audit-chain tampering

| Trường | Nội dung |
|--------|----------|
| **threat** | Ai đó sửa nội dung của một audit event (vd. thay đổi "reason") để che giấu vi phạm |
| **expected_system_response** | verify() returns ok=False với danh sách errors chỉ rõ event bị sửa |
| **test_evidence** | T26: `test_hash_chain_fails_after_event_tamper` (TestT26_HashChainTamper) |
| **observed_result** | PASS — verify() returns ok=False, errors ≥ 1 sau khi sửa reason field |
| **residual_risk** | MEDIUM — SHA-256 hash chain verified offline; production requires WORM storage (R1.3) to prevent replace-then-rehash attack; offline JSONL is not WORM |
| **validation_lead_review_required** | Có — confirm residual risk (replace-then-rehash) is documented and understood; confirm WORM requirement deferred to R1.3 |

---

## AC-12 — Missing previous-event hash

| Trường | Nội dung |
|--------|----------|
| **threat** | Attacker insert một event giả vào ledger không có previous_event_hash đúng |
| **expected_system_response** | verify() phát hiện chain break; kết quả FAIL |
| **test_evidence** | T26 (T26 also covers previous_event_hash chain break when first event hash changes) |
| **observed_result** | PASS — khi event #1 bị sửa, event #2 previous_event_hash không còn khớp → chain break detected |
| **residual_risk** | LOW — chain verification covers both hash integrity and chain linkage |
| **validation_lead_review_required** | Không |

---

## AC-13 — Attempt to mark synthetic identity as authenticated

| Trường | Nội dung |
|--------|----------|
| **threat** | Code hay test vô tình set authentication_state='AUTHENTICATED' → overclaim identity |
| **expected_system_response** | SyntheticIdentityError raised tại construction với message "AUTHENTICATED" |
| **test_evidence** | T02a: `test_authenticated_state_rejected` (TestT02_NoAuthentication) |
| **observed_result** | PASS — SyntheticIdentityError raised |
| **residual_risk** | LOW — enforced at object construction; clear |
| **validation_lead_review_required** | Không |

---

## AC-14 — Attempt to create FINAL_APPROVAL

| Trường | Nội dung |
|--------|----------|
| **threat** | Actor cố tình hoặc vô tình gọi FINAL_APPROVAL action → overclaim research completion |
| **expected_system_response** | BLOCK với reason_code=FORBIDDEN_ACTION_ALL_ROLES trước RBAC policy check |
| **test_evidence** | T15: `test_t15_final_approval_blocked_for_pi` (TestT15T16T17_ForbiddenActions) |
| **observed_result** | PASS — blocked với FORBIDDEN_ACTION_ALL_ROLES cho cả PI |
| **residual_risk** | LOW — gate evaluated before RBAC policy; applies to all roles |
| **validation_lead_review_required** | Không |

---

## AC-15 — Attempt to create ETHICS_APPROVAL

| Trường | Nội dung |
|--------|----------|
| **threat** | System tự tuyên bố đã có ethics approval → vi phạm governance requirement |
| **expected_system_response** | BLOCK với reason_code=FORBIDDEN_ACTION_ALL_ROLES |
| **test_evidence** | T16: `test_t16_ethics_approval_blocked_for_pi` |
| **observed_result** | PASS — blocked |
| **residual_risk** | LOW |
| **validation_lead_review_required** | Không |

---

## AC-16 — Attempt to create EXTERNAL_SUBMISSION

| Trường | Nội dung |
|--------|----------|
| **threat** | System tự nộp nghiên cứu ra ngoài mà không có ethics/PI approval thật |
| **expected_system_response** | BLOCK với reason_code=FORBIDDEN_ACTION_ALL_ROLES |
| **test_evidence** | Shared guard path với T15 (EXTERNAL_SUBMISSION ∈ FORBIDDEN_ACTIONS_ALL_ROLES) |
| **observed_result** | PASS (guard path shared) |
| **residual_risk** | LOW — same pre-RBAC gate; note: no dedicated test for EXTERNAL_SUBMISSION specifically |
| **validation_lead_review_required** | Có — confirm shared-path evidence is acceptable, or request dedicated test |

---

## Tổng kết abuse cases

| ID | Abuse Case | Guard | Test | Observed | Residual Risk | VL Review |
|----|-----------|-------|------|----------|---------------|-----------|
| AC-01 | PI self-independent-review | SoD-01 | T07 | PASS | LOW | Có |
| AC-02 | Admin research approval | SoD-02 | T08 | PASS | LOW | Có |
| AC-03 | Read-only auditor write | SoD-03 | T09 | PASS | LOW | Có |
| AC-04 | Disabled actor | SoD-08 | T13 | PASS | LOW | Không |
| AC-05 | Expired role | SoD-07 | T14 | PASS | MEDIUM | Có |
| AC-06 | Self-delegation | DelegationError | T19 | PASS | LOW | Không |
| AC-07 | Delegation with forbidden action | DelegationError | T20 | PASS | LOW | Có |
| AC-08 | Expired delegation use | Auto-expiry | T22 | PASS | LOW | Không |
| AC-09 | Revoked delegation use | REVOKED state | T21 | PASS | LOW | Không |
| AC-10 | Rejected delegation activation | State machine | T28 | PASS | LOW | Không |
| AC-11 | Audit-chain tampering | SHA-256 chain | T26 | PASS | MEDIUM | Có |
| AC-12 | Missing previous-event hash | Chain linkage | T26 | PASS | LOW | Không |
| AC-13 | Mark synthetic as authenticated | SyntheticIdentityError | T02a | PASS | LOW | Không |
| AC-14 | FINAL_APPROVAL | Forbidden gate | T15 | PASS | LOW | Không |
| AC-15 | ETHICS_APPROVAL | Forbidden gate | T16 | PASS | LOW | Không |
| AC-16 | EXTERNAL_SUBMISSION | Shared forbidden gate | T15 | PASS | LOW | Có |

**Cases requiring Validation Lead review:** AC-01 (production gap), AC-02 (action set), AC-03 (write set), AC-05 (reason_code), AC-07 (shared guard), AC-11 (WORM gap), AC-16 (shared guard evidence)

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
