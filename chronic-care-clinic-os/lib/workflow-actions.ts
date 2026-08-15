import type { AuditEvent } from "./audit";
import {
  buildPersistentAuditWritePlan,
  validatePersistentAuditWritePlan,
  type AuditStorageValidation,
  type AuditStorageWritePlan
} from "./audit-storage-contract";
import type { AuditLedgerEntry } from "./audit-ledger";
import { authorizeBackendAction, type GuardDecision } from "./backend-guard";
import type { CareGap } from "./care-orchestrator";
import type { CarePlanApprovalPackage } from "./care-plan-approval";
import type { CarePlanDraft } from "./care-plan-draft";
import type { PatientEducationReleasePackage } from "./patient-education";
import type { AccessContext, Permission, ResourceScope } from "./rbac";
import type { Appointment, ClinicalRule, Patient, Role } from "./types";

export type WorkflowActionInput = {
  actorName: string;
  actorRole: Role;
  accessContext: AccessContext;
  resourceScope: ResourceScope;
  confirmationChecked: boolean;
  reason: string;
};

export type AppointmentDraftInput = Pick<Appointment, "appointmentType" | "scheduledAt" | "providerName" | "reason" | "riskFlag">;

export type EducationTemplateDraftInput = {
  title: string;
  conditionKeywords: string[];
  sections: string[];
  sourceNote: string;
};

export type PatientRegistrationDraftInput = {
  fullName: string;
  dateOfBirth: string;
  sex: Patient["sex"];
  phone: string;
  consentStatus: Patient["consentStatus"];
  intakeReason: string;
  chronicProgramCandidates: string[];
};

export type ClinicalRuleDraftInput = Pick<
  ClinicalRule,
  | "ruleName"
  | "ruleDescription"
  | "purpose"
  | "scope"
  | "referenceSource"
  | "severity"
  | "suggestedAction"
  | "requiresPhysicianConfirmation"
  | "version"
  | "effectiveDate"
  | "reviewDate"
  | "limitationNotes"
>;

export type UserInviteDraftInput = {
  name: string;
  email: string;
  role: Exclude<Role, "SUPER_ADMIN" | "PATIENT" | "PATIENT_PORTAL_USER">;
  organizationId: string;
  clinicSiteId: string;
  invitationReason: string;
};

export type WorkflowActionPreview = {
  actionName:
    | "approveCarePlanVersion"
    | "releaseApprovedPatientHandout"
    | "claimOverdueFollowUpTask"
    | "createCareAppointment"
    | "createCarePlanDraft"
    | "createEducationTemplateDraft"
    | "registerPatient"
    | "createClinicalRuleDraft"
    | "inviteUser";
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

export type PersistentBusinessWritePlan = {
  entityType:
    | "CareCoordinationTask"
    | "Appointment"
    | "AIDraft"
    | "EducationMaterial"
    | "Patient"
    | "ClinicalRule"
    | "UserInvite"
    | "CarePlanVersion"
    | "PatientHandout";
  entityId: string;
  operation:
    | "UPSERT_CARE_COORDINATION_TASK"
    | "INSERT_APPOINTMENT"
    | "INSERT_CARE_PLAN_DRAFT"
    | "INSERT_EDUCATION_TEMPLATE_DRAFT"
    | "INSERT_PATIENT_REGISTRATION"
    | "INSERT_CLINICAL_RULE_DRAFT"
    | "INSERT_USER_INVITE"
    | "INSERT_IMMUTABLE_VERSION"
    | "INSERT_APPROVED_HANDOUT";
  requiredAtomicWithAuditLog: true;
  productionCommitDisabled: true;
  writeSet: Record<string, unknown>;
  forbiddenSideEffects: string[];
};

export type PersistentWorkflowActionPlan = {
  actionName: WorkflowActionPreview["actionName"];
  serverActionName:
    | "approveCarePlanVersionAction"
    | "releaseApprovedPatientHandoutAction"
    | "claimOverdueFollowUpTaskAction"
    | "createCareAppointmentAction"
    | "createCarePlanDraftAction"
    | "createEducationTemplateDraftAction"
    | "registerPatientAction"
    | "createClinicalRuleDraftAction"
    | "inviteUserAction";
  status: "READY_FOR_ATOMIC_COMMIT_WHEN_DB_WIRING_EXISTS" | "BLOCKED";
  allowed: boolean;
  persistenceMode: "PERSISTENT_PLAN_NOT_COMMITTED";
  preview: WorkflowActionPreview;
  auditWritePlan: AuditStorageWritePlan | null;
  auditValidation: AuditStorageValidation;
  businessWritePlan: PersistentBusinessWritePlan | null;
  blockedReasons: string[];
  transactionContract: string[];
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

export function approveCarePlanVersionAction(
  approvalPackage: CarePlanApprovalPackage,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewApproveCarePlanAction(approvalPackage, input, today);
  return buildPersistentWorkflowActionPlan({
    actionName: "approveCarePlanVersion",
    serverActionName: "approveCarePlanVersionAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "APPROVE",
      entityType: "CarePlanVersion",
      entityId: approvalPackage.versionPreview.versionId,
      summary: "Persistent plan ky duyet CarePlanVersion; commit that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        carePlanId: approvalPackage.versionPreview.carePlanId,
        draftId: approvalPackage.draftId,
        previousStatus: "DRAFT_OR_CURRENT"
      },
      afterData: {
        versionPreview: approvalPackage.versionPreview,
        approvalGateStatus: approvalPackage.gateStatus,
        approvedByRole: input.actorRole,
        patientCommunicationAllowedAfterApproval: approvalPackage.patientCommunicationAllowedAfterApproval
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "CarePlanVersion",
      entityId: approvalPackage.versionPreview.versionId,
      operation: "INSERT_IMMUTABLE_VERSION",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        carePlanId: approvalPackage.versionPreview.carePlanId,
        generatedFromDraftId: approvalPackage.versionPreview.generatedFromDraftId,
        status: "APPROVED_AFTER_PHYSICIAN_SIGNOFF",
        immutableAfterApproval: true,
        effectiveDate: approvalPackage.versionPreview.effectiveDate,
        changeSummaryCount: approvalPackage.versionPreview.changeSummary.length
      },
      forbiddenSideEffects: [
        "NO_MEDICATION_CHANGE",
        "NO_PRESCRIPTION",
        "NO_PATIENT_MESSAGE",
        "NO_EMR_WRITEBACK_OUTSIDE_TRANSACTION"
      ]
    }
  });
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

export function releaseApprovedPatientHandoutAction(
  releasePackage: PatientEducationReleasePackage,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewReleasePatientHandoutAction(releasePackage, input, today);
  return buildPersistentWorkflowActionPlan({
    actionName: "releaseApprovedPatientHandout",
    serverActionName: "releaseApprovedPatientHandoutAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "PatientHandout",
      entityId: releasePackage.packageId,
      summary: "Persistent plan phat hanh PatientHandout da duyet; commit/gui that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        patientId: releasePackage.patientId,
        templateId: releasePackage.template.templateId,
        releaseStatus: "NOT_RELEASED"
      },
      afterData: {
        packageId: releasePackage.packageId,
        templateId: releasePackage.template.templateId,
        templateVersion: releasePackage.template.version,
        releaseStatus: releasePackage.releaseStatus,
        handoutSectionsCount: releasePackage.handoutSections.length,
        patientMessageAllowed: releasePackage.patientMessageAllowed
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "PatientHandout",
      entityId: releasePackage.packageId,
      operation: "INSERT_APPROVED_HANDOUT",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        patientId: releasePackage.patientId,
        templateId: releasePackage.template.templateId,
        templateVersion: releasePackage.template.version,
        source: "APPROVED_TEMPLATE_ONLY",
        status: "READY_TO_PRINT_APPROVED_HANDOUT"
      },
      forbiddenSideEffects: [
        "NO_FREE_TEXT_TREATMENT_INSTRUCTION",
        "NO_AUTOMATIC_PRINT",
        "NO_AUTOMATIC_PATIENT_MESSAGE",
        "NO_EMR_WRITEBACK_OUTSIDE_TRANSACTION"
      ]
    }
  });
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

export function claimOverdueFollowUpTaskAction(
  gap: CareGap,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewClaimOverdueFollowUpTaskAction(gap, input, today);
  return buildPersistentWorkflowActionPlan({
    actionName: "claimOverdueFollowUpTask",
    serverActionName: "claimOverdueFollowUpTaskAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "UPDATE",
      entityType: "CareCoordinationTask",
      entityId: gap.id,
      summary: "Persistent plan nhan task goi nhac tai kham; commit/gui that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        taskId: gap.id,
        category: gap.category,
        assignmentStatus: "UNCLAIMED_OR_OPEN"
      },
      afterData: {
        taskId: gap.id,
        assignedRole: gap.assignedRole,
        dueDate: gap.dueDate,
        communicationGate: gap.patientCommunicationAllowed ? "APPROVED_TEMPLATE_AND_CONSENT_REQUIRED" : "BLOCKED"
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "CareCoordinationTask",
      entityId: gap.id,
      operation: "UPSERT_CARE_COORDINATION_TASK",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        taskId: gap.id,
        patientId: gap.patientId,
        category: gap.category,
        assignedRole: gap.assignedRole,
        status: "CLAIMED_FOR_COORDINATION_CALL",
        communicationMode: "APPROVED_REMINDER_TEMPLATE_ONLY"
      },
      forbiddenSideEffects: [
        "NO_AUTOMATIC_CALL",
        "NO_AUTOMATIC_PATIENT_MESSAGE",
        "NO_TREATMENT_ADVICE",
        "NO_CARE_PLAN_CHANGE"
      ]
    }
  });
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

export function createCareAppointmentAction(
  patient: Patient,
  appointmentDraft: AppointmentDraftInput,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewCreateCareAppointmentAction(patient, appointmentDraft, input, today);
  const appointmentId = `appointment-${patient.id}-${appointmentDraft.scheduledAt.slice(0, 10)}`;
  return buildPersistentWorkflowActionPlan({
    actionName: "createCareAppointment",
    serverActionName: "createCareAppointmentAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "Appointment",
      entityId: appointmentId,
      summary: "Persistent plan tao lich hen dieu phoi; commit that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        patientId: patient.id,
        appointmentStatus: "NOT_CREATED"
      },
      afterData: {
        patientId: patient.id,
        appointmentType: appointmentDraft.appointmentType,
        scheduledAt: appointmentDraft.scheduledAt,
        riskFlag: appointmentDraft.riskFlag
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "Appointment",
      entityId: appointmentId,
      operation: "INSERT_APPOINTMENT",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        patientId: patient.id,
        appointmentType: appointmentDraft.appointmentType,
        scheduledAt: appointmentDraft.scheduledAt,
        providerName: appointmentDraft.providerName,
        reason: appointmentDraft.reason,
        riskFlag: appointmentDraft.riskFlag,
        source: "CARE_COORDINATION_WORKFLOW"
      },
      forbiddenSideEffects: [
        "NO_AUTOMATIC_PATIENT_MESSAGE",
        "NO_LAB_ORDER",
        "NO_MEDICATION_ORDER",
        "NO_TREATMENT_INSTRUCTION"
      ]
    }
  });
}

export function previewCreateCarePlanDraftAction(
  patient: Patient,
  draft: CarePlanDraft,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "care_plan.version");
  const blockedReasons = [
    ...requireRole(input.actorRole, ["PHYSICIAN"], "Chi bac si moi duoc tao care plan draft lam sang."),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Bac si phai xac nhan draft chi la ban nhap va can ky duyet rieng."),
    ...(patient.status !== "ACTIVE" ? [`Nguoi benh hien tai la ${patient.status}, khong duoc tao draft moi.`] : []),
    ...(draft.requiresPhysicianApproval ? [] : ["Care plan draft phai bat buoc bac si phe duyet."])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "createCarePlanDraft",
    serverActionName: "createCarePlanDraftAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-care-plan-draft-${patient.id}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "AIDraft",
      entityId: draft.draftId,
      summary: allowed
        ? "Preview tao care plan draft can bac si duyet; chua ghi DB production."
        : "Chan preview tao care plan draft do thieu role, scope, xac nhan hoac trang thai nguoi benh."
    }),
    requiredServerSideGuards: [
      "Re-read patient, current care plan, care gaps and risk state inside server action.",
      "Call authorizeBackendAction with care_plan.version and active same-organization/session permission.",
      "Create AIDraft/CarePlanVersion draft and append-only AuditLog in one transaction.",
      "Mark draft as requiring physician approval before any print, message or care-plan writeback.",
      "Never create prescriptions, medication changes or treatment messages from this action."
    ],
    safetyBoundary:
      "Preview nay chi tao ban nhap care plan, khong ky duyet, khong ke don, khong thay doi dieu tri va khong gui thong diep dieu tri."
  };
}

export function createCarePlanDraftAction(
  patient: Patient,
  draft: CarePlanDraft,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewCreateCarePlanDraftAction(patient, draft, input, today);
  return buildPersistentWorkflowActionPlan({
    actionName: "createCarePlanDraft",
    serverActionName: "createCarePlanDraftAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "AIDraft",
      entityId: draft.draftId,
      summary: "Persistent plan tao care plan draft can bac si phe duyet; commit that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        patientId: patient.id,
        draftStatus: "NOT_CREATED"
      },
      afterData: {
        patientId: patient.id,
        draftId: draft.draftId,
        riskLevel: draft.riskLevel,
        sourceGapCount: draft.sourceGapIds.length,
        requiresPhysicianApproval: draft.requiresPhysicianApproval
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "AIDraft",
      entityId: draft.draftId,
      operation: "INSERT_CARE_PLAN_DRAFT",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        patientId: patient.id,
        draftId: draft.draftId,
        riskLevel: draft.riskLevel,
        sourceGapIds: draft.sourceGapIds,
        status: "DRAFT_REQUIRES_PHYSICIAN_APPROVAL",
        requiresPhysicianApproval: true
      },
      forbiddenSideEffects: [
        "NO_APPROVAL",
        "NO_MEDICATION_CHANGE",
        "NO_PRESCRIPTION",
        "NO_PATIENT_MESSAGE",
        "NO_CARE_PLAN_WRITEBACK"
      ]
    }
  });
}

export function previewCreateEducationTemplateDraftAction(
  templateDraft: EducationTemplateDraftInput,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "clinical_rules.manage");
  const blockedReasons = [
    ...requireRole(input.actorRole, ["CLINIC_ADMIN", "PHYSICIAN"], "Chi admin phong kham hoac bac si moi duoc tao template draft."),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan template draft can hoi dong/bac si duyet rieng."),
    ...(templateDraft.title.trim() ? [] : ["Template title khong duoc trong."]),
    ...(templateDraft.conditionKeywords.length > 0 ? [] : ["Template can it nhat mot condition keyword."]),
    ...(templateDraft.sections.length > 0 ? [] : ["Template can it nhat mot noi dung section."]),
    ...(templateDraft.sourceNote.trim() ? [] : ["Template can ghi nguon/SOP noi bo de review."])
  ];
  const allowed = blockedReasons.length === 0;

  return {
    actionName: "createEducationTemplateDraft",
    serverActionName: "createEducationTemplateDraftAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-template-draft-${slugify(templateDraft.title)}-${today}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "EducationMaterial",
      entityId: `education-template-draft-${slugify(templateDraft.title)}-${today}`,
      summary: allowed
        ? "Preview tao education template draft; chua ghi DB production va chua duoc dung voi nguoi benh."
        : "Chan preview tao education template draft do thieu role, scope, xac nhan hoac noi dung review."
    }),
    requiredServerSideGuards: [
      "Re-read actor role and clinic scope inside server action.",
      "Call authorizeBackendAction with clinical_rules.manage and active same-organization/session permission.",
      "Create EducationMaterial draft and append-only AuditLog in one transaction.",
      "Require separate EducationMaterialApproval before template can be printed or sent.",
      "Reject free-text medication changes, diagnoses or treatment directives in patient-facing sections."
    ],
    safetyBoundary:
      "Preview nay chi tao template draft, khong phe duyet noi dung, khong dung cho nguoi benh va khong gui thong diep dieu tri."
  };
}

export function createEducationTemplateDraftAction(
  templateDraft: EducationTemplateDraftInput,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewCreateEducationTemplateDraftAction(templateDraft, input, today);
  const templateId = `education-template-draft-${slugify(templateDraft.title)}-${today}`;
  return buildPersistentWorkflowActionPlan({
    actionName: "createEducationTemplateDraft",
    serverActionName: "createEducationTemplateDraftAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "EducationMaterial",
      entityId: templateId,
      summary: "Persistent plan tao education template draft; commit that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        templateId,
        status: "NOT_CREATED"
      },
      afterData: {
        templateId,
        conditionKeywordCount: templateDraft.conditionKeywords.length,
        sectionCount: templateDraft.sections.length,
        status: "DRAFT_REQUIRES_CONTENT_APPROVAL"
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "EducationMaterial",
      entityId: templateId,
      operation: "INSERT_EDUCATION_TEMPLATE_DRAFT",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        templateId,
        title: templateDraft.title,
        conditionKeywords: templateDraft.conditionKeywords,
        sections: templateDraft.sections,
        sourceNote: templateDraft.sourceNote,
        status: "DRAFT_REQUIRES_CONTENT_APPROVAL"
      },
      forbiddenSideEffects: [
        "NO_TEMPLATE_APPROVAL",
        "NO_PATIENT_USE",
        "NO_AUTOMATIC_PRINT",
        "NO_AUTOMATIC_PATIENT_MESSAGE"
      ]
    }
  });
}

export function previewRegisterPatientAction(
  registrationDraft: PatientRegistrationDraftInput,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "patient.register");
  const blockedReasons = [
    ...requireRole(
      input.actorRole,
      ["RECEPTIONIST", "NURSE", "NURSE_COORDINATOR", "PHYSICIAN", "CLINIC_ADMIN"],
      "Chi nhan su tiep don, dieu duong, bac si hoac admin phong kham moi duoc dang ky nguoi benh."
    ),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan da kiem tra dinh danh, consent va site tiep nhan."),
    ...(registrationDraft.fullName.trim() ? [] : ["Ho ten nguoi benh khong duoc trong."]),
    ...requireIsoDate(registrationDraft.dateOfBirth, "Ngay sinh"),
    ...(registrationDraft.phone.trim() ? [] : ["So dien thoai lien he khong duoc trong."]),
    ...(registrationDraft.intakeReason.trim() ? [] : ["Can ghi ly do dang ky/nguon tiep nhan."]),
    ...(registrationDraft.chronicProgramCandidates.length > 0 ? [] : ["Can chon it nhat mot chuong trinh benh man can sang loc."]),
    ...(registrationDraft.consentStatus === "DECLINED"
      ? ["Consent dang DECLINED; khong duoc dua vao workflow benh man hoac lien he chu dong."]
      : [])
  ];
  const allowed = blockedReasons.length === 0;
  const draftId = `patient-registration-${slugify(registrationDraft.fullName)}-${today}`;

  return {
    actionName: "registerPatient",
    serverActionName: "registerPatientAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-${draftId}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "Patient",
      entityId: draftId,
      summary: allowed
        ? "Preview dang ky nguoi benh moi; chua ghi DB production va chua mo lien he tu dong."
        : "Chan preview dang ky nguoi benh do thieu role, scope, consent hoac thong tin bat buoc."
    }),
    requiredServerSideGuards: [
      "Re-check identity fields, duplicate MRN/contact and active clinic scope inside server action.",
      "Call authorizeBackendAction with patient.register and active same-organization/session permission.",
      "Create Patient, PatientIdentifier/PatientContact, consent record and append-only AuditLog in one transaction.",
      "Require signed consent before any patient communication, portal invite or chronic-care outreach.",
      "Do not create diagnoses, medications, care plans, lab orders or treatment messages from registration."
    ],
    safetyBoundary:
      "Preview nay chi dang ky ho so hanh chinh ban dau, khong chan doan, khong ke don, khong tao care plan va khong gui tin nhan tu dong."
  };
}

export function registerPatientAction(
  registrationDraft: PatientRegistrationDraftInput,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewRegisterPatientAction(registrationDraft, input, today);
  const registrationId = `patient-registration-pending-${today}`;
  return buildPersistentWorkflowActionPlan({
    actionName: "registerPatient",
    serverActionName: "registerPatientAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "Patient",
      entityId: registrationId,
      summary: "Persistent plan dang ky nguoi benh; audit payload khong chua ten/phone/email va commit that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        registrationId,
        status: "NOT_CREATED"
      },
      afterData: {
        registrationId,
        sex: registrationDraft.sex,
        consentStatus: registrationDraft.consentStatus,
        chronicProgramCandidateCount: registrationDraft.chronicProgramCandidates.length,
        piiStoredOnlyInBusinessWrite: true
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "Patient",
      entityId: registrationId,
      operation: "INSERT_PATIENT_REGISTRATION",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        registrationId,
        identityFields: "STORE_IN_PATIENT_IDENTIFIER_AND_CONTACT_TABLES_ONLY",
        dateOfBirth: registrationDraft.dateOfBirth,
        sex: registrationDraft.sex,
        consentStatus: registrationDraft.consentStatus,
        intakeReason: registrationDraft.intakeReason,
        chronicProgramCandidates: registrationDraft.chronicProgramCandidates
      },
      forbiddenSideEffects: [
        "NO_DIAGNOSIS",
        "NO_CARE_PLAN",
        "NO_PATIENT_PORTAL_INVITE",
        "NO_AUTOMATIC_OUTREACH"
      ]
    }
  });
}

export function previewCreateClinicalRuleDraftAction(
  ruleDraft: ClinicalRuleDraftInput,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "clinical_rules.manage");
  const blockedReasons = [
    ...requireRole(input.actorRole, ["CLINIC_ADMIN", "PHYSICIAN"], "Chi admin phong kham hoac bac si moi duoc tao clinical rule draft."),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan rule draft can hoi dong/bac si duyet rieng truoc khi active."),
    ...(ruleDraft.ruleName.trim() ? [] : ["Ten rule khong duoc trong."]),
    ...(ruleDraft.ruleDescription.trim() ? [] : ["Mo ta rule khong duoc trong."]),
    ...(ruleDraft.suggestedAction.trim() ? [] : ["Suggested action khong duoc trong."]),
    ...(ruleDraft.referenceSource?.trim() ? [] : ["Can ghi nguon guideline/SOP noi bo de review."]),
    ...(ruleDraft.requiresPhysicianConfirmation ? [] : ["Clinical rule draft phai bat buoc bac si xac nhan khi ap dung."]),
    ...requireIsoDate(ruleDraft.effectiveDate, "Ngay hieu luc du kien"),
    ...requireIsoDate(ruleDraft.reviewDate, "Ngay review"),
    ...requireReviewAfterEffectiveDate(ruleDraft.effectiveDate, ruleDraft.reviewDate)
  ];
  const allowed = blockedReasons.length === 0;
  const draftId = `clinical-rule-draft-${slugify(ruleDraft.ruleName)}-${today}`;

  return {
    actionName: "createClinicalRuleDraft",
    serverActionName: "createClinicalRuleDraftAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-${draftId}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "ClinicalRule",
      entityId: draftId,
      summary: allowed
        ? "Preview tao ClinicalRule draft; chua ghi DB production va chua active rule engine."
        : "Chan preview tao ClinicalRule draft do thieu role, scope, xac nhan hoac noi dung review."
    }),
    requiredServerSideGuards: [
      "Re-read actor role, clinic scope and latest active rule versions inside server action.",
      "Call authorizeBackendAction with clinical_rules.manage and active same-organization/session permission.",
      "Create ClinicalRuleVersion draft and append-only AuditLog in one transaction.",
      "Require separate ClinicalRuleApproval before rule can become active or affect risk scoring.",
      "Reject rules that remove physician confirmation, create diagnoses, prescribe, order labs or send treatment messages."
    ],
    safetyBoundary:
      "Preview nay chi tao clinical rule draft, khong kich hoat rule engine, khong tu chan doan, khong ke don va khong thay doi muc nguy co that."
  };
}

export function createClinicalRuleDraftAction(
  ruleDraft: ClinicalRuleDraftInput,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewCreateClinicalRuleDraftAction(ruleDraft, input, today);
  const ruleDraftId = `clinical-rule-draft-${slugify(ruleDraft.ruleName)}-${today}`;
  return buildPersistentWorkflowActionPlan({
    actionName: "createClinicalRuleDraft",
    serverActionName: "createClinicalRuleDraftAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "ClinicalRule",
      entityId: ruleDraftId,
      summary: "Persistent plan tao clinical rule draft; commit/active rule engine van bi tat cho den khi co DB transaction test.",
      beforeData: {
        ruleDraftId,
        status: "NOT_CREATED"
      },
      afterData: {
        ruleDraftId,
        severity: ruleDraft.severity,
        requiresPhysicianConfirmation: ruleDraft.requiresPhysicianConfirmation,
        effectiveDate: ruleDraft.effectiveDate,
        reviewDate: ruleDraft.reviewDate
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "ClinicalRule",
      entityId: ruleDraftId,
      operation: "INSERT_CLINICAL_RULE_DRAFT",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        ruleDraftId,
        ruleName: ruleDraft.ruleName,
        ruleDescription: ruleDraft.ruleDescription,
        purpose: ruleDraft.purpose,
        scope: ruleDraft.scope,
        referenceSource: ruleDraft.referenceSource,
        severity: ruleDraft.severity,
        suggestedAction: ruleDraft.suggestedAction,
        requiresPhysicianConfirmation: true,
        version: ruleDraft.version,
        effectiveDate: ruleDraft.effectiveDate,
        reviewDate: ruleDraft.reviewDate,
        limitationNotes: ruleDraft.limitationNotes,
        status: "DRAFT_REQUIRES_CLINICAL_APPROVAL"
      },
      forbiddenSideEffects: [
        "NO_RULE_ENGINE_ACTIVATION",
        "NO_RISK_SCORE_CHANGE",
        "NO_DIAGNOSIS",
        "NO_PRESCRIPTION",
        "NO_PATIENT_MESSAGE"
      ]
    }
  });
}

export function previewInviteUserAction(
  inviteDraft: UserInviteDraftInput,
  input: WorkflowActionInput,
  today = "2026-06-19"
): WorkflowActionPreview {
  const backendGuard = authorizeWorkflowAction(input, "user.manage");
  const blockedReasons = [
    ...requireRole(input.actorRole, ["SUPER_ADMIN", "CLINIC_ADMIN"], "Chi super admin hoac clinic admin moi duoc moi nguoi dung noi bo."),
    ...requireBackendGuard(backendGuard),
    ...requireConfirmation(input, "Nguoi thuc hien phai xac nhan vai tro, site va ly do moi nguoi dung."),
    ...(inviteDraft.name.trim() ? [] : ["Ten nguoi dung khong duoc trong."]),
    ...requireEmail(inviteDraft.email),
    ...(inviteDraft.organizationId === input.resourceScope.organizationId ? [] : ["Invite phai nam trong cung organization scope."]),
    ...(inviteDraft.clinicSiteId === input.resourceScope.clinicSiteId ? [] : ["Invite phai nam trong cung clinic site scope."]),
    ...(inviteDraft.invitationReason.trim() ? [] : ["Can ghi ly do moi nguoi dung."])
  ];
  const allowed = blockedReasons.length === 0;
  const draftId = `user-invite-${slugify(inviteDraft.email)}-${today}`;

  return {
    actionName: "inviteUser",
    serverActionName: "inviteUserAction",
    status: allowed ? "READY_FOR_SERVER_ACTION" : "BLOCKED",
    allowed,
    persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
    blockedReasons,
    backendGuard,
    auditPreview: buildAuditPreview({
      id: `audit-action-${draftId}`,
      actorName: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "UserInvite",
      entityId: draftId,
      summary: allowed
        ? "Preview moi nguoi dung noi bo; chua ghi DB production va chua gui email moi."
        : "Chan preview moi nguoi dung do thieu role, scope, email hoac ly do."
    }),
    requiredServerSideGuards: [
      "Re-check active organization, clinic site, duplicate email and inviter session inside server action.",
      "Call authorizeBackendAction with user.manage and active same-organization/session permission.",
      "Create User invitation, scoped UserRole assignment and append-only AuditLog in one transaction.",
      "Reject privilege escalation, SUPER_ADMIN invites, patient-account invites and cross-site role assignment.",
      "Do not create passwords, sessions, MFA state or send invite email until mail delivery is explicitly approved."
    ],
    safetyBoundary:
      "Preview nay chi tao loi moi noi bo, khong tao tai khoan dang nhap hoat dong, khong gui email that va khong cap quyen vuot scope."
  };
}

export function inviteUserAction(
  inviteDraft: UserInviteDraftInput,
  input: WorkflowActionInput,
  existingLedger: AuditLedgerEntry[],
  today = "2026-06-19"
): PersistentWorkflowActionPlan {
  const preview = previewInviteUserAction(inviteDraft, input, today);
  const inviteId = `user-invite-${slugify(inviteDraft.role)}-${today}`;
  return buildPersistentWorkflowActionPlan({
    actionName: "inviteUser",
    serverActionName: "inviteUserAction",
    preview,
    existingLedger,
    auditIntent: {
      userId: null,
      actor: input.actorName,
      actorRole: input.actorRole,
      actionType: "CREATE",
      entityType: "UserInvite",
      entityId: inviteId,
      summary: "Persistent plan moi nguoi dung noi bo; audit payload khong chua email va commit/gui that van bi tat cho den khi co DB transaction test.",
      beforeData: {
        inviteId,
        status: "NOT_CREATED"
      },
      afterData: {
        inviteId,
        role: inviteDraft.role,
        organizationId: inviteDraft.organizationId,
        clinicSiteId: inviteDraft.clinicSiteId,
        emailStoredOnlyInBusinessWrite: true
      },
      createdAt: `${today}T00:00:00+07:00`
    },
    businessWritePlan: {
      entityType: "UserInvite",
      entityId: inviteId,
      operation: "INSERT_USER_INVITE",
      requiredAtomicWithAuditLog: true,
      productionCommitDisabled: true,
      writeSet: {
        inviteId,
        name: inviteDraft.name,
        email: inviteDraft.email,
        role: inviteDraft.role,
        organizationId: inviteDraft.organizationId,
        clinicSiteId: inviteDraft.clinicSiteId,
        invitationReason: inviteDraft.invitationReason,
        status: "DRAFT_INVITE_NOT_SENT"
      },
      forbiddenSideEffects: [
        "NO_EMAIL_SEND",
        "NO_ACTIVE_ACCOUNT",
        "NO_PASSWORD_CREATION",
        "NO_SESSION_CREATION",
        "NO_PRIVILEGE_ESCALATION"
      ]
    }
  });
}

function authorizeWorkflowAction(input: WorkflowActionInput, permission: Permission): GuardDecision {
  return authorizeBackendAction(input.accessContext, permission, input.resourceScope);
}

function buildPersistentWorkflowActionPlan(input: {
  actionName: PersistentWorkflowActionPlan["actionName"];
  serverActionName: PersistentWorkflowActionPlan["serverActionName"];
  preview: WorkflowActionPreview;
  existingLedger: AuditLedgerEntry[];
  auditIntent: Parameters<typeof buildPersistentAuditWritePlan>[1];
  businessWritePlan: PersistentBusinessWritePlan;
}): PersistentWorkflowActionPlan {
  if (!input.preview.allowed) {
    return {
      actionName: input.actionName,
      serverActionName: input.serverActionName,
      status: "BLOCKED",
      allowed: false,
      persistenceMode: "PERSISTENT_PLAN_NOT_COMMITTED",
      preview: input.preview,
      auditWritePlan: null,
      auditValidation: {
        valid: false,
        reason: "Preview gates blocked; persistent write plan was not built.",
        blockedReasons: input.preview.blockedReasons
      },
      businessWritePlan: null,
      blockedReasons: input.preview.blockedReasons,
      transactionContract: persistentTransactionContract(),
      safetyBoundary:
        "Khong ghi DB khi preview gate bi chan; khong co audit/business write rieng le."
    };
  }

  const auditWritePlan = buildPersistentAuditWritePlan(input.existingLedger, input.auditIntent);
  const auditValidation = validatePersistentAuditWritePlan(input.existingLedger, auditWritePlan);
  const blockedReasons = auditValidation.valid ? [] : auditValidation.blockedReasons;
  const allowed = blockedReasons.length === 0;

  return {
    actionName: input.actionName,
    serverActionName: input.serverActionName,
    status: allowed ? "READY_FOR_ATOMIC_COMMIT_WHEN_DB_WIRING_EXISTS" : "BLOCKED",
    allowed,
    persistenceMode: "PERSISTENT_PLAN_NOT_COMMITTED",
    preview: input.preview,
    auditWritePlan,
    auditValidation,
    businessWritePlan: allowed ? input.businessWritePlan : null,
    blockedReasons,
    transactionContract: persistentTransactionContract(),
    safetyBoundary:
      "Persistent plan nay chi mo ta write set; production commit van disabled cho den khi AuditLog insert va business write duoc test atomically."
  };
}

function persistentTransactionContract(): string[] {
  return [
    "Start one database transaction and re-read all source rows with the same organization/site scope.",
    "Apply exactly one business write and exactly one AuditLog insert inside that transaction.",
    "Validate AuditLog sequence, previousHash and eventHash immediately before commit.",
    "Rollback both business write and AuditLog insert if either side fails.",
    "Do not emit patient messages, prescriptions, medication changes or external EMR writes from these actions."
  ];
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

function requireIsoDate(value: string, label: string): string[] {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) ? [] : [`${label} phai theo dinh dang YYYY-MM-DD.`];
}

function requireReviewAfterEffectiveDate(effectiveDate: string, reviewDate: string): string[] {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(effectiveDate) || !/^\d{4}-\d{2}-\d{2}$/.test(reviewDate)) return [];
  return reviewDate > effectiveDate ? [] : ["Ngay review phai sau ngay hieu luc du kien."];
}

function requireEmail(value: string): string[] {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value) ? [] : ["Email moi nguoi dung khong hop le."];
}

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "untitled";
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
