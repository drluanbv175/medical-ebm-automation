"""Hồi quy khôi phục thẻ cách ly khi dashboard gốc đã có nguồn truy nguyên."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[2] / "EBM_MASTER" / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location("ingest_dashboard_rehydration", TOOLS / "ingest_dashboard.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


def _quarantined(card_id: str = "EVID-2026-0271") -> dict:
    return {
        "id": card_id,
        "date_added": "2026-07-10",
        "specialty": "Hô hấp",
        "topic": "GOLD 2026: case-finding chủ đích",
        "source": {"pmid": "", "doi": "", "url": ""},
        "decision": "notyet",
        "verification_status": "cần truy nguyên nguồn trước khi áp dụng",
        "quarantine_reason": "missing PMID/DOI/URL/references",
        "history": [
            {
                "date": "2026-07-10",
                "change": "nạp từ dashboard COPD_2026.html",
            }
        ],
    }


def _traceable_card() -> dict:
    return {
        "id": "EVID-2026-9999",
        "date_added": "2026-08-14",
        "specialty": "",
        "topic": "GOLD 2026: case-finding chủ đích",
        "source": {
            "pmid": "",
            "doi": "",
            "url": "https://goldcopd.org/2026-gold-report-and-pocket-guide/",
        },
        "decision": "apply",
        "verification_status": "đã xác minh",
        "history": [{"change": "nạp từ dashboard COPD_2026.html"}],
    }


def test_rehydrate_preserves_identity_and_forces_manual_review_queue():
    old = _quarantined()
    data = {"evidence_cards": [], "quarantined_cards": [old]}

    changed = MODULE.rehydrate_quarantined_card(
        data,
        _traceable_card(),
        today="2026-08-14",
        dashboard_name="COPD_2026.html",
    )

    assert changed == "preserved"
    assert data["quarantined_cards"] == []
    assert len(data["evidence_cards"]) == 1
    restored = data["evidence_cards"][0]
    assert restored["id"] == "EVID-2026-0271"
    assert restored["date_added"] == "2026-07-10"
    assert restored["specialty"] == "Hô hấp"
    assert restored["decision"] == "notyet"
    assert restored["verification_status"] == "cần bác sĩ xác minh nguồn sau khôi phục tự động"
    assert restored["quarantine_recovery"]["status"] == "RESTORED_TO_REVIEW_QUEUE"
    assert restored["quarantine_recovery"]["original_id"] == "EVID-2026-0271"
    assert restored["quarantine_recovery"]["id_conflict"] is False
    assert "quarantine_reason" not in restored
    assert any("giữ ID" in event["change"] for event in restored["history"])


def test_rehydrate_refuses_card_without_new_traceability():
    data = {"evidence_cards": [], "quarantined_cards": [_quarantined()]}
    card = _traceable_card()
    card["source"]["url"] = ""

    changed = MODULE.rehydrate_quarantined_card(
        data,
        card,
        today="2026-08-14",
        dashboard_name="COPD_2026.html",
    )

    assert changed is False
    assert len(data["quarantined_cards"]) == 1
    assert data["evidence_cards"] == []


def test_rehydrate_requires_same_origin_dashboard():
    data = {"evidence_cards": [], "quarantined_cards": [_quarantined()]}

    changed = MODULE.rehydrate_quarantined_card(
        data,
        _traceable_card(),
        today="2026-08-14",
        dashboard_name="OTHER.html",
    )

    assert changed is False
    assert len(data["quarantined_cards"]) == 1


def test_rehydrate_fails_closed_when_match_is_ambiguous():
    data = {
        "evidence_cards": [],
        "quarantined_cards": [_quarantined("A"), _quarantined("B")],
    }

    try:
        MODULE.rehydrate_quarantined_card(
            data,
            _traceable_card(),
            today="2026-08-14",
            dashboard_name="COPD_2026.html",
        )
    except RuntimeError as exc:
        assert "cần bác sĩ chọn thẻ khôi phục" in str(exc)
    else:
        raise AssertionError("Nhiều ứng viên khôi phục phải fail-closed")


def test_rehydrate_reassigns_colliding_historical_id_and_keeps_lineage():
    old = _quarantined("EVID-2026-0274")
    data = {
        "evidence_cards": [
            {
                "id": "EVID-2026-0274",
                "topic": "Một chứng cứ khác đã được cấp cùng ID trong quá khứ",
            }
        ],
        "quarantined_cards": [old],
    }
    card = _traceable_card()
    card["id"] = "EVID-2026-0300"

    changed = MODULE.rehydrate_quarantined_card(
        data,
        card,
        today="2026-08-14",
        dashboard_name="COPD_2026.html",
    )

    assert changed == "reassigned"
    assert data["quarantined_cards"] == []
    assert len({item["id"] for item in data["evidence_cards"]}) == 2
    restored = next(item for item in data["evidence_cards"] if item["id"] == "EVID-2026-0300")
    assert restored["decision"] == "notyet"
    assert restored["quarantine_recovery"] == {
        "status": "RESTORED_TO_REVIEW_QUEUE",
        "dashboard": "COPD_2026.html",
        "restored_at": "2026-08-14",
        "original_id": "EVID-2026-0274",
        "assigned_id": "EVID-2026-0300",
        "id_conflict": True,
    }
    assert any("cấp ID mới" in event["change"] for event in restored["history"])


def test_max_ledger_seq_reserves_ids_held_by_quarantine():
    data = {
        "evidence_cards": [{"id": "EVID-2026-0270"}],
        "quarantined_cards": [{"id": "EVID-2026-0999"}],
    }

    assert MODULE.max_ledger_seq(data) == 999
