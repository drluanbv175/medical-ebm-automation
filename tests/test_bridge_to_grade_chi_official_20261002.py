"""Hồi quy 02/10/2026 (EV-08): cầu nối engine → sổ cái KHÔNG được biến điểm MÁY CHẤM thành `gradeLevel`.

Lỗi gốc: `to_grade` đọc cả `operational_evidence_level`. Khi nguồn không có GRADE, trường đó là mức VẬN HÀNH máy
ước từ điểm chất lượng ("High (operational)") ⇒ mọi thẻ engine tier A thành `gradeLevel: high` (đo 02/10/2026:
409/409 thẻ `from_engine` mang «high», +111 thẻ trong 4 ngày; WebApp hiện nhãn «GRADE: high» cho chúng).
Luật: `gradeLevel` chỉ đến từ phân hạng do NGUỒN công bố (`official_grade`); không có ⇒ "na" (không phải «yếu»).
Offline, không mạng; `ledger_ids` (sống ở EBM_MASTER/tools của repo gốc, vắng khi CI chỉ có repo y khoa) được thay
bằng bản giả tối thiểu.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import types
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "bridge_to_ebm_master.py"


@pytest.fixture()
def bridge(monkeypatch):
    gia = types.ModuleType("ledger_ids")
    gia.assert_unique = lambda cards: None
    gia.max_seq = lambda cards: len(cards)
    monkeypatch.setitem(sys.modules, "ledger_ids", gia)
    spec = importlib.util.spec_from_file_location("bridge_to_ebm_master_under_test", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("item,mong_doi", [
    # Ca lỗi gốc: chỉ có mức vận hành do máy ước ⇒ KHÔNG được thành high.
    ({"operational_evidence_level": "High (operational)", "reliability_tier": "A"}, "na"),
    ({"operational_evidence_level": "Moderate (operational)"}, "na"),
    ({"operational_evidence_level": "Low (operational)"}, "na"),
    ({"operational_evidence_level": "High"}, "na"),  # kể cả chữ «High» trơn: không phải phân hạng của nguồn
    ({}, "na"),
    ({"official_grade": None}, "na"),
    ({"official_grade": ""}, "na"),
    # Phân hạng chính thức của nguồn được giữ.
    ({"official_grade": "High"}, "high"),
    ({"official_grade": "GRADE: Moderate certainty"}, "mod"),
    ({"official_grade": "Low"}, "low"),
    ({"official_grade": "Very low"}, "vlow"),
    ({"official_grade": "vlow"}, "vlow"),
    # Văn bản tự do nhắc cả cao lẫn thấp ⇒ mức THẤP hơn (thận trọng).
    ({"official_grade": "Downgraded from high to low"}, "low"),
    ({"official_grade": "High risk of bias, low certainty"}, "low"),
    ({"official_grade": "high to moderate"}, "mod"),
    # Có nhãn nguồn nhưng không nêu mức ⇒ "na", không đoán.
    ({"official_grade": "GRADE (theo ESC)"}, "na"),
    ({"official_grade": "Strong recommendation"}, "na"),
    # Không khớp chuỗi con trong từ khác («below», «allow»).
    ({"official_grade": "below threshold"}, "na"),
])
def test_to_grade_chi_tu_official_grade(bridge, item, mong_doi):
    assert bridge.to_grade(item) == mong_doi


def test_to_grade_official_thang_operational_khi_hai_truong_khac_nhau(bridge):
    """Nguồn nói «low» thì low, bất kể điểm máy gợi ý «High (operational)»."""
    item = {"official_grade": "Low", "operational_evidence_level": "High (operational)"}
    assert bridge.to_grade(item) == "low"


def test_to_decision_van_khong_bao_gio_apply(bridge):
    assert bridge.to_decision({"is_actionable": 1}) == "consider"
    assert bridge.to_decision({"is_actionable": 0}) == "notyet"


def _tao_db(duong_dan: Path, hang: list[dict]) -> None:
    cot = ["is_mock", "is_actionable", "reliability_tier", "practice_change_score", "evidence_quality_score",
           "journal_or_organization", "source", "title", "url", "pmid", "doi", "source_type", "study_type",
           "publication_date", "update_date", "clinical_area", "population", "intervention", "comparator",
           "outcomes", "practice_impact", "safety_signal", "actionable_reason", "reason_for_exclusion",
           "official_grade", "operational_evidence_level", "synthesis", "last_run_id"]
    con = sqlite3.connect(duong_dan)
    con.execute("CREATE TABLE evidence_items (%s)" % ", ".join(cot))
    for h in hang:
        day = {c: None for c in cot}
        day.update(h)
        con.execute("INSERT INTO evidence_items VALUES (%s)" % ", ".join("?" * len(cot)), [day[c] for c in cot])
    con.commit()
    con.close()


def test_main_dau_cuoi_the_engine_tier_a_khong_mang_high(bridge, tmp_path, monkeypatch, capsys):
    """Đầu–cuối trên DB giả: thẻ tier A chỉ có điểm máy ⇒ gradeLevel "na"; thẻ có official_grade ⇒ giữ."""
    hub = tmp_path / "EBM_MASTER"
    hub.mkdir()
    (hub / "EBM_MASTER.json").write_text(json.dumps(
        {"meta": {"counts": {"evidence_cards": 0}}, "evidence_cards": []}), encoding="utf-8")
    db = tmp_path / "medical_ebm.db"
    _tao_db(db, [
        {"is_mock": 0, "is_actionable": 1, "reliability_tier": "A", "practice_change_score": 80,
         "evidence_quality_score": 90, "title": "Chỉ có điểm máy", "pmid": "111",
         "operational_evidence_level": "High (operational)"},
        {"is_mock": 0, "is_actionable": 1, "reliability_tier": "A", "practice_change_score": 70,
         "evidence_quality_score": 85, "title": "Có GRADE của nguồn", "pmid": "222",
         "official_grade": "Moderate", "operational_evidence_level": "Moderate"},
    ])
    monkeypatch.setattr(bridge, "HUB", str(hub))
    monkeypatch.setattr(sys, "argv", ["bridge", "--today", "2026-10-02", "--db", str(db)])
    assert bridge.main() == 0
    the = json.loads((hub / "EBM_MASTER.json").read_text(encoding="utf-8"))["evidence_cards"]
    theo_pmid = {c["source"]["pmid"]: c for c in the}
    assert theo_pmid["111"]["gradeLevel"] == "na"
    assert theo_pmid["222"]["gradeLevel"] == "mod"
    assert all(c["provenance"] == "from_engine" and c["decision"] != "apply" for c in the)
    assert "máy chấm" in theo_pmid["111"]["certainty"]  # điểm máy vẫn hiện, gắn nhãn đúng bản chất
