# Phase 2C Pack Selection Status

Ngày: 2026-06-18.

## Config

- `config/phase_2c_pilot_selection.yaml`

## Current state

- `selected_pack = hypertension_adult_outpatient`
- `physician_approval_required = true`
- `approval_record_path = docs/system-v7/PHASE_2C_HYPERTENSION_SELECTION_RECORD.json`
- `approval_status = pending`

Allowed choices:

- `hypertension_adult_outpatient`
- `adult_asthma_outpatient`
- `type_2_diabetes_outpatient`

## Decision

The topic has been selected as `hypertension_adult_outpatient` / tăng huyết áp người lớn ngoại trú ổn định. A review-only draft Clinical Knowledge Pack now exists at `knowledge-packs/hypertension_adult_outpatient/2026.1-draft/`.

Current pack state:

- 13/13 required pack artifacts exist.
- Claims are traceable to named source pages but remain `SOURCE_UNAVAILABLE` until live validation succeeds.
- Approval remains `pending`; release remains blocked.
- Clinical production, prescription, dose generation, patient-facing output, EMR/HIS write, and auto-apply are not allowed.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
