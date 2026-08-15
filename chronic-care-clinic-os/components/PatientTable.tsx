import Link from "next/link";
import { RiskBadge } from "@/components/Badge";
import type { Patient } from "@/lib/types";

export function PatientTable({ patients }: { patients: Patient[] }) {
  return (
    <table className="table">
      <thead>
        <tr>
          <th>Ma HS</th>
          <th>Nguoi benh</th>
          <th>Benh man</th>
          <th>Nguy co</th>
          <th>Hen gan nhat</th>
          <th>Can xu ly</th>
        </tr>
      </thead>
      <tbody>
        {patients.map((patient) => (
          <tr key={patient.id}>
            <td>{patient.medicalRecordNumber}</td>
            <td>
              <Link href={`/patients/${patient.id}`}>
                <strong>{patient.fullName}</strong>
              </Link>
              <div className="eyebrow">{patient.phone}</div>
            </td>
            <td>{patient.conditions.map((condition) => condition.conditionName).join(", ")}</td>
            <td>
              <RiskBadge level={patient.suggestedRiskLevel} />
            </td>
            <td>{patient.appointments[0]?.scheduledAt.slice(0, 10)}</td>
            <td>{patient.tasks.length > 0 ? patient.tasks.map((task) => task.taskType).join(", ") : "Khong co task mo"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
