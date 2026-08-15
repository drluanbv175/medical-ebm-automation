import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";
import { previewCreateCareAppointmentAction } from "@/lib/workflow-actions";

export default function AppointmentsPage() {
  const appointments = patients.map((patient) => ({ patient, appointment: patient.appointments[0] }));
  const appointmentAction = previewCreateCareAppointmentAction(
    patients[0],
    {
      appointmentType: "FOLLOW_UP",
      scheduledAt: "2026-07-18T09:00:00+07:00",
      providerName: "BS Nguyen Minh",
      reason: "Tai kham dieu phoi benh man",
      riskFlag: patients[0].suggestedRiskLevel
    },
    {
      actorName: "DP Tran Mai",
      actorRole: "CARE_COORDINATOR",
      accessContext: { role: "CARE_COORDINATOR", organizationId: "org-demo", clinicSiteId: "site-demo" },
      resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
      confirmationChecked: true,
      reason: "Demo preview hop dong server action cho tao hen tai kham."
    }
  );
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
        <h2>Create appointment preview</h2>
        <p>
          <StatusBadge>{appointmentAction.status}</StatusBadge> {appointmentAction.serverActionName}
        </p>
        <p>Backend guard: {appointmentAction.backendGuard.reason}</p>
        <p>Persistence: {appointmentAction.persistenceMode}</p>
        <p>{appointmentAction.safetyBoundary}</p>
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
