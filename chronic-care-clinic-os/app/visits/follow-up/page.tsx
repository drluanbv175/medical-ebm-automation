import { PageHeader } from "@/components/PageHeader";
import { WorkflowChecklist } from "@/components/WorkflowChecklist";
import { patients } from "@/lib/seed-data";

export default function FollowUpPage() {
  const sample = patients.find((patient) => patient.carePlan.status === "APPROVED") ?? patients[0];
  return (
    <>
      <PageHeader eyebrow="Luong tai kham" title="Cap nhat tien trien va muc tieu" />
      <section className="grid cols-2">
        <div className="panel">
          <WorkflowChecklist
            steps={[
              { label: "Nhac hen truoc kham", done: true },
              { label: "Cap nhat sinh hieu va thuoc", done: false },
              { label: "Hien muc tieu lan truoc", done: true },
              { label: "Hien xet nghiem moi", done: true },
              { label: "Hien task chua hoan thanh", done: true },
              { label: "Bac si danh gia tien trien", done: false },
              { label: "Cap nhat care plan", done: false },
              { label: "Chot lich tai kham", done: false },
              { label: "In loi dan moi", done: false }
            ]}
          />
        </div>
        <div className="panel">
          <h2>Muc tieu cua {sample.fullName}</h2>
          {sample.carePlan.goals.map((goal) => (
            <p key={goal.goalName}>
              <strong>{goal.goalDomain}</strong>: {goal.goalName} - {goal.status}
            </p>
          ))}
        </div>
      </section>
    </>
  );
}
