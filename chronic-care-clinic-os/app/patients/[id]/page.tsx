import { notFound } from "next/navigation";
import { RiskBadge, StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { assessRisk } from "@/lib/clinical-safety";
import { getPatient } from "@/lib/seed-data";

export default function PatientDetailPage({ params }: { params: { id: string } }) {
  const patient = getPatient(params.id);
  if (!patient) notFound();
  const assessment = assessRisk(patient);

  return (
    <>
      <PageHeader
        eyebrow={patient.medicalRecordNumber}
        title={patient.fullName}
        actions={
          <>
            <RiskBadge level={assessment.suggestedRiskLevel} />
            <button className="button secondary">Tao care plan draft</button>
            <button className="button">In loi dan A5</button>
          </>
        }
      />

      {assessment.safetyMessage ? <div className="danger-box">{assessment.safetyMessage}</div> : null}

      <div className="tabs">
        {["Tong quan", "Benh man", "Thuoc", "Sinh hieu", "Xet nghiem", "Care plan", "Lich hen", "Lan kham", "Loi dan", "Task", "Lien he", "Chuyen tuyen", "Audit"].map((tab) => (
          <span key={tab}>{tab}</span>
        ))}
      </div>

      <section className="grid cols-3">
        <div className="panel">
          <h2>Hanh chinh</h2>
          <p>Ngay sinh: {patient.dateOfBirth}</p>
          <p>Gioi tinh: {patient.sex}</p>
          <p>Dien thoai: {patient.phone}</p>
          <p>Nguoi lien he: {patient.emergencyContact}</p>
        </div>
        <div className="panel">
          <h2>Benh man</h2>
          {patient.conditions.map((condition) => (
            <p key={condition.conditionCode}>
              <strong>{condition.conditionName}</strong> <StatusBadge>{condition.severity}</StatusBadge>
            </p>
          ))}
        </div>
        <div className="panel">
          <h2>Rule triggered</h2>
          {assessment.triggeredRules.map((rule) => (
            <p key={rule.ruleName}>
              <RiskBadge level={rule.severity} /> {rule.ruleDescription}
            </p>
          ))}
        </div>
      </section>

      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Thuoc dang dung</h2>
          <table className="table">
            <tbody>
              {patient.medications.map((medication) => (
                <tr key={`${medication.genericName}-${medication.drugName}`}>
                  <td>{medication.drugName}</td>
                  <td>{medication.category}</td>
                  <td>{medication.medicationClass}</td>
                  <td>{medication.adherenceStatus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h2>Care plan</h2>
          <p>
            Trang thai: <StatusBadge>{patient.carePlan.status}</StatusBadge>
          </p>
          <p>Van de chinh: {patient.carePlan.mainProblems.join(", ")}</p>
          <p>Ngay tai kham: {patient.carePlan.nextFollowUpDate}</p>
          <p>{patient.carePlan.redFlagPlan}</p>
        </div>
      </section>

      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Sinh hieu gan nhat</h2>
          <p>
            HA {patient.vitals[0].systolicBp}/{patient.vitals[0].diastolicBp} mmHg, Mach {patient.vitals[0].heartRate}
          </p>
          <p>BMI {patient.vitals[0].bmi}</p>
        </div>
        <div className="panel">
          <h2>Xet nghiem</h2>
          <table className="table">
            <tbody>
              {patient.labs.map((lab) => (
                <tr key={lab.testCode}>
                  <td>{lab.testName}</td>
                  <td>
                    {lab.resultValue} {lab.unit}
                  </td>
                  <td>{lab.abnormalFlag}</td>
                  <td>{lab.reviewStatus}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}
