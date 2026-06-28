# R1.2 RBAC Persistence Design

**Document:** R1_2_RBAC_PERSISTENCE_DESIGN.md  
**Date:** 2026-06-28  
**Phase:** R1.2 — Design Only  
**Status:** DESIGN ONLY — NOT IMPLEMENTED  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

## Purpose

Design the persistence layer for RBAC policy data (roles, permissions, delegations, SoD rules) for production deployment. The current offline harness holds all data in Python data structures. This document defines the production schema design.

---

## 1. Current state (R1.1.x offline harness)

```
Role registry:        Python dict in project_rbac_simulation.py
Permission matrix:    Python dict constant
Delegation registry:  In-memory DelegationRegistry class
SoD rules:           Python enum + set constants
Audit ledger:        Local JSONL file
```

**Status:** In-memory / local file. Not persistent across process restarts in production sense.

---

## 2. Production RBAC persistence schema design

### 2.1 Role table (design)

| Column | Type | Constraint |
|--------|------|------------|
| role_id | UUID | PRIMARY KEY |
| role_name | VARCHAR(100) | UNIQUE; matches R1.1 role name |
| role_level | INTEGER | 1–5; governs SoD authority |
| is_active | BOOLEAN | Default TRUE |
| created_at_utc | TIMESTAMP | NOT NULL |
| created_by_actor_id | VARCHAR | FK to actor; NOT NULL |
| last_modified_utc | TIMESTAMP | |

### 2.2 Permission matrix table (design)

| Column | Type | Constraint |
|--------|------|------------|
| permission_id | UUID | PRIMARY KEY |
| role_id | UUID | FK → role table |
| action_name | VARCHAR(200) | Matches R1.1 action constants |
| resource_type | VARCHAR(100) | |
| is_permitted | BOOLEAN | NOT NULL |
| effective_from_utc | TIMESTAMP | |
| effective_until_utc | TIMESTAMP | NULL = no expiry |

### 2.3 Delegation table (design)

| Column | Type | Constraint |
|--------|------|------------|
| delegation_id | UUID | PRIMARY KEY |
| delegator_actor_id | VARCHAR | NOT NULL |
| delegatee_actor_id | VARCHAR | NOT NULL |
| delegated_role | VARCHAR(100) | FK → role table |
| scope_constraint | JSONB | Actions or objects permitted |
| status | ENUM | PROPOSED/ACTIVE/EXPIRED/REVOKED/REJECTED |
| reason_code | VARCHAR | DelegationReasonCode |
| effective_from_utc | TIMESTAMP | NOT NULL |
| effective_until_utc | TIMESTAMP | NOT NULL |
| created_at_utc | TIMESTAMP | NOT NULL |
| revoked_at_utc | TIMESTAMP | NULL if not revoked |

### 2.4 SoD rules table (design)

| Column | Type | Constraint |
|--------|------|------------|
| sod_rule_id | UUID | PRIMARY KEY |
| rule_name | VARCHAR(200) | |
| action_a | VARCHAR(200) | Action that triggers check |
| role_constraint | JSONB | Roles that cannot hold action_a simultaneously |
| guard_type | VARCHAR | ROLE_LEVEL / FORBIDDEN_PAIR / EXPIRY |
| is_active | BOOLEAN | |

---

## 3. Migration from offline harness

The R1.1.x Python constants serve as the authoritative source for seeding the production schema:

| Source (R1.1.x) | Target (production) |
|----------------|-------------------|
| `_ROLES` dict | role table (initial seed) |
| `_ACTIONS` + permission matrix | permission matrix table |
| `DelegationRegistry` in-memory | delegation table |
| `SoDViolation` enum | SoD rules table |

Migration tooling: NOT IMPLEMENTED. Required before R1.3 production RBAC service.

---

## 4. Access pattern requirements

| Operation | SLA target (design) | Caching |
|-----------|-------------------|---------|
| Permission check (allow/deny) | < 50ms | Role permission cache, TTL 60s |
| Delegation status lookup | < 30ms | Per-session cache |
| SoD guard evaluation | < 20ms | In-process constant evaluation |
| Audit event write | < 200ms | Async queue; immediate return |

---

## 5. Open dependencies

| Dependency | Status |
|-----------|--------|
| Production database (PostgreSQL / managed) | EXTERNAL — NOT PROVIDED |
| Database hosting | EXTERNAL — NOT PROVIDED |
| Database credentials management | EXTERNAL — NOT PROVIDED |
| ORM / connection pooling layer | NOT IMPLEMENTED |
| Schema migration tooling | NOT IMPLEMENTED |

---

## Conclusion

```
RBAC persistence design: COMPLETE
Production RBAC persistence: NOT IMPLEMENTED
Target: R1.3
```

*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*  
*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*
