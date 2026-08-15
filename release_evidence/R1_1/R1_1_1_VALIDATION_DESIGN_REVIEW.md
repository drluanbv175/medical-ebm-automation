# R1.1.1 Validation Design Review

**Document:** R1_1_1_VALIDATION_DESIGN_REVIEW.md  
**Date:** 2026-06-28  
**Phase:** R1.1.1 — Validation Evidence Pack  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **Câu bắt buộc:**
> R1.1 validates offline policy logic only.
> R1.1 does not validate production authentication.
> R1.1 does not validate SSO, MFA, real user identity,
> electronic signature, institutional delegation,
> or production audit attribution.

---

## 1. Intended Use of R1.1

R1.1 là **offline test harness** cho RBAC policy và synthetic identity model. Mục đích duy nhất:

| Mục đích | Mô tả |
|---------|-------|
| Kiểm định RBAC schema | Xác minh 10 roles, 15 permitted actions, 5 forbidden actions hoạt động đúng theo policy table |
| Kiểm định SoD guards | Xác minh 8 prohibited scenarios đều bị block với structured reason_code |
| Kiểm định delegation lifecycle | Xác minh 5 states (PROPOSED/ACTIVE/EXPIRED/REVOKED/REJECTED) và transitions đúng |
| Kiểm định audit hash chain | Xác minh SHA-256 hash chain và tamper detection hoạt động |
| Tài liệu hóa RBAC schema | Cung cấp basis cho R1.2 design review với IT Lead và institution |

R1.1 **không phải** production identity infrastructure. Nó là design documentation + code baseline dùng để kiểm tra policy trước khi đầu tư vào SSO/MFA.

---

## 2. Explicit Non-Intended Use

Những điều sau KHÔNG phải mục đích của R1.1 và không được suy ra từ kết quả R1.1:

| Không được dùng cho | Lý do |
|--------------------|-------|
| Xác thực user thật | Không có SSO, không có identity provider |
| Enforcement MFA | Không có authentication layer |
| Production RBAC service | Là offline simulation, không có persistent service |
| Electronic signature | ReviewLedger là manual attestation only, không phải e-sign |
| Ethics/IRB approval | Không liên quan; không thể mô phỏng |
| Independent review thật | Cần reviewer độc lập thật, không thể mô phỏng |
| Audit trail production | Là simulation với `production_valid=False` trên mọi event |
| Level-A pilot study | Chưa đủ điều kiện; cần GATE-R1 PASS |
| Research data processing | Không có EDC, không có eHospital integration |
| Kết luận "hệ thống an toàn" | Cần independent pentest (IQ-20, R1.5) |

---

## 3. Requirement Coverage Assessment

Tổng số requirements đã trace: **43** (xem `R1_1_1_REQUIREMENT_TEST_TRACEABILITY_MATRIX.csv`)

| Nhóm | Số requirement | Covered | Uncovered |
|------|---------------|---------|-----------|
| Synthetic identity boundary | 8 | 8 | 0 |
| RBAC allow rules | 5 | 5 | 0 |
| RBAC deny / forbidden actions | 5 | 5 | 0 |
| SoD controls | 8 | 8 | 0 |
| Delegation lifecycle | 5 | 5 | 0 |
| Audit event schema | 5 | 5 | 0 |
| Append-only ledger | 2 | 2 | 0 |
| Hash-chain integrity | 2 | 2 | 0 |
| Tamper detection | 1 | 1 | 0 |
| BLOCK decision structure | 1 | 1 | 0 |
| CLI boundaries | 1 | 1 | 0 |
| Hermetic / no-network | 1 | 1 | 0 |
| **Total** | **44** | **44** | **0** |

**CRITICAL requirements uncovered:** 0  
**HIGH requirements uncovered:** 0  

---

## 4. Test Design Adequacy

### 4.1 Test types used

| Type | Count | Examples |
|------|-------|---------|
| POSITIVE (happy path) | 15 | T04 PI can create, T11 DM can unlock with auth, T23a event fields |
| NEGATIVE (guard enforcement) | 24 | T07 SoD-01, T08 SoD-02, T26 tamper detect, T19 self-delegation |

### 4.2 Test isolation

- Mỗi test dùng `tmp_path` fixture của pytest cho JSONL ledgers → không có side effect giữa tests
- `build_default_registry()` trả về fresh registry mỗi lần gọi → không có shared state
- Không có database, không có file system state ngoài tmp_path

### 4.3 Test determinism

- Tất cả tests chạy hermetic với `MRAQ_OFFLINE_CI=1`
- Không có mock nào che giấu production code path trong R1.1 modules
- Datetime được tính tại runtime bằng `datetime.now(timezone.utc)` → `past_utc` và `future_utc` fixtures đảm bảo offset đúng

### 4.4 Adequacy gaps cần Validation Lead xem xét

| Gap | Mô tả |
|-----|-------|
| G-01 | CLI commands có compile check nhưng không có end-to-end functional test qua subprocess |
| G-02 | EXTERNAL_SUBMISSION và CLINICAL_RELEASE được cover qua shared guard path với FINAL_APPROVAL, không có dedicated test |
| G-03 | _RESEARCH_CONTENT_APPROVAL_ACTIONS set (SoD-02) không có test cho LOCK_RESEARCH_DATA bị block khi actor là SYSADMIN |
| G-04 | Expired role test (T14) chấp nhận cả hai reason_code; Validation Lead cần confirm policy intent |

---

## 5. Boundary-Condition Coverage

| Boundary | Tested | Test ID | Note |
|----------|--------|---------|------|
| Actor với 0 active roles | Có | T14 | expired role → no active roles |
| Actor vừa hết hạn (1h ago) | Có | T14 | `expires_at_utc = now - 1h` |
| Delegation window starts now | Có | T21 | `effective_from_utc = now` |
| Delegation window ended yesterday | Có | T22 | `effective_until_utc = now - 1d` |
| Ledger với 1 event | Có | T23a, T23b | single event verify |
| Ledger với 3 events | Có | T25 | multi-event hash chain |
| Empty permitted_actions list | Có | (DelegationError guard) | validated in _validate_delegation |
| Actor self-delegation | Có | T19 | same ID in both fields |
| Delegation with mixed valid+forbidden actions | Có | T20 | list containing FINAL_APPROVAL |

**Boundary không được test:**

| Boundary | Lý do thiếu | Risk |
|----------|------------|------|
| Actor với 0 role_assignments | Không test | LOW — active_roles() returns [] → BLOCK |
| Ledger với 1000+ events | Không test | LOW — JSONL is append-only; no upper bound |
| delegation_id không tồn tại | Không test | LOW — get_status() returns None |
| audit_event_hash truncation/collision | Không test | VERY LOW — SHA-256, 64-char hex |

---

## 6. Negative-Test Coverage

**16 abuse cases** đã được đánh giá trong `R1_1_1_NEGATIVE_TEST_AND_ABUSE_CASE_REVIEW.md`.

| Danh mục | Cases | PASS | MEDIUM+ risk |
|---------|-------|------|-------------|
| SoD violations | 5 | 5 | 1 (AC-05 reason_code) |
| Delegation abuse | 5 | 5 | 0 |
| Audit tampering | 2 | 2 | 1 (AC-11 WORM gap) |
| Identity overclaim | 2 | 2 | 0 |
| Forbidden action | 3 | 3 | 1 (AC-16 shared path) |
| **Total** | **16** | **16** | **3** |

3 cases với MEDIUM residual risk — tất cả là do giới hạn của offline harness; không phải bug.

---

## 7. Residual Risk Assessment

| Risk ID | Mô tả | Level | Mitigation |
|---------|-------|-------|-----------|
| RR-01 | SoD guards offline only; không có production technical enforcement | HIGH | R1.3 sẽ implement SSO + RBAC service |
| RR-02 | JSONL ledger không phải WORM; replace-then-rehash possible nếu có write access | MEDIUM | R1.3 yêu cầu WORM hoặc hash seal với external timestamp |
| RR-03 | Expired role (T14) chấp nhận cả hai reason_code; intent ambiguous | LOW | Validation Lead confirm |
| RR-04 | EXTERNAL_SUBMISSION/CLINICAL_RELEASE không có dedicated test | LOW | Shared guard path; same code |
| RR-05 | CLI không có functional E2E test | LOW | Compile + module tests cover logic |
| RR-06 | _RESEARCH_CONTENT_APPROVAL_ACTIONS set cho SoD-02 không test LOCK_RESEARCH_DATA case | LOW | Set defined in code; partially covered |

**No CRITICAL residual risk.** Tất cả MEDIUM risks đều là gap giữa offline simulation và production requirement (R1.3).

---

## 8. Fresh-Archive Reproducibility Evidence

Từ `R1_1_1_FRESH_ARCHIVE_EVIDENCE_CONFIRMATION.json` (Phase D):

| Evidence item | Value |
|---------------|-------|
| git_tag | r1.1-frozen |
| git_commit | 9fdfdff |
| archive_sha256 | 0523a9667c439628b6b5d223a3b7c5984a0e7d383831c2cbebf0c0fa11853007 |
| archive_size_bytes | 1,504,708 |
| passed | 836 |
| failed | 0 |
| skipped | 5 |
| network_attempts | 0 |
| api_attempts | 0 |
| real_pii_inputs | 0 |
| production_connector_attempts | 0 |

Kết quả hoàn toàn tái lập từ frozen archive dưới điều kiện hermetic.

---

## 9. Manifest and Registry Verification Evidence

| Check | Result | Detail |
|-------|--------|--------|
| manifest_path_in_repo | True | agent_source_manifest.csv present |
| manifest_self_check | MATCH | hash of manifest matches stored hash |
| agent_count | 48 | minimum 48 enforced |
| all_hash_verified | True | 0 mismatches |
| required_4_enforced_and_present | True | 4 core agents present |
| missing_agent_paths | 0 | all paths resolve |
| RESULT | PASS | |

---

## 10. Known Limitations

| # | Limitation | Impact |
|---|-----------|--------|
| L-01 | R1.1 không có production RBAC service; mọi enforcement là offline Python evaluation | SoD rules không được enforce tại API/network layer |
| L-02 | Không có SSO; synthetic_actor_id không được verify bởi identity provider | Không có authenticated attribution |
| L-03 | JSONL ledger là append-only nhưng không WORM; file có thể bị replace với rehashed content | Production cần WORM (R1.3) |
| L-04 | Delegation records không có PI authenticated signature | Manual attestation only |
| L-05 | CLI commands không được test E2E qua subprocess trong pytest | Logic được test qua module tests |
| L-06 | Independent security test (IQ-20) chưa được thực hiện | Cần external tester (R1.5) |
| L-07 | 5 tests skipped trong full suite — không liên quan đến R1.1 modules | Carryover từ earlier versions |

---

## 11. Required Validation Lead Decisions

| Decision ID | Câu hỏi | Phân loại |
|-------------|---------|-----------|
| VLD-01 | Shared guard path (T15) có đủ làm evidence cho EXTERNAL_SUBMISSION và CLINICAL_RELEASE không, hay cần dedicated tests? | Test adequacy |
| VLD-02 | _WRITE_ACTIONS set (SoD-03) có đủ đầy đủ không? Có action write nào bị thiếu không? | Policy completeness |
| VLD-03 | _RESEARCH_CONTENT_APPROVAL_ACTIONS set (SoD-02) có cần test thêm cho LOCK_RESEARCH_DATA không? | Test gap |
| VLD-04 | T14 chấp nhận hai reason_code — EXPIRED_ROLE hay ROLE_NOT_PERMITTED đều ok, hay cần specific code? | Policy intent |
| VLD-05 | Residual risk RR-02 (WORM gap) — có acceptable cho offline harness, hoặc cần note đặc biệt? | Risk acceptance |
| VLD-06 | CLI gap (G-01) — compile check có đủ, hay cần subprocess test? | Test scope |
| VLD-07 | SoD-02 ADMIN_RESEARCH_APPROVAL: test chỉ cover RECORD_REVIEW_ATTESTATION — cần test RECORD_EVIDENCE_ATTESTATION + LOCK_RESEARCH_DATA nữa không? | Test completeness |

---

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
