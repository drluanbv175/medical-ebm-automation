import { RiskBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function AppointmentsPage() {
  const appointments = patients.map((patient) => ({ patient, appointment: patient.appointments[0] }));
  return (
    <>
      <PageHeader
        eyebrow="Lich hen"
        title="Danh sach hen va check-in"
        actions={
          <>
            <input className="input" type="date" defaultValue="2026-06-18" />
            <button className="button">Tao hen</button>
          </>
        }
      />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Gio</th>
              <th>Nguoi benh</th>
              <th>Loai hen</th>
              <th>Nguy co</th>
              <th>Trang thai</th>
              <th>Checklist</th>
            </tr>
          </thead>
          <tbody>
            {appointments.map(({ patient, appointment }) => (
              <tr key={appointment.id}>
                <td>{appointment.scheduledAt.slice(11, 16)}</td>
                <td>{patient.fullName}</td>
                <td>{appointment.appointmentType}</td>
                <td>
                  <RiskBadge level={appointment.riskFlag} />
                </td>
                <td>{appointment.status}</td>
                <td>Do sinh hieu, ra soat thuoc, sang loc co do</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
