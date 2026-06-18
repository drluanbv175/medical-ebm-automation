import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { StatCard } from "@/components/StatCard";
import { dashboardStats, patients } from "@/lib/seed-data";

export default function DoctorDashboardPage() {
  const stats = dashboardStats();
  const redPatients = patients.filter((patient) => patient.suggestedRiskLevel === "RED");
  const pendingPlans = patients.filter((patient) => patient.carePlan.status === "PENDING_APPROVAL");

  return (
    <>
      <PageHeader eyebrow="Dashboard bac si" title="Uu tien danh gia va duyet lam sang" />
      <section className="grid cols-4">
        <StatCard label="Lich hom nay" value={patients.filter((patient) => patient.appointments[0]?.status === "SCHEDULED").length} />
        <StatCard label="Nguoi benh nguy co do" value={redPatients.length} tone="red" />
        <StatCard label="Care plan can duyet" value={stats.pendingCarePlans} tone="yellow" />
        <StatCard label="Lab bat thuong moi" value={patients.filter((patient) => patient.labs.some((lab) => lab.reviewStatus === "NEW")).length} />
      </section>
      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Nguy co do</h2>
          <PatientTable patients={redPatients} />
        </div>
        <div className="panel">
          <h2>Can bac si duyet care plan</h2>
          <PatientTable patients={pendingPlans.slice(0, 8)} />
        </div>
      </section>
    </>
  );
}
