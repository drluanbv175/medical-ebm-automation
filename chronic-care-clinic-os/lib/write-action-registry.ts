import type { Permission } from "./rbac";
import type { Role } from "./types";

export type WriteActionGuardStatus = "GUARDED_PREVIEW" | "UI_PLACEHOLDER" | "BLOCKED_FOR_PRODUCTION";

export type WriteActionRegistryItem = {
  actionId: string;
  label: string;
  route: string;
  permission: Permission;
  ownerRole: Role;
  guardStatus: WriteActionGuardStatus;
  serverActionName?: string;
  persistenceRequired: true;
  auditRequired: true;
  reason: string;
};

export type WriteActionRegistrySummary = {
  total: number;
  guardedPreview: number;
  uiPlaceholder: number;
  blockedForProduction: number;
  productionReady: false;
};

export const writeActionRegistry: WriteActionRegistryItem[] = [
  guarded(
    "care-plan-approve",
    "Ky duyet care plan version",
    "/care-plans",
    "care_plan.approve",
    "PHYSICIAN",
    "approveCarePlanVersionAction",
    "Da co workflow action contract, RBAC guard va audit preview; chua ghi DB."
  ),
  guarded(
    "overdue-claim-call-task",
    "Nhan task goi nhac qua han",
    "/overdue",
    "task.manage",
    "CARE_COORDINATOR",
    "claimOverdueFollowUpTaskAction",
    "Da co workflow action contract, RBAC guard va audit preview; chua ghi DB hoac gui tin nhan."
  ),
  guarded(
    "handout-release",
    "Phe duyet/phat hanh loi dan A5",
    "/handouts",
    "handout.approve",
    "PHYSICIAN",
    "releaseApprovedPatientHandoutAction",
    "Da co workflow action contract, RBAC guard, consent/template gate va audit preview; chua ghi DB."
  ),
  placeholder("patient-register", "Dang ky nguoi benh", "/patients", "patient.register", "RECEPTIONIST"),
  placeholder("appointment-create", "Tao hen", "/appointments", "task.manage", "CARE_COORDINATOR"),
  placeholder("patient-care-plan-draft", "Tao care plan draft tu ho so nguoi benh", "/patients/[id]", "care_plan.version", "PHYSICIAN"),
  placeholder("template-draft", "Tao template loi dan draft", "/admin/templates", "clinical_rules.manage", "CLINIC_ADMIN"),
  placeholder("clinical-rule-draft", "Tao clinical rule draft", "/admin/rules", "clinical_rules.manage", "CLINIC_ADMIN"),
  placeholder("user-invite", "Moi nguoi dung", "/admin/users", "user.manage", "CLINIC_ADMIN"),
  blocked("quality-export-csv", "Xuat CSV chat luong", "/dashboard/quality", "export.aggregate", "QUALITY_MANAGER"),
  blocked("audit-export", "Xuat audit log", "/admin/audit", "audit.view", "READ_ONLY_AUDITOR")
];

export function summarizeWriteActionRegistry(items = writeActionRegistry): WriteActionRegistrySummary {
  return {
    total: items.length,
    guardedPreview: items.filter((item) => item.guardStatus === "GUARDED_PREVIEW").length,
    uiPlaceholder: items.filter((item) => item.guardStatus === "UI_PLACEHOLDER").length,
    blockedForProduction: items.filter((item) => item.guardStatus === "BLOCKED_FOR_PRODUCTION").length,
    productionReady: false
  };
}

export function unsafeWriteActions(items = writeActionRegistry): WriteActionRegistryItem[] {
  return items.filter((item) => item.guardStatus !== "GUARDED_PREVIEW");
}

function guarded(
  actionId: string,
  label: string,
  route: string,
  permission: Permission,
  ownerRole: Role,
  serverActionName: string,
  reason: string
): WriteActionRegistryItem {
  return {
    actionId,
    label,
    route,
    permission,
    ownerRole,
    guardStatus: "GUARDED_PREVIEW",
    serverActionName,
    persistenceRequired: true,
    auditRequired: true,
    reason
  };
}

function placeholder(
  actionId: string,
  label: string,
  route: string,
  permission: Permission,
  ownerRole: Role
): WriteActionRegistryItem {
  return {
    actionId,
    label,
    route,
    permission,
    ownerRole,
    guardStatus: "UI_PLACEHOLDER",
    persistenceRequired: true,
    auditRequired: true,
    reason: "Nut UI demo chua co workflow action contract, server action, persistent audit va RBAC scope guard."
  };
}

function blocked(
  actionId: string,
  label: string,
  route: string,
  permission: Permission,
  ownerRole: Role
): WriteActionRegistryItem {
  return {
    actionId,
    label,
    route,
    permission,
    ownerRole,
    guardStatus: "BLOCKED_FOR_PRODUCTION",
    persistenceRequired: true,
    auditRequired: true,
    reason: "Production blocker: can export scope, de-identification, audit ledger append va approval truoc khi bat."
  };
}
