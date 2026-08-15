import Link from "next/link";
import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { buildVisitPrepQueue } from "@/lib/visit-prep";
import { patients } from "@/lib/seed-data";

export default function VisitPrepPage() {
  const packets = buildVisitPrepQueue(patients);
  const focusPacket = packets[0];

  return (
    <>
      <PageHeader
        eyebrow="Pre-visit planning"
        title="Chuan bi truoc buoi kham"
        actions={
          <Link className="button" href={`/patients/${focusPacket.patientId}`}>
            Mo ho so uu tien
          </Link>
        }
      />

      <div className="danger-box">{focusPacket.safetyBoundary}</div>

      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Packet uu tien</h2>
          <p>
            <strong>{focusPacket.patientName}</strong> ({focusPacket.medicalRecordNumber})
          </p>
          <p>
            Nguy co: <RiskBadge level={focusPacket.riskLevel} />
          </p>
          <p>Chuong trinh: {focusPacket.programNames.join(", ")}</p>
          <WorkflowChecklist
            steps={focusPacket.checklist.map((item) => ({
              label: item.label,
              done: item.done,
              note: `${item.ownerRole} - ${item.note}`
            }))}
          />
        </div>
        <div className="panel">
          <h2>Bac si can xem</h2>
          {focusPacket.clinicianReviewItems.length === 0 ? (
            <p>Khong co gap bac si uu tien trong demo.</p>
          ) : (
            focusPacket.clinicianReviewItems.map((item) => (
              <p key={item.id}>
                <StatusBadge>{item.priority}</StatusBadge> <strong>{item.title}</strong>
                <br />
                <span className="eyebrow">{item.reason}</span>
              </p>
            ))
          )}
        </div>
      </section>

      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Cau hoi dieu duong</h2>
          {focusPacket.nursingIntakePrompts.map((prompt) => (
            <p key={prompt}>{prompt}</p>
          ))}
        </div>
        <div className="panel">
          <h2>Thuoc va lab</h2>
          {focusPacket.medicationQuestions.map((question) => (
            <p key={question}>{question}</p>
          ))}
          {focusPacket.labReviewItems.map((lab) => (
            <p key={lab}>{lab}</p>
          ))}
        </div>
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Hang doi packet</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Nguy co</th>
              <th>Chuong trinh</th>
              <th>Checklist chua xong</th>
              <th>Bac si can xem</th>
            </tr>
          </thead>
          <tbody>
            {packets.slice(0, 20).map((packet) => (
              <tr key={packet.patientId}>
                <td>
                  <Link href={`/patients/${packet.patientId}`}>
                    <strong>{packet.patientName}</strong>
                  </Link>
                  <div className="eyebrow">{packet.medicalRecordNumber}</div>
                </td>
                <td>
                  <RiskBadge level={packet.riskLevel} />
                </td>
                <td>{packet.programNames.join(", ")}</td>
                <td>{packet.checklist.filter((item) => !item.done).length}</td>
                <td>{packet.clinicianReviewItems.length}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
