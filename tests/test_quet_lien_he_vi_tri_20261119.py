# -*- coding: utf-8 -*-
"""G9-AUTO-06 / G10-AUTO-08: phân biệt «chưa có tệp» với «có PII» và nêu vị trí dòng (19/11/2026).

Ca thật: G10 của đề tài BTM chưa lắp gói nên chưa có G10_RELEASE_READINESS.json; hàm cũ trả True khi không đọc được
tệp ⇒ bằng chứng «contact_pii_detected=True». Hội đồng cổng (2 người chấm + trọng tài) đi tìm PII không có thật và
ghi bài học hệ thống: bằng chứng phải nêu tệp/dòng. Vẫn chặn khi chưa có tệp (fail-closed) — chỉ đổi lời bằng chứng.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import g9_quality_gate as G9  # noqa: E402
import g10_quality_gate as G10  # noqa: E402


@pytest.mark.parametrize("mod", [G9, G10])
def test_chua_co_tep_la_chua_do_khong_phai_co_pii(tmp_path, mod):
    kq, mo_ta = mod.quet_lien_he(tmp_path / "G10_RELEASE_READINESS.json")
    assert kq is None and "chưa đo" in mo_ta
    assert mod._readiness_has_contact_pii(tmp_path / "khong-co.json") is True  # người gọi cũ vẫn chặn


@pytest.mark.parametrize("mod", [G9, G10])
def test_co_pii_neu_dong_khong_chep_noi_dung(tmp_path, mod):
    p = tmp_path / "r.json"
    p.write_text('{\n "a": "AUTHOR-01",\n "lien_he": "bs.a@example.com",\n "dt": "0912 345 678"\n}\n',
                 encoding="utf-8", newline="\n")
    kq, mo_ta = mod.quet_lien_he(p)
    assert kq is True
    assert "dòng 3 (email)" in mo_ta and "dòng 4 (điện thoại)" in mo_ta
    assert "example.com" not in mo_ta and "345" not in mo_ta


@pytest.mark.parametrize("mod", [G9, G10])
def test_tep_sach(tmp_path, mod):
    p = tmp_path / "r.json"
    p.write_text('{"nguoi_ky": "PI-REF-01"}\n', encoding="utf-8", newline="\n")
    assert mod.quet_lien_he(p)[0] is False
    assert mod._readiness_has_contact_pii(p) is False


def _hang(report, ma):
    return next(r for r in report["automatic_criteria"] if r["id"] == ma)


def test_g10_auto_08_bang_chung_noi_dung_chua_co_tep(tmp_path, monkeypatch):
    """Đi qua đường gọi thật của bộ chấm: tệp readiness vắng ⇒ BLOCK, bằng chứng «chưa đo», không «=True»."""
    goi = []
    goc = G10.quet_lien_he

    def _gian(path):
        kq = goc(path)
        goi.append(kq)
        return kq

    monkeypatch.setattr(G10, "quet_lien_he", _gian)
    out = tmp_path / "exports" / "de-tai-thu"
    out.mkdir(parents=True)
    report = G10.evaluate_study("de-tai-thu", out, repo_root=tmp_path, write=False)
    hang = _hang(report, "G10-AUTO-08")
    assert hang["status"] == "BLOCK"
    assert "contact_pii_detected=chưa đo" in hang["evidence"] and "contact_pii_detected=True" not in hang["evidence"]
    assert goi and goi[0][0] is None


def test_g9_auto_06_chua_co_tep_van_chan_va_noi_dung(tmp_path):
    out = tmp_path / "exports" / "de-tai-thu"
    out.mkdir(parents=True)
    report = G9.evaluate_study("de-tai-thu", out, repo_root=tmp_path, write=False)
    hang = _hang(report, "G9-AUTO-06")
    assert hang["status"] == "BLOCK"
    assert "contact_pii_readiness=chưa đo" in hang["evidence"]
    assert "contact_pii_readiness=True" not in hang["evidence"]
