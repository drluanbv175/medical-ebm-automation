import type { AuditEvent } from "./audit";
import { authorizeBackendAction, type GuardDecision } from "./backend-guard";
import type { CareGap } from "./care-orchestrator";
import type { CarePlanApprovalPackage } from "./care-plan-approval";
import type { PatientEducationReleasePackage } from "./patient-education";
import type { AccessContext, Permission, ResourceScope } from "./rbac";
import type { Appointment, Patient, Role } from "./types";

export type WorkflowActionInput = {
  actorName: string;
  actorRole: Role;
  accessContext: AccessContext;
  resourceScope: ResourceScope;
  confirmationChecked: boolean;
  reason: string;
};

export type AppointmentDraftInput = Pick<Appointment, "appointmentType" | "scheduledAt" | "providerName" | "reason" | "riskFlag">;

export type WorkflowActionPreview = {
  actionName:
    | "approveCarePlanVersion"
    | "releaseApprovedPatientHandout"
    | "claimOverdueFollowUpTask"
    | "createCareAppointment";
  serverActionName: string;
  status: "READY_FOR_SERVER_ACTION" | "BLOCKED";
  allowed: boolean;
  persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED";
  blockedReasons: string[];
  backendGuard: GuardDecision;
  auditPreview: AuditEvent;
  requiredServerSideGuards: string[];
  safetyBoundary: string;
};

export function previewApproveCarePlanAction(
  approvalPackage: CarePlanApprovalPackage,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "care_plan.approve");
  const blockedReasons = [
    ...requireRole(input.actorRole, ["PHYSICIAN"], "Chi bac si moi duoc ky duyet care plan."),
    ...requireBackendGuard(backendGuard),
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
    backendGuard,
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
      "Call authorizeBackendAction with care_plan.approve and active same-organization/session permission.",
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
  const backendGuard = authorizeWorkflowAction(input, "handout.approve");
  const blockedReasons = [
    ...requireRole(
      input.actorRole,
      ["PHYSICIAN"],
      "Chi bac si moi duoc phe duyet phat hanh loi dan trong contract hien tai."
    ),
    ...requireBackendGuard(backendGuard),
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
    backendGuard,
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
      "Call authorizeBackendAction with handout.approve and active same-organization/session permission.",
      "Create PatientHandout and append-only AuditLog in one transaction.",
      "Use only approved template content and reject free-text treatment instructions.",
      "Do not send patient messages automatically; queue communication only through approved template workflow."
    ],
    safetyBoundary:
      "Preview nay khong tu dong in/gui, khong them loi dan dieu tri tu do va khong thay the tu van/cap cuu."
  };
}

export function previewClaimOverdueFollowUpTaskAction(
  gap: CareGap,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "task.manage");
  const blockedReasons = [
    ...requireRole(
      input.actorRole,
      ["CARE_COORDINATOR", "NURSE_COORDINATOR"],
      "Chi care coordinator hoac dieu duong dieu phoi moi duoc nhan task goi nhac."
    ),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan dung kich ban da duyet va khong gui thong diep dieu tri."),
    ...(gap.category !== "FOLLOW_UP" ? ["Chi duoc nhan task FOLLOW_UP trong action nay."] : []),
    ...(gap.patientCommunicationAllowed ? [] : ["Chua du dieu kien lien he nguoi benh bang template/consent."])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "claimOverdueFollowUpTask",
    serverActionName: "claimOverdueFollowUpTaskAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-claim-task-${gap.patientId}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "UPDATE",
      entityType: "CareCoordinationTask",
      entityId: gap.id,
      summary: allowed
        ? "Preview nhan task goi nhac tai kham qua han; chua ghi DB production."
        : "Chan preview nhan task do thieu role, scope, consent/template hoac sai loai gap."
    }),
    requiredServerSideGuards: [
      "Re-read care gap/task and patient consent inside server action.",
      "Call authorizeBackendAction with task.manage and active same-organization/session permission.",
      "Create or update CareCoordinationTask and append-only AuditLog in one transaction.",
      "Use only approved reminder template; do not include treatment advice.",
      "Escalate to PHYSICIAN if contact fails or red flag is reported."
    ],
    safetyBoundary:
      "Preview nay khong tu dong goi/gui tin nhan, khong dua loi khuyen dieu tri va khong thay doi care plan."
  };
}

export function previewCreateCareAppointmentAction(
  patient: Patient,
  appointmentDraft: AppointmentDraftInput,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "task.manage");
  const blockedReasons = [
    ...requireRole(
      input.actorRole,
      ["CARE_COORDINATOR", "NURSE_COORDINATOR"],
      "Chi care coordinator hoac dieu duong dieu phoi moi duoc tao hen dieu phoi."
    ),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan day la lich hen dieu phoi, khong phai chi dinh dieu tri."),
    ...requireFutureAppointment(appointmentDraft.scheduledAt, today),
    ...(patient.status !== "ACTIVE" ? [`Nguoi benh hien tai la ${patient.status}, khong duoc tao hen moi.`] : [])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "createCareAppointment",
    serverActionName: "createCareAppointmentAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-appointment-${patient.id}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "Appointment",
      entityId: `appointment-preview-${patient.id}-${appointmentDraft.scheduledAt.slice(0, 10)}`,
      summary: allowed
        ? "Preview tao lich hen dieu phoi benh man; chua ghi DB production."
        : "Chan preview tao lich hen do thieu role, scope, xac nhan hoac ngay hen khong hop le."
    }),
    requiredServerSideGuards: [
      "Re-read patient status and active care plan inside server action.",
      "Call authorizeBackendAction with task.manage and active same-organization/session permission.",
      "Create Appointment and append-only AuditLog in one transaction.",
      "Reject appointment dates in the past and overlapping provider slots.",
      "Do not create medication, lab or treatment instructions from this action."
    ],
    safetyBoundary:
      "Preview nay chi tao lich hen dieu phoi, khong tu dong chan doan, khong chi dinh xet nghiem/thuoc va khong gui tin nhan dieu tri."
  };
}

function authorizeWorkflowAction(input: WorkflowActionInput, permission: Permission): GuardDecision {
  return authorizeBackendAction(input.accessContext, permission, input.resourceScope);
}

function requireRole(actorRole: Role, allowedRoles: Role[], message: string): string[] {
  return allowedRoles.includes(actorRole) ? [] : [message];
}

function requireBackendGuard(decision: GuardDecision): string[] {
  return decision.allowed ? [] : [decision.reason];
}

function requireConfirmation(input: WorkflowActionInput, message: string): string[] {
  if (!input.confirmationChecked) return [message];
  if (!input.reason.trim()) return ["Can ghi ly do/ghi chu thao tac truoc khi tao preview action."];
  return [];
}

function requireFutureAppointment(scheduledAt: string, today: string): string[] {
  return scheduledAt.slice(0, 10) >= today ? [] : ["Ngay hen khong duoc nam trong qua khu."];
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
