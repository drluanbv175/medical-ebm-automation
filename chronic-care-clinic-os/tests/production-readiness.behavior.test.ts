import assert from "node:assert/strict";
import test from "node:test";

import {
  buildProductionReadinessReport,
  openProductionBlockers,
  productionBlockers,
  summarizeProductionReadiness
} from "../lib/production-readiness";

test("production readiness report is machine-readable and blocks production", () => {
  const report = buildProductionReadinessReport("2026-07-15T00:00:00.000Z");

  assert.equal(report.kind, "chronic_care_production_readiness_report");
  assert.equal(report.generatedAt, "2026-07-15T00:00:00.000Z");
  assert.equal(report.summary.totalBlockers, 24);
  assert.equal(report.summary.openBlockers, 24);
  assert.equal(report.summary.clearedBlockers, 0);
  assert.equal(report.summary.productionReady, false);
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

test("production summary remains blocked even with custom cleared input", () => {
  const cleared = productionBlockers.map((item) => ({ ...item, status: "CLEARED" as const }));
  const summary = summarizeProductionReadiness(cleared);

  assert.equal(summary.totalBlockers, 24);
  assert.equal(summary.openBlockers, 0);
  assert.equal(summary.clearedBlockers, 24);
  assert.equal(summary.productionReady, false);
});
