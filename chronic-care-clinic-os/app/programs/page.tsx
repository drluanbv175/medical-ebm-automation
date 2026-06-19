import Link from "next/link";
import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { buildProgramRegistrySnapshot, chronicCarePrograms } from "@/lib/program-registry";
import { patients } from "@/lib/seed-data";

export default function ProgramsPage() {
  const snapshot = buildProgramRegistrySnapshot(patients);
  const openReviews = snapshot.reviews.filter((review) => review.openMonitorCount > 0).slice(0, 20);

  return (
    <>
      <PageHeader
        eyebrow="Chronic care registry"
        title="Chuong trinh quan ly benh man"
        actions={
          <Link className="button" href="/command-center">
            Mo Command Center
          </Link>
        }
      />

      <section className="grid cols-4">
        <StatCard label="Luot ghi danh chuong trinh" value={snapshot.totalEnrollments} />
        <StatCard label="Chuong trinh co gap" value={snapshot.enrollmentsWithOpenMonitors} tone="yellow" />
        <StatCard label="Monitor dang mo" value={snapshot.openMonitorCount} tone="yellow" />
        <StatCard label="So chuong trinh" value={chronicCarePrograms.length} />
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Bao phu theo chuong trinh</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Chuong trinh</th>
              <th>So nguoi benh</th>
              <th>Monitor mac dinh</th>
            </tr>
          </thead>
          <tbody>
            {chronicCarePrograms.map((program) => (
              <tr key={program.programId}>
                <td>
                  <strong>{program.programName}</strong>
                  <div className="eyebrow">{program.programId}</div>
                </td>
                <td>{snapshot.byProgram[program.programId]}</td>
                <td>{program.monitors.map((monitor) => monitor.label).join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Gap theo doi can dieu phoi</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Chuong trinh</th>
              <th>Nguy co</th>
              <th>Monitor dang mo</th>
              <th>Trang thai</th>
              <th>Phu trach</th>
            </tr>
          </thead>
          <tbody>
            {openReviews.map((review) => {
              const openMonitors = review.monitors.filter((monitor) => monitor.status !== "CURRENT");
              return (
                <tr key={`${review.patientId}-${review.programId}`}>
                  <td>
                    <Link href={`/patients/${review.patientId}`}>
                      <strong>{review.patientName}</strong>
                    </Link>
                  </td>
                  <td>{review.programName}</td>
                  <td>
                    <RiskBadge level={review.riskLevel} />
                  </td>
                  <td>{openMonitors.map((monitor) => monitor.label).join(", ")}</td>
                  <td>
                    {openMonitors.map((monitor) => (
                      <StatusBadge key={monitor.monitorId}>{monitor.status}</StatusBadge>
                    ))}
                  </td>
                  <td>{openMonitors.map((monitor) => monitor.assignedRole).join(", ")}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </>
  );
}
