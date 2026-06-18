# Integration Strategy

## EMR / Clinical record

Chronic Care Clinic OS khong thay the EMR. Huong tich hop la doc/nhap du lieu duoc phep tu EMR hoac HIS, sau do tao coordination record rieng co audit.

## FHIR-ready path

Tuong lai co the them FHIR API layer cho:

- Patient.
- Appointment.
- Observation.
- MedicationStatement.
- CarePlan.
- Task.
- ServiceRequest/Referral.

## Communication gateways

SMS/Zalo/email chi duoc bat khi:

- Template duoc duyet.
- Consent hop le.
- Message khong chua dieu tri ca the hoa chua duyet.
- Co audit va delivery log.

## AI integration

AI disabled by default, sandbox only luc dau, khong gui PII len public AI API. Moi output AI la draft va can human review.
