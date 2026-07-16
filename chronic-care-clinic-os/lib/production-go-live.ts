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

export type ProductionGoLiveReport = {
  kind: "chronic_care_production_go_live_report";
  generatedAt: string;
  status: ProductionGoLiveStatus;
  productionReady: boolean;
  blockedReasons: string[];
  readiness: ProductionReadinessReport;
  runtimeEnvironment: RuntimeHardeningDecision;
  secureHeaders: RuntimeHardeningDecision;
  emittedHeaders: Record<string, string>;
  safetyBoundary: string;
};

export function buildProductionGoLiveReport(
  evidencePackage: ProductionEvidencePackage,
  env: Record<string, string | undefined> = process.env,
  generatedAt = new Date().toISOString()
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
    ...secureHeaders.blockedReasons.map((reason) => `secure_headers:${reason}`)
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
    readiness,
    runtimeEnvironment,
    secureHeaders,
    emittedHeaders,
    safetyBoundary: productionReady
      ? "Production-ready for the signed evidence scope and this validated deployment environment."
      : "Blocked: do not use with real patient data until evidence, runtime env and production headers all pass in one go-live run."
  };
}
