# Data Retention And Archive Policy

Status: repository control contract, not final clinic/legal approval.

## Scope

This policy covers Chronic Care Clinic OS records including patient identity/contact data, care-plan versions, audit logs, AI draft metadata, quality metrics and patient handouts. It is intended to prevent uncontrolled deletion, indefinite ambiguous retention and unreviewed exports.

## Core Rules

- Direct delete is not allowed for patient records, identifiers, contacts, care-plan versions, patient handouts or audit logs.
- Audit logs and approved care-plan versions are immutable records and must be retained according to the approved retention schedule.
- Legal hold blocks archive, de-identification and delete plans.
- Active clinical episodes block archive or de-identification plans.
- Aggregate export may proceed only when the export is de-identified and reviewed.
- Any retention action requires data-protection review, an artifact reference, a legal-hold check and an append-only audit record.

## Repository Contract

The executable contract is `lib/data-retention.ts`. It defines minimum retention years, allowed post-retention actions and fail-closed decisions for legal hold, active care, direct delete and missing review evidence.

## Production Boundary

This repository policy does not itself authorize production archive/delete jobs. Real use requires clinic/legal approval, data protection sign-off, verified backup/restore, and an auditable execution log.

Cần bác sĩ kiểm chứng.
