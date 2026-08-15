# Phase 2B Implementation Report

Ngày: 2026-06-18.

## File chính đã thêm/sửa

- Live-source validation: `app/evidence/live_adapters/`, `app/evidence/live_adapter_registry.py`, `app/evidence/source_health_monitor.py`, `app/evidence/citation_cache.py`, `app/evidence/citation_provenance.py`.
- Scripts: `scripts/phase_2b_live_source_smoke_test.py`, `scripts/phase_2b_migrate_test_db.py`, `scripts/phase_2b_rollback_test_db.py`, `scripts/phase_2b_seed_governance_test_data.py`.
- Shadow pilot: `app/clinical_content/shadow_pilot.py`.
- ResearchOS pilot: `app/research_os/pilot.py`.
- Red-team: `app/safety/red_team.py`, `tests/evals/red_team/`.
- Dashboard read-only: `app/dashboard/v7_readonly.py`.
- Tests: `tests/test_phase_2b_*.py`.

## Safety boundaries

Risky clinical flags vẫn mặc định `False`: `v7_clinical_release`, `v7_patient_education_export`, `v7_emr_write`, `v7_production_pathway`, `v7_auto_apply_recommendations`.

Không bật clinical production. Không kê đơn. Không ghi EMR/HIS. Không gửi patient-facing output.

## Focused validation

- Phase 2B focused tests: 8 passed.
- Live-source smoke: PASS safe statuses; network/DNS unavailable sources are `SOURCE_UNAVAILABLE`.
- Test DB migration: PASS.
- Test DB rollback/reapply: PASS.

## Full validation

- Full pytest: 276 passed, 1 warning.
- Ruff: PASS.
- Compileall: PASS.
- Live-source smoke: PASS safe statuses.
- Test DB migration: PASS.
- Test DB rollback/reapply: PASS.
- Agent sync check: PASS, 48 source agents, 48 Codex TOML.
- EBM audit: PASS.
- ChatGPT Project manifest: 47 files, `safe_to_upload=true`.

Không có clinical production flag nào được bật.
