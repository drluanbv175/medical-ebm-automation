import type { AuditEvent } from "./audit";
import type { CarePlanApprovalPackage } from "./care-plan-approval";
import type { PatientEducationReleasePackage } from "./patient-education";
import type { Role } from "./types";

export type WorkflowActionInput = {
  actorName: string;
  actorRole: Role;
  confirmationChecked: boolean;
  reason: string;
};

export type WorkflowActionPreview = {
  actionName: "approveCarePlanVersion" | "releaseApprovedPatientHandout";
  serverActionName: string;
  status: "READY_FOR_SERVER_ACTION" | "BLOCKED";
  allowed: boolean;
  persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED";
  blockedReasons: string[];
  auditPreview: AuditEvent;
  requiredServerSideGuards: string[];
  safetyBoundary: string;
};

export function previewApproveCarePlanAction(
  approvalPackage: CarePlanApprovalPackage,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const blockedReasons = [
    ...requireRole(input.actorRole, ["PHYSICIAN"], "Chi bac si moi duoc ky duyet care plan."),
    ...requireConfirmation(input, "Bac si phai tich xac nhan da xem risk, lab, thuoc, muc tieu va safety-net."),
    ...approvalPackage.blockedReasons,
    ...(!approvalPackage.approvalActionAllowed ? ["Approval package chua san sang de ky duyet."] : [])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "approveCarePlanVersion",
    serverActionName: "approveCarePlanVersionAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    auditPreview: buildAuditPreview({
      id: `audit-action-care-plan-${approvalPackage.patientId}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "APPROVE",
      entityType: "CarePlanVersion",
      entityId: approvalPackage.versionPreview.versionId,
      summary: allowed
        ? "Preview ky duyet CarePlanVersion; chua ghi DB production."
        : "Chan preview ky duyet CarePlanVersion do thieu role, xac nhan hoac gate."
    }),
    requiredServerSideGuards: [
      "Re-read patient, draft, approval gates and current care plan inside server action.",
      "Require PHYSICIAN role and active same-organization/session permission.",
      "Create immutable CarePlanVersion and append-only AuditLog in one transaction.",
      "Reject stale draft/version ids and any blocked approval gate.",
      "Never create medication changes or patient messages from this action."
    ],
    safetyBoundary:
      "Preview nay khong ky thay bac si, khong ghi DB, khong tao don thuoc va khong gui thong diep dieu tri."
  };
}

export function previewReleasePatientHandoutAction(
  releasePackage: PatientEducationReleasePackage,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const blockedReasons = [
    ...requireRole(
      input.actorRole,
      ["PHYSICIAN", "NURSE"],
      "Chi bac si hoac dieu duong moi duoc phat hanh loi dan da duyet."
    ),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan template, care plan va consent hop le."),
    ...releasePackage.blockedReasons,
    ...(!releasePackage.printAllowed ? ["Release package chua san sang de in/phat hanh."] : [])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "releaseApprovedPatientHandout",
    serverActionName: "releaseApprovedPatientHandoutAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    auditPreview: buildAuditPreview({
      id: `audit-action-handout-${releasePackage.patientId}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "PatientHandout",
      entityId: releasePackage.packageId,
      summary: allowed
        ? "Preview phat hanh PatientHandout tu template da duyet; chua ghi DB production."
        : "Chan preview phat hanh PatientHandout do thieu role, xac nhan, consent hoac phe duyet."
    }),
    requiredServerSideGuards: [
      "Re-read template approval, care plan status and patient consent inside server action.",
      "Require PHYSICIAN or NURSE role with site-level access.",
      "Create PatientHandout and append-only AuditLog in one transaction.",
      "Use only approved template content and reject free-text treatment instructions.",
      "Do not send patient messages automatically; queue communication only through approved template workflow."
    ],
    safetyBoundary:
      "Preview nay khong tu dong in/gui, khong them loi dan dieu tri tu do va khong thay the tu van/cap cuu."
  };
}

function requireRole(actorRole: Role, allowedRoles: Role[], message: string): string[] {
  return allowedRoles.includes(actorRole) ? [] : [message];
}

function requireConfirmation(input: WorkflowActionInput, message: string): string[] {
  if (!input.confirmationChecked) return [message];
  if (!input.reason.trim()) return ["Can ghi ly do/ghi chu thao tac truoc khi tao preview action."];
  return [];
}

function buildAuditPreview(input: {
  id: string;
  actorName: string;
  actorRole: Role;
  actionType: AuditEvent["actionType"];
  entityType: string;
  entityId: string;
  summary: string;
}): AuditEvent {
  return {
    id: input.id,
    actor: input.actorName,
    actorRole: input.actorRole,
    actionType: input.actionType,
    entityType: input.entityType,
    entityId: input.entityId,
    summary: input.summary,
    createdAt: "2026-06-19T00:00:00+07:00"
  };
}
