import type { LaboratoryResult, Patient, RiskLevel, Role, VitalSign } from "./types";

export type ChronicCareProgramId =
  | "HYPERTENSION"
  | "TYPE_2_DIABETES"
  | "DYSLIPIDEMIA"
  | "CKD"
  | "HEART_FAILURE"
  | "POLYPHARMACY";

export type ProgramMonitorStatus = "CURRENT" | "DUE_SOON" | "OVERDUE" | "MISSING";

export type ProgramMonitor = {
  monitorId: string;
  label: string;
  status: ProgramMonitorStatus;
  lastRecordedAt?: string;
  dueDate?: string;
  assignedRole: Role;
  reason: string;
};

export type ProgramEnrollmentReview = {
  programId: ChronicCareProgramId;
  programName: string;
  patientId: string;
  patientName: string;
  riskLevel: RiskLevel;
  monitors: ProgramMonitor[];
  openMonitorCount: number;
};

export type ProgramRegistrySnapshot = {
  totalEnrollments: number;
  enrollmentsWithOpenMonitors: number;
  openMonitorCount: number;
  byProgram: Record<ChronicCareProgramId, number>;
  reviews: ProgramEnrollmentReview[];
};

type ProgramDefinition = {
  programId: ChronicCareProgramId;
  programName: string;
  conditionNames: string[];
  monitors: Array<{
    monitorId: string;
    label: string;
    sourceType: "vital" | "lab" | "medication" | "carePlan";
    labCodes?: string[];
    intervalDays: number;
    assignedRole: Role;
  }>;
};

export const chronicCarePrograms: ProgramDefinition[] = [
  {
    programId: "HYPERTENSION",
    programName: "Tang huyet ap",
    conditionNames: ["Hypertension"],
    monitors: [
      {
        monitorId: "bp-recent",
        label: "Huyet ap gan nhat",
        sourceType: "vital",
        intervalDays: 90,
        assignedRole: "NURSE"
      },
      {
        monitorId: "care-plan-follow-up",
        label: "Ngay tai kham trong care plan",
        sourceType: "carePlan",
        intervalDays: 90,
        assignedRole: "CARE_COORDINATOR"
      }
    ]
  },
  {
    programId: "TYPE_2_DIABETES",
    programName: "Dai thao duong type 2",
    conditionNames: ["Type 2 Diabetes"],
    monitors: [
      {
        monitorId: "hba1c-recent",
        label: "HbA1c gan nhat",
        sourceType: "lab",
        labCodes: ["HBA1C"],
        intervalDays: 180,
        assignedRole: "PHYSICIAN"
      },
      {
        monitorId: "medication-adherence",
        label: "Tinh trang tuan thu thuoc",
        sourceType: "medication",
        intervalDays: 90,
        assignedRole: "NURSE"
      }
    ]
  },
  {
    programId: "DYSLIPIDEMIA",
    programName: "Roi loan lipid mau",
    conditionNames: ["Dyslipidemia", "Coronary Artery Disease"],
    monitors: [
      {
        monitorId: "ldlc-recent",
        label: "LDL-C gan nhat",
        sourceType: "lab",
        labCodes: ["LDLC"],
        intervalDays: 365,
        assignedRole: "PHYSICIAN"
      }
    ]
  },
  {
    programId: "CKD",
    programName: "Benh than man",
    conditionNames: ["Chronic Kidney Disease"],
    monitors: [
      {
        monitorId: "egfr-recent",
        label: "eGFR gan nhat",
        sourceType: "lab",
        labCodes: ["EGFR"],
        intervalDays: 180,
        assignedRole: "PHYSICIAN"
      },
      {
        monitorId: "medication-safety-review",
        label: "Ra soat an toan thuoc theo chuc nang than",
        sourceType: "medication",
        intervalDays: 90,
        assignedRole: "PHARMACIST"
      }
    ]
  },
  {
    programId: "HEART_FAILURE",
    programName: "Suy tim / sau xuat vien tim mach",
    conditionNames: ["Heart Failure"],
    monitors: [
      {
        monitorId: "post-discharge-follow-up",
        label: "Theo doi som sau xuat vien",
        sourceType: "carePlan",
        intervalDays: 30,
        assignedRole: "NURSE"
      }
    ]
  },
  {
    programId: "POLYPHARMACY",
    programName: "Da thuoc",
    conditionNames: ["Polypharmacy"],
    monitors: [
      {
        monitorId: "medication-reconciliation",
        label: "Doi chieu danh sach thuoc",
        sourceType: "medication",
        intervalDays: 90,
        assignedRole: "PHARMACIST"
      }
    ]
  }
];

export function buildProgramRegistrySnapshot(patients: Patient[], today = "2026-06-19"): ProgramRegistrySnapshot {
  const reviews = patients.flatMap((patient) => reviewProgramEnrollments(patient, today));
  const byProgram = Object.fromEntries(chronicCarePrograms.map((program) => [program.programId, 0])) as Record<ChronicCareProgramId, number>;

  for (const review of reviews) {
    byProgram[review.programId] += 1;
  }

  return {
    totalEnrollments: reviews.length,
    enrollmentsWithOpenMonitors: reviews.filter((review) => review.openMonitorCount > 0).length,
    openMonitorCount: reviews.reduce((sum, review) => sum + review.openMonitorCount, 0),
    byProgram,
    reviews
  };
}

export function reviewProgramEnrollments(patient: Patient, today = "2026-06-19"): ProgramEnrollmentReview[] {
  return chronicCarePrograms
    .filter((program) => isPatientInProgram(patient, program))
    .map((program) => {
      const monitors = program.monitors.map((monitor) => evaluateMonitor(patient, monitor, today));
      return {
        programId: program.programId,
        programName: program.programName,
        patientId: patient.id,
        patientName: patient.fullName,
        riskLevel: patient.suggestedRiskLevel,
        monitors,
        openMonitorCount: monitors.filter((monitor) => monitor.status !== "CURRENT").length
      };
    });
}

function isPatientInProgram(patient: Patient, program: ProgramDefinition): boolean {
  return patient.conditions.some((condition) => program.conditionNames.includes(condition.conditionName));
}

function evaluateMonitor(
  patient: Patient,
  monitor: ProgramDefinition["monitors"][number],
  today: string
): ProgramMonitor {
  const recordedAt = latestRecordedDate(patient, monitor);
  if (!recordedAt) {
    return {
      monitorId: monitor.monitorId,
      label: monitor.label,
      status: "MISSING",
      assignedRole: monitor.assignedRole,
      reason: "Chua co du lieu theo doi can thiet trong ho so demo."
    };
  }

  const dueDate = addDays(recordedAt, monitor.intervalDays);
  const daysUntilDue = daysBetween(today, dueDate);
  const status: ProgramMonitorStatus = daysUntilDue < 0 ? "OVERDUE" : daysUntilDue <= 30 ? "DUE_SOON" : "CURRENT";
  return {
    monitorId: monitor.monitorId,
    label: monitor.label,
    status,
    lastRecordedAt: recordedAt,
    dueDate,
    assignedRole: monitor.assignedRole,
    reason:
      status === "CURRENT"
        ? "Du lieu theo doi con hieu luc."
        : status === "DUE_SOON"
          ? "Sap den han theo doi, can len ke hoach truoc."
          : "Qua han theo doi, can dieu phoi lai."
  };
}

function latestRecordedDate(patient: Patient, monitor: ProgramDefinition["monitors"][number]): string | undefined {
  if (monitor.sourceType === "vital") {
    return latestVitalDate(patient.vitals);
  }
  if (monitor.sourceType === "lab") {
    return latestLabDate(patient.labs, monitor.labCodes ?? []);
  }
  if (monitor.sourceType === "carePlan") {
    return patient.carePlan.nextFollowUpDate;
  }
  if (monitor.sourceType === "medication") {
    return latestMedicationDate(patient);
  }
  return undefined;
}

function latestVitalDate(vitals: VitalSign[]): string | undefined {
  return vitals.map((vital) => vital.measuredAt.slice(0, 10)).sort().at(-1);
}

function latestLabDate(labs: LaboratoryResult[], codes: string[]): string | undefined {
  return labs
    .filter((lab) => codes.includes(lab.testCode))
    .map((lab) => lab.collectedDate)
    .sort()
    .at(-1);
}

function latestMedicationDate(patient: Patient): string | undefined {
  return patient.medications
    .filter((medication) => medication.isActive)
    .map((medication) => medication.startDate)
    .sort()
    .at(-1);
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

function daysBetween(startDate: string, endDate: string): number {
  const [startYear, startMonth, startDay] = startDate.split("-").map(Number);
  const [endYear, endMonth, endDay] = endDate.split("-").map(Number);
  const start = Date.UTC(startYear, startMonth - 1, startDay);
  const end = Date.UTC(endYear, endMonth - 1, endDay);
  return Math.round((end - start) / 86_400_000);
}
