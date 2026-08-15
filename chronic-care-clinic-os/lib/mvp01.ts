import type { Mvp01WorkflowEvent } from "./types";

export const mvp01Name = "MVP-01: Hypertension and Type 2 Diabetes Follow-up Pathway";

export const mvp01Scope = ["Hypertension", "Type 2 Diabetes", "Dyslipidemia"];

export const mvp01Workflow: Mvp01WorkflowEvent[] = [
  { stepId: "create_fake_patient", actorRole: "RECEPTIONIST", action: "Tao nguoi benh gia lap", requiresAudit: true },
  { stepId: "schedule_visit", actorRole: "RECEPTIONIST", action: "Dat lich kham", requiresAudit: true },
  { stepId: "nurse_check_in", actorRole: "NURSE", action: "Dieu duong tiep nhan", requiresAudit: true },
  { stepId: "record_vitals", actorRole: "NURSE", action: "Ghi sinh hieu", requiresAudit: true },
  { stepId: "med_reconciliation", actorRole: "PHARMACIST", action: "Ra soat thuoc", requiresAudit: true },
  { stepId: "draft_care_plan", actorRole: "PHYSICIAN", action: "Bac si lap care plan", requiresAudit: true, requiresApproval: true },
  { stepId: "approve_handout", actorRole: "PHYSICIAN", action: "Bac si phe duyet loi dan", requiresAudit: true, requiresApproval: true },
  { stepId: "print_a5", actorRole: "NURSE", action: "In A5/PDF", requiresAudit: true },
  { stepId: "schedule_follow_up", actorRole: "RECEPTIONIST", action: "Dat lich tai kham", requiresAudit: true },
  { stepId: "create_reminder_task", actorRole: "CARE_COORDINATOR", action: "Tao task nhac hen", requiresAudit: true },
  { stepId: "dashboard_visible", actorRole: "PHYSICIAN", action: "Dashboard hien thi nguoi benh", requiresAudit: false },
  { stepId: "audit_complete", actorRole: "READ_ONLY_AUDITOR", action: "Audit log day du", requiresAudit: false }
];

export function mvp01HasFullAuditTrail(): boolean {
  return mvp01Workflow.filter((step) => step.requiresAudit).length >= 10;
}
