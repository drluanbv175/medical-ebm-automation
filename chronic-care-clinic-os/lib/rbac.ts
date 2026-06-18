import type { Role } from "./types";

export const permissions = [
  "organization.manage",
  "clinic_site.manage",
  "user.manage",
  "patient.register",
  "patient.view_admin",
  "patient.view_clinical",
  "patient.view_identity",
  "vitals.update",
  "medication.review",
  "care_plan.approve",
  "care_plan.version",
  "task.manage",
  "quality.view",
  "audit.view",
  "export.aggregate",
  "clinical_rules.manage",
  "clinical_rules.approve",
  "handout.approve",
  "safety_alert.review",
  "incident.manage",
  "automation.manage",
  "backend.read",
  "backend.write"
] as const;

export type Permission = (typeof permissions)[number];

export const roleLabels: Record<Role, string> = {
  SUPER_ADMIN: "Super Admin",
  CLINIC_ADMIN: "Clinic Admin",
  PHYSICIAN: "Bac si",
  NURSE: "Dieu duong",
  CARE_COORDINATOR: "Care Coordinator",
  NURSE_COORDINATOR: "Dieu duong / Care Coordinator",
  RECEPTIONIST: "Le tan",
  PHARMACIST: "Duoc si cong tac",
  QUALITY_MANAGER: "Quan ly chat luong",
  READ_ONLY_AUDITOR: "Read-only Auditor",
  PATIENT: "Nguoi benh",
  PATIENT_PORTAL_USER: "Patient Portal User"
};

export const rolePermissions: Record<Role, Permission[]> = {
  SUPER_ADMIN: [...permissions],
  CLINIC_ADMIN: [
    "clinic_site.manage",
    "user.manage",
    "patient.register",
    "patient.view_admin",
    "patient.view_identity",
    "task.manage",
    "quality.view",
    "audit.view",
    "automation.manage",
    "backend.read",
    "backend.write"
  ],
  PHYSICIAN: [
    "patient.register",
    "patient.view_admin",
    "patient.view_clinical",
    "patient.view_identity",
    "vitals.update",
    "medication.review",
    "care_plan.approve",
    "care_plan.version",
    "task.manage",
    "handout.approve",
    "safety_alert.review",
    "backend.read",
    "backend.write"
  ],
  NURSE: ["patient.register", "patient.view_admin", "patient.view_identity", "patient.view_clinical", "vitals.update", "task.manage", "backend.read", "backend.write"],
  CARE_COORDINATOR: ["patient.view_admin", "patient.view_clinical", "task.manage", "backend.read", "backend.write"],
  NURSE_COORDINATOR: [
    "patient.register",
    "patient.view_admin",
    "patient.view_clinical",
    "patient.view_identity",
    "vitals.update",
    "medication.review",
    "task.manage",
    "backend.read",
    "backend.write"
  ],
  RECEPTIONIST: ["patient.register", "patient.view_admin", "patient.view_identity", "backend.read", "backend.write"],
  PHARMACIST: ["patient.view_clinical", "medication.review", "task.manage", "backend.read", "backend.write"],
  QUALITY_MANAGER: ["quality.view", "audit.view", "export.aggregate", "backend.read"],
  READ_ONLY_AUDITOR: ["audit.view", "quality.view", "backend.read"],
  PATIENT: ["patient.view_admin"],
  PATIENT_PORTAL_USER: ["patient.view_admin", "backend.read"]
};

export function can(role: Role, permission: Permission): boolean {
  return rolePermissions[role].includes(permission);
}

export function requirePermission(role: Role, permission: Permission): void {
  if (!can(role, permission)) {
    throw new Error(`Role ${role} does not have permission ${permission}`);
  }
}

export type AccessContext = {
  role: Role;
  organizationId: string;
  clinicSiteId: string;
};

export type ResourceScope = {
  organizationId: string;
  clinicSiteId?: string;
};

export function canAccessResource(context: AccessContext, resource: ResourceScope): boolean {
  if (context.organizationId !== resource.organizationId) return false;
  if (resource.clinicSiteId && context.role !== "SUPER_ADMIN" && context.clinicSiteId !== resource.clinicSiteId) return false;
  return true;
}
