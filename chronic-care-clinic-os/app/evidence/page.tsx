import Link from "next/link";
import { StatusBadge } from "@/components/Badge";
import { PageHeader } from "@/components/PageHeader";
import { StatCard } from "@/components/StatCard";
import { buildEvidenceBridgeSnapshot } from "@/lib/evidence-integration";

export default function EvidenceBridgePage() {
  const snapshot = buildEvidenceBridgeSnapshot();
  const pendingItems = snapshot.items.slice(0, 20);

  return (
    <>
      <PageHeader
        eyebrow="Evidence bridge | read-only"
        title="Knowledge pack review queue"
        actions={
          <Link className="button secondary" href="/programs">
            Chuong trinh
          </Link>
        }
      />

      <div className="danger-box">
        Evidence bridge chi doc hang cho cap nhat. Khong tu chan doan, khong tu ke don, khong gui tin nhan nguoi benh va khong tu thay doi dieu tri.
      </div>

      <section className="grid cols-4" style={{ marginTop: 16 }}>
        <StatCard label="Muc cho duyet" value={snapshot.totalQueueItems} />
        <StatCard label="Uu tien cao" value={snapshot.highPriorityItems} tone={snapshot.highPriorityItems ? "red" : undefined} />
        <StatCard label="Pack co cap nhat" value={snapshot.packsWithPendingItems} tone={snapshot.packsWithPendingItems ? "yellow" : undefined} />
        <StatCard label="Pack dang co" value={`${snapshot.activeKnowledgePacks}/${snapshot.expectedKnowledgePacks}`} />
      </section>

      <section className="panel" style={{ marginTop: 16 }}>
        <h2>Hang cho cap nhat knowledge pack</h2>
        <table className="table">
          <thead>
            <tr>
              <th>Uu tien</th>
              <th>Pack</th>
              <th>Bang chung moi</th>
              <th>Nguon</th>
              <th>Ly do</th>
              <th>Trang thai</th>
            </tr>
          </thead>
          <tbody>
            {pendingItems.length === 0 ? (
              <tr>
                <td colSpan={6}>Khong co muc cap nhat dang cho trong queue hien tai.</td>
              </tr>
            ) : (
              pendingItems.map((item) => (
                <tr key={item.queueId}>
                  <td>
                    <StatusBadge>{item.priority}</StatusBadge>
                  </td>
                  <td>
                    <strong>{item.packLabel}</strong>
                    <div className="eyebrow">{item.packId}</div>
                  </td>
                  <td>{item.title}</td>
                  <td>{item.sourceRefs.length ? item.sourceRefs.join(", ") : "Can bo sung truy nguyen"}</td>
                  <td>{item.reasonCodes.join(", ")}</td>
                  <td>
                    {item.reviewStatus}
                    <div className="eyebrow">{item.autoApply ? "Sai chot: auto apply" : "Bac si duyet truoc"}</div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </section>

      <section className="grid cols-2" style={{ marginTop: 16 }}>
        <div className="panel">
          <h2>Chot an toan</h2>
          <p>{snapshot.safetyBoundary}</p>
          <p>Review policy: {snapshot.reviewPolicy}</p>
        </div>
        <div className="panel">
          <h2>Nguon dong bo</h2>
          <p>{snapshot.sourceFile}</p>
          <p>Generated at: {snapshot.generatedAt}</p>
        </div>
      </section>
    </>
  );
}
