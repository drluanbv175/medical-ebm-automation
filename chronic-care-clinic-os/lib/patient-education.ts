import { isPatientCommunicationAllowed } from "./automation";
import type { AuditEvent } from "./audit";
import type { Patient } from "./types";

export type EducationTemplate = {
  templateId: string;
  title: string;
  conditionKeywords: string[];
  version: string;
  status: "APPROVED" | "DRAFT" | "RETIRED";
  approvedBy: string;
  approvedAt: string;
  reviewDate: string;
  sections: string[];
};

export type PatientEducationReleasePackage = {
  packageId: string;
  patientId: string;
  patientName: string;
  medicalRecordNumber: string;
  template: EducationTemplate;
  releaseStatus: "READY_TO_PRINT_APPROVED_HANDOUT" | "BLOCKED_REQUIRES_APPROVAL_OR_CONSENT";
  printAllowed: boolean;
  patientMessageAllowed: boolean;
  blockedReasons: string[];
  handoutSections: string[];
  auditPreview: AuditEvent;
  safetyBoundary: string;
};

export const educationTemplates: EducationTemplate[] = [
  {
    templateId: "edu-htn-2026-06",
    title: "Tang huyet ap",
    conditionKeywords: ["Hypertension"],
    version: "2026.06",
    status: "APPROVED",
    approvedBy: "Clinical education board",
    approvedAt: "2026-06-18T10:00:00+07:00",
    reviewDate: "2026-09-18",
    sections: [
      "Do huyet ap theo huong dan da duoc bac si xac nhan va ghi lai de mang khi tai kham.",
      "Dung thuoc theo don dang co; khong tu y them, bot hoac doi lieu.",
      "Can danh gia y te truc tiep ngay neu dau nguc cap, kho tho cap, yeu liet, ngat hoac lu lan."
    ]
  },
  {
    templateId: "edu-dm-2026-06",
    title: "Dai thao duong type 2",
    conditionKeywords: ["Type 2 Diabetes"],
    version: "2026.06",
    status: "APPROVED",
    approvedBy: "Clinical education board",
    approvedAt: "2026-06-18T10:00:00+07:00",
    reviewDate: "2026-09-18",
    sections: [
      "Theo doi duong huyet tai nha neu da duoc huong dan va mang so ghi khi tai kham.",
      "Duy tri an uong, van dong va dung thuoc theo ke hoach da duoc bac si phe duyet.",
      "Can lien he y te phu hop neu ha duong huyet nang, non/roi loan y thuc hoac dau hieu nguy hiem."
    ]
  },
  {
    templateId: "edu-ckd-2026-06",
    title: "Benh than man",
    conditionKeywords: ["Chronic Kidney Disease"],
    version: "2026.06",
    status: "APPROVED",
    approvedBy: "Clinical education board",
    approvedAt: "2026-06-18T10:00:00+07:00",
    reviewDate: "2026-09-18",
    sections: [
      "Lam xet nghiem va tai kham theo lich da co trong care plan duoc phe duyet.",
      "Thong bao voi bac si/duoc si tat ca thuoc OTC, thao duoc va thuc pham bo sung dang dung.",
      "Khong tu y dung them thuoc giam dau/khuyen mai neu chua duoc nhan vien y te phu hop xac nhan."
    ]
  },
  {
    templateId: "edu-post-discharge-2026-06",
    title: "Sau xuat vien",
    conditionKeywords: ["Heart Failure", "Coronary Artery Disease"],
    version: "2026.06",
    status: "APPROVED",
    approvedBy: "Clinical education board",
    approvedAt: "2026-06-18T10:00:00+07:00",
    reviewDate: "2026-09-18",
    sections: [
      "Mang giay ra vien, don thuoc va cac ket qua xet nghiem/hinh anh khi tai kham.",
      "Doi chieu thuoc sau xuat vien voi dieu duong/duoc si truoc khi chot care plan moi.",
      "Can danh gia ngay neu kho tho tang, dau nguc, phu nhanh, ngat, lu lan hoac trieu chung nang len."
    ]
  }
];

export function buildPatientEducationReleasePackage(
  patient: Patient,
  today = "2026-06-19"
): PatientEducationReleasePackage {
  const { template, matchedCondition } = selectEducationTemplate(patient);
  const hasApprovedTemplate = template.status === "APPROVED";
  const hasApprovedCarePlan = patient.carePlan.status === "APPROVED";
  const hasConsent = patient.consentStatus === "SIGNED";
  // SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 9): PATIENT_COMMUNICATION_POLICY.md
  // yeu cau "Red flags block patient communication" nhung ham nay truoc day khong doc
  // patient.redFlags o dau ca - chi co evaluatePatientCommunicationPolicy() (runtime-hardening.ts)
  // kiem dieu nay, va ham do KHONG duoc goi tu day. Them kiem tra truc tiep de cong quyet dinh
  // release-gate that su tuan thu chinh sach da cong bo.
  const hasNoActiveRedFlag = patient.redFlags.length === 0;
  const blockedReasons = [
    // SUA 2026-07-22 (vong 9): truoc day selectEducationTemplate() im lang tra ve
    // educationTemplates[0] (Tang huyet ap) khi KHONG co template nao khop benh nen
    // (vd benh nhan chi co Dyslipidemia/Obesity/Frailty/Polypharmacy) - template.status
    // van la "APPROVED" nen hasApprovedTemplate=true dan toi phat hanh loi dan SAI noi dung
    // ma khong ai biet. Nay bao 🔴 rieng khi khong khop, khong lam an nhu dung template that.
    ...(!matchedCondition
      ? [`Khong tim thay template giao duc khop voi benh nen (${patient.conditions.map((c) => c.conditionName).join(", ")}) - dang tam dung mau "${template.title}" chi de tham khao cau truc, CAN chon/soan template dung chuyen khoa truoc khi phat hanh.`]
      : []),
    ...(!hasApprovedTemplate ? ["Template chua duoc phe duyet."] : []),
    ...(!hasApprovedCarePlan ? [`Care plan hien tai la ${patient.carePlan.status}, chua duoc APPROVED.`] : []),
    ...(!hasConsent ? [`Consent hien tai la ${patient.consentStatus}.`] : []),
    ...(!hasNoActiveRedFlag
      ? [`Co canh bao do (red flag) dang hoat dong: ${patient.redFlags.join("; ")} - can bac si danh gia truc tiep, khong phat hanh loi dan/nhan tin tu dong.`]
      : [])
  ];
  const printAllowed = blockedReasons.length === 0;
  const patientMessageAllowed = isPatientCommunicationAllowed("APPROVED_EDUCATION_READY", hasApprovedTemplate, hasConsent);

  return {
    packageId: `education-${patient.id}-${template.templateId}-${today}`,
    patientId: patient.id,
    patientName: patient.fullName,
    medicalRecordNumber: patient.medicalRecordNumber,
    template,
    releaseStatus: printAllowed ? "READY_TO_PRINT_APPROVED_HANDOUT" : "BLOCKED_REQUIRES_APPROVAL_OR_CONSENT",
    printAllowed,
    patientMessageAllowed: printAllowed && patientMessageAllowed,
    blockedReasons,
    handoutSections: buildHandoutSections(patient, template),
    auditPreview: {
      id: `audit-education-preview-${patient.id}-${today}`,
      actor: "SYSTEM_PREVIEW",
      actorRole: "READ_ONLY_AUDITOR",
      actionType: "CREATE",
      entityType: "PatientHandout",
      entityId: patient.id,
      summary: printAllowed
        ? "Tao preview loi dan A5 tu template da duyet; chua ghi production."
        : "Chan phat hanh loi dan vi thieu phe duyet care plan, template hoac consent.",
      createdAt: `${today}T00:00:00+07:00`
    },
    safetyBoundary:
      "Goi loi dan chi dung template da duyet, khong tu dong gui cho nguoi benh va khong thay the don thuoc/chan doan/cap cuu."
  };
}

export function buildPatientEducationReleaseQueue(
  patients: Patient[],
  today = "2026-06-19"
): PatientEducationReleasePackage[] {
  return patients
    .map((patient) => buildPatientEducationReleasePackage(patient, today))
    .sort(
      (a, b) =>
        Number(b.printAllowed) - Number(a.printAllowed) ||
        b.blockedReasons.length - a.blockedReasons.length
    );
}

function selectEducationTemplate(patient: Patient): { template: EducationTemplate; matchedCondition: boolean } {
  const matched = educationTemplates.find((template) =>
    patient.conditions.some((condition) => template.conditionKeywords.includes(condition.conditionName))
  );
  return { template: matched ?? educationTemplates[0], matchedCondition: Boolean(matched) };
}

// SUA 2026-07-22 (vong lap kiem tra-hoan thien vong 9): xuat tin hieu "co template giao duc
// da duyet KHOP benh nen" that su de care-orchestrator.ts dung, thay vi tu hardcode true
// khong doi chieu gi (finding MEDIUM: hasApprovedTemplate=true trong buildCareGaps()).
export function hasApprovedEducationTemplate(patient: Patient): boolean {
  const { template, matchedCondition } = selectEducationTemplate(patient);
  return matchedCondition && template.status === "APPROVED";
}

function buildHandoutSections(patient: Patient, template: EducationTemplate): string[] {
  return [
    `Nguoi benh: ${patient.fullName} (${patient.medicalRecordNumber}).`,
    `Benh man trong ho so: ${patient.conditions.map((condition) => condition.conditionName).join(", ")}.`,
    `Template: ${template.title}, version ${template.version}, duyet boi ${template.approvedBy}.`,
    `Ngay tai kham: ${patient.carePlan.nextFollowUpDate ?? "can bac si xac nhan"}.`,
    ...template.sections,
    "Neu co trieu chung nguy hiem, can lien he co so y te phu hop hoac cap cuu theo danh gia chuyen mon."
  ];
}
