import assert from "node:assert/strict";
import test from "node:test";

import {
  validateDependencyScanEvidence,
  validateDockerRunEvidence,
  validateGovernancePersistenceEvidence,
  validateOrganizationSiteIsolationContract,
  validatePrismaMigrationReviewEvidence,
  validateRouteGuardCoverage
} from "../lib/production-go-live-controls";
import { runtimeHardeningControls } from "../lib/runtime-hardening";
import { writeActionRegistry } from "../lib/write-action-registry";

test("route guard coverage maps write surfaces to registry and blocks orphan write actions", () => {
  const result = validateRouteGuardCoverage(undefined, writeActionRegistry);

  assert.equal(result.accepted, true);
  assert.deepEqual(result.blockedReasons, []);
  assert.ok(result.controlsVerified.includes("route_inventory"));

  const orphaned = validateRouteGuardCoverage(undefined, [
    ...writeActionRegistry,
    {
      ...writeActionRegistry[0],
      actionId: "unsafe-orphan-write-action",
      route: "/unsafe"
    }
  ]);

  assert.equal(orphaned.accepted, false);
  assert.ok(orphaned.blockedReasons.includes("write_action_not_covered_by_route_surface:unsafe-orphan-write-action"));
});

test("organization and site isolation contract denies cross-boundary clinical access", () => {
  const result = validateOrganizationSiteIsolationContract();

  assert.equal(result.accepted, true);
  assert.deepEqual(result.blockedReasons, []);
  assert.ok(result.controlsVerified.includes("cross_org_denied"));
  assert.ok(result.controlsVerified.includes("cross_site_denied"));
});

test("dependency scan evidence requires exact lockfile hash and zero high or critical vulnerabilities", () => {
  const accepted = validateDependencyScanEvidence({
    scanId: "dependency-scan-001",
    scanner: "pnpm-audit",
    generatedAt: "2026-07-15T00:00:00.000Z",
    lockfileSha256: "b".repeat(64),
    criticalCount: 0,
    highCount: 0,
    moderateCount: 2,
    ignoredAdvisories: ["ADVISORY-LOW-RISK-REVIEW-001"],
    artifactRef: "security/evidence/dependency-scan-001.json",
    reviewerReference: "CLINIC_ADMIN_REVIEWER_001"
  });

  assert.equal(accepted.accepted, true);
  assert.deepEqual(accepted.blockedReasons, []);

  const blocked = validateDependencyScanEvidence({
    scanId: "dependency-scan-002",
    scanner: "pnpm-audit",
    generatedAt: "2026-07-15T00:00:00.000Z",
    lockfileSha256: "bad-hash",
    criticalCount: 1,
    highCount: 1,
    moderateCount: 0,
    ignoredAdvisories: ["TODO-ignore"],
    artifactRef: "TODO/scan.json",
    reviewerReference: "CLINIC_ADMIN_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("lockfile_sha256_invalid"));
  assert.ok(blocked.blockedReasons.includes("dependency_scan_has_critical_vulnerabilities"));
  assert.ok(blocked.blockedReasons.includes("dependency_scan_has_high_vulnerabilities"));
});

test("Prisma migration review evidence requires audit hash chain and mutation blocking", () => {
  const accepted = validatePrismaMigrationReviewEvidence({
    reviewId: "migration-review-001",
    migrationFolder: "202606190001_audit_log_hash_chain_hardening",
    schemaPrismaSha256: "c".repeat(64),
    migrationSqlSha256: "d".repeat(64),
    includesAuditHashChain: true,
    includesUpdateDeleteBlock: true,
    migrationSmokePassed: true,
    rollbackPlanArtifactRef: "operations/evidence/prisma-migration-review-001.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(accepted.accepted, true);
  assert.deepEqual(accepted.blockedReasons, []);

  const blocked = validatePrismaMigrationReviewEvidence({
    reviewId: "migration-review-002",
    migrationFolder: "migration",
    schemaPrismaSha256: "bad",
    migrationSqlSha256: "bad",
    includesAuditHashChain: false,
    includesUpdateDeleteBlock: false,
    migrationSmokePassed: false,
    rollbackPlanArtifactRef: "TODO/rollback.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("migration_folder_name_invalid"));
  assert.ok(blocked.blockedReasons.includes("migration_missing_audit_hash_chain"));
  assert.ok(blocked.blockedReasons.includes("migration_missing_update_delete_block"));
});

test("Docker smoke evidence accepts non-production run and rejects unsafe production-like run", () => {
  const accepted = validateDockerRunEvidence({
    runId: "docker-smoke-001",
    command: "docker compose up --build",
    composeFile: "docker-compose.yml",
    environment: "staging",
    healthcheckPassed: true,
    appResponded: true,
    databaseResponded: true,
    noSecretsPrinted: true,
    artifactRef: "operations/evidence/docker-smoke-001.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(accepted.accepted, true);

  const blocked = validateDockerRunEvidence({
    runId: "docker-smoke-002",
    command: "docker compose up",
    composeFile: "docker-compose.yml",
    environment: "production",
    healthcheckPassed: false,
    appResponded: false,
    databaseResponded: false,
    noSecretsPrinted: false,
    artifactRef: "TODO/docker.json",
    reviewerReference: "OPERATIONS_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("production_docker_run_requires_separate_infrastructure_approval"));
  assert.ok(blocked.blockedReasons.includes("docker_logs_printed_secrets"));
});

test("governance persistence evidence requires all live governance tables and audit linkage", () => {
  const accepted = validateGovernancePersistenceEvidence({
    evidenceId: "governance-persistence-001",
    tables: [
      "ClinicalRuleApproval",
      "ClinicalContentApproval",
      "EducationMaterialApproval",
      "SafetyAlertReview",
      "IncidentReview",
      "SystemSetting"
    ],
    approvalWorkflowPersisted: true,
    auditLogLinked: true,
    appendOnlyAuditVerified: true,
    backupCovered: true,
    migrationReviewed: true,
    artifactRef: "governance/evidence/persistence-001.json",
    reviewerReference: "DATA_PROTECTION_REVIEWER_001"
  });

  assert.equal(accepted.accepted, true);

  const blocked = validateGovernancePersistenceEvidence({
    evidenceId: "governance-persistence-002",
    tables: ["SystemSetting"],
    approvalWorkflowPersisted: false,
    auditLogLinked: false,
    appendOnlyAuditVerified: false,
    backupCovered: false,
    migrationReviewed: false,
    artifactRef: "TODO/governance.json",
    reviewerReference: "DATA_PROTECTION_REVIEWER_001"
  });

  assert.equal(blocked.accepted, false);
  assert.ok(blocked.blockedReasons.includes("governance_table_missing:ClinicalRuleApproval"));
  assert.ok(blocked.blockedReasons.includes("approval_workflow_not_persisted"));
  assert.ok(blocked.blockedReasons.includes("append_only_audit_not_verified"));
});

test("runtime hardening manifest exposes remaining go-live evidence hooks", () => {
  for (const controlId of [
    "RUNTIME-RBAC-COVERAGE-001",
    "RUNTIME-DEPENDENCY-SCAN-001",
    "RUNTIME-PRISMA-MIGRATION-001",
    "RUNTIME-SITE-ISOLATION-001",
    "RUNTIME-DOCKER-SMOKE-001",
    "RUNTIME-GOVERNANCE-PERSISTENCE-001"
  ]) {
    assert.ok(runtimeHardeningControls.some((item) => item.controlId === controlId), `${controlId} missing`);
  }
});
