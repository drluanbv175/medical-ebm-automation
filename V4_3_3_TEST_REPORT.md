---
document: V4_3_3_TEST_REPORT
version: V4.3.3
commit: e57058f4eebe9e7f691c4937ad64e718326d6ec4
generated: 2026-06-28T00:45:00Z
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# V4.3.3 Test Report

## Environment

| Field | Value |
|-------|-------|
| Commit | `e57058f4eebe9e7f691c4937ad64e718326d6ec4` |
| Python | 3.9.6 |
| pytest | 8.4.2 |
| Platform | darwin (macOS) |
| venv | `~/.ebm-venv` (external to OneDrive per project convention) |
| MRAQ_OFFLINE_CI | 1 (set for hermetic archive run) |
| ANTHROPIC_API_KEY | unset |
| OPENAI_API_KEY | unset |
| EHOSPITAL_ENABLED | unset |

---

## Run 1 — Working Tree (branch head)

```
pytest --tb=short -q
```

| Metric | Value |
|--------|-------|
| collected | 746 |
| passed | 739 |
| failed | 0 |
| skipped | 7 |
| warnings | 1 (urllib3 LibreSSL — test infra only, not product) |
| exit_code | 0 |
| duration | ~7.7 s |

---

## Run 2 — Hermetic Archive (from `git archive e57058f`, isolated directory)

```
cd <SCRATCHPAD>/v4_3_3_fresh_archive
MRAQ_OFFLINE_CI=1 pytest --tb=short -q
```

| Metric | Value |
|--------|-------|
| collected | 746 |
| passed | 741 |
| failed | 0 |
| skipped | 5 |
| warnings | 1 (urllib3 LibreSSL — test infra only) |
| exit_code | 0 |
| duration | ~5.4 s |

**Difference (7 vs 5 skipped):** 2 additional tests are skipped on working tree due to venv
path resolution differences; both runs exit 0 with 0 failures.

---

## Collect-Only

```
pytest --co -q
746 tests collected
```

All 746 tests resolvable without network or API.

---

## Test Distribution by Module

| Test file | Tests |
|-----------|-------|
| `test_v4_3_3_project_dossier.py` (V4.3.3 NEW) | 38 |
| `test_research_project_workflow.py` | ~60 |
| `test_research_studio_*.py` | ~80 |
| `test_runtime_*.py` | ~120 |
| `test_workflow_state_machine.py` | ~80 |
| Other test files | ~368 |
| **Total** | **746** |

---

## V4.3.3 New Tests — Detail (38 functions)

### Group 1 — project_config (T1–T3)
- T1: StudyType has 7 values — PASS
- T2: ArtifactID has 19 artifacts — PASS
- T3: PII/fabrication/external-action/real-data guards detect correctly — PASS

### Group 2 — project_artifact_graph (T4–T6)
- T4: RESEARCH_CHARTER has downstream artifacts — PASS
- T5: mark_stale() propagates STALE to dependents — PASS
- T6: topological_build_order() returns all 19 ArtifactIDs — PASS

### Group 3 — project_registry (T7–T10)
- T7: register() + load() round-trip — PASS
- T8: duplicate registration raises DuplicateProjectError — PASS
- T9: unknown project raises UnknownProjectError — PASS
- T10: list_projects() returns correct count — PASS

### Group 4 — project_evidence_intake (T11–T13)
- T11: add_evidence() + load_all() round-trip — PASS
- T12: PII in source_description → BLOCKED — PASS
- T13: RETRACTED on new add → BLOCKED — PASS

### Group 5 — project_methodology_planner (T14–T17)
- T14: 7 study types × correct reporting standard (parametrized, 7 variants) — PASS ×7
- T15: MethodologyPlan RCT has REQUIRE_HUMAN_INPUT in sample_size_note — PASS
- T16: CRF RCT has ≥3 sections including AE — PASS
- T17: Reporting checklist item counts (CONSORT≥25, PRISMA≥20, COREQ≥30) — PASS

### Group 6 — project_dossier_builder (T18–T20)
- T18: build() total artifacts_created + artifacts_skipped = 19 — PASS
- T19: PII in title → blocked — PASS
- T20: PROTOCOL_DRAFT contains REQUIRE_HUMAN_INPUT marker — PASS

### Group 7 — project_change_control (T21–T23)
- T21: record_change() creates CHG- record, bumps version — PASS
- T22: PII in new_value → BLOCKED — PASS
- T23: audit log append-only, 3 records, all with correct project_id — PASS

### Group 8 — project_qa_runner (T24–T27)
- T24: D-R9/D-R10/D-R11 PASS on clean dossier — PASS
- T25: D-R10 FAIL when PII injected into artifact — PASS
- T26: D-R9 FAIL when fabrication marker injected — PASS
- T27: D-R11 FAIL when draft_only=False — PASS

### Group 9 — project_review_pack (T28–T29)
- T28: Review pack generates ≥1 decision when objectives contain RHI — PASS
- T29: Review pack markdown contains DISCLAIMER — PASS

### Group 10 — project_cli (T30)
- T30: CLI project-status exits 0 after project-init — PASS

### Invariants (2)
- invariant_no_api_import: package does not import anthropic/openai — PASS
- invariant_all_artifacts_have_filename: every ArtifactID has ARTIFACT_FILENAME entry — PASS

---

## Safety Counters

| Counter | Value |
|---------|-------|
| network_attempts | 0 |
| api_attempts | 0 |
| real_pii_inputs | 0 |
| synthetic_pii_guard_cases | 3 (T12, T19, T22 — all BLOCKED as expected) |
| production_connector_attempts | 0 |

---

## Conclusion

```
739 passed, 7 skipped (working tree)   — exit 0
741 passed, 5 skipped (hermetic archive) — exit 0
0 failures in either run
```

**Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE**
**All outputs are DRAFT — REQUIRE HUMAN REVIEW**
