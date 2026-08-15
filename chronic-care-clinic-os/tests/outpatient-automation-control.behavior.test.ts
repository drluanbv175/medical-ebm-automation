import assert from "node:assert/strict";
import test from "node:test";

import {
  buildOutpatientAutomationControlReport,
  evaluateOutpatientAutomationRule
} from "../lib/outpatient-automation-control";
import { automationRules } from "../lib/automation";
import type { AutomationRule } from "../lib/types";

test("outpatient automation control report allows only safe controlled automation", () => {
  const report = buildOutpatientAutomationControlReport(automationRules, "2026-07-16");

  assert.equal(report.kind, "outpatient_automation_control_report");
  assert.equal(report.status, "SAFE_INTERNAL_AUTOMATION_READY");
  assert.equal(report.summary.totalRules, 12);
  assert.equal(report.summary.activeRules, 12);
  assert.equal(report.summary.blockedRules, 0);
  assert.equal(report.summary.expiredReviewRules, 0);
  assert.equal(report.summary.productionReady, false);
  assert.ok(report.summary.safeInternalRules >= 10);
  assert.equal(report.summary.patientCommunicationTaskRules, 1);
  assert.deepEqual(report.blockedReasons, []);
  assert.match(report.safetyBoundary, /internal tasks, checklists, queues and draft reports/);
  assert.ok(report.decisions.every((item) => item.allowedAutomation !== "BLOCKED"));
});

test("outpatient automation blocks urgent rules not routed to a physician", () => {
  const rule = mutateRule("AUTO-010", {
    assignedRole: "NURSE"
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("urgent_rule_must_route_to_physician"));
});

test("outpatient automation blocks patient-facing rules without human approval", () => {
  const rule = mutateRule("AUTO-011", {
    approvalRequired: false
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.patientFacing, true);
  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("patient_facing_rule_requires_human_approval"));
});

test("outpatient automation blocks expired review dates", () => {
  const rule = mutateRule("AUTO-002", {
    reviewDate: "2026-07-15"
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("review_date_expired"));
});

test("outpatient automation blocks unsafe clinical directives", () => {
  const rule = mutateRule("AUTO-012", {
    notificationTemplate: "SEND_TREATMENT_MESSAGE"
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("unsafe_clinical_automation_directive"));
});

test("outpatient automation blocks unallowlisted patient-facing templates", () => {
  const rule = mutateRule("AUTO-011", {
    notificationTemplate: "patient_sms_followup"
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.patientFacing, true);
  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("patient_facing_template_not_allowlisted"));
});

test("outpatient automation blocks unknown non-internal notification templates", () => {
  const rule = mutateRule("AUTO-002", {
    notificationTemplate: "clinic_ops_slack_webhook"
  });
  const decision = evaluateOutpatientAutomationRule(rule, "2026-07-16");

  assert.equal(decision.patientFacing, false);
  assert.equal(decision.allowedAutomation, "BLOCKED");
  assert.ok(decision.blockedReasons.includes("unapproved_external_notification_template"));
});

function mutateRule(ruleId: string, patch: Partial<AutomationRule>): AutomationRule {
  const rule = automationRules.find((item) => item.ruleId === ruleId);
  assert.ok(rule, `${ruleId} missing`);
  return {
    ...rule,
    ...patch
  };
}
