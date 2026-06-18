# Phase 3A Scope Boundary

## Được phép

- Synthetic patient registry.
- Synthetic chronic-care enrollment.
- Synthetic care coordination tasks.
- Synthetic follow-up timeline.
- Draft risk assessment.
- Draft care-plan shell.
- Read-only chronic-care dashboard.
- Approval workflow.
- Audit events.
- Quality metrics trên synthetic dataset.
- Export aggregate de-identified statistics.

## Không được phép

- Clinical production.
- Patient-facing messaging.
- Patient education export.
- PDF lời dặn người bệnh thật.
- Prescription workflow.
- Medication change workflow.
- Dose adjustment.
- EMR/HIS write-back.
- Auto-apply pathway.
- Auto-triage quyết định cuối cùng.
- Auto-referral.
- Real patient data.
- External AI call với dữ liệu định danh.

## Program labels

Phase 3A chỉ dùng label vận hành: `HTN_PROGRAM`, `T2D_PROGRAM`, `DYSLIPIDEMIA_PROGRAM`, `CARDIOMETABOLIC_RISK_PROGRAM`, `POLYPHARMACY_REVIEW_PROGRAM`, `POST_DISCHARGE_REVIEW_PROGRAM`.

Các label này không phải guideline và không sinh khuyến cáo điều trị.
