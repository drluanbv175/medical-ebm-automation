import assert from "node:assert/strict";
import test from "node:test";

import { buildPersistentAuditWritePlan } from "../lib/audit-storage-contract";
import {
  runPersistentWorkflowTransactionHarness,
  type PersistentTransactionFailurePoint,
  type PersistentTransactionState
} from "../lib/persistent-transaction";
import {
  buildPrismaTransactionContract,
  evaluatePrismaTestDatabaseGate,
  validatePrismaTransactionContract
} from "../lib/prisma-transaction-contract";
import {
  evaluatePrismaRollbackEvidenceReport,
  validatePrismaRollbackEvidenceReportSchema,
  type PrismaRollbackEvidenceReport
} from "../lib/prisma-rollback-evidence";
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

test("prisma transaction contract stays disabled until real rollback tests exist", () => {
  const contract = buildPrismaTransactionContract(plan);

  assert.equal(contract.adapter, "PRISMA_TRANSACTION_CONTRACT_ONLY");
  assert.equal(contract.productionCommitDisabled, true);
  assert.equal(contract.sameTransactionRequired, true);
  assert.equal(contract.businessOperation, "INSERT_IMMUTABLE_VERSION");
  assert.equal(contract.auditEntityType, "CarePlanVersion");
  assert.deepEqual(validatePrismaTransactionContract(contract), []);
  assert.ok(contract.blockedReasons.includes("Real Prisma adapter is not enabled until rollback tests run against a test database."));
  assert.ok(contract.requiredOperations.includes("APPLY_EXACTLY_ONE_BUSINESS_WRITE"));
  assert.ok(contract.requiredOperations.includes("INSERT_EXACTLY_ONE_AUDIT_LOG_ROW"));
  assert.ok(contract.requiredRollbackCases.includes("FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT"));
  assert.ok(contract.forbiddenAdapterBehaviors.includes("NO_AUDIT_LOG_UPDATE_OR_DELETE"));
});

test("prisma test database gate requires rollback evidence before adapter promotion", () => {
  const contract = buildPrismaTransactionContract(plan);
  const missingEvidence = evaluatePrismaTestDatabaseGate(contract, {
    testDatabaseOnly: true,
    noProductionData: true,
    migrationApplied: true,
    auditMutationBlocked: false,
    rollbackCases: {
      FAIL_BEFORE_BUSINESS_WRITE: true,
      FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT: false,
      FAIL_AFTER_AUDIT_BEFORE_COMMIT: false
    },
    evidenceArtifact: null,
    reviewerSignoff: null
  });

  assert.equal(missingEvidence.canEnableTestDatabaseAdapter, false);
  assert.equal(missingEvidence.canEnableProductionCommit, false);
  assert.equal(missingEvidence.productionCommitDisabled, true);
  assert.ok(missingEvidence.blockedReasons.includes("AuditLog UPDATE/DELETE must be blocked in the test database."));
  assert.ok(missingEvidence.blockedReasons.includes("Missing rollback evidence after business write before AuditLog insert."));
  assert.ok(missingEvidence.blockedReasons.includes("Missing reviewer signoff for transaction rollback evidence."));
});

test("prisma test database gate can only unlock test adapter, never production commit", () => {
  const contract = buildPrismaTransactionContract(plan);
  const gate = evaluatePrismaTestDatabaseGate(contract, {
    testDatabaseOnly: true,
    noProductionData: true,
    migrationApplied: true,
    auditMutationBlocked: true,
    rollbackCases: {
      FAIL_BEFORE_BUSINESS_WRITE: true,
      FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT: true,
      FAIL_AFTER_AUDIT_BEFORE_COMMIT: true
    },
    evidenceArtifact: "reports/ccos-prisma-rollback-test.md",
    reviewerSignoff: "reviewer:quality-manager"
  });

  assert.equal(gate.canEnableTestDatabaseAdapter, true);
  assert.equal(gate.canEnableProductionCommit, false);
  assert.equal(gate.productionCommitDisabled, true);
  assert.deepEqual(gate.blockedReasons, []);
  assert.ok(gate.requiredEvidence.includes("Rollback observed after AuditLog insert before commit"));
});

test("prisma rollback evidence schema blocks malformed or incomplete reports", () => {
  const malformed = validatePrismaRollbackEvidenceReportSchema({
    artifactKind: "PRISMA_ROLLBACK_EVIDENCE_REPORT",
    artifactVersion: 1,
    workflowActionName: "approveCarePlanVersion",
    databaseScope: "ISOLATED_TEST_DATABASE",
    productionDataPresent: false,
    migration: {
      migrationName: "202606190001_audit_log_hash_chain_hardening",
      auditLogHardeningApplied: false
    },
    auditMutationProbe: {
      updateBlocked: false,
      deleteBlocked: false,
      observedErrorCode: null
    },
    rollbackProbes: {},
    evidenceArtifact: null,
    reviewerSignoff: null,
    productionCommitRequested: false
  });

  assert.equal(malformed.valid, false);
  assert.equal(malformed.report, null);
  assert.ok(malformed.blockedReasons.includes("rollbackProbes.FAIL_BEFORE_BUSINESS_WRITE is required."));
});

test("prisma rollback evidence report gates only the test database adapter", () => {
  const contract = buildPrismaTransactionContract(plan);
  const report = completeRollbackEvidenceReport();
  const schema = validatePrismaRollbackEvidenceReportSchema(report);

  assert.equal(schema.valid, true);
  assert.ok(schema.report);

  const readiness = evaluatePrismaRollbackEvidenceReport(contract, schema.report);

  assert.equal(readiness.reportReady, true);
  assert.equal(readiness.canEnableTestDatabaseAdapter, true);
  assert.equal(readiness.canEnableProductionCommit, false);
  assert.equal(readiness.productionCommitDisabled, true);
  assert.deepEqual(readiness.blockedReasons, []);
});

test("prisma rollback evidence report rejects production-like data even with rollback traces", () => {
  const contract = buildPrismaTransactionContract(plan);
  const unsafeReport: PrismaRollbackEvidenceReport = {
    ...completeRollbackEvidenceReport(),
    databaseScope: "PRODUCTION_DATABASE",
    productionDataPresent: true
  };
  const readiness = evaluatePrismaRollbackEvidenceReport(contract, unsafeReport);

  assert.equal(readiness.reportReady, false);
  assert.equal(readiness.canEnableTestDatabaseAdapter, false);
  assert.equal(readiness.canEnableProductionCommit, false);
  assert.ok(readiness.blockedReasons.includes("Evidence must come from an isolated test database only."));
  assert.ok(readiness.blockedReasons.includes("Test database must contain no production patient data."));
});

function completeRollbackEvidenceReport(): PrismaRollbackEvidenceReport {
  return {
    artifactKind: "PRISMA_ROLLBACK_EVIDENCE_REPORT",
    artifactVersion: 1,
    workflowActionName: "approveCarePlanVersion",
    databaseScope: "ISOLATED_TEST_DATABASE",
    productionDataPresent: false,
    migration: {
      migrationName: "202606190001_audit_log_hash_chain_hardening",
      auditLogHardeningApplied: true
    },
    auditMutationProbe: {
      updateBlocked: true,
      deleteBlocked: true,
      observedErrorCode: "P0001"
    },
    rollbackProbes: {
      FAIL_BEFORE_BUSINESS_WRITE: passedRollbackProbe(),
      FAIL_AFTER_BUSINESS_WRITE_BEFORE_AUDIT: passedRollbackProbe(),
      FAIL_AFTER_AUDIT_BEFORE_COMMIT: passedRollbackProbe()
    },
    evidenceArtifact: "reports/ccos-prisma-rollback-test.md",
    reviewerSignoff: {
      reviewer: "quality-manager",
      role: "QUALITY_MANAGER",
      signedAt: "2026-07-15T06:30:00+07:00"
    },
    productionCommitRequested: false
  };
}

function passedRollbackProbe() {
  return {
    status: "PASSED" as const,
    businessWriteCountAfterRollback: 0,
    auditLogCountAfterRollback: 0,
    observedTrace: ["BEGIN_TRANSACTION", "ROLLBACK_ATOMICALLY"]
  };
}
