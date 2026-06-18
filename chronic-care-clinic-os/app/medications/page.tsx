import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function MedicationsPage() {
  const reviewList = patients.filter((patient) => patient.medications.filter((medication) => medication.isActive).length >= 5);
  return (
    <>
      <PageHeader eyebrow="Medication reconciliation" title="Ra soat thuoc va canh bao can duyet" />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>So thuoc</th>
              <th>Loai canh bao</th>
              <th>Hanh dong</th>
            </tr>
          </thead>
          <tbody>
            {reviewList.map((patient) => (
              <tr key={patient.id}>
                <td>{patient.fullName}</td>
                <td>{patient.medications.length}</td>
                <td>Da thuoc / co the trung nhom dieu tri</td>
                <td>Can bac si hoac duoc si ra soat; khong tu ket luan chong chi dinh.</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
