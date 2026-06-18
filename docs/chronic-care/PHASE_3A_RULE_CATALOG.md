# Phase 3A Rule Catalog

## CC-001 Follow-up overdue

Creates `REVIEW_OVERDUE_CASE` task. No clinical decision. No patient-facing output.

## CC-002 Missing care-plan review

Creates `REQUEST_PHYSICIAN_REVIEW` task for stale pending draft.

## CC-003 Risk draft RED

Creates high-priority physician review task and dashboard alert. Does not decide emergency disposition.

## CC-004 Medication review due

Creates `MEDICATION_LIST_REVIEW` task. Does not change medication.

## CC-005 Post-discharge review flag

Creates `POST_DISCHARGE_REVIEW` task and requires physician review.

All rules are approved for test/shadow only and require risky feature flags to remain false.
