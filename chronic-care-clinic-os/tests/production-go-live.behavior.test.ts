import assert from "node:assert/strict";
import test from "node:test";

import { buildProductionEvidenceTemplate } from "../lib/production-evidence-template";
import { buildProductionGoLiveReport } from "../lib/production-go-live";
import {
  productionBlockers,
  requiredRepositoryControlIdsForBlocker,
  requiredProductionSignoffs,
  type ProductionEvidencePackage
} from "../lib/production-readiness";

const safeEnv = {
  NODE_ENV: "production",
  DATABASE_URL: "postgresql://app:secret@db.example.internal:5432/clinic",
  APP_BASE_URL: "https://clinic.example.org",
  NEXTAUTH_SECRET: "12345678901234567890123456789012",
  CSRF_SECRET: "abcdefabcdefabcdefabcdefabcdefabcd",
  AI_DRAFTS_ENABLED: "false",
  SESSION_COOKIE_SECURE: "true",
  RATE_LIMIT_ENABLED: "true",
  RATE_LIMIT_MAX: "120",
  RATE_LIMIT_WINDOW_SECONDS: "60",
  SECURITY_HEADERS_ENABLED: "true",
  AUDIT_LOG_REDACTION_ENABLED: "true",
  PATIENT_COMMUNICATIONS_ENABLED: "true",
  PATIENT_COMMUNICATION_POLICY_VERSION: "clinic-policy-2026-07-16",
  ALLOWED_ORIGINS: "https://clinic.example.org",
  SOURCE_COMMIT_SHA: "abcdef1234567890",
  PRODUCTION_RELEASE_ID: "release-2026-07-16-001",
  PRODUCTION_OPERATOR_REF: "OPS_GO_LIVE_001",
  PRODUCTION_ADMIN_APPROVER_REF: "ADMIN_APPROVER_001",
  PRODUCTION_CHANGE_TICKET_REF: "CHANGE_TICKET_2026_07_16_001",
  PRODUCTION_ROLLBACK_PLAN_REF: "operations/evidence/rollback-plan-001.json",
  PRODUCTION_POST_DEPLOY_CHECKLIST_REF: "operations/evidence/post-deploy-checklist-001.json"
};

const safeAttestation = {
  evidenceSha256: "a".repeat(64),
  evidenceDossierSha256: "b".repeat(64),
  evidencePath: "/secure/path/production-evidence.json",
  sourceCommitSha: safeEnv.SOURCE_COMMIT_SHA,
  releaseId: safeEnv.PRODUCTION_RELEASE_ID,
  operatorReference: safeEnv.PRODUCTION_OPERATOR_REF,
  adminApproverReference: safeEnv.PRODUCTION_ADMIN_APPROVER_REF,
  changeTicketReference: safeEnv.PRODUCTION_CHANGE_TICKET_REF,
  rollbackPlanArtifactRef: safeEnv.PRODUCTION_ROLLBACK_PLAN_REF,
  postDeploymentChecklistRef: safeEnv.PRODUCTION_POST_DEPLOY_CHECKLIST_REF
};

test("one go-live report becomes production ready only when evidence env and headers pass together", () => {
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    safeEnv,
    "2026-07-16T00:00:00.000Z",
    safeAttestation
  );

  assert.equal(report.kind, "chronic_care_production_go_live_report");
  assert.equal(report.status, "PRODUCTION_READY");
  assert.equal(report.productionReady, true);
  assert.deepEqual(report.blockedReasons, []);
  assert.equal(report.readiness.releaseDecision.status, "PRODUCTION_READY");
  assert.equal(report.runtimeEnvironment.allowed, true);
  assert.equal(report.runtimeEnvironment.warnings.length, 0);
  assert.equal(report.secureHeaders.allowed, true);
  assert.equal(report.emittedHeaders["X-Clinical-Production-Ready"], "true");
  assert.equal(report.attestation.evidenceSha256, "a".repeat(64));
  assert.equal(report.attestation.evidenceDossierSha256, "b".repeat(64));
  assert.equal(report.attestation.sourceCommitSha, safeEnv.SOURCE_COMMIT_SHA);
});

test("one go-live report blocks runtime warnings instead of calling production", () => {
  const envWithoutAllowedOrigins = { ...safeEnv, ALLOWED_ORIGINS: undefined };
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    envWithoutAllowedOrigins,
    "2026-07-16T00:00:00.000Z",
    safeAttestation
  );

  assert.equal(report.status, "BLOCKED");
  assert.equal(report.productionReady, false);
  assert.ok(report.blockedReasons.includes("runtime_env_warning:allowed_origins_not_declared"));
});

test("one go-live report blocks placeholder evidence template even in a safe env", () => {
  const report = buildProductionGoLiveReport(
    buildProductionEvidenceTemplate({
      generatedAt: "2026-07-16T00:00:00.000Z",
      reviewedAt: "2026-07-15T12:00:00.000Z",
      expiresAt: "2027-07-16T00:00:00.000Z"
    }),
    safeEnv,
    "2026-07-16T00:00:00.000Z",
    safeAttestation
  );

  assert.equal(report.status, "BLOCKED");
  assert.equal(report.productionReady, false);
  assert.ok(report.blockedReasons.some((reason) => reason.startsWith("readiness:open_blocker:")));
  assert.equal(report.emittedHeaders["X-Clinical-Production-Ready"], "false");
});

test("one go-live report blocks missing release attestation", () => {
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    safeEnv,
    "2026-07-16T00:00:00.000Z",
    {
      evidenceSha256: null,
      evidenceDossierSha256: null,
      evidencePath: null,
      sourceCommitSha: null,
      releaseId: null,
      operatorReference: null,
      adminApproverReference: null,
      changeTicketReference: null,
      rollbackPlanArtifactRef: null,
      postDeploymentChecklistRef: null
    }
  );

  assert.equal(report.status, "BLOCKED");
  assert.equal(report.productionReady, false);
  assert.ok(report.blockedReasons.includes("attestation:evidence_sha256_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:evidence_dossier_sha256_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:source_commit_sha_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:release_id_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:operator_reference_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:admin_approver_reference_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:change_ticket_reference_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:rollback_plan_artifact_ref_missing_or_invalid"));
  assert.ok(report.blockedReasons.includes("attestation:post_deployment_checklist_ref_missing_or_invalid"));
});

test("one go-live report blocks operator self-approval by system admin", () => {
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    safeEnv,
    "2026-07-16T00:00:00.000Z",
    {
      ...safeAttestation,
      adminApproverReference: safeAttestation.operatorReference
    }
  );

  assert.equal(report.status, "BLOCKED");
  assert.equal(report.productionReady, false);
  assert.ok(report.blockedReasons.includes("attestation:operator_and_admin_approver_must_be_distinct"));
});

function completeEvidencePackage(): ProductionEvidencePackage {
  return {
    kind: "chronic_care_production_evidence_package",
    generatedAt: "2026-07-16T00:00:00.000Z",
    evidence: productionBlockers.map((blocker) => ({
      blockerId: blocker.id,
      status: "CLEARED",
      reviewedByRole: blocker.owner,
      reviewerReference: `${blocker.owner}_REVIEWER_001`,
      reviewedAt: "2026-07-15T12:00:00.000Z",
      artifactRefs: [`production-readiness/evidence/${blocker.id}.json`],
      controlsVerified: [blocker.evidenceRequired, ...requiredRepositoryControlIdsForBlocker(blocker.id)],
      expiresAt: "2027-07-16T00:00:00.000Z"
    })),
    signoffs: requiredProductionSignoffs.map((role) => ({
      role,
      signerReference: `${role.toUpperCase()}_SIGNER_001`,
      signedAt: "2026-07-15T18:00:00.000Z",
      scope: "production release for chronic care clinic os MVP-01",
      artifactRefs: [`production-readiness/signoffs/${role}.json`]
    }))
  };
}
