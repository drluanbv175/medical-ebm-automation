# Incident Response Playbook

## Triage

1. Record incident time, reporter, affected module and suspected data scope.
2. Disable affected account/session if access compromise is suspected.
3. Preserve audit logs and application logs.
4. Notify data protection owner and clinical safety owner.

## Containment

- Disable affected automation rule if clinical safety risk exists.
- Disable external communication gateway if message leakage is suspected.
- Rotate secrets if credential exposure is possible.

## Investigation

- Review audit log.
- Identify organization/site and patients affected.
- Check whether PHI left the approved environment.
- Check whether unapproved clinical content/rule was used.

## Recovery

- Restore from verified backup if data integrity is affected.
- Document corrective actions.
- Require signoff before re-enabling affected workflow.

## Do not

- Do not delete clinical records.
- Do not edit audit logs through normal UI.
- Do not send patient-facing explanations until approved by responsible leadership.
