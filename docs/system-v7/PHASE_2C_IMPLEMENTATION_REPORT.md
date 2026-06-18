# Phase 2C Implementation Report

Ngày: 2026-06-18.

## File chính đã thêm/sửa

- Selection config: `config/phase_2c_pilot_selection.yaml`.
- Selection gate: `app/clinical_content/phase_2c_selection.py`.
- Pathway review-only: `app/clinical_content/pilot_pathway_builder.py`, `app/clinical_content/pilot_pathway_validator.py`, `app/clinical_content/pilot_pathway_release_gate.py`.
- Hypertension real-pack draft: `knowledge-packs/hypertension_adult_outpatient/2026.1-draft/`.
- Hypertension pathway: `app/clinical_content/hypertension_pilot_pathway_builder.py`, `app/clinical_content/hypertension_pilot_pathway_validator.py`, `app/clinical_content/hypertension_pilot_pathway_release_gate.py`.
- Hypertension local adaptation: `app/evidence/hypertension_local_adaptation.py`.
- Shadow schema: `app/clinical_content/phase_2c_shadow.py`.
- Synthetic vignettes: `app/clinical_content/phase_2c_vignettes.py`.
- Live validation command: `scripts/phase_2c_live_source_validation.py`.
- Dashboard read-only screens: `app/dashboard/v7_readonly.py`.
- ChatGPT Project manifest: `exports/chatgpt_project/v7_manifest.json`.
- Tests: `tests/test_phase_2c_*.py`.

## Implementation status

Phase 2C hạ tầng đã được tạo. Bác sĩ đã chọn `hypertension_adult_outpatient`; một Clinical Knowledge Pack bản nháp review-only đã được tạo tại `knowledge-packs/hypertension_adult_outpatient/2026.1-draft/`.

Pack này chưa được phép dùng cho shadow pilot thật vì approval record vẫn ở trạng thái `pending`, các claim đang `SOURCE_UNAVAILABLE`/`pending`, và mọi release clinical production vẫn bị chặn. Đây là chặn an toàn có chủ ý.

## Validation so far

- Phase 2C focused tests after hypertension pack: 7 passed.
- Full pytest: 285 passed, 1 urllib3/LibreSSL warning.
- Ruff: PASS.
- Compileall: PASS with `PYTHONPYCACHEPREFIX=/private/tmp/ebm-phase2c-pycache`.
- Agent sync check: PASS, 48 source agents, 48 `.Codex/agents` TOML, 48 `.codex/agents` TOML.
- EBM audit: PASS.
- Live source command kept unavailable network sources as `SOURCE_UNAVAILABLE`; no offline source was marked PASS.
- ChatGPT Project manifest: 34 files, `safe_to_upload=true`, `contains_pii=false`, `recommendation_unapproved_count=3`, `failed_runs_count=6`.

Because approval status is still `pending` and source claims are not verified, the correct Phase 2C decision remains NO-GO for physician-supervised real-pack shadow pilot.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
