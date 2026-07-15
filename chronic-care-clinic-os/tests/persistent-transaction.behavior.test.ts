import assert from "node:assert/strict";
import test from "node:test";

import { buildPersistentAuditWritePlan } from "../lib/audit-storage-contract";
import {
  runPersistentWorkflowTransactionHarness,
  type PersistentTransactionFailurePoint,
  type PersistentTransactionState
} from "../lib/persistent-transaction";
import type { PersistentBusinessWritePlan, PersistentWorkflowActionPlan, WorkflowActionPreview } from "../lib/workflow-actions";

const auditWritePlan = buildPersistentAuditWritePlan([], {
  userId: null,
  actor: "Dr Test",
  actorRole: "PHYSICIAN",
  actionType: "APPROVE",
  entityType: "CarePlanVersion",
  entityId: "cpv-test-001",
  summary: "Behavior test persistent plan.",
  beforeData: { status: "DRAFT" },
  afterData: { status: "APPROVED_AFTER_PHYSICIAN_SIGNOFF" },
  createdAt: "2026-06-19T00:00:00+07:00"
});

const preview: WorkflowActionPreview = {
  actionName: "approveCarePlanVersion",
  serverActionName: "approveCarePlanVersionAction",
  status: "READY_FOR_SERVER_ACTION",
  allowed: true,
  persistenceMode: "PREVIEW_ONLY_NOT_PERSISTED",
  blockedReasons: [],
  backendGuard: { allowed: true, reason: "Allowed", auditRequired: true },
  auditPreview: {
    id: "audit-preview-behavior",
    actor: "Dr Test",
    actorRole: "PHYSICIAN",
    actionType: "APPROVE",
    entityType: "CarePlanVersion",
    entityId: "cpv-test-001",
    summary: "Preview only.",
    createdAt: "2026-06-19T00:00:00+07:00"
  },
  requiredServerSideGuards: [],
  safetyBoundary: "Behavior test boundary."
};

const businessWritePlan: PersistentBusinessWritePlan = {
  entityType: "CarePlanVersion",
  entityId: "cpv-test-001",
  operation: "INSERT_IMMUTABLE_VERSION",
  requiredAtomicWithAuditLog: true,
  productionCommitDisabled: true,
  writeSet: {
    carePlanId: "cp-test",
    status: "APPROVED_AFTER_PHYSICIAN_SIGNOFF"
  },
  forbiddenSideEffects: ["NO_PATIENT_MESSAGE", "NO_PRESCRIPTION"]
};

const plan: PersistentWorkflowActionPlan = {
  actionName: "approveCarePlanVersion",
  serverActionName: "approveCarePlanVersionAction",
  status: "READY_FOR_ATOMIC_COMMIT_WHEN_DB_WIRING_EXISTS",
  allowed: true,
  persistenceMode: "PERSISTENT_PLAN_NOT_COMMITTED",
  preview,
  auditWritePlan,
  auditValidation: {
    valid: true,
    reason: "Valid persistent audit write plan.",
    blockedReasons: []
  },
  businessWritePlan,
  blockedReasons: [],
  transactionContract: ["Apply exactly one business write and exactly one AuditLog insert inside that transaction."],
  safetyBoundary: "Production commit disabled."
};

function emptyState(): PersistentTransactionState {
  return { businessRecords: [], auditLedger: [] };
}

test("persistent transaction harness commits business and audit writes together", () => {
  const result = runPersistentWorkflowTransactionHarness(plan, emptyState());

  assert.equal(result.committed, true);
  assert.equal(result.rolledBack, false);
  assert.equal(result.productionCommitDisabled, true);
  assert.deepEqual(result.blockedReasons, []);
  assert.equal(result.state.businessRecords.length, 1);
  assert.equal(result.state.auditLedger.length, 1);
  assert.equal(result.state.businessRecords[0].entityId, "cpv-test-001");
  assert.equal(result.state.auditLedger[0].previousHash, "GENESIS");
  assert.ok(result.trace.includes("COMMIT_ATOMICALLY"));
});

test("persistent transaction harness rolls back without mutating input state at every failure point", () => {
  const failurePoints: PersistentTransactionFailurePoint[] = [
    "BEFORE_BUSINESS_WRITE",
    "AFTER_BUSINESS_WRITE_BEFORE_AUDIT",
    "AFTER_AUDIT_WRITE_BEFORE_COMMIT"
  ];

  for (const failAt of failurePoints) {
    const currentState = emptyState();
    const result = runPersistentWorkflowTransactionHarness(plan, currentState, { failAt });

    assert.equal(result.committed, false);
    assert.equal(result.rolledBack, true);
    assert.equal(result.state.businessRecords.length, 0);
    assert.equal(result.state.auditLedger.length, 0);
    assert.equal(currentState.businessRecords.length, 0);
    assert.equal(currentState.auditLedger.length, 0);
    assert.ok(result.trace.includes("ROLLBACK_ATOMICALLY"));
  }
});

test("persistent transaction harness blocks plans that are missing audit or business sides", () => {
  const blockedPlan: PersistentWorkflowActionPlan = {
    ...plan,
    auditWritePlan: null,
    auditValidation: {
      valid: false,
      reason: "Missing audit side.",
      blockedReasons: ["Missing AuditLog write plan."]
    }
  };
  const result = runPersistentWorkflowTransactionHarness(blockedPlan, emptyState());

  assert.equal(result.committed, false);
  assert.equal(result.rolledBack, false);
  assert.equal(result.state.businessRecords.length, 0);
  assert.equal(result.state.auditLedger.length, 0);
  assert.deepEqual(result.trace, ["BLOCKED_BEFORE_TRANSACTION"]);
});
