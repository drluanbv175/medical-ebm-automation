import { loadProductionEvidencePackageFromEnv } from "@/lib/production-evidence-loader";
import { buildProductionReadinessReport } from "@/lib/production-readiness";
import { buildSecureHeaders } from "@/lib/runtime-hardening";

export const runtime = "nodejs";

export function GET() {
  const evidenceLoad = loadProductionEvidencePackageFromEnv();
  const report = buildProductionReadinessReport(undefined, undefined, evidenceLoad.package);
  if (!evidenceLoad.loaded && evidenceLoad.warnings.length > 0) {
    report.findings.unshift({
      severity: "ERROR",
      code: "production_evidence_package_load_failed",
      message: evidenceLoad.warnings.join(" ")
    });
    if (!report.releaseDecision.blockedReasons.includes("production_evidence_package_load_failed")) {
      report.releaseDecision.blockedReasons.unshift("production_evidence_package_load_failed");
    }
  }
  return Response.json(report, {
    headers: buildSecureHeaders(
      { "Cache-Control": "no-store" },
      { productionReady: report.summary.productionReady }
    )
  });
}
