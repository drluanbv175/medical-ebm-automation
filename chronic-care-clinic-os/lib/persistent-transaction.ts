import { validateAuditLedger, type AuditLedgerEntry } from "./audit-ledger";
import type { PersistentBusinessWritePlan, PersistentWorkflowActionPlan } from "./workflow-actions";

export type PersistentTransactionFailurePoint =
  | "BEFORE_BUSINESS_WRITE"
  | "AFTER_BUSINESS_WRITE_BEFORE_AUDIT"
  | "AFTER_AUDIT_WRITE_BEFORE_COMMIT";

export type PersistentBusinessRecord = {
  entityType: PersistentBusinessWritePlan["entityType"];
  entityId: string;
  operation: PersistentBusinessWritePlan["operation"];
  writeSet: Record<string, unknown>;
  committedAt: string;
  productionCommitDisabled: true;
};

export type PersistentTransactionState = {
  businessRecords: PersistentBusinessRecord[];
  auditLedger: AuditLedgerEntry[];
};

export type PersistentTransactionResult = {
  committed: boolean;
  rolledBack: boolean;
  databaseAdapter: "IN_MEMORY_TRANSACTION_HARNESS_ONLY";
  productionCommitDisabled: true;
  state: PersistentTransactionState;
  blockedReasons: string[];
  trace: string[];
};

export function runPersistentWorkflowTransactionHarness(
  plan: PersistentWorkflowActionPlan,
  currentState: PersistentTransactionState,
  options?: {
    failAt?: PersistentTransactionFailurePoint;
    committedAt?: string;
  }
): PersistentTransactionResult {
  const baseState = cloneState(currentState);
  const blockedReasons = validatePlanCanEnterTransaction(plan);
  if (blockedReasons.length > 0) {
    return blocked(baseState, blockedReasons, ["BLOCKED_BEFORE_TRANSACTION"]);
  }
  const businessWritePlan = plan.businessWritePlan;
  const auditWritePlan = plan.auditWritePlan;
  if (!businessWritePlan || !auditWritePlan) {
    return blocked(baseState, ["Persistent plan lost business or AuditLog write plan after validation."], [
      "BLOCKED_BEFORE_TRANSACTION"
    ]);
  }

  if (options?.failAt === "BEFORE_BUSINESS_WRITE") {
    return rollback(baseState, "Injected failure before business write.");
  }

  const businessRecord: PersistentBusinessRecord = {
    entityType: businessWritePlan.entityType,
    entityId: businessWritePlan.entityId,
    operation: businessWritePlan.operation,
    writeSet: { ...businessWritePlan.writeSet },
    committedAt: options?.committedAt ?? auditWritePlan.auditLogRecord.createdAt,
    productionCommitDisabled: true
  };
  const draftState: PersistentTransactionState = {
    businessRecords: [...baseState.businessRecords, businessRecord],
    auditLedger: [...baseState.auditLedger]
  };

  if (options?.failAt === "AFTER_BUSINESS_WRITE_BEFORE_AUDIT") {
    return rollback(baseState, "Injected failure after business write before AuditLog insert.");
  }

  draftState.auditLedger.push(auditWritePlan.ledgerEntry);
  const ledgerValidation = validateAuditLedger(draftState.auditLedger);
  if (!ledgerValidation.valid) {
    return rollback(baseState, ledgerValidation.reason);
  }

  if (options?.failAt === "AFTER_AUDIT_WRITE_BEFORE_COMMIT") {
    return rollback(baseState, "Injected failure after AuditLog insert before commit.");
  }

  return {
    committed: true,
    rolledBack: false,
    databaseAdapter: "IN_MEMORY_TRANSACTION_HARNESS_ONLY",
    productionCommitDisabled: true,
    state: draftState,
    blockedReasons: [],
    trace: [
      "BEGIN_TRANSACTION",
      "BUSINESS_WRITE_STAGED",
      "AUDIT_LOG_STAGED",
      "LEDGER_HASH_CHAIN_VALIDATED",
      "COMMIT_ATOMICALLY"
    ]
  };
}

function validatePlanCanEnterTransaction(plan: PersistentWorkflowActionPlan): string[] {
  if (!plan.allowed) return plan.blockedReasons.length ? plan.blockedReasons : ["Persistent plan is not allowed."];
  if (!plan.businessWritePlan) return ["Missing business write plan."];
  if (!plan.auditWritePlan) return ["Missing AuditLog write plan."];
  if (!plan.businessWritePlan.requiredAtomicWithAuditLog) return ["Business write is not marked atomic with AuditLog."];
  if (!plan.auditWritePlan.transactionRequired) return ["AuditLog write is not marked transaction-required."];
  if (!plan.businessWritePlan.productionCommitDisabled) return ["Production commit must remain disabled in harness mode."];
  return [];
}

function cloneState(state: PersistentTransactionState): PersistentTransactionState {
  return {
    businessRecords: state.businessRecords.map((record) => ({
      ...record,
      writeSet: { ...record.writeSet }
    })),
    auditLedger: state.auditLedger.map((entry) => ({ ...entry }))
  };
}

function blocked(
  state: PersistentTransactionState,
  blockedReasons: string[],
  trace: string[]
): PersistentTransactionResult {
  return {
    committed: false,
    rolledBack: false,
    databaseAdapter: "IN_MEMORY_TRANSACTION_HARNESS_ONLY",
    productionCommitDisabled: true,
    state,
    blockedReasons,
    trace
  };
}

function rollback(state: PersistentTransactionState, reason: string): PersistentTransactionResult {
  return {
    committed: false,
    rolledBack: true,
    databaseAdapter: "IN_MEMORY_TRANSACTION_HARNESS_ONLY",
    productionCommitDisabled: true,
    state,
    blockedReasons: [reason],
    trace: ["BEGIN_TRANSACTION", "ROLLBACK_ATOMICALLY"]
  };
}
