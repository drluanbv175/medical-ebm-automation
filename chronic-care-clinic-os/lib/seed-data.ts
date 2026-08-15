import { assessRisk } from "./clinical-safety";
import type { Appointment, CareGoal, CarePlan, CareTask, ChronicCondition, LaboratoryResult, Medication, Patient, Referral, VitalSign } from "./types";

const conditionCatalog = {
  htn: { conditionCode: "I10", conditionName: "Hypertension" },
  dm: { conditionCode: "E11", conditionName: "Type 2 Diabetes" },
  lipid: { conditionCode: "E78.5", conditionName: "Dyslipidemia" },
  obesity: { conditionCode: "E66", conditionName: "Obesity" },
  ckd: { conditionCode: "N18", conditionName: "Chronic Kidney Disease" },
  cad: { conditionCode: "I25", conditionName: "Coronary Artery Disease" },
  hf: { conditionCode: "I50", conditionName: "Heart Failure" },
  frailty: { conditionCode: "R54", conditionName: "Frailty" },
  poly: { conditionCode: "Z79.899", conditionName: "Polypharmacy" }
} as const;

export const patients: Patient[] = Array.from({ length: 50 }, (_, index) => buildPatient(index + 1)).map((patient) => {
  const assessment = assessRisk(patient);
  return { ...patient, suggestedRiskLevel: assessment.suggestedRiskLevel };
});

export function getPatient(id: string): Patient | undefined {
  return patients.find((patient) => patient.id === id);
}

export function dashboardStats() {
  const red = patients.filter((patient) => patient.suggestedRiskLevel === "RED").length;
  const yellow = patients.filter((patient) => patient.suggestedRiskLevel === "YELLOW").length;
  const overdue = patients.filter((patient) => (patient.missedAppointments ?? 0) > 0).length;
  const pendingCarePlans = patients.filter((patient) => patient.carePlan.status === "PENDING_APPROVAL").length;
  const medicationReview = patients.filter((patient) => patient.medications.filter((med) => med.isActive).length >= 5).length;

  return {
    total: patients.length,
    red,
    yellow,
    green: patients.length - red - yellow,
    overdue,
    pendingCarePlans,
    medicationReview,
    onTimeFollowUpRate: Math.round(((patients.length - overdue) / patients.length) * 100),
    carePlanRate: Math.round((patients.filter((patient) => patient.carePlan.status !== "DRAFT").length / patients.length) * 100)
  };
}

function buildPatient(number: number): Patient {
  const group = groupFor(number);
  const conditions = conditionsFor(group);
  const age = number % 5 === 0 ? 72 : 48 + (number % 17);
  const bpHigh = group === "uncontrolled-bp" || number === 12 || number === 33;
  const red = number === 7 || number === 35;
  const hba1cHigh = group === "hba1c-high" || number === 18;
  const egfrLow = group === "ckd" || number === 29;
  const polypharmacy = group === "polypharmacy" || number === 41;
  const noShow = group === "missed-follow-up" || number === 44;
  const postDischarge = group === "post-discharge";
  const riskLabel = red ? "RED" : bpHigh || hba1cHigh || egfrLow || polypharmacy || noShow || postDischarge ? "YELLOW" : "GREEN";

  const vitals = [makeVitals(number, bpHigh, red)];
  const labs = makeLabs(hba1cHigh, egfrLow, number);
  const medications = makeMedications(conditions, polypharmacy);
  const id = `p-${number.toString().padStart(3, "0")}`;

  return {
    id,
    medicalRecordNumber: `CC-${number.toString().padStart(5, "0")}`,
    fullName: `Nguoi benh gia lap ${number.toString().padStart(2, "0")}`,
    dateOfBirth: `${new Date().getFullYear() - age}-01-${String((number % 27) + 1).padStart(2, "0")}`,
    sex: number % 2 === 0 ? "Female" : "Male",
    phone: `090000${number.toString().padStart(4, "0")}`,
    address: `Dia chi gia lap ${number}, Quan Demo`,
    emergencyContact: `Nguoi lien he demo ${number}`,
    primaryCaregiver: number % 4 === 0 ? "Con gai" : "Tu cham soc",
    occupation: number % 3 === 0 ? "Huu tri" : "Nhan vien van phong",
    insuranceInformation: "BHYT demo",
    consentStatus: "SIGNED",
    status: "ACTIVE",
    conditions,
    medications,
    vitals,
    labs,
    appointments: [makeAppointment(id, number, noShow, postDischarge, riskLabel)],
    carePlan: makeCarePlan(id, conditions, riskLabel),
    tasks: makeTasks(id, noShow, polypharmacy, postDischarge, red),
    referrals: makeReferrals(id, red, egfrLow),
    redFlags: red ? ["Dau nguc cap hoac kho tho cap - can danh gia truc tiep"] : [],
    scenarioTags: scenarioTagsFor(group, { bpHigh, hba1cHigh, egfrLow, polypharmacy, noShow, postDischarge, red }),
    suggestedRiskLevel: riskLabel,
    recentHospitalization: postDischarge,
    missedAppointments: noShow ? 1 : 0
  };
}

function groupFor(number: number) {
  if (number <= 10) return number <= 5 ? "controlled" : "uncontrolled-bp";
  if (number <= 20) return number <= 15 ? "diabetes" : "hba1c-high";
  if (number <= 30) return number <= 25 ? "combined" : "ckd";
  if (number <= 35) return "polypharmacy";
  if (number <= 40) return "high-cv-risk";
  if (number <= 45) return "post-discharge";
  return "missed-follow-up";
}

function conditionsFor(group: string): ChronicCondition[] {
  const base: ChronicCondition[] = [];
  const push = (key: keyof typeof conditionCatalog, severity: ChronicCondition["severity"] = "MODERATE") =>
    base.push({
      ...conditionCatalog[key],
      diagnosedDate: "2022-01-01",
      status: "ACTIVE",
      severity,
      notes: "Du lieu demo, can bac si kiem chung."
    });

  if (["controlled", "uncontrolled-bp", "combined", "ckd", "polypharmacy", "high-cv-risk", "post-discharge", "missed-follow-up"].includes(group)) push("htn");
  if (["diabetes", "hba1c-high", "combined", "ckd", "polypharmacy", "high-cv-risk", "post-discharge"].includes(group)) push("dm");
  if (["combined", "high-cv-risk", "post-discharge"].includes(group)) push("lipid");
  if (["ckd"].includes(group)) push("ckd");
  if (["polypharmacy"].includes(group)) push("poly");
  if (["high-cv-risk"].includes(group)) push("cad");
  if (["post-discharge"].includes(group)) push("hf");
  return base;
}

function makeVitals(number: number, bpHigh: boolean, red: boolean): VitalSign {
  const heightCm = 158 + (number % 18);
  const weightKg = 58 + (number % 26);
  return {
    measuredAt: "2026-06-18T08:00:00+07:00",
    systolicBp: red ? 190 : bpHigh ? 164 : 128 + (number % 8),
    diastolicBp: red ? 122 : bpHigh ? 98 : 76 + (number % 8),
    heartRate: red ? 104 : 72 + (number % 12),
    respiratoryRate: red ? 24 : 16,
    temperature: 36.7,
    spo2: red ? 92 : 97,
    weightKg,
    heightCm,
    bmi: Math.round((weightKg / Math.pow(heightCm / 100, 2)) * 10) / 10,
    waistCircumferenceCm: 82 + (number % 20),
    painScore: red ? 6 : number % 4
  };
}

function makeLabs(hba1cHigh: boolean, egfrLow: boolean, number: number): LaboratoryResult[] {
  return [
    {
      testCode: "HBA1C",
      testName: "HbA1c",
      resultValue: hba1cHigh ? 9.4 : 6.8 + (number % 4) * 0.2,
      unit: "%",
      abnormalFlag: hba1cHigh ? "HIGH" : "NORMAL",
      collectedDate: "2026-06-10",
      reviewStatus: hba1cHigh ? "NEW" : "REVIEWED"
    },
    {
      testCode: "EGFR",
      testName: "eGFR",
      resultValue: egfrLow ? 42 : 78 - (number % 12),
      unit: "mL/min/1.73m2",
      abnormalFlag: egfrLow ? "LOW" : "NORMAL",
      collectedDate: "2026-06-10",
      reviewStatus: egfrLow ? "NEW" : "REVIEWED"
    },
    {
      testCode: "LDLC",
      testName: "LDL-C",
      resultValue: number % 6 === 0 ? 156 : 92 + (number % 30),
      unit: "mg/dL",
      abnormalFlag: number % 6 === 0 ? "HIGH" : "NORMAL",
      collectedDate: "2026-06-10",
      reviewStatus: number % 6 === 0 ? "NEW" : "REVIEWED"
    }
  ];
}

function makeMedications(conditions: ChronicCondition[], polypharmacy: boolean): Medication[] {
  const meds: Medication[] = [];
  const add = (drugName: string, genericName: string, medicationClass: string, category: Medication["category"] = "PRESCRIPTION") =>
    meds.push({
      drugName,
      genericName,
      dose: "Theo don hien tai",
      route: "Uong",
      frequency: "1 lan/ngay",
      indication: "Theo ho so demo",
      startDate: "2025-01-01",
      prescribingProvider: "Bac si demo",
      adherenceStatus: "GOOD",
      isActive: true,
      category,
      medicationClass
    });

  if (conditions.some((item) => item.conditionName === "Hypertension")) add("Amlodipine demo", "amlodipine", "CCB");
  if (conditions.some((item) => item.conditionName === "Type 2 Diabetes")) add("Metformin demo", "metformin", "Biguanide");
  if (conditions.some((item) => item.conditionName === "Dyslipidemia")) add("Atorvastatin demo", "atorvastatin", "Statin");
  if (conditions.some((item) => item.conditionName === "Chronic Kidney Disease")) add("Losartan demo", "losartan", "ARB");
  if (polypharmacy) {
    add("Vitamin demo", "multivitamin", "Supplement", "SUPPLEMENT");
    add("Ginkgo demo", "ginkgo biloba", "Herbal", "HERBAL");
    add("Ibuprofen OTC demo", "ibuprofen", "NSAID", "OTC");
    add("Thuoc huyet ap trung nhom demo", "nifedipine", "CCB");
  }
  return meds;
}

function makeAppointment(patientId: string, number: number, noShow: boolean, postDischarge: boolean, riskFlag: string): Appointment {
  return {
    id: `appt-${patientId}`,
    appointmentType: postDischarge ? "POST_DISCHARGE" : number % 2 === 0 ? "FOLLOW_UP" : "INITIAL",
    scheduledAt: noShow ? "2026-06-01T09:00:00+07:00" : "2026-06-18T09:00:00+07:00",
    providerName: "BS Nguyen Minh",
    status: noShow ? "NO_SHOW" : "SCHEDULED",
    reason: postDischarge ? "Tai kham som sau xuat vien" : "Theo doi benh man",
    riskFlag: riskFlag as Appointment["riskFlag"],
    reminderStatus: noShow ? "DUE" : "NOT_DUE"
  };
}

function makeCarePlan(patientId: string, conditions: ChronicCondition[], riskLevel: string): CarePlan {
  const goals: CareGoal[] = [
    {
      goalDomain: "Blood pressure",
      goalName: "Theo doi huyet ap tai nha theo ke hoach da duyet",
      baselineValue: "Theo sinh hieu gan nhat",
      targetValue: "Ca the hoa sau khi bac si xac nhan",
      targetUnit: "mmHg",
      targetDate: "2026-09-18",
      status: "IN_PROGRESS",
      notes: "Muc tieu demo, can bac si kiem chung."
    }
  ];

  if (conditions.some((item) => item.conditionName === "Type 2 Diabetes")) {
    goals.push({
      goalDomain: "HbA1c",
      goalName: "Theo doi HbA1c",
      baselineValue: "Theo xet nghiem gan nhat",
      targetValue: "Ca the hoa",
      targetUnit: "%",
      targetDate: "2026-09-18",
      status: "IN_PROGRESS"
    });
  }

  return {
    id: `cp-${patientId}`,
    status: riskLevel === "GREEN" ? "APPROVED" : "PENDING_APPROVAL",
    riskLevel: riskLevel as CarePlan["riskLevel"],
    mainProblems: conditions.map((item) => item.conditionName),
    goals,
    medicationPlan: "Khong tu dong ke don. Bac si ra soat va ghi ke hoach neu phu hop.",
    lifestylePlan: "Tu van an uong, van dong va tu theo doi theo SOP da duyet.",
    monitoringPlan: "Theo doi sinh hieu, tuan thu va dau hieu can di cap cuu.",
    laboratoryPlan: "Xet nghiem theo lich da duyet trong care plan.",
    referralPlan: "Chuyen tuyen khi co chi dinh chuyen mon.",
    redFlagPlan: "Can bac si danh gia truc tiep ngay neu co dau hieu nguy hiem.",
    nextFollowUpDate: riskLevel === "GREEN" ? "2026-09-18" : "2026-07-18",
    approvedBy: riskLevel === "GREEN" ? "BS Nguyen Minh" : undefined
  };
}

function makeTasks(patientId: string, noShow: boolean, polypharmacy: boolean, postDischarge: boolean, red: boolean): CareTask[] {
  const tasks: CareTask[] = [];
  if (noShow) {
    tasks.push({
      id: `task-${patientId}-call`,
      taskType: "CALL_PATIENT",
      priority: "HIGH",
      status: "OPEN",
      dueDate: "2026-06-18",
      assignedTo: "DD Tran Lan",
      notes: "Goi nhac tai kham bang kich ban da duyet; khong gui thong diep dieu tri tu dong."
    });
  }
  if (polypharmacy) {
    tasks.push({
      id: `task-${patientId}-med`,
      taskType: "MEDICATION_RECONCILIATION",
      priority: "HIGH",
      status: "OPEN",
      dueDate: "2026-06-19",
      assignedTo: "DS Le Hoa",
      notes: "Can ra soat da thuoc va trung nhom."
    });
  }
  if (postDischarge) {
    tasks.push({
      id: `task-${patientId}-dc`,
      taskType: "FOLLOW_UP_AFTER_DISCHARGE",
      priority: "HIGH",
      status: "OPEN",
      dueDate: "2026-06-20",
      assignedTo: "DD Tran Lan",
      notes: "Can thu thap giay ra vien va doi chieu thuoc."
    });
  }
  if (red) {
    tasks.push({
      id: `task-${patientId}-red`,
      taskType: "REVIEW_RED_FLAG",
      priority: "URGENT",
      status: "OPEN",
      dueDate: "2026-06-18",
      assignedTo: "BS Nguyen Minh",
      notes: "Can bac si danh gia truc tiep ngay."
    });
  }
  return tasks;
}

function makeReferrals(patientId: string, red: boolean, egfrLow: boolean): Referral[] {
  if (red) {
    return [
      {
        id: `ref-${patientId}-er`,
        referralType: "EMERGENCY",
        destination: "Co so cap cuu phu hop",
        specialty: "Cap cuu",
        reason: "Dau hieu nguy co cao",
        urgency: "URGENT",
        status: "PENDING_APPROVAL"
      }
    ];
  }
  if (egfrLow) {
    return [
      {
        id: `ref-${patientId}-renal`,
        referralType: "SPECIALIST",
        destination: "Chuyen khoa than",
        specialty: "Than tiet nieu",
        reason: "eGFR giam can danh gia them",
        urgency: "SOON",
        status: "DRAFT"
      }
    ];
  }
  return [];
}

function scenarioTagsFor(group: string, flags: Record<string, boolean>): string[] {
  const tags = [group];
  for (const [key, value] of Object.entries(flags)) {
    if (value) tags.push(key);
  }
  return tags;
}
