---
document: V4_3_3_2_FULL_SUITE_TEST_REPORT
version: V4.3.3.2
generated: 2026-06-28
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
verification_type: FULL_SUITE_FRESH_ARCHIVE
---

# V4.3.3.2 Full-Suite Fresh-Archive Test Report

## Environment

| Item | Value |
|------|-------|
| Git commit | `0ce0d472f3c739806a59c2c066948fe7a11f954f` |
| Git commit short | `0ce0d47` |
| Archive SHA256 | `591a1a8981704b03ff5eb85d7bb380224514c58fde7be3474286790fc70beaf1` |
| Archive size | 5,980,160 bytes |
| Archive file count | 722 |
| Symlinks in archive | 0 |
| Python | 3.9.6 |
| pytest | 8.4.2 |
| Platform | macOS arm64 |
| MRAQ_OFFLINE_CI | 1 |
| API keys set | none |
| eHospital flags | unset |
| Source isolation | used_only_source_inside_archive = true |

---

## Phase 0 — Precheck

| Check | Result |
|-------|--------|
| Commit `0ce0d47` exists | ✅ PASS |
| Tag `v4.3.3.2-frozen` pre-existing | ✅ Not pre-existing (created after verification) |
| Working tree clean | ✅ Clean |
| API keys in environment | ✅ None |
| eHospital flags | ✅ Unset |

---

## Phase 1 — Archive Creation

```
git archive --format=tar --prefix=medical-ebm-automation/ 0ce0d47 > v4_3_3_2_baseline.tar
```

| Field | Value |
|-------|-------|
| archive_sha256 | `591a1a8981704b03ff5eb85d7bb380224514c58fde7be3474286790fc70beaf1` |
| archive_size_bytes | 5,980,160 |
| files_in_archive | 722 |
| symlinks | 0 |
| self_contained | true |

---

## Phase 2 — Full Test Suite (Fresh Archive)

### Manifest + Registry Verify

```
manifest_self_check=MATCH
agent_count=48 (min=48)
all_hash_verified=True
required_4_enforced_and_present=True
RESULT=PASS
```

### pytest --collect-only

```
761 tests collected
```

### Full Suite Run

**Command:** `MRAQ_OFFLINE_CI=1 python3 -m pytest -q -p no:cacheprovider --junit-xml=...`

**Result: 756 passed, 5 skipped, 0 failed — exit 0**

| Metric | Value |
|--------|-------|
| collected | 761 |
| passed | 756 |
| failed | 0 |
| skipped | 5 |
| exit_code | 0 |
| duration_seconds | 6 |
| consistency | 761 = 756 + 0 + 5 ✅ |

> Note: 761 collected vs baseline 756+5=761 — consistent with V4.3.3.2 (53 targeted tests) + previous full suite (756 passed, 5 skipped). Collect-only, JUnit XML, and text run all agree.

---

## Phase 3 — Project Dossier CLI Smoke

| Step | Result |
|------|--------|
| `project-init` (canonical YAML) | ✅ PASS — exit 0 |
| `project-build` | ✅ PASS — 19/19 artifacts DRAFT created, exit 0 |
| `project-qa` | ✅ PASS — 14 PASS, 0 FAIL, 1 WARN (D-R8 REQUIRE_HUMAN_EVIDENCE_INPUT), exit 0 |
| `project-review-pack` | ✅ PASS — 5 decisions generated, exit 0 |
| `project-reproducibility-check` | ✅ PASS — 19/19 artifacts present, exit 0 |

**Artifact invariants:**
- 19/19 artifacts created
- All DRAFT (no final/released/submitted artifacts found)
- No PII markers in any artifact
- No external endpoints or API calls
- Review pack generated with 5 human decisions needed
- Reproducibility: 19/19 present

---

## Phase 4 — D-R13 Semantic Validation

### A. Safe Instructional Text (expected: PASS = False)

| Text | Result |
|------|--------|
| `Không được tự nộp đề cương.` | ✅ PASS (no false positive) |
| `External submission is blocked.` | ✅ PASS (no false positive) |
| `Không được phát hành ra ngoài hệ thống.` | ✅ PASS (no false positive) |
| `Cần PI/human review trước bất kỳ hành động bên ngoài nào.` | ✅ PASS (no false positive) |
| `Không tự nộp ethics, protocol, manuscript hoặc báo cáo.` | ✅ PASS (no false positive) |
| `KHÔNG publish kết quả khi chưa được PI phê duyệt.` | ✅ PASS (no false positive) |
| `Do not submit to any external registry.` | ✅ PASS (no false positive) |
| `Cấm nộp bất kỳ tài liệu nào ra ngoài hệ thống.` | ✅ PASS (no false positive) |

**ALL_SAFE_PASS: True (8/8)**

### B. Structured External Action (expected: BLOCK = True)

| Action | Result |
|--------|--------|
| `submit protocol to IRB` | ✅ BLOCK |
| `action_type=SUBMIT` | ✅ BLOCK |
| `publish results now` | ✅ BLOCK |
| `gửi tới tạp chí ngay` | ✅ BLOCK |
| `nộp ethics application` | ✅ BLOCK |
| `upload_to_registry` | ✅ BLOCK |
| `send_to_irb: true` | ✅ BLOCK |
| `post_to external server` | ✅ BLOCK |
| `email_to journal@example.com` | ✅ BLOCK |
| `register_trial on ClinicalTrials.gov` | ✅ BLOCK |

**ALL_ACTION_BLOCK: True (10/10)**

**D-R13 OVERALL: PASS**

---

## Phase 5 — D-R8 Evidence-State Validation

| Situation | GateStatus | evidence_gate_state | Result |
|-----------|-----------|---------------------|--------|
| Empty manifest | WARN | REQUIRE_HUMAN_EVIDENCE_INPUT | ✅ PASS |
| RETRACTED citation | FAIL | BLOCK | ✅ PASS |
| MANUAL_REVIEW_REQUIRED | WARN | REQUIRE_HUMAN_REVIEW | ✅ PASS |
| VERIFIED_BY_HUMAN | PASS | PASS | ✅ PASS |

**No bare WARN without semantic state: True**

**D-R8 OVERALL: PASS**

---

## Phase 6 — Safety Counters

| Counter | Value | Condition |
|---------|-------|-----------|
| network_attempts | 0 | ✅ PASS |
| api_attempts | 0 | ✅ PASS |
| real_pii_inputs | 0 | ✅ PASS |
| synthetic_pii_guard_cases | 3 | ✅ Allowed (blocked correctly) |
| production_connector_attempts | 0 | ✅ PASS |
| direct_network_imports_in_source | 0 | ✅ PASS |

---

## Final Verdict

**PASS — V4.3.3.2 GATE CORRECTIONS AND REPOSITORY RATIONALIZATION BASELINE FROZEN**

```
Repository rationalization:           PASS
D-R13 semantic correctness:           PASS
D-R8 evidence-state correctness:      PASS
Full-suite baseline reproducibility:  PASS (756 passed, 0 failed)
Real research execution:              BLOCKED
External release/submission:          BLOCKED
Live Agent behavior:                  NOT VERIFIED
API connectivity:                     NOT RUN
Independent review:                   NOT ESTABLISHED
Qualification:                        NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
```

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
