import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/Badge";
import { buildProductionEvidenceDossier } from "@/lib/production-evidence-dossier";
import { loadProductionEvidencePackageFromEnv } from "@/lib/production-evidence-loader";
import { summarizeWriteActionRegistry, unsafeWriteActions, writeActionRegistry } from "@/lib/write-action-registry";

export default function SettingsPage() {
  const evidenceLoad = loadProductionEvidencePackageFromEnv();
  const productionEvidenceDossier = buildProductionEvidenceDossier(evidenceLoad.package);
  const productionReadiness = productionEvidenceDossier.readiness;
  const openBlockers = productionReadiness.blockers.filter((item) => item.status === "OPEN");
  const writeSummary = summarizeWriteActionRegistry();
  const unsafeActions = unsafeWriteActions();

  return (
    <>
      <PageHeader eyebrow="System settings" title="Cai dat he thong" />
      <section className="grid cols-2">
        <div className="panel">
          <h2>Security</h2>
          <p>Session timeout: 30 phut</p>
          <p>MFA-ready: planned</p>
          <p>Hard delete clinical record: disabled</p>
        </div>
        <div className="panel">
          <h2>AI draft assistance</h2>
          <p>Production default: disabled</p>
          <p>Khong tu ky note, khong tu gui tin nhan, khong tu thay doi du lieu goc.</p>
        </div>
        <div className="panel">
          <h2>Backup</h2>
          <p>Can cau hinh lich backup PostgreSQL truoc production.</p>
        </div>
        <div className="panel">
          <h2>Deployment</h2>
          <p>Local Docker Compose, san sang private server/on-premise.</p>
        </div>
      </section>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Production readiness</h2>
        <p>
          Production ready: <StatusBadge>{String(productionReadiness.summary.productionReady)}</StatusBadge>
        </p>
        <p>
          Release decision: <StatusBadge>{productionReadiness.releaseDecision.status}</StatusBadge>; valid evidence:
          {" "}{productionReadiness.evidenceSummary.validEvidenceRecords} / {productionReadiness.summary.totalBlockers};
          signoffs: {productionReadiness.evidenceSummary.validSignoffs} / {productionReadiness.evidenceSummary.requiredSignoffs};
          findings: {productionReadiness.findings.length}.
        </p>
        <p>
          Open blockers: {productionReadiness.summary.openBlockers} / {productionReadiness.summary.totalBlockers};
          security: {productionReadiness.summary.byCategory.security}; data protection: {productionReadiness.summary.byCategory.data_protection};
          clinical safety: {productionReadiness.summary.byCategory.clinical_safety}; operations: {productionReadiness.summary.byCategory.operations};
          AI governance: {productionReadiness.summary.byCategory.ai_governance}.
        </p>
        <p>
          Evidence dossier: <StatusBadge>{productionEvidenceDossier.status}</StatusBadge>; blocker evidence:
          {" "}{productionEvidenceDossier.summary.validBlockerEvidence} / {productionEvidenceDossier.summary.totalBlockers};
          missing control links: {productionEvidenceDossier.summary.missingRepositoryControlLinks};
          invalid signoffs: {productionEvidenceDossier.summary.invalidSignoffs}.
        </p>
        {evidenceLoad.warnings.length > 0 ? (
          <p className="eyebrow">Evidence load warning: {evidenceLoad.warnings.join(" ")}</p>
        ) : null}
        <p className="eyebrow">{productionReadiness.safetyBoundary}</p>
        <table className="table">
          <thead>
            <tr>
              <th>Blocker</th>
              <th>Category</th>
              <th>Owner</th>
              <th>Evidence required</th>
            </tr>
          </thead>
          <tbody>
            {openBlockers.slice(0, 8).map((item) => (
              <tr key={item.id}>
                <td>{item.id}: {item.title}</td>
                <td>{item.category}</td>
                <td>{item.owner}</td>
                <td>{item.evidenceRequired}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="eyebrow">
          Showing first 8 blockers; the machine-readable manifest remains the source for automation and signoff.
        </p>
      </section>
      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Write action readiness</h2>
        <p>
          Production ready: <StatusBadge>{String(writeSummary.productionReady)}</StatusBadge>
        </p>
        <p>
          Guarded preview: {writeSummary.guardedPreview} / {writeSummary.total}; placeholders: {writeSummary.uiPlaceholder};
          blocked exports: {writeSummary.blockedForProduction}.
        </p>
        <table className="table">
          <thead>
            <tr>
              <th>Action</th>
              <th>Route</th>
              <th>Permission</th>
              <th>Status</th>
              <th>Reason</th>
            </tr>
          </thead>
          <tbody>
            {writeActionRegistry.map((item) => (
              <tr key={item.actionId}>
                <td>{item.label}</td>
                <td>{item.route}</td>
                <td>{item.permission}</td>
                <td>
                  <StatusBadge>{item.guardStatus}</StatusBadge>
                </td>
                <td>{item.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <p className="eyebrow">
          {unsafeActions.length} action chua duoc phep production; tat ca can persistent audit va RBAC scope guard truoc khi bat ghi that.
        </p>
      </section>
    </>
  );
}
