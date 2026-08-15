# MVP-01 Acceptance Test

MVP-01: Hypertension and Type 2 Diabetes Follow-up Pathway.

## Acceptance checklist

1. [ ] Backend RBAC enforced on every API/server action.
2. [ ] Audit log append-only for normal UI.
3. [x] Seed data is fake.
4. [ ] Docker local one-command run verified after npm install/dependency lock.
5. [ ] Versioned database migration generated and tested.
6. [ ] Backup/restore guide exists and restore tested.
7. [ ] Care plan version history wired to write workflow.
8. [x] Task workflow model and UI exist.
9. [x] Overdue follow-up automation rule exists.
10. [ ] Rule review/approval workflow is executable.
11. [x] Doctor dashboard exists.
12. [x] Nurse dashboard exists.
13. [ ] A5 PDF generator exists and is tested.
14. [x] Offline test covers main structure.
15. [x] Offline test covers RBAC matrix.
16. [x] Offline test covers audit immutability policy.
17. [x] Offline test covers red flag safety copy.
18. [x] No e-prescribing or automatic treatment messaging.
19. [x] No real data.
20. [x] Installation documentation exists.

## Result

Not accepted for production. The slice is a working architectural and UI foundation, not a production clinical system.
