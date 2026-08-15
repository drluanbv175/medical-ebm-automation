# Phase 3A Data Dictionary

## ChronicCareEnrollment

Synthetic enrollment into one program label. `patient_reference_id` must start with `SYN-`.

## ChronicCareReview

Shadow review item: initial, follow-up, overdue, medication, lab, care-plan or risk review.

## ChronicCareRiskDraft

Draft operational risk label: GREEN, YELLOW, RED, UNASSESSED. RED only means priority physician review in shadow mode.

## ChronicCareTask

Operational task for nurse/care coordinator/physician/pharmacist. No medication change or treatment instruction.

## ChronicCarePlanDraft

Draft shell for shadow review. Status can be `APPROVED_FOR_SHADOW`, never active clinical plan.

## ChronicCareTimelineEvent

Non-PII timeline event for synthetic enrollment.

## ChronicCareQualityMetric

Aggregate de-identified metric, generated from synthetic dataset.
