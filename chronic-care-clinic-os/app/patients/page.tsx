import { PageHeader } from "@/components/PageHeader";
import { PatientTable } from "@/components/PatientTable";
import { patients } from "@/lib/seed-data";

export default function PatientsPage() {
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
      <section className="panel">
        <PatientTable patients={patients} />
      </section>
    </>
  );
}
