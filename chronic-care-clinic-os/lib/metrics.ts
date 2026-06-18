import { patients } from "./seed-data";

export function qualityMetrics() {
  const denominator = patients.length;
  const withCarePlan = patients.filter((patient) => patient.carePlan.status !== "DRAFT").length;
  const medReconciled = patients.filter((patient) => patient.medications.length > 0).length;
  const redRisk = patients.filter((patient) => patient.suggestedRiskLevel === "RED").length;
  const overdue = patients.filter((patient) => (patient.missedAppointments ?? 0) > 0).length;
  const unmetGoals = patients.filter((patient) => patient.carePlan.goals.some((goal) => goal.status !== "MET")).length;
  const labPlan = patients.filter((patient) => patient.labs.length > 0).length;
  const referrals = patients.filter((patient) => patient.referrals.length > 0).length;

  return [
    metric("Nguoi benh dang quan ly", denominator, denominator),
    metric("Co care plan", withCarePlan, denominator),
    metric("Danh muc thuoc duoc cap nhat", medReconciled, denominator),
    metric("Tai kham dung hen", denominator - overdue, denominator),
    metric("Bo hen/qua han", overdue, denominator),
    metric("Nguy co do", redRisk, denominator),
    metric("Chua dat muc tieu", unmetGoals, denominator),
    metric("Co xet nghiem theo ke hoach", labPlan, denominator),
    metric("Co chuyen tuyen khi can", referrals, denominator)
  ];
}

function metric(metricName: string, numerator: number, denominator: number) {
  return {
    metricName,
    metricCategory: "Clinic quality",
    numerator,
    denominator,
    resultValue: denominator === 0 ? 0 : Math.round((numerator / denominator) * 100),
    measurementPeriod: "2026-06",
    owner: "Quan ly chat luong",
    notes: "Du lieu demo da khu dinh danh."
  };
}
