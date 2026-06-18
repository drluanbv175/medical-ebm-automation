import type { Role } from "./types";

export type AuditEvent = {
  id: string;
  actor: string;
  actorRole: Role;
  actionType: "VIEW" | "CREATE" | "UPDATE" | "APPROVE" | "REJECT" | "EXPORT" | "ARCHIVE";
  entityType: string;
  entityId: string;
  summary: string;
  createdAt: string;
};

export const demoAuditEvents: AuditEvent[] = [
  {
    id: "audit-001",
    actor: "BS Nguyen Minh",
    actorRole: "PHYSICIAN",
    actionType: "APPROVE",
    entityType: "CarePlan",
    entityId: "cp-001",
    summary: "Duyet care plan tang huyet ap va dai thao duong.",
    createdAt: "2026-06-18T08:10:00+07:00"
  },
  {
    id: "audit-002",
    actor: "DD Tran Lan",
    actorRole: "NURSE_COORDINATOR",
    actionType: "UPDATE",
    entityType: "VitalSign",
    entityId: "vs-014",
    summary: "Cap nhat sinh hieu truoc kham.",
    createdAt: "2026-06-18T08:20:00+07:00"
  },
  {
    id: "audit-003",
    actor: "QLCL Pham An",
    actorRole: "QUALITY_MANAGER",
    actionType: "EXPORT",
    entityType: "QualityMetric",
    entityId: "qm-monthly",
    summary: "Xuat du lieu tong hop da khu dinh danh.",
    createdAt: "2026-06-18T09:00:00+07:00"
  }
];
