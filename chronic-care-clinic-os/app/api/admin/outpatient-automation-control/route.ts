import { buildOutpatientAutomationControlReport } from "@/lib/outpatient-automation-control";
import { buildSecureHeaders } from "@/lib/runtime-hardening";

export const runtime = "nodejs";

export function GET() {
  const report = buildOutpatientAutomationControlReport();
  return Response.json(report, {
    headers: buildSecureHeaders(
      { "Cache-Control": "no-store" },
      { productionReady: false }
    )
  });
}
