# R-GOV.1 Hospital Information Security and Incident Plan

**Document:** R_GOV_1_HOSPITAL_INFORMATION_SECURITY_AND_INCIDENT_PLAN.md  
**Date:** 2026-06-28  
**Decision ID:** HOSP-GOV-01  
**Status:** READY_FOR_EXTERNAL_REVIEW  
**Qualification:** NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE

---

> **MANDATORY STATEMENT:**  
> This is a preparation dossier — not hospital authorization.  
> Information security controls must be reviewed and approved  
> by the hospital IT Security Officer before any data access commences.

---

## Part 1 — Current security posture (HONEST DISCLOSURE)

| Control | Current status | Risk |
|---------|---------------|------|
| SSO / institutional identity | NOT IMPLEMENTED | HIGH — no verified identity |
| Multi-factor authentication | NOT IMPLEMENTED | HIGH |
| Production RBAC | NOT IMPLEMENTED | HIGH |
| WORM-capable audit trail | NOT IMPLEMENTED (PROD-AUD-01 OPEN) | MEDIUM |
| Encryption at rest | NOT CONFIRMED | HIGH |
| Encryption in transit | NOT CONFIRMED | HIGH |
| Certified security management (ISO 27001) | NOT CERTIFIED | MEDIUM |
| Independent security penetration test | NOT CONDUCTED (ACT-R1-05) | HIGH |
| Data Loss Prevention (DLP) | NOT IMPLEMENTED | MEDIUM |

**Assessment: Current security posture does NOT meet the requirements for real patient data access.**  
**All controls above must be confirmed BEFORE eHospital data access is granted.**

---

## Part 2 — Planned security controls (to be implemented before data access)

| Control | Planned solution | Responsible | Target milestone |
|---------|----------------|-------------|----------------|
| Identity verification | Institutional SSO (SAML 2.0 or OIDC) — ACT-R1-03 | Hospital IT + PI | R1.3 |
| MFA | Institutional MFA enforcement — ACT-R1-03 | Hospital IT + PI | R1.3 |
| RBAC | Production RBAC service — R1.3 phase | PI (system design) | R1.3 |
| Audit trail | WORM-capable storage — ACT-R1-01/ACT-R1-04 | PI | R1.3 |
| Encryption at rest | OS-level full-disk encryption; application-level encryption for research dataset | PI + Hospital IT | Before data access |
| Encryption in transit | TLS 1.2+ for all data transfer; VPN for institutional network | Hospital IT | Before data access |
| Penetration test | External independent security test — ACT-R1-05 | PI (engage external tester) | R1.5 |
| DLP | Endpoint DLP per hospital policy | Hospital IT | Before data access |
| Network segmentation | Research workstation on separate VLAN or institutional research network | Hospital IT | Before data access |

---

## Part 3 — Data breach incident response plan (design)

### 3.1 Incident categories

| Category | Description | Severity |
|---------|------------|---------|
| Cat-1 | Loss or theft of device containing pseudonymized data | HIGH |
| Cat-2 | Unauthorized access to research OS or dataset | HIGH |
| Cat-3 | Accidental disclosure of pseudonymized data | MEDIUM |
| Cat-4 | Re-identification risk identified | HIGH |
| Cat-5 | Audit trail tampering detected | HIGH |
| Cat-6 | Ransomware or malware on research workstation | HIGH |

### 3.2 Incident response steps

| Step | Action | Responsible | Timeline |
|------|--------|------------|---------|
| 1 | Detect — identify and confirm incident | Any team member | Immediately on discovery |
| 2 | Contain — isolate affected system (disconnect from network) | PI + Hospital IT | Within 1 hour |
| 3 | Report — notify PI, Hospital IT Security Officer, and Data Owner | Team member who detected | Within 2 hours |
| 4 | Assess — determine nature and scope of breach | PI + Hospital IT | Within 24 hours |
| 5 | Notify authorities — report to competent authority per Decree 13/2023 | PI + Legal | Within 72 hours (if personal data breach) |
| 6 | Notify ethics committee | PI | Per ethics committee protocol |
| 7 | Remediate — implement corrective actions | PI + Hospital IT | Within 5 business days |
| 8 | Document — incident report written and archived | PI | Within 14 days |
| 9 | Review — post-incident review and protocol update | PI + Hospital IT | Within 30 days |

### 3.3 Notification contacts

| Role | Contact | To be completed |
|------|---------|----------------|
| Hospital IT Security Officer | [TO BE CONFIRMED BY PI] | — |
| Data Owner / HIS administrator | [TO BE CONFIRMED BY PI] | — |
| Data Protection Officer | [TO BE CONFIRMED BY PI] | — |
| Ethics committee | [TO BE CONFIRMED BY PI] | — |
| Competent authority (Decree 13/2023) | [Ministry of Public Security — TO BE CONFIRMED WITH LEGAL] | — |
| Research Management Office | [TO BE CONFIRMED BY PI] | — |

---

## Part 4 — Acceptable use policy (research workstation)

| Policy | Requirement |
|--------|------------|
| Authorized users only | Only persons on delegation log may access research OS |
| No personal use on research workstation | Research workstation used only for study purposes |
| No unauthorized software | Only approved software installed |
| No sharing of credentials | Individual accounts required (MFA when implemented) |
| No storage of pseudonymized data on personal devices | Data only on approved institutional or encrypted devices |
| No printing of research data | Unless formally approved |
| Lock screen when unattended | Enforced or manual |
| Report security incidents | Within 2 hours of discovery |

---

## Part 5 — Security review sign-off template (hospital IT to complete)

| Field | Hospital IT to complete |
|-------|------------------------|
| Review date | [DATE] |
| Reviewer name and title | [NAME, TITLE] |
| Review scope | Software use approval, network clearance, storage arrangement |
| Findings | [FINDINGS] |
| Conditions for approval | [CONDITIONS] |
| Approved / Conditional / Rejected | [DECISION] |
| Signature | [SIGNATURE] |

> Current status: NOT YET REVIEWED — READY_FOR_EXTERNAL_REVIEW

---

*Qualification: NO-GO — NOT QUALIFIED FOR RESEARCH WORKFLOW USE*  
*All outputs are DRAFT — REQUIRE HUMAN REVIEW.*
