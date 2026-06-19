import Link from "next/link";
import { StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { buildCarePlanDraftQueue } from "@/lib/care-plan-draft";
import { patients } from "@/lib/seed-data";

export default function CarePlansPage() {
  const drafts = buildCarePlanDraftQueue(patients);
  const focusDraft = drafts[0];

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
            </tr>
          </thead>
          <tbody>
            {patients.map((patient) => {
              const draft = drafts.find((item) => item.patientId === patient.id);
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
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </>
  );
}
