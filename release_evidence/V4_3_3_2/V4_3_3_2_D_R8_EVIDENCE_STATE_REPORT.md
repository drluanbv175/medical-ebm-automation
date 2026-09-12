---
document: V4_3_3_2_D_R8_EVIDENCE_STATE_REPORT
version: V4.3.3.2
generated: 2026-06-28
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# D-R8 Evidence State Correction Report — V4.3.3.2

## Problem Statement

Gate D-R8 (`_dr8_evidence_status`) returned a generic `GateStatus.WARN` with an
undifferentiated message when the evidence manifest was empty:

```
"evidence_manifest.csv trống — chưa có bằng chứng nào được nhập."
```

This made it impossible for orchestrators to distinguish:
- "No evidence yet loaded" (PI must supply) → `REQUIRE_HUMAN_EVIDENCE_INPUT`
- "Evidence present but needs review" → `REQUIRE_HUMAN_REVIEW`
- "Retracted evidence in use" → `BLOCK`

## Fix

### New constants in `project_config.py`

```python
EVIDENCE_GATE_STATE_PASS                 = "PASS"
EVIDENCE_GATE_STATE_REQUIRE_HUMAN_INPUT  = "REQUIRE_HUMAN_EVIDENCE_INPUT"
EVIDENCE_GATE_STATE_REQUIRE_HUMAN_REVIEW = "REQUIRE_HUMAN_REVIEW"
EVIDENCE_GATE_STATE_BLOCK                = "BLOCK"
```

### New field in `QualityGateResult`

```python
evidence_gate_state: Optional[str] = None  # D-R8 semantic state only
```

Included in `as_dict()` only when set (non-None), backward-compatible.

### D-R8 state mapping

| Condition | GateStatus | evidence_gate_state |
|-----------|------------|---------------------|
| evidence/ dir absent | SKIP | None |
| manifest empty (0 items) | WARN | `REQUIRE_HUMAN_EVIDENCE_INPUT` |
| ≥1 RETRACTED | FAIL | `BLOCK` |
| ≥1 MANUAL_REVIEW_REQUIRED | WARN | `REQUIRE_HUMAN_REVIEW` |
| All VERIFIED_BY_HUMAN | PASS | `PASS` |

**Design note:** `REQUIRE_HUMAN_EVIDENCE_INPUT` maps to `WARN` not `FAIL` because
empty manifest is an expected initial state for a new project — it requires PI input,
not a system error. Orchestrators checking `evidence_gate_state` can distinguish this
from other warnings.

## Test Coverage (Phase E)

5 new tests in `tests/test_v4_3_3_2_gate_corrections.py`:

| Test | Condition | Expected state | Result |
|------|-----------|---------------|--------|
| `test_v4332_dr8_empty_manifest_state` | manifest empty | `REQUIRE_HUMAN_EVIDENCE_INPUT` | ✅ |
| `test_v4332_dr8_retracted_state` | RETRACTED in manifest | `BLOCK` | ✅ |
| `test_v4332_dr8_manual_review_state` | MANUAL_REVIEW_REQUIRED | `REQUIRE_HUMAN_REVIEW` | ✅ |
| `test_v4332_dr8_verified_state` | VERIFIED_BY_HUMAN | `PASS` | ✅ |
| `test_v4332_dr8_no_evidence_dir` | no evidence/ dir | SKIP / None | ✅ |

## Backward Compatibility

- `GateStatus` enum unchanged (PASS/FAIL/WARN/SKIP)
- `evidence_gate_state` is optional; absent for all gates except D-R8
- `as_dict()` only emits `evidence_gate_state` key when set — existing JSON consumers unaffected
- All 53 existing + new tests pass: 0 regressions
