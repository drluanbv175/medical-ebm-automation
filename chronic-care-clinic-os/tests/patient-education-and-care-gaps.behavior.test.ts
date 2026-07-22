// Hoi quy cho 3 phat hien MEDIUM/HIGH tu vong lap kiem tra-hoan thien vong 9
// (2026-07-22, workflow doi khang wf_110cffc4-258):
// 1) buildPatientEducationReleasePackage() khong doc patient.redFlags -> lam
//    dang gate phat hanh loi dan khong tuan thu PATIENT_COMMUNICATION_POLICY.md
//    ("Red flags block patient communication").
// 2) selectEducationTemplate() im lang fallback ve educationTemplates[0] (Tang
//    huyet ap) khi khong benh nen nao khop template that -> hasApprovedTemplate
//    bao true sai cho noi dung khong lien quan.
// 3) buildCareGaps() hardcode hasApprovedTemplate=true cho CA 3 loai nhan tin du
//    khong doi chieu template nao ca.
import assert from "node:assert/strict";
import test from "node:test";

import { buildCareGaps } from "../lib/care-orchestrator";
import { buildPatientEducationReleasePackage, hasApprovedEducationTemplate } from "../lib/patient-education";
import { patients } from "../lib/seed-data";
import type { Patient } from "../lib/types";

// p-001 (nhom "controlled", GREEN): carePlan APPROVED, consent SIGNED, chi co
// dieu kien Hypertension (khop template Tang huyet ap da duyet), khong red flag.
const baselinePatient = patients.find((p) => p.id === "p-001");
if (!baselinePatient) {
  throw new Error("Fixture p-001 not found in seed-data.ts patients array");
}
assert.equal(baselinePatient.carePlan.status, "APPROVED");
assert.equal(baselinePatient.consentStatus, "SIGNED");
assert.equal(baselinePatient.redFlags.length, 0);

test("patient education release package is fully allowed when template/care-plan/consent approved and no red flag", () => {
  const pkg = buildPatientEducationReleasePackage(baselinePatient);
  assert.equal(pkg.printAllowed, true);
  assert.equal(pkg.releaseStatus, "READY_TO_PRINT_APPROVED_HANDOUT");
  assert.deepEqual(pkg.blockedReasons, []);
});

test("patient education release package blocks handout/messaging when an active red flag is present (vong 9 fix)", () => {
  const patientWithRedFlag: Patient = {
    ...baselinePatient,
    redFlags: ["Dau nguc cap hoac kho tho cap - can danh gia truc tiep"]
  };
  const pkg = buildPatientEducationReleasePackage(patientWithRedFlag);
  assert.equal(pkg.printAllowed, false, "red flag phai chan phat hanh, khong duoc phep chi vi care plan/template/consent da du");
  assert.equal(pkg.patientMessageAllowed, false);
  assert.equal(pkg.releaseStatus, "BLOCKED_REQUIRES_APPROVAL_OR_CONSENT");
  assert.ok(
    pkg.blockedReasons.some((reason) => reason.includes("canh bao do") || reason.toLowerCase().includes("red flag")),
    "blockedReasons phai neu ro ly do la red flag dang hoat dong"
  );
});

test("patient education release package flags an unmatched condition instead of silently reusing an unrelated template (vong 9 fix)", () => {
  const patientWithUnmappedConditionsOnly: Patient = {
    ...baselinePatient,
    conditions: [
      {
        conditionCode: "E78.5",
        conditionName: "Dyslipidemia",
        diagnosedDate: "2022-01-01",
        status: "ACTIVE",
        severity: "MODERATE",
        notes: "Du lieu test."
      }
    ]
  };
  const pkg = buildPatientEducationReleasePackage(patientWithUnmappedConditionsOnly);
  assert.equal(pkg.printAllowed, false, "khong co template khop benh nen thi KHONG duoc phat hanh du template fallback co status APPROVED");
  assert.ok(
    pkg.blockedReasons.some((reason) => reason.toLowerCase().includes("khong tim thay template")),
    "blockedReasons phai canh bao ro rang khong tim thay template khop, khong duoc im lang dung mau khac"
  );
});

test("hasApprovedEducationTemplate() reflects real template match, not a hardcoded true", () => {
  assert.equal(hasApprovedEducationTemplate(baselinePatient), true);
  const unmatchedPatient: Patient = {
    ...baselinePatient,
    conditions: [
      {
        conditionCode: "E66",
        conditionName: "Obesity",
        diagnosedDate: "2022-01-01",
        status: "ACTIVE",
        severity: "MODERATE",
        notes: "Du lieu test."
      }
    ]
  };
  assert.equal(hasApprovedEducationTemplate(unmatchedPatient), false);
});

test("care gaps never claim reminder/pre-visit patient communication is allowed without a real template registry (vong 9 fix)", () => {
  const patientWithMissedAppointment: Patient = { ...baselinePatient, missedAppointments: 2 };
  const followUpGap = buildCareGaps(patientWithMissedAppointment).find((gap) => gap.category === "FOLLOW_UP");
  assert.ok(followUpGap, "expected a FOLLOW_UP care gap for a patient with missed appointments");
  assert.equal(
    followUpGap!.patientCommunicationAllowed,
    false,
    "khong co template registry that cho nhac tai kham -> phai fail-closed, khong duoc bao da duyet"
  );

  const patientWithRecentHospitalization: Patient = { ...baselinePatient, recentHospitalization: true };
  const postDischargeGap = buildCareGaps(patientWithRecentHospitalization).find((gap) => gap.category === "POST_DISCHARGE");
  assert.ok(postDischargeGap, "expected a POST_DISCHARGE care gap");
  assert.equal(postDischargeGap!.patientCommunicationAllowed, false);
});

test("adherence care gap's patient communication flag now tracks the real education template match", () => {
  const patientWithLowAdherence: Patient = {
    ...baselinePatient,
    medications: baselinePatient.medications.map((medication, index) =>
      index === 0 ? { ...medication, adherenceStatus: "LOW" } : medication
    )
  };
  const adherenceGap = buildCareGaps(patientWithLowAdherence).find((gap) => gap.category === "ADHERENCE");
  assert.ok(adherenceGap, "expected an ADHERENCE care gap for low medication adherence");
  assert.equal(
    adherenceGap!.patientCommunicationAllowed,
    true,
    "benh nhan co template giao duc khop (Hypertension) va consent SIGNED -> duoc phep"
  );

  const patientWithUnmatchedConditionAndLowAdherence: Patient = {
    ...patientWithLowAdherence,
    conditions: [
      {
        conditionCode: "R54",
        conditionName: "Frailty",
        diagnosedDate: "2022-01-01",
        status: "ACTIVE",
        severity: "MODERATE",
        notes: "Du lieu test."
      }
    ]
  };
  const adherenceGapUnmatched = buildCareGaps(patientWithUnmatchedConditionAndLowAdherence).find(
    (gap) => gap.category === "ADHERENCE"
  );
  assert.ok(adherenceGapUnmatched, "expected an ADHERENCE care gap even without a matching education template");
  assert.equal(
    adherenceGapUnmatched!.patientCommunicationAllowed,
    false,
    "khong co template giao duc khop benh nen -> khong duoc bao da duyet"
  );
});
