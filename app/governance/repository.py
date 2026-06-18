"""Repository persistence cho governance V7."""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict, Mapping, Optional
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.audit_logger import scrub_pii
from app.core.run_packet import RunPacket
from app.core.run_state_machine import RunState, transition
from app.evidence.citation_verification import CitationVerificationResult
from app.models.governance_v7 import (
    ApprovalRecord,
    AuditEventRecord,
    CitationVerificationRecord,
    EvidenceRecordV2,
    ExportManifestRecord,
    FeatureFlagAuditRecord,
    RunPacketRecord,
)


def _stable_hash(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


class GovernanceRepository:
    """Repository tối thiểu, dễ thay DB vendor vì chỉ phụ thuộc SQLAlchemy session."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def save_run_packet(self, packet: RunPacket, state: str = "queued") -> RunPacketRecord:
        record = RunPacketRecord(
            run_id=packet.run_id,
            request_id=packet.request_id,
            lane=packet.lane.value,
            objective=packet.objective,
            risk_level=packet.risk_level.value,
            input_completeness=packet.input_completeness.value,
            pii_status=packet.pii_status.value,
            approval_status=packet.approval_status.value,
            state=state,
            status=state,
            trace_ids=list(packet.trace_ids),
            feature_flags=dict(packet.feature_flags),
            metadata_json=dict(packet.metadata),
        )
        self.session.add(record)
        self.audit(packet.run_id, "run_packet_saved", "system", {"state": state})
        return record

    def create_approval(self, run_id: str, item_type: str, summary: str) -> ApprovalRecord:
        record = ApprovalRecord(
            approval_id=f"apr_{uuid4().hex}",
            run_id=run_id,
            item_type=item_type,
            summary=summary,
            status="pending",
        )
        self.session.add(record)
        self.audit(run_id, "approval_created", "system", {"approval_id": record.approval_id})
        return record

    def audit(
        self,
        run_id: str,
        event_type: str,
        actor: str,
        payload: Optional[Mapping[str, Any]] = None,
    ) -> AuditEventRecord:
        record = AuditEventRecord(
            event_id=f"audit_{uuid4().hex}",
            run_id=run_id,
            event_type=event_type,
            actor=actor,
            created_by=actor,
            payload_json=scrub_pii(dict(payload or {})),
        )
        self.session.add(record)
        return record

    def save_export_manifest(
        self,
        *,
        system_version: str,
        environment: str,
        contains_pii: bool,
        safe_to_upload: bool,
        files: Mapping[str, Any],
        status: str = "draft",
    ) -> ExportManifestRecord:
        payload: Dict[str, Any] = {
            "system_version": system_version,
            "environment": environment,
            "contains_pii": contains_pii,
            "safe_to_upload": safe_to_upload,
            "files": dict(files),
        }
        record = ExportManifestRecord(
            manifest_id=f"manifest_{uuid4().hex}",
            system_version=system_version,
            environment=environment,
            contains_pii=contains_pii,
            safe_to_upload=safe_to_upload,
            files_json=dict(files),
            sha256=_stable_hash(payload),
            status=status,
        )
        self.session.add(record)
        self.audit("export", "export_manifest_saved", "system", {"manifest_id": record.manifest_id})
        return record

    def record_feature_flag_change(
        self,
        flag_name: str,
        old_value: bool,
        new_value: bool,
        changed_by: str,
        reason: str,
    ) -> FeatureFlagAuditRecord:
        record = FeatureFlagAuditRecord(
            flag_name=flag_name,
            old_value=old_value,
            new_value=new_value,
            changed_by=changed_by,
            reason=reason,
        )
        self.session.add(record)
        self.audit("feature_flags", "feature_flag_changed", changed_by, {
            "flag_name": flag_name,
            "old_value": old_value,
            "new_value": new_value,
        })
        return record

    def transition_run_state(
        self,
        run_id: str,
        target_state: RunState,
        *,
        reason: str,
        actor: str = "system",
    ) -> RunPacketRecord:
        record = self.session.execute(
            select(RunPacketRecord).where(RunPacketRecord.run_id == run_id)
        ).scalar_one()
        state_change = transition(RunState(record.state), target_state, reason)
        record.state = state_change.current.value
        record.status = state_change.current.value
        record.version += 1
        self.audit(run_id, "run_state_transition", actor, {
            "previous": state_change.previous.value,
            "current": state_change.current.value,
            "reason": state_change.reason,
        })
        return record

    def record_rollback(self, run_id: str, *, reason: str, actor: str = "system") -> AuditEventRecord:
        return self.audit(run_id, "rollback_event", actor, {"reason": reason})

    def mark_evidence_superseded(
        self,
        evidence_id: str,
        *,
        replacement_evidence_id: str,
        reason: str,
        actor: str = "system",
    ) -> EvidenceRecordV2:
        record = self.session.execute(
            select(EvidenceRecordV2).where(EvidenceRecordV2.evidence_id == evidence_id)
        ).scalar_one()
        history = list(record.history_json or [])
        history.append({
            "event": "superseded",
            "replacement_evidence_id": replacement_evidence_id,
            "reason": reason,
            "actor": actor,
        })
        record.lifecycle_status = "superseded"
        record.status = "superseded"
        record.history_json = history
        record.version += 1
        self.audit(record.run_id or "evidence", "evidence_superseded", actor, {
            "evidence_id": evidence_id,
            "replacement_evidence_id": replacement_evidence_id,
            "reason": reason,
        })
        return record

    def save_citation_verification(
        self,
        *,
        result: CitationVerificationResult,
        traceability_id: str,
        run_id: Optional[str] = None,
        evidence_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        actor: str = "system",
    ) -> CitationVerificationRecord:
        source = asdict(result.source_metadata)
        record = CitationVerificationRecord(
            verification_id=f"cv_{uuid4().hex}",
            run_id=run_id,
            evidence_id=evidence_id,
            claim_id=claim_id,
            traceability_id=traceability_id,
            status=result.status.value,
            verification_method=result.verification_method,
            last_verified_date=result.last_verified_date,
            checks_json=dict(result.checks),
            reasons_json=list(result.reasons),
            source_metadata_json=source,
            created_by=actor,
        )
        self.session.add(record)
        self.audit(run_id or "citation_verification", "citation_verification_saved", actor, {
            "verification_id": record.verification_id,
            "traceability_id": traceability_id,
            "status": record.status,
        })
        return record
