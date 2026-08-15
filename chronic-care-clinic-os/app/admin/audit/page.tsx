import { PageHeader } from "@/components/PageHeader";
import { demoAuditEvents } from "@/lib/audit";
import { buildAuditLedger, validateAuditLedger } from "@/lib/audit-ledger";
import { buildPersistentAuditWritePlan, validatePersistentAuditWritePlan } from "@/lib/audit-storage-contract";

export default function AuditPage() {
  const ledger = buildAuditLedger(demoAuditEvents);
  const validation = validateAuditLedger(ledger);
  const persistentWritePlan = buildPersistentAuditWritePlan(ledger, {
    userId: "user-demo-admin",
    actor: "Admin Phong Kham",
    actorRole: "CLINIC_ADMIN",
    actionType: "CREATE",
    entityType: "UserInvite",
    entityId: "user-invite-care-coordinator-demo",
    summary: "Preview persistent append-only AuditLog insert for guarded server action.",
    afterData: { serverActionName: "inviteUserAction", persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED" },
    ipAddress: "127.0.0.1",
    userAgent: "demo-browser",
    createdAt: "2026-06-19T00:00:00+07:00"
  });
  const persistentValidation = validatePersistentAuditWritePlan(ledger, persistentWritePlan);

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
          <p>{persistentValidation.reason}</p>
          <p>Mode: {persistentWritePlan.mode}</p>
          <p>Policy: {persistentWritePlan.mutationPolicy}</p>
        </div>
      </section>
      <section className="panel" style={{ marginBottom: 16 }}>
        <h2>Persistent AuditLog write plan</h2>
        <p>Server actions must append AuditLog in the same transaction as clinical writes.</p>
        <p>
          Next sequence: {persistentWritePlan.auditLogRecord.sequence} / previousHash: {persistentWritePlan.expectedPreviousHash}
        </p>
        <p>eventHash: {persistentWritePlan.auditLogRecord.eventHash}</p>
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
