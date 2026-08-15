import { PageHeader } from "@/components/PageHeader";
import { qualityMetrics } from "@/lib/metrics";

export default function QualityDashboardPage() {
  const metrics = qualityMetrics();

  return (
    <>
      <PageHeader
        eyebrow="Dashboard quan ly chat luong"
        title="Chi so tong hop da khu dinh danh"
        actions={
          <>
            <select className="select" aria-label="Loc ngay">
              <option>Thang 06/2026</option>
            </select>
            <select className="select" aria-label="Loc bac si">
              <option>Tat ca bac si</option>
            </select>
            <button className="button secondary">Xuat CSV</button>
          </>
        }
      />
      <section className="panel">
        <table className="table">
          <thead>
            <tr>
              <th>Chi so</th>
              <th>Tu so</th>
              <th>Mau so</th>
              <th>Ket qua</th>
              <th>Ghi chu</th>
            </tr>
          </thead>
          <tbody>
            {metrics.map((metric) => (
              <tr key={metric.metricName}>
                <td>{metric.metricName}</td>
                <td>{metric.numerator}</td>
                <td>{metric.denominator}</td>
                <td>
                  <strong>{metric.resultValue}%</strong>
                </td>
                <td>{metric.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
