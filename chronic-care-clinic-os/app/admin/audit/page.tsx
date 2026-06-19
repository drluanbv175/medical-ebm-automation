import { PageHeader } from "@/components/PageHeader";
import { demoAuditEvents } from "@/lib/audit";
import { buildAuditLedger, validateAuditLedger } from "@/lib/audit-ledger";

export default function AuditPage() {
  const ledger = buildAuditLedger(demoAuditEvents);
  const validation = validateAuditLedger(ledger);

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
      <section className="grid cols-3" style={{ marginBottom: 16 }}>
        <div className="panel">
          <h2>Ledger integrity</h2>
          <p>{validation.reason}</p>
          <p>Checked entries: {validation.checkedEntries}</p>
        </div>
        <div className="panel">
          <h2>Append-only mode</h2>
          <p>Audit entries are chained by previousHash and eventHash.</p>
          <p>Normal UI cannot update or delete audit log rows.</p>
        </div>
        <div className="panel">
          <h2>Next write guard</h2>
          <p>Server actions must append AuditLog in the same transaction as clinical writes.</p>
        </div>
      </section>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Seq</th>
              <th>Thoi diem</th>
              <th>Nguoi thuc hien</th>
              <th>Role</th>
              <th>Hanh dong</th>
              <th>Doi tuong</th>
              <th>Hash</th>
              <th>Tom tat</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map((event) => (
              <tr key={event.id}>
                <td>{event.sequence}</td>
                <td>{event.createdAt}</td>
                <td>{event.actor}</td>
                <td>{event.actorRole}</td>
                <td>{event.actionType}</td>
                <td>
                  {event.entityType} / {event.entityId}
                </td>
                <td>{event.eventHash}</td>
                <td>{event.summary}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
