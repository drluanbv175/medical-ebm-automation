import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { automationRules } from "@/lib/automation";
import { mvp01Name, mvp01Scope, mvp01Workflow } from "@/lib/mvp01";

export default function Mvp01Page() {
  const steps = mvp01Workflow.map((step, index) => ({
    label: step.action,
    done: index < 5,
    note: `${step.actorRole}${step.requiresApproval ? " - can phe duyet" : ""}${step.requiresAudit ? " - audit" : ""}`
  }));
  const focusedAutomation = automationRules.filter((rule) => ["AUTO-001", "AUTO-002", "AUTO-005", "AUTO-008", "AUTO-010", "AUTO-011"].includes(rule.ruleId));

  return (
    <>
      <PageHeader eyebrow="Thin vertical slice" title={mvp01Name} />
      <div className="danger-box">
        MVP-01 chi la luong dieu phoi tang huyet ap, dai thao duong type 2 va roi loan lipid. Khong phai EMR phap ly,
        khong tu ke don, khong tu gui dieu tri ca the hoa.
      </div>
      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Pham vi</h2>
          {mvp01Scope.map((item) => (
            <p key={item}>{item}</p>
          ))}
        </div>
        <div className="panel">
          <h2>Can dat truoc khi production</h2>
          <p>Backend RBAC, audit bat bien, migration, backup/restore, PDF A5 that, rule/content approval va user acceptance testing.</p>
        </div>
      </section>
      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Luong dau cuoi</h2>
          <WorkflowChecklist steps={steps} />
        </div>
        <div className="panel">
          <h2>Automation lien quan</h2>
          <table className="table">
            <tbody>
              {focusedAutomation.map((rule) => (
                <tr key={rule.ruleId}>
                  <td>{rule.ruleId}</td>
                  <td>{rule.ruleName}</td>
                  <td>{rule.actionType}</td>
                  <td>{rule.assignedRole}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
