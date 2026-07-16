import { runtimeHardeningControls, type RuntimeHardeningControlEvidence } from "./runtime-hardening";

export type ProductionBlockerCategory = "security" | "data_protection" | "clinical_safety" | "operations" | "ai_governance";

export type ProductionBlockerStatus = "OPEN" | "CLEARED";

export type ProductionBlocker = {
  id: string;
  category: ProductionBlockerCategory;
  title: string;
  owner: "CLINIC_ADMIN" | "DATA_PROTECTION" | "PHYSICIAN_LEAD" | "OPERATIONS" | "AI_GOVERNANCE";
  evidenceRequired: string;
  status: ProductionBlockerStatus;
  blocksProduction: true;
};

export type ProductionEvidenceRecord = {
  blockerId: string;
  status: "CLEARED";
  reviewedByRole: ProductionBlocker["owner"];
  reviewerReference: string;
  reviewedAt: string;
  artifactRefs: string[];
  controlsVerified: string[];
  expiresAt?: string;
  notes?: string;
};

export type ProductionSignoffRole =
  | "security_owner"
  | "data_protection_owner"
  | "physician_lead"
  | "operations_owner"
  | "ai_governance_owner";

export type ProductionSignoff = {
  role: ProductionSignoffRole;
  signerReference: string;
  signedAt: string;
  scope: string;
  artifactRefs: string[];
};

export type ProductionEvidencePackage = {
  kind: "chronic_care_production_evidence_package";
  generatedAt: string;
  evidence: ProductionEvidenceRecord[];
  signoffs: ProductionSignoff[];
};

export type ProductionReadinessFinding = {
  severity: "ERROR" | "WARN";
  code: string;
  blockerId?: string;
  message: string;
};

export type ProductionEvidenceSummary = {
  evidenceRecords: number;
  validEvidenceRecords: number;
  invalidEvidenceRecords: number;
  validSignoffs: number;
  requiredSignoffs: number;
  missingSignoffs: ProductionSignoffRole[];
};

export type ProductionReleaseDecision = {
  productionReady: boolean;
  status: "BLOCKED" | "PRODUCTION_READY";
  blockedReasons: string[];
};

export type ProductionReadinessSummary = {
  totalBlockers: number;
  openBlockers: number;
  clearedBlockers: number;
  byCategory: Record<ProductionBlockerCategory, number>;
  productionReady: boolean;
};

export type ProductionReadinessReport = {
  kind: "chronic_care_production_readiness_report";
  generatedAt: string;
  summary: ProductionReadinessSummary;
  blockers: ProductionBlocker[];
  repositoryControls: RuntimeHardeningControlEvidence[];
  evidenceSummary: ProductionEvidenceSummary;
  findings: ProductionReadinessFinding[];
  releaseDecision: ProductionReleaseDecision;
  requiredSignoffs: ProductionSignoffRole[];
  safetyBoundary: string;
};

const categoryOrder: ProductionBlockerCategory[] = [
  "security",
  "data_protection",
  "clinical_safety",
  "operations",
  "ai_governance"
];

export const requiredProductionSignoffs: ProductionSignoffRole[] = [
  "security_owner",
  "data_protection_owner",
  "physician_lead",
  "operations_owner",
  "ai_governance_owner"
];

export const productionBlockers: ProductionBlocker[] = [
  blocker("SEC-001", "security", "Backend RBAC wired to every route/action.", "CLINIC_ADMIN", "Route/action RBAC coverage inventory, deployed route review and reviewer signoff."),
  blocker("SEC-002", "security", "Production authentication, session and MFA implemented.", "CLINIC_ADMIN", "Auth threat model, MFA test evidence and session hardening review."),
  blocker("SEC-003", "security", "Password hashing implemented.", "CLINIC_ADMIN", "Password storage review proving scrypt hashing, salt/pepper handling and no plaintext path."),
  blocker("SEC-004", "security", "Rate limiting and CSRF controls implemented.", "CLINIC_ADMIN", "Abuse test evidence for write routes and forms."),
  blocker("SEC-005", "security", "Secure headers verified.", "CLINIC_ADMIN", "Header scan or deployment smoke report."),
  blocker("SEC-006", "security", "Environment validation implemented.", "CLINIC_ADMIN", "Startup gate rejects unsafe or missing production configuration."),
  blocker("SEC-007", "security", "Dependency lockfile and vulnerability scan completed.", "CLINIC_ADMIN", "Exact lockfile hash plus reviewed vulnerability scan with zero high/critical findings."),
  blocker("SEC-008", "security", "PHI redaction logger implemented.", "CLINIC_ADMIN", "Logging test showing PHI/PII is redacted before persistence."),

  blocker("DATA-001", "data_protection", "Organization/site isolation enforced end-to-end.", "DATA_PROTECTION", "Cross-organization and cross-site denial tests plus deployed/UAT signoff."),
  blocker("DATA-002", "data_protection", "Backup/restore procedure tested.", "DATA_PROTECTION", "Restore drill report with checksum plus RPO/RTO evidence."),
  blocker("DATA-003", "data_protection", "Audit log immutability enforced in reviewed runtime migration.", "DATA_PROTECTION", "Migration review and runtime mutation-denial evidence."),
  blocker("DATA-004", "data_protection", "Formal data retention/archive policy approved.", "DATA_PROTECTION", "Approved retention policy, legal-hold check and archive/delete procedure evidence."),
  blocker("DATA-005", "data_protection", "UAT completed with de-identified workflow data.", "DATA_PROTECTION", "UAT signoff using de-identified data only."),

  blocker("CLIN-001", "clinical_safety", "Clinical rules formally approved.", "PHYSICIAN_LEAD", "Signed clinical rule approval record."),
  blocker("CLIN-002", "clinical_safety", "Rule approval workflow fully executable.", "PHYSICIAN_LEAD", "End-to-end approval workflow test evidence."),
  blocker("CLIN-003", "clinical_safety", "Clinical content and patient education approval executable.", "PHYSICIAN_LEAD", "Content approval and patient education release evidence."),
  blocker("CLIN-004", "clinical_safety", "A5 PDF output tested.", "PHYSICIAN_LEAD", "Rendered A5/PDF output QA evidence with checksum, disclaimer and emergency boundary."),
  blocker("CLIN-005", "clinical_safety", "Red flag workflow tested with operational users.", "PHYSICIAN_LEAD", "Operational red-flag drill or UAT report."),
  blocker("CLIN-006", "clinical_safety", "Clinical safety signoff completed.", "PHYSICIAN_LEAD", "Signed clinical safety signoff."),

  blocker("OPS-001", "operations", "Docker one-command run verified.", "OPERATIONS", "Fresh-machine Docker run report with app/db health checks and redacted logs."),
  blocker("OPS-002", "operations", "Prisma migration folder generated and reviewed.", "OPERATIONS", "Reviewed migration folder, SQL hash, migration smoke test and rollback plan."),
  blocker("OPS-003", "operations", "Error logging and monitoring configured.", "OPERATIONS", "Monitoring smoke report covering errors, audit failures, red flags and on-call route."),
  blocker("OPS-004", "operations", "Incident response process drilled.", "OPERATIONS", "Incident response tabletop/drill record with physician, data protection and operations roles."),

  blocker("AI-001", "ai_governance", "AI remains disabled until privacy controls and human review workflow are verified.", "AI_GOVERNANCE", "AI_DRAFTS_ENABLED gate evidence plus privacy and review workflow signoff.")
];

export function summarizeProductionReadiness(blockers = productionBlockers, productionReady = false): ProductionReadinessSummary {
  const byCategory = Object.fromEntries(categoryOrder.map((category) => [category, 0])) as Record<ProductionBlockerCategory, number>;
  for (const item of blockers) {
    byCategory[item.category] += 1;
  }
  const openBlockers = blockers.filter((item) => item.status === "OPEN").length;
  return {
    totalBlockers: blockers.length,
    openBlockers,
    clearedBlockers: blockers.length - openBlockers,
    byCategory,
    productionReady
  };
}

export function openProductionBlockers(blockers = productionBlockers): ProductionBlocker[] {
  return blockers.filter((item) => item.status === "OPEN");
}

export function buildProductionReadinessReport(
  generatedAt = new Date().toISOString(),
  blockers = productionBlockers,
  evidencePackage: ProductionEvidencePackage | null = null
): ProductionReadinessReport {
  const assessment = assessProductionEvidence(blockers, evidencePackage, generatedAt);
  const releaseDecision = decideProductionRelease(assessment.blockers, assessment.findings, assessment.evidenceSummary);
  return {
    kind: "chronic_care_production_readiness_report",
    generatedAt,
    summary: summarizeProductionReadiness(assessment.blockers, releaseDecision.productionReady),
    blockers: assessment.blockers,
    repositoryControls: runtimeHardeningControls,
    evidenceSummary: assessment.evidenceSummary,
    findings: assessment.findings,
    releaseDecision,
    requiredSignoffs: requiredProductionSignoffs,
    safetyBoundary: releaseDecision.productionReady
      ? "Production-ready only for the signed scope in the evidence package; continue post-deployment monitoring and incident drills."
      : "Not production-ready; must not be used with real patient data until every blocker is cleared with evidence and all signoffs are complete."
  };
}

export function assessProductionEvidence(
  blockers = productionBlockers,
  evidencePackage: ProductionEvidencePackage | null = null,
  generatedAt = new Date().toISOString()
): {
  blockers: ProductionBlocker[];
  evidenceSummary: ProductionEvidenceSummary;
  findings: ProductionReadinessFinding[];
} {
  const findings: ProductionReadinessFinding[] = [];
  const evidenceRecords = evidencePackage?.evidence ?? [];
  const signoffs = evidencePackage?.signoffs ?? [];
  const blockerById = new Map(blockers.map((item) => [item.id, item]));
  const validEvidenceByBlocker = new Map<string, ProductionEvidenceRecord>();

  if (!evidencePackage) {
    findings.push({
      severity: "ERROR",
      code: "production_evidence_package_missing",
      message: "No production evidence package was provided."
    });
  } else if (evidencePackage.kind !== "chronic_care_production_evidence_package") {
    findings.push({
      severity: "ERROR",
      code: "production_evidence_package_kind_invalid",
      message: "Evidence package kind must be chronic_care_production_evidence_package."
    });
  } else if (!isValidPastOrPresentIso(evidencePackage.generatedAt, generatedAt)) {
    findings.push({
      severity: "ERROR",
      code: "production_evidence_package_timestamp_invalid",
      message: "Evidence package generatedAt must be a valid ISO timestamp not after report generation."
    });
  }

  const seenEvidenceBlockers = new Set<string>();
  for (const record of evidenceRecords) {
    const duplicate = seenEvidenceBlockers.has(record.blockerId);
    seenEvidenceBlockers.add(record.blockerId);
    const blocker = blockerById.get(record.blockerId);
    const errors = blocker ? validateEvidenceRecord(record, blocker, generatedAt) : [
      `Unknown blockerId: ${record.blockerId}`
    ];
    if (duplicate) {
      errors.push(`Duplicate evidence record for blockerId: ${record.blockerId}`);
    }
    if (errors.length > 0) {
      for (const message of errors) {
        findings.push({
          severity: "ERROR",
          code: "invalid_blocker_evidence",
          blockerId: record.blockerId,
          message
        });
      }
      continue;
    }
    validEvidenceByBlocker.set(record.blockerId, record);
  }

  for (const blocker of blockers) {
    if (!validEvidenceByBlocker.has(blocker.id)) {
      findings.push({
        severity: "ERROR",
        code: "missing_blocker_evidence",
        blockerId: blocker.id,
        message: `${blocker.id} requires evidence: ${blocker.evidenceRequired}`
      });
    }
  }

  const signoffValidation = validateProductionSignoffs(signoffs, generatedAt);
  findings.push(...signoffValidation.findings);

  return {
    blockers: blockers.map((item) => ({
      ...item,
      status: validEvidenceByBlocker.has(item.id) ? "CLEARED" : "OPEN"
    })),
    evidenceSummary: {
      evidenceRecords: evidenceRecords.length,
      validEvidenceRecords: validEvidenceByBlocker.size,
      invalidEvidenceRecords: Math.max(0, evidenceRecords.length - validEvidenceByBlocker.size),
      validSignoffs: signoffValidation.validRoles.size,
      requiredSignoffs: requiredProductionSignoffs.length,
      missingSignoffs: requiredProductionSignoffs.filter((role) => !signoffValidation.validRoles.has(role))
    },
    findings
  };
}

export function decideProductionRelease(
  blockers: ProductionBlocker[],
  findings: ProductionReadinessFinding[],
  evidenceSummary: ProductionEvidenceSummary
): ProductionReleaseDecision {
  const openBlockers = blockers.filter((item) => item.status === "OPEN");
  const errorFindings = findings.filter((item) => item.severity === "ERROR");
  const blockedReasons = [
    ...openBlockers.map((item) => `open_blocker:${item.id}`),
    ...evidenceSummary.missingSignoffs.map((role) => `missing_signoff:${role}`),
    ...errorFindings.map((item) => item.blockerId ? `${item.code}:${item.blockerId}` : item.code)
  ];
  const uniqueReasons = Array.from(new Set(blockedReasons));
  const productionReady = uniqueReasons.length === 0;
  return {
    productionReady,
    status: productionReady ? "PRODUCTION_READY" : "BLOCKED",
    blockedReasons: uniqueReasons
  };
}

function validateEvidenceRecord(
  record: ProductionEvidenceRecord,
  blocker: ProductionBlocker,
  generatedAt: string
): string[] {
  const errors: string[] = [];
  if (record.status !== "CLEARED") {
    errors.push(`${record.blockerId} evidence status must be CLEARED.`);
  }
  if (record.reviewedByRole !== blocker.owner) {
    errors.push(`${record.blockerId} must be reviewed by ${blocker.owner}.`);
  }
  if (!safeReference(record.reviewerReference)) {
    errors.push(`${record.blockerId} reviewerReference is missing, placeholder, or appears to contain PII.`);
  }
  if (!isValidPastOrPresentIso(record.reviewedAt, generatedAt)) {
    errors.push(`${record.blockerId} reviewedAt must be a valid ISO timestamp not after report generation.`);
  }
  if (!Array.isArray(record.artifactRefs) || record.artifactRefs.length === 0 || record.artifactRefs.some((item) => !safeArtifactRef(item))) {
    errors.push(`${record.blockerId} requires at least one safe artifact reference.`);
  }
  if (!Array.isArray(record.controlsVerified)
    || record.controlsVerified.length === 0
    || record.controlsVerified.some((item) => !safeControlEvidence(item))) {
    errors.push(`${record.blockerId} requires non-placeholder controlsVerified entries.`);
  }
  if (record.expiresAt && !isValidFutureIso(record.expiresAt, generatedAt)) {
    errors.push(`${record.blockerId} evidence has expired or expiresAt is invalid.`);
  }
  return errors;
}

function validateProductionSignoffs(
  signoffs: ProductionSignoff[],
  generatedAt: string
): { validRoles: Set<ProductionSignoffRole>; findings: ProductionReadinessFinding[] } {
  const validRoles = new Set<ProductionSignoffRole>();
  const findings: ProductionReadinessFinding[] = [];
  for (const signoff of signoffs) {
    const errors: string[] = [];
    if (!requiredProductionSignoffs.includes(signoff.role)) {
      errors.push(`Unknown signoff role: ${String(signoff.role)}`);
    }
    if (!safeReference(signoff.signerReference)) {
      errors.push(`${signoff.role} signerReference is missing, placeholder, or appears to contain PII.`);
    }
    if (!isValidPastOrPresentIso(signoff.signedAt, generatedAt)) {
      errors.push(`${signoff.role} signedAt must be a valid ISO timestamp not after report generation.`);
    }
    if (containsPlaceholder(signoff.scope)) {
      errors.push(`${signoff.role} scope must not contain placeholders.`);
    }
    if (!signoff.scope.toLowerCase().includes("production")) {
      errors.push(`${signoff.role} scope must explicitly include production.`);
    }
    if (!Array.isArray(signoff.artifactRefs) || signoff.artifactRefs.length === 0 || signoff.artifactRefs.some((item) => !safeArtifactRef(item))) {
      errors.push(`${signoff.role} requires at least one safe signoff artifact reference.`);
    }
    if (errors.length > 0) {
      for (const message of errors) {
        findings.push({
          severity: "ERROR",
          code: "invalid_required_signoff",
          message
        });
      }
      continue;
    }
    validRoles.add(signoff.role);
  }
  for (const role of requiredProductionSignoffs) {
    if (!validRoles.has(role)) {
      findings.push({
        severity: "ERROR",
        code: "missing_required_signoff",
        message: `Missing required production signoff: ${role}`
      });
    }
  }
  return { validRoles, findings };
}

function isValidPastOrPresentIso(value: string, generatedAt: string): boolean {
  const timestamp = Date.parse(value);
  const reportTimestamp = Date.parse(generatedAt);
  return Number.isFinite(timestamp) && Number.isFinite(reportTimestamp) && timestamp <= reportTimestamp;
}

function isValidFutureIso(value: string, generatedAt: string): boolean {
  const timestamp = Date.parse(value);
  const reportTimestamp = Date.parse(generatedAt);
  return Number.isFinite(timestamp) && Number.isFinite(reportTimestamp) && timestamp > reportTimestamp;
}

function safeReference(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !containsPlaceholder(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}

function safeArtifactRef(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !containsPlaceholder(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}

function safeControlEvidence(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !containsPlaceholder(value);
}

function containsPlaceholder(value: string): boolean {
  return /(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value);
}

function blocker(
  id: string,
  category: ProductionBlockerCategory,
  title: string,
  owner: ProductionBlocker["owner"],
  evidenceRequired: string
): ProductionBlocker {
  return {
    id,
    category,
    title,
    owner,
    evidenceRequired,
    status: "OPEN",
    blocksProduction: true
  };
}
