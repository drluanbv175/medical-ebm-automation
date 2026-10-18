"""Hồi quy 18/10/2026: cầu nối engine → sổ cái KHÔNG nạp lại mục bác sĩ đã thay nguồn hoặc đã loại.

Lỗi đo thật: cầu nối quét lại MỌI mục tier A/actionable của engine ở mỗi lượt và chỉ chống trùng theo `source.doi`
của thẻ đang có. 5 thẻ hub trỏ DOI máy sinh (4 câu trả lời AI AskTrip trên Zenodo + 1 kỷ yếu DOI 10.82161) — bác sĩ
duyệt đổi sang DOI guideline gốc / loại thẻ trùng. Sau khi đổi, khoá Zenodo biến mất khỏi sổ cái ⇒ lượt
`weekly_safety.sh` kế tiếp nạp lại đúng 5 mục đó thành thẻ mới. Danh sách chặn nằm ở `meta.bridge_khong_nap_lai`.
Offline; `ledger_ids` thay bằng bản giả tối thiểu (như test EV-08).
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
_COT = ["is_mock", "is_actionable", "reliability_tier", "practice_change_score", "evidence_quality_score",
        "journal_or_organization", "source", "title", "url", "pmid", "doi", "source_type", "study_type",
        "publication_date", "update_date", "clinical_area", "population", "intervention", "comparator",
        "outcomes", "practice_impact", "safety_signal", "actionable_reason", "reason_for_exclusion",
        "official_grade", "operational_evidence_level", "synthesis", "last_run_id"]


@pytest.fixture()
def bridge(monkeypatch):
    gia = types.ModuleType("ledger_ids")
    gia.assert_unique = lambda cards: None
    gia.max_seq = lambda cards: len(cards)
    monkeypatch.setitem(sys.modules, "ledger_ids", gia)
    spec = importlib.util.spec_from_file_location("bridge_to_ebm_master_khong_nap_lai", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _tao_db(duong_dan: Path, hang: list[dict]) -> None:
    con = sqlite3.connect(duong_dan)
    con.execute("CREATE TABLE evidence_items (%s)" % ", ".join(_COT))
    for h in hang:
        day = {c: None for c in _COT}
        day.update({"is_mock": 0, "is_actionable": 1, "reliability_tier": "A", "practice_change_score": 60,
                    "evidence_quality_score": 93})
        day.update(h)
        con.execute("INSERT INTO evidence_items VALUES (%s)" % ", ".join("?" * len(_COT)), [day[c] for c in _COT])
    con.commit()
    con.close()


def _chay(bridge, tmp_path, monkeypatch, meta_them: dict, the_co_san: list[dict]) -> list[dict]:
    hub = tmp_path / "EBM_MASTER"
    hub.mkdir()
    meta = {"counts": {"evidence_cards": len(the_co_san)}}
    meta.update(meta_them)
    (hub / "EBM_MASTER.json").write_text(json.dumps({"meta": meta, "evidence_cards": the_co_san}),
                                         encoding="utf-8", newline="\n")
    db = tmp_path / "medical_ebm.db"
    _tao_db(db, [
        {"title": "What do the KDIGO guidelines recommend for anemia management?", "doi": "10.5281/zenodo.20834906"},
        {"title": "2018 EULAR RECOMMENDATIONS FOR PHYSICAL ACTIVITY", "doi": "10.82161/0fgc-zz44"},
        {"title": "Một guideline mới thật", "pmid": "99999999"},
    ])
    monkeypatch.setattr(bridge, "HUB", str(hub))
    monkeypatch.setattr(sys, "argv", ["bridge", "--today", "2026-10-19", "--db", str(db)])
    assert bridge.main() == 0
    return json.loads((hub / "EBM_MASTER.json").read_text(encoding="utf-8"))["evidence_cards"]


def test_khoa_khong_nap_lai_doc_ca_chuoi_lan_dict_khong_phan_biet_hoa_thuong(bridge):
    data = {"meta": {"bridge_khong_nap_lai": [
        "10.5281/ZENODO.1", {"key": " 10.82161/0FGC-ZZ44 ", "ly_do": "kỷ yếu"}, {"ly_do": "thiếu khoá"}, "", 7, None]}}
    assert bridge.khoa_khong_nap_lai(data) == {"10.5281/zenodo.1", "10.82161/0fgc-zz44"}
    assert bridge.khoa_khong_nap_lai({}) == set()
    assert bridge.khoa_khong_nap_lai({"meta": {"bridge_khong_nap_lai": None}}) == set()


def test_ca_loi_goc_khong_co_danh_sach_thi_nap_lai_muc_da_thay_nguon(bridge, tmp_path, monkeypatch):
    """Đối chứng: thẻ đã đổi sang DOI gốc, sổ cái KHÔNG có danh sách ⇒ mục Zenodo bị nạp lại (đúng lỗi 18/10)."""
    da_thay = {"id": "EVID-2026-1149", "source": {"doi": "10.1016/j.ard.2026.03.006", "pmid": "42036268"}}
    the = _chay(bridge, tmp_path, monkeypatch, {}, [da_thay])
    assert {c["source"]["doi"] for c in the} >= {"10.5281/zenodo.20834906", "10.82161/0fgc-zz44"}


def test_danh_sach_chan_nap_lai_nhung_van_nap_muc_moi_that(bridge, tmp_path, monkeypatch, capsys):
    da_thay = {"id": "EVID-2026-1149", "source": {"doi": "10.1016/j.ard.2026.03.006", "pmid": "42036268"}}
    meta = {"bridge_khong_nap_lai": [
        {"key": "10.5281/zenodo.20834906", "ly_do": "trùng EVID-2026-1242 — đã loại"},
        {"key": "10.82161/0FGC-ZZ44", "ly_do": "đã thay nguồn sang EULAR 2025"}]}
    the = _chay(bridge, tmp_path, monkeypatch, meta, [da_thay])
    doi = {c["source"]["doi"] for c in the}
    assert "10.5281/zenodo.20834906" not in doi and "10.82161/0fgc-zz44" not in doi
    assert any(c["source"]["pmid"] == "99999999" for c in the), "mục mới thật vẫn được nạp"
    assert len(the) == 2
    assert "2 bỏ qua theo danh sách không nạp lại" in capsys.readouterr().out
