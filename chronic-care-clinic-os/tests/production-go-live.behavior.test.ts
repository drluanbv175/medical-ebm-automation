import assert from "node:assert/strict";
import test from "node:test";

import { buildProductionEvidenceTemplate } from "../lib/production-evidence-template";
import { buildProductionGoLiveReport } from "../lib/production-go-live";
import {
  productionBlockers,
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
  ALLOWED_ORIGINS: "https://clinic.example.org"
};

test("one go-live report becomes production ready only when evidence env and headers pass together", () => {
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    safeEnv,
    "2026-07-16T00:00:00.000Z"
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
});

test("one go-live report blocks runtime warnings instead of calling production", () => {
  const envWithoutAllowedOrigins = { ...safeEnv, ALLOWED_ORIGINS: undefined };
  const report = buildProductionGoLiveReport(
    completeEvidencePackage(),
    envWithoutAllowedOrigins,
    "2026-07-16T00:00:00.000Z"
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
    "2026-07-16T00:00:00.000Z"
  );

  assert.equal(report.status, "BLOCKED");
  assert.equal(report.productionReady, false);
  assert.ok(report.blockedReasons.some((reason) => reason.startsWith("readiness:open_blocker:")));
  assert.equal(report.emittedHeaders["X-Clinical-Production-Ready"], "false");
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
      controlsVerified: [blocker.evidenceRequired],
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
