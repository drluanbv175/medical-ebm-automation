# R1.3 PROD-AUD-01 Architecture

**Document:** R1_3_PROD_AUD_01_ARCHITECTURE.md  
**Date:** 2026-06-28  
**Phase:** R1.3 — Audit Retention Architecture  
**Status:** ARCHITECTURE DESIGN — NOT IMPLEMENTED  
**Open action:** ACT-R1-01 (from GATE-R1.1 ACCEPT_WITH_ACTIONS)  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Context: PROD-AUD-01 requirement

PROD-AUD-01 was identified in R1.1 as a production gap: the offline harness produces a tamper-evident local JSONL ledger but does NOT provide:
- WORM-capable (Write-Once-Read-Many) storage
- Off-system backup
- Restore verification
- Legal hold

ACT-R1-01 requires PROD-AUD-01 to be designed and addressed in R1.3.

**Current classification:** `LOCAL_LEDGER_CLASSIFICATION = "TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM"`

---

## 1. Production audit trail architecture (design)

```
[Research OS — Audit Event Generator]
    │  (project_audit_attribution.py / future authenticated extension)
    │  fields: event_id, actor_id, session_id, action, timestamp_utc
    │           attribution_mode, previous_event_hash, audit_event_hash
    ▼
[Audit Event Bus] ← async queue (NOT IMPLEMENTED)
    │  Options: Kafka, Azure Service Bus, AWS SQS + SNS, RabbitMQ
    │  Guarantee: at-least-once delivery; idempotent consumer
    ▼
[WORM Retention Adapter] ← audit_retention_contract.py
    │  interface: WormRetentionProviderInterface
    │  writes each event to WORM-capable storage
    │  returns write_receipt (provider ID + timestamp + immutability claim)
    ▼
[WORM-capable Storage] ← EXTERNAL — NOT PROVIDED
    │  Options:
    │  • AWS S3 Object Lock (Compliance mode, 7-year minimum for medical)
    │  • Azure Blob Storage Immutability Policy
    │  • Google Cloud Storage Object Lock
    │  • On-premises WORM appliance (e.g., NetApp ONTAP SnapLock)
    ▼
[Off-system Backup] ← EXTERNAL — NOT PROVIDED
    │  Separate storage account/region from primary WORM store
    │  Independent access credentials
    ▼
[Restore Verification] ← see R1_3_BACKUP_RESTORE_VERIFICATION_PLAN.md
    │  Scheduled restore test (quarterly minimum)
    │  Hash verification of restored events against write_receipts
    ▼
[Retention Policy Enforcement] ← EXTERNAL — automated lifecycle rules
    │  Minimum retention: 7 years (Vietnamese medical record regulation)
    │  Legal hold: indefinite until released
    │  Deletion: only after retention period + explicit legal hold release
```

---

## 2. PROD-AUD-01 gap status

| Gap item | R1.1 status | R1.3 design | R1.3 implementation |
|----------|------------|-------------|-------------------|
| WORM storage | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |
| Off-system backup | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |
| Restore verification | NOT IMPLEMENTED | DESIGNED (plan) | NOT IMPLEMENTED |
| Legal hold | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |
| Retention enforcement | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |
| Audit event bus | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |
| Write receipt | NOT IMPLEMENTED | DESIGNED | NOT IMPLEMENTED |

**PROD-AUD-01 status after R1.3:** DESIGN COMPLETE — OPEN until external provider evidence exists

---

## 3. Replace-then-rehash residual risk (RR-02 / AC-11) — design treatment

R1.1 documented this as MEDIUM risk: attacker with filesystem write access can rebuild entire local JSONL with a fresh valid hash chain. This is inherent to local filesystem storage.

**R1.3 design treatment:**
- WORM storage makes replace-then-rehash impossible by design (object lock prevents overwrite)
- Write receipts from WORM provider are stored off-system
- Hash chain verification can be cross-checked against WORM provider manifest

**After R1.3 implementation:** RR-02 risk is ELIMINATED for the WORM-stored portion. Local simulation copy (for offline testing) retains MEDIUM risk and remains classified as `TAMPER_EVIDENT_LOCAL_SIMULATION_NOT_WORM`.

---

## 4. Retention period requirements

| Record type | Minimum retention | Source |
|------------|-----------------|--------|
| Research audit events | 7 years | Vietnamese Circular 44/2014/TT-BYT |
| Clinical audit events | 10 years | Vietnamese Circular 44/2014/TT-BYT |
| Ethics and consent records | 15 years (or life of study + 3) | ICH-GCP E6 |
| Adverse event records | 15 years | ICH-GCP E6 |

---

## 5. Open dependencies

| Dependency | Status |
|-----------|--------|
| WORM storage provider (AWS/Azure/GCP/on-prem) | EXTERNAL — NOT PROVIDED |
| Audit event bus | EXTERNAL — NOT PROVIDED |
| Off-system backup infrastructure | EXTERNAL — NOT PROVIDED |
| Legal hold management system | EXTERNAL — NOT PROVIDED |
| Restore verification tooling | NOT IMPLEMENTED |

---

## Conclusion

```
Production WORM retention: DESIGN — NOT IMPLEMENTED
PROD-AUD-01: OPEN until external provider evidence exists
ACT-R1-01: OPEN — target R1.3 implementation (requires external provider)
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
