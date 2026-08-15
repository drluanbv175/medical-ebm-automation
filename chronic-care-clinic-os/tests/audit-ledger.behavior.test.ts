// Hoi quy cho phat hien LOW tu vong lap kiem tra-hoan thien vong 9 (2026-07-22,
// workflow doi khang wf_110cffc4-258): hashAuditPayload() dung FNV-1a 32-bit
// (khong phai ma bam mat ma) - da doi sang SHA-256 (node:crypto).
import assert from "node:assert/strict";
import test from "node:test";

import { buildAuditLedger, validateAuditLedger } from "../lib/audit-ledger";
import { demoAuditEvents } from "../lib/audit";

test("audit ledger hash chain uses a cryptographic SHA-256 digest, not FNV-1a", () => {
  const ledger = buildAuditLedger(demoAuditEvents);
  assert.ok(ledger.length > 0);
  for (const entry of ledger) {
    assert.match(entry.eventHash, /^sha256-[0-9a-f]{64}$/, "eventHash phai la SHA-256 hex 64 ky tu, khong phai fnv1a-XXXXXXXX 32-bit");
  }
});

test("audit ledger validation still detects tampering after the hash algorithm upgrade", () => {
  const ledger = buildAuditLedger(demoAuditEvents);
  const intact = validateAuditLedger(ledger);
  assert.equal(intact.valid, true);

  const tampered = ledger.map((entry, index) =>
    index === 0 ? { ...entry, summary: "TAMPERED: " + entry.summary } : entry
  );
  const broken = validateAuditLedger(tampered);
  assert.equal(broken.valid, false);
  assert.equal(broken.brokenAtSequence, 1);
});
