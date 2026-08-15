import { authorizeBackendAction } from "./backend-guard";
import type { Permission } from "./rbac";
import type { WriteActionRegistryItem } from "./write-action-registry";

export type ControlValidationResult = {
  accepted: boolean;
  blockedReasons: string[];
  controlsVerified: string[];
  safetyBoundary: string;
};

export type RouteGuardSurface = {
  route: string;
  surfaceType: "PAGE" | "API";
  accessMode: "READ_ONLY" | "GUARDED_WRITE_PREVIEW" | "BLOCKED_EXPORT";
  requiredPermission: Permission;
  requiredWriteActionId?: string;
  requiresOrganizationScope: boolean;
  requiresClinicSiteScope: boolean;
};

export const productionRouteGuardSurfaces: RouteGuardSurface[] = [
  surface("/", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/command-center", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/programs", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/evidence", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/mvp-01", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/dashboard/doctor", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/dashboard/nurse", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/dashboard/quality", "PAGE", "BLOCKED_EXPORT", "export.aggregate", true, true, "quality-export-csv"),
  surface("/patients", "PAGE", "GUARDED_WRITE_PREVIEW", "patient.register", true, true, "patient-register"),
  surface("/patients/[id]", "PAGE", "GUARDED_WRITE_PREVIEW", "care_plan.version", true, true, "patient-care-plan-draft"),
  surface("/appointments", "PAGE", "GUARDED_WRITE_PREVIEW", "task.manage", true, true, "appointment-create"),
  surface("/visits/prep", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/visits/initial", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/visits/follow-up", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/medications", "PAGE", "READ_ONLY", "medication.review", true, true),
  surface("/labs", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/care-plans", "PAGE", "GUARDED_WRITE_PREVIEW", "care_plan.approve", true, true, "care-plan-approve"),
  surface("/tasks", "PAGE", "READ_ONLY", "task.manage", true, true),
  surface("/referrals", "PAGE", "READ_ONLY", "patient.view_clinical", true, true),
  surface("/handouts", "PAGE", "GUARDED_WRITE_PREVIEW", "handout.approve", true, true, "handout-release"),
  surface("/risk/red", "PAGE", "READ_ONLY", "safety_alert.review", true, true),
  surface("/overdue", "PAGE", "GUARDED_WRITE_PREVIEW", "task.manage", true, true, "overdue-claim-call-task"),
  surface("/admin/rules", "PAGE", "GUARDED_WRITE_PREVIEW", "clinical_rules.manage", true, true, "clinical-rule-draft"),
  surface("/admin/templates", "PAGE", "GUARDED_WRITE_PREVIEW", "clinical_rules.manage", true, true, "template-draft"),
  surface("/admin/sop", "PAGE", "READ_ONLY", "backend.read", true, true),
  surface("/admin/users", "PAGE", "GUARDED_WRITE_PREVIEW", "user.manage", true, true, "user-invite"),
  surface("/admin/audit", "PAGE", "BLOCKED_EXPORT", "audit.view", true, true, "audit-export"),
  surface("/admin/settings", "PAGE", "READ_ONLY", "automation.manage", true, true),
  surface("/api/admin/outpatient-automation-control", "API", "READ_ONLY", "automation.manage", true, true),
  surface("/api/admin/production-readiness", "API", "READ_ONLY", "backend.read", true, true),
  surface("/api/evidence/knowledge-pack", "API", "READ_ONLY", "backend.read", true, true)
];

export function validateRouteGuardCoverage(
  surfaces: RouteGuardSurface[] = productionRouteGuardSurfaces,
  writeActions: WriteActionRegistryItem[]
): ControlValidationResult {
  const blockedReasons: string[] = [];
  const actionById = new Map(writeActions.map((item) => [item.actionId, item]));

  for (const item of surfaces) {
    if (!item.requiresOrganizationScope) {
      blockedReasons.push(`route_missing_organization_scope:${item.route}`);
    }
    if (!item.requiresClinicSiteScope) {
      blockedReasons.push(`route_missing_clinic_site_scope:${item.route}`);
    }
    if (item.accessMode !== "READ_ONLY") {
      if (!item.requiredWriteActionId) {
        blockedReasons.push(`route_missing_write_action_id:${item.route}`);
        continue;
      }
      const action = actionById.get(item.requiredWriteActionId);
      if (!action) {
        blockedReasons.push(`route_write_action_not_registered:${item.route}:${item.requiredWriteActionId}`);
        continue;
      }
      if (action.route !== item.route) {
        blockedReasons.push(`route_write_action_route_mismatch:${item.route}:${action.route}`);
      }
      if (action.permission !== item.requiredPermission) {
        blockedReasons.push(`route_permission_mismatch:${item.route}:${action.permission}`);
      }
      if (item.accessMode === "GUARDED_WRITE_PREVIEW" && action.guardStatus !== "GUARDED_PREVIEW") {
        blockedReasons.push(`route_not_guarded_preview:${item.route}:${action.guardStatus}`);
      }
      if (item.accessMode === "BLOCKED_EXPORT" && action.guardStatus !== "BLOCKED_FOR_PRODUCTION") {
        blockedReasons.push(`blocked_export_not_marked_blocked:${item.route}:${action.guardStatus}`);
      }
      if (!action.persistenceRequired || !action.auditRequired) {
        blockedReasons.push(`route_write_action_missing_persistence_or_audit:${item.route}`);
      }
    }
  }

  for (const action of writeActions) {
    if (!surfaces.some((item) => item.requiredWriteActionId === action.actionId)) {
      blockedReasons.push(`write_action_not_covered_by_route_surface:${action.actionId}`);
    }
  }

  return controlDecision(blockedReasons, ["route_inventory", "write_action_registry", "rbac_permissions", "scope_required"]);
}

export function validateOrganizationSiteIsolationContract(): ControlValidationResult {
  const allowed = authorizeBackendAction(
    { role: "PHYSICIAN", organizationId: "org-a", clinicSiteId: "site-a" },
    "patient.view_clinical",
    { organizationId: "org-a", clinicSiteId: "site-a" }
  );
  const crossOrg = authorizeBackendAction(
    { role: "PHYSICIAN", organizationId: "org-a", clinicSiteId: "site-a" },
    "patient.view_clinical",
    { organizationId: "org-b", clinicSiteId: "site-a" }
  );
  const crossSite = authorizeBackendAction(
    { role: "PHYSICIAN", organizationId: "org-a", clinicSiteId: "site-a" },
    "patient.view_clinical",
    { organizationId: "org-a", clinicSiteId: "site-b" }
  );

  const blockedReasons = [
    ...(allowed.allowed ? [] : ["same_site_access_should_be_allowed"]),
    ...(crossOrg.allowed ? ["cross_organization_access_allowed"] : []),
    ...(crossSite.allowed ? ["cross_site_access_allowed"] : []),
    ...(crossOrg.auditRequired && crossSite.auditRequired ? [] : ["denied_scope_access_must_require_audit"])
  ];

  return controlDecision(blockedReasons, ["same_site_allowed", "cross_org_denied", "cross_site_denied", "audit_on_denial"]);
}

export type DependencyScanEvidence = {
  scanId: string;
  scanner: "pnpm-audit" | "osv-scanner" | "snyk" | "manual-reviewed";
  generatedAt: string;
  lockfileSha256: string;
  criticalCount: number;
  highCount: number;
  moderateCount: number;
  ignoredAdvisories: string[];
  artifactRef: string;
  reviewerReference: string;
};

export function validateDependencyScanEvidence(evidence: DependencyScanEvidence): ControlValidationResult {
  const blockedReasons: string[] = [];
  if (!isPastOrPresentIso(evidence.generatedAt)) {
    blockedReasons.push("dependency_scan_generated_at_invalid_or_future");
  }
  if (!/^[a-f0-9]{64}$/i.test(evidence.lockfileSha256)) {
    blockedReasons.push("lockfile_sha256_invalid");
  }
  if (evidence.criticalCount > 0) {
    blockedReasons.push("dependency_scan_has_critical_vulnerabilities");
  }
  if (evidence.highCount > 0) {
    blockedReasons.push("dependency_scan_has_high_vulnerabilities");
  }
  if (evidence.ignoredAdvisories.some((item) => !safeReference(item))) {
    blockedReasons.push("ignored_advisory_reference_invalid");
  }
  if (!safeReference(evidence.artifactRef)) {
    blockedReasons.push("dependency_scan_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return controlDecision(blockedReasons, ["lockfile_hash", "critical_zero", "high_zero", "reviewed_artifact"]);
}

export type PrismaMigrationReviewEvidence = {
  reviewId: string;
  migrationFolder: string;
  schemaPrismaSha256: string;
  migrationSqlSha256: string;
  includesAuditHashChain: boolean;
  includesUpdateDeleteBlock: boolean;
  migrationSmokePassed: boolean;
  rollbackPlanArtifactRef: string;
  reviewerReference: string;
};

export function validatePrismaMigrationReviewEvidence(evidence: PrismaMigrationReviewEvidence): ControlValidationResult {
  const blockedReasons: string[] = [];
  if (!/^20\d{10,}_[a-z0-9_ -]+$/i.test(evidence.migrationFolder)) {
    blockedReasons.push("migration_folder_name_invalid");
  }
  if (!/^[a-f0-9]{64}$/i.test(evidence.schemaPrismaSha256)) {
    blockedReasons.push("schema_prisma_sha256_invalid");
  }
  if (!/^[a-f0-9]{64}$/i.test(evidence.migrationSqlSha256)) {
    blockedReasons.push("migration_sql_sha256_invalid");
  }
  if (!evidence.includesAuditHashChain) {
    blockedReasons.push("migration_missing_audit_hash_chain");
  }
  if (!evidence.includesUpdateDeleteBlock) {
    blockedReasons.push("migration_missing_update_delete_block");
  }
  if (!evidence.migrationSmokePassed) {
    blockedReasons.push("migration_smoke_not_passed");
  }
  if (!safeReference(evidence.rollbackPlanArtifactRef)) {
    blockedReasons.push("rollback_plan_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return controlDecision(blockedReasons, [
    "migration_folder",
    "schema_hash",
    "migration_hash",
    "audit_hash_chain",
    "mutation_block",
    "smoke_test"
  ]);
}

export type DockerRunEvidence = {
  runId: string;
  command: "docker compose up --build" | "docker compose up";
  composeFile: "docker-compose.yml";
  environment: "local" | "staging" | "production";
  healthcheckPassed: boolean;
  appResponded: boolean;
  databaseResponded: boolean;
  noSecretsPrinted: boolean;
  artifactRef: string;
  reviewerReference: string;
};

export function validateDockerRunEvidence(evidence: DockerRunEvidence): ControlValidationResult {
  const blockedReasons: string[] = [];
  if (evidence.environment === "production") {
    blockedReasons.push("production_docker_run_requires_separate_infrastructure_approval");
  }
  if (!evidence.healthcheckPassed) {
    blockedReasons.push("docker_healthcheck_not_passed");
  }
  if (!evidence.appResponded) {
    blockedReasons.push("docker_app_not_responding");
  }
  if (!evidence.databaseResponded) {
    blockedReasons.push("docker_database_not_responding");
  }
  if (!evidence.noSecretsPrinted) {
    blockedReasons.push("docker_logs_printed_secrets");
  }
  if (!safeReference(evidence.artifactRef)) {
    blockedReasons.push("docker_run_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return controlDecision(blockedReasons, ["docker_command", "app_healthcheck", "db_healthcheck", "secret_redaction"]);
}

export type GovernancePersistenceEvidence = {
  evidenceId: string;
  tables: string[];
  approvalWorkflowPersisted: boolean;
  auditLogLinked: boolean;
  appendOnlyAuditVerified: boolean;
  backupCovered: boolean;
  migrationReviewed: boolean;
  artifactRef: string;
  reviewerReference: string;
};

export function validateGovernancePersistenceEvidence(evidence: GovernancePersistenceEvidence): ControlValidationResult {
  const blockedReasons: string[] = [];
  for (const table of [
    "ClinicalRuleApproval",
    "ClinicalContentApproval",
    "EducationMaterialApproval",
    "SafetyAlertReview",
    "IncidentReview",
    "SystemSetting"
  ]) {
    if (!evidence.tables.includes(table)) {
      blockedReasons.push(`governance_table_missing:${table}`);
    }
  }
  if (!evidence.approvalWorkflowPersisted) {
    blockedReasons.push("approval_workflow_not_persisted");
  }
  if (!evidence.auditLogLinked) {
    blockedReasons.push("audit_log_not_linked");
  }
  if (!evidence.appendOnlyAuditVerified) {
    blockedReasons.push("append_only_audit_not_verified");
  }
  if (!evidence.backupCovered) {
    blockedReasons.push("governance_tables_not_covered_by_backup");
  }
  if (!evidence.migrationReviewed) {
    blockedReasons.push("governance_migration_not_reviewed");
  }
  if (!safeReference(evidence.artifactRef)) {
    blockedReasons.push("governance_artifact_ref_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return controlDecision(blockedReasons, [
    "governance_tables",
    "approval_persistence",
    "audit_link",
    "append_only_audit",
    "backup_coverage",
    "migration_review"
  ]);
}

function surface(
  route: string,
  surfaceType: RouteGuardSurface["surfaceType"],
  accessMode: RouteGuardSurface["accessMode"],
  requiredPermission: Permission,
  requiresOrganizationScope: boolean,
  requiresClinicSiteScope: boolean,
  requiredWriteActionId?: string
): RouteGuardSurface {
  return {
    route,
    surfaceType,
    accessMode,
    requiredPermission,
    requiredWriteActionId,
    requiresOrganizationScope,
    requiresClinicSiteScope
  };
}

function controlDecision(blockedReasons: string[], controlsVerified: string[]): ControlValidationResult {
  return {
    accepted: blockedReasons.length === 0,
    blockedReasons,
    controlsVerified,
    safetyBoundary:
      "This repository control can support production evidence review, but it does not authorize real patient use without signed evidence and go-live approval."
  };
}

function isPastOrPresentIso(value: string): boolean {
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) && timestamp <= Date.now();
}

function safeReference(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !/(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}
