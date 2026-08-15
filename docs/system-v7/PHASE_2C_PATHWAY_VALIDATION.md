# Phase 2C Pathway Validation

Ngày: 2026-06-18.

## Modules

- `app/clinical_content/pilot_pathway_builder.py`
- `app/clinical_content/pilot_pathway_validator.py`
- `app/clinical_content/pilot_pathway_release_gate.py`
- `app/clinical_content/hypertension_pilot_pathway_builder.py`
- `app/clinical_content/hypertension_pilot_pathway_validator.py`
- `app/clinical_content/hypertension_pilot_pathway_release_gate.py`
- `app/evidence/hypertension_local_adaptation.py`

## Result

Focused tests PASS:

- Default `selected_pack=null` blocks real-pack build.
- Approved synthetic selection can build a review-only pathway.
- Current `hypertension_adult_outpatient` selection is `pending` and blocks real-pack shadow pilot.
- Hypertension draft pack has all 13 required artifacts.
- Hypertension manifest claims contain required traceability fields and remain release-blocked while `SOURCE_UNAVAILABLE`.
- Validator requires entry criteria, inputs, sufficiency rules, red flags, hard stops, decision nodes, claim links, medication safety, follow-up/referral rules, and physician review.
- Release gate always blocks clinical release in Phase 2C.
- Local adaptation marks medicine availability, monitoring, lab testing, outpatient feasibility, renal monitoring, pregnancy/reproductive status, local constraints, referral, and internal policy as needing local review without changing original certainty or guideline meaning.

## Safety gates

- Missing input -> `WAITING_FOR_INPUT`.
- Red flag -> stop outpatient pathway and referral.
- Evidence not verified or needing physician review -> no release.
- Missing approval record -> review-only.
- Medication-related recommendation -> medication safety required.
- Pathway cannot create prescription.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
