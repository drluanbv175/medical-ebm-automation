import {
  productionBlockers,
  requiredRepositoryControlIdsForBlocker,
  requiredProductionSignoffs,
  type ProductionEvidencePackage
} from "./production-readiness";

export type ProductionEvidenceTemplateOptions = {
  generatedAt?: string;
  reviewedAt?: string;
  expiresAt?: string;
  scope?: string;
};

export function buildProductionEvidenceTemplate(
  options: ProductionEvidenceTemplateOptions = {}
): ProductionEvidencePackage {
  const generatedAt = options.generatedAt ?? new Date().toISOString();
  const reviewedAt = options.reviewedAt ?? generatedAt;
  const expiresAt = options.expiresAt ?? addOneYearIso(generatedAt);
  const scope = options.scope ?? "TODO production release scope for chronic care clinic os MVP-01";

  return {
    kind: "chronic_care_production_evidence_package",
    generatedAt,
    evidence: productionBlockers.map((blocker) => ({
      blockerId: blocker.id,
      status: "CLEARED",
      reviewedByRole: blocker.owner,
      reviewerReference: `TODO_${blocker.owner}_REVIEWER_REF`,
      reviewedAt,
      artifactRefs: [`TODO/evidence/${blocker.id}.json`],
      controlsVerified: [
        `TODO: ${blocker.evidenceRequired}`,
        ...requiredRepositoryControlIdsForBlocker(blocker.id).map((controlId) => `${controlId}: TODO reviewed artifact`)
      ],
      expiresAt,
      notes: `TODO: attach reviewed evidence for ${blocker.id} - ${blocker.title}`
    })),
    signoffs: requiredProductionSignoffs.map((role) => ({
      role,
      signerReference: `TODO_${role.toUpperCase()}_SIGNER_REF`,
      signedAt: reviewedAt,
      scope,
      artifactRefs: [`TODO/signoffs/${role}.json`]
    }))
  };
}

function addOneYearIso(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  date.setUTCFullYear(date.getUTCFullYear() + 1);
  return date.toISOString();
}
