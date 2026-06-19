import type { AuditEvent } from "./audit";
import { appendAuditEventPreview, type AuditLedgerEntry } from "./audit-ledger";

export type PersistedAuditLogRecord = {
  id: string;
  userId: string | null;
  actionType: AuditEvent["actionType"];
  entityType: string;
  entityId: string;
  beforeData: Record<string, unknown> | null;
  afterData: Record<string, unknown> | null;
  ipAddress: string | null;
  userAgent: string | null;
  sequence: number;
  previousHash: string;
  eventHash: string;
  immutableAfterAppend: true;
  createdAt: string;
};

export type AuditWriteIntent = {
  userId: string | null;
  actor: string;
  actorRole: AuditEvent["actorRole"];
  actionType: AuditEvent["actionType"];
  entityType: string;
  entityId: string;
  summary: string;
  beforeData?: Record<string, unknown> | null;
  afterData?: Record<string, unknown> | null;
  ipAddress?: string | null;
  userAgent?: string | null;
  createdAt: string;
};

export type AuditStorageWritePlan = {
  mode: "PERSISTENT_APPEND_ONLY";
  transactionRequired: true;
  mutationPolicy: "INSERT_ONLY_NO_UPDATE_NO_DELETE";
  expectedPreviousHash: string;
  auditLogRecord: PersistedAuditLogRecord;
  ledgerEntry: AuditLedgerEntry;
  requiredDatabaseGuards: string[];
};

export type AuditStorageValidation = {
  valid: boolean;
  reason: string;
  blockedReasons: string[];
};

export function buildPersistentAuditWritePlan(
  existingLedger: AuditLedgerEntry[],
  intent: AuditWriteIntent
): AuditStorageWritePlan {
  const ledgerEntry = appendAuditEventPreview(existingLedger, {
    id: `audit-log-${intent.entityType}-${intent.entityId}-${existingLedger.length + 1}`,
    actor: intent.actor,
    actorRole: intent.actorRole,
    actionType: intent.actionType,
    entityType: intent.entityType,
    entityId: intent.entityId,
    summary: intent.summary,
    createdAt: intent.createdAt
  });

  return {
    mode: "PERSISTENT_APPEND_ONLY",
    transactionRequired: true,
    mutationPolicy: "INSERT_ONLY_NO_UPDATE_NO_DELETE",
    expectedPreviousHash: ledgerEntry.previousHash,
    ledgerEntry,
    auditLogRecord: {
      id: ledgerEntry.id,
      userId: intent.userId,
      actionType: intent.actionType,
      entityType: intent.entityType,
      entityId: intent.entityId,
      beforeData: intent.beforeData ?? null,
      afterData: {
        ...(intent.afterData ?? {}),
        auditSummary: intent.summary,
        actor: intent.actor,
        actorRole: intent.actorRole
      },
      ipAddress: intent.ipAddress ?? null,
      userAgent: intent.userAgent ?? null,
      sequence: ledgerEntry.sequence,
      previousHash: ledgerEntry.previousHash,
      eventHash: ledgerEntry.eventHash,
      immutableAfterAppend: true,
      createdAt: intent.createdAt
    },
    requiredDatabaseGuards: [
      "Read the latest AuditLog row ordered by sequence inside the same database transaction.",
      "Insert exactly one AuditLog row with sequence = latest.sequence + 1 and previousHash = latest.eventHash.",
      "Persist eventHash generated from canonical audit payload before committing the business write.",
      "Reject UPDATE_AUDIT_LOG and DELETE_AUDIT_LOG paths for normal application roles.",
      "Commit the business write and AuditLog insert atomically; rollback both on any failure."
    ]
  };
}

export function validatePersistentAuditWritePlan(
  existingLedger: AuditLedgerEntry[],
  plan: AuditStorageWritePlan
): AuditStorageValidation {
  const blockedReasons = [
    ...(plan.transactionRequired ? [] : ["Persistent audit writes must run in the same transaction as the business write."]),
    ...(plan.mutationPolicy === "INSERT_ONLY_NO_UPDATE_NO_DELETE" ? [] : ["AuditLog storage policy must be insert-only."]),
    ...(plan.auditLogRecord.immutableAfterAppend ? [] : ["AuditLog record must be immutable after append."]),
    ...(plan.auditLogRecord.sequence === existingLedger.length + 1 ? [] : ["AuditLog sequence must be contiguous."]),
    ...(plan.auditLogRecord.previousHash === (existingLedger.at(-1)?.eventHash ?? "GENESIS")
      ? []
      : ["AuditLog previousHash must match the latest persisted eventHash."]),
    ...(plan.auditLogRecord.eventHash === plan.ledgerEntry.eventHash ? [] : ["AuditLog eventHash must match the ledger entry hash."])
  ];

  return {
    valid: blockedReasons.length === 0,
    reason:
      blockedReasons.length === 0
        ? "Persistent AuditLog write plan is append-only, hash chained and transaction-bound."
        : "Persistent AuditLog write plan is blocked.",
    blockedReasons
  };
}
