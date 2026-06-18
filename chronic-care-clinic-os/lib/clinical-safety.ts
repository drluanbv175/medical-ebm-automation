import type { ClinicalRule, Patient, RiskAssessment, RiskLevel } from "./types";

export const redFlagMessage =
  "Can bac si danh gia truc tiep ngay. Khong su dung he thong nhu cong cu thay the cap cuu. Khuyen nghi chuyen cap cuu hoac co so y te phu hop theo danh gia chuyen mon.";

export const clinicalRules: ClinicalRule[] = [
  {
    ruleName: "red_flag_symptom_present",
    ruleDescription: "Co dau nguc cap, kho tho cap, dau than kinh khu tru, ngat, lu lan, ha duong huyet nang hoac trieu chung can cap cuu.",
    severity: "RED",
    suggestedAction: redFlagMessage,
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  },
  {
    ruleName: "very_high_bp_with_symptoms_or_severe_bp",
    ruleDescription: "Huyet ap tam thu >= 180 hoac tam truong >= 120, can bac si danh gia trong boi canh lam sang.",
    severity: "RED",
    suggestedAction: redFlagMessage,
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  },
  {
    ruleName: "uncontrolled_bp_or_glucose",
    ruleDescription: "Chua dat muc tieu huyet ap hoac HbA1c tang, can hen som hon va tao task theo doi.",
    severity: "YELLOW",
    suggestedAction: "Tao task theo doi, hen som hon va chuyen bac si xac nhan muc nguy co.",
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  },
  {
    ruleName: "polypharmacy_review",
    ruleDescription: "Nguoi benh dang dung tu 5 thuoc/che pham tro len hoac co trung nhom dieu tri.",
    severity: "YELLOW",
    suggestedAction: "Can bac si hoac duoc si ra soat thuoc; khong tu ket luan chong chi dinh.",
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  },
  {
    ruleName: "missed_follow_up",
    ruleDescription: "Bo hen hoac qua han tai kham, can care coordinator lien he bang kich ban da duyet.",
    severity: "YELLOW",
    suggestedAction: "Tao task goi nhac; khong gui thong diep dieu tri tu dong.",
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  },
  {
    ruleName: "stable_on_plan",
    ruleDescription: "Dang on dinh, khong co co do, khong qua han tai kham va muc tieu gan dat.",
    severity: "GREEN",
    suggestedAction: "Theo doi dinh ky theo care plan da duyet.",
    requiresPhysicianConfirmation: true,
    version: "2026.06",
    effectiveDate: "2026-06-18",
    reviewDate: "2026-09-18",
    approvedBy: "Clinical safety officer draft"
  }
];

export function assessRisk(patient: Patient): RiskAssessment {
  const triggeredRules: ClinicalRule[] = [];
  const latestVitals = patient.vitals[0];
  const latestHba1c = patient.labs.find((lab) => lab.testCode === "HBA1C");

  if (patient.redFlags.length > 0) {
    triggeredRules.push(rule("red_flag_symptom_present"));
  }

  if (latestVitals && (latestVitals.systolicBp >= 180 || latestVitals.diastolicBp >= 120)) {
    triggeredRules.push(rule("very_high_bp_with_symptoms_or_severe_bp"));
  }

  if (
    latestVitals &&
    (latestVitals.systolicBp >= 160 || latestVitals.diastolicBp >= 100 || (latestHba1c?.resultValue ?? 0) >= 9)
  ) {
    triggeredRules.push(rule("uncontrolled_bp_or_glucose"));
  }

  if (patient.medications.filter((med) => med.isActive).length >= 5 || hasDuplicateMedicationClass(patient)) {
    triggeredRules.push(rule("polypharmacy_review"));
  }

  if ((patient.missedAppointments ?? 0) > 0 || patient.appointments.some((item) => item.status === "NO_SHOW")) {
    triggeredRules.push(rule("missed_follow_up"));
  }

  if (triggeredRules.length === 0) {
    triggeredRules.push(rule("stable_on_plan"));
  }

  const suggestedRiskLevel = highestSeverity(triggeredRules);
  return {
    suggestedRiskLevel,
    triggeredRules,
    safetyMessage: suggestedRiskLevel === "RED" ? redFlagMessage : undefined
  };
}

export function hasDuplicateMedicationClass(patient: Patient): boolean {
  const classes = patient.medications.filter((med) => med.isActive).map((med) => med.medicationClass);
  return new Set(classes).size !== classes.length;
}

function rule(ruleName: string): ClinicalRule {
  const found = clinicalRules.find((item) => item.ruleName === ruleName);
  if (!found) {
    throw new Error(`Missing clinical rule ${ruleName}`);
  }
  return found;
}

function highestSeverity(rules: ClinicalRule[]): RiskLevel {
  if (rules.some((item) => item.severity === "RED")) return "RED";
  if (rules.some((item) => item.severity === "YELLOW")) return "YELLOW";
  return "GREEN";
}
