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
    "docs/deployment/claude-code-handoff.md",
    "docs/deployment/sync-mac-windows-claude-code.md",
    "security/THREAT_MODEL.md",
    "security/SECURITY_TEST_CASES.md",
    "security/INCIDENT_RESPONSE_PLAYBOOK.md",
    "MVP_01_ACCEPTANCE_TEST.md",
    "MVP_01_DEMO_GUIDE.md",
    "MVP_01_LIMITATIONS.md",
    "PRODUCTION_BLOCKERS.md",
    "PRODUCTION_GO_LIVE_RUNBOOK.md",
    "PATIENT_COMMUNICATION_POLICY.md",
    "DATA_RETENTION_POLICY.md",
    "PRODUCTION_EVIDENCE_PACKAGE_TEMPLATE.md",
    "CLINICAL_SAFETY_SIGNOFF_TEMPLATE.md",
    "DATA_PROTECTION_SIGNOFF_TEMPLATE.md",
    "SECURITY_SIGNOFF_TEMPLATE.md",
    "LEGAL_COMPLIANCE_SIGNOFF_TEMPLATE.md",
    "UAT_SIGNOFF_TEMPLATE.md",
    "GO_LIVE_APPROVAL_RECORD_TEMPLATE.md",
    "GO_LIVE_ATTESTATION_TEMPLATE.md"
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
  assert.match(schema, /sequence\s+Int\s+@unique/);
  assert.match(schema, /previousHash\s+String/);
  assert.match(schema, /eventHash\s+String\s+@unique/);
  assert.match(schema, /immutableAfterAppend\s+Boolean\s+@default\(true\)/);
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
  assert.match(rbac, /clinical_rules\.manage/);
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
  const outpatientControl = read("lib/outpatient-automation-control.ts");
  const settings = read("app/admin/settings/page.tsx");
  for (let index = 1; index <= 12; index += 1) {
    assert.match(automation, new RegExp(`AUTO-${String(index).padStart(3, "0")}`));
  }
  assert.match(automation, /isPatientCommunicationAllowed/);
  assert.match(automation, /hasApprovedTemplate && hasConsent/);
  assert.match(outpatientControl, /outpatient_automation_control_report/);
  assert.match(outpatientControl, /SAFE_INTERNAL_AUTOMATION_READY/);
  assert.match(outpatientControl, /unsafe_clinical_automation_directive/);
  assert.match(outpatientControl, /patient_facing_rule_requires_human_approval/);
  assert.match(settings, /Outpatient automation control/);
  assert.match(settings, /khong tu chan doan, khong tu ke don/);
  assert.match(read("package.json"), /outpatient:verify/);
  assert.match(read("scripts/verify-outpatient-automation-control.ts"), /buildOutpatientAutomationControlReport/);
  assert.doesNotMatch(automation, /SEND_TREATMENT_MESSAGE/);
});

test("cross-platform sync workflow is pinned and documented", () => {
  assert.match(read("package.json"), /"sync:check": "node scripts\/sync-check\.mjs"/);
  assert.match(read("package.json"), /"test": "python scripts\/run_node_tests\.py"/);
  assert.match(read("package.json"), /"typecheck:app": "python scripts\/typecheck_app\.py"/);
  assert.match(read("scripts/run_node_tests.py"), /\*\.test\.ts/);
  assert.match(read("scripts/run_node_tests.py"), /TemporaryDirectory/);
  assert.match(read("scripts/run_node_tests.py"), /str\(find_tsc\(\)\)/);
  assert.match(read("scripts/run_node_tests.py"), /"--module",\s+"CommonJS"/);
  assert.match(read("scripts/node_runtime.py"), /codex-primary-runtime/);
  assert.match(read("tsconfig.check.json"), /app\/admin\/audit\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/admin\/rules\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/admin\/settings\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/admin\/templates\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/admin\/users\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/appointments\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/care-plans\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/evidence\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/api\/admin\/outpatient-automation-control\/route\.ts/);
  assert.match(read("tsconfig.check.json"), /app\/api\/evidence\/knowledge-pack\/route\.tsx?/);
  assert.match(read("tsconfig.check.json"), /app\/handouts\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/overdue\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/patients\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /app\/programs\/page\.tsx/);
  assert.match(read("tsconfig.check.json"), /lib\/care-plan-approval\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/care-plan-draft\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/evidence-integration\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/patient-education\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/workflow-actions\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/persistent-transaction\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/prisma-transaction-contract\.ts/);
  assert.match(read("tsconfig.check.json"), /tests\/persistent-transaction\.behavior\.test\.ts/);
  assert.match(read("tsconfig.check.json"), /tests\/runtime-hardening\.behavior\.test\.ts/);
  assert.match(read("tsconfig.check.json"), /tests\/outpatient-automation-control\.behavior\.test\.ts/);
  assert.match(read("tsconfig.check.json"), /tests\/production-control-contracts\.behavior\.test\.ts/);
  assert.match(read("tsconfig.check.json"), /tests\/production-go-live-controls\.behavior\.test\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/a5-output-qa\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/data-retention\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/operations-readiness\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/outpatient-automation-control\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/password-security\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/production-go-live-controls\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/runtime-hardening\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/audit-ledger\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/audit-storage-contract\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/backend-guard\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/rbac\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/write-action-registry\.ts/);
  assert.match(read("tsconfig.check.json"), /lib\/visit-prep\.ts/);
  assert.match(read("scripts/sync-check.mjs"), /pnpm-lock\.yaml pins app dependencies/);
  assert.match(read("scripts/sync-check.mjs"), /Claude Code handoff manifest is present/);
  assert.match(read("scripts/sync-check.mjs"), /CLAUDE\.md points Claude Code to Chronic Care Clinic OS/);
  assert.match(read("docs/deployment/claude-code-handoff.md"), /Safety boundaries that must stay true/);
  assert.match(read("docs/deployment/claude-code-handoff.md"), /Recommended next tasks/);
  assert.match(read("../CLAUDE.md"), /Current Active Subproject: Chronic Care Clinic OS/);
  assert.match(read("scripts/sync-check.mjs"), /No git remote configured/);
  assert.match(read("docs/deployment/sync-mac-windows-claude-code.md"), /Windows, MacBook and Claude Code/);
  assert.match(read("../.gitattributes"), /\* text=auto eol=lf/);
  assert.match(read("../.gitignore"), /\*\*\/node_modules\//);
  assert.match(read(".gitignore"), /\.pnpm-store\//);
});

test("evidence bridge exposes read-only knowledge pack queue without unsafe automation", () => {
  const integration = read("lib/evidence-integration.ts");
  const route = read("app/api/evidence/knowledge-pack/route.ts");
  const page = read("app/evidence/page.tsx");
  const navigation = read("lib/navigation.ts");

  assert.match(integration, /buildEvidenceBridgeSnapshot/);
  assert.match(integration, /knowledge_pack_update_queue\.json/);
  assert.match(integration, /review_only_no_auto_apply/);
  assert.match(integration, /humanRequired/);
  assert.match(integration, /autoApply/);
  assert.match(integration, /no automatic diagnosis, prescribing, patient messaging or treatment change/);
  assert.match(route, /Response\.json\(buildEvidenceBridgeSnapshot/);
  assert.match(route, /Cache-Control/);
  assert.match(page, /Knowledge pack review queue/);
  assert.match(page, /Bac si duyet truoc/);
  assert.match(page, /Khong tu chan doan, khong tu ke don/);
  assert.match(navigation, /href: "\/evidence"/);
  assert.doesNotMatch(integration, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
  assert.doesNotMatch(page, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
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

test("care plan approval package is preview-only with version and audit guardrails", () => {
  const approval = read("lib/care-plan-approval.ts");
  const page = read("app/care-plans/page.tsx");
  assert.match(approval, /buildCarePlanApprovalPackage/);
  assert.match(approval, /buildCarePlanApprovalQueue/);
  assert.match(approval, /READY_FOR_PHYSICIAN_SIGNOFF/);
  assert.match(approval, /BLOCKED_REQUIRES_DIRECT_REVIEW/);
  assert.match(approval, /CarePlanVersion/);
  assert.match(approval, /AuditEvent/);
  assert.match(approval, /PREVIEW_ONLY_REQUIRES_SERVER_ACTION_AND_AUDIT/);
  assert.match(approval, /khong ghi DB, khong ky thay bac si/i);
  assert.match(page, /Goi phe duyet/);
  assert.match(page, /Version va audit preview/);
  assert.match(page, /gate bi chan/);
  assert.doesNotMatch(approval, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
});

test("patient education package uses approved templates without auto messaging", () => {
  const education = read("lib/patient-education.ts");
  const page = read("app/handouts/page.tsx");
  assert.match(education, /educationTemplates/);
  assert.match(education, /buildPatientEducationReleasePackage/);
  assert.match(education, /buildPatientEducationReleaseQueue/);
  assert.match(education, /READY_TO_PRINT_APPROVED_HANDOUT/);
  assert.match(education, /BLOCKED_REQUIRES_APPROVAL_OR_CONSENT/);
  assert.match(education, /isPatientCommunicationAllowed/);
  assert.match(education, /PatientHandout/);
  assert.match(education, /khong tu dong gui cho nguoi benh/i);
  assert.match(page, /Dieu kien phat hanh/);
  assert.match(page, /Hang doi loi dan/);
  assert.match(page, /demo van khong tu dong gui/);
  assert.doesNotMatch(education, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
});

test("workflow action contracts stay preview-only until persistence exists", () => {
  const actions = read("lib/workflow-actions.ts");
  const appointmentsPage = read("app/appointments/page.tsx");
  const adminRulesPage = read("app/admin/rules/page.tsx");
  const adminUsersPage = read("app/admin/users/page.tsx");
  const carePlansPage = read("app/care-plans/page.tsx");
  const handoutsPage = read("app/handouts/page.tsx");
  const patientsPage = read("app/patients/page.tsx");
  assert.match(actions, /previewApproveCarePlanAction/);
  assert.match(actions, /previewReleasePatientHandoutAction/);
  assert.match(actions, /export function approveCarePlanVersionAction/);
  assert.match(actions, /export function releaseApprovedPatientHandoutAction/);
  assert.match(actions, /export function claimOverdueFollowUpTaskAction/);
  assert.match(actions, /export function createCareAppointmentAction/);
  assert.match(actions, /export function createCarePlanDraftAction/);
  assert.match(actions, /export function createEducationTemplateDraftAction/);
  assert.match(actions, /export function registerPatientAction/);
  assert.match(actions, /export function createClinicalRuleDraftAction/);
  assert.match(actions, /export function inviteUserAction/);
  assert.match(actions, /previewClaimOverdueFollowUpTaskAction/);
  assert.match(actions, /previewCreateCareAppointmentAction/);
  assert.match(actions, /previewCreateCarePlanDraftAction/);
  assert.match(actions, /previewCreateEducationTemplateDraftAction/);
  assert.match(actions, /previewRegisterPatientAction/);
  assert.match(actions, /previewCreateClinicalRuleDraftAction/);
  assert.match(actions, /previewInviteUserAction/);
  assert.match(actions, /approveCarePlanVersionAction/);
  assert.match(actions, /releaseApprovedPatientHandoutAction/);
  assert.match(actions, /buildPersistentAuditWritePlan/);
  assert.match(actions, /validatePersistentAuditWritePlan/);
  assert.match(actions, /PERSISTENT_PLAN_NOT_COMMITTED/);
  assert.match(actions, /READY_FOR_ATOMIC_COMMIT_WHEN_DB_WIRING_EXISTS/);
  assert.match(actions, /requiredAtomicWithAuditLog: true/);
  assert.match(actions, /productionCommitDisabled: true/);
  assert.match(actions, /UPSERT_CARE_COORDINATION_TASK/);
  assert.match(actions, /INSERT_APPOINTMENT/);
  assert.match(actions, /INSERT_CARE_PLAN_DRAFT/);
  assert.match(actions, /INSERT_EDUCATION_TEMPLATE_DRAFT/);
  assert.match(actions, /INSERT_PATIENT_REGISTRATION/);
  assert.match(actions, /INSERT_CLINICAL_RULE_DRAFT/);
  assert.match(actions, /INSERT_USER_INVITE/);
  assert.match(actions, /Rollback both business write and AuditLog insert if either side fails/);
  assert.match(actions, /Do not emit patient messages, prescriptions, medication changes or external EMR writes/);
  assert.match(actions, /claimOverdueFollowUpTaskAction/);
  assert.match(actions, /createCareAppointmentAction/);
  assert.match(actions, /createCarePlanDraftAction/);
  assert.match(actions, /createEducationTemplateDraftAction/);
  assert.match(actions, /registerPatientAction/);
  assert.match(actions, /createClinicalRuleDraftAction/);
  assert.match(actions, /inviteUserAction/);
  assert.match(actions, /authorizeBackendAction/);
  assert.match(actions, /care_plan\.approve/);
  assert.match(actions, /handout\.approve/);
  assert.match(actions, /care_plan\.version/);
  assert.match(actions, /clinical_rules\.manage/);
  assert.match(actions, /patient\.register/);
  assert.match(actions, /user\.manage/);
  assert.match(actions, /task\.manage/);
  assert.match(actions, /PREVIEW_ONLY_NOT_PERSISTED/);
  assert.match(actions, /Ngay hen khong duoc nam trong qua khu/);
  assert.match(actions, /Create immutable CarePlanVersion and append-only AuditLog in one transaction/);
  assert.match(actions, /Do not send patient messages automatically/);
  assert.match(actions, /Never create prescriptions, medication changes or treatment messages/);
  assert.match(actions, /NO_MEDICATION_CHANGE/);
  assert.match(actions, /NO_AUTOMATIC_PATIENT_MESSAGE/);
  assert.match(actions, /NO_AUTOMATIC_OUTREACH/);
  assert.match(actions, /NO_RULE_ENGINE_ACTIVATION/);
  assert.match(actions, /NO_EMAIL_SEND/);
  assert.match(actions, /audit payload khong chua ten\/phone\/email/);
  assert.match(actions, /audit payload khong chua email/);
  assert.match(actions, /patient-registration-pending-\$\{today\}/);
  assert.match(actions, /user-invite-\$\{slugify\(inviteDraft\.role\)\}-\$\{today\}/);
  assert.match(actions, /Require separate EducationMaterialApproval before template can be printed or sent/);
  assert.match(actions, /Require signed consent before any patient communication/);
  assert.match(actions, /Do not create diagnoses, medications, care plans, lab orders or treatment messages from registration/);
  assert.match(actions, /Require separate ClinicalRuleApproval before rule can become active or affect risk scoring/);
  assert.match(actions, /Reject rules that remove physician confirmation, create diagnoses, prescribe, order labs or send treatment messages/);
  assert.match(actions, /Reject privilege escalation, SUPER_ADMIN invites, patient-account invites and cross-site role assignment/);
  assert.match(actions, /Do not create passwords, sessions, MFA state or send invite email until mail delivery is explicitly approved/);
  assert.match(actions, /backendGuard/);
  assert.match(actions, /khong ghi DB, khong tao don thuoc/i);
  assert.match(adminRulesPage, /Clinical rule draft preview/);
  assert.match(adminRulesPage, /Backend guard/);
  assert.match(adminUsersPage, /User invite preview/);
  assert.match(adminUsersPage, /Backend guard/);
  assert.match(appointmentsPage, /Create appointment preview/);
  assert.match(appointmentsPage, /Backend guard/);
  assert.match(carePlansPage, /Server action preview/);
  assert.match(carePlansPage, /Backend guard/);
  assert.match(handoutsPage, /Server action preview/);
  assert.match(handoutsPage, /Backend guard/);
  assert.match(patientsPage, /Patient registration preview/);
  assert.match(patientsPage, /Backend guard/);
  assert.doesNotMatch(actions, /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing/i);
});

test("audit ledger is append-only and hash chained", () => {
  const ledger = read("lib/audit-ledger.ts");
  const storage = read("lib/audit-storage-contract.ts");
  const auditPage = read("app/admin/audit/page.tsx");
  assert.match(ledger, /buildAuditLedger/);
  assert.match(ledger, /appendAuditEventPreview/);
  assert.match(ledger, /validateAuditLedger/);
  assert.match(ledger, /immutableAfterAppend: true/);
  assert.match(ledger, /previousHash/);
  assert.match(ledger, /eventHash/);
  assert.match(ledger, /Audit ledger is append-only and hash chain is intact/);
  assert.match(storage, /buildPersistentAuditWritePlan/);
  assert.match(storage, /validatePersistentAuditWritePlan/);
  assert.match(storage, /PERSISTENT_APPEND_ONLY/);
  assert.match(storage, /INSERT_ONLY_NO_UPDATE_NO_DELETE/);
  assert.match(storage, /Commit the business write and AuditLog insert atomically/);
  assert.match(storage, /Read the latest AuditLog row ordered by sequence inside the same database transaction/);
  assert.match(storage, /Reject UPDATE_AUDIT_LOG and DELETE_AUDIT_LOG paths/);
  assert.match(auditPage, /Ledger integrity/);
  assert.match(auditPage, /Persistent AuditLog write plan/);
  assert.match(auditPage, /Next sequence/);
  assert.match(auditPage, /Normal UI cannot update or delete audit log rows/);
  assert.doesNotMatch(ledger, /DELETE_AUDIT_LOG|UPDATE_AUDIT_LOG/);
});

test("persistent transaction harness rolls back business and audit writes atomically", () => {
  const harness = read("lib/persistent-transaction.ts");
  const prismaContract = read("lib/prisma-transaction-contract.ts");
  const rollbackEvidence = read("lib/prisma-rollback-evidence.ts");
  const rollbackTemplate = JSON.parse(read("docs/templates/prisma-rollback-evidence.template.json"));
  const behaviorTest = read("tests/persistent-transaction.behavior.test.ts");
  assert.match(harness, /runPersistentWorkflowTransactionHarness/);
  assert.match(harness, /PersistentTransactionFailurePoint/);
  assert.match(harness, /BEFORE_BUSINESS_WRITE/);
  assert.match(harness, /AFTER_BUSINESS_WRITE_BEFORE_AUDIT/);
  assert.match(harness, /AFTER_AUDIT_WRITE_BEFORE_COMMIT/);
  assert.match(harness, /BUSINESS_WRITE_STAGED/);
  assert.match(harness, /AUDIT_LOG_STAGED/);
  assert.match(harness, /LEDGER_HASH_CHAIN_VALIDATED/);
  assert.match(harness, /COMMIT_ATOMICALLY/);
  assert.match(harness, /ROLLBACK_ATOMICALLY/);
  assert.match(harness, /IN_MEMORY_TRANSACTION_HARNESS_ONLY/);
  assert.match(harness, /productionCommitDisabled: true/);
  assert.match(harness, /validateAuditLedger/);
  assert.match(harness, /Business write is not marked atomic with AuditLog/);
  assert.match(harness, /AuditLog write is not marked transaction-required/);
  assert.match(behaviorTest, /commits business and audit writes together/);
  assert.match(behaviorTest, /rolls back without mutating input state at every failure point/);
  assert.match(behaviorTest, /Missing AuditLog write plan/);
  assert.match(behaviorTest, /prisma test database gate requires rollback evidence before adapter promotion/);
  assert.match(behaviorTest, /prisma test database gate can only unlock test adapter, never production commit/);
  assert.match(behaviorTest, /prisma rollback evidence schema blocks malformed or incomplete reports/);
  assert.match(behaviorTest, /prisma rollback evidence report gates only the test database adapter/);
  assert.match(prismaContract, /PRISMA_TRANSACTION_CONTRACT_ONLY/);
  assert.match(prismaContract, /buildPrismaTransactionContract/);
  assert.match(prismaContract, /validatePrismaTransactionContract/);
  assert.match(prismaContract, /evaluatePrismaTestDatabaseGate/);
  assert.match(prismaContract, /PRISMA_TEST_DATABASE_ROLLBACK_GATE/);
  assert.match(prismaContract, /canEnableProductionCommit: false/);
  assert.match(prismaContract, /APPLY_EXACTLY_ONE_BUSINESS_WRITE/);
  assert.match(prismaContract, /INSERT_EXACTLY_ONE_AUDIT_LOG_ROW/);
  assert.match(prismaContract, /FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT/);
  assert.match(prismaContract, /Missing reviewer signoff for transaction rollback evidence/);
  assert.match(prismaContract, /AuditLog UPDATE\/DELETE must be blocked in the test database/);
  assert.match(prismaContract, /NO_AUDIT_LOG_UPDATE_OR_DELETE/);
  assert.match(rollbackEvidence, /PRISMA_ROLLBACK_EVIDENCE_REPORT/);
  assert.match(rollbackEvidence, /validatePrismaRollbackEvidenceReportSchema/);
  assert.match(rollbackEvidence, /evaluatePrismaRollbackEvidenceReport/);
  assert.match(rollbackEvidence, /AUDIT_LOG_HARDENING_MIGRATION_NAME/);
  assert.match(rollbackEvidence, /productionCommitRequested must be false/);
  assert.equal(rollbackTemplate.artifactKind, "PRISMA_ROLLBACK_EVIDENCE_REPORT");
  assert.equal(rollbackTemplate.productionCommitRequested, false);
  assert.equal(rollbackTemplate.migration.auditLogHardeningApplied, false);
  assert.equal(rollbackTemplate.rollbackProbes.FAIL_AFTER_AUDIT_BEFORE_COMMIT.status, "NOT_RUN");
  assert.doesNotMatch(harness, /prisma\.|fetch\(|sendMail|SMTP|UPDATE_AUDIT_LOG|DELETE_AUDIT_LOG/);
  assert.doesNotMatch(prismaContract, /from ["']@prisma|new PrismaClient|prisma\./);
  assert.doesNotMatch(rollbackEvidence, /from ["']@prisma|new PrismaClient|prisma\./);
});

test("AuditLog migration hardens persistent hash-chain storage", () => {
  const migrationFiles = listFiles("prisma/migrations").filter((file) => file.endsWith("migration.sql"));
  const auditMigrationPath = migrationFiles.find((file) => file.includes("audit_log_hash_chain_hardening"));
  assert.ok(auditMigrationPath, "AuditLog hardening migration is missing");

  const migration = read(auditMigrationPath);
  assert.match(migration, /CREATE UNIQUE INDEX IF NOT EXISTS "AuditLog_sequence_key"/);
  assert.match(migration, /CREATE UNIQUE INDEX IF NOT EXISTS "AuditLog_eventHash_key"/);
  assert.match(migration, /"AuditLog_sequence_positive"/);
  assert.match(migration, /"AuditLog_previousHash_not_empty"/);
  assert.match(migration, /"AuditLog_eventHash_not_empty"/);
  assert.match(migration, /"AuditLog_immutable_after_append_true"/);
  assert.match(migration, /CREATE OR REPLACE FUNCTION prevent_audit_log_mutation/);
  assert.match(migration, /BEFORE UPDATE ON "AuditLog"/);
  assert.match(migration, /BEFORE DELETE ON "AuditLog"/);
  assert.match(migration, /UPDATE and DELETE are blocked/);
  assert.match(read("DATABASE_SCHEMA.md"), /AuditLog hardening migration/);
  assert.match(read("IMPLEMENTATION_STATUS.md"), /AuditLog hardening migration/);
});

test("write action registry tracks guarded and blocked write surfaces", () => {
  const registry = read("lib/write-action-registry.ts");
  const settings = read("app/admin/settings/page.tsx");
  const overdue = read("app/overdue/page.tsx");
  assert.match(registry, /writeActionRegistry/);
  assert.match(registry, /summarizeWriteActionRegistry/);
  assert.match(registry, /unsafeWriteActions/);
  assert.match(registry, /GUARDED_PREVIEW/);
  assert.match(registry, /UI_PLACEHOLDER/);
  assert.match(registry, /BLOCKED_FOR_PRODUCTION/);
  assert.match(registry, /approveCarePlanVersionAction/);
  assert.match(registry, /releaseApprovedPatientHandoutAction/);
  assert.match(registry, /claimOverdueFollowUpTaskAction/);
  assert.match(registry, /createCareAppointmentAction/);
  assert.match(registry, /createCarePlanDraftAction/);
  assert.match(registry, /createEducationTemplateDraftAction/);
  assert.match(registry, /registerPatientAction/);
  assert.match(registry, /createClinicalRuleDraftAction/);
  assert.match(registry, /inviteUserAction/);
  assert.match(registry, /persistent audit write plan/);
  assert.match(registry, /production commit/);
  assert.match(registry, /persistent audit va RBAC scope guard/);
  assert.match(settings, /Write action readiness/);
  assert.match(settings, /Production ready/);
  assert.match(settings, /chua duoc phep production/);
  assert.match(overdue, /Task claim preview/);
  assert.match(overdue, /Backend guard/);
});

test("production readiness blockers are machine-readable and surfaced in settings", () => {
  const readiness = read("lib/production-readiness.ts");
  const route = read("app/api/admin/production-readiness/route.ts");
  const outpatientRoute = read("app/api/admin/outpatient-automation-control/route.ts");
  const hardening = read("lib/runtime-hardening.ts");
  const settings = read("app/admin/settings/page.tsx");
  const blockers = read("PRODUCTION_BLOCKERS.md");
  const typecheck = read("tsconfig.check.json");
  const pkg = read("package.json");
  const verifyScript = read("scripts/verify-production-readiness.ts");
  const dossierScript = read("scripts/build-production-evidence-dossier.ts");
  const goLiveScript = read("scripts/production-go-live.ts");
  const template = read("lib/production-evidence-template.ts");
  const dossier = read("lib/production-evidence-dossier.ts");
  const goLive = read("lib/production-go-live.ts");

  assert.match(readiness, /chronic_care_production_readiness_report/);
  assert.match(readiness, /productionBlockers/);
  assert.match(readiness, /requiredRepositoryControlIdsForBlocker/);
  assert.match(readiness, /summarizeProductionReadiness/);
  assert.match(readiness, /buildProductionReadinessReport/);
  assert.match(readiness, /repositoryControls/);
  assert.match(readiness, /PRODUCTION_READY/);
  assert.match(readiness, /ProductionEvidencePackage/);
  assert.match(readiness, /distinct accountable people/);
  for (const id of ["SEC-001", "DATA-001", "CLIN-001", "OPS-001", "AI-001"]) {
    assert.match(readiness, new RegExp(id), `${id} missing`);
  }
  assert.match(settings, /Production readiness/);
  assert.match(settings, /Open blockers/);
  assert.match(settings, /loadProductionEvidencePackageFromEnv/);
  assert.match(settings, /buildProductionEvidenceDossier/);
  assert.match(settings, /Release decision/);
  assert.match(settings, /Evidence dossier/);
  assert.match(route, /loadProductionEvidencePackageFromEnv/);
  assert.match(route, /buildProductionReadinessReport/);
  assert.match(route, /productionReady: report\.summary\.productionReady/);
  assert.match(route, /buildSecureHeaders/);
  assert.match(route, /Cache-Control/);
  assert.match(route, /no-store/);
  assert.match(outpatientRoute, /buildOutpatientAutomationControlReport/);
  assert.match(outpatientRoute, /productionReady: false/);
  assert.match(outpatientRoute, /Cache-Control/);
  assert.match(hardening, /X-Clinical-Production-Ready/);
  assert.match(hardening, /RUNTIME-OUTPATIENT-AUTOMATION-001/);
  assert.match(hardening, /options\.productionReady/);
  assert.match(pkg, /production:dossier/);
  assert.match(pkg, /production:verify/);
  assert.match(pkg, /production:go-live/);
  assert.match(dossier, /chronic_care_production_evidence_dossier/);
  assert.match(dossier, /READY_FOR_FINAL_GO_LIVE_CHECK/);
  assert.match(dossier, /missingRepositoryControlIds/);
  assert.match(verifyScript, /buildProductionReadinessReport/);
  assert.match(verifyScript, /--init-template/);
  assert.match(verifyScript, /process\.exit\(main\(\)\)/);
  assert.match(dossierScript, /buildProductionEvidenceDossier/);
  assert.match(dossierScript, /--evidence/);
  assert.match(dossierScript, /process\.exit\(main\(\)\)/);
  assert.match(goLiveScript, /buildProductionGoLiveReport/);
  assert.match(goLiveScript, /--admin-approver/);
  assert.match(goLiveScript, /evidenceDossierSha256/);
  assert.match(goLiveScript, /process\.exit\(main\(\)\)/);
  assert.match(template, /buildProductionEvidenceTemplate/);
  assert.match(template, /TODO/);
  assert.match(goLive, /chronic_care_production_go_live_report/);
  assert.match(goLive, /evidenceDossierSha256/);
  assert.match(goLive, /operator_and_admin_approver_must_be_distinct/);
  assert.match(goLive, /runtime_env_warning/);
  assert.match(blockers, /dual-control admin change attestation/);
  assert.match(blockers, /lib\/production-readiness\.ts/);
  assert.match(typecheck, /app\/api\/admin\/production-readiness\/route\.ts/);
  assert.match(typecheck, /lib\/production-go-live\.ts/);
  assert.match(typecheck, /lib\/production-readiness\.ts/);
  assert.match(typecheck, /lib\/production-evidence-dossier\.ts/);
  assert.match(typecheck, /lib\/production-evidence-loader\.ts/);
  assert.match(typecheck, /lib\/production-evidence-template\.ts/);
  assert.match(typecheck, /scripts\/verify-production-readiness\.ts/);
  assert.match(typecheck, /scripts\/build-production-evidence-dossier\.ts/);
  assert.match(typecheck, /scripts\/verify-outpatient-automation-control\.ts/);
  assert.match(typecheck, /types\/next-shims\.d\.ts/);
  assert.match(typecheck, /tests\/production-readiness\.behavior\.test\.ts/);
  assert.match(typecheck, /tests\/production-evidence-dossier\.behavior\.test\.ts/);
  assert.match(typecheck, /tests\/production-go-live\.behavior\.test\.ts/);
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

test("AI_DRAFTS_ENABLED has a real code-level circuit breaker, not just a doc promise", () => {
  // 2026-07-12 audit: .env.example declared AI_DRAFTS_ENABLED=false and PRODUCTION_BLOCKERS.md
  // promised "AI must remain disabled," but no code anywhere read the flag — true only because no
  // AI call site existed yet. Locks in the fix: a guard module any future call site must invoke.
  const guard = read("lib/ai-guard.ts");
  const blockers = read("PRODUCTION_BLOCKERS.md");
  const envExample = read(".env.example");
  assert.match(guard, /export function assertAiDraftsEnabled/);
  assert.match(guard, /export function isAiDraftsEnabled/);
  assert.match(guard, /AI_DRAFTS_ENABLED/);
  assert.match(guard, /throw new Error/);
  assert.match(envExample, /AI_DRAFTS_ENABLED="false"/);
  assert.match(blockers, /lib\/ai-guard\.ts::assertAiDraftsEnabled/);
});
