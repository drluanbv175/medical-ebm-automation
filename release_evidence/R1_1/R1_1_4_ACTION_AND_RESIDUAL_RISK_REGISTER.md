# R1.1.4 Action and Residual Risk Register

**Document:** R1_1_4_ACTION_AND_RESIDUAL_RISK_REGISTER.md  
**Date:** 2026-06-28  
**Phase:** R1.1.4 — Phase D  
**Decision ID:** VL-GATE-R1.1-2026-002  
**Gate:** GATE-R1.1 = ACCEPTED_WITH_ACTIONS  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> Actions in this register are **gate-blocking**: GATE-R1.1 transitions from  
> ACCEPTED_WITH_ACTIONS to PASS only after all OPEN actions are marked COMPLETE  
> and Dr Luân re-confirms by 2026-09-30.

---

## Section 1 — Action Register

| action_id | source_decision | risk_or_dependency | owner_reference | due_date | status | closure_evidence_required | production_blocking_effect |
|-----------|----------------|-------------------|----------------|----------|--------|--------------------------|---------------------------|
| ACT-R1-01 | VL-GATE-R1.1-2026-002 Human Action 1 | PROD-AUD-01: production WORM retention not implemented; local ledger is not an audit trail | Dr Luân | R1.3 qualification | **OPEN** | R1.3 implements and verifies WORM-capable retention; PROD-AUD-01 marked CLOSED with evidence | Blocks all production audit readiness claims; blocks any claim that R1.3 audit trail is compliant |
| ACT-R1-02 | VL-GATE-R1.1-2026-002 Human Action 2 | Truthfulness: local hash-chain must not be described as WORM, immutable storage, or production audit trail | Dr Luân | Ongoing | **OPEN** | All downstream R1.2 and R1.3 documents verified to use only "tamper-evident local simulation" label; no WORM/immutable claim found | Blocks any document that mislabels local ledger as production-grade |
| ACT-R1-03 | VL-GATE-R1.1-2026-002 Human Action 3 | R1.2 scope boundary: no SSO, MFA, real data, eHospital, production EDC | Dr Luân | R1.2 completion | **OPEN** | R1.2 gate review confirms all work products are design documents only; no real systems connected | Blocks R1.2 from implementing any production identity or data system |
| ACT-R1-04 | Spec ACT-R1-05 | R1.3 must address WORM retention, off-system backup, restore verification, replace-then-rehash residual risk | Dr Luân | R1.3 qualification | **OPEN** | R1.3 provides: (a) WORM-capable storage solution, (b) off-system backup verification, (c) restore test evidence, (d) replace-then-rehash mitigation design | Blocks R1.3 from claiming production audit readiness without WORM solution |
| ACT-R1-05 | Spec — IQ-20 | Independent security pentest (IQ-20) not yet conducted | Dr Luân | R1.5 | **OPEN** | External tester engaged; pentest report issued; findings remediated | Blocks independent security certification claim; does not block R1.2–R1.4 design work |

---

## Section 2 — Residual Risk Register

| risk_id | description | level | accepted_by | date_accepted | target_milestone | closure_condition |
|---------|-------------|-------|-------------|--------------|-----------------|-------------------|
| RR-02 / AC-11 | Replace-then-rehash: attacker with filesystem write access can rebuild entire JSONL with fresh valid hash chain; verify_hash_chain() passes because new chain is internally consistent | MEDIUM | Dr Luân (VL-GATE-R1.1-2026-002) | 2026-06-28 | R1.3 (PROD-AUD-01) | WORM-capable storage prevents file replacement; requires ACT-R1-01 and ACT-R1-04 |
| PROD-AUD-01 | Production WORM retention not implemented; local JSONL is NOT an audit trail suitable for production | — | Dr Luân (VL-GATE-R1.1-2026-002) | 2026-06-28 | R1.3 | ACT-R1-01 closed with verified WORM solution |
| PROD-RBAC-01 | Production RBAC enforcement service not implemented; R1.1 is a test harness only | — | Dr Luân (VL-GATE-R1.1-2026-002) | 2026-06-28 | R1.3 | R1.3 deploys production RBAC service; GATE-R1.3 passed |
| IQ-20 | Independent security pentest not conducted; no external adversarial assessment of policy engine, audit ledger, or delegation controls | — | Dr Luân (VL-GATE-R1.1-2026-002) | 2026-06-28 | R1.5 | External pentest completed; findings remediated; report archived |

---

## Section 3 — Closure protocol

To close an action and update its status:

1. Human (Dr Luân or designated successor) provides written confirmation that closure evidence has been produced and verified.
2. Claude Code updates `status` field to `COMPLETE` and records closure date and evidence reference.
3. After ALL actions marked COMPLETE, Dr Luân re-confirms that GATE-R1.1 may transition to PASS.
4. Claude Code updates `R1_1_4_GATE_R1_1_STATUS_UPDATE.md` → GATE-R1.1: PASS.

**Claude Code must not mark any action COMPLETE without explicit human instruction and evidence reference.**

---

## Section 4 — Invariants that actions cannot close prematurely

The following remain true regardless of action status:

| Item | Invariant |
|------|-----------|
| SSO | NOT IMPLEMENTED — cannot be closed by documentation action |
| MFA | NOT IMPLEMENTED — cannot be closed by documentation action |
| Authenticated identity | NOT IMPLEMENTED |
| Ethics/IRB approval | NOT IMPLEMENTED |
| Real research execution | BLOCKED until GATE-R1, GATE-R2, GATE-R3 all pass |
| Independent review | NOT ESTABLISHED — self-review only |
| Qualification | NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE |

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
