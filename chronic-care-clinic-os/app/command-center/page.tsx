import Link from "next/link";
import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { buildCommandCenterSnapshot } from "@/lib/care-orchestrator";
import { patients } from "@/lib/seed-data";

export default function CommandCenterPage() {
  const snapshot = buildCommandCenterSnapshot(patients);
  const priorityQueue = snapshot.queue.slice(0, 18);

  return (
    <>
      <PageHeader
        eyebrow={`Command center | cap nhat ${snapshot.generatedAt}`}
        title="Dieu phoi tu dong benh man"
        actions={
          <>
            <Link className="button" href="/tasks">
              Xem task
            </Link>
            <Link className="button secondary" href="/admin/rules">
              Rule governance
            </Link>
          </>
        }
      />

      <div className="danger-box">
        Day la hang doi dieu phoi noi bo. He thong khong tu chan doan, khong tu ke don, khong tu thay doi dieu tri va khong gui loi khuyen dieu tri cho nguoi benh.
      </div>

      <section className="grid cols-4" style={{ marginTop: 16 }}>
        <StatCard label="Care gaps dang mo" value={snapshot.activeCareGaps} />
        <StatCard label="Can xu ly khan" value={snapshot.urgentCareGaps} tone="red" />
        <StatCard label="Bac si can xem" value={snapshot.physicianReview} tone="yellow" />
        <StatCard label="Tin nhan bi chan an toan" value={snapshot.blockedPatientMessages} />
      </section>

      <section className="grid cols-4" style={{ marginTop: 16 }}>
        <StatCard label="Duyet care plan" value={snapshot.carePlanApprovalQueue} />
        <StatCard label="Lab can review" value={snapshot.labReviewQueue} />
        <StatCard label="Ra soat thuoc" value={snapshot.medicationReviewQueue} />
        <StatCard label="Khoi phuc tai kham" value={snapshot.followUpRecoveryQueue} />
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Hang doi uu tien lien phong ban</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Uu tien</th>
              <th>Nguoi benh</th>
              <th>Loai viec</th>
              <th>Phu trach</th>
              <th>SLA</th>
              <th>Ly do</th>
              <th>Hanh dong an toan</th>
            </tr>
          </thead>
          <tbody>
            {priorityQueue.map((gap) => (
              <tr key={gap.id}>
                <td>
                  <StatusBadge>{gap.priority}</StatusBadge>
                </td>
                <td>
                  <Link href={`/patients/${gap.patientId}`}>
                    <strong>{gap.patientName}</strong>
                  </Link>
                  <div className="eyebrow">{gap.medicalRecordNumber}</div>
                  <RiskBadge level={gap.riskLevel} />
                </td>
                <td>
                  <strong>{gap.title}</strong>
                  <div className="eyebrow">{gap.category}</div>
                </td>
                <td>{gap.assignedRole}</td>
                <td>{gap.dueDate}</td>
                <td>{gap.reason}</td>
                <td>
                  {gap.recommendedAction}
                  <div className="eyebrow">
                    {gap.patientCommunicationAllowed ? "Duoc lien he bang template da duyet" : "Khong gui tin nhan tu dong"}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="grid cols-3" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Phan bo doi ngu</h2>
          <p>Bac si: {snapshot.physicianReview}</p>
          <p>Dieu duong: {snapshot.nurseQueue}</p>
          <p>Dieu phoi vien: {snapshot.coordinatorQueue}</p>
          <p>Duoc si: {snapshot.pharmacistQueue}</p>
        </div>
        <div className="panel">
          <h2>Rui ro dan so</h2>
          <p>Nguy co do: {snapshot.redPatients}</p>
          <p>Nguy co vang: {snapshot.yellowPatients}</p>
          <p>Tong nguoi benh: {snapshot.totalPatients}</p>
        </div>
        <div className="panel">
          <h2>Chot an toan</h2>
          <p>Moi care gap deu yeu cau xac nhan bac si neu tac dong den quyet dinh lam sang.</p>
          <p>Giao tiep nguoi benh chi cho phep khi co dong y va template da phe duyet.</p>
        </div>
      </section>
    </>
  );
}
