"""
R2.0 Synthetic EDC Lifecycle Tests — freeze, lock, export, query, correction, backup.

MRAQ_OFFLINE_CI=1 pytest tests/test_r2_0_synthetic_edc_lifecycle.py -v
"""

import pytest

from research_project.synthetic_edc_lifecycle import (
    AuditEntry,
    BackupReceipt,
    DataFreezeManager,
    DataLockManager,
    EDCAuditLog,
    ExportManager,
    RecordStatus,
    SyntheticBackupManager,
    SyntheticRecord,
)
from research_project.synthetic_edc_query import (
    CorrectionManager,
    DeviationRegistry,
    DeviationSeverity,
    EDCQuery,
    QueryLifecycleManager,
    QueryStatus,
)


# ── Fixtures ────────────────────────────────────────────────────────────────

def _make_record(record_id: str = "rec-001", status: RecordStatus = RecordStatus.ACTIVE) -> SyntheticRecord:
    r = SyntheticRecord(
        record_id=record_id,
        subject_id=f"subj-{record_id}",
        crf_version_id="v1.0",
        data={"age": 45, "sex": "M", "sbp": 120.0},
    )
    r.status = status
    return r

def _make_audit_log() -> EDCAuditLog:
    return EDCAuditLog()

TS = "2026-06-28T00:00:00Z"


# ── SyntheticRecord ─────────────────────────────────────────────────────────

class TestSyntheticRecord:
    def test_valid_record_created(self):
        r = _make_record()
        assert r.record_id == "rec-001"
        assert r.attribution_mode == "SYNTHETIC"

    def test_empty_record_id_raises(self):
        with pytest.raises(ValueError, match="record_id"):
            SyntheticRecord("", "subj", "v1", {})

    def test_empty_subject_id_raises(self):
        with pytest.raises(ValueError, match="subject_id"):
            SyntheticRecord("r1", "", "v1", {})

    def test_empty_crf_version_id_raises(self):
        with pytest.raises(ValueError, match="crf_version_id"):
            SyntheticRecord("r1", "s1", "", {})

    def test_default_status_is_draft(self):
        r = SyntheticRecord("r1", "s1", "v1", {})
        assert r.status == RecordStatus.DRAFT

    def test_disclaimer_present(self):
        r = _make_record()
        assert r.disclaimer
        assert len(r.disclaimer) > 0


# ── EDCAuditLog ─────────────────────────────────────────────────────────────

class TestEDCAuditLog:
    def test_log_creates_entry(self):
        log = _make_audit_log()
        entry = log.log("DATA_FREEZE", "rec-001", "actor", TS, "test")
        assert isinstance(entry, AuditEntry)
        assert entry.event_type == "DATA_FREEZE"

    def test_entries_for_record_filters_correctly(self):
        log = _make_audit_log()
        log.log("FREEZE", "rec-A", "actor", TS, "")
        log.log("LOCK", "rec-B", "actor", TS, "")
        log.log("EXPORT", "rec-A", "actor", TS, "")
        entries = log.entries_for_record("rec-A")
        assert len(entries) == 2
        assert all(e.record_id == "rec-A" for e in entries)

    def test_entry_count(self):
        log = _make_audit_log()
        log.log("E1", "r1", "a", TS, "d1")
        log.log("E2", "r2", "a", TS, "d2")
        assert log.entry_count == 2

    def test_all_entries_returns_all(self):
        log = _make_audit_log()
        log.log("X", "r1", "a", TS, "")
        log.log("Y", "r2", "a", TS, "")
        assert len(log.all_entries()) == 2


# ── DataFreezeManager ───────────────────────────────────────────────────────

class TestDataFreezeManager:
    def test_freeze_sets_status(self):
        log = _make_audit_log()
        mgr = DataFreezeManager(log)
        r = _make_record()
        mgr.freeze(r, "actor", TS, "end of enrollment")
        assert r.status == RecordStatus.FROZEN
        assert mgr.is_frozen(r.record_id)

    def test_freeze_creates_audit_entry(self):
        log = _make_audit_log()
        mgr = DataFreezeManager(log)
        r = _make_record()
        mgr.freeze(r, "actor", TS, "reason")
        assert log.entry_count == 1

    def test_double_freeze_raises(self):
        log = _make_audit_log()
        mgr = DataFreezeManager(log)
        r = _make_record()
        mgr.freeze(r, "actor", TS, "reason")
        with pytest.raises(ValueError):
            mgr.freeze(r, "actor", TS, "again")

    def test_unfreeze_sets_active(self):
        log = _make_audit_log()
        mgr = DataFreezeManager(log)
        r = _make_record()
        mgr.freeze(r, "actor", TS, "reason")
        mgr.unfreeze(r, "actor", TS, "protocol amendment")
        assert r.status == RecordStatus.ACTIVE
        assert not mgr.is_frozen(r.record_id)

    def test_freeze_locked_record_raises(self):
        log = _make_audit_log()
        mgr = DataFreezeManager(log)
        r = _make_record(status=RecordStatus.LOCKED)
        with pytest.raises(PermissionError):
            mgr.freeze(r, "actor", TS, "reason")


# ── DataLockManager ─────────────────────────────────────────────────────────

class TestDataLockManager:
    def test_lock_sets_status(self):
        log = _make_audit_log()
        mgr = DataLockManager(log)
        r = _make_record()
        mgr.lock(r, "actor", TS, "IRB_AUTH_001")
        assert r.status == RecordStatus.LOCKED
        assert mgr.is_locked(r.record_id)

    def test_lock_requires_authority(self):
        log = _make_audit_log()
        mgr = DataLockManager(log)
        r = _make_record()
        with pytest.raises(ValueError, match="authority"):
            mgr.lock(r, "actor", TS, "")

    def test_double_lock_raises(self):
        log = _make_audit_log()
        mgr = DataLockManager(log)
        r = _make_record()
        mgr.lock(r, "actor", TS, "AUTH")
        with pytest.raises(ValueError):
            mgr.lock(r, "actor", TS, "AUTH2")

    def test_attempt_modify_locked_raises(self):
        log = _make_audit_log()
        mgr = DataLockManager(log)
        r = _make_record()
        mgr.lock(r, "actor", TS, "AUTH")
        with pytest.raises(PermissionError):
            mgr.attempt_modify_locked(r.record_id)

    def test_unlocked_record_is_not_locked(self):
        log = _make_audit_log()
        mgr = DataLockManager(log)
        assert not mgr.is_locked("never-locked-record")


# ── ExportManager ───────────────────────────────────────────────────────────

class TestExportManager:
    def test_create_manifest_for_locked_records(self):
        log = _make_audit_log()
        mgr = ExportManager(log)
        r1 = _make_record("rec-001", RecordStatus.LOCKED)
        r2 = _make_record("rec-002", RecordStatus.LOCKED)
        manifest = mgr.create_manifest([r1, r2], "actor", TS)
        assert manifest.record_count == 2
        assert set(manifest.record_ids) == {"rec-001", "rec-002"}
        assert manifest.content_hash
        assert manifest.is_synthetic is True

    def test_export_non_locked_record_raises(self):
        log = _make_audit_log()
        mgr = ExportManager(log)
        r = _make_record("rec-001", RecordStatus.ACTIVE)
        with pytest.raises(PermissionError):
            mgr.create_manifest([r], "actor", TS)

    def test_export_creates_audit_entry(self):
        log = _make_audit_log()
        mgr = ExportManager(log)
        r = _make_record("rec-001", RecordStatus.LOCKED)
        mgr.create_manifest([r], "actor", TS)
        assert log.entry_count == 1

    def test_manifest_disclaimer_present(self):
        log = _make_audit_log()
        mgr = ExportManager(log)
        r = _make_record("rec-001", RecordStatus.LOCKED)
        manifest = mgr.create_manifest([r], "actor", TS)
        assert manifest.disclaimer


# ── SyntheticBackupManager ──────────────────────────────────────────────────

class TestSyntheticBackupManager:
    def test_backup_returns_receipt(self):
        mgr = SyntheticBackupManager()
        records = [_make_record("r1"), _make_record("r2")]
        receipt = mgr.backup(records, TS)
        assert isinstance(receipt, BackupReceipt)
        assert receipt.record_count == 2
        assert receipt.is_synthetic is True

    def test_restore_returns_stored_data(self):
        mgr = SyntheticBackupManager()
        records = [_make_record("r1")]
        receipt = mgr.backup(records, TS)
        restored = mgr.restore(receipt.backup_id)
        assert "r1" in restored
        assert restored["r1"]["age"] == 45

    def test_restore_unknown_backup_raises(self):
        mgr = SyntheticBackupManager()
        with pytest.raises(KeyError):
            mgr.restore("nonexistent-backup-id")

    def test_verify_correct_hash_returns_true(self):
        mgr = SyntheticBackupManager()
        records = [_make_record("r1")]
        receipt = mgr.backup(records, TS)
        assert mgr.verify(receipt.backup_id, receipt.content_hash) is True

    def test_verify_wrong_hash_returns_false(self):
        mgr = SyntheticBackupManager()
        records = [_make_record("r1")]
        receipt = mgr.backup(records, TS)
        assert mgr.verify(receipt.backup_id, "wrong_hash") is False

    def test_not_implemented_constant(self):
        assert SyntheticBackupManager.NOT_IMPLEMENTED


# ── QueryLifecycleManager ───────────────────────────────────────────────────

class TestQueryLifecycleManager:
    def test_raise_query(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("rec-001", "sbp", "Value seems high", "monitor", TS)
        assert isinstance(q, EDCQuery)
        assert q.status == QueryStatus.OPEN

    def test_answer_open_query(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("rec-001", "sbp", "msg", "monitor", TS)
        mgr.answer_query(q.query_id, "Confirmed correct", "site_coordinator", TS)
        assert q.status == QueryStatus.ANSWERED
        assert q.answer == "Confirmed correct"

    def test_answer_non_open_query_raises(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("r1", "f1", "msg", "m", TS)
        mgr.answer_query(q.query_id, "ans", "coord", TS)
        with pytest.raises(ValueError):
            mgr.answer_query(q.query_id, "re-answer", "coord", TS)

    def test_close_answered_query(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("r1", "f1", "msg", "m", TS)
        mgr.answer_query(q.query_id, "ans", "coord", TS)
        mgr.close_query(q.query_id, "dm", TS)
        assert q.status == QueryStatus.CLOSED

    def test_close_without_answer_raises(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("r1", "f1", "msg", "m", TS)
        with pytest.raises(ValueError):
            mgr.close_query(q.query_id, "dm", TS)

    def test_cancel_open_query(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("r1", "f1", "msg", "m", TS)
        mgr.cancel_query(q.query_id, "dm", "Entered wrong field")
        assert q.status == QueryStatus.CANCELLED

    def test_cancel_closed_query_raises(self):
        mgr = QueryLifecycleManager()
        q = mgr.raise_query("r1", "f1", "msg", "m", TS)
        mgr.answer_query(q.query_id, "ans", "coord", TS)
        mgr.close_query(q.query_id, "dm", TS)
        with pytest.raises(ValueError):
            mgr.cancel_query(q.query_id, "dm", "too late")

    def test_open_queries_filtered(self):
        mgr = QueryLifecycleManager()
        q1 = mgr.raise_query("r1", "f1", "msg", "m", TS)
        q2 = mgr.raise_query("r2", "f1", "msg", "m", TS)
        mgr.answer_query(q1.query_id, "ans", "c", TS)
        mgr.close_query(q1.query_id, "dm", TS)
        open_qs = mgr.open_queries()
        assert len(open_qs) == 1
        assert open_qs[0].query_id == q2.query_id


# ── CorrectionManager ───────────────────────────────────────────────────────

class TestCorrectionManager:
    def test_record_correction(self):
        mgr = CorrectionManager()
        c = mgr.record_correction("r1", "sbp", 120, 125, "Transcription error", "coord", TS)
        assert c.old_value == 120
        assert c.new_value == 125
        assert c.reason == "Transcription error"

    def test_correction_without_reason_raises(self):
        mgr = CorrectionManager()
        with pytest.raises(ValueError, match="reason"):
            mgr.record_correction("r1", "sbp", 120, 125, "", "coord", TS)

    def test_corrections_for_record(self):
        mgr = CorrectionManager()
        mgr.record_correction("r1", "sbp", 120, 125, "reason", "a", TS)
        mgr.record_correction("r2", "age", 40, 41, "reason", "a", TS)
        assert len(mgr.corrections_for_record("r1")) == 1

    def test_corrections_for_field(self):
        mgr = CorrectionManager()
        mgr.record_correction("r1", "sbp", 120, 125, "r1", "a", TS)
        mgr.record_correction("r1", "age", 40, 41, "r2", "a", TS)
        assert len(mgr.corrections_for_field("r1", "sbp")) == 1


# ── DeviationRegistry ───────────────────────────────────────────────────────

class TestDeviationRegistry:
    def test_record_deviation(self):
        reg = DeviationRegistry()
        d = reg.record_deviation(
            "r1", "Missed visit window", DeviationSeverity.MINOR,
            "coord", TS, "No impact", "Document in file"
        )
        assert d.severity == DeviationSeverity.MINOR
        assert reg.total_deviations == 1

    def test_major_or_critical_filter(self):
        reg = DeviationRegistry()
        reg.record_deviation("r1", "Minor", DeviationSeverity.MINOR, "c", TS, "n", "d")
        reg.record_deviation("r2", "Major", DeviationSeverity.MAJOR, "c", TS, "n", "d")
        reg.record_deviation("r3", "Critical", DeviationSeverity.CRITICAL, "c", TS, "n", "d")
        mc = reg.major_or_critical()
        assert len(mc) == 2

    def test_deviation_without_corrective_action_raises(self):
        reg = DeviationRegistry()
        with pytest.raises(ValueError, match="corrective_action"):
            from research_project.synthetic_edc_query import ProtocolDeviation
            ProtocolDeviation("d1", "r1", "desc", DeviationSeverity.MINOR, "c", TS, "impact", "")
