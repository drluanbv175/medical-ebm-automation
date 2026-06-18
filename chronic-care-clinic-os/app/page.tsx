import Link from "next/link";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { PatientTable } from "@/components/PatientTable";
import { dashboardStats, patients } from "@/lib/seed-data";

export default function HomePage() {
  const stats = dashboardStats();
  const priority = patients.filter((patient) => patient.suggestedRiskLevel !== "GREEN").slice(0, 8);

  return (
    <>
      <PageHeader
        eyebrow="MVP local demo"
        title="Quan ly lien tuc nguoi benh benh man"
        actions={
          <>
            <Link className="button" href="/patients">
              Tim nguoi benh
            </Link>
            <Link className="button secondary" href="/login">
              Doi vai tro demo
            </Link>
          </>
        }
      />

      <div className="danger-box">
        Moi canh bao lam sang trong he thong la clinical decision support draft. Can bac si xac nhan truoc khi ap dung.
      </div>

      <section className="grid cols-4" style={{ marginTop: 16 }}>
        <StatCard label="Nguoi benh demo" value={stats.total} />
        <StatCard label="Nguy co do" value={stats.red} tone="red" />
        <StatCard label="Can duyet care plan" value={stats.pendingCarePlans} tone="yellow" />
        <StatCard label="Qua han tai kham" value={stats.overdue} tone="yellow" />
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Hang doi uu tien</h2>
        <PatientTable patients={priority} />
      </section>
    </>
  );
}
