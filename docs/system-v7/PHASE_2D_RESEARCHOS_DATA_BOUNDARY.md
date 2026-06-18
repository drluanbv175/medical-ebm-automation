# Phase 2D ResearchOS Data Boundary

## Allowed

- Protocol title and objectives.
- Study design metadata.
- Outcome names.
- Variable names without patient values.
- Questionnaire item IDs without responses.
- Data dictionary schema.
- SAP metadata and lock status.
- Syntax version metadata.
- Expected table shells.
- Reporting checklist status.
- Data quality summary without PII or row-level data.

## Not Allowed

- Raw dataset.
- Patient names, DOB, phone, address, MRN, exact visit date.
- Individual questionnaire responses.
- SPSS/Stata/SAS/Excel files containing row-level patient data.
- Any export that includes restricted/raw dataset.

## Current Boundary Decision

ResearchOS remains metadata-only and not analysis-ready.

Cần bác sĩ/PI kiểm chứng trước khi áp dụng nghiên cứu.
