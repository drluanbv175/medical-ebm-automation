# Phase 2D Shadow Pilot Case Form

Use only de-identified, minimal case metadata. Do not enter patient name, date of birth, phone, address, MRN, exact visit date, images, or free text containing identifiers.

## Case Metadata

- shadow_case_id:
- pathway_id: `hypertension_adult_outpatient_review_only`
- pathway_version: `2026.1-draft`
- environment: `shadow`
- question_type:
- data_completeness:
- red_flag_screen_completed:
- red_flags_present:
- comorbidity_flags_no_pii:
- medication_context_no_pii:
- evidence_snapshot_id:
- blocked_reason:

## Required Result

Any red flag must stop the outpatient pathway. Any missing required input must return `WAITING_FOR_INPUT`.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
