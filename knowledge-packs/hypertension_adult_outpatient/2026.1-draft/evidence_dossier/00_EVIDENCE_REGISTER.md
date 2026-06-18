# Phase 2D Evidence Register — Hypertension Adult Outpatient

Pack: `hypertension_adult_outpatient`
Version: `2026.1-draft`
Environment: `review`
Generated: `2026-06-18`

## Register Status

This register tracks draft claims from `10_evidence_manifest.json`. It does not certify clinical use.

| Claim ID | Evidence ID | Organization | Source type | Source URL | Verification | Approval | Release |
|---|---|---|---|---|---|---|---|
| `htn_claim_scope_and_diagnosis` | `ev_nice_ng136_2026` | NICE | guideline | https://www.nice.org.uk/guidance/ng136 | `SOURCE_UNAVAILABLE` | `pending` | blocked |
| `htn_claim_pharmacologic_framework` | `ev_who_htn_2021` | WHO | guideline | https://www.who.int/publications/i/item/9789240033986 | `SOURCE_UNAVAILABLE` | `pending` | blocked |
| `htn_claim_conflict_queue` | `ev_acc_aha_2025_hub` | ACC/AHA and partners | guideline_hub | https://www.acc.org/Guidelines/Hubs/High-Blood-Pressure | `SOURCE_UNAVAILABLE` | `pending` | blocked |

## Notes

- No claim is `VERIFIED`.
- No claim has physician/system owner approval for real-case shadow pilot.
- Two draft recommendation IDs in `05_recommendations.yaml` are not yet promoted into the manifest and remain draft-only: `htn_claim_lifestyle_and_risk`, `htn_claim_follow_up_monitoring`.
- Clinical release, prescribing, dose generation, EMR/HIS write, patient-facing output, and auto-apply remain not allowed.

Cần bác sĩ kiểm chứng trước khi áp dụng lâm sàng.
