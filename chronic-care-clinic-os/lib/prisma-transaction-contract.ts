import type { PersistentWorkflowActionPlan } from "./workflow-actions";

export type PrismaTransactionReadiness =
  | "CONTRACT_READY_NOT_CONNECTED"
  | "BLOCKED_BY_PERSISTENT_PLAN"
  | "BLOCKED_UNTIL_REAL_DB_ROLLBACK_TESTS";

export type PrismaTransactionContract = {
  adapter: "PRISMA_TRANSACTION_CONTRACT_ONLY";
  readiness: PrismaTransactionReadiness;
  productionCommitDisabled: true;
  planActionName: PersistentWorkflowActionPlan["actionName"];
  sameTransactionRequired: true;
  requiredOperations: [
    "RE_READ_SOURCE_ROWS_WITH_ORG_SITE_SCOPE",
    "APPLY_EXACTLY_ONE_BUSINESS_WRITE",
    "INSERT_EXACTLY_ONE_AUDIT_LOG_ROW",
    "VALIDATE_AUDIT_HASH_CHAIN_BEFORE_COMMIT"
  ];
  requiredRollbackCases: [
    "FAIL_BEFORE_BUSINESS_WRITE",
    "FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT",
    "FAIL_AFTER_AUDIT_BEFORE_COMMIT"
  ];
  blockedReasons: string[];
  forbiddenAdapterBehaviors: string[];
  businessOperation: string | null;
  auditEntityType: string | null;
};

export function buildPrismaTransactionContract(plan: PersistentWorkflowActionPlan): PrismaTransactionContract {
  const blockedReasons = [
    ...(!plan.allowed ? plan.blockedReasons : []),
    ...(!plan.businessWritePlan ? ["Missing business write plan."] : []),
    ...(!plan.auditWritePlan ? ["Missing AuditLog write plan."] : []),
    "Real Prisma adapter is not enabled until rollback tests run against a test database."
  ];

  return {
    adapter: "PRISMA_TRANSACTION_CONTRACT_ONLY",
    readiness: blockedReasons.length > 1 ? "BLOCKED_BY_PERSISTENT_PLAN" : "CONTRACT_READY_NOT_CONNECTED",
    productionCommitDisabled: true,
    planActionName: plan.actionName,
    sameTransactionRequired: true,
    requiredOperations: [
      "RE_READ_SOURCE_ROWS_WITH_ORG_SITE_SCOPE",
      "APPLY_EXACTLY_ONE_BUSINESS_WRITE",
      "INSERT_EXACTLY_ONE_AUDIT_LOG_ROW",
      "VALIDATE_AUDIT_HASH_CHAIN_BEFORE_COMMIT"
    ],
    requiredRollbackCases: [
      "FAIL_BEFORE_BUSINESS_WRITE",
      "FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT",
      "FAIL_AFTER_AUDIT_BEFORE_COMMIT"
    ],
    blockedReasons,
    forbiddenAdapterBehaviors: [
      "NO_BUSINESS_WRITE_OUTSIDE_TRANSACTION",
      "NO_AUDIT_LOG_INSERT_OUTSIDE_TRANSACTION",
      "NO_PATIENT_MESSAGE",
      "NO_PRESCRIPTION",
      "NO_EXTERNAL_EMR_WRITEBACK",
      "NO_AUDIT_LOG_UPDATE_OR_DELETE"
    ],
    businessOperation: plan.businessWritePlan?.operation ?? null,
    auditEntityType: plan.auditWritePlan?.auditLogRecord.entityType ?? null
  };
}

export function validatePrismaTransactionContract(contract: PrismaTransactionContract): string[] {
  const blockedReasons = [
    ...(contract.adapter === "PRISMA_TRANSACTION_CONTRACT_ONLY" ? [] : ["Adapter must remain contract-only."]),
    ...(contract.productionCommitDisabled ? [] : ["Production commit must remain disabled."]),
    ...(contract.sameTransactionRequired ? [] : ["Business write and AuditLog insert must use one transaction."]),
    ...(contract.requiredOperations.includes("APPLY_EXACTLY_ONE_BUSINESS_WRITE")
      ? []
      : ["Contract must require exactly one business write."]),
    ...(contract.requiredOperations.includes("INSERT_EXACTLY_ONE_AUDIT_LOG_ROW")
      ? []
      : ["Contract must require exactly one AuditLog insert."]),
    ...(contract.requiredRollbackCases.length === 3 ? [] : ["Contract must keep all three rollback test cases."]),
    ...(contract.forbiddenAdapterBehaviors.includes("NO_AUDIT_LOG_UPDATE_OR_DELETE")
      ? []
      : ["Adapter must forbid AuditLog update/delete paths."])
  ];

  return blockedReasons;
}
