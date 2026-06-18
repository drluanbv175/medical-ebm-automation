import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { StatCard } from "@/components/StatCard";
import { dashboardStats, patients } from "@/lib/seed-data";

export default function NurseDashboardPage() {
  const stats = dashboardStats();
  const callList = patients.filter((patient) => patient.tasks.some((task) => task.taskType === "CALL_PATIENT"));
  const medReview = patients.filter((patient) => patient.tasks.some((task) => task.taskType === "MEDICATION_RECONCILIATION"));

  return (
    <>
      <PageHeader eyebrow="Dashboard dieu duong / care coordinator" title="Theo doi task va lien he chu dong" />
      <section className="grid cols-4">
        <StatCard label="Can goi nhac" value={callList.length} tone="yellow" />
        <StatCard label="Bo hen/qua han" value={stats.overdue} tone="yellow" />
        <StatCard label="Can ra soat thuoc" value={medReview.length} />
        <StatCard label="Ty le tai kham dung hen" value={`${stats.onTimeFollowUpRate}%`} />
      </section>
      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Danh sach can goi</h2>
          <PatientTable patients={callList} />
        </div>
        <div className="panel">
          <h2>Can medication reconciliation</h2>
          <PatientTable patients={medReview} />
        </div>
      </section>
    </>
  );
}
