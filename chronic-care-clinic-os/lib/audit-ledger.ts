import type { AuditEvent } from "./audit";

export type AuditLedgerEntry = AuditEvent & {
  sequence: number;
  previousHash: string;
  eventHash: string;
  immutableAfterAppend: true;
};

export type AuditLedgerValidation = {
  valid: boolean;
  checkedEntries: number;
  brokenAtSequence?: number;
  reason: string;
};

export function buildAuditLedger(events: AuditEvent[]): AuditLedgerEntry[] {
  return events.reduce<AuditLedgerEntry[]>((ledger, event) => {
    const previousHash = ledger.at(-1)?.eventHash ?? "GENESIS";
    const sequence = ledger.length + 1;
    const eventHash = hashAuditPayload({ ...event, sequence, previousHash });
    ledger.push({
      ...event,
      sequence,
      previousHash,
      eventHash,
      immutableAfterAppend: true
    });
    return ledger;
  }, []);
}

export function appendAuditEventPreview(ledger: AuditLedgerEntry[], event: AuditEvent): AuditLedgerEntry {
  const previousHash = ledger.at(-1)?.eventHash ?? "GENESIS";
  const sequence = ledger.length + 1;
  return {
    ...event,
    sequence,
    previousHash,
    eventHash: hashAuditPayload({ ...event, sequence, previousHash }),
    immutableAfterAppend: true
  };
}

export function validateAuditLedger(ledger: AuditLedgerEntry[]): AuditLedgerValidation {
  for (let index = 0; index < ledger.length; index += 1) {
    const entry = ledger[index];
    const expectedPreviousHash = index === 0 ? "GENESIS" : ledger[index - 1].eventHash;
    if (entry.sequence !== index + 1) {
      return {
        valid: false,
        checkedEntries: index,
        brokenAtSequence: entry.sequence,
        reason: "Audit sequence is not contiguous."
      };
    }
    if (entry.previousHash !== expectedPreviousHash) {
      return {
        valid: false,
        checkedEntries: index,
        brokenAtSequence: entry.sequence,
        reason: "Audit previousHash does not match prior eventHash."
      };
    }
    const expectedHash = hashAuditPayload({
      id: entry.id,
      actor: entry.actor,
      actorRole: entry.actorRole,
      actionType: entry.actionType,
      entityType: entry.entityType,
      entityId: entry.entityId,
      summary: entry.summary,
      createdAt: entry.createdAt,
      sequence: entry.sequence,
      previousHash: entry.previousHash
    });
    if (entry.eventHash !== expectedHash) {
      return {
        valid: false,
        checkedEntries: index,
        brokenAtSequence: entry.sequence,
        reason: "Audit eventHash does not match canonical payload."
      };
    }
  }

  return {
    valid: true,
    checkedEntries: ledger.length,
    reason: "Audit ledger is append-only and hash chain is intact."
  };
}

function hashAuditPayload(payload: Record<string, unknown>): string {
  const canonical = Object.keys(payload)
    .sort()
    .map((key) => `${key}:${String(payload[key])}`)
    .join("|");
  let hash = 2166136261;
  for (let index = 0; index < canonical.length; index += 1) {
    hash ^= canonical.charCodeAt(index);
    hash = Math.imul(hash, 16777619);
  }
  return `fnv1a-${(hash >>> 0).toString(16).padStart(8, "0")}`;
}
