# Phase 2C Synthetic Vignette Report

Ngày: 2026-06-18.

## Module

- `app/clinical_content/phase_2c_vignettes.py`
- `tests/evals/clinical_safety/vignettes/phase_2c_minimum_vignettes.json`

Topic: `hypertension_adult_outpatient`.

## Distribution

- 10 routine pathway scenarios.
- 8 missing-data scenarios.
- 5 red flag/referral scenarios.
- 4 high-risk medication/contraindication scenarios.
- 3 evidence conflict/source unavailable scenarios.

Total: 30 synthetic vignettes, no PII, no free LLM output dependency.

## Metrics

Focused tests PASS:

- `routine_pathway_gate_accuracy = 1`
- `missing_data_block_accuracy = 1`
- `red_flag_detection_rate = 1`
- `contraindication_block_rate = 1`
- `critical_red_flag_miss = 0`
- `emergency_referral_miss = 0`
- `contraindicated_medication_allowed = 0`
- `recommendation_without_verified_traceability_released = 0`
- `approval_bypass = 0`
- `pii_leakage = 0`

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
