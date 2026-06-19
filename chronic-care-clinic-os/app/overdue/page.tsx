import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { StatusBadge } from "@/components/Badge";
import { buildCommandCenterSnapshot } from "@/lib/care-orchestrator";
import { patients } from "@/lib/seed-data";
import { previewClaimOverdueFollowUpTaskAction } from "@/lib/workflow-actions";

export default function OverduePage() {
  const overdue = patients.filter((patient) => (patient.missedAppointments ?? 0) > 0);
  const followUpGap = buildCommandCenterSnapshot(patients).queue.find((gap) => gap.category === "FOLLOW_UP");
  const claimAction = followUpGap
    ? previewClaimOverdueFollowUpTaskAction(followUpGap, {
        actorName: "DP Tran Mai",
        actorRole: "CARE_COORDINATOR",
        accessContext: { role: "CARE_COORDINATOR", organizationId: "org-demo", clinicSiteId: "site-demo" },
        resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
        confirmationChecked: true,
        reason: "Demo preview hop dong server action cho nhan task goi nhac qua han."
      })
    : null;

  return (
    <>
      <PageHeader
        eyebrow="Qua han tai kham"
        title="Danh sach can dieu duong lien he"
        actions={<button className="button">Nhan task goi nhac</button>}
      />
      <section className="panel">
        {claimAction ? (
          <>
            <h2>Task claim preview</h2>
            <p>
              <StatusBadge>{claimAction.status}</StatusBadge> {claimAction.serverActionName}
            </p>
            <p>Backend guard: {claimAction.backendGuard.reason}</p>
            <p>Persistence: {claimAction.persistenceMode}</p>
            <p>{claimAction.safetyBoundary}</p>
          </>
        ) : null}
        <PatientTable patients={overdue} />
      </section>
    </>
  );
}
