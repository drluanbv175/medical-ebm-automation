import { buildProductionReadinessReport } from "@/lib/production-readiness";

export const runtime = "nodejs";

export function GET() {
  return Response.json(buildProductionReadinessReport(), {
    headers: {
      "Cache-Control": "no-store",
      "X-Clinical-Production-Ready": "false"
    }
  });
}
