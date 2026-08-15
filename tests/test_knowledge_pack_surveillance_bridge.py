"""Test bridge surveillance -> knowledge pack update queue."""
from __future__ import annotations

import json

from app.database import session_scope
from app.models import EvidenceItem, PipelineRun
from app.services.knowledge_pack_surveillance import (
    build_knowledge_pack_update_queue,
    write_knowledge_pack_update_queue,
)
from tools import gen_morning_brief


def _cleanup_pytest_surveillance_rows() -> None:
    with session_scope() as session:
        session.query(EvidenceItem).filter(EvidenceItem.source == "pytest_surveillance").delete()


def _seed_run_with_items() -> int:
    with session_scope() as session:
        run = PipelineRun(mode="live", status="ok", total_fetched=2, new_items=2)
        session.add(run)
        session.flush()
        run_id = run.id

        session.add(EvidenceItem(
            source="pytest_surveillance",
            source_type="guideline",
            title="ADA 2026 update for type 2 diabetes: SGLT2 and GLP-1 recommendations",
            journal_or_organization="ADA",
            publication_date="2026",
            study_type="guideline",
            clinical_area="Nội tiết - Chuyển hóa",
            abstract="Type 2 diabetes glycemic management and cardiovascular risk update.",
            doi="10.1000/pytest-diabetes-guideline",
            practice_change_score=88,
            reliability_tier="A",
            is_actionable=True,
            classification="actionable",
            is_primary_record=True,
            is_mock=False,
            first_seen_run_id=run_id,
        ))
        session.add(EvidenceItem(
            source="pytest_surveillance",
            source_type="guideline",
            title="Mock hypertension guideline should not enter review queue",
            study_type="guideline",
            clinical_area="Tim mạch",
            practice_change_score=99,
            is_actionable=True,
            classification="actionable",
            is_primary_record=True,
            is_mock=True,
            first_seen_run_id=run_id,
        ))
        return run_id


def test_surveillance_bridge_maps_new_guideline_to_knowledge_pack():
    _cleanup_pytest_surveillance_rows()
    try:
        _seed_run_with_items()

        payload = build_knowledge_pack_update_queue(days=7)

        diabetes_items = [
            item for item in payload["items"]
            if item["pack_id"] == "diabetes_t2_adult_outpatient"
            and "ADA 2026" in item["title"]
        ]
        assert len(diabetes_items) == 1
        item = diabetes_items[0]
        assert item["priority"] == "HIGH"
        assert item["review_status"] == "pending_physician_review"
        assert item["human_required"] is True
        assert item["auto_apply"] is False
        assert "guideline_update" in item["reason_codes"]
        assert "actionable_practice_change" in item["reason_codes"]
        assert item["source_refs"] == ["DOI:10.1000/pytest-diabetes-guideline"]
        assert not any("Mock hypertension" in row["title"] for row in payload["items"])
    finally:
        _cleanup_pytest_surveillance_rows()


def test_write_knowledge_pack_update_queue_outputs_json(tmp_path):
    _cleanup_pytest_surveillance_rows()
    try:
        _seed_run_with_items()
        output = tmp_path / "queue.json"

        path = write_knowledge_pack_update_queue(output_path=output)

        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["kind"] == "knowledge_pack_update_queue"
        assert payload["review_policy"] == "review_only_no_auto_apply"
        assert payload["total_items"] >= 1
    finally:
        _cleanup_pytest_surveillance_rows()


def test_morning_brief_surveillance_section_reads_pack_update_queue(tmp_path, monkeypatch):
    monkeypatch.setattr(gen_morning_brief, "RESULTS_DIR", tmp_path)
    queue_path = tmp_path / "knowledge_pack_update_queue.json"
    queue_path.write_text(json.dumps({
        "items": [
            {
                "priority": "HIGH",
                "pack_id": "diabetes_t2_adult_outpatient",
                "pack_label": "Đái tháo đường type 2",
                "title": "ADA update",
            },
            {
                "priority": "MEDIUM",
                "pack_id": "ckd_adult_outpatient",
                "pack_label": "Bệnh thận mạn",
                "title": "KDIGO update",
            },
        ]
    }, ensure_ascii=False), encoding="utf-8")

    updates = gen_morning_brief.check_surveillance_updates()

    assert any("Knowledge pack queue: 2 mục" in update for update in updates)
    assert any("Đái tháo đường type 2" in update for update in updates)
