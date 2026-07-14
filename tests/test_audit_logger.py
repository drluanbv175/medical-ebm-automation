"""
Tests cho AuditLogger — Phase 3 Offline Controlled-System.
Không có API call, không PII, hoàn toàn deterministic.
"""

from runtime.audit_logger import AuditLogger
from runtime.schemas import AuditEvent, PolicyDecisionEnum, RuntimeTypeEnum


def _make_event(
    logger: AuditLogger,
    policy_decision: PolicyDecisionEnum = PolicyDecisionEnum.PASS,
    pii_verdict: str = "CLEAN",
    notes: str = "",
) -> AuditEvent:
    return AuditEvent(
        run_id=logger.run_id,
        workflow_id="WF-TEST-001",
        agent_id="co-mau-nghien-cuu",
        fixture_id="FX-001",
        runtime_type=RuntimeTypeEnum.MOCK,
        state_before="DRAFT",
        state_after="METHOD_REVIEW",
        policy_decision=policy_decision,
        approval_reference=None,
        output_schema_verdict="PASS",
        pii_verdict=pii_verdict,
        timestamp_utc="2026-06-21T00:00:00+00:00",
        notes=notes,
    )


class TestAuditLoggerBasic:
    """Ghi và đọc audit event."""

    def test_log_and_count(self):
        logger = AuditLogger()
        event = _make_event(logger)
        logger.log_event(event)
        assert logger.count() == 1

    def test_get_events(self):
        logger = AuditLogger()
        e1 = _make_event(logger)
        e2 = _make_event(logger, policy_decision=PolicyDecisionEnum.BLOCK)
        logger.log_event(e1)
        logger.log_event(e2)
        events = logger.get_events()
        assert len(events) == 2

    def test_get_events_by_decision(self):
        logger = AuditLogger()
        logger.log_event(_make_event(logger, PolicyDecisionEnum.PASS))
        logger.log_event(_make_event(logger, PolicyDecisionEnum.BLOCK))
        logger.log_event(_make_event(logger, PolicyDecisionEnum.BLOCK))
        blocked = logger.get_events_by_decision(PolicyDecisionEnum.BLOCK)
        assert len(blocked) == 2


class TestAuditLoggerPiiScrub:
    """PII trong notes bị scrub trước khi log."""

    def test_phone_scrubbed_from_notes(self):
        logger = AuditLogger()
        # Số điện thoại VN thật trong notes
        event = _make_event(logger, notes="Bệnh nhân gọi 0912345678 báo triệu chứng")
        logger.log_event(event)
        logged = logger.get_events()[0]
        assert "0912345678" not in logged.notes
        assert "[REDACTED]" in logged.notes

    def test_clean_notes_not_modified(self):
        logger = AuditLogger()
        event = _make_event(logger, notes="Policy decision PASS for co-mau agent")
        logger.log_event(event)
        logged = logger.get_events()[0]
        assert logged.notes == "Policy decision PASS for co-mau agent"

    def test_pii_blocked_event_detected(self):
        logger = AuditLogger()
        event = _make_event(logger, pii_verdict="BLOCKED")
        logger.log_event(event)
        assert logger.has_pii_blocked_event()

    def test_no_pii_blocked_initially(self):
        logger = AuditLogger()
        event = _make_event(logger, pii_verdict="CLEAN")
        logger.log_event(event)
        assert not logger.has_pii_blocked_event()


class TestAuditLoggerConvenienceMethod:
    """log_gate_decision helper method."""

    def test_log_gate_decision_creates_event(self):
        logger = AuditLogger()
        event = logger.log_gate_decision(
            workflow_id="WF-001",
            agent_id="phan-tich-thong-ke",
            fixture_id="FX-002",
            runtime_type=RuntimeTypeEnum.MOCK,
            state_before="SAP_LOCKED",
            state_after="ANALYSIS_ALLOWED",
            policy_decision=PolicyDecisionEnum.BLOCK,
            pii_verdict="CLEAN",
            output_schema_verdict="PASS",
            notes="SAP bypass attempt blocked",
        )
        assert logger.count() == 1
        assert event.policy_decision == PolicyDecisionEnum.BLOCK


class TestAuditLoggerExport:
    """Export JSON và text không có PII, không có raw prompt."""

    def test_export_json_structure(self):
        import json
        logger = AuditLogger(run_id="run-test-001")
        logger.log_event(_make_event(logger))
        payload = logger.export_json()
        data = json.loads(payload)
        assert data["run_id"] == "run-test-001"
        assert data["event_count"] == 1
        assert "events" in data
        event_dict = data["events"][0]
        # Không có raw_prompt, raw_response, raw_exception
        assert "raw_prompt" not in event_dict
        assert "raw_response" not in event_dict
        assert "raw_exception" not in event_dict

    def test_export_text_readable(self):
        logger = AuditLogger(run_id="run-text-001")
        logger.log_event(_make_event(logger, PolicyDecisionEnum.PASS))
        text = logger.export_text()
        assert "AUDIT LOG" in text
        assert "PASS" in text

    def test_run_id_format(self):
        logger = AuditLogger()
        assert logger.run_id.startswith("run-")
