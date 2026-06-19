import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { clinicalRules } from "@/lib/clinical-safety";
import { previewCreateClinicalRuleDraftAction } from "@/lib/workflow-actions";

export default function RulesPage() {
  const ruleDraftAction = previewCreateClinicalRuleDraftAction(
    {
      ruleName: "uncontrolled_bp_follow_up_draft",
      ruleDescription: "Nguoi benh tang huyet ap chua dat muc tieu can duoc dua vao hang doi bac si review va dieu phoi tai kham.",
      purpose: "Tang do nhay phat hien follow-up gap trong chuong trinh tang huyet ap.",
      scope: "Hypertension follow-up; khong ap dung cho cap cuu.",
      referenceSource: "SOP noi bo tang huyet ap 2026, can hoi dong/bac si duyet rieng.",
      severity: "YELLOW",
      suggestedAction: "Tao task review noi bo va hen tai kham theo care plan da duyet; khong gui loi khuyen dieu tri tu dong.",
      requiresPhysicianConfirmation: true,
      version: "draft-2026.06",
      effectiveDate: "2026-07-01",
      reviewDate: "2026-10-01",
      limitationNotes: "Draft chi dung de review; khong kich hoat risk engine."
    },
    {
      actorName: "Admin Phong Kham",
      actorRole: "CLINIC_ADMIN",
      accessContext: { role: "CLINIC_ADMIN", organizationId: "org-demo", clinicSiteId: "site-demo" },
      resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
      confirmationChecked: true,
      reason: "Demo preview hop dong server action cho tao clinical rule draft."
    }
  );

  return (
    <>
      <PageHeader eyebrow="Clinical rules" title="Quan ly rule phan tang nguy co" actions={<button className="button">Tao rule draft</button>} />
      <section className="panel" style={{ marginBottom: 16 }}>
        <h2>Clinical rule draft preview</h2>
        <p>
          <StatusBadge>{ruleDraftAction.status}</StatusBadge> {ruleDraftAction.serverActionName}
        </p>
        <p>Backend guard: {ruleDraftAction.backendGuard.reason}</p>
        <p>Persistence: {ruleDraftAction.persistenceMode}</p>
        <p>{ruleDraftAction.safetyBoundary}</p>
      </section>
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Rule</th>
              <th>Muc</th>
              <th>Mo ta</th>
              <th>Hanh dong</th>
              <th>Review</th>
              <th>Phe duyet</th>
            </tr>
          </thead>
          <tbody>
            {clinicalRules.map((rule) => (
              <tr key={rule.ruleName}>
                <td>{rule.ruleName}</td>
                <td>
                  <RiskBadge level={rule.severity} />
                </td>
                <td>{rule.ruleDescription}</td>
                <td>{rule.suggestedAction}</td>
                <td>{rule.reviewDate}</td>
                <td>{rule.approvedBy}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
