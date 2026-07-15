# Patient Communication Policy

Status: repository control contract, not clinic-approved production policy.

## Scope

This policy applies to patient-facing communication generated or coordinated by Chronic Care Clinic OS. It covers printed A5 handouts, portal messages and staff call tasks. It does not authorize diagnosis, prescription, medication changes, emergency triage or direct treatment instructions.

## Release Rules

- Communication is allowed only when the message type is on the allow-list, an approved template exists, patient consent is present and a physician has approved the release package.
- Red flags block patient communication. The workflow must route to direct physician review and advise care at the nearest medical facility when urgent assessment is needed.
- Messages must not contain new treatment instructions, dose changes, diagnosis assertions or AI-generated advice that has not been approved by a physician.
- SMS is blocked in the current contract because identity, consent, delivery failure handling and privacy controls have not been operationally validated.
- Every released communication requires an audit entry with PHI/PII redaction before persistence.

## Operational Boundary

This repository policy is a technical guardrail. Real use still requires clinic approval, staff training, UAT with de-identified workflow data, privacy review and clinical safety sign-off.

Cần bác sĩ kiểm chứng.
