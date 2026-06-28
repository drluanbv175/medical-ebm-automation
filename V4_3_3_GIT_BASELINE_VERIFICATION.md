---
document: V4_3_3_GIT_BASELINE_VERIFICATION
version: V4.3.3
commit: e57058f4eebe9e7f691c4937ad64e718326d6ec4
branch: feat/v4-3-3-research-project-dossier
generated: 2026-06-28T00:45:00Z
qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE
---

# V4.3.3 Git Baseline Verification

## 1. Commit Identity

| Field | Value |
|-------|-------|
| Commit | `e57058f4eebe9e7f691c4937ad64e718326d6ec4` |
| Short | `e57058f` |
| Branch | `feat/v4-3-3-research-project-dossier` |
| Message | `feat: V4.3.3 research_project dossier & change-control automation (PHASE K)` |
| Parent | `863390f` (V4.3.2.1 reproducible offline automation baseline) |
| Files changed | 16 (+5012 insertions, −1 deletion) |

---

## 2. Required Directories — Tracked Status

| Path | In Archive | Status |
|------|-----------|--------|
| `runtime/` | ✅ | PRESENT — agent_registry.py, agent_runtime.py, approval_ledger.py, audit_logger.py, claude_api_runtime.py, controlled_orchestrator.py, data_boundary.py, dispatch_guard.py, ehospital_connector.py, mock_agent_runtime.py, policy_gate_engine.py, schemas.py, workflow_context.py, workflow_state_machine.py |
| `runtime/manifests/` | ✅ | PRESENT — agent_source_manifest.csv (48 agent rows) |
| `research_studio/` | ✅ | PRESENT — artifact_registry.py, capability_profile.py, dashboard.py, governance.py, project_registry.py, project_schema.py, research_quality_checks.py, research_workflow.py, study_type_router.py |
| `research_automation/` | ✅ | PRESENT — artifact_template_engine.py, automation_cli.py, automation_dashboard_data.py, idempotency_guard.py, project_intake.py, project_snapshot.py, quality_gate_runner.py, retry_policy.py, review_queue.py, run_registry.py, schedule_runner.py, work_queue.py, workflow_runner.py |
| `research_project/` | ✅ | PRESENT (V4.3.3 NEW) — 14 Python files: __init__.py + 13 modules |
| `tests/` | ✅ | PRESENT — 746 tests collected across all test_*.py files |
| `scripts/` | ✅ | PRESENT — bridge_to_ebm_master.py, run_agent_registry.py, verify_manifest_registry.py + others |
| `.github/` | ✅ | PRESENT — .github/workflows/offline-ci.yml |
| `.claude/agents/` | ✅ | PRESENT — 74 agent .md files (48 named agents + 26 shared policy docs) |
| `dashboard_mockups/templates/` | ✅ | PRESENT — evidence-workbench-template.html, dark-analyst-template.html |
| `automation_schedule.yaml` | ✅ | PRESENT |
| `research_project_request.yaml` | ✅ | PRESENT (updated V4.3.3) |

---

## 3. Key V4.3.3 Additions Verified in Archive

### research_project/ package (13 modules + __init__)

| Module | Lines (approx) | Role |
|--------|---------------|------|
| `project_config.py` | ~230 | Enums, dataclasses, safety guards |
| `project_artifact_graph.py` | ~130 | Dependency graph, Kahn topological sort, mark_stale() |
| `project_registry.py` | ~190 | Filesystem registry, register/load/save/list |
| `project_evidence_intake.py` | ~210 | evidence_manifest.csv, EV- ID, PII/retracted guards |
| `project_methodology_planner.py` | ~260 | 7 study-type checklists (STROBE/CONSORT/STARD/PRISMA/COREQ) |
| `project_crf_builder.py` | ~280 | CRF sections per study type → Markdown table |
| `project_sap_builder.py` | ~350 | SAP sections per study type with lock_reminder |
| `project_reporting_planner.py` | ~310 | STROBE-22/CONSORT-35/STARD-24/PRISMA-28/COREQ-32 |
| `project_change_control.py` | ~230 | ImmutableAuditLog JSONL, ChangeControlEngine, bump_version |
| `project_dossier_builder.py` | ~430 | Orchestrator: 19 artifacts in topological order |
| `project_qa_runner.py` | ~330 | 15 quality gates D-R1..D-R15 |
| `project_review_pack.py` | ~360 | Structured human review pack, decision list |
| `project_cli.py` | ~280 | researchctl CLI: 8 subcommands |
| `__init__.py` | ~75 | Package exports |

### tests/test_v4_3_3_project_dossier.py

- 38 test functions (30 named + 2 invariants + 6 parametrized variants)
- Covers all 13 modules
- All deterministic, no network, no API

---

## 4. Tracked vs Untracked Source

### Tracked in e57058f (source critical)
All files listed in `git ls-tree -r --name-only e57058f` — 100% committed.

### Untracked at commit time (non-critical)
- `MRAQ100_AUDIT/` — audit output directory, not source
- `__pycache__/` — bytecode, excluded by .gitignore
- `.env` — secrets, excluded by .gitignore (symlink to ~/.ebm-secrets/)
- `projects/` — runtime project dossiers created by CLI

### Source missing from archive
- None. All required source directories are tracked and present.

---

## 5. Archive Self-Containment Assessment

| Check | Result |
|-------|--------|
| `.claude/agents/` in archive | ✅ 74 files |
| `runtime/manifests/` in archive | ✅ agent_source_manifest.csv (48 rows) |
| `research_project/` package complete | ✅ 14 Python files |
| No dependency on parent folder | ✅ Verified — archive tested in isolated SCRATCHPAD dir |
| No API key required | ✅ Tests pass with ANTHROPIC_API_KEY unset |
| No eHospital flags required | ✅ Tests pass with EHOSPITAL_ENABLED unset |
| `requirements.txt` present | ✅ (venv dependencies managed externally per project convention) |

**Conclusion: Archive is self-contained.**

---

## 6. Baseline Reproducibility

| Step | Result |
|------|--------|
| `git archive --format=tar e57058f` | ✅ Exit 0, 5.5 MB |
| `tar xf v4_3_3_baseline.tar -C <clean_dir>` | ✅ Exit 0 |
| `pytest --co -q` from archive | ✅ 746 tests collected |
| `pytest --tb=short -q` from archive (MRAQ_OFFLINE_CI=1) | ✅ 741 passed, 5 skipped, exit 0 |
| `researchctl project-init` | ✅ HERMETIC-001 registered |
| `researchctl project-build` | ✅ 19/19 artifacts created |
| `researchctl project-qa` | ⚠️ 13 PASS, 1 FAIL (D-R13 expected DRAFT behavior), 1 WARN |
| `researchctl project-review-pack` | ✅ 6 decisions generated |
| `researchctl project-reproducibility-check` | ✅ 19/19 artifacts present |

**D-R13 note**: Gate correctly flags fresh DRAFT artifacts that contain "BLOCKED" instruction text (e.g., "KHÔNG được tự nộp"). This is expected DRAFT-state behavior — the gate is working as designed. PI must review and update before release.

**Conclusion: Baseline IS reproducible.**

---

## 7. Security Invariants Verified in Archive Source

| Invariant | Verified |
|-----------|---------|
| `NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE` | ✅ in project_cli.py, project_qa_runner.py |
| "Không gọi API, network, Claude/OpenAI SDK" | ✅ no such imports in research_project/ |
| PII → BLOCK | ✅ contains_pii() guard in every write path |
| Fabrication → BLOCK | ✅ contains_fabrication() guard |
| Real data → BLOCK | ✅ contains_real_data() guard |
| External action → BLOCK | ✅ contains_external_action() guard |
| eHospital/HIS/EMR/LIS/PACS → BLOCK | ✅ in ehospital_connector.py policy gate |
| `draft_only=True` bắt biến | ✅ enforced in ProjectConfig + dossier_builder |
| All outputs DRAFT — REQUIRE HUMAN REVIEW | ✅ DISCLAIMER constant in every artifact |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
*All outputs are DRAFT — REQUIRE HUMAN REVIEW*
