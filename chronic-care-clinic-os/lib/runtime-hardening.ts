import type { AuditEvent } from "./audit";
import { isPatientCommunicationAllowed } from "./automation";

export type RuntimeHardeningDecision = {
  allowed: boolean;
  productionReady: false;
  status: "PASS_WITH_HUMAN_GATES" | "BLOCKED";
  blockedReasons: string[];
  warnings: string[];
  controls: string[];
  safetyBoundary: string;
};

export type RuntimeHardeningControlEvidence = {
  controlId: string;
  blockerIds: string[];
  implementationStatus: "REPO_CONTRACT_READY";
  files: string[];
  residualGate: string;
};

export const runtimeHardeningControls: RuntimeHardeningControlEvidence[] = [
  {
    controlId: "RUNTIME-ENV-001",
    blockerIds: ["SEC-006"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/runtime-hardening.ts", "tests/runtime-hardening.behavior.test.ts"],
    residualGate: "Deployment owner must run this gate with real production env and sign the evidence."
  },
  {
    controlId: "RUNTIME-HEADERS-001",
    blockerIds: ["SEC-005"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/runtime-hardening.ts", "next.config.mjs", "app/api/admin/production-readiness/route.ts"],
    residualGate: "External header scan is still required after deployment."
  },
  {
    controlId: "RUNTIME-WRITE-GUARD-001",
    blockerIds: ["SEC-004"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/runtime-hardening.ts", "tests/runtime-hardening.behavior.test.ts"],
    residualGate: "Every future write route must call this guard before persistence is enabled."
  },
  {
    controlId: "RUNTIME-PHI-LOG-001",
    blockerIds: ["SEC-008"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/runtime-hardening.ts", "tests/runtime-hardening.behavior.test.ts"],
    residualGate: "Reviewer must inspect persisted logs from a de-identified UAT run."
  },
  {
    controlId: "RUNTIME-PATIENT-COMM-001",
    blockerIds: ["CLIN-003", "PHASE3A-PATIENT-COMMUNICATION-POLICY"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/runtime-hardening.ts", "PATIENT_COMMUNICATION_POLICY.md", "tests/runtime-hardening.behavior.test.ts"],
    residualGate: "Clinic leadership must approve the policy before real patient communication."
  },
  {
    controlId: "RUNTIME-PASSWORD-001",
    blockerIds: ["SEC-003"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/password-security.ts", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "Production auth/session/MFA workflow must wire this hash contract before real credentials are allowed."
  },
  {
    controlId: "RUNTIME-RETENTION-001",
    blockerIds: ["DATA-004"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/data-retention.ts", "DATA_RETENTION_POLICY.md", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "Data protection owner must approve retention scope and archive/delete evidence."
  },
  {
    controlId: "RUNTIME-BACKUP-RESTORE-001",
    blockerIds: ["DATA-002"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/operations-readiness.ts", "docs/deployment/backup-restore.md", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "A real staging/production restore drill report is still required before go-live."
  },
  {
    controlId: "RUNTIME-A5-QA-001",
    blockerIds: ["CLIN-004"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/a5-output-qa.ts", "app/handouts/page.tsx", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "Rendered A5/PDF artifact must be reviewed by physician lead before patient use."
  },
  {
    controlId: "RUNTIME-MONITORING-001",
    blockerIds: ["OPS-003"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/operations-readiness.ts", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "Deployment monitoring smoke report and on-call route evidence are still required."
  },
  {
    controlId: "RUNTIME-INCIDENT-DRILL-001",
    blockerIds: ["OPS-004"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/operations-readiness.ts", "security/INCIDENT_RESPONSE_PLAYBOOK.md", "tests/production-control-contracts.behavior.test.ts"],
    residualGate: "Clinical safety/data protection/operations tabletop drill must be signed before go-live."
  },
  {
    controlId: "RUNTIME-RBAC-COVERAGE-001",
    blockerIds: ["SEC-001"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "lib/write-action-registry.ts", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Route/action coverage must be reviewed against the deployed build before go-live."
  },
  {
    controlId: "RUNTIME-DEPENDENCY-SCAN-001",
    blockerIds: ["SEC-007"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "pnpm-lock.yaml", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Security owner must attach a reviewed vulnerability scan artifact for the exact lockfile hash."
  },
  {
    controlId: "RUNTIME-PRISMA-MIGRATION-001",
    blockerIds: ["OPS-002"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "prisma/migrations", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Operations owner must sign migration smoke and rollback evidence before production migration."
  },
  {
    controlId: "RUNTIME-SITE-ISOLATION-001",
    blockerIds: ["DATA-001"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "lib/backend-guard.ts", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Cross-organization and cross-site denial must be verified in deployed runtime/UAT."
  },
  {
    controlId: "RUNTIME-DOCKER-SMOKE-001",
    blockerIds: ["OPS-001"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "docker-compose.yml", "Dockerfile", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Operations owner must attach fresh-machine Docker run evidence for the target environment."
  },
  {
    controlId: "RUNTIME-GOVERNANCE-PERSISTENCE-001",
    blockerIds: ["PHASE3A-LIVE-GOVERNANCE-PERSISTENCE"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: ["lib/production-go-live-controls.ts", "prisma/schema.prisma", "tests/production-go-live-controls.behavior.test.ts"],
    residualGate: "Live governance tables need migration, backup and append-only audit evidence before production."
  },
  {
    controlId: "RUNTIME-OUTPATIENT-AUTOMATION-001",
    blockerIds: ["CLIN-002", "CLIN-003"],
    implementationStatus: "REPO_CONTRACT_READY",
    files: [
      "lib/outpatient-automation-control.ts",
      "app/api/admin/outpatient-automation-control/route.ts",
      "app/admin/settings/page.tsx",
      "tests/outpatient-automation-control.behavior.test.ts"
    ],
    residualGate: "Clinic leadership must review automation rules, patient-facing templates, consent workflow and escalation evidence before real outpatient use."
  }
];

export const secureHeaderPolicy = {
  "Content-Security-Policy":
    "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'",
  "Referrer-Policy": "strict-origin-when-cross-origin",
  "X-Content-Type-Options": "nosniff",
  "X-Frame-Options": "DENY",
  "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
  "Cross-Origin-Opener-Policy": "same-origin",
  "X-Clinical-Production-Ready": "false"
} as const;

type RuntimeEnvironment = Record<string, string | undefined>;

export function validateProductionRuntimeEnvironment(env: RuntimeEnvironment): RuntimeHardeningDecision {
  const blockedReasons: string[] = [];
  const warnings: string[] = [];

  if (env.NODE_ENV !== "production") {
    blockedReasons.push("node_env_not_production");
  }
  requirePresent(env, "DATABASE_URL", blockedReasons);
  requireHttpsUrl(env, "APP_BASE_URL", blockedReasons);
  requireSecret(env, "NEXTAUTH_SECRET", blockedReasons);
  requireSecret(env, "CSRF_SECRET", blockedReasons);

  if (isEnabled(env.AI_DRAFTS_ENABLED)) {
    blockedReasons.push("ai_drafts_must_remain_disabled");
  }
  if (!isEnabled(env.SESSION_COOKIE_SECURE)) {
    blockedReasons.push("session_cookie_secure_not_enabled");
  }
  if (!isEnabled(env.RATE_LIMIT_ENABLED)) {
    blockedReasons.push("rate_limit_not_enabled");
  }
  requireNumberInRange(env, "RATE_LIMIT_MAX", 1, 600, blockedReasons);
  requireNumberInRange(env, "RATE_LIMIT_WINDOW_SECONDS", 1, 3600, blockedReasons);
  if (!isEnabled(env.SECURITY_HEADERS_ENABLED)) {
    blockedReasons.push("security_headers_not_enabled");
  }
  if (!isEnabled(env.AUDIT_LOG_REDACTION_ENABLED)) {
    blockedReasons.push("audit_log_redaction_not_enabled");
  }
  if (isEnabled(env.PATIENT_COMMUNICATIONS_ENABLED) && !env.PATIENT_COMMUNICATION_POLICY_VERSION) {
    blockedReasons.push("patient_communication_policy_version_missing");
  }
  if (!env.ALLOWED_ORIGINS) {
    warnings.push("allowed_origins_not_declared");
  }

  return hardeningDecision(blockedReasons, warnings, [
    "production_env_schema",
    "ai_disabled",
    "secure_cookie",
    "csrf_secret",
    "rate_limit_config",
    "security_headers_config",
    "audit_redaction_config"
  ]);
}

export function buildSecureHeaders(
  extra: Record<string, string> = {},
  options: { productionReady?: boolean } = {}
): Record<string, string> {
  return {
    ...extra,
    ...secureHeaderPolicy,
    "X-Clinical-Production-Ready": options.productionReady ? "true" : "false"
  };
}

export function validateSecureHeaders(
  headers: Record<string, string | undefined>,
  options: { productionReady?: boolean } = {}
): RuntimeHardeningDecision {
  const blockedReasons: string[] = [];

  for (const [name, expected] of Object.entries(secureHeaderPolicy)) {
    const expectedValue = name === "X-Clinical-Production-Ready"
      ? (options.productionReady ? "true" : "false")
      : expected;
    const actual = lookupHeader(headers, name);
    if (!actual) {
      blockedReasons.push(`missing_header:${name}`);
      continue;
    }
    if (name === "Content-Security-Policy") {
      for (const required of ["default-src 'self'", "frame-ancestors 'none'", "object-src 'none'"]) {
        if (!actual.includes(required)) {
          blockedReasons.push(`csp_missing_directive:${required}`);
        }
      }
      continue;
    }
    if (actual !== expectedValue) {
      blockedReasons.push(`header_value_mismatch:${name}`);
    }
  }

  return hardeningDecision(blockedReasons, [], ["secure_headers"]);
}

export type RequestSecurityInput = {
  method: string;
  path: string;
  origin?: string | null;
  allowedOrigins: string[];
  authenticatedActorId?: string | null;
  csrfTokenPresent?: boolean;
  csrfCookiePresent?: boolean;
  rateLimitRemaining?: number | null;
};

export function evaluateRequestSecurityControls(input: RequestSecurityInput): RuntimeHardeningDecision {
  const blockedReasons: string[] = [];
  const method = input.method.toUpperCase();
  const unsafeMethod = !["GET", "HEAD", "OPTIONS"].includes(method);

  if (!input.authenticatedActorId) {
    blockedReasons.push("missing_authenticated_actor");
  }
  if (input.origin && input.allowedOrigins.length > 0 && !input.allowedOrigins.includes(input.origin)) {
    blockedReasons.push("origin_not_allowed");
  }
  if (unsafeMethod) {
    if (!input.csrfTokenPresent || !input.csrfCookiePresent) {
      blockedReasons.push("csrf_double_submit_missing");
    }
    if (input.rateLimitRemaining === null || input.rateLimitRemaining === undefined) {
      blockedReasons.push("rate_limit_not_evaluated");
    } else if (input.rateLimitRemaining <= 0) {
      blockedReasons.push("rate_limit_exceeded");
    }
  }

  return hardeningDecision(blockedReasons, [], ["authenticated_actor", "origin_check", "csrf_for_write", "rate_limit_for_write"]);
}

export type PhiSafeAuditEnvelope = {
  persistenceAllowed: boolean;
  redactionApplied: boolean;
  redactedEvent: AuditEvent | null;
  redactedPayload: {
    beforeData: unknown;
    afterData: unknown;
  };
  redactedFields: string[];
  blockedReasons: string[];
  safetyBoundary: string;
};

export function sanitizeAuditEventForPersistence(
  event: AuditEvent,
  payload: { beforeData?: unknown; afterData?: unknown } = {},
  options: { redactionEnabled: boolean } = { redactionEnabled: true }
): PhiSafeAuditEnvelope {
  if (!options.redactionEnabled) {
    return {
      persistenceAllowed: false,
      redactionApplied: false,
      redactedEvent: null,
      redactedPayload: { beforeData: null, afterData: null },
      redactedFields: [],
      blockedReasons: ["audit_redaction_disabled"],
      safetyBoundary: "Audit persistence is blocked until PHI/PII redaction is enabled."
    };
  }

  const eventRedaction = redactPhiFromValue(event);
  const beforeRedaction = redactPhiFromValue(payload.beforeData ?? null);
  const afterRedaction = redactPhiFromValue(payload.afterData ?? null);
  const redactedFields = [
    ...eventRedaction.redactedFields,
    ...beforeRedaction.redactedFields.map((field) => `beforeData.${field}`),
    ...afterRedaction.redactedFields.map((field) => `afterData.${field}`)
  ];

  return {
    persistenceAllowed: true,
    redactionApplied: redactedFields.length > 0,
    redactedEvent: eventRedaction.value as AuditEvent,
    redactedPayload: {
      beforeData: beforeRedaction.value,
      afterData: afterRedaction.value
    },
    redactedFields,
    blockedReasons: [],
    safetyBoundary: "Only redacted audit payloads may be persisted; raw PHI/PII must be dropped before storage."
  };
}

export type PatientCommunicationPolicyInput = {
  messageType: string;
  hasApprovedTemplate: boolean;
  hasConsent: boolean;
  physicianApproved: boolean;
  redFlagActive: boolean;
  includesTreatmentInstruction: boolean;
  policyVersion?: string | null;
  channel: "PRINTED_HANDOUT" | "PHONE_CALL_TASK" | "PORTAL_MESSAGE" | "SMS";
};

export function evaluatePatientCommunicationPolicy(input: PatientCommunicationPolicyInput): RuntimeHardeningDecision {
  const blockedReasons: string[] = [];
  const automationAllowed = isPatientCommunicationAllowed(
    input.messageType,
    input.hasApprovedTemplate,
    input.hasConsent
  );

  if (!input.policyVersion) {
    blockedReasons.push("patient_communication_policy_version_missing");
  }
  if (!automationAllowed) {
    blockedReasons.push("message_type_template_or_consent_not_allowed");
  }
  if (!input.physicianApproved) {
    blockedReasons.push("physician_approval_missing");
  }
  if (input.redFlagActive) {
    blockedReasons.push("red_flag_blocks_patient_communication");
  }
  if (input.includesTreatmentInstruction) {
    blockedReasons.push("treatment_instruction_messages_not_allowed");
  }
  if (!["PRINTED_HANDOUT", "PHONE_CALL_TASK", "PORTAL_MESSAGE"].includes(input.channel)) {
    blockedReasons.push(`channel_not_allowed:${input.channel}`);
  }

  return hardeningDecision(blockedReasons, [], [
    "approved_template",
    "patient_consent",
    "physician_approval",
    "red_flag_stop",
    "no_treatment_instruction"
  ]);
}

function redactPhiFromValue(value: unknown, path = "$"): { value: unknown; redactedFields: string[] } {
  if (typeof value === "string") {
    const redacted = redactPhiFromString(value);
    return {
      value: redacted.value,
      redactedFields: redacted.redacted ? [path] : []
    };
  }
  if (Array.isArray(value)) {
    const redactedFields: string[] = [];
    const redactedArray = value.map((item, index) => {
      const redacted = redactPhiFromValue(item, `${path}[${index}]`);
      redactedFields.push(...redacted.redactedFields);
      return redacted.value;
    });
    return { value: redactedArray, redactedFields };
  }
  if (value && typeof value === "object") {
    const redactedFields: string[] = [];
    const redactedObject: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(value)) {
      const redacted = redactPhiFromValue(item, `${path}.${key}`);
      redactedObject[key] = redacted.value;
      redactedFields.push(...redacted.redactedFields);
    }
    return { value: redactedObject, redactedFields };
  }
  return { value, redactedFields: [] };
}

function redactPhiFromString(value: string): { value: string; redacted: boolean } {
  const patterns: Array<{ regex: RegExp; replacement: string }> = [
    { regex: /\b0\d{9,10}\b/g, replacement: "[REDACTED_PHONE]" },
    { regex: /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, replacement: "[REDACTED_EMAIL]" },
    { regex: /\b\d{12}\b/g, replacement: "[REDACTED_NATIONAL_ID]" },
    { regex: /\b\d{2}\/\d{2}\/\d{4}\b/g, replacement: "[REDACTED_DATE]" },
    { regex: /\b(?:MRN|CCCD|CMND|BHYT|so ho so)\s*[:#-]?\s*[A-Z0-9-]+\b/gi, replacement: "[REDACTED_RECORD_ID]" }
  ];
  let redacted = value;
  for (const pattern of patterns) {
    redacted = redacted.replace(pattern.regex, pattern.replacement);
  }
  return {
    value: redacted,
    redacted: redacted !== value
  };
}

function hardeningDecision(blockedReasons: string[], warnings: string[], controls: string[]): RuntimeHardeningDecision {
  return {
    allowed: blockedReasons.length === 0,
    productionReady: false,
    status: blockedReasons.length === 0 ? "PASS_WITH_HUMAN_GATES" : "BLOCKED",
    blockedReasons,
    warnings,
    controls,
    safetyBoundary:
      "Runtime hardening gates reduce technical risk but do not make chronic-care clinical runtime production-ready without human signoff, UAT, legal/privacy review and deployment evidence."
  };
}

function requirePresent(env: RuntimeEnvironment, name: string, blockedReasons: string[]): void {
  if (!env[name]) {
    blockedReasons.push(`missing_env:${name}`);
  }
}

function requireSecret(env: RuntimeEnvironment, name: string, blockedReasons: string[]): void {
  const value = env[name] ?? "";
  if (value.length < 32) {
    blockedReasons.push(`weak_or_missing_secret:${name}`);
  }
}

function requireHttpsUrl(env: RuntimeEnvironment, name: string, blockedReasons: string[]): void {
  const value = env[name] ?? "";
  if (!value.startsWith("https://")) {
    blockedReasons.push(`https_url_required:${name}`);
  }
}

function requireNumberInRange(
  env: RuntimeEnvironment,
  name: string,
  min: number,
  max: number,
  blockedReasons: string[]
): void {
  const raw = env[name];
  const parsed = raw ? Number.parseInt(raw, 10) : Number.NaN;
  if (!Number.isInteger(parsed) || parsed < min || parsed > max) {
    blockedReasons.push(`env_number_out_of_range:${name}`);
  }
}

function isEnabled(value: string | undefined): boolean {
  return ["1", "true", "yes", "on"].includes((value ?? "").trim().toLowerCase());
}

function lookupHeader(headers: Record<string, string | undefined>, name: string): string | undefined {
  const needle = name.toLowerCase();
  for (const [key, value] of Object.entries(headers)) {
    if (key.toLowerCase() === needle) {
      return value;
    }
  }
  return undefined;
}
