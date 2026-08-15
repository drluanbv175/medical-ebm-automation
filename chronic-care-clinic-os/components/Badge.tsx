import type { RiskLevel } from "@/lib/types";

export function RiskBadge({ level }: { level: RiskLevel }) {
  const label = level === "RED" ? "Do" : level === "YELLOW" ? "Vang" : "Xanh";
  return <span className={`badge ${level.toLowerCase()}`}>{label}</span>;
}

export function StatusBadge({ children }: { children: React.ReactNode }) {
  return <span className="badge neutral">{children}</span>;
}
