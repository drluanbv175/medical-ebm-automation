export function StatCard({ label, value, tone }: { label: string; value: string | number; tone?: "red" | "yellow" | "green" }) {
  return (
    <div className="card stat">
      <span>{label}</span>
      <strong className={tone ? `text-${tone}` : undefined}>{value}</strong>
    </div>
  );
}
