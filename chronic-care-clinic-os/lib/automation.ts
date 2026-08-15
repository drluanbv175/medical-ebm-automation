import type { AutomationRule } from "./types";

export const automationRules: AutomationRule[] = [
  rule("AUTO-001", "Nhac tai kham qua han", "Nguoi benh qua ngay tai kham", "HIGH", "DAILY_JOB", "patient.nextFollowUpDate < today", "redFlagActive == true", "CARE_COORDINATOR", false, "internal_overdue_followup", "3 lan khong lien he duoc -> PHYSICIAN", true, "CREATE_TASK"),
  rule("AUTO-002", "Chuan bi truoc buoi kham", "Tao checklist 48-72 gio truoc hen", "MEDIUM", "APPOINTMENT_WINDOW", "appointment.scheduledAt in 48..72h", "appointment.cancelled == true", "NURSE", false, "internal_previsit_checklist", "task qua han -> CARE_COORDINATOR", true, "CREATE_CHECKLIST"),
  rule("AUTO-003", "Khong dat muc tieu", "Care goal qua han hoac chua dat", "MEDIUM", "DAILY_JOB", "careGoal.status in MISSED/IN_PROGRESS and targetDate < today", "carePlan.status != APPROVED", "PHYSICIAN", false, "internal_unmet_goal", "qua 7 ngay -> CLINIC_ADMIN", true, "ADD_TO_QUEUE"),
  rule("AUTO-004", "Theo doi sau doi thuoc", "Bac si xac nhan co thay doi thuoc", "HIGH", "CLINICIAN_MARKED", "physicianMarkedMedicationChange == true", "followUpDate not set by physician", "CARE_COORDINATOR", true, "internal_med_change_followup", "khong co lich -> PHYSICIAN", true, "CREATE_TASK"),
  rule("AUTO-005", "Nguoi benh bo hen", "Appointment status = No Show", "HIGH", "STATUS_CHANGE", "appointment.status == NO_SHOW", "patient.optedOut == true", "CARE_COORDINATOR", false, "internal_no_show", "3 lan khong lien he duoc -> PHYSICIAN", true, "CREATE_TASK"),
  rule("AUTO-006", "Sau xuat vien", "Post-discharge follow-up required", "HIGH", "CLINICIAN_MARKED", "postDischargeRequired == true", "missingDischargeSummary == true", "NURSE", true, "internal_post_discharge", "risk RED -> PHYSICIAN", true, "CREATE_CHECKLIST"),
  rule("AUTO-007", "Thieu ra soat thuoc", "Medication list qua han reconciliation", "MEDIUM", "DAILY_JOB", "lastReconciledAt older than setting", "noActiveMedication == true", "PHARMACIST", false, "internal_med_reconciliation_due", "qua 7 ngay -> PHYSICIAN", true, "ADD_TO_QUEUE"),
  rule("AUTO-008", "Xet nghiem can bac si xem", "Lab bat thuong hoac can review", "HIGH", "STATUS_CHANGE", "lab.abnormalFlag != NORMAL or reviewStatus == NEW", "lab.alreadyReviewed == true", "PHYSICIAN", false, "internal_lab_review", "critical -> PHYSICIAN urgent", true, "CREATE_TASK"),
  rule("AUTO-009", "Care plan can ra soat", "Care plan qua ngay review", "MEDIUM", "DAILY_JOB", "carePlan.reviewDate < today", "carePlan.status != APPROVED", "PHYSICIAN", false, "internal_care_plan_review", "qua 14 ngay -> CLINIC_ADMIN", true, "ADD_TO_QUEUE"),
  rule("AUTO-010", "Co do", "Dieu duong nhap dau hieu nguy co cao", "URGENT", "STATUS_CHANGE", "redFlagInput == true", "none", "PHYSICIAN", true, "internal_red_flag_alert", "immediate direct physician review", true, "SHOW_ALERT"),
  rule("AUTO-011", "Giao duc nguoi benh", "Bac si duyet care plan hoac loi dan", "MEDIUM", "STATUS_CHANGE", "handout.status == APPROVED or carePlan.status == APPROVED", "noConsent == true", "NURSE", true, "approved_patient_education_ready", "template missing -> PHYSICIAN", true, "CREATE_TASK"),
  rule("AUTO-012", "Bao cao chat luong thang", "Ngay dau moi thang tao bao cao draft", "LOW", "MONTHLY_JOB", "firstDayOfMonth == true", "qualityManagerUnavailable == true", "QUALITY_MANAGER", true, "internal_monthly_quality_report", "qua 7 ngay -> CLINIC_ADMIN", true, "CREATE_DRAFT_REPORT")
];

function rule(
  ruleId: string,
  ruleName: string,
  description: string,
  priority: AutomationRule["priority"],
  triggerType: AutomationRule["triggerType"],
  eligibilityLogic: string,
  exclusionLogic: string,
  assignedRole: AutomationRule["assignedRole"],
  approvalRequired: boolean,
  notificationTemplate: string,
  escalationLogic: string,
  isActive: boolean,
  actionType: AutomationRule["actionType"]
): AutomationRule {
  return {
    ruleId,
    ruleName,
    description,
    priority,
    triggerType,
    eligibilityLogic,
    exclusionLogic,
    assignedRole,
    approvalRequired,
    notificationTemplate,
    escalationLogic,
    isActive,
    version: "2026.06",
    approvedBy: "Clinical operations draft approver",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    actionType
  };
}

export function enabledAutomationRules(): AutomationRule[] {
  return automationRules.filter((item) => item.isActive && item.approvedBy);
}

export function isPatientCommunicationAllowed(messageType: string, hasApprovedTemplate: boolean, hasConsent: boolean): boolean {
  const allowed = ["APPOINTMENT_REMINDER", "PRE_VISIT_PREP", "BRING_LABS", "BRING_MEDICATIONS", "APPOINTMENT_CONFIRMATION", "APPROVED_EDUCATION_READY"];
  return allowed.includes(messageType) && hasApprovedTemplate && hasConsent;
}
