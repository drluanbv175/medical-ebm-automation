import { PageHeader } from "@/components/PageHeader";
import { buildCommandCenterSnapshot } from "@/lib/care-orchestrator";
import { patients } from "@/lib/seed-data";

export default function TasksPage() {
  const snapshot = buildCommandCenterSnapshot(patients);
  return (
    <>
      <PageHeader eyebrow="Care coordination tasks" title="Task tu dong va viec can dieu phoi" />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Nguoi benh</th>
              <th>Task</th>
              <th>Uu tien</th>
              <th>Han</th>
              <th>Phu trach</th>
              <th>Ghi chu</th>
            </tr>
          </thead>
          <tbody>
            {snapshot.queue.map((gap) => (
              <tr key={gap.id}>
                <td>{gap.patientName}</td>
                <td>{gap.title}</td>
                <td>{gap.priority}</td>
                <td>{gap.dueDate}</td>
                <td>{gap.assignedRole}</td>
                <td>{gap.recommendedAction}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
