import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { redFlagMessage } from "@/lib/clinical-safety";
import { patients } from "@/lib/seed-data";

export default function RedRiskPage() {
  const red = patients.filter((patient) => patient.suggestedRiskLevel === "RED");
  return (
    <>
      <PageHeader eyebrow="Danh sach nguy co do" title="Can bac si danh gia truc tiep" />
      <div className="danger-box">{redFlagMessage}</div>
      <section className="panel" style={{ marginTop: 16 }}>
        <PatientTable patients={red} />
      </section>
    </>
  );
}
