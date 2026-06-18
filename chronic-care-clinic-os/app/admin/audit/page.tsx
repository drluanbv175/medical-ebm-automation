import { PageHeader } from "@/components/PageHeader";
import { demoAuditEvents } from "@/lib/audit";

export default function AuditPage() {
  return (
    <>
      <PageHeader
        eyebrow="Audit log"
        title="Nhat ky xem, sua, duyet va xuat du lieu"
        actions={
          <>
            <input className="input" type="date" defaultValue="2026-06-18" />
            <button className="button secondary">Xuat audit</button>
          </>
        }
      />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Thoi diem</th>
              <th>Nguoi thuc hien</th>
              <th>Role</th>
              <th>Hanh dong</th>
              <th>Doi tuong</th>
              <th>Tom tat</th>
            </tr>
          </thead>
          <tbody>
            {demoAuditEvents.map((event) => (
              <tr key={event.id}>
                <td>{event.createdAt}</td>
                <td>{event.actor}</td>
                <td>{event.actorRole}</td>
                <td>{event.actionType}</td>
                <td>
                  {event.entityType} / {event.entityId}
                </td>
                <td>{event.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
