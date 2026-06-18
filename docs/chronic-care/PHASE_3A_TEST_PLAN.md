# Phase 3A Test Plan

## Functional

- Create synthetic enrollment.
- Create follow-up review.
- Create overdue task.
- Complete task.
- Escalate overdue task.
- Create risk draft.
- Physician approve/reject risk draft.
- Create care-plan draft.
- Block care-plan approval if evidence missing.
- Approve care-plan for shadow if all gates pass.
- Generate quality metrics.
- Render dashboard state.
- Export de-identified aggregate data.

## Safety

- No real PII accepted in synthetic seed.
- No patient-facing message generated.
- No patient education export.
- No medication change/prescription/EMR write action.
- No auto-apply pathway.
- No production flag activation.
- No approval bypass.
- No audit event omission.
- No evidence spoofing.

## Red-team

- Prompt injection in synthetic note.
- PII-like synthetic case.
- Attempt to enable risky flag via dashboard.
- Attempt to approve without physician role.
- Attempt to export non-deidentified dataset.
- Fake citation/claim ID bypass attempts.
