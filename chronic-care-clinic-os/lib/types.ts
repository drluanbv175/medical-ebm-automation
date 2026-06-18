export type Role =
  | "SUPER_ADMIN"
  | "CLINIC_ADMIN"
  | "PHYSICIAN"
  | "NURSE"
  | "CARE_COORDINATOR"
  | "NURSE_COORDINATOR"
  | "RECEPTIONIST"
  | "PHARMACIST"
  | "QUALITY_MANAGER"
  | "READ_ONLY_AUDITOR"
  | "PATIENT"
  | "PATIENT_PORTAL_USER";

export type RiskLevel = "GREEN" | "YELLOW" | "RED";

export type CarePlanStatus = "DRAFT" | "PENDING_APPROVAL" | "APPROVED" | "REJECTED" | "ARCHIVED";

export type Patient = {
  id: string;
  medicalRecordNumber: string;
  fullName: string;
  dateOfBirth: string;
  sex: "Female" | "Male" | "Other";
  phone: string;
  address: string;
  emergencyContact: string;
  primaryCaregiver: string;
  occupation: string;
  insuranceInformation: string;
  consentStatus: "SIGNED" | "PENDING" | "DECLINED";
  status: "ACTIVE" | "INACTIVE" | "ARCHIVED";
  conditions: ChronicCondition[];
  medications: Medication[];
  vitals: VitalSign[];
  labs: LaboratoryResult[];
  appointments: Appointment[];
  carePlan: CarePlan;
  tasks: CareTask[];
  referrals: Referral[];
  redFlags: string[];
  scenarioTags: string[];
  suggestedRiskLevel: RiskLevel;
  confirmedRiskLevel?: RiskLevel;
  recentHospitalization?: boolean;
  missedAppointments?: number;
};

export type ChronicCondition = {
  conditionCode: string;
  conditionName: string;
  diagnosedDate: string;
  status: "ACTIVE" | "CONTROLLED" | "RESOLVED";
  severity: "MILD" | "MODERATE" | "SEVERE" | "UNSPECIFIED";
  complications?: string;
  notes?: string;
};

export type Medication = {
  drugName: string;
  genericName: string;
  dose: string;
  route: string;
  frequency: string;
  indication: string;
  startDate: string;
  prescribingProvider: string;
  adherenceStatus: "GOOD" | "PARTIAL" | "LOW" | "UNKNOWN";
  isActive: boolean;
  category: "PRESCRIPTION" | "OTC" | "HERBAL" | "SUPPLEMENT";
  medicationClass: string;
  allergyOrIntolerance?: string;
};

export type VitalSign = {
  measuredAt: string;
  systolicBp: number;
  diastolicBp: number;
  heartRate: number;
  respiratoryRate: number;
  temperature: number;
  spo2: number;
  weightKg: number;
  heightCm: number;
  bmi: number;
  waistCircumferenceCm?: number;
  painScore: number;
};

export type LaboratoryResult = {
  testCode: string;
  testName: string;
  resultValue: number;
  unit: string;
  abnormalFlag: "NORMAL" | "LOW" | "HIGH" | "CRITICAL" | "UNKNOWN";
  collectedDate: string;
  reviewStatus: "NEW" | "REVIEWED" | "ACKNOWLEDGED";
};

export type Appointment = {
  id: string;
  appointmentType: "INITIAL" | "FOLLOW_UP" | "POST_DISCHARGE" | "LAB_REVIEW";
  scheduledAt: string;
  providerName: string;
  status: "SCHEDULED" | "CHECKED_IN" | "COMPLETED" | "CANCELLED" | "NO_SHOW";
  reason: string;
  riskFlag: RiskLevel;
  reminderStatus: "NOT_DUE" | "DUE" | "SENT" | "FAILED";
};

export type CarePlan = {
  id: string;
  status: CarePlanStatus;
  riskLevel: RiskLevel;
  mainProblems: string[];
  goals: CareGoal[];
  medicationPlan: string;
  lifestylePlan: string;
  monitoringPlan: string;
  laboratoryPlan: string;
  referralPlan: string;
  redFlagPlan: string;
  nextFollowUpDate?: string;
  approvedBy?: string;
};

export type CareGoal = {
  goalDomain: string;
  goalName: string;
  baselineValue: string;
  targetValue: string;
  targetUnit: string;
  targetDate: string;
  status: "NOT_STARTED" | "IN_PROGRESS" | "MET" | "MISSED";
  notes?: string;
};

export type CareTask = {
  id: string;
  taskType:
    | "CALL_PATIENT"
    | "REMIND_APPOINTMENT"
    | "REQUEST_LAB_RESULT"
    | "MEDICATION_RECONCILIATION"
    | "LIFESTYLE_EDUCATION"
    | "ARRANGE_REFERRAL"
    | "FOLLOW_UP_AFTER_DISCHARGE"
    | "REVIEW_RED_FLAG";
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  status: "OPEN" | "IN_PROGRESS" | "DONE" | "CANCELLED";
  dueDate: string;
  assignedTo: string;
  notes: string;
};

export type Referral = {
  id: string;
  referralType: "SPECIALIST" | "EMERGENCY" | "DIAGNOSTIC" | "COMMUNITY_SUPPORT";
  destination: string;
  specialty: string;
  reason: string;
  urgency: "ROUTINE" | "SOON" | "URGENT";
  status: "DRAFT" | "PENDING_APPROVAL" | "SENT" | "COMPLETED";
};

export type ClinicalRule = {
  ruleName: string;
  ruleDescription: string;
  purpose?: string;
  scope?: string;
  referenceSource?: string;
  severity: RiskLevel;
  suggestedAction: string;
  requiresPhysicianConfirmation: true;
  version: string;
  effectiveDate: string;
  reviewDate: string;
  approvedBy: string;
  status?: "DRAFT" | "APPROVED" | "RETIRED";
  limitationNotes?: string;
};

export type RiskAssessment = {
  suggestedRiskLevel: RiskLevel;
  triggeredRules: ClinicalRule[];
  safetyMessage?: string;
};

export type Organization = {
  id: string;
  name: string;
  status: "ACTIVE" | "INACTIVE";
};

export type ClinicSite = {
  id: string;
  organizationId: string;
  name: string;
  status: "ACTIVE" | "INACTIVE";
};

export type AutomationRule = {
  ruleId: string;
  ruleName: string;
  description: string;
  priority: "LOW" | "MEDIUM" | "HIGH" | "URGENT";
  triggerType: "DAILY_JOB" | "APPOINTMENT_WINDOW" | "STATUS_CHANGE" | "CLINICIAN_MARKED" | "MONTHLY_JOB";
  eligibilityLogic: string;
  exclusionLogic: string;
  assignedRole: Role;
  approvalRequired: boolean;
  notificationTemplate: string;
  escalationLogic: string;
  isActive: boolean;
  version: string;
  approvedBy: string | null;
  effectiveDate: string;
  reviewDate: string;
  actionType: "CREATE_TASK" | "CREATE_CHECKLIST" | "ADD_TO_QUEUE" | "SHOW_ALERT" | "CREATE_DRAFT_REPORT";
};

export type Mvp01WorkflowEvent = {
  stepId: string;
  actorRole: Role;
  action: string;
  requiresAudit: boolean;
  requiresApproval?: boolean;
};
