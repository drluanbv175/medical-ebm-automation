# V4.3.4 Review Routing Matrix

**Version:** 4.3.4  
**Date:** 2026-06-28  
**Status:** DRAFT — REQUIRE HUMAN REVIEW

---

## Ma trận định tuyến (19 ArtifactID → Role + Risk + Gate)

| Artifact | Primary Role(s) | Mandatory Focus | Risk | Gate |
|----------|----------------|-----------------|------|------|
| `00_RESEARCH_CHARTER` | PI_PROJECT_OWNER | objectives, outcomes, feasibility | HIGH | D-R1 |
| `01_RESEARCH_QUESTION_AND_PICO` | PI_PROJECT_OWNER | objectives, outcomes, feasibility | HIGH | D-R2 |
| `02_PROTOCOL_DRAFT` | PI_PROJECT_OWNER, METHODS_STATISTICS_REVIEWER | design, population, bias, ethics readiness | **CRITICAL** | D-R4 |
| `03_EVIDENCE_PLAN` | EVIDENCE_CITATION_REVIEWER | evidence status, verification, retraction | HIGH | D-R8 |
| `04_METHODS_AND_SAMPLE_SIZE_ASSUMPTIONS` | METHODS_STATISTICS_REVIEWER | assumptions, confounding, missing data | **CRITICAL** | D-R15 |
| `05_CRF_DRAFT` | DATA_GOVERNANCE_QA_REVIEWER | variables, coding, validation, provenance | HIGH | D-R5 |
| `06_DATA_DICTIONARY` | DATA_GOVERNANCE_QA_REVIEWER | variables, coding, validation, provenance | HIGH | D-R5 |
| `07_STATISTICAL_ANALYSIS_PLAN_DRAFT` | METHODS_STATISTICS_REVIEWER | outcome-analysis consistency | **CRITICAL** | D-R6 |
| `08_TABLE_AND_FIGURE_SHELLS` | METHODS_STATISTICS_REVIEWER | outcome-analysis consistency | MEDIUM | D-R7 |
| `09_SYNTHETIC_ANALYSIS_READINESS` | METHODS_STATISTICS_REVIEWER | synthetic data readiness, no real data | MEDIUM | D-R9 |
| `10_REPORTING_CHECKLIST_DRAFT` | PI_PROJECT_OWNER, EVIDENCE_CITATION_REVIEWER | reporting standard, citations | HIGH | D-R11 |
| `11_MANUSCRIPT_OUTLINE_DRAFT` | PI_PROJECT_OWNER | outline completeness, draft-only status | MEDIUM | D-R11 |
| `12_GOVERNANCE_AND_CAPA_PACK` | DATA_GOVERNANCE_QA_REVIEWER | traceability, change control, audit | HIGH | D-R12 |
| `13_REVIEW_PACK` | PI_PROJECT_OWNER | unresolved decisions and next action | HIGH | D-R14 |
| `14_PROJECT_TRACEABILITY_MATRIX` | DATA_GOVERNANCE_QA_REVIEWER | traceability completeness | MEDIUM | D-R14 |
| `15_PROJECT_QA_REPORT` | PI_PROJECT_OWNER | gate results, outstanding WARN/FAIL | HIGH | D-R1 |
| `16_CHANGE_IMPACT_REPORT` | PI_PROJECT_OWNER | stale artifacts, propagation | MEDIUM | D-R12 |
| `17_DECISION_REGISTER` | PI_PROJECT_OWNER | decision completeness, outstanding items | MEDIUM | D-R12 |
| `18_VERSION_REGISTER` | DATA_GOVERNANCE_QA_REVIEWER | version sequence, no overwrite | LOW | D-R12 |

---

## Phân bổ theo risk level

| Risk | Artifacts |
|------|-----------|
| CRITICAL | `02_PROTOCOL_DRAFT`, `04_METHODS_AND_SAMPLE_SIZE`, `07_SAP_DRAFT` (3) |
| HIGH | `00`, `01`, `03`, `05`, `06`, `10`, `12`, `13`, `15` (9) |
| MEDIUM | `08`, `09`, `11`, `14`, `16`, `17` (6) |
| LOW | `18` (1) |

---

## Phân bổ theo role

| Role | Artifacts |
|------|-----------|
| PI_PROJECT_OWNER | `00`, `01`, `02*`, `10*`, `11`, `13`, `15`, `16`, `17` |
| METHODS_STATISTICS_REVIEWER | `02*`, `04`, `07`, `08`, `09` |
| EVIDENCE_CITATION_REVIEWER | `03`, `10*` |
| DATA_GOVERNANCE_QA_REVIEWER | `05`, `06`, `12`, `14`, `18` |

_*Artifact có nhiều reviewer._

---

## Nguyên tắc routing

1. **CRITICAL artifacts** cần PI_PROJECT_OWNER và/hoặc METHODS_STATISTICS_REVIEWER.
2. **Evidence artifacts** bắt buộc EVIDENCE_CITATION_REVIEWER để tránh fabricated citations.
3. **Data/governance artifacts** bắt buộc DATA_GOVERNANCE_QA_REVIEWER để đảm bảo ALCOA+.
4. Routing không tự approve — chỉ chỉ định ai cần review, không thay thế quyết định người thật.

---

*Cần bác sĩ / PI kiểm chứng. Đây là bản DRAFT tự động — KHÔNG thực thi thật.*
