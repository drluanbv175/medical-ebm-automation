import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { patients } from "@/lib/seed-data";

export default function OverduePage() {
  const overdue = patients.filter((patient) => (patient.missedAppointments ?? 0) > 0);
  return (
    <>
      <PageHeader
        eyebrow="Qua han tai kham"
        title="Danh sach can dieu duong lien he"
        actions={<button className="button">Nhan task goi nhac</button>}
      />
      <section className="panel">
        <PatientTable patients={overdue} />
      </section>
    </>
  );
}
