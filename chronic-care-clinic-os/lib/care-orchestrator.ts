import { assessRisk, hasDuplicateMedicationClass } from "./clinical-safety";
import { isPatientCommunicationAllowed } from "./automation";
import { reviewProgramEnrollments } from "./program-registry";
import type { Patient, RiskLevel, Role } from "./types";

export type CareGapCategory =
  | "SAFETY"
  | "FOLLOW_UP"
  | "LAB_REVIEW"
  | "MEDICATION"
  | "CARE_PLAN"
  | "EDUCATION"
  | "POST_DISCHARGE"
  | "ADHERENCE"
  | "PROGRAM_MONITORING";

export type CareGapPriority = "LOW" | "MEDIUM" | "HIGH" | "URGENT";

export type CareGap = {
  id: string;
  patientId: string;
  patientName: string;
  medicalRecordNumber: string;
  category: CareGapCategory;
  priority: CareGapPriority;
  riskLevel: RiskLevel;
  assignedRole: Role;
  dueDate: string;
  title: string;
  reason: string;
  recommendedAction: string;
  requiresPhysicianConfirmation: true;
  patientCommunicationAllowed: boolean;
  sourceRules: string[];
};

export type CommandCenterSnapshot = {
  generatedAt: string;
  totalPatients: number;
  activeCareGaps: number;
  urgentCareGaps: number;
  physicianReview: number;
  nurseQueue: number;
  coordinatorQueue: number;
  pharmacistQueue: number;
  blockedPatientMessages: number;
  redPatients: number;
  yellowPatients: number;
  carePlanApprovalQueue: number;
  labReviewQueue: number;
  medicationReviewQueue: number;
  followUpRecoveryQueue: number;
  programMonitoringQueue: number;
  queue: CareGap[];
};

const priorityRank: Record<CareGapPriority, number> = {
  URGENT: 0,
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3
};

const riskRank: Record<RiskLevel, number> = {
  RED: 0,
  YELLOW: 1,
  GREEN: 2
};

export function buildCommandCenterSnapshot(patients: Patient[], today = "2026-06-19"): CommandCenterSnapshot {
  const queue = patients.flatMap((patient) => buildCareGaps(patient, today)).sort(compareCareGaps);
  return {
    generatedAt: today,
    totalPatients: patients.length,
    activeCareGaps: queue.length,
    urgentCareGaps: queue.filter((gap) => gap.priority === "URGENT").length,
    physicianReview: queue.filter((gap) => gap.assignedRole === "PHYSICIAN").length,
    nurseQueue: queue.filter((gap) => gap.assignedRole === "NURSE").length,
    coordinatorQueue: queue.filter((gap) => gap.assignedRole === "CARE_COORDINATOR").length,
    pharmacistQueue: queue.filter((gap) => gap.assignedRole === "PHARMACIST").length,
    blockedPatientMessages: queue.filter((gap) => !gap.patientCommunicationAllowed).length,
    redPatients: patients.filter((patient) => patient.suggestedRiskLevel === "RED").length,
    yellowPatients: patients.filter((patient) => patient.suggestedRiskLevel === "YELLOW").length,
    carePlanApprovalQueue: queue.filter((gap) => gap.category === "CARE_PLAN").length,
    labReviewQueue: queue.filter((gap) => gap.category === "LAB_REVIEW").length,
    medicationReviewQueue: queue.filter((gap) => gap.category === "MEDICATION").length,
    followUpRecoveryQueue: queue.filter((gap) => gap.category === "FOLLOW_UP").length,
    programMonitoringQueue: queue.filter((gap) => gap.category === "PROGRAM_MONITORING").length,
    queue
  };
}

export function buildCareGaps(patient: Patient, today = "2026-06-19"): CareGap[] {
  const assessment = assessRisk(patient);
  const gaps: CareGap[] = [];
  const activeMedicationCount = patient.medications.filter((medication) => medication.isActive).length;
  const communicationConsent = patient.consentStatus === "SIGNED";
  const hasApprovedTemplate = true;

  if (assessment.suggestedRiskLevel === "RED") {
    gaps.push(
      careGap(patient, {
        category: "SAFETY",
        priority: "URGENT",
        riskLevel: "RED",
        assignedRole: "PHYSICIAN",
        dueDate: today,
        title: "Danh gia truc tiep co do",
        reason: assessment.triggeredRules.map((rule) => rule.ruleDescription).join(" | "),
        recommendedAction: assessment.safetyMessage ?? "Can bac si danh gia truc tiep ngay.",
        patientCommunicationAllowed: false,
        sourceRules: assessment.triggeredRules.map((rule) => rule.ruleName)
      })
    );
  }

  const noShow = patient.appointments.some((appointment) => appointment.status === "NO_SHOW");
  if ((patient.missedAppointments ?? 0) > 0 || noShow) {
    gaps.push(
      careGap(patient, {
        category: "FOLLOW_UP",
        priority: "HIGH",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "CARE_COORDINATOR",
        dueDate: today,
        title: "Khoi phuc lien he sau bo hen",
        reason: "Nguoi benh bo hen hoac qua han tai kham.",
        recommendedAction: "Goi nhac bang kich ban da duyet, dat lai lich va bao bac si neu khong lien he duoc.",
        patientCommunicationAllowed: isPatientCommunicationAllowed("APPOINTMENT_REMINDER", hasApprovedTemplate, communicationConsent),
        sourceRules: ["AUTO-001", "AUTO-005"]
      })
    );
  }

  const labsForReview = patient.labs.filter((lab) => lab.reviewStatus === "NEW" || lab.abnormalFlag !== "NORMAL");
  for (const lab of labsForReview) {
    gaps.push(
      careGap(patient, {
        category: "LAB_REVIEW",
        priority: lab.abnormalFlag === "CRITICAL" ? "URGENT" : "HIGH",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "PHYSICIAN",
        dueDate: today,
        title: `Bac si xem ${lab.testName}`,
        reason: `${lab.testName}: ${lab.resultValue} ${lab.unit}, flag ${lab.abnormalFlag}, status ${lab.reviewStatus}.`,
        recommendedAction: "Doi chieu boi canh lam sang va ghi nhan da review; khong tu dong thay doi dieu tri.",
        patientCommunicationAllowed: false,
        sourceRules: ["AUTO-008"]
      })
    );
  }

  if (activeMedicationCount >= 5 || hasDuplicateMedicationClass(patient)) {
    gaps.push(
      careGap(patient, {
        category: "MEDICATION",
        priority: "HIGH",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "PHARMACIST",
        dueDate: addDays(today, 1),
        title: "Ra soat da thuoc va trung nhom",
        reason: `${activeMedicationCount} thuoc/che pham dang hoat dong${hasDuplicateMedicationClass(patient) ? ", co trung nhom" : ""}.`,
        recommendedAction: "Lap danh sach can hoi lai nguoi benh va gui bac si/duoc si xac nhan.",
        patientCommunicationAllowed: false,
        sourceRules: ["AUTO-007", "polypharmacy_review"]
      })
    );
  }

  if (patient.carePlan.status === "PENDING_APPROVAL" || patient.carePlan.status === "DRAFT") {
    gaps.push(
      careGap(patient, {
        category: "CARE_PLAN",
        priority: assessment.suggestedRiskLevel === "RED" ? "URGENT" : "MEDIUM",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "PHYSICIAN",
        dueDate: assessment.suggestedRiskLevel === "RED" ? today : addDays(today, 2),
        title: "Duyet care plan ca the hoa",
        reason: `Care plan dang o trang thai ${patient.carePlan.status}.`,
        recommendedAction: "Bac si xac nhan muc tieu, lich theo doi, xet nghiem va dieu kien chuyen tuyen.",
        patientCommunicationAllowed: false,
        sourceRules: ["AUTO-003", "AUTO-009"]
      })
    );
  }

  if (patient.recentHospitalization) {
    gaps.push(
      careGap(patient, {
        category: "POST_DISCHARGE",
        priority: "HIGH",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "NURSE",
        dueDate: today,
        title: "Checklist sau xuat vien",
        reason: "Nguoi benh moi xuat vien can doi chieu thuoc, giay ra vien va lich tai kham.",
        recommendedAction: "Thu thap tom tat ra vien, doi chieu thuoc va chuyen bac si neu co thong tin thieu.",
        patientCommunicationAllowed: isPatientCommunicationAllowed("PRE_VISIT_PREP", hasApprovedTemplate, communicationConsent),
        sourceRules: ["AUTO-006"]
      })
    );
  }

  if (patient.medications.some((medication) => medication.adherenceStatus === "LOW" || medication.adherenceStatus === "PARTIAL")) {
    gaps.push(
      careGap(patient, {
        category: "ADHERENCE",
        priority: "MEDIUM",
        riskLevel: assessment.suggestedRiskLevel,
        assignedRole: "NURSE",
        dueDate: addDays(today, 3),
        title: "Danh gia rao can tuan thu",
        reason: "Ho so co dau hieu tuan thu thuoc chua tot.",
        recommendedAction: "Dung teach-back va phan loai rao can; khong gui loi khuyen dieu tri tu dong.",
        patientCommunicationAllowed: isPatientCommunicationAllowed("APPROVED_EDUCATION_READY", hasApprovedTemplate, communicationConsent),
        sourceRules: ["AUTO-011"]
      })
    );
  }

  for (const review of reviewProgramEnrollments(patient, today)) {
    for (const monitor of review.monitors.filter((item) => item.status !== "CURRENT")) {
      gaps.push(
        careGap(patient, {
          category: "PROGRAM_MONITORING",
          priority: monitor.status === "OVERDUE" || monitor.status === "MISSING" ? "MEDIUM" : "LOW",
          riskLevel: review.riskLevel,
          assignedRole: monitor.assignedRole,
          dueDate: monitor.dueDate ?? today,
          title: `${review.programName}: ${monitor.label}`,
          reason: `${monitor.reason} Trang thai: ${monitor.status}.`,
          recommendedAction: "Bo sung du lieu theo doi hoac len lich theo SOP; neu thay doi quyet dinh lam sang thi can bac si xac nhan.",
          patientCommunicationAllowed: false,
          sourceRules: [`PROGRAM-${review.programId}`, monitor.monitorId]
        })
      );
    }
  }

  return deduplicateGaps(gaps).sort(compareCareGaps);
}

function careGap(
  patient: Patient,
  fields: Omit<CareGap, "id" | "patientId" | "patientName" | "medicalRecordNumber" | "requiresPhysicianConfirmation">
): CareGap {
  return {
    id: `${patient.id}-${fields.category.toLowerCase()}-${fields.sourceRules[0]}`,
    patientId: patient.id,
    patientName: patient.fullName,
    medicalRecordNumber: patient.medicalRecordNumber,
    requiresPhysicianConfirmation: true,
    ...fields
  };
}

function deduplicateGaps(gaps: CareGap[]): CareGap[] {
  const seen = new Set<string>();
  return gaps.filter((gap) => {
    const key = `${gap.patientId}-${gap.category}-${gap.title}`;
    if (seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function compareCareGaps(a: CareGap, b: CareGap): number {
  return (
    priorityRank[a.priority] - priorityRank[b.priority] ||
    riskRank[a.riskLevel] - riskRank[b.riskLevel] ||
    a.dueDate.localeCompare(b.dueDate) ||
    a.patientName.localeCompare(b.patientName)
  );
}

function addDays(date: string, days: number): string {
  const [year, month, day] = date.split("-").map(Number);
  const value = new Date(year, month - 1, day);
  value.setDate(value.getDate() + days);
  return [
    value.getFullYear(),
    String(value.getMonth() + 1).padStart(2, "0"),
    String(value.getDate()).padStart(2, "0")
  ].join("-");
}
