import { StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function CarePlansPage() {
  return (
    <>
      <PageHeader eyebrow="Care plans" title="Danh sach ke hoach cham soc" />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Van de chinh</th>
              <th>Nguy co</th>
              <th>Trang thai</th>
              <th>Tai kham</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((patient) => (
              <tr key={patient.carePlan.id}>
                <td>{patient.fullName}</td>
                <td>{patient.carePlan.mainProblems.join(", ")}</td>
                <td>{patient.carePlan.riskLevel}</td>
                <td>
                  <StatusBadge>{patient.carePlan.status}</StatusBadge>
                </td>
                <td>{patient.carePlan.nextFollowUpDate}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
