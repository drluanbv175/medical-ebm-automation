# Phase 2C Shadow Pilot Protocol

Ngày: 2026-06-18.

## Module

- `app/clinical_content/phase_2c_shadow.py`

## Allowed schema

- `shadow_pilot_case_id`
- `pathway_id`
- `pathway_version`
- `environment`
- `clinical_domain`
- `question_type`
- `data_completeness`
- `red_flag_screen`
- `comorbidity_flags`
- `medication_context`
- `evidence_snapshot_id`
- `physician_review_required`

## Forbidden fields

- `patient_name`
- `date_of_birth`
- `phone_number`
- `address`
- `medical_record_number`
- `exact_visit_date`
- `photo`
- `free_text_containing_identifiers`

## Not allowed in pilot

- No treatment-plan change.
- No patient message.
- No EMR/HIS write.
- No prescription.
- No release flag enablement.
- No PII.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
