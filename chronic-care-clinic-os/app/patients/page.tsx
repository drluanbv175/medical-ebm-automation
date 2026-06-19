import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { StatusBadge } from "@/components/Badge";
import { patients } from "@/lib/seed-data";
import { previewRegisterPatientAction } from "@/lib/workflow-actions";

export default function PatientsPage() {
  const registrationAction = previewRegisterPatientAction(
    {
      fullName: "Demo Nguyen Van A",
      dateOfBirth: "1962-04-12",
      sex: "Male",
      phone: "0900000000",
      consentStatus: "PENDING",
      intakeReason: "Dang ky sang loc va theo doi tang huyet ap, dai thao duong.",
      chronicProgramCandidates: ["Hypertension", "Type 2 Diabetes"]
    },
    {
      actorName: "Le Tan Demo",
      actorRole: "RECEPTIONIST",
      accessContext: { role: "RECEPTIONIST", organizationId: "org-demo", clinicSiteId: "site-demo" },
      resourceScope: { organizationId: "org-demo", clinicSiteId: "site-demo" },
      confirmationChecked: true,
      reason: "Demo preview hop dong server action cho dang ky nguoi benh moi."
    }
  );

  return (
    <>
      <PageHeader
        eyebrow="Patient registry"
        title="Danh sach nguoi benh"
        actions={
          <>
            <input className="input" placeholder="Tim theo ten, ma HS, so dien thoai" />
            <select className="select" aria-label="Loc nguy co">
              <option>Tat ca muc nguy co</option>
              <option>Do</option>
              <option>Vang</option>
              <option>Xanh</option>
            </select>
            <button className="button">Dang ky nguoi benh</button>
          </>
        }
      />
      <section className="panel" style={{ marginBottom: 16 }}>
        <h2>Patient registration preview</h2>
        <p>
          <StatusBadge>{registrationAction.status}</StatusBadge> {registrationAction.serverActionName}
        </p>
        <p>Backend guard: {registrationAction.backendGuard.reason}</p>
        <p>Persistence: {registrationAction.persistenceMode}</p>
        <p>{registrationAction.safetyBoundary}</p>
      </section>
      <section className="panel">
        <PatientTable patients={patients} />
      </section>
    </>
  );
}
