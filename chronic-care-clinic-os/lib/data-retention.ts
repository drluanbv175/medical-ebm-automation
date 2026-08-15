export type RetentionEntityType =
  | "Patient"
  | "PatientIdentifier"
  | "PatientContact"
  | "CarePlanVersion"
  | "AuditLog"
  | "AIDraft"
  | "QualityMetric"
  | "PatientHandout";

export type RetentionRule = {
  entityType: RetentionEntityType;
  minimumRetentionYears: number;
  actionAfterRetention: "ARCHIVE" | "DEIDENTIFY_AND_ARCHIVE" | "KEEP_IMMUTABLE";
  deleteAllowed: boolean;
  legalHoldBlocksAction: true;
  requiresDataProtectionReview: true;
};

export type RetentionEvaluationInput = {
  entityType: RetentionEntityType;
  recordAgeYears: number;
  legalHold: boolean;
  activeClinicalEpisode: boolean;
  patientConsentWithdrawn?: boolean;
  requestedAction: "ARCHIVE" | "DEIDENTIFY" | "DELETE" | "EXPORT_AGGREGATE";
  reviewedByRole?: "DATA_PROTECTION" | "CLINIC_ADMIN" | "PHYSICIAN_LEAD" | null;
  artifactRef?: string | null;
};

export type RetentionDecision = {
  allowed: boolean;
  action: "BLOCKED" | "ARCHIVE_ALLOWED" | "DEIDENTIFY_AND_ARCHIVE_ALLOWED" | "KEEP_IMMUTABLE" | "AGGREGATE_EXPORT_ALLOWED";
  blockedReasons: string[];
  requiredEvidence: string[];
  rule: RetentionRule;
  safetyBoundary: string;
};

export const retentionRules: RetentionRule[] = [
  rule("Patient", 10, "DEIDENTIFY_AND_ARCHIVE", false),
  rule("PatientIdentifier", 10, "DEIDENTIFY_AND_ARCHIVE", false),
  rule("PatientContact", 10, "DEIDENTIFY_AND_ARCHIVE", false),
  rule("CarePlanVersion", 10, "KEEP_IMMUTABLE", false),
  rule("AuditLog", 10, "KEEP_IMMUTABLE", false),
  rule("AIDraft", 1, "DEIDENTIFY_AND_ARCHIVE", false),
  rule("QualityMetric", 5, "ARCHIVE", false),
  rule("PatientHandout", 10, "KEEP_IMMUTABLE", false)
];

export function evaluateRetentionRequest(input: RetentionEvaluationInput): RetentionDecision {
  const ruleForEntity = retentionRules.find((item) => item.entityType === input.entityType);
  if (!ruleForEntity) {
    throw new Error(`No retention rule for entity type ${input.entityType}`);
  }

  const blockedReasons: string[] = [];
  if (input.legalHold) {
    blockedReasons.push("legal_hold_blocks_retention_action");
  }
  if (input.activeClinicalEpisode) {
    blockedReasons.push("active_clinical_episode_blocks_retention_action");
  }
  if (input.recordAgeYears < ruleForEntity.minimumRetentionYears && input.requestedAction !== "EXPORT_AGGREGATE") {
    blockedReasons.push(`minimum_retention_not_met:${ruleForEntity.minimumRetentionYears}_years`);
  }
  if (input.requestedAction === "DELETE" && !ruleForEntity.deleteAllowed) {
    blockedReasons.push("direct_delete_not_allowed");
  }
  if (input.reviewedByRole !== "DATA_PROTECTION") {
    blockedReasons.push("data_protection_review_required");
  }
  if (!safeArtifactRef(input.artifactRef)) {
    blockedReasons.push("retention_artifact_ref_required");
  }
  if (input.patientConsentWithdrawn && input.entityType === "AuditLog") {
    blockedReasons.push("consent_withdrawal_cannot_delete_audit_log");
  }

  const allowed = blockedReasons.length === 0;
  return {
    allowed,
    action: allowed ? allowedRetentionAction(input, ruleForEntity) : "BLOCKED",
    blockedReasons,
    requiredEvidence: [
      "data_protection_review_record",
      "retention_scope_and_entity_list",
      "legal_hold_check",
      "deidentification_or_archive_log",
      "audit_log_append_record"
    ],
    rule: ruleForEntity,
    safetyBoundary:
      "Retention actions are governance plans only; production archive/delete jobs require reviewed evidence, legal hold checks and append-only audit logging."
  };
}

function allowedRetentionAction(
  input: RetentionEvaluationInput,
  ruleForEntity: RetentionRule
): RetentionDecision["action"] {
  if (input.requestedAction === "EXPORT_AGGREGATE") {
    return "AGGREGATE_EXPORT_ALLOWED";
  }
  if (ruleForEntity.actionAfterRetention === "KEEP_IMMUTABLE") {
    return "KEEP_IMMUTABLE";
  }
  if (ruleForEntity.actionAfterRetention === "DEIDENTIFY_AND_ARCHIVE") {
    return "DEIDENTIFY_AND_ARCHIVE_ALLOWED";
  }
  return "ARCHIVE_ALLOWED";
}

function rule(
  entityType: RetentionEntityType,
  minimumRetentionYears: number,
  actionAfterRetention: RetentionRule["actionAfterRetention"],
  deleteAllowed: boolean
): RetentionRule {
  return {
    entityType,
    minimumRetentionYears,
    actionAfterRetention,
    deleteAllowed,
    legalHoldBlocksAction: true,
    requiresDataProtectionReview: true
  };
}

function safeArtifactRef(value: string | null | undefined): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !/(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}
