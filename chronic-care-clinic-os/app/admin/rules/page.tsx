import { RiskBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { clinicalRules } from "@/lib/clinical-safety";

export default function RulesPage() {
  return (
    <>
      <PageHeader eyebrow="Clinical rules" title="Quan ly rule phan tang nguy co" actions={<button className="button">Tao rule draft</button>} />
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
