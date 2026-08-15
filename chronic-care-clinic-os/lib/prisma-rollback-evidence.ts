import {
  evaluatePrismaTestDatabaseGate,
  type PrismaRollbackEvidenceCase,
  type PrismaTestDatabaseGate,
  type PrismaTransactionContract
} from "./prisma-transaction-contract";

export const PRISMA_ROLLBACK_EVIDENCE_ARTIFACT_KIND = "PRISMA_ROLLBACK_EVIDENCE_REPORT";
export const AUDIT_LOG_HARDENING_MIGRATION_NAME = "202606190001_audit_log_hash_chain_hardening";

export type PrismaRollbackProbeStatus = "PASSED" | "FAILED" | "NOT_RUN";

export type PrismaRollbackProbeEvidence = {
  status: PrismaRollbackProbeStatus;
  businessWriteCountAfterRollback: number | null;
  auditLogCountAfterRollback: number | null;
  observedTrace: string[];
};

export type PrismaRollbackEvidenceReport = {
  artifactKind: typeof PRISMA_ROLLBACK_EVIDENCE_ARTIFACT_KIND;
  artifactVersion: 1;
  workflowActionName: PrismaTransactionContract["planActionName"];
  databaseScope: "ISOLATED_TEST_DATABASE" | "UNKNOWN_OR_SHARED_DATABASE" | "PRODUCTION_DATABASE";
  productionDataPresent: boolean;
  migration: {
    migrationName: string;
    auditLogHardeningApplied: boolean;
  };
  auditMutationProbe: {
    updateBlocked: boolean;
    deleteBlocked: boolean;
    observedErrorCode: string | null;
  };
  rollbackProbes: Record<PrismaRollbackEvidenceCase, PrismaRollbackProbeEvidence>;
  evidenceArtifact: string | null;
  reviewerSignoff: {
    reviewer: string;
    role: "QUALITY_MANAGER" | "READ_ONLY_AUDITOR" | "CLINIC_ADMIN";
    signedAt: string;
  } | null;
  productionCommitRequested: false;
};

export type PrismaRollbackEvidenceSchemaValidation = {
  valid: boolean;
  blockedReasons: string[];
  report: PrismaRollbackEvidenceReport | null;
};

export type PrismaRollbackEvidenceReadiness = PrismaTestDatabaseGate & {
  reportReady: boolean;
  reportProblems: string[];
};

const ROLLBACK_CASES: PrismaRollbackEvidenceCase[] = [
  "FAIL_BEFORE_BUSINESS_WRITE",
  "FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT",
  "FAIL_AFTER_AUDIT_BEFORE_COMMIT"
];

export function validatePrismaRollbackEvidenceReportSchema(value: unknown): PrismaRollbackEvidenceSchemaValidation {
  if (!isRecord(value)) {
    return {
      valid: false,
      blockedReasons: ["Rollback evidence report must be a JSON object."],
      report: null
    };
  }

  const blockedReasons = [
    ...(value.artifactKind === PRISMA_ROLLBACK_EVIDENCE_ARTIFACT_KIND
      ? []
      : ["artifactKind must be PRISMA_ROLLBACK_EVIDENCE_REPORT."]),
    ...(value.artifactVersion === 1 ? [] : ["artifactVersion must be 1."]),
    ...(isNonEmptyString(value.workflowActionName) ? [] : ["workflowActionName is required."]),
    ...(value.databaseScope === "ISOLATED_TEST_DATABASE" ||
    value.databaseScope === "UNKNOWN_OR_SHARED_DATABASE" ||
    value.databaseScope === "PRODUCTION_DATABASE"
      ? []
      : ["databaseScope must be explicit."]),
    ...(typeof value.productionDataPresent === "boolean" ? [] : ["productionDataPresent must be boolean."]),
    ...(isRecord(value.migration) ? [] : ["migration object is required."]),
    ...(isRecord(value.auditMutationProbe) ? [] : ["auditMutationProbe object is required."]),
    ...(isRecord(value.rollbackProbes) ? [] : ["rollbackProbes object is required."]),
    ...(value.evidenceArtifact === null || isNonEmptyString(value.evidenceArtifact)
      ? []
      : ["evidenceArtifact must be null or a non-empty string."]),
    ...(value.reviewerSignoff === null || isValidReviewerSignoff(value.reviewerSignoff)
      ? []
      : ["reviewerSignoff must be null or contain reviewer, role and signedAt."]),
    ...(value.productionCommitRequested === false ? [] : ["productionCommitRequested must be false."])
  ];

  if (isRecord(value.migration)) {
    if (!isNonEmptyString(value.migration.migrationName)) blockedReasons.push("migration.migrationName is required.");
    if (typeof value.migration.auditLogHardeningApplied !== "boolean") {
      blockedReasons.push("migration.auditLogHardeningApplied must be boolean.");
    }
  }

  if (isRecord(value.auditMutationProbe)) {
    if (typeof value.auditMutationProbe.updateBlocked !== "boolean") {
      blockedReasons.push("auditMutationProbe.updateBlocked must be boolean.");
    }
    if (typeof value.auditMutationProbe.deleteBlocked !== "boolean") {
      blockedReasons.push("auditMutationProbe.deleteBlocked must be boolean.");
    }
    if (value.auditMutationProbe.observedErrorCode !== null && !isNonEmptyString(value.auditMutationProbe.observedErrorCode)) {
      blockedReasons.push("auditMutationProbe.observedErrorCode must be null or a non-empty string.");
    }
  }

  if (isRecord(value.rollbackProbes)) {
    for (const rollbackCase of ROLLBACK_CASES) {
      const probe = value.rollbackProbes[rollbackCase];
      if (!isRecord(probe)) {
        blockedReasons.push(`rollbackProbes.${rollbackCase} is required.`);
        continue;
      }
      if (probe.status !== "PASSED" && probe.status !== "FAILED" && probe.status !== "NOT_RUN") {
        blockedReasons.push(`rollbackProbes.${rollbackCase}.status must be PASSED, FAILED or NOT_RUN.`);
      }
      if (!isNullableNumber(probe.businessWriteCountAfterRollback)) {
        blockedReasons.push(`rollbackProbes.${rollbackCase}.businessWriteCountAfterRollback must be number or null.`);
      }
      if (!isNullableNumber(probe.auditLogCountAfterRollback)) {
        blockedReasons.push(`rollbackProbes.${rollbackCase}.auditLogCountAfterRollback must be number or null.`);
      }
      if (!isStringArray(probe.observedTrace)) {
        blockedReasons.push(`rollbackProbes.${rollbackCase}.observedTrace must be an array of strings.`);
      }
    }
  }

  return {
    valid: blockedReasons.length === 0,
    blockedReasons,
    report: blockedReasons.length === 0 ? (value as PrismaRollbackEvidenceReport) : null
  };
}

export function evaluatePrismaRollbackEvidenceReport(
  contract: PrismaTransactionContract,
  report: PrismaRollbackEvidenceReport
): PrismaRollbackEvidenceReadiness {
  const reportProblems = [
    ...(report.workflowActionName === contract.planActionName
      ? []
      : ["Evidence workflow action must match the transaction contract."]),
    ...(report.productionCommitRequested === false ? [] : ["Rollback evidence cannot request production commit."]),
    ...(report.migration.migrationName === AUDIT_LOG_HARDENING_MIGRATION_NAME
      ? []
      : ["Evidence must reference the AuditLog hardening migration by name."]),
    ...(report.evidenceArtifact?.startsWith("reports/") ? [] : ["Evidence artifact must be stored under reports/."]),
    ...(validReviewerSignoff(report.reviewerSignoff) ? [] : ["Reviewer signoff is incomplete."])
  ];

  const gate = evaluatePrismaTestDatabaseGate(contract, {
    testDatabaseOnly: report.databaseScope === "ISOLATED_TEST_DATABASE",
    noProductionData: !report.productionDataPresent,
    migrationApplied:
      report.migration.auditLogHardeningApplied && report.migration.migrationName === AUDIT_LOG_HARDENING_MIGRATION_NAME,
    auditMutationBlocked: report.auditMutationProbe.updateBlocked && report.auditMutationProbe.deleteBlocked,
    rollbackCases: {
      FAIL_BEFORE_BUSINESS_WRITE: rollbackProbePassed(report.rollbackProbes.FAIL_BEFORE_BUSINESS_WRITE),
      FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT: rollbackProbePassed(
        report.rollbackProbes.FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT
      ),
      FAIL_AFTER_AUDIT_BEFORE_COMMIT: rollbackProbePassed(report.rollbackProbes.FAIL_AFTER_AUDIT_BEFORE_COMMIT)
    },
    evidenceArtifact: report.evidenceArtifact?.startsWith("reports/") ? report.evidenceArtifact : null,
    reviewerSignoff: validReviewerSignoff(report.reviewerSignoff)
      ? `${report.reviewerSignoff.role}:${report.reviewerSignoff.reviewer}:${report.reviewerSignoff.signedAt}`
      : null
  });

  const blockedReasons = [...gate.blockedReasons, ...reportProblems];
  return {
    ...gate,
    canEnableTestDatabaseAdapter: blockedReasons.length === 0,
    canEnableProductionCommit: false,
    productionCommitDisabled: true,
    blockedReasons,
    reportReady: blockedReasons.length === 0,
    reportProblems
  };
}

function rollbackProbePassed(probe: PrismaRollbackProbeEvidence): boolean {
  return (
    probe.status === "PASSED" &&
    probe.businessWriteCountAfterRollback === 0 &&
    probe.auditLogCountAfterRollback === 0 &&
    probe.observedTrace.includes("ROLLBACK_ATOMICALLY")
  );
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function isNonEmptyString(value: unknown): value is string {
  return typeof value === "string" && value.trim().length > 0;
}

function isNullableNumber(value: unknown): value is number | null {
  return value === null || typeof value === "number";
}

function isStringArray(value: unknown): value is string[] {
  return Array.isArray(value) && value.every((item) => typeof item === "string");
}

function isValidReviewerSignoff(value: unknown): boolean {
  return (
    isRecord(value) &&
    isNonEmptyString(value.reviewer) &&
    (value.role === "QUALITY_MANAGER" || value.role === "READ_ONLY_AUDITOR" || value.role === "CLINIC_ADMIN") &&
    isNonEmptyString(value.signedAt)
  );
}

function validReviewerSignoff(value: PrismaRollbackEvidenceReport["reviewerSignoff"]): value is NonNullable<
  PrismaRollbackEvidenceReport["reviewerSignoff"]
> {
  return isValidReviewerSignoff(value);
}
