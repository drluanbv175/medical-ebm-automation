export type ProductionBlockerCategory = "security" | "data_protection" | "clinical_safety" | "operations" | "ai_governance";

export type ProductionBlockerStatus = "OPEN" | "CLEARED";

export type ProductionBlocker = {
  id: string;
  category: ProductionBlockerCategory;
  title: string;
  owner: "CLINIC_ADMIN" | "DATA_PROTECTION" | "PHYSICIAN_LEAD" | "OPERATIONS" | "AI_GOVERNANCE";
  evidenceRequired: string;
  status: ProductionBlockerStatus;
  blocksProduction: true;
};

export type ProductionReadinessSummary = {
  totalBlockers: number;
  openBlockers: number;
  clearedBlockers: number;
  byCategory: Record<ProductionBlockerCategory, number>;
  productionReady: false;
};

export type ProductionReadinessReport = {
  kind: "chronic_care_production_readiness_report";
  generatedAt: string;
  summary: ProductionReadinessSummary;
  blockers: ProductionBlocker[];
  requiredSignoffs: string[];
  safetyBoundary: string;
};

const categoryOrder: ProductionBlockerCategory[] = [
  "security",
  "data_protection",
  "clinical_safety",
  "operations",
  "ai_governance"
];

export const productionBlockers: ProductionBlocker[] = [
  blocker("SEC-001", "security", "Backend RBAC wired to every route/action.", "CLINIC_ADMIN", "Route/action RBAC coverage test and reviewer signoff."),
  blocker("SEC-002", "security", "Production authentication, session and MFA implemented.", "CLINIC_ADMIN", "Auth threat model, MFA test evidence and session hardening review."),
  blocker("SEC-003", "security", "Password hashing implemented.", "CLINIC_ADMIN", "Password storage review proving one-way hashing and no plaintext path."),
  blocker("SEC-004", "security", "Rate limiting and CSRF controls implemented.", "CLINIC_ADMIN", "Abuse test evidence for write routes and forms."),
  blocker("SEC-005", "security", "Secure headers verified.", "CLINIC_ADMIN", "Header scan or deployment smoke report."),
  blocker("SEC-006", "security", "Environment validation implemented.", "CLINIC_ADMIN", "Startup gate rejects unsafe or missing production configuration."),
  blocker("SEC-007", "security", "Dependency lockfile and vulnerability scan completed.", "CLINIC_ADMIN", "Lockfile plus vulnerability scan report reviewed."),
  blocker("SEC-008", "security", "PHI redaction logger implemented.", "CLINIC_ADMIN", "Logging test showing PHI/PII is redacted before persistence."),

  blocker("DATA-001", "data_protection", "Organization/site isolation enforced end-to-end.", "DATA_PROTECTION", "Cross-organization and cross-site denial tests."),
  blocker("DATA-002", "data_protection", "Backup/restore procedure tested.", "DATA_PROTECTION", "Restore drill report with RPO/RTO evidence."),
  blocker("DATA-003", "data_protection", "Audit log immutability enforced in reviewed runtime migration.", "DATA_PROTECTION", "Migration review and runtime mutation-denial evidence."),
  blocker("DATA-004", "data_protection", "Formal data retention/archive policy approved.", "DATA_PROTECTION", "Approved retention policy and archive/delete procedure."),
  blocker("DATA-005", "data_protection", "UAT completed with de-identified workflow data.", "DATA_PROTECTION", "UAT signoff using de-identified data only."),

  blocker("CLIN-001", "clinical_safety", "Clinical rules formally approved.", "PHYSICIAN_LEAD", "Signed clinical rule approval record."),
  blocker("CLIN-002", "clinical_safety", "Rule approval workflow fully executable.", "PHYSICIAN_LEAD", "End-to-end approval workflow test evidence."),
  blocker("CLIN-003", "clinical_safety", "Clinical content and patient education approval executable.", "PHYSICIAN_LEAD", "Content approval and patient education release evidence."),
  blocker("CLIN-004", "clinical_safety", "A5 PDF output tested.", "PHYSICIAN_LEAD", "Rendered A5 output QA evidence."),
  blocker("CLIN-005", "clinical_safety", "Red flag workflow tested with operational users.", "PHYSICIAN_LEAD", "Operational red-flag drill or UAT report."),
  blocker("CLIN-006", "clinical_safety", "Clinical safety signoff completed.", "PHYSICIAN_LEAD", "Signed clinical safety signoff."),

  blocker("OPS-001", "operations", "Docker one-command run verified.", "OPERATIONS", "Fresh-machine Docker run report."),
  blocker("OPS-002", "operations", "Prisma migration folder generated and reviewed.", "OPERATIONS", "Reviewed migration folder and migration smoke test."),
  blocker("OPS-003", "operations", "Error logging and monitoring configured.", "OPERATIONS", "Monitoring and alert smoke report."),
  blocker("OPS-004", "operations", "Incident response process drilled.", "OPERATIONS", "Incident response tabletop/drill record."),

  blocker("AI-001", "ai_governance", "AI remains disabled until privacy controls and human review workflow are verified.", "AI_GOVERNANCE", "AI_DRAFTS_ENABLED gate evidence plus privacy and review workflow signoff.")
];

export function summarizeProductionReadiness(blockers = productionBlockers): ProductionReadinessSummary {
  const byCategory = Object.fromEntries(categoryOrder.map((category) => [category, 0])) as Record<ProductionBlockerCategory, number>;
  for (const item of blockers) {
    byCategory[item.category] += 1;
  }
  const openBlockers = blockers.filter((item) => item.status === "OPEN").length;
  return {
    totalBlockers: blockers.length,
    openBlockers,
    clearedBlockers: blockers.length - openBlockers,
    byCategory,
    productionReady: false
  };
}

export function openProductionBlockers(blockers = productionBlockers): ProductionBlocker[] {
  return blockers.filter((item) => item.status === "OPEN");
}

export function buildProductionReadinessReport(
  generatedAt = new Date().toISOString(),
  blockers = productionBlockers
): ProductionReadinessReport {
  return {
    kind: "chronic_care_production_readiness_report",
    generatedAt,
    summary: summarizeProductionReadiness(blockers),
    blockers,
    requiredSignoffs: [
      "security_owner",
      "data_protection_owner",
      "physician_lead",
      "operations_owner",
      "ai_governance_owner"
    ],
    safetyBoundary: "Not production-ready; must not be used with real patient data until every blocker is cleared and signoffs are complete."
  };
}

function blocker(
  id: string,
  category: ProductionBlockerCategory,
  title: string,
  owner: ProductionBlocker["owner"],
  evidenceRequired: string
): ProductionBlocker {
  return {
    id,
    category,
    title,
    owner,
    evidenceRequired,
    status: "OPEN",
    blocksProduction: true
  };
}
