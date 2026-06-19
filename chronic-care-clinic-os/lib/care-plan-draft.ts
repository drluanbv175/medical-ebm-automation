import { assessRisk } from "./clinical-safety";
import { buildCareGaps } from "./care-orchestrator";
import { reviewProgramEnrollments } from "./program-registry";
import { buildVisitPrepPacket } from "./visit-prep";
import type { CareGap } from "./care-orchestrator";
import type { Patient, RiskLevel } from "./types";

export type CarePlanDraftSection = {
  title: string;
  items: string[];
};

export type CarePlanDraft = {
  draftId: string;
  patientId: string;
  patientName: string;
  medicalRecordNumber: string;
  generatedAt: string;
  riskLevel: RiskLevel;
  status: "DRAFT_REQUIRES_PHYSICIAN_APPROVAL";
  requiresPhysicianApproval: true;
  sourceGapIds: string[];
  problemSummary: string[];
  goals: CarePlanDraftSection;
  monitoringPlan: CarePlanDraftSection;
  medicationReviewPlan: CarePlanDraftSection;
  labPlan: CarePlanDraftSection;
  referralPlan: CarePlanDraftSection;
  patientEducationPlan: CarePlanDraftSection;
  safetyNetPlan: CarePlanDraftSection;
  approvalChecklist: string[];
  safetyBoundary: string;
};

export function buildCarePlanDraft(patient: Patient, today = "2026-06-19"): CarePlanDraft {
  const assessment = assessRisk(patient);
  const careGaps = buildCareGaps(patient, today);
  const prepPacket = buildVisitPrepPacket(patient, today);
  const programReviews = reviewProgramEnrollments(patient, today);
  const openProgramMonitors = programReviews.flatMap((review) =>
    review.monitors
      .filter((monitor) => monitor.status !== "CURRENT")
      .map((monitor) => `${review.programName}: ${monitor.label} (${monitor.status})`)
  );
  const abnormalLabs = patient.labs.filter((lab) => lab.reviewStatus === "NEW" || lab.abnormalFlag !== "NORMAL");

  return {
    draftId: `draft-${patient.id}-${today}`,
    patientId: patient.id,
    patientName: patient.fullName,
    medicalRecordNumber: patient.medicalRecordNumber,
    generatedAt: today,
    riskLevel: assessment.suggestedRiskLevel,
    status: "DRAFT_REQUIRES_PHYSICIAN_APPROVAL",
    requiresPhysicianApproval: true,
    sourceGapIds: careGaps.map((gap) => gap.id),
    problemSummary: buildProblemSummary(patient, careGaps),
    goals: {
      title: "Muc tieu can bac si ca the hoa",
      items: buildGoalItems(patient, openProgramMonitors)
    },
    monitoringPlan: {
      title: "Theo doi va tai kham",
      items: [
        `Ngay tai kham hien tai trong ho so: ${patient.carePlan.nextFollowUpDate ?? "chua co"}.`,
        ...openProgramMonitors.map((monitor) => `Can xu ly monitor: ${monitor}.`),
        "Dieu duong/care coordinator xac nhan kha nang tu theo doi tai nha va rao can tai kham."
      ]
    },
    medicationReviewPlan: {
      title: "Ra soat thuoc",
      items: buildMedicationReviewItems(patient, careGaps)
    },
    labPlan: {
      title: "Xet nghiem va ket qua can xem",
      items:
        abnormalLabs.length > 0
          ? abnormalLabs.map((lab) => `${lab.testName}: ${lab.resultValue} ${lab.unit} (${lab.abnormalFlag}, ${lab.reviewStatus}).`)
          : ["Khong co lab bat thuong moi trong du lieu demo."]
    },
    referralPlan: {
      title: "Chuyen tuyen / hoi chan",
      items: buildReferralItems(patient, careGaps)
    },
    patientEducationPlan: {
      title: "Loi dan va giao duc nguoi benh",
      items: [
        "Chi giao noi dung da duoc bac si phe duyet va phu hop voi dong y giao tiep.",
        "Dung teach-back de xac nhan nguoi benh hieu lich tai kham, dau hieu nguy hiem va cach mang thuoc/lab khi tai kham.",
        ...prepPacket.nursingIntakePrompts.slice(0, 2).map((prompt) => `Hoi lai: ${prompt}`)
      ]
    },
    safetyNetPlan: {
      title: "Safety-netting",
      items: [
        "Neu co dau nguc cap, kho tho cap, yeu liet, ngat, lu lan, ha duong huyet nang hoac trieu chung nguy hiem: can danh gia y te truc tiep ngay.",
        "Khong dung ban nhap nay thay the cap cuu, chan doan hoac don thuoc.",
        assessment.safetyMessage ?? "Neu trieu chung xau di, lien he co so y te phu hop theo huong dan da duyet."
      ]
    },
    approvalChecklist: [
      "Bac si xac nhan muc nguy co va muc tieu ca the hoa.",
      "Bac si/duoc si xac nhan phan ra soat thuoc truoc khi in/giao.",
      "Lab bat thuong da duoc bac si xem va ghi nhan.",
      "Loi dan nguoi benh dung template da duyet va co dong y giao tiep.",
      "Moi thay doi dieu tri, neu co, duoc ghi trong he thong chinh thuc va audit."
    ],
    safetyBoundary:
      "Day la care plan draft ho tro dieu phoi. He thong khong tu chan doan, khong tu ke don, khong tu thay doi dieu tri va khong tu gui thong diep dieu tri cho nguoi benh."
  };
}

export function buildCarePlanDraftQueue(patients: Patient[], today = "2026-06-19"): CarePlanDraft[] {
  return patients
    .map((patient) => buildCarePlanDraft(patient, today))
    .filter((draft) => draft.sourceGapIds.length > 0 || draft.riskLevel !== "GREEN")
    .sort((a, b) => riskSort(a.riskLevel) - riskSort(b.riskLevel) || b.sourceGapIds.length - a.sourceGapIds.length);
}

function buildProblemSummary(patient: Patient, careGaps: CareGap[]): string[] {
  return [
    `Benh man: ${patient.conditions.map((condition) => condition.conditionName).join(", ")}.`,
    `Care plan hien tai: ${patient.carePlan.status}.`,
    `Care gaps dang mo: ${careGaps.length}.`,
    ...careGaps.slice(0, 5).map((gap) => `${gap.category}: ${gap.title}.`)
  ];
}

function buildGoalItems(patient: Patient, openProgramMonitors: string[]): string[] {
  const existingGoals = patient.carePlan.goals.map((goal) => `${goal.goalDomain}: ${goal.goalName} (${goal.status}).`);
  return [
    ...existingGoals,
    "Muc tieu so hoc va nguong can hanh dong phai do bac si ca the hoa theo tuoi, benh kem, nguy co va so thich nguoi benh.",
    ...openProgramMonitors.slice(0, 3).map((monitor) => `Can muc tieu/ke hoach cho monitor: ${monitor}.`)
  ];
}

function buildMedicationReviewItems(patient: Patient, careGaps: CareGap[]): string[] {
  const activeMedicationCount = patient.medications.filter((medication) => medication.isActive).length;
  const items = [
    `So thuoc/che pham dang hoat dong: ${activeMedicationCount}.`,
    "Doi chieu thuoc thuc te nguoi benh mang theo voi ho so; ghi nhan OTC, thao duoc, thuc pham bo sung va di ung/khong dung nap.",
    "Khong tu dong de xuat them/bot/doi thuoc trong draft nay."
  ];
  if (careGaps.some((gap) => gap.category === "MEDICATION")) {
    items.push("Co gap ra soat thuoc: can duoc si hoac bac si xac nhan truoc khi chot care plan.");
  }
  return items;
}

function buildReferralItems(patient: Patient, careGaps: CareGap[]): string[] {
  const referralItems = patient.referrals.map((referral) => `${referral.specialty}: ${referral.reason} (${referral.urgency}, ${referral.status}).`);
  if (careGaps.some((gap) => gap.category === "SAFETY")) {
    referralItems.unshift("Co co do: uu tien danh gia truc tiep va chuyen cap cuu/co so phu hop neu bac si xac nhan.");
  }
  return referralItems.length > 0 ? referralItems : ["Chua co chuyen tuyen trong du lieu demo; bac si xac nhan neu can."];
}

function riskSort(riskLevel: RiskLevel): number {
  if (riskLevel === "RED") return 0;
  if (riskLevel === "YELLOW") return 1;
  return 2;
}
