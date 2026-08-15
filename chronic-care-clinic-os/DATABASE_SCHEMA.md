# Database Schema

Nguon schema executable nam tai `prisma/schema.prisma`.

## Core entities

- Organization, ClinicSite, User, Role, Permission, UserRole, Session.
- Patient.
- PatientConsent, PatientIdentifier, PatientContact.
- CareProgramEnrollment, CareRiskAssessment.
- ChronicCondition.
- Medication.
- MedicationReconciliation.
- VitalSign.
- LaboratoryResult.
- LaboratoryReview.
- Appointment.
- VisitNote.
- CarePlan.
- CarePlanVersion.
- CareGoal.
- CareCoordinationTask.
- TaskEscalation.
- CommunicationLog.
- Referral.
- QualityMetric.
- QualityMetricDefinition.
- AuditLog.
- ClinicalRule, ClinicalRuleVersion, ClinicalRuleApproval.
- AutomationRule.
- SafetyAlert, SafetyAlertReview.
- IncidentReport, IncidentReview.
- ClinicalContent, ClinicalContentVersion, ClinicalContentApproval.
- EducationMaterial, EducationMaterialApproval.
- PatientHandout.
- AIDraft.
- VersionHistory.
- SystemSetting.

## Nguyen tac du lieu

- Moi entity lam sang co `createdAt`, `updatedAt` khi phu hop.
- Khong hard delete ho so lam sang; dung `status`, `archivedAt` hoac version history.
- AuditLog luu `beforeData` va `afterData` dang JSON, co `ipAddress` va `userAgent`.
- AuditLog bat buoc co `sequence`, `previousHash`, `eventHash` va `immutableAfterAppend` de ho tro append-only hash chain.
- Cac truong nhay cam chi hien thi cho role co quyen.
- Demo seed la du lieu gia lap, khong phai nguoi that.
- CareRiskAssessment khong duoc xem la final neu thieu `confirmedBy`.
- ClinicalRule khong duoc chay production neu thieu approval.

## Migration

Dung Prisma migration:

```bash
npx prisma migrate dev --name init_chronic_care
```

Production phai dung migration da review:

```bash
npx prisma migrate deploy
```

Da co AuditLog hardening migration review dau tien cho audit storage:

- `prisma/migrations/202606190001_audit_log_hash_chain_hardening/migration.sql` khoa `sequence`, `previousHash`, `eventHash`, `immutableAfterAppend` va trigger chan `UPDATE`/`DELETE` tren `AuditLog`.

Luu y: migration nay la hardening cho bang `AuditLog` sau baseline schema; chua thay the nhu cau tao full baseline migration cho tat ca model truoc production.
