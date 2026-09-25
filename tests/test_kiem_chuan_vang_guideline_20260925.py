"""Kiểm `tools/kiem_chuan_vang_guideline.py` (25/09/2026) — OFFLINE, hàm tìm được tiêm vào."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

GOC = Path(__file__).resolve().parents[1]
_TEP = GOC / "tools" / "kiem_chuan_vang_guideline.py"
_sp = importlib.util.spec_from_file_location("kiem_chuan_vang_guideline", _TEP)
M = importlib.util.module_from_spec(_sp)
_sp.loader.exec_module(M)

CHUAN = {"top_n": 3, "chu_de": [
    {"chu_de": "A", "truy_van": "qa", "nhom": [
        {"ten": "g1", "pmid": ["1", "11"], "bac_si_duyet": None},
        {"ten": "g2", "pmid": ["2"], "bac_si_duyet": "2026-09-25"}]},
    {"chu_de": "B", "truy_van": "qb", "nhom": [{"ten": "g3", "pmid": ["3"], "bac_si_duyet": None}]},
]}


def test_dat_truot_va_vi_tri():
    kq = M.cham(CHUAN, lambda q, n: {"qa": ["9", "11", "8", "2"], "qb": ["3"]}[q])
    a = kq["chu_de"][0]["nhom"]
    assert a[0]["vi_tri"] == 2          # bản thứ hai của cùng guideline vẫn tính
    assert a[1]["vi_tri"] is None       # PMID 2 nằm NGOÀI top 3 ⇒ trượt
    assert (kq["dat"], kq["truot"], kq["khong_do_duoc"]) == (2, 1, 0)


def test_loi_engine_la_khong_do_duoc_khong_phai_truot():
    def tim(q, n):
        if q == "qb":
            raise RuntimeError("PubMed lỗi")
        return ["1", "2"]
    kq = M.cham(CHUAN, tim)
    assert (kq["dat"], kq["truot"], kq["khong_do_duoc"]) == (2, 0, 1)
    assert "PubMed lỗi" in kq["chu_de"][1]["loi"]


def test_ma_thoat(monkeypatch, tmp_path):
    tep = tmp_path / "c.json"
    tep.write_text(json.dumps(CHUAN), encoding="utf-8", newline="\n")
    monkeypatch.setattr(sys, "argv", ["x", "--tep", str(tep)])
    monkeypatch.setattr(M, "_tim_that", lambda q, n: ["1", "2", "3"])
    assert M.main() == 0
    monkeypatch.setattr(M, "_tim_that", lambda q, n: [])
    assert M.main() == 1

    def hong(q, n):
        raise RuntimeError("mock")
    monkeypatch.setattr(M, "_tim_that", hong)
    assert M.main() == 2                 # không đo được KHÔNG bao giờ thành 0


def test_tep_chuan_vang_that_hop_le():
    chuan = json.loads((GOC / "config" / "chuan_vang_guideline.json").read_text(encoding="utf-8"))
    assert chuan["top_n"] >= 5
    for cd in chuan["chu_de"]:
        assert cd["truy_van"] and cd["nhom"]
        for nh in cd["nhom"]:
            assert nh["pmid"] and all(p.isdigit() for p in nh["pmid"])
            assert "bac_si_duyet" in nh     # trường duyệt phải có sẵn để bác sĩ điền
