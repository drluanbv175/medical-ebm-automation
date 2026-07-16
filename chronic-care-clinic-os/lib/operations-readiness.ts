export type BackupRestoreEvidence = {
  drillId: string;
  databaseScope: "ISOLATED_TEST_DATABASE" | "STAGING_DATABASE" | "PRODUCTION_DATABASE";
  backupStartedAt: string;
  restoreCompletedAt: string;
  backupArtifactRef: string;
  restoredRowCountsMatch: boolean;
  checksumVerified: boolean;
  rpoMinutes: number;
  rtoMinutes: number;
  containsProductionPatientData: boolean;
  reviewerReference: string;
};

export type MonitoringSmokeEvidence = {
  smokeId: string;
  environment: "staging" | "production";
  errorCaptureVerified: boolean;
  auditFailureAlertVerified: boolean;
  redFlagWorkflowAlertVerified: boolean;
  onCallRouteVerified: boolean;
  dashboardArtifactRef: string;
  reviewerReference: string;
};

export type IncidentDrillEvidence = {
  drillId: string;
  scenario: "PHI_EXPOSURE" | "CLINICAL_SAFETY_EVENT" | "OUTAGE" | "UNAUTHORIZED_ACCESS";
  tabletopCompletedAt: string;
  rolesPresent: string[];
  timelineMinutes: number;
  actionItemsClosed: boolean;
  artifactRef: string;
  reviewerReference: string;
};

export type OperationsEvidenceDecision = {
  accepted: boolean;
  blockedReasons: string[];
  controlsVerified: string[];
  safetyBoundary: string;
};

export function validateBackupRestoreEvidence(evidence: BackupRestoreEvidence): OperationsEvidenceDecision {
  const blockedReasons: string[] = [];
  if (evidence.databaseScope === "PRODUCTION_DATABASE") {
    blockedReasons.push("production_database_drill_requires_separate_approval");
  }
  if (evidence.containsProductionPatientData) {
    blockedReasons.push("production_patient_data_not_allowed_in_repo_drill");
  }
  if (!isPastOrPresentIso(evidence.backupStartedAt, evidence.restoreCompletedAt)) {
    blockedReasons.push("backup_started_at_invalid");
  }
  if (!isPastOrPresentIso(evidence.restoreCompletedAt, new Date().toISOString())) {
    blockedReasons.push("restore_completed_at_invalid_or_future");
  }
  if (!evidence.restoredRowCountsMatch) {
    blockedReasons.push("restored_row_counts_mismatch");
  }
  if (!evidence.checksumVerified) {
    blockedReasons.push("backup_checksum_not_verified");
  }
  if (evidence.rpoMinutes > 60) {
    blockedReasons.push("rpo_exceeds_60_minutes");
  }
  if (evidence.rtoMinutes > 240) {
    blockedReasons.push("rto_exceeds_240_minutes");
  }
  if (!safeReference(evidence.backupArtifactRef)) {
    blockedReasons.push("backup_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return operationsDecision(blockedReasons, ["backup_created", "restore_completed", "checksum_verified", "rpo_rto_recorded"]);
}

export function validateMonitoringSmokeEvidence(evidence: MonitoringSmokeEvidence): OperationsEvidenceDecision {
  const blockedReasons: string[] = [];
  if (!evidence.errorCaptureVerified) {
    blockedReasons.push("error_capture_not_verified");
  }
  if (!evidence.auditFailureAlertVerified) {
    blockedReasons.push("audit_failure_alert_not_verified");
  }
  if (!evidence.redFlagWorkflowAlertVerified) {
    blockedReasons.push("red_flag_alert_not_verified");
  }
  if (!evidence.onCallRouteVerified) {
    blockedReasons.push("on_call_route_not_verified");
  }
  if (!safeReference(evidence.dashboardArtifactRef)) {
    blockedReasons.push("dashboard_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return operationsDecision(blockedReasons, [
    "error_capture",
    "audit_alert",
    "red_flag_alert",
    "on_call_route",
    "monitoring_dashboard"
  ]);
}

export function validateIncidentDrillEvidence(evidence: IncidentDrillEvidence): OperationsEvidenceDecision {
  const blockedReasons: string[] = [];
  const requiredRoles = ["PHYSICIAN_LEAD", "DATA_PROTECTION", "OPERATIONS"];
  for (const role of requiredRoles) {
    if (!evidence.rolesPresent.includes(role)) {
      blockedReasons.push(`incident_drill_missing_role:${role}`);
    }
  }
  if (!isPastOrPresentIso(evidence.tabletopCompletedAt, new Date().toISOString())) {
    blockedReasons.push("tabletop_completed_at_invalid_or_future");
  }
  if (evidence.timelineMinutes > 120) {
    blockedReasons.push("incident_response_timeline_exceeds_120_minutes");
  }
  if (!evidence.actionItemsClosed) {
    blockedReasons.push("incident_action_items_not_closed");
  }
  if (!safeReference(evidence.artifactRef)) {
    blockedReasons.push("incident_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return operationsDecision(blockedReasons, ["incident_roles", "timeline", "action_items", "review_record"]);
}

function operationsDecision(blockedReasons: string[], controlsVerified: string[]): OperationsEvidenceDecision {
  return {
    accepted: blockedReasons.length === 0,
    blockedReasons,
    controlsVerified,
    safetyBoundary:
      "Operations evidence can support production review only after a responsible owner signs the artifact; this validator never touches production data."
  };
}

function isPastOrPresentIso(value: string, referenceIso: string): boolean {
  const timestamp = Date.parse(value);
  const reference = Date.parse(referenceIso);
  return Number.isFinite(timestamp) && Number.isFinite(reference) && timestamp <= reference;
}

function safeReference(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !/(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}
