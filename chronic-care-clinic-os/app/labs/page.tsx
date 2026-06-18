import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function LabsPage() {
  const abnormal = patients.flatMap((patient) =>
    patient.labs.filter((lab) => lab.abnormalFlag !== "NORMAL").map((lab) => ({ patient, lab }))
  );
  return (
    <>
      <PageHeader eyebrow="Lab review workflow" title="Ket qua xet nghiem bat thuong chua xem" />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Xet nghiem</th>
              <th>Ket qua</th>
              <th>Trang thai</th>
            </tr>
          </thead>
          <tbody>
            {abnormal.map(({ patient, lab }) => (
              <tr key={`${patient.id}-${lab.testCode}`}>
                <td>{patient.fullName}</td>
                <td>{lab.testName}</td>
                <td>
                  {lab.resultValue} {lab.unit} ({lab.abnormalFlag})
                </td>
                <td>{lab.reviewStatus}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
