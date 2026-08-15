import assert from "node:assert/strict";
import test from "node:test";

import { validateA5OutputQa } from "../lib/a5-output-qa";
import { evaluateRetentionRequest } from "../lib/data-retention";
import {
  validateBackupRestoreEvidence,
  validateIncidentDrillEvidence,
  validateMonitoringSmokeEvidence
} from "../lib/operations-readiness";
import { buildPatientEducationReleasePackage } from "../lib/patient-education";
import {
  hashPasswordForStorage,
  isPasswordHashRecordSafe,
  validatePasswordPolicy,
  verifyPasswordAgainstHash
} from "../lib/password-security";
import { runtimeHardeningControls } from "../lib/runtime-hardening";
import { patients } from "../lib/seed-data";

test("password hashing contract rejects weak passwords and stores only scrypt hash material", () => {
  const weak = validatePasswordPolicy("password123");
  assert.equal(weak.accepted, false);
  assert.ok(weak.blockedReasons.includes("password_too_short_min_14"));
  assert.ok(weak.blockedReasons.includes("password_contains_common_token"));

  const record = hashPasswordForStorage("Stronger!Passphrase2026", {
    salt: "clinic-os-test-salt-2026-07-16-abcdef",
    pepper: "pepper-rotation-key-001",
    createdAt: "2026-07-16T00:00:00.000Z"
  });

  assert.equal(record.algorithm, "scrypt");
  assert.equal(isPasswordHashRecordSafe(record), true);
  assert.equal(JSON.stringify(record).includes("Stronger!Passphrase2026"), false);
  assert.equal(verifyPasswordAgainstHash("Stronger!Passphrase2026", record, { pepper: "pepper-rotation-key-001" }), true);
  assert.equal(verifyPasswordAgainstHash("Stronger!Passphrase2026", record, { pepper: "wrong-pepper" }), false);
  assert.equal(verifyPasswordAgainstHash("wrong-password", record, { pepper: "pepper-rotation-key-001" }), false);
});

test("retention policy blocks direct delete and legal-hold archive plans", () => {
  const blocked = evaluateRetentionRequest({
    entityType: "Patient",
    recordAgeYears: 12,
    legalHold: true,
    activeClinicalEpisode: false,
    requestedAction: "DELETE",
    reviewedByRole: "DATA_PROTECTION",
    artifactRef: "retention/evidence/patient-archive-review-001.json"
  });

  assert.equal(blocked.allowed, false);
  assert.ok(blocked.blockedReasons.includes("legal_hold_blocks_retention_action"));
  assert.ok(blocked.blockedReasons.includes("direct_delete_not_allowed"));

  const allowed = evaluateRetentionRequest({
    entityType: "Patient",
    recordAgeYears: 12,
    legalHold: false,
    activeClinicalEpisode: false,
    requestedAction: "ARCHIVE",
    reviewedByRole: "DATA_PROTECTION",
    artifactRef: "retention/evidence/patient-archive-review-002.json"
  });

  assert.equal(allowed.allowed, true);
  assert.equal(allowed.action, "DEIDENTIFY_AND_ARCHIVE_ALLOWED");
  assert.ok(allowed.requiredEvidence.includes("audit_log_append_record"));
});

test("backup restore evidence accepts only non-production drills with checksum and RPO/RTO proof", () => {
  const accepted = validateBackupRestoreEvidence({
    drillId: "backup-drill-001",
    databaseScope: "STAGING_DATABASE",
    backupStartedAt: "2026-07-15T01:00:00.000Z",
    restoreCompletedAt: "2026-07-15T02:30:00.000Z",
    backupArtifactRef: "operations/evidence/backup-restore-drill-001.json",
    restoredRowCountsMatch: true,
    checksumVerified: true,
    rpoMinutes: 30,
    rtoMinutes: 90,
    containsProductionPatientData: false,
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(accepted.accepted, true);
  assert.deepEqual(accepted.blockedReasons, []);

  const blocked = validateBackupRestoreEvidence({
    drillId: "backup-drill-unsafe",
    databaseScope: "PRODUCTION_DATABASE",
    backupStartedAt: "2026-07-15T01:00:00.000Z",
    restoreCompletedAt: "2026-07-15T02:30:00.000Z",
    backupArtifactRef: "TODO/backup.json",
    restoredRowCountsMatch: false,
    checksumVerified: false,
    rpoMinutes: 120,
    rtoMinutes: 300,
    containsProductionPatientData: true,
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("production_database_drill_requires_separate_approval"));
  assert.ok(blocked.blockedReasons.includes("production_patient_data_not_allowed_in_repo_drill"));
  assert.ok(blocked.blockedReasons.includes("backup_checksum_not_verified"));
});

test("monitoring and incident drill evidence require clinical safety operations coverage", () => {
  const monitoring = validateMonitoringSmokeEvidence({
    smokeId: "monitoring-smoke-001",
    environment: "staging",
    errorCaptureVerified: true,
    auditFailureAlertVerified: true,
    redFlagWorkflowAlertVerified: true,
    onCallRouteVerified: true,
    dashboardArtifactRef: "operations/evidence/monitoring-smoke-001.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });
  assert.equal(monitoring.accepted, true);

  const incident = validateIncidentDrillEvidence({
    drillId: "incident-drill-001",
    scenario: "CLINICAL_SAFETY_EVENT",
    tabletopCompletedAt: "2026-07-15T03:00:00.000Z",
    rolesPresent: ["PHYSICIAN_LEAD", "DATA_PROTECTION", "OPERATIONS"],
    timelineMinutes: 45,
    actionItemsClosed: true,
    artifactRef: "operations/evidence/incident-drill-001.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });
  assert.equal(incident.accepted, true);

  const missingRole = validateIncidentDrillEvidence({
    ...{
      drillId: "incident-drill-002",
      scenario: "PHI_EXPOSURE" as const,
      tabletopCompletedAt: "2026-07-15T03:00:00.000Z",
      rolesPresent: ["OPERATIONS"],
      timelineMinutes: 180,
      actionItemsClosed: false,
      artifactRef: "operations/evidence/incident-drill-002.json",
      reviewerReference: "OPERATIONS_REVIEWER_001"
    }
  });
  assert.equal(missingRole.accepted, false);
  assert.ok(missingRole.blockedReasons.includes("incident_drill_missing_role:PHYSICIAN_LEAD"));
  assert.ok(missingRole.blockedReasons.includes("incident_drill_missing_role:DATA_PROTECTION"));
  assert.ok(missingRole.blockedReasons.includes("incident_response_timeline_exceeds_120_minutes"));
});

test("A5 output QA requires approved package, A5 format, disclaimer and emergency boundary", () => {
  const patient = patients.find((item) => item.carePlan.status === "APPROVED" && item.consentStatus === "SIGNED");
  assert.ok(patient, "Need at least one synthetic approved patient with consent.");
  const releasePackage = buildPatientEducationReleasePackage(patient);

  const qa = validateA5OutputQa(releasePackage, {
    renderId: "a5-render-001",
    renderer: "PRINT_HTML",
    pageFormat: "A5",
    renderedAt: "2026-07-15T04:00:00.000Z",
    artifactRef: "clinical-safety/evidence/a5-render-001.html",
    visualQaPassed: true,
    textOverflowDetected: false,
    containsEmergencyBoundary: true,
    containsDoctorVerificationDisclaimer: true,
    checksumSha256: "a".repeat(64),
    reviewerReference: "PHYSICIAN_LEAD_REVIEWER_001"
  });

  assert.equal(qa.accepted, true);
  assert.ok(qa.controlsVerified.includes("a5_page_format"));

  const blocked = validateA5OutputQa(releasePackage, {
    renderId: "a5-render-002",
    renderer: "PDF",
    pageFormat: "A5",
    renderedAt: "2026-07-15T04:00:00.000Z",
    artifactRef: "TODO/a5.pdf",
    visualQaPassed: false,
    textOverflowDetected: true,
    containsEmergencyBoundary: false,
    containsDoctorVerificationDisclaimer: false,
    checksumSha256: "bad",
    reviewerReference: "PHYSICIAN_LEAD_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("visual_qa_not_passed"));
  assert.ok(blocked.blockedReasons.includes("text_overflow_detected"));
  assert.ok(blocked.blockedReasons.includes("doctor_verification_disclaimer_missing"));
});

test("runtime hardening manifest exposes new production control evidence hooks", () => {
  for (const controlId of [
    "RUNTIME-PASSWORD-001",
    "RUNTIME-RETENTION-001",
    "RUNTIME-BACKUP-RESTORE-001",
    "RUNTIME-A5-QA-001",
    "RUNTIME-MONITORING-001",
    "RUNTIME-INCIDENT-DRILL-001",
    "RUNTIME-OUTPATIENT-AUTOMATION-001"
  ]) {
    assert.ok(runtimeHardeningControls.some((item) => item.controlId === controlId), `${controlId} missing`);
  }
});
