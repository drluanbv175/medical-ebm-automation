import {
  buildProductionReadinessReport,
  productionBlockers,
  repositoryControlsForProductionBlocker,
  requiredProductionSignoffs,
  requiredRepositoryControlIdsForBlocker,
  type ProductionBlocker,
  type ProductionEvidencePackage,
  type ProductionEvidenceRecord,
  type ProductionReadinessFinding,
  type ProductionReadinessReport,
  type ProductionSignoff,
  type ProductionSignoffRole
} from "./production-readiness";
import { runtimeHardeningControls, type RuntimeHardeningControlEvidence } from "./runtime-hardening";

export type ProductionDossierStatus = "BLOCKED" | "READY_FOR_FINAL_GO_LIVE_CHECK";
export type ProductionDossierItemStatus = "MISSING" | "INVALID" | "VALID";

export type ProductionEvidenceDossierBlocker = {
  blockerId: string;
  category: ProductionBlocker["category"];
  title: string;
  owner: ProductionBlocker["owner"];
  evidenceRequired: string;
  blockerStatus: ProductionBlocker["status"];
  evidenceStatus: ProductionDossierItemStatus;
  reviewedByRole: ProductionBlocker["owner"] | null;
  reviewerReference: string | null;
  artifactRefs: string[];
  controlsVerified: string[];
  requiredRepositoryControlIds: string[];
  missingRepositoryControlIds: string[];
  residualGates: string[];
  findings: ProductionReadinessFinding[];
};

export type ProductionEvidenceDossierSignoff = {
  role: ProductionSignoffRole;
  status: ProductionDossierItemStatus;
  signerReference: string | null;
  signedAt: string | null;
  scope: string | null;
  artifactRefs: string[];
  findings: ProductionReadinessFinding[];
};

export type ProductionEvidenceDossierSummary = {
  totalBlockers: number;
  validBlockerEvidence: number;
  missingBlockerEvidence: number;
  invalidBlockerEvidence: number;
  requiredRepositoryControls: number;
  missingRepositoryControlLinks: number;
  validSignoffs: number;
  missingSignoffs: number;
  invalidSignoffs: number;
};

export type ProductionEvidenceDossier = {
  kind: "chronic_care_production_evidence_dossier";
  generatedAt: string;
  status: ProductionDossierStatus;
  readyForFinalGoLiveCheck: boolean;
  summary: ProductionEvidenceDossierSummary;
  blockers: ProductionEvidenceDossierBlocker[];
  signoffs: ProductionEvidenceDossierSignoff[];
  readiness: ProductionReadinessReport;
  repositoryControlsOutsideProductionBlockers: RuntimeHardeningControlEvidence[];
  blockedReasons: string[];
  safetyBoundary: string;
};

export function buildProductionEvidenceDossier(
  evidencePackage: ProductionEvidencePackage | null = null,
  generatedAt = new Date().toISOString()
): ProductionEvidenceDossier {
  const readiness = buildProductionReadinessReport(generatedAt, productionBlockers, evidencePackage);
  const evidenceByBlocker = new Map<string, ProductionEvidenceRecord>();
  for (const record of evidencePackage?.evidence ?? []) {
    if (!evidenceByBlocker.has(record.blockerId)) {
      evidenceByBlocker.set(record.blockerId, record);
    }
  }
  const blockerItems = readiness.blockers.map((blocker) => buildBlockerDossierItem(
    blocker,
    evidenceByBlocker.get(blocker.id) ?? null,
    readiness.findings
  ));
  const signoffItems = requiredProductionSignoffs.map((role) => buildSignoffDossierItem(
    role,
    evidencePackage?.signoffs.find((item) => item.role === role) ?? null,
    readiness.findings
  ));
  const summary = summarizeDossier(blockerItems, signoffItems);
  const blockedReasons = [
    ...readiness.releaseDecision.blockedReasons,
    ...(summary.missingRepositoryControlLinks > 0 ? ["missing_repository_control_links"] : []),
    ...(summary.invalidSignoffs > 0 ? ["invalid_signoff_records"] : [])
  ];
  const uniqueBlockedReasons = Array.from(new Set(blockedReasons));
  const readyForFinalGoLiveCheck = readiness.releaseDecision.productionReady
    && summary.missingRepositoryControlLinks === 0
    && summary.invalidSignoffs === 0
    && uniqueBlockedReasons.length === 0;

  return {
    kind: "chronic_care_production_evidence_dossier",
    generatedAt,
    status: readyForFinalGoLiveCheck ? "READY_FOR_FINAL_GO_LIVE_CHECK" : "BLOCKED",
    readyForFinalGoLiveCheck,
    summary,
    blockers: blockerItems,
    signoffs: signoffItems,
    readiness,
    repositoryControlsOutsideProductionBlockers: runtimeHardeningControls.filter(
      (control) => !control.blockerIds.some((blockerId) => productionBlockers.some((blocker) => blocker.id === blockerId))
    ),
    blockedReasons: uniqueBlockedReasons,
    safetyBoundary: readyForFinalGoLiveCheck
      ? "Evidence dossier is complete enough to run the final go-live gate; it is not itself a production approval."
      : "Dossier blocked: collect reviewed artifacts, repository control IDs and required signoffs before final go-live."
  };
}

function buildBlockerDossierItem(
  blocker: ProductionBlocker,
  evidence: ProductionEvidenceRecord | null,
  findings: ProductionReadinessFinding[]
): ProductionEvidenceDossierBlocker {
  const blockerFindings = findings.filter((finding) => finding.blockerId === blocker.id);
  const requiredRepositoryControlIds = requiredRepositoryControlIdsForBlocker(blocker.id);
  const controlsVerified = evidence?.controlsVerified ?? [];
  const missingRepositoryControlIds = requiredRepositoryControlIds.filter((controlId) => !controlsVerified.includes(controlId));
  const evidenceStatus = !evidence
    ? "MISSING"
    : (blockerFindings.length > 0 || missingRepositoryControlIds.length > 0 ? "INVALID" : "VALID");
  const residualGates = repositoryControlsForProductionBlocker(blocker.id).map((control) => control.residualGate);

  return {
    blockerId: blocker.id,
    category: blocker.category,
    title: blocker.title,
    owner: blocker.owner,
    evidenceRequired: blocker.evidenceRequired,
    blockerStatus: blocker.status,
    evidenceStatus,
    reviewedByRole: evidence?.reviewedByRole ?? null,
    reviewerReference: evidence?.reviewerReference ?? null,
    artifactRefs: evidence?.artifactRefs ?? [],
    controlsVerified,
    requiredRepositoryControlIds,
    missingRepositoryControlIds,
    residualGates,
    findings: blockerFindings
  };
}

function buildSignoffDossierItem(
  role: ProductionSignoffRole,
  signoff: ProductionSignoff | null,
  findings: ProductionReadinessFinding[]
): ProductionEvidenceDossierSignoff {
  const roleFindings = findings.filter((finding) => finding.message.includes(role));
  const missing = findings.some(
    (finding) => finding.code === "missing_required_signoff" && finding.message.includes(role)
  );
  return {
    role,
    status: !signoff || missing ? "MISSING" : (roleFindings.length > 0 ? "INVALID" : "VALID"),
    signerReference: signoff?.signerReference ?? null,
    signedAt: signoff?.signedAt ?? null,
    scope: signoff?.scope ?? null,
    artifactRefs: signoff?.artifactRefs ?? [],
    findings: roleFindings
  };
}

function summarizeDossier(
  blockers: ProductionEvidenceDossierBlocker[],
  signoffs: ProductionEvidenceDossierSignoff[]
): ProductionEvidenceDossierSummary {
  return {
    totalBlockers: blockers.length,
    validBlockerEvidence: blockers.filter((item) => item.evidenceStatus === "VALID").length,
    missingBlockerEvidence: blockers.filter((item) => item.evidenceStatus === "MISSING").length,
    invalidBlockerEvidence: blockers.filter((item) => item.evidenceStatus === "INVALID").length,
    requiredRepositoryControls: blockers.reduce((sum, item) => sum + item.requiredRepositoryControlIds.length, 0),
    missingRepositoryControlLinks: blockers.reduce((sum, item) => sum + item.missingRepositoryControlIds.length, 0),
    validSignoffs: signoffs.filter((item) => item.status === "VALID").length,
    missingSignoffs: signoffs.filter((item) => item.status === "MISSING").length,
    invalidSignoffs: signoffs.filter((item) => item.status === "INVALID").length
  };
}
