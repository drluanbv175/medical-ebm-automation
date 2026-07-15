import { buildEvidenceBridgeSnapshot } from "@/lib/evidence-integration";

export const runtime = "nodejs";

export function GET() {
  return Response.json(buildEvidenceBridgeSnapshot(), {
    headers: {
      "Cache-Control": "no-store"
    }
  });
}
