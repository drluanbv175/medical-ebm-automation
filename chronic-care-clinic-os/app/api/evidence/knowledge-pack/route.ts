import { buildEvidenceBridgeSnapshot } from "@/lib/evidence-integration";
import { buildSecureHeaders } from "@/lib/runtime-hardening";

export const runtime = "nodejs";

export function GET() {
  return Response.json(buildEvidenceBridgeSnapshot(), {
    headers: buildSecureHeaders({ "Cache-Control": "no-store" })
  });
}
