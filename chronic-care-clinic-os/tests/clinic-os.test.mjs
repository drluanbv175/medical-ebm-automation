import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, join } from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = dirname(dirname(fileURLToPath(import.meta.url)));

function read(path) {
  return readFileSync(join(root, path), "utf8");
}

function listFiles(path) {
  return readdirSync(join(root, path)).flatMap((entry) => {
    const full = join(path, entry);
    const stat = statSync(join(root, full));
    return stat.isDirectory() ? listFiles(full) : [full];
  });
}

test("required planning and governance docs exist", () => {
  for (const file of [
    "PROJECT_PLAN.md",
    "ARCHITECTURE.md",
    "DATABASE_SCHEMA.md",
    "USER_STORIES.md",
    "BACKLOG.md",
    "ASSUMPTIONS.md",
    "RISK_REGISTER.md",
    "SECURITY.md",
    "DATA_GOVERNANCE.md",
    "CLINICAL_SAFETY.md",
    "ROLE_MATRIX.md",
    "API_SPEC.md",
    "DEPLOYMENT.md",
    "OPERATIONS_MANUAL.md",
    "TEST_PLAN.md",
    "CHANGELOG.md"
  ]) {
    assert.ok(read(file).length > 100, `${file} should be non-empty`);
  }
});

test("supplemental architecture and security docs exist", () => {
  for (const file of [
    "docs/architecture/GAP_ANALYSIS.md",
    "docs/architecture/TARGET_ARCHITECTURE.md",
    "docs/architecture/CLINICAL_BOUNDARY.md",
    "docs/architecture/DATA_CLASSIFICATION.md",
    "docs/architecture/AUTOMATION_SAFETY_MODEL.md",
    "docs/architecture/INTEGRATION_STRATEGY.md",
    "docs/architecture/PRODUCTION_READINESS_CHECKLIST.md",
    "docs/deployment/sync-mac-windows-claude-code.md",
    "security/THREAT_MODEL.md",
    "security/SECURITY_TEST_CASES.md",
    "security/INCIDENT_RESPONSE_PLAYBOOK.md",
    "MVP_01_ACCEPTANCE_TEST.md",
    "MVP_01_DEMO_GUIDE.md",
    "MVP_01_LIMITATIONS.md",
    "PRODUCTION_BLOCKERS.md",
    "CLINICAL_SAFETY_SIGNOFF_TEMPLATE.md",
    "DATA_PROTECTION_SIGNOFF_TEMPLATE.md"
  ]) {
    assert.ok(read(file).length > 100, `${file} should be non-empty`);
  }
});

test("Prisma schema contains core clinical and governance models", () => {
  const schema = read("prisma/schema.prisma");
  for (const model of [
    "Patient",
    "ChronicCondition",
    "Medication",
    "VitalSign",
    "LaboratoryResult",
    "CarePlan",
    "CareGoal",
    "Appointment",
    "VisitNote",
    "CareCoordinationTask",
    "CommunicationLog",
    "Referral",
    "QualityMetric",
    "AuditLog",
    "Organization",
    "ClinicSite",
    "Permission",
    "Session",
    "PatientConsent",
    "PatientIdentifier",
    "PatientContact",
    "CareProgramEnrollment",
    "CareRiskAssessment",
    "CarePlanVersion",
    "TaskEscalation",
    "ClinicalRule",
    "ClinicalRuleVersion",
    "ClinicalRuleApproval",
    "AutomationRule",
    "PatientHandout",
    "AIDraft",
    "MedicationReconciliation",
    "LaboratoryReview",
    "EducationMaterial",
    "EducationMaterialApproval",
    "SafetyAlert",
    "SafetyAlertReview",
    "IncidentReport",
    "IncidentReview",
    "ClinicalContent",
    "ClinicalContentVersion",
    "ClinicalContentApproval",
    "QualityMetricDefinition",
    "SystemSetting"
  ]) {
    assert.ok(schema.includes(`model ${model} {`), `${model} model missing`);
  }
});

test("demo seed covers 50 fake patients and required scenarios", () => {
  const seed = read("lib/seed-data.ts");
  assert.match(seed, /Array\.from\(\{ length: 50 \}/);
  for (const scenario of [
    "controlled",
    "uncontrolled-bp",
    "hba1c-high",
    "ckd",
    "polypharmacy",
    "missed-follow-up",
    "post-discharge",
    "high-cv-risk"
  ]) {
    assert.match(seed, new RegExp(scenario), `${scenario} scenario missing`);
  }
});

test("clinical safety blocks unsafe automation patterns", () => {
  const safety = read("lib/clinical-safety.ts");
  assert.match(safety, /requiresPhysicianConfirmation: true/g);
  assert.match(safety, /Khong su dung he thong nhu cong cu thay the cap cuu/);
  assert.match(read("CLINICAL_SAFETY.md"), /Khong tu chan doan/);
  assert.match(read("app/handouts/page.tsx"), /Can bac si kiem chung va phe duyet/);
});

test("RBAC denies receptionist clinical-note style access", () => {
  const rbac = read("lib/rbac.ts");
  assert.match(rbac, /RECEPTIONIST: \["patient.register", "patient.view_admin"/);
  assert.doesNotMatch(rbac, /RECEPTIONIST:[^\n]+patient\.view_clinical/);
  for (const role of ["CLINIC_ADMIN", "NURSE", "CARE_COORDINATOR", "READ_ONLY_AUDITOR", "PATIENT_PORTAL_USER"]) {
    assert.match(rbac, new RegExp(`${role}:`), `${role} missing`);
  }
  assert.match(read("lib/backend-guard.ts"), /Cross-organization or cross-site access denied/);
  assert.match(read("lib/backend-guard.ts"), /Audit logs are append-only/);
});

test("all requested route families have implementation pages", () => {
  const pages = listFiles("app").filter((file) => file.endsWith("page.tsx"));
  for (const route of [
    "mvp-01/page.tsx",
    "command-center/page.tsx",
    "programs/page.tsx",
    "login/page.tsx",
    "dashboard/doctor/page.tsx",
    "dashboard/nurse/page.tsx",
    "dashboard/quality/page.tsx",
    "patients/page.tsx",
    "patients/[id]/page.tsx",
    "appointments/page.tsx",
    "visits/prep/page.tsx",
    "visits/initial/page.tsx",
    "visits/follow-up/page.tsx",
    "care-plans/page.tsx",
    "risk/red/page.tsx",
    "overdue/page.tsx",
    "medications/page.tsx",
    "labs/page.tsx",
    "tasks/page.tsx",
    "referrals/page.tsx",
    "handouts/page.tsx",
    "admin/rules/page.tsx",
    "admin/templates/page.tsx",
    "admin/sop/page.tsx",
    "admin/users/page.tsx",
    "admin/audit/page.tsx",
    "admin/settings/page.tsx"
  ]) {
    assert.ok(pages.includes(join("app", route)), `${route} missing`);
  }
});

test("AI is disabled by default in environment and docs", () => {
  assert.match(read(".env.example"), /AI_DRAFTS_ENABLED="false"/);
  assert.match(read("ASSUMPTIONS.md"), /AI mac dinh disabled/);
});

test("clinical boundary prevents EMR replacement and unsafe automation", () => {
  assert.match(read("docs/architecture/CLINICAL_BOUNDARY.md"), /Tu thay the EMR phap ly/);
  assert.match(read("docs/architecture/TARGET_ARCHITECTURE.md"), /Clinical Coordination Platform/);
  assert.match(read("PRODUCTION_BLOCKERS.md"), /not production-ready/);
  assert.match(read("MVP_01_LIMITATIONS.md"), /not production authentication/);
});

test("automation rules define the 12 required core automations", () => {
  const automation = read("lib/automation.ts");
  for (let index = 1; index <= 12; index += 1) {
    assert.match(automation, new RegExp(`AUTO-${String(index).padStart(3, "0")}`));
  }
  assert.match(automation, /isPatientCommunicationAllowed/);
  assert.match(automation, /hasApprovedTemplate && hasConsent/);
  assert.doesNotMatch(automation, /SEND_TREATMENT_MESSAGE/);
});

test("cross-platform sync workflow is pinned and documented", () => {
  assert.match(read("package.json"), /"sync:check": "node scripts\/sync-check\.mjs"/);
  assert.match(read("package.json"), /"typecheck:app": "tsc -p tsconfig\.check\.json --noEmit"/);
  assert.match(read("tsconfig.check.json"), /app\/care-plans\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/programs\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /lib\/care-plan-draft\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/visit-prep\.ts/);
  assert.match(read("scripts/sync-check.mjs"), /pnpm-lock\.yaml pins app dependencies/);
  assert.match(read("scripts/sync-check.mjs"), /No git remote configured/);
  assert.match(read("docs/deployment/sync-mac-windows-claude-code.md"), /Windows, MacBook and Claude Code/);
  assert.match(read("../.gitattributes"), /\* text=auto eol=lf/);
  assert.match(read("../.gitignore"), /\*\*\/node_modules\//);
  assert.match(read(".gitignore"), /\.pnpm-store\//);
});

test("command center orchestrates care gaps without unsafe treatment automation", () => {
  const orchestrator = read("lib/care-orchestrator.ts");
  const commandCenterPage = read("app/command-center/page.tsx");
  assert.match(orchestrator, /buildCommandCenterSnapshot/);
  assert.match(orchestrator, /buildCareGaps/);
  assert.match(orchestrator, /PROGRAM_MONITORING/);
  assert.match(orchestrator, /reviewProgramEnrollments/);
  assert.match(orchestrator, /requiresPhysicianConfirmation: true/);
  assert.match(orchestrator, /isPatientCommunicationAllowed/);
  assert.match(orchestrator, /patientCommunicationAllowed: false/);
  assert.match(orchestrator, /khong tu dong thay doi dieu tri/i);
  assert.match(commandCenterPage, /Dieu phoi tu dong benh man/);
  assert.match(commandCenterPage, /Khong gui tin nhan tu dong/);
  assert.doesNotMatch(orchestrator, /PRESCRIBE|AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE/);
});

test("program registry tracks chronic disease monitoring without prescribing", () => {
  const registry = read("lib/program-registry.ts");
  const page = read("app/programs/page.tsx");
  for (const program of ["HYPERTENSION", "TYPE_2_DIABETES", "DYSLIPIDEMIA", "CKD", "HEART_FAILURE", "POLYPHARMACY"]) {
    assert.match(registry, new RegExp(program), `${program} missing`);
  }
  assert.match(registry, /buildProgramRegistrySnapshot/);
  assert.match(registry, /reviewProgramEnrollments/);
  assert.match(registry, /ProgramMonitorStatus/);
  assert.match(page, /Chuong trinh quan ly benh man/);
  assert.doesNotMatch(registry, /ke don|prescribe|AUTO_PRESCRIBE/i);
});

test("pre-visit packet prepares visits without treatment automation", () => {
  const prep = read("lib/visit-prep.ts");
  const page = read("app/visits/prep/page.tsx");
  const patientDetail = read("app/patients/[id]/page.tsx");
  assert.match(prep, /buildVisitPrepPacket/);
  assert.match(prep, /buildVisitPrepQueue/);
  assert.match(prep, /safetyBoundary/);
  assert.match(prep, /Khong tu chan doan/);
  assert.match(page, /Chuan bi truoc buoi kham/);
  assert.match(patientDetail, /Packet truoc kham/);
  assert.doesNotMatch(prep, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
});

test("care plan draft workspace requires physician approval before use", () => {
  const draft = read("lib/care-plan-draft.ts");
  const page = read("app/care-plans/page.tsx");
  assert.match(draft, /buildCarePlanDraft/);
  assert.match(draft, /buildCarePlanDraftQueue/);
  assert.match(draft, /DRAFT_REQUIRES_PHYSICIAN_APPROVAL/);
  assert.match(draft, /requiresPhysicianApproval: true/);
  assert.match(draft, /approvalChecklist/);
  assert.match(draft, /Khong tu dong de xuat them\/bot\/doi thuoc/);
  assert.match(draft, /khong tu chan doan, khong tu ke don, khong tu thay doi dieu tri/i);
  assert.match(page, /Ke hoach cham soc can bac si duyet/);
  assert.match(page, /Draft uu tien/);
  assert.match(page, /Checklist phe duyet/);
  assert.doesNotMatch(draft, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
});

test("MVP-01 is scoped to cardiometabolic follow-up and has audit steps", () => {
  const mvp = read("lib/mvp01.ts");
  assert.match(mvp, /Hypertension and Type 2 Diabetes Follow-up Pathway/);
  assert.match(mvp, /Hypertension/);
  assert.match(mvp, /Type 2 Diabetes/);
  assert.match(mvp, /Dyslipidemia/);
  assert.match(mvp, /requiresAudit: true/);
  assert.doesNotMatch(mvp, /COPD|Asthma|Telehealth/);
});
