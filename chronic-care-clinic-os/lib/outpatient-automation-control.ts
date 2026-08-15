import { automationRules, isPatientCommunicationAllowed } from "./automation";
import type { AutomationRule } from "./types";

export type OutpatientAutomationStatus = "SAFE_INTERNAL_AUTOMATION_READY" | "BLOCKED_FOR_REVIEW";

export type OutpatientAutomationRuleDecision = {
  ruleId: string;
  ruleName: string;
  actionType: AutomationRule["actionType"];
  assignedRole: AutomationRule["assignedRole"];
  priority: AutomationRule["priority"];
  patientFacing: boolean;
  humanGate: string;
  allowedAutomation: "INTERNAL_TASK_ONLY" | "PATIENT_COMMUNICATION_TASK" | "BLOCKED";
  blockedReasons: string[];
  warnings: string[];
};

export type OutpatientAutomationControlSummary = {
  totalRules: number;
  activeRules: number;
  safeInternalRules: number;
  patientCommunicationTaskRules: number;
  blockedRules: number;
  physicianGatedRules: number;
  expiredReviewRules: number;
  productionReady: false;
};

export type OutpatientAutomationControlReport = {
  kind: "outpatient_automation_control_report";
  generatedAt: string;
  status: OutpatientAutomationStatus;
  summary: OutpatientAutomationControlSummary;
  decisions: OutpatientAutomationRuleDecision[];
  blockedReasons: string[];
  safetyBoundary: string;
};

const patientFacingTemplateMap: Record<string, string> = {
  approved_patient_education_ready: "APPROVED_EDUCATION_READY"
};

const patientFacingTemplatePattern =
  /(?:^|_)(patient|patient_portal|portal|sms|zalo|email|message_patient|nguoi_benh|benh_nhan)(?:_|$)/i;

const unsafeAutomationPattern =
  /AUTO_PRESCRIBE|SEND_TREATMENT_MESSAGE|automatic prescribing|ORDER_LAB|AUTO_DIAGNOSE|SMS_PATIENT|EMAIL_PATIENT|PATIENT_PORTAL_MESSAGE|tu dong ke don|tu dong chan doan|tu dong thay doi dieu tri|gui tin nhan cho nguoi benh|nhan tin cho benh nhan/i;

export function buildOutpatientAutomationControlReport(
  rules: AutomationRule[] = automationRules,
  generatedAt = "2026-07-16"
): OutpatientAutomationControlReport {
  const decisions = rules.map((rule) => evaluateOutpatientAutomationRule(rule, generatedAt));
  const blockedReasons = Array.from(new Set(decisions.flatMap((item) => item.blockedReasons.map((reason) => `${item.ruleId}:${reason}`))));
  const status: OutpatientAutomationStatus = blockedReasons.length === 0
    ? "SAFE_INTERNAL_AUTOMATION_READY"
    : "BLOCKED_FOR_REVIEW";

  return {
    kind: "outpatient_automation_control_report",
    generatedAt,
    status,
    summary: {
      totalRules: decisions.length,
      activeRules: rules.filter((item) => item.isActive).length,
      safeInternalRules: decisions.filter((item) => item.allowedAutomation === "INTERNAL_TASK_ONLY").length,
      patientCommunicationTaskRules: decisions.filter((item) => item.allowedAutomation === "PATIENT_COMMUNICATION_TASK").length,
      blockedRules: decisions.filter((item) => item.allowedAutomation === "BLOCKED").length,
      physicianGatedRules: decisions.filter((item) => item.humanGate.includes("PHYSICIAN")).length,
      expiredReviewRules: decisions.filter((item) => item.blockedReasons.includes("review_date_expired")).length,
      productionReady: false
    },
    decisions,
    blockedReasons,
    safetyBoundary: status === "SAFE_INTERNAL_AUTOMATION_READY"
      ? "Outpatient automation is limited to internal tasks, checklists, queues and draft reports; clinical decisions and patient communication still require human gates."
      : "Outpatient automation is blocked until unsafe, expired or ungated rules are reviewed by the accountable clinic roles."
  };
}

export function evaluateOutpatientAutomationRule(
  rule: AutomationRule,
  generatedAt = "2026-07-16"
): OutpatientAutomationRuleDecision {
  const blockedReasons: string[] = [];
  const warnings: string[] = [];
  const patientFacingType = patientFacingTemplateType(rule.notificationTemplate);
  const patientFacing = patientFacingType !== null;

  if (!rule.isActive) {
    warnings.push("rule_inactive");
  }
  if (!rule.approvedBy || containsPlaceholder(rule.approvedBy)) {
    blockedReasons.push("missing_rule_approval");
  }
  if (!isReviewDateCurrent(rule.reviewDate, generatedAt)) {
    blockedReasons.push("review_date_expired");
  }
  if (!rule.escalationLogic || rule.escalationLogic.trim().length < 5) {
    blockedReasons.push("missing_escalation_logic");
  }
  if (rule.priority === "URGENT" && rule.assignedRole !== "PHYSICIAN") {
    blockedReasons.push("urgent_rule_must_route_to_physician");
  }
  if (unsafeAutomationPattern.test([
    rule.ruleName,
    rule.description,
    rule.eligibilityLogic,
    rule.notificationTemplate,
    rule.escalationLogic,
    rule.actionType
  ].join(" "))) {
    blockedReasons.push("unsafe_clinical_automation_directive");
  }
  if (patientFacing) {
    if (!rule.approvalRequired) {
      blockedReasons.push("patient_facing_rule_requires_human_approval");
    }
    if (!isPatientCommunicationAllowed(patientFacingType, true, true)) {
      blockedReasons.push("patient_facing_template_not_allowlisted");
    }
  } else if (!isInternalNotificationTemplate(rule.notificationTemplate)) {
    blockedReasons.push("unapproved_external_notification_template");
  }

  return {
    ruleId: rule.ruleId,
    ruleName: rule.ruleName,
    actionType: rule.actionType,
    assignedRole: rule.assignedRole,
    priority: rule.priority,
    patientFacing,
    humanGate: describeHumanGate(rule, patientFacing),
    allowedAutomation: blockedReasons.length > 0
      ? "BLOCKED"
      : (patientFacing ? "PATIENT_COMMUNICATION_TASK" : "INTERNAL_TASK_ONLY"),
    blockedReasons,
    warnings
  };
}

function describeHumanGate(rule: AutomationRule, patientFacing: boolean): string {
  if (rule.assignedRole === "PHYSICIAN" || rule.priority === "URGENT") {
    return "PHYSICIAN_REVIEW_REQUIRED";
  }
  if (patientFacing) {
    return "APPROVED_TEMPLATE_CONSENT_AND_CLINICIAN_REVIEW_REQUIRED";
  }
  if (rule.approvalRequired) {
    return `${rule.assignedRole}_REVIEW_REQUIRED`;
  }
  return `${rule.assignedRole}_TASK_OWNER_REVIEW`;
}

function patientFacingTemplateType(template: string): string | null {
  return patientFacingTemplateMap[template]
    ?? (patientFacingTemplatePattern.test(template) ? "UNAPPROVED_PATIENT_FACING_TEMPLATE" : null);
}

function isInternalNotificationTemplate(template: string): boolean {
  return /^internal_[a-z0-9_]+$/i.test(template);
}

function isReviewDateCurrent(reviewDate: string, generatedAt: string): boolean {
  const reviewTimestamp = Date.parse(reviewDate);
  const generatedTimestamp = Date.parse(generatedAt);
  return Number.isFinite(reviewTimestamp)
    && Number.isFinite(generatedTimestamp)
    && reviewTimestamp >= generatedTimestamp;
}

function containsPlaceholder(value: string): boolean {
  return /(TODO|TBD|PLACEHOLDER|REPLACE_ME)/i.test(value);
}
