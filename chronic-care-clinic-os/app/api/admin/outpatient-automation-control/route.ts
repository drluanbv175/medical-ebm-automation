import { automationRules } from "@/lib/automation";
import { buildOutpatientAutomationControlReport } from "@/lib/outpatient-automation-control";
import { buildSecureHeaders } from "@/lib/runtime-hardening";

export const runtime = "nodejs";

export function GET() {
  // SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 9, phat hien LOW): truoc day goi
  // buildOutpatientAutomationControlReport() KHONG tham so, nen luon dung gia tri mac dinh
  // generatedAt="2026-07-16" (dat de test goi tuong minh), khien isReviewDateCurrent() khong
  // bao gio so voi thoi gian THAT - "review_date_expired" khong the kich hoat qua API song
  // du that su het han. Nay truyen ngay hien tai that (UTC, dinh dang YYYY-MM-DD giong
  // reviewDate cac rule) de tu-kiem phan anh dung thoi gian thuc.
  const generatedAt = new Date().toISOString().slice(0, 10);
  const report = buildOutpatientAutomationControlReport(automationRules, generatedAt);
  return Response.json(report, {
    headers: buildSecureHeaders(
      { "Cache-Control": "no-store" },
      { productionReady: false }
    )
  });
}
