import {
  buildProductionReadinessReport,
  type ProductionEvidencePackage,
  type ProductionReadinessReport
} from "./production-readiness";
import {
  buildSecureHeaders,
  validateProductionRuntimeEnvironment,
  validateSecureHeaders,
  type RuntimeHardeningDecision
} from "./runtime-hardening";

export type ProductionGoLiveStatus = "BLOCKED" | "PRODUCTION_READY";

export type ProductionGoLiveAttestation = {
  evidenceSha256: string | null;
  evidencePath: string | null;
  sourceCommitSha: string | null;
  releaseId: string | null;
  operatorReference: string | null;
};

export type ProductionGoLiveReport = {
  kind: "chronic_care_production_go_live_report";
  generatedAt: string;
  status: ProductionGoLiveStatus;
  productionReady: boolean;
  blockedReasons: string[];
  attestation: ProductionGoLiveAttestation;
  readiness: ProductionReadinessReport;
  runtimeEnvironment: RuntimeHardeningDecision;
  secureHeaders: RuntimeHardeningDecision;
  emittedHeaders: Record<string, string>;
  safetyBoundary: string;
};

export function buildProductionGoLiveReport(
  evidencePackage: ProductionEvidencePackage,
  env: Record<string, string | undefined> = process.env,
  generatedAt = new Date().toISOString(),
  attestation: ProductionGoLiveAttestation = {
    evidenceSha256: null,
    evidencePath: null,
    sourceCommitSha: env.SOURCE_COMMIT_SHA ?? null,
    releaseId: env.PRODUCTION_RELEASE_ID ?? null,
    operatorReference: env.PRODUCTION_OPERATOR_REF ?? null
  }
): ProductionGoLiveReport {
  const readiness = buildProductionReadinessReport(generatedAt, undefined, evidencePackage);
  const runtimeEnvironment = validateProductionRuntimeEnvironment(env);
  const emittedHeaders = buildSecureHeaders(
    { "Cache-Control": "no-store" },
    { productionReady: readiness.summary.productionReady }
  );
  const secureHeaders = validateSecureHeaders(
    emittedHeaders,
    { productionReady: readiness.summary.productionReady }
  );

  const blockedReasons = [
    ...readiness.releaseDecision.blockedReasons.map((reason) => `readiness:${reason}`),
    ...runtimeEnvironment.blockedReasons.map((reason) => `runtime_env:${reason}`),
    ...runtimeEnvironment.warnings.map((warning) => `runtime_env_warning:${warning}`),
    ...secureHeaders.blockedReasons.map((reason) => `secure_headers:${reason}`),
    ...validateAttestation(attestation).map((reason) => `attestation:${reason}`)
  ];
  const productionReady = readiness.summary.productionReady
    && runtimeEnvironment.allowed
    && runtimeEnvironment.warnings.length === 0
    && secureHeaders.allowed
    && blockedReasons.length === 0;

  return {
    kind: "chronic_care_production_go_live_report",
    generatedAt,
    status: productionReady ? "PRODUCTION_READY" : "BLOCKED",
    productionReady,
    blockedReasons,
    attestation,
    readiness,
    runtimeEnvironment,
    secureHeaders,
    emittedHeaders,
    safetyBoundary: productionReady
      ? "Production-ready for the signed evidence scope and this validated deployment environment."
      : "Blocked: do not use with real patient data until evidence, runtime env and production headers all pass in one go-live run."
  };
}

function validateAttestation(attestation: ProductionGoLiveAttestation): string[] {
  const reasons: string[] = [];
  if (!attestation.evidenceSha256 || !/^[a-f0-9]{64}$/i.test(attestation.evidenceSha256)) {
    reasons.push("evidence_sha256_missing_or_invalid");
  }
  if (!attestation.sourceCommitSha || !/^[a-f0-9]{7,40}$/i.test(attestation.sourceCommitSha)) {
    reasons.push("source_commit_sha_missing_or_invalid");
  }
  if (!safeOpaqueReference(attestation.releaseId)) {
    reasons.push("release_id_missing_or_invalid");
  }
  if (!safeOpaqueReference(attestation.operatorReference)) {
    reasons.push("operator_reference_missing_or_invalid");
  }
  if (attestation.evidencePath && containsPlaceholder(attestation.evidencePath)) {
    reasons.push("evidence_path_placeholder");
  }
  return reasons;
}

function safeOpaqueReference(value: string | null): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !containsPlaceholder(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}

function containsPlaceholder(value: string): boolean {
  return /(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value);
}
