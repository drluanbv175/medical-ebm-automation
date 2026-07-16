import assert from "node:assert/strict";
import test from "node:test";

import {
  buildProductionReadinessReport,
  type ProductionEvidencePackage,
  openProductionBlockers,
  productionBlockers,
  requiredProductionSignoffs,
  summarizeProductionReadiness
} from "../lib/production-readiness";
import { validateEvidencePackageShape } from "../lib/production-evidence-loader";
import { buildProductionEvidenceTemplate } from "../lib/production-evidence-template";

test("production readiness report is machine-readable and blocks production", () => {
  const report = buildProductionReadinessReport("2026-07-15T00:00:00.000Z");

  assert.equal(report.kind, "chronic_care_production_readiness_report");
  assert.equal(report.generatedAt, "2026-07-15T00:00:00.000Z");
  assert.equal(report.summary.totalBlockers, 24);
  assert.equal(report.summary.openBlockers, 24);
  assert.equal(report.summary.clearedBlockers, 0);
  assert.equal(report.summary.productionReady, false);
  assert.equal(report.releaseDecision.status, "BLOCKED");
  assert.ok(report.releaseDecision.blockedReasons.includes("production_evidence_package_missing"));
  assert.equal(report.evidenceSummary.evidenceRecords, 0);
  assert.equal(report.evidenceSummary.validSignoffs, 0);
  assert.equal(report.evidenceSummary.missingSignoffs.length, 5);
  assert.equal(report.summary.byCategory.security, 8);
  assert.equal(report.summary.byCategory.data_protection, 5);
  assert.equal(report.summary.byCategory.clinical_safety, 6);
  assert.equal(report.summary.byCategory.operations, 4);
  assert.equal(report.summary.byCategory.ai_governance, 1);
  assert.match(report.safetyBoundary, /must not be used with real patient data/);
  assert.deepEqual(report.requiredSignoffs, [
    "security_owner",
    "data_protection_owner",
    "physician_lead",
    "operations_owner",
    "ai_governance_owner"
  ]);
});

test("production blockers require explicit evidence before clearing", () => {
  assert.equal(openProductionBlockers().length, productionBlockers.length);
  assert.ok(productionBlockers.every((item) => item.status === "OPEN"));
  assert.ok(productionBlockers.every((item) => item.blocksProduction === true));
  assert.ok(productionBlockers.every((item) => item.evidenceRequired.length > 20));
});

test("production summary is true only when release evidence explicitly allows it", () => {
  const cleared = productionBlockers.map((item) => ({ ...item, status: "CLEARED" as const }));
  const blockedSummary = summarizeProductionReadiness(cleared);
  const readySummary = summarizeProductionReadiness(cleared, true);

  assert.equal(blockedSummary.totalBlockers, 24);
  assert.equal(blockedSummary.openBlockers, 0);
  assert.equal(blockedSummary.clearedBlockers, 24);
  assert.equal(blockedSummary.productionReady, false);
  assert.equal(readySummary.productionReady, true);
});

test("complete production evidence package can unlock production readiness for signed scope", () => {
  const report = buildProductionReadinessReport(
    "2026-07-16T00:00:00.000Z",
    productionBlockers,
    completeEvidencePackage()
  );

  assert.equal(report.summary.openBlockers, 0);
  assert.equal(report.summary.clearedBlockers, 24);
  assert.equal(report.summary.productionReady, true);
  assert.equal(report.releaseDecision.status, "PRODUCTION_READY");
  assert.deepEqual(report.releaseDecision.blockedReasons, []);
  assert.equal(report.evidenceSummary.validEvidenceRecords, 24);
  assert.equal(report.evidenceSummary.validSignoffs, requiredProductionSignoffs.length);
  assert.equal(report.findings.length, 0);
  assert.match(report.safetyBoundary, /signed scope/);
});

test("production evidence package stays blocked when signoff is missing", () => {
  const pkg = completeEvidencePackage();
  pkg.signoffs = pkg.signoffs.filter((item) => item.role !== "physician_lead");
  const report = buildProductionReadinessReport("2026-07-16T00:00:00.000Z", productionBlockers, pkg);

  assert.equal(report.summary.productionReady, false);
  assert.ok(report.evidenceSummary.missingSignoffs.includes("physician_lead"));
  assert.ok(report.releaseDecision.blockedReasons.includes("missing_signoff:physician_lead"));
});

test("production evidence package stays blocked when blocker evidence is expired", () => {
  const pkg = completeEvidencePackage();
  pkg.evidence[0] = {
    ...pkg.evidence[0],
    expiresAt: "2026-07-15T00:00:00.000Z"
  };
  const report = buildProductionReadinessReport("2026-07-16T00:00:00.000Z", productionBlockers, pkg);

  assert.equal(report.summary.productionReady, false);
  assert.equal(report.blockers[0].status, "OPEN");
  assert.ok(report.releaseDecision.blockedReasons.includes(`open_blocker:${pkg.evidence[0].blockerId}`));
  assert.ok(report.findings.some((item) => item.message.includes("evidence has expired")));
});

test("production evidence template covers all gates but cannot unlock with placeholders", () => {
  const template = buildProductionEvidenceTemplate({
    generatedAt: "2026-07-16T00:00:00.000Z",
    reviewedAt: "2026-07-15T12:00:00.000Z",
    expiresAt: "2027-07-16T00:00:00.000Z"
  });
  const report = buildProductionReadinessReport("2026-07-16T00:00:00.000Z", productionBlockers, template);

  assert.equal(template.evidence.length, productionBlockers.length);
  assert.equal(template.signoffs.length, requiredProductionSignoffs.length);
  assert.equal(report.summary.productionReady, false);
  assert.ok(report.findings.some((item) => item.message.includes("placeholder")));
  assert.ok(report.releaseDecision.blockedReasons.some((item) => item.startsWith("open_blocker:")));
});

test("production evidence validator rejects placeholder references", () => {
  const pkg = completeEvidencePackage();
  pkg.evidence[0] = {
    ...pkg.evidence[0],
    reviewerReference: "TODO_REVIEWER"
  };
  const report = buildProductionReadinessReport("2026-07-16T00:00:00.000Z", productionBlockers, pkg);

  assert.equal(report.summary.productionReady, false);
  assert.ok(report.findings.some((item) => item.message.includes("placeholder")));
});

test("production evidence package shape validator rejects malformed package", () => {
  const warnings = validateEvidencePackageShape({
    kind: "wrong",
    generatedAt: "not-a-date",
    evidence: [],
    signoffs: []
  });

  assert.ok(warnings.some((item) => item.includes("kind must be")));
  assert.ok(warnings.some((item) => item.includes("generatedAt")));
  assert.ok(warnings.some((item) => item.includes("security_owner")));
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
