import { buildProductionReadinessReport } from "@/lib/production-readiness";
import { buildSecureHeaders } from "@/lib/runtime-hardening";

export const runtime = "nodejs";

export function GET() {
  return Response.json(buildProductionReadinessReport(), {
    headers: buildSecureHeaders({ "Cache-Control": "no-store" })
  });
}
