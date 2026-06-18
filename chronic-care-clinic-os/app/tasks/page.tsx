import { PageHeader } from "@/components/PageHeader";
import { patients } from "@/lib/seed-data";

export default function TasksPage() {
  const tasks = patients.flatMap((patient) => patient.tasks.map((task) => ({ patient, task })));
  return (
    <>
      <PageHeader eyebrow="Care coordination tasks" title="Task qua han va task nguy co" />
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
            {tasks.map(({ patient, task }) => (
              <tr key={task.id}>
                <td>{patient.fullName}</td>
                <td>{task.taskType}</td>
                <td>{task.priority}</td>
                <td>{task.dueDate}</td>
                <td>{task.assignedTo}</td>
                <td>{task.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
