import Link from "next/link";
import { StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { buildCarePlanApprovalQueue } from "@/lib/care-plan-approval";
import { buildCarePlanDraftQueue } from "@/lib/care-plan-draft";
import { patients } from "@/lib/seed-data";
import { previewApproveCarePlanAction } from "@/lib/workflow-actions";

export default function CarePlansPage() {
  const drafts = buildCarePlanDraftQueue(patients);
  const approvalPackages = buildCarePlanApprovalQueue(patients);
  const focusDraft = drafts[0];
  const focusApproval =
    approvalPackages.find((approvalPackage) => approvalPackage.patientId === focusDraft?.patientId) ?? approvalPackages[0];
  const focusApprovalAction = focusApproval
    ? previewApproveCarePlanAction(focusApproval, {
        actorName: "BS Nguyen Minh",
        actorRole: "PHYSICIAN",
        accessContext: { role: "PHYSICIAN", organizationId: "org-demo", clinicSiteId: "site-demo" },
        resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
        confirmationChecked: true,
        reason: "Demo preview hop dong server action cho ky duyet care plan."
      })
    : null;

  return (
    <>
      <PageHeader
        eyebrow="Care plans"
        title="Ke hoach cham soc can bac si duyet"
        actions={
          focusDraft ? (
            <Link className="button" href={`/patients/${focusDraft.patientId}`}>
              Mo ho so uu tien
            </Link>
          ) : null
        }
      />

      {focusDraft ? (
        <>
          <div className="danger-box">{focusDraft.safetyBoundary}</div>
          <section className="grid cols-2" style={{ marginTop: 16 }}>
            <div className="panel">
              <h2>Draft uu tien</h2>
              <p>
                <strong>{focusDraft.patientName}</strong> ({focusDraft.medicalRecordNumber})
              </p>
              <p>
                Trang thai: <StatusBadge>{focusDraft.status}</StatusBadge>
              </p>
              <h3>{focusDraft.goals.title}</h3>
              {focusDraft.goals.items.slice(0, 5).map((item) => (
                <p key={item}>{item}</p>
              ))}
            </div>
            <div className="panel">
              <h2>Checklist phe duyet</h2>
              <WorkflowChecklist
                steps={focusDraft.approvalChecklist.map((item) => ({
                  label: item,
                  done: false,
                  note: "Can bac si/doi ngu phu hop xac nhan"
                }))}
              />
            </div>
          </section>

          <section className="grid cols-3" style={{ marginTop: 16 }}>
            {[
              focusDraft.monitoringPlan,
              focusDraft.medicationReviewPlan,
              focusDraft.labPlan,
              focusDraft.referralPlan,
              focusDraft.patientEducationPlan,
              focusDraft.safetyNetPlan
            ].map((section) => (
              <div className="panel" key={section.title}>
                <h2>{section.title}</h2>
                {section.items.map((item) => (
                  <p key={item}>{item}</p>
                ))}
              </div>
            ))}
          </section>
        </>
      ) : null}

      {focusApproval ? (
        <section className="grid cols-2" style={{ marginTop: 16 }}>
          <div className="panel">
            <h2>Goi phe duyet</h2>
            <p>
              Trang thai: <StatusBadge>{focusApproval.gateStatus}</StatusBadge>
            </p>
            <p>{focusApproval.safetyBoundary}</p>
            <WorkflowChecklist
              steps={focusApproval.gates.map((gate) => ({
                label: gate.label,
                done: gate.status === "PASS",
                note: `${gate.ownerRole} - ${gate.evidence}`
              }))}
            />
          </div>
          <div className="panel">
            <h2>Version va audit preview</h2>
            <p>
              Version du kien: <strong>{focusApproval.versionPreview.versionId}</strong>
            </p>
            <p>Che do ghi: {focusApproval.writebackMode}</p>
            <p>Audit preview: {focusApproval.auditPreview.summary}</p>
            {focusApprovalAction ? (
              <>
                <h3>Server action preview</h3>
                <p>
                  <StatusBadge>{focusApprovalAction.status}</StatusBadge> {focusApprovalAction.serverActionName}
                </p>
                <p>Persistence: {focusApprovalAction.persistenceMode}</p>
                <p>Backend guard: {focusApprovalAction.backendGuard.reason}</p>
                <p>{focusApprovalAction.safetyBoundary}</p>
              </>
            ) : null}
            <h3>Huong dan ky duyet</h3>
            {focusApproval.signoffInstructions.map((instruction) => (
              <p key={instruction}>{instruction}</p>
            ))}
          </div>
        </section>
      ) : null}

      <section className="panel">
        <h2>Danh sach care plan</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Van de chinh</th>
              <th>Nguy co</th>
              <th>Trang thai</th>
              <th>Tai kham</th>
              <th>Draft gaps</th>
              <th>Phe duyet</th>
            </tr>
          </thead>
          <tbody>
            {patients.map((patient) => {
              const draft = drafts.find((item) => item.patientId === patient.id);
              const approvalPackage = approvalPackages.find((item) => item.patientId === patient.id);
              return (
                <tr key={patient.carePlan.id}>
                  <td>{patient.fullName}</td>
                  <td>{patient.carePlan.mainProblems.join(", ")}</td>
                  <td>{patient.carePlan.riskLevel}</td>
                  <td>
                    <StatusBadge>{patient.carePlan.status}</StatusBadge>
                  </td>
                  <td>{patient.carePlan.nextFollowUpDate}</td>
                  <td>{draft ? draft.sourceGapIds.length : 0}</td>
                  <td>
                    {approvalPackage ? (
                      <>
                        <StatusBadge>{approvalPackage.gateStatus}</StatusBadge>
                        <div className="eyebrow">{approvalPackage.blockedReasons.length} gate bi chan</div>
                      </>
                    ) : (
                      "Khong co draft"
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </>
  );
}
