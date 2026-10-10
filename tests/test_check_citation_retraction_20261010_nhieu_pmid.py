# -*- coding: utf-8 -*-
"""`check_citation_retraction.py` nhận nhiều PMID theo đúng cách guardrail của MỌI agent dạy — vá 10/10/2026.

Guardrail bắt buộc (`enforce_agent_guardrails.NEW_RUT_BAI`, chép vào 65 tài liệu agent) và skill cập nhật chứng cứ dạy
`--pmid <PMID…>`; bản cũ chỉ có `--pmids` nhận MỘT chuỗi nối phẩy ⇒ `--pmid 1 2` chết «unrecognized arguments» (mã 2)
đúng ở bước tra rút bài bắt buộc. Ngoại tuyến: chuỗi tra rút bài được thay bằng bản giả.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import check_citation_retraction as CLI  # noqa: E402


class _ChuoiGia:
    hoi: list = []

    def check(self, pmids):
        _ChuoiGia.hoi.append(list(pmids))
        return {p: {"status": "ok", "sources_tried": ["gia"]} for p in pmids}


@pytest.mark.parametrize("doi_so, mong", [
    (["--pmid", "30267080"], ["30267080"]),
    (["--pmid", "30267080", "41485807"], ["30267080", "41485807"]),
    (["--pmids", "30267080,41485807"], ["30267080", "41485807"]),
    (["--pmid", "30267080,41485807", "39578415"], ["30267080", "41485807", "39578415"]),
    (["--pmids", "30267080", "30267080,", "41485807"], ["30267080", "41485807"]),
])
def test_nhan_nhieu_pmid_cach_trang_hoac_phay_khong_trung(monkeypatch, doi_so, mong):
    _ChuoiGia.hoi = []
    monkeypatch.setattr(CLI, "RetractionChain", _ChuoiGia)
    monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", *doi_so, "--json"])
    assert CLI.main() == 0
    assert _ChuoiGia.hoi == [mong]


def test_thieu_pmid_van_bao_loi_doi_so(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", "--json"])
    with pytest.raises(SystemExit) as e:
        CLI.main()
    assert e.value.code == 2


def test_chi_toan_dau_phay_la_rong(monkeypatch, capsys):
    monkeypatch.setattr(CLI, "RetractionChain", _ChuoiGia)
    monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", "--pmid", ",", ","])
    assert CLI.main() == 1
    assert "rỗng" in capsys.readouterr().out
