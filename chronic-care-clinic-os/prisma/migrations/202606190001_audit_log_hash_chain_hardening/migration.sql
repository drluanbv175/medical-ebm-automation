-- Reviewed AuditLog hardening migration.
-- Scope: enforce the persistent append-only hash-chain contract for AuditLog.
-- Assumption: baseline Prisma schema has already created AuditLog with
-- sequence, previousHash, eventHash and immutableAfterAppend columns.

CREATE UNIQUE INDEX IF NOT EXISTS "AuditLog_sequence_key"
  ON "AuditLog"("sequence");

CREATE UNIQUE INDEX IF NOT EXISTS "AuditLog_eventHash_key"
  ON "AuditLog"("eventHash");

CREATE INDEX IF NOT EXISTS "AuditLog_entityType_entityId_idx"
  ON "AuditLog"("entityType", "entityId");

ALTER TABLE "AuditLog"
  ADD CONSTRAINT "AuditLog_sequence_positive"
  CHECK ("sequence" > 0);

ALTER TABLE "AuditLog"
  ADD CONSTRAINT "AuditLog_previousHash_not_empty"
  CHECK (length("previousHash") > 0);

ALTER TABLE "AuditLog"
  ADD CONSTRAINT "AuditLog_eventHash_not_empty"
  CHECK (length("eventHash") > 0);

ALTER TABLE "AuditLog"
  ADD CONSTRAINT "AuditLog_immutable_after_append_true"
  CHECK ("immutableAfterAppend" = true);

CREATE OR REPLACE FUNCTION prevent_audit_log_mutation()
RETURNS trigger AS $$
BEGIN
  RAISE EXCEPTION 'AuditLog rows are append-only; UPDATE and DELETE are blocked';
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS "AuditLog_prevent_update" ON "AuditLog";
CREATE TRIGGER "AuditLog_prevent_update"
  BEFORE UPDATE ON "AuditLog"
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();

DROP TRIGGER IF EXISTS "AuditLog_prevent_delete" ON "AuditLog";
CREATE TRIGGER "AuditLog_prevent_delete"
  BEFORE DELETE ON "AuditLog"
  FOR EACH ROW EXECUTE FUNCTION prevent_audit_log_mutation();
