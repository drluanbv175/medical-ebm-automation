import assert from "node:assert/strict";
import test from "node:test";

import { buildProductionEvidenceDossier } from "../lib/production-evidence-dossier";
import {
  productionBlockers,
  requiredProductionSignoffs,
  requiredRepositoryControlIdsForBlocker,
  type ProductionEvidencePackage
} from "../lib/production-readiness";

test("production evidence dossier creates a full checklist when no package exists", () => {
  const dossier = buildProductionEvidenceDossier(null, "2026-07-16T00:00:00.000Z");

  assert.equal(dossier.kind, "chronic_care_production_evidence_dossier");
  assert.equal(dossier.status, "BLOCKED");
  assert.equal(dossier.readyForFinalGoLiveCheck, false);
  assert.equal(dossier.summary.totalBlockers, productionBlockers.length);
  assert.equal(dossier.summary.validBlockerEvidence, 0);
  assert.equal(dossier.summary.missingBlockerEvidence, productionBlockers.length);
  assert.equal(dossier.summary.missingSignoffs, requiredProductionSignoffs.length);
  assert.ok(dossier.blockedReasons.includes("production_evidence_package_missing"));
  const sec001 = dossier.blockers.find((item) => item.blockerId === "SEC-001");
  assert.ok(sec001);
  assert.equal(sec001.evidenceStatus, "MISSING");
  assert.ok(sec001.requiredRepositoryControlIds.includes("RUNTIME-RBAC-COVERAGE-001"));
  assert.ok(sec001.residualGates.some((item) => item.includes("Route/action coverage")));
  assert.match(dossier.safetyBoundary, /Dossier blocked/);
});

test("production evidence dossier can become ready for final go-live check only after complete evidence", () => {
  const dossier = buildProductionEvidenceDossier(
    completeEvidencePackage(),
    "2026-07-16T00:00:00.000Z"
  );

  assert.equal(dossier.status, "READY_FOR_FINAL_GO_LIVE_CHECK");
  assert.equal(dossier.readyForFinalGoLiveCheck, true);
  assert.equal(dossier.summary.validBlockerEvidence, productionBlockers.length);
  assert.equal(dossier.summary.missingBlockerEvidence, 0);
  assert.equal(dossier.summary.invalidBlockerEvidence, 0);
  assert.equal(dossier.summary.missingRepositoryControlLinks, 0);
  assert.equal(dossier.summary.validSignoffs, requiredProductionSignoffs.length);
  assert.deepEqual(dossier.blockedReasons, []);
  assert.match(dossier.safetyBoundary, /not itself a production approval/);
});

test("production evidence dossier pinpoints missing repository control links", () => {
  const pkg = completeEvidencePackage();
  pkg.evidence = pkg.evidence.map((record) => record.blockerId === "SEC-007"
    ? {
        ...record,
        controlsVerified: record.controlsVerified.filter((controlId) => controlId !== "RUNTIME-DEPENDENCY-SCAN-001")
      }
    : record);

  const dossier = buildProductionEvidenceDossier(pkg, "2026-07-16T00:00:00.000Z");
  const sec007 = dossier.blockers.find((item) => item.blockerId === "SEC-007");

  assert.equal(dossier.status, "BLOCKED");
  assert.equal(dossier.readyForFinalGoLiveCheck, false);
  assert.ok(sec007);
  assert.equal(sec007.evidenceStatus, "INVALID");
  assert.deepEqual(sec007.missingRepositoryControlIds, ["RUNTIME-DEPENDENCY-SCAN-001"]);
  assert.ok(dossier.blockedReasons.includes("invalid_blocker_evidence:SEC-007"));
});

test("production evidence dossier surfaces invalid duplicate signoffs", () => {
  const pkg = completeEvidencePackage();
  pkg.signoffs.push({ ...pkg.signoffs[0], signerReference: "SECURITY_OWNER_SIGNER_002" });

  const dossier = buildProductionEvidenceDossier(pkg, "2026-07-16T00:00:00.000Z");
  const security = dossier.signoffs.find((item) => item.role === "security_owner");

  assert.equal(dossier.status, "BLOCKED");
  assert.equal(dossier.summary.invalidSignoffs, 1);
  assert.ok(security);
  assert.equal(security.status, "INVALID");
  assert.ok(security.findings.some((finding) => finding.message.includes("Duplicate required production signoff")));
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
