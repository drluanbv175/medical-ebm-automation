"""
AuditLogger — Ghi audit trail cho mọi workflow event.
Không log PII, không log raw prompt/response, không log raw exception.
"""

from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from typing import Optional
from .schemas import AuditEvent, PolicyDecisionEnum, RuntimeTypeEnum
from .data_boundary import DataBoundary

_boundary = DataBoundary()

# Các field tuyệt đối không được log
_FORBIDDEN_LOG_FIELDS = {
    "raw_prompt", "raw_response", "raw_exception", "patient_data",
    "raw_input", "api_key", "secret", "password",
}


class AuditLogger:
    """
    Append-only audit log cho toàn bộ workflow.
    PII được scrub trước khi ghi.
    """

    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or self._new_run_id()
        self._events: list[AuditEvent] = []

    # ── Write ─────────────────────────────────────────────────────────────────

    def log_event(self, event: AuditEvent) -> None:
        """Ghi một AuditEvent. PII trong notes được scrub."""
        # Scrub PII trong notes
        if event.notes:
            event = self._scrub_event(event)
        self._events.append(event)

    def log_gate_decision(
        self,
        *,
        workflow_id: str,
        agent_id: str,
        fixture_id: str,
        runtime_type: RuntimeTypeEnum,
        state_before: str,
        state_after: str,
        policy_decision: PolicyDecisionEnum,
        approval_reference: Optional[str] = None,
        output_schema_verdict: str = "NOT_CHECKED",
        pii_verdict: str = "NOT_CHECKED",
        notes: str = "",
        agent_source_hash: Optional[str] = None,
    ) -> AuditEvent:
        """Convenience method: tạo và log AuditEvent từ parameters.

        V4.2.1 (GAP-004): truyền ``agent_source_hash`` cho mọi audit event của
        một dispatch (PASS/BLOCK) để khép kín truy nguyên agent↔hash↔quyết định.
        """
        event = AuditEvent(
            run_id=self.run_id,
            workflow_id=workflow_id,
            agent_id=agent_id,
            fixture_id=fixture_id,
            runtime_type=runtime_type,
            state_before=state_before,
            state_after=state_after,
            policy_decision=policy_decision,
            approval_reference=approval_reference,
            output_schema_verdict=output_schema_verdict,
            pii_verdict=pii_verdict,
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
            notes=notes,
            agent_source_hash=agent_source_hash,
        )
        self.log_event(event)
        return event

    # ── Read ──────────────────────────────────────────────────────────────────

    def get_events(self) -> list[AuditEvent]:
        return list(self._events)

    def count(self) -> int:
        return len(self._events)

    def get_events_by_decision(self, decision: PolicyDecisionEnum) -> list[AuditEvent]:
        return [e for e in self._events if e.policy_decision == decision]

    def has_pii_blocked_event(self) -> bool:
        return any(
            e.pii_verdict == "BLOCKED" for e in self._events
        )

    def dispatch_events_missing_hash(self) -> list[AuditEvent]:
        """V4.2.1 (GAP-004): trả các event của một dispatch (runtime đã chạy)
        nhưng THIẾU agent_source_hash. Dùng để fail-closed/kiểm toán.

        Event được coi là 'dispatch' khi runtime_type là MOCK hoặc CLAUDE_API.
        """
        from .schemas import RuntimeTypeEnum as _RT
        dispatch_runtimes = {_RT.MOCK, _RT.CLAUDE_API}
        return [
            e for e in self._events
            if e.runtime_type in dispatch_runtimes and not e.agent_source_hash
        ]

    def all_dispatch_events_hashed(self) -> bool:
        """True khi mọi audit event của dispatch đều có agent_source_hash."""
        return not self.dispatch_events_missing_hash()

    # ── Export ────────────────────────────────────────────────────────────────

    def export_json(self, path: Optional[str] = None) -> str:
        """Xuất log thành JSON. Không có PII."""
        data = {
            "run_id": self.run_id,
            "event_count": len(self._events),
            "events": [self._event_to_dict(e) for e in self._events],
        }
        payload = json.dumps(data, indent=2, ensure_ascii=False)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
        return payload

    def export_text(self, path: Optional[str] = None) -> str:
        """Xuất log thành text dễ đọc."""
        lines = [f"=== AUDIT LOG run_id={self.run_id} ==="]
        for i, e in enumerate(self._events, 1):
            lines.append(
                f"[{i:03d}] {e.timestamp_utc} | {e.agent_id} | "
                f"{e.policy_decision.value} | pii={e.pii_verdict} | "
                f"schema={e.output_schema_verdict}"
            )
            if e.notes:
                lines.append(f"      notes: {e.notes}")
        payload = "\n".join(lines)
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
        return payload

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _scrub_event(self, event: AuditEvent) -> AuditEvent:
        """Scrub PII trong notes. Trả AuditEvent mới."""
        scrubbed_notes = _boundary.scrub_pii(event.notes) if event.notes else ""
        return AuditEvent(
            run_id=event.run_id,
            workflow_id=event.workflow_id,
            agent_id=event.agent_id,
            fixture_id=event.fixture_id,
            runtime_type=event.runtime_type,
            state_before=event.state_before,
            state_after=event.state_after,
            policy_decision=event.policy_decision,
            approval_reference=event.approval_reference,
            output_schema_verdict=event.output_schema_verdict,
            pii_verdict=event.pii_verdict,
            timestamp_utc=event.timestamp_utc,
            notes=scrubbed_notes,
            agent_source_hash=event.agent_source_hash,
        )

    @staticmethod
    def _event_to_dict(event: AuditEvent) -> dict:
        return {
            "run_id": event.run_id,
            "workflow_id": event.workflow_id,
            "agent_id": event.agent_id,
            "fixture_id": event.fixture_id,
            "runtime_type": event.runtime_type.value,
            "state_before": event.state_before,
            "state_after": event.state_after,
            "policy_decision": event.policy_decision.value,
            "approval_reference": event.approval_reference,
            "output_schema_verdict": event.output_schema_verdict,
            "pii_verdict": event.pii_verdict,
            "timestamp_utc": event.timestamp_utc,
            "notes": event.notes,
            "agent_source_hash": event.agent_source_hash,
        }

    @staticmethod
    def _new_run_id() -> str:
        import uuid
        return f"run-{uuid.uuid4().hex[:12]}"
