"""Hồi quy 14/10/2026: chuỗi PubMed có thẻ trường gửi nguyên sang ClinicalTrials.gov ⇒ HTTP 400.

Lần chạy lại G0 của C1a với chuỗi PubMed PI chọn (có `[Mesh]`, `[tiab]`) làm bước tra đăng ký thành
«CHƯA TRA ĐƯỢC» dù mạng tốt: `check_trial_registry` gửi nguyên chuỗi sang CT.gov, mà CT.gov từ chối thẻ trường
PubMed. Đo thật cùng ngày: bỏ thẻ ⇒ HTTP 200. Bản vá `trial_registry.truy_van_ctgov` bỏ thẻ trước khi gửi và ghi
chuỗi đã gửi vào `query_gui_ctgov` (truy nguyên PRISMA-S). Test mock `app.utils.http.HttpClient` theo khuôn sẵn có.
"""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import trial_registry as TR  # noqa: E402

import app.utils.http as http_mod  # noqa: E402
from app.config import settings  # noqa: E402

CHUOI_PUBMED = ('("Patient Satisfaction"[Mesh] OR satisf*[tiab]) AND ("Outpatients"[Mesh] OR outpatient*[tiab]) '
                'AND ("Vietnam"[Mesh] OR vietnam*[tiab])')


class _HttpGhiLai:
    """Giả CT.gov: từ chối mọi `query.term` còn thẻ trường PubMed (như API thật), ghi lại tham số đã gửi."""

    da_gui: list = []

    def get_json(self, url, params=None):
        term = (params or {}).get("query.term", "")
        _HttpGhiLai.da_gui.append(term)
        if "[" in term or "]" in term:
            raise RuntimeError("400 Client Error: Bad Request")
        return {"totalCount": 5, "studies": []}


def _tra(q):
    _HttpGhiLai.da_gui = []
    with patch.object(settings, "use_mock_sources", False), patch.object(http_mod, "HttpClient", _HttpGhiLai):
        return TR.check_trial_registry(q)


def test_chuoi_pubmed_co_the_truong_van_tra_duoc_va_ghi_chuoi_da_gui():
    kq = _tra(CHUOI_PUBMED)
    assert kq["checked"] is True, kq.get("error")
    assert kq["n_trials"] == 5
    assert _HttpGhiLai.da_gui and all("[" not in t for t in _HttpGhiLai.da_gui)
    assert kq["query"] == CHUOI_PUBMED  # chuỗi gốc giữ nguyên
    assert kq["query_gui_ctgov"] == _HttpGhiLai.da_gui[0]
    assert '"Patient Satisfaction" OR satisf*' in kq["query_gui_ctgov"]


def test_chuoi_thuong_gui_nguyen_va_khong_them_khoa():
    kq = _tra("patient satisfaction outpatient department Vietnam hospital")
    assert kq["checked"] is True
    assert _HttpGhiLai.da_gui[0] == "patient satisfaction outpatient department Vietnam hospital"
    assert "query_gui_ctgov" not in kq


def test_chi_co_the_truong_thi_la_truy_van_rong_khong_goi_mang():
    kq = _tra("[Mesh] [tiab]")
    assert kq["checked"] is False and kq["error"] == "truy vấn rỗng"
    assert _HttpGhiLai.da_gui == []


def test_lien_ket_tra_lai_dung_chuoi_da_gui():
    url = TR.registry_search_url(CHUOI_PUBMED)
    assert "%5B" not in url and "Mesh" not in url
