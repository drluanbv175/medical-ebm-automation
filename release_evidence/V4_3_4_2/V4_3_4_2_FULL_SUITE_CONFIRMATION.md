# V4.3.4.2 Full Suite Confirmation — Fresh Archive

**Acceptance ID:** V4.3.4.2-MRA-20260628  
**Date:** 2026-06-28T02:38:23Z  
**Source:** `git archive --format=tar --prefix=medical-ebm-automation/ v4.3.4`  
**Commit:** `101ca08a331605e95b15cb82a4839e0e2a799e3e`  
**Status:** DRAFT — REQUIRE HUMAN REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Môi trường

```
Platform:         darwin (macOS)
MRAQ_OFFLINE_CI:  1
ANTHROPIC_API_KEY: unset
OPENAI_API_KEY:    unset
EHOSPITAL_ENABLED: unset
```

---

## Kết quả

| Metric | Giá trị |
|--------|---------|
| collected | **781** |
| passed | **776** |
| failed | **0** |
| skipped | 5 |
| equation | 776 + 5 = 781 ✓ |
| exit_code | **0** |
| **Verdict** | **PASS** |

---

## Manifest + Registry

| Metric | Giá trị |
|--------|---------|
| manifest_path | `runtime/manifests/agent_source_manifest.csv` |
| manifest_hash_matches_self_check | true |
| manifest_rows | **48** |
| registry_agent_count | **48** |
| required_agents_present | true |
| all_hash_verified | true |
| hash_mismatches | **0** |
| missing_agent_paths | **0** |
| verifier (`scripts/verify_manifest_registry.py`) | **PASS** |

---

## Security invariants

```
NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
Real research execution:      BLOCKED
External release/submission:  BLOCKED
Live Agent behavior:          NOT VERIFIED
API connectivity:             NOT RUN
Independent review:           NOT ESTABLISHED
All outputs are DRAFT —       REQUIRE HUMAN REVIEW
```

---

*Manual review record does not constitute ethics, PI, final, or independent approval.*
