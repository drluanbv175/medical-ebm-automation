from datetime import date

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import sessionmaker

from app.core.run_packet import Lane, new_run_packet
from app.core.run_state_machine import InvalidTransition, RunState
from app.evidence.citation_verification import (
    CitationVerificationStatus,
    CitationVerifier,
    SourceMetadata,
    StaticSourceLookupAdapter,
)
from app.governance.migrations import GOVERNANCE_TABLES, build_governance_migration_plan, create_governance_schema
from app.governance.repository import GovernanceRepository
from app.models.governance_v7 import AuditEventRecord, EvidenceRecordV2


def test_governance_migration_plan_is_additive_and_non_destructive():
    engine = create_engine("sqlite:///:memory:", future=True)
    plan = build_governance_migration_plan(engine)

    assert plan.migration_id.startswith("v7_phase_2a_governance")
    assert set(plan.missing_tables) == set(GOVERNANCE_TABLES)
    assert plan.ready_for_dry_run
    assert not plan.destructive
    assert all(statement.startswith("CREATE TABLE") for statement in plan.sql)


def test_governance_tables_have_required_minimum_fields_and_no_pii_columns():
    engine = create_engine("sqlite:///:memory:", future=True)
    create_governance_schema(engine)
    inspector = inspect(engine)
    required = {"id", "version", "created_at", "updated_at", "created_by", "status", "environment"}
    forbidden = {"patient_name", "dob", "phone", "email", "mrn", "address"}

    for table in GOVERNANCE_TABLES:
        columns = {column["name"] for column in inspector.get_columns(table)}
        assert required.issubset(columns), table
        assert not (forbidden & columns), table
    assert "citation_verification_records" in inspector.get_table_names()


def test_governance_repository_persists_run_approval_audit_and_export_manifest():
    engine = create_engine("sqlite:///:memory:", future=True)
    create_governance_schema(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    packet = new_run_packet(Lane.CLINICAL, "Shadow mode synthetic run")

    with session_factory() as session:
        repo = GovernanceRepository(session)
        run_record = repo.save_run_packet(packet)
        approval = repo.create_approval(packet.run_id, "clinical_draft", "Draft only")
        audit = repo.audit(packet.run_id, "pii_test", "assistant", {"note": "dob: 01/01/2000"})
        manifest = repo.save_export_manifest(
            system_version="EBM_OS_V7_PHASE_2A",
            environment="review",
            contains_pii=False,
            safe_to_upload=True,
            files={"safe.md": {"sha256": "abc", "allowed": True}},
        )
        session.commit()

        assert run_record.run_id == packet.run_id
        assert approval.status == "pending"
        assert "[REDACTED_PII]" in audit.payload_json["note"]
        assert manifest.sha256


def test_governance_repository_validates_state_transitions_and_records_rollback():
    engine = create_engine("sqlite:///:memory:", future=True)
    create_governance_schema(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)
    packet = new_run_packet(Lane.CLINICAL, "Shadow mode transition")

    with session_factory() as session:
        repo = GovernanceRepository(session)
        run_record = repo.save_run_packet(packet)
        repo.transition_run_state(packet.run_id, RunState.RUNNING, reason="start shadow run", actor="assistant")
        rollback = repo.record_rollback(packet.run_id, reason="dry-run rollback", actor="assistant")
        session.commit()

        assert run_record.state == "running"
        assert run_record.version == 2
        assert rollback.event_type == "rollback_event"

    with session_factory() as session:
        repo = GovernanceRepository(session)
        with pytest.raises(InvalidTransition):
            repo.transition_run_state(packet.run_id, RunState.RELEASED, reason="illegal release", actor="assistant")


def test_governance_repository_keeps_superseded_evidence_history_and_citation_records():
    engine = create_engine("sqlite:///:memory:", future=True)
    create_governance_schema(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False, future=True)

    source = SourceMetadata(
        found=True,
        title="Correct Trial Title",
        authors_or_organization="AHA",
        year_or_version="2026-01-01",
        source_type="guideline",
        population="Adults",
    )
    verifier = CitationVerifier(
        StaticSourceLookupAdapter({"doi:10.1000/test": source}),
        today=date(2026, 6, 18),
    )
    result = verifier.verify({
        "doi": "10.1000/test",
        "title": "Correct Trial Title",
        "source": "AHA",
        "year_or_version": "2026",
        "source_type": "guideline",
        "population": "Adults",
        "claim_location": "section 2",
    })

    with session_factory() as session:
        session.add(EvidenceRecordV2(
            evidence_id="ev_old",
            traceability_id="doi:10.1000/test",
            title="Correct Trial Title",
            source="AHA",
            evidence_type="guideline",
            identifiers_json={"doi": "10.1000/test"},
        ))
        repo = GovernanceRepository(session)
        citation = repo.save_citation_verification(
            result=result,
            traceability_id="doi:10.1000/test",
            evidence_id="ev_old",
            claim_id="claim_1",
            actor="assistant",
        )
        superseded = repo.mark_evidence_superseded(
            "ev_old",
            replacement_evidence_id="ev_new",
            reason="newer source",
            actor="assistant",
        )
        session.commit()

        audits = session.execute(select(AuditEventRecord.event_type)).scalars().all()
        assert result.status is CitationVerificationStatus.VERIFIED
        assert citation.status == "VERIFIED"
        assert superseded.status == "superseded"
        assert superseded.history_json[0]["replacement_evidence_id"] == "ev_new"
        assert "citation_verification_saved" in audits
        assert "evidence_superseded" in audits
