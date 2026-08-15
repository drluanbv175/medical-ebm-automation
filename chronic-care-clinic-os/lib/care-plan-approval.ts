import { buildCarePlanDraftQueue } from "./care-plan-draft";
import type { AuditEvent } from "./audit";
import type { CarePlanDraft } from "./care-plan-draft";
import type { Patient, Role } from "./types";

export type ApprovalGateStatus = "PASS" | "BLOCK";

export type CarePlanApprovalGate = {
  gateId: string;
  label: string;
  ownerRole: Role;
  status: ApprovalGateStatus;
  evidence: string;
};

export type CarePlanVersionPreview = {
  versionId: string;
  carePlanId: string;
  versionNumber: number;
  status: "PENDING_APPROVAL";
  generatedFromDraftId: string;
  effectiveDate: string;
  changeSummary: string[];
  immutableAfterApproval: true;
};

export type CarePlanApprovalPackage = {
  packageId: string;
  patientId: string;
  patientName: string;
  medicalRecordNumber: string;
  draftId: string;
  gateStatus: "READY_FOR_PHYSICIAN_SIGNOFF" | "BLOCKED_REQUIRES_DIRECT_REVIEW";
  approvalActionAllowed: boolean;
  patientCommunicationAllowedAfterApproval: boolean;
  gates: CarePlanApprovalGate[];
  blockedReasons: string[];
  versionPreview: CarePlanVersionPreview;
  auditPreview: AuditEvent;
  signoffInstructions: string[];
  writebackMode: "PREVIEW_ONLY_REQUIRES_SERVER_ACTION_AND_AUDIT";
  safetyBoundary: string;
};

export function buildCarePlanApprovalPackage(
  patient: Patient,
  draft: CarePlanDraft,
  today = "2026-06-19"
): CarePlanApprovalPackage {
  const gates = buildApprovalGates(patient, draft);
  const blockedReasons = gates
    .filter((gate) => gate.status === "BLOCK")
    .map((gate) => `${gate.label}: ${gate.evidence}`);
  const approvalActionAllowed = blockedReasons.length === 0;

  return {
    packageId: `approval-${draft.draftId}`,
    patientId: patient.id,
    patientName: patient.fullName,
    medicalRecordNumber: patient.medicalRecordNumber,
    draftId: draft.draftId,
    gateStatus: approvalActionAllowed ? "READY_FOR_PHYSICIAN_SIGNOFF" : "BLOCKED_REQUIRES_DIRECT_REVIEW",
    approvalActionAllowed,
    patientCommunicationAllowedAfterApproval: approvalActionAllowed && patient.consentStatus === "SIGNED",
    gates,
    blockedReasons,
    versionPreview: {
      versionId: `cpv-${patient.carePlan.id}-${today}`,
      carePlanId: patient.carePlan.id,
      versionNumber: patient.carePlan.status === "APPROVED" ? 2 : 1,
      status: "PENDING_APPROVAL",
      generatedFromDraftId: draft.draftId,
      effectiveDate: today,
      changeSummary: [
        `Risk level de xuat: ${draft.riskLevel}.`,
        `So care gaps nguon: ${draft.sourceGapIds.length}.`,
        `So muc can bac si/doi ngu phe duyet: ${draft.approvalChecklist.length}.`
      ],
      immutableAfterApproval: true
    },
    auditPreview: {
      id: `audit-preview-${patient.id}-${today}`,
      actor: "SYSTEM_PREVIEW",
      actorRole: "READ_ONLY_AUDITOR",
      actionType: "CREATE",
      entityType: "CarePlanVersion",
      entityId: patient.carePlan.id,
      summary: approvalActionAllowed
        ? "Tao preview version care plan cho bac si ky duyet; chua ghi production."
        : "Chan preview ky duyet care plan vi con gate can danh gia truc tiep.",
      createdAt: `${today}T00:00:00+07:00`
    },
    signoffInstructions: [
      "Bac si mo ho so nguoi benh, xac nhan risk va muc tieu ca the hoa.",
      "Chi ky duyet sau khi cac gate PASS va lab/thuoc/co do da duoc xem.",
      "Khi co server action that, moi lan ky duyet phai tao CarePlanVersion bat bien va AuditLog append-only.",
      "Sau phe duyet, giao tiep voi nguoi benh chi duoc dung template da duyet va consent hop le."
    ],
    writebackMode: "PREVIEW_ONLY_REQUIRES_SERVER_ACTION_AND_AUDIT",
    safetyBoundary:
      "Goi phe duyet nay khong ghi DB, khong ky thay bac si, khong tu dong gui loi dan va khong tao thay doi dieu tri."
  };
}

export function buildCarePlanApprovalQueue(patients: Patient[], today = "2026-06-19"): CarePlanApprovalPackage[] {
  const drafts = buildCarePlanDraftQueue(patients, today);
  return drafts
    .map((draft) => {
      const patient = patients.find((item) => item.id === draft.patientId);
      return patient ? buildCarePlanApprovalPackage(patient, draft, today) : null;
    })
    .filter((item): item is CarePlanApprovalPackage => item !== null)
    .sort(
      (a, b) =>
        Number(b.approvalActionAllowed) - Number(a.approvalActionAllowed) ||
        b.blockedReasons.length - a.blockedReasons.length
    );
}

function buildApprovalGates(patient: Patient, draft: CarePlanDraft): CarePlanApprovalGate[] {
  const abnormalNewLabs = patient.labs.filter((lab) => lab.abnormalFlag !== "NORMAL" && lab.reviewStatus === "NEW");
  const activeMedicationCount = patient.medications.filter((medication) => medication.isActive).length;
  const hasRedFlag = patient.redFlags.length > 0 || draft.riskLevel === "RED";
  const hasSignedConsent = patient.consentStatus === "SIGNED";

  return [
    {
      gateId: "risk-signoff",
      label: "Bac si xac nhan muc nguy co",
      ownerRole: "PHYSICIAN",
      status: hasRedFlag ? "BLOCK" : "PASS",
      evidence: hasRedFlag
        ? "Co co do hoac RED risk, can danh gia truc tiep truoc khi ky."
        : `Risk de xuat ${draft.riskLevel}, khong co co do trong demo.`
    },
    {
      gateId: "lab-review",
      label: "Lab bat thuong da duoc xem",
      ownerRole: "PHYSICIAN",
      status: abnormalNewLabs.length > 0 ? "BLOCK" : "PASS",
      evidence:
        abnormalNewLabs.length > 0
          ? `${abnormalNewLabs.length} lab bat thuong moi can bac si acknowledge.`
          : "Khong co lab bat thuong moi chua xem."
    },
    {
      gateId: "medication-reconciliation",
      label: "Ra soat thuoc khi da thuoc",
      ownerRole: activeMedicationCount >= 5 ? "PHARMACIST" : "PHYSICIAN",
      status: activeMedicationCount >= 5 ? "BLOCK" : "PASS",
      evidence:
        activeMedicationCount >= 5
          ? `${activeMedicationCount} thuoc/che pham dang hoat dong, can reconciliation truoc phe duyet.`
          : `${activeMedicationCount} thuoc/che pham dang hoat dong.`
    },
    {
      gateId: "patient-communication-consent",
      label: "Consent giao tiep voi nguoi benh hop le",
      ownerRole: "CARE_COORDINATOR",
      status: hasSignedConsent ? "PASS" : "BLOCK",
      evidence: hasSignedConsent ? "Consent SIGNED trong du lieu demo." : `Consent hien tai: ${patient.consentStatus}.`
    },
    {
      gateId: "approval-checklist-present",
      label: "Checklist phe duyet duoc tao",
      ownerRole: "PHYSICIAN",
      status: draft.approvalChecklist.length > 0 ? "PASS" : "BLOCK",
      evidence: `${draft.approvalChecklist.length} muc checklist can ky duyet.`
    }
  ];
}
