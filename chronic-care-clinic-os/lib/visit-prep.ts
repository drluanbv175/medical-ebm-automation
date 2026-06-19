import { buildCareGaps } from "./care-orchestrator";
import { reviewProgramEnrollments } from "./program-registry";
import type { CareGap } from "./care-orchestrator";
import type { Patient, Role } from "./types";

export type VisitPrepChecklistItem = {
  label: string;
  ownerRole: Role;
  done: boolean;
  note: string;
};

export type VisitPrepPacket = {
  patientId: string;
  patientName: string;
  medicalRecordNumber: string;
  generatedAt: string;
  riskLevel: Patient["suggestedRiskLevel"];
  programNames: string[];
  checklist: VisitPrepChecklistItem[];
  clinicianReviewItems: CareGap[];
  nursingIntakePrompts: string[];
  medicationQuestions: string[];
  labReviewItems: string[];
  safetyBoundary: string;
};

export function buildVisitPrepPacket(patient: Patient, today = "2026-06-19"): VisitPrepPacket {
  const careGaps = buildCareGaps(patient, today);
  const programReviews = reviewProgramEnrollments(patient, today);
  const abnormalLabs = patient.labs.filter((lab) => lab.reviewStatus === "NEW" || lab.abnormalFlag !== "NORMAL");
  const activeMedications = patient.medications.filter((medication) => medication.isActive);
  const openProgramMonitors = programReviews.flatMap((review) =>
    review.monitors
      .filter((monitor) => monitor.status !== "CURRENT")
      .map((monitor) => `${review.programName}: ${monitor.label} (${monitor.status})`)
  );

  return {
    patientId: patient.id,
    patientName: patient.fullName,
    medicalRecordNumber: patient.medicalRecordNumber,
    generatedAt: today,
    riskLevel: patient.suggestedRiskLevel,
    programNames: programReviews.map((review) => review.programName),
    checklist: buildChecklist(patient, careGaps, abnormalLabs.length, openProgramMonitors.length),
    clinicianReviewItems: careGaps.filter((gap) => gap.assignedRole === "PHYSICIAN").slice(0, 8),
    nursingIntakePrompts: buildNursingPrompts(patient, openProgramMonitors),
    medicationQuestions: buildMedicationQuestions(patient, activeMedications.length),
    labReviewItems: abnormalLabs.map((lab) => `${lab.testName}: ${lab.resultValue} ${lab.unit} (${lab.abnormalFlag}, ${lab.reviewStatus})`),
    safetyBoundary:
      "Goi y trong packet nay chi de chuan bi buoi kham. Khong tu chan doan, khong tu ke don, khong tu thay doi dieu tri va khong gui loi khuyen dieu tri ca the hoa cho nguoi benh."
  };
}

export function buildVisitPrepQueue(patients: Patient[], today = "2026-06-19"): VisitPrepPacket[] {
  return patients
    .map((patient) => buildVisitPrepPacket(patient, today))
    .sort((a, b) => riskSort(a.riskLevel) - riskSort(b.riskLevel) || b.clinicianReviewItems.length - a.clinicianReviewItems.length);
}

function buildChecklist(
  patient: Patient,
  careGaps: CareGap[],
  abnormalLabCount: number,
  openProgramMonitorCount: number
): VisitPrepChecklistItem[] {
  return [
    {
      label: "Xac minh thong tin lien he va dong y giao tiep",
      ownerRole: "RECEPTIONIST",
      done: patient.consentStatus === "SIGNED",
      note: `Trang thai dong y: ${patient.consentStatus}`
    },
    {
      label: "Cap nhat sinh hieu va trieu chung co do",
      ownerRole: "NURSE",
      done: patient.vitals.length > 0 && patient.redFlags.length === 0,
      note: patient.redFlags.length > 0 ? "Co co do, uu tien bac si danh gia truc tiep." : "Can xac nhan tai buoi kham."
    },
    {
      label: "Doi chieu danh sach thuoc va tuan thu",
      ownerRole: "PHARMACIST",
      done: !careGaps.some((gap) => gap.category === "MEDICATION" || gap.category === "ADHERENCE"),
      note: "Hoi lai thuoc thuc te dang dung, OTC, thao duoc va tac dung khong mong muon."
    },
    {
      label: "Chuan bi lab/xet nghiem can bac si xem",
      ownerRole: "PHYSICIAN",
      done: abnormalLabCount === 0,
      note: abnormalLabCount > 0 ? `${abnormalLabCount} ket qua can review.` : "Khong co lab bat thuong moi trong demo."
    },
    {
      label: "Ra soat gap theo chuong trinh benh man",
      ownerRole: "CARE_COORDINATOR",
      done: openProgramMonitorCount === 0,
      note: openProgramMonitorCount > 0 ? `${openProgramMonitorCount} monitor sap den han/qua han/thieu.` : "Monitor chuong trinh dang hien hanh."
    },
    {
      label: "Chuan bi care plan va loi dan de bac si phe duyet",
      ownerRole: "PHYSICIAN",
      done: patient.carePlan.status === "APPROVED",
      note: `Care plan: ${patient.carePlan.status}`
    }
  ];
}

function buildNursingPrompts(patient: Patient, openProgramMonitors: string[]): string[] {
  const prompts = [
    "Nguoi benh co dau nguc, kho tho, yeu liet, ngat, lu lan, ha duong huyet nang hoac trieu chung nguy hiem nao khong?",
    "Sinh hieu tai phong kham co khac thuong so voi lan truoc khong?",
    "Nguoi benh co kho khan khi tu theo doi huyet ap/duong huyet hoac tai kham khong?"
  ];
  if ((patient.missedAppointments ?? 0) > 0) {
    prompts.push("Hoi ly do bo hen va rao can di lai, chi phi, lich lam viec, nguoi cham soc.");
  }
  if (openProgramMonitors.length > 0) {
    prompts.push(`Can thu thap/hen bo sung: ${openProgramMonitors.slice(0, 4).join("; ")}.`);
  }
  return prompts;
}

function buildMedicationQuestions(patient: Patient, activeMedicationCount: number): string[] {
  const questions = [
    "Nguoi benh co mang theo tat ca thuoc dang dung, ke ca OTC/thao duoc/thuc pham bo sung khong?",
    "Co quen lieu, tu ngung, doi lieu, hoac tac dung khong mong muon nao khong?"
  ];
  if (activeMedicationCount >= 5) {
    questions.push("Danh sach thuoc co nhieu muc, can duoc si/bac si ra soat trung nhom va nguy co tuong tac.");
  }
  if (patient.medications.some((medication) => medication.category === "HERBAL" || medication.category === "OTC")) {
    questions.push("Can hoi ro tan suat dung OTC/thao duoc va ghi vao ho so truoc khi bac si quyet dinh.");
  }
  return questions;
}

function riskSort(riskLevel: Patient["suggestedRiskLevel"]): number {
  if (riskLevel === "RED") return 0;
  if (riskLevel === "YELLOW") return 1;
  return 2;
}
