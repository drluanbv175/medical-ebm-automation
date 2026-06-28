# R1.3 WORM Solution Design

**Document:** R1_3_WORM_SOLUTION_DESIGN.md  
**Date:** 2026-06-28  
**Phase:** R1.3 — Audit Retention Architecture  
**Status:** DESIGN ONLY — NO PROVIDER SELECTED OR CONNECTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Compare WORM-capable storage options and provide a decision framework for Dr Luân and institutional IT. No provider has been selected. This document is a design input, not a procurement decision.

---

## 1. Provider comparison

| Provider | Type | Min retention | Object lock | Legal hold | Compliance mode | Cost model |
|---------|------|--------------|------------|-----------|----------------|-----------|
| AWS S3 Object Lock | Cloud managed | Configurable | YES | YES | YES (Compliance) | Per GB/month |
| Azure Blob Immutable Storage | Cloud managed | Configurable | YES | YES | YES (Regulatory compliance) | Per GB/month |
| Google Cloud Storage WORM | Cloud managed | Configurable | YES | YES | YES (Retention policy) | Per GB/month |
| NetApp ONTAP SnapLock | On-premises | Configurable | YES | YES | YES | CapEx + support |
| Dell EMC DataDomain | On-premises | Configurable | YES | YES | YES | CapEx + support |

**Recommendation framework:** Cloud managed WORM (AWS/Azure/GCP) preferred for a small research operation unless institutional policy requires on-premises data residency.

---

## 2. Required WORM provider capabilities

A compliant WORM provider for PROD-AUD-01 must satisfy ALL of:

| Capability | Requirement |
|-----------|-------------|
| Object immutability | Once written, object cannot be modified or deleted until retention period expires |
| Compliance mode | Even account owner/admin CANNOT delete objects before retention expires |
| Legal hold | Indefinite hold independent of retention period |
| Write receipt | Provider returns a receipt confirming write with provider timestamp |
| Audit log of access | Provider logs every read/write/delete attempt |
| Encryption at rest | AES-256 minimum |
| Encryption in transit | TLS 1.2 minimum |
| Cross-region backup | Replication to second region or backup account |
| SLA | 99.9% durability minimum (11 nines preferred: 99.999999999%) |

---

## 3. Vietnamese medical data residency consideration

| Consideration | Design guidance |
|--------------|----------------|
| Data residency | Prefer provider with Vietnamese or APAC region data center |
| Regulatory reference | Circular 44/2014/TT-BYT; Decree 13/2023/ND-CP (personal data) |
| Export controls | Audit events containing actor_id (pseudonymous) may be stored abroad if no PII; legal review required |

**Design decision:** Pseudonymized actor_id (no PII) should be acceptable for cloud WORM. Legal review by institutional counsel required before production use.

---

## 4. Integration architecture (design)

```python
# Interface: WormRetentionProviderInterface (see audit_retention_contract.py)
provider = WormRetentionProviderInterface(...)
receipt = provider.write_event(audit_event_dict)
# receipt contains: provider_id, provider_timestamp, immutability_expiry, etag
```

The `WormRetentionProviderInterface` defines the adapter contract. Concrete implementations (one per provider) implement this interface. The Research OS never calls cloud provider APIs directly — always through the adapter.

**Implementation status:** Fake adapter in `audit_retention_contract.py` for offline tests. Real adapter: NOT IMPLEMENTED.

---

## 5. Decision gate

PROD-AUD-01 cannot be closed until:
1. Provider is selected by Dr Luân and institutional IT
2. Contract/service agreement is signed
3. Retention adapter is implemented for that provider
4. Integration tests pass against the real provider
5. Restore verification test is run and documented

**None of these steps are completed in R1.3.** R1.3 produces design only.

---

## Conclusion

```
WORM solution design: COMPLETE
Provider selected: NO
WORM adapter implemented: NO (fake only)
PROD-AUD-01: OPEN until real provider connected and verified
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
