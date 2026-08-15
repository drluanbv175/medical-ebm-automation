# R1.1.4 Human Governance Decision Record

**Document:** R1_1_4_HUMAN_GOVERNANCE_DECISION_RECORD.md  
**Date created:** 2026-06-28  
**Supersedes:** VL-GATE-R1.1-2026-001 (ACCEPT_TECHNICAL_TEST_DESIGN, commit 8a0e008)  
**Phase:** R1.1.4 — Phase A  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This record documents a human governance decision.  
> It does not constitute:
> - production authorization;
> - research authorization;
> - ethics approval;
> - independent validation;
> - electronic signature;
> - permission to process real research data.

---

> **SELF-REVIEW DISCLOSURE:**  
> `review_mode = SELF_REVIEW`  
> This is self-review. Reviewer independence is not established.  
> The reviewer and the PI/developer of the evidence are the same person.

---

## Decision Record — Verbatim as provided

---

**decision_id**

```
VL-GATE-R1.1-2026-002
```

---

**decision_date_utc**

```
2026-06-28T05:30:28Z
```

---

**reviewer_reference**

```
Dr Luân
```

---

**review_mode**

```
SELF_REVIEW
```

---

**reviewer_role**

```
Bác sĩ điều trị, nhà nghiên cứu
```

---

**baseline_commit**

```
e806e0e (feat/r1-1-2-design-gap-remediation)
Suite result: 867 passed / 0 failed / 5 skipped
Manifest: PASS (48 agents, all_hash_verified=True)
```

---

**decision**

```
ACCEPT_WITH_ACTIONS
```

---

**decision_rationale** *(human's words, verbatim)*

```
Tôi đã tự rà soát evidence pack R1.1, R1.1.1, R1.1.2 và kết quả kiểm thử
kỹ thuật tương ứng. Tôi chấp nhận thiết kế kiểm thử offline cho RBAC,
separation of duties, delegation và tamper-evident local audit simulation,
nhưng yêu cầu theo dõi rõ PROD-AUD-01 và duy trì các ràng buộc scope của R1.2
thông qua action register có chủ sở hữu. Quyết định này chỉ chấp nhận thiết kế
kỹ thuật có điều kiện; không phải phê duyệt production, nghiên cứu thật,
ethics, hay independent validation.
```

---

**conditions_or_actions** *(verbatim)*

```
Action 1: PROD-AUD-01 phải được xử lý tại R1.3 trước khi tuyên bố
  production audit readiness. Owner: Dr Luân. Due: R1.3 qualification.

Action 2: Local audit ledger chỉ được mô tả là tamper-evident local
  simulation, không phải WORM, immutable storage hoặc production audit trail.
  Owner: Dr Luân. Due: Ongoing.

Action 3: R1.2 chỉ là design-only; không triển khai SSO, MFA, dữ liệu thật,
  eHospital hoặc production EDC. Owner: Dr Luân. Due: R1.2 completion.
```

---

**residual_risks_accepted** *(verbatim)*

```
RR-02 replace-then-rehash residual risk (MEDIUM);
PROD-AUD-01 production WORM retention (deferred to R1.3);
production RBAC (NOT IMPLEMENTED);
IQ-20 independent security-test evidence (deferred to R1.5).
```

---

**follow_up_owner**

```
Dr Luân
```

---

**follow_up_due_date**

```
2026-09-30
```

---

**signature_or_external_attestation_reference**

```
Dr Luân xác nhận đã đọc evidence pack và đưa ra quyết định này, 2026-06-28.
```

---

## Field validation summary

| Field | Provided | Valid |
|-------|----------|-------|
| decision_id | VL-GATE-R1.1-2026-002 | ✓ |
| decision_date_utc | 2026-06-28T05:30:28Z | ✓ |
| reviewer_reference | Dr Luân | ✓ (human name) |
| review_mode | SELF_REVIEW | ✓ (valid value) |
| reviewer_role | Bác sĩ điều trị, nhà nghiên cứu | ✓ |
| baseline_commit | e806e0e | ✓ |
| decision | ACCEPT_WITH_ACTIONS | ✓ (valid value) |
| decision_rationale | Human words — no prohibited language | ✓ |
| conditions_or_actions | 3 actions with owner and due date | ✓ |
| residual_risks_accepted | 4 risks listed | ✓ |
| follow_up_owner | Dr Luân | ✓ |
| follow_up_due_date | 2026-09-30 | ✓ |
| signature_or_external_attestation_reference | Provided | ✓ |

All 13 fields: **VALID**  
Prohibited approval language check: **CLEAR** (rationale explicitly excludes production/ethics/independent validation claims)

---

## Limitations this record cannot override

| Item | Status |
|------|--------|
| PROD-AUD-01 | OPEN — tracked as ACT-R1-01 |
| Replace-then-rehash (RR-02) | MEDIUM — inherent to local filesystem |
| Institutional SSO | NOT IMPLEMENTED |
| MFA | NOT IMPLEMENTED |
| Authenticated identity | NOT IMPLEMENTED |
| Production audit attribution | NOT IMPLEMENTED |
| Ethics/IRB approval | NOT IMPLEMENTED |
| Reviewer independence | NOT ESTABLISHED |
| Real research execution | BLOCKED |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
