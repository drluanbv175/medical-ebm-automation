import { PageHeader } from "@/components/PageHeader";
import { StatusBadge } from "@/components/Badge";
import { previewCreateEducationTemplateDraftAction } from "@/lib/workflow-actions";

const templates = ["Tang huyet ap", "Dai thao duong", "Roi loan lipid", "Benh than man", "Suy tim on dinh", "COPD", "Hen", "Da thuoc o nguoi cao tuoi", "Sau xuat vien"];

export default function TemplatesPage() {
  const templateDraftAction = previewCreateEducationTemplateDraftAction(
    {
      title: "Tang huyet ap - draft noi bo",
      conditionKeywords: ["Hypertension"],
      sections: ["Do huyet ap tai nha theo huong dan da duoc bac si xac nhan."],
      sourceNote: "SOP giao duc nguoi benh noi bo, can hoi dong/bac si duyet rieng."
    },
    {
      actorName: "Admin Phong Kham",
      actorRole: "CLINIC_ADMIN",
      accessContext: { role: "CLINIC_ADMIN", organizationId: "org-demo", clinicSiteId: "site-demo" },
      resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
      confirmationChecked: true,
      reason: "Demo preview hop dong server action cho tao template draft."
    }
  );

  return (
    <>
      <PageHeader eyebrow="Template management" title="Quan ly mau loi dan va checklist" actions={<button className="button">Tao template draft</button>} />
      <section className="panel" style={{ marginBottom: 16 }}>
        <h2>Template draft preview</h2>
        <p>
          <StatusBadge>{templateDraftAction.status}</StatusBadge> {templateDraftAction.serverActionName}
        </p>
        <p>Backend guard: {templateDraftAction.backendGuard.reason}</p>
        <p>Persistence: {templateDraftAction.persistenceMode}</p>
        <p>{templateDraftAction.safetyBoundary}</p>
      </section>
      <section className="grid cols-3">
        {templates.map((template) => (
          <div className="card" key={template}>
            <h3>{template}</h3>
            <p className="eyebrow">Trang thai: draft governance, can bac si duyet truoc production.</p>
          </div>
        ))}
      </section>
    </>
  );
}
