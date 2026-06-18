import { can, canAccessResource, type AccessContext, type Permission, type ResourceScope } from "./rbac";

export type GuardDecision = {
  allowed: boolean;
  reason: string;
  auditRequired: boolean;
};

export function authorizeBackendAction(context: AccessContext, permission: Permission, resource: ResourceScope): GuardDecision {
  if (!can(context.role, permission)) {
    return { allowed: false, reason: `Missing permission ${permission}`, auditRequired: true };
  }
  if (!canAccessResource(context, resource)) {
    return { allowed: false, reason: "Cross-organization or cross-site access denied", auditRequired: true };
  }
  return { allowed: true, reason: "Allowed", auditRequired: true };
}

export function assertAuditImmutable(actionType: string): GuardDecision {
  if (["UPDATE_AUDIT_LOG", "DELETE_AUDIT_LOG"].includes(actionType)) {
    return { allowed: false, reason: "Audit logs are append-only for normal UI", auditRequired: true };
  }
  return { allowed: true, reason: "Append-only audit action", auditRequired: true };
}
