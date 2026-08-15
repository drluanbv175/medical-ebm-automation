---
document: V4_3_3_EXECUTIVE_SUMMARY
version: V4.3.3
commit: e57058f4eebe9e7f691c4937ad64e718326d6ec4
generated: 2026-06-28T00:45:00Z
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# V4.3.3 Executive Summary — Research Project Dossier Automation

## Identity

| Field | Value |
|-------|-------|
| Version | V4.3.3 |
| Commit | `e57058f4eebe9e7f691c4937ad64e718326d6ec4` |
| Branch | `feat/v4-3-3-research-project-dossier` |
| Parent baseline | `863390f` (V4.3.2.1) |
| Date | 2026-06-28 |
| Python | 3.9.6 |
| pytest | 8.4.2 |

## What Was Delivered

V4.3.3 adds the `research_project/` package — a **13-module, offline, deterministic, DRAFT-only** per-project dossier automation layer for medical research projects.

### Core capability

Given a synthetic project config (YAML/JSON), the system automatically generates a **19-artifact research dossier** adapted to 7 study types (cross-sectional, cohort, case-control, RCT, diagnostic, SR/MA, qualitative), covering the full arc from Research Charter through Version Register.

### Safety invariants (unchanged from V4.3.x)

- OFFLINE: zero network calls, zero API calls, zero eHospital/HIS/EMR/LIS/PACS connections
- DRAFT-ONLY: `draft_only=True` enforced in every write path; `REQUIRE_HUMAN_INPUT` marker in all template placeholders
- PII guard: `contains_pii()` blocks at every write boundary
- Fabrication guard: `contains_fabrication()` blocks at every write boundary
- External action guard: `contains_external_action()` blocks in change control and QA gates
- Immutable audit log: `audit_log.jsonl` append-only; never deleted or modified

## Test Results (from commit e57058f)

| Run context | Collected | Passed | Failed | Skipped | Exit |
|-------------|-----------|--------|--------|---------|------|
| Working tree | 746 | 739 | 0 | 7 | 0 |
| Hermetic archive (MRAQ_OFFLINE_CI=1) | 746 | 741 | 0 | 5 | 0 |

- network_attempts: **0**
- api_attempts: **0**
- real_pii_inputs: **0**
- synthetic_pii_guard_cases: **3** (T12, T19, T22 — all correctly BLOCKED)
- production_connector_attempts: **0**

## Project CLI Smoke (from archive, project HERMETIC-001)

| Step | Result |
|------|--------|
| `project-init` | PASS — project registered |
| `project-build` | PASS — 19/19 artifacts created |
| `project-qa` | 13/15 PASS; D-R13 expected DRAFT flag; D-R8 WARN (no evidence) |
| `project-review-pack` | PASS — 6 decisions generated |
| `project-reproducibility-check` | PASS — 19/19 artifacts on disk |

## Qualification

```
NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

Real research execution: BLOCKED
External release/submission: BLOCKED
Live Agent behavior: NOT VERIFIED
API connectivity: NOT RUN
Independent review: NOT ESTABLISHED

All outputs are DRAFT — REQUIRE HUMAN REVIEW
Cần bác sĩ / PI kiểm chứng — KHÔNG thực thi thật.
```
