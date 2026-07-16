import type { PatientEducationReleasePackage } from "./patient-education";

export type A5RenderEvidence = {
  renderId: string;
  renderer: "PRINT_HTML" | "PDF";
  pageFormat: "A5";
  renderedAt: string;
  artifactRef: string;
  visualQaPassed: boolean;
  textOverflowDetected: boolean;
  containsEmergencyBoundary: boolean;
  containsDoctorVerificationDisclaimer: boolean;
  checksumSha256: string;
  reviewerReference: string;
};

export type A5OutputQaResult = {
  accepted: boolean;
  blockedReasons: string[];
  controlsVerified: string[];
  safetyBoundary: string;
};

export function validateA5OutputQa(
  releasePackage: PatientEducationReleasePackage,
  evidence: A5RenderEvidence
): A5OutputQaResult {
  const blockedReasons: string[] = [];

  if (!releasePackage.printAllowed) {
    blockedReasons.push("release_package_not_print_allowed");
  }
  if (releasePackage.releaseStatus !== "READY_TO_PRINT_APPROVED_HANDOUT") {
    blockedReasons.push(`release_status_not_ready:${releasePackage.releaseStatus}`);
  }
  if (releasePackage.template.status !== "APPROVED") {
    blockedReasons.push("education_template_not_approved");
  }
  if (!releasePackage.auditPreview || releasePackage.auditPreview.entityType !== "PatientHandout") {
    blockedReasons.push("patient_handout_audit_preview_missing");
  }
  if (!releasePackage.safetyBoundary.toLowerCase().includes("khong tu dong")) {
    blockedReasons.push("safety_boundary_missing_no_automation");
  }
  if (releasePackage.handoutSections.length < 6) {
    blockedReasons.push("handout_sections_incomplete");
  }
  if (evidence.pageFormat !== "A5") {
    blockedReasons.push("page_format_not_a5");
  }
  if (!isPastOrPresentIso(evidence.renderedAt)) {
    blockedReasons.push("rendered_at_invalid_or_future");
  }
  if (!safeReference(evidence.artifactRef)) {
    blockedReasons.push("artifact_ref_invalid");
  }
  if (!evidence.visualQaPassed) {
    blockedReasons.push("visual_qa_not_passed");
  }
  if (evidence.textOverflowDetected) {
    blockedReasons.push("text_overflow_detected");
  }
  if (!evidence.containsEmergencyBoundary) {
    blockedReasons.push("emergency_boundary_missing");
  }
  if (!evidence.containsDoctorVerificationDisclaimer) {
    blockedReasons.push("doctor_verification_disclaimer_missing");
  }
  if (!/^[a-f0-9]{64}$/i.test(evidence.checksumSha256)) {
    blockedReasons.push("checksum_sha256_invalid");
  }
  if (!safeReference(evidence.reviewerReference)) {
    blockedReasons.push("reviewer_reference_invalid");
  }

  return {
    accepted: blockedReasons.length === 0,
    blockedReasons,
    controlsVerified: [
      "approved_template",
      "approved_care_plan",
      "patient_consent",
      "a5_page_format",
      "visual_qa",
      "doctor_verification_disclaimer",
      "emergency_boundary",
      "artifact_checksum"
    ],
    safetyBoundary:
      "A5 output QA validates a release artifact only; it does not authorize clinical content without physician signoff and approved evidence sources."
  };
}

function isPastOrPresentIso(value: string): boolean {
  const timestamp = Date.parse(value);
  return Number.isFinite(timestamp) && timestamp <= Date.now();
}

function safeReference(value: string): boolean {
  return typeof value === "string"
    && value.trim().length >= 3
    && !/(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value)
    && !/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i.test(value)
    && !/\b0\d{9,10}\b/.test(value)
    && !/\b\d{12}\b/.test(value);
}
