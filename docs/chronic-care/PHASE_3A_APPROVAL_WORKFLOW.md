# Phase 3A Approval Workflow

## Risk draft

Risk draft `RED` or `YELLOW` requires physician review. Approval changes only shadow workflow status.

## Care-plan draft

Care-plan draft approval is blocked if claim/evidence references are missing or unverified. Approved status is `APPROVED_FOR_SHADOW`.

## Audit

Create/review/approve/reject actions must write audit events with actor, action, entity, environment, run_id, state hashes and approval reference.
