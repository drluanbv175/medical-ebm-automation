import assert from "node:assert/strict";
import test from "node:test";

import type { AuditEvent } from "../lib/audit";
import { assertAiDraftsEnabled, isAiDraftsEnabled } from "../lib/ai-guard";
import { buildProductionReadinessReport } from "../lib/production-readiness";
import {
  buildSecureHeaders,
  evaluatePatientCommunicationPolicy,
  evaluateRequestSecurityControls,
  runtimeHardeningControls,
  sanitizeAuditEventForPersistence,
  validateProductionRuntimeEnvironment,
  validateSecureHeaders
} from "../lib/runtime-hardening";

const safeEnv = {
  NODE_ENV: "production",
  DATABASE_URL: "postgresql://app:secret@db.example.internal:5432/clinic",
  APP_BASE_URL: "https://clinic.example.org",
  NEXTAUTH_SECRET: "12345678901234567890123456789012",
  CSRF_SECRET: "abcdefabcdefabcdefabcdefabcdefabcd",
  AI_DRAFTS_ENABLED: "false",
  SESSION_COOKIE_SECURE: "true",
  RATE_LIMIT_ENABLED: "true",
  RATE_LIMIT_MAX: "120",
  RATE_LIMIT_WINDOW_SECONDS: "60",
  SECURITY_HEADERS_ENABLED: "true",
  AUDIT_LOG_REDACTION_ENABLED: "true",
  PATIENT_COMMUNICATIONS_ENABLED: "true",
  PATIENT_COMMUNICATION_POLICY_VERSION: "repo-policy-2026-07-16",
  ALLOWED_ORIGINS: "https://clinic.example.org"
};

test("production runtime environment gate passes only the technical contract and never claims production readiness", () => {
  const decision = validateProductionRuntimeEnvironment(safeEnv);

  assert.equal(decision.allowed, true);
  assert.equal(decision.productionReady, false);
  assert.equal(decision.status, "PASS_WITH_HUMAN_GATES");
  assert.deepEqual(decision.blockedReasons, []);
  assert.match(decision.safetyBoundary, /human signoff/);
});

test("production runtime environment gate blocks unsafe production configuration", () => {
  const decision = validateProductionRuntimeEnvironment({
    ...safeEnv,
    APP_BASE_URL: "http://clinic.example.org",
    AI_DRAFTS_ENABLED: "true",
    AUDIT_LOG_REDACTION_ENABLED: "false",
    NEXTAUTH_SECRET: "short"
  });

  assert.equal(decision.allowed, false);
  assert.ok(decision.blockedReasons.includes("https_url_required:APP_BASE_URL"));
  assert.ok(decision.blockedReasons.includes("ai_drafts_must_remain_disabled"));
  assert.ok(decision.blockedReasons.includes("audit_log_redaction_not_enabled"));
  assert.ok(decision.blockedReasons.includes("weak_or_missing_secret:NEXTAUTH_SECRET"));
});

test("AI draft circuit breaker blocks future LLM call sites unless explicitly enabled", () => {
  const previous = process.env.AI_DRAFTS_ENABLED;
  try {
    process.env.AI_DRAFTS_ENABLED = "false";
    assert.equal(isAiDraftsEnabled(), false);
    assert.throws(
      () => assertAiDraftsEnabled("synthetic-care-plan-draft"),
      /AI drafting is disabled/
    );

    process.env.AI_DRAFTS_ENABLED = "true";
    assert.equal(isAiDraftsEnabled(), true);
    assert.doesNotThrow(() => assertAiDraftsEnabled("synthetic-care-plan-draft"));
  } finally {
    if (previous === undefined) {
      delete process.env.AI_DRAFTS_ENABLED;
    } else {
      process.env.AI_DRAFTS_ENABLED = previous;
    }
  }
});

test("secure header policy validates API and page hardening headers", () => {
  const headers = buildSecureHeaders({ "Cache-Control": "no-store" });
  const decision = validateSecureHeaders(headers);

  assert.equal(headers["X-Clinical-Production-Ready"], "false");
  assert.equal(decision.allowed, true);
  assert.deepEqual(decision.blockedReasons, []);

  const broken = validateSecureHeaders({ ...headers, "Content-Security-Policy": "default-src 'self'" });
  assert.equal(broken.allowed, false);
  assert.ok(broken.blockedReasons.includes("csp_missing_directive:frame-ancestors 'none'"));
});

test("clinical production readiness header follows signed production decision", () => {
  const readyHeaders = buildSecureHeaders(
    { "Cache-Control": "no-store" },
    { productionReady: true }
  );
  const blockedHeaders = buildSecureHeaders(
    { "Cache-Control": "no-store" },
    { productionReady: false }
  );

  assert.equal(readyHeaders["X-Clinical-Production-Ready"], "true");
  assert.equal(blockedHeaders["X-Clinical-Production-Ready"], "false");
  assert.equal(validateSecureHeaders(readyHeaders, { productionReady: true }).allowed, true);
  assert.equal(validateSecureHeaders(readyHeaders).allowed, false);
});

test("request security guard blocks unsafe writes without actor, CSRF and rate-limit evidence", () => {
  const blocked = evaluateRequestSecurityControls({
    method: "POST",
    path: "/api/patients",
    origin: "https://clinic.example.org",
    allowedOrigins: ["https://clinic.example.org"],
    authenticatedActorId: null,
    csrfTokenPresent: false,
    csrfCookiePresent: false,
    rateLimitRemaining: 0
  });

  assert.equal(blocked.allowed, false);
  assert.ok(blocked.blockedReasons.includes("missing_authenticated_actor"));
  assert.ok(blocked.blockedReasons.includes("csrf_double_submit_missing"));
  assert.ok(blocked.blockedReasons.includes("rate_limit_exceeded"));

  const readOnly = evaluateRequestSecurityControls({
    method: "GET",
    path: "/api/admin/production-readiness",
    origin: "https://clinic.example.org",
    allowedOrigins: ["https://clinic.example.org"],
    authenticatedActorId: "user-001"
  });
  assert.equal(readOnly.allowed, true);
});

test("audit persistence sanitizer redacts PHI and PII before storage", () => {
  const event: AuditEvent = {
    id: "audit-phi-001",
    actor: "staff@example.org",
    actorRole: "PHYSICIAN",
    actionType: "UPDATE",
    entityType: "Patient",
    entityId: "MRN 2026-00001",
    summary: "Patient phone 0912345678, CCCD 012345678901, DOB 01/02/1970",
    createdAt: "2026-07-16T00:00:00+07:00"
  };

  const envelope = sanitizeAuditEventForPersistence(event, {
    beforeData: { phone: "0912345678" },
    afterData: { email: "patient@example.org", record: "BHYT DN123456" }
  });
  const serialized = JSON.stringify(envelope);

  assert.equal(envelope.persistenceAllowed, true);
  assert.equal(envelope.redactionApplied, true);
  assert.ok(envelope.redactedFields.length >= 5);
  assert.doesNotMatch(serialized, /0912345678/);
  assert.doesNotMatch(serialized, /012345678901/);
  assert.doesNotMatch(serialized, /patient@example\.org/);
  assert.match(serialized, /\[REDACTED_PHONE\]/);
});

test("audit persistence blocks when redaction is disabled", () => {
  const event: AuditEvent = {
    id: "audit-phi-002",
    actor: "Dr Test",
    actorRole: "PHYSICIAN",
    actionType: "VIEW",
    entityType: "Patient",
    entityId: "patient-001",
    summary: "View chart.",
    createdAt: "2026-07-16T00:00:00+07:00"
  };

  const envelope = sanitizeAuditEventForPersistence(event, {}, { redactionEnabled: false });

  assert.equal(envelope.persistenceAllowed, false);
  assert.deepEqual(envelope.blockedReasons, ["audit_redaction_disabled"]);
  assert.equal(envelope.redactedEvent, null);
});

test("patient communication policy allows only consented physician-approved non-treatment communication", () => {
  const allowed = evaluatePatientCommunicationPolicy({
    messageType: "APPROVED_EDUCATION_READY",
    hasApprovedTemplate: true,
    hasConsent: true,
    physicianApproved: true,
    redFlagActive: false,
    includesTreatmentInstruction: false,
    policyVersion: "repo-policy-2026-07-16",
    channel: "PRINTED_HANDOUT"
  });

  assert.equal(allowed.allowed, true);
  assert.equal(allowed.productionReady, false);

  const blocked = evaluatePatientCommunicationPolicy({
    messageType: "APPROVED_EDUCATION_READY",
    hasApprovedTemplate: true,
    hasConsent: true,
    physicianApproved: false,
    redFlagActive: true,
    includesTreatmentInstruction: true,
    policyVersion: null,
    channel: "SMS"
  });

  assert.equal(blocked.allowed, false);
  assert.ok(blocked.blockedReasons.includes("physician_approval_missing"));
  assert.ok(blocked.blockedReasons.includes("red_flag_blocks_patient_communication"));
  assert.ok(blocked.blockedReasons.includes("treatment_instruction_messages_not_allowed"));
  assert.ok(blocked.blockedReasons.includes("channel_not_allowed:SMS"));
});

test("production readiness report surfaces repository hardening controls without unlocking production", () => {
  const report = buildProductionReadinessReport("2026-07-16T00:00:00.000Z");

  assert.equal(report.summary.productionReady, false);
  assert.equal(report.repositoryControls.length, runtimeHardeningControls.length);
  assert.ok(report.repositoryControls.some((item) => item.blockerIds.includes("SEC-008")));
  assert.ok(report.repositoryControls.some((item) => item.blockerIds.includes("DATA-003")));
  assert.ok(report.repositoryControls.some((item) => item.blockerIds.includes("AI-001")));
  assert.ok(report.repositoryControls.every((item) => item.implementationStatus === "REPO_CONTRACT_READY"));
});
