---
document: V4_3_3_2_D_R13_SEMANTIC_CORRECTION_REPORT
version: V4.3.3.2
generated: 2026-06-28
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# D-R13 Semantic Correction Report — V4.3.3.2

## Problem Statement

Gate D-R13 (`_dr13_no_external_action`) used `contains_external_action()` which performs
a plain substring match for markers: `submit`, `nộp`, `send_to_irb`, `upload_to_registry`,
`publish`, `post_to`, `email_to`, `gửi tới`, `nộp ethics`, `register_trial`.

**False positive root cause:** DRAFT template artifacts include mandatory safety
instruction text such as:
- "Không được tự nộp đề cương lên Hội đồng Đạo đức."
- "External submission is BLOCKED until human review."
- "Do not publish this draft without PI approval."

These prohibition phrases contain the same tokens as actual external actions, causing
D-R13 to FAIL on every fresh project build — even though no real action was being taken.

## Fix

### New function: `contains_external_action_positive(text)`

Added to `research_project/project_config.py`:

```python
_EXTERNAL_ACTION_NEGATION_CONTEXT = (
    "không được", "không tự", "không phép", "cấm",
    "blocked", "forbidden", "not allowed", "do not",
    "không ", "bị chặn", "disable", "block",
)

def contains_external_action_positive(text: str) -> bool:
    """True nếu có external action THẬT (không phải instruction cấm).
    Duyệt từng dòng: dòng có action marker + ngữ cảnh phủ định → bỏ qua.
    """
    for line in text.splitlines():
        line_low = line.lower()
        if not any(m.lower() in line_low for m in _EXTERNAL_ACTION_MARKERS):
            continue
        is_negated = any(neg in line_low for neg in _EXTERNAL_ACTION_NEGATION_CONTEXT)
        if not is_negated:
            return True
    return False
```

### Gate D-R13 updated

`research_project/project_qa_runner.py` — `_dr13_no_external_action()` now calls
`contains_external_action_positive()` instead of `contains_external_action()`.

**Note:** The strict `contains_external_action()` is kept unchanged for write-path
guards (artifact builder, change control) where it remains appropriate to be strict.

## Test Coverage (Phase E)

8 new tests covering D-R13 in `tests/test_v4_3_3_2_gate_corrections.py`:

| Test | Assertion | Result |
|------|-----------|--------|
| `test_v4332_dr13_safety_no_submit` | "không được tự nộp" → PASS | ✅ |
| `test_v4332_dr13_safety_blocked_publish` | "blocked/do not publish" → PASS | ✅ |
| `test_v4332_dr13_safety_forbidden_email` | "cấm email_to" → PASS | ✅ |
| `test_v4332_dr13_safety_do_not_post` | "DO NOT post_to" → PASS | ✅ |
| `test_v4332_dr13_real_action_submit` | "submit to IRB" → DETECT | ✅ |
| `test_v4332_dr13_real_action_publish` | "publish in Nature" → DETECT | ✅ |
| `test_v4332_dr13_mixed_lines` | safety + action lines → DETECT action | ✅ |
| `test_v4332_dr13_empty_content` | empty string → PASS | ✅ |
| `test_v4332_integration_fresh_draft_dr13_no_false_positive` | full template → PASS | ✅ |

## Security Invariants Preserved

- `contains_external_action()` (strict) unchanged → write-path still blocks all markers
- `contains_external_action_positive()` only used in D-R13 QA gate
- Safety instruction text ("KHÔNG được", "blocked", "do not") correctly identified
- Real action text without negation still triggers FAIL
- No API, network, or real data involved
