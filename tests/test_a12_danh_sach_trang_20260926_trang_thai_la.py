"""Cổng A12: DANH SÁCH TRẮNG {"ok"} — trạng thái lạ không bao giờ được tính là sạch.

Vá 26/09/2026 (phát hiện #34). Receipt A12 (được ký; G10 chỉ đọc `all_clean`) và mã thoát CLI của
`check_citation_retraction.py`/`check_citations.py` trước đây dùng DANH SÁCH ĐEN `_PROBLEM_STATUSES`:
một trạng thái chưa từng liệt kê ('rate_limited', None, '', bản ghi không phải dict…) bị tính là SẠCH ⇒
`all_clean=true` ⇒ G10 mở cổng dù không PMID nào được kiểm — đúng kịch bản fail-open ngày 14/08.

Phòng thủ nhiều lớp được khoá ở đây:
  (1) `check_citation_retraction.la_van_de` — chỉ `{"status": "ok"}` là sạch (receipt + mã thoát);
  (2) `check_citations.py` — rút bài qua `CCR.la_van_de`, metadata chỉ "resolved";
  (3) `RetractionChain` — trạng thái lạ của PubMed được hỏi Europe PMC, và nếu không nguồn nào kết luận
      được thì chuẩn hoá thành 'unknown_fetch_error' (giữ trạng thái gốc trong `reason`).

Ngoại tuyến hoàn toàn: client PubMed/Europe PMC là bản giả, không gọi mạng; receipt ghi vào tmp_path.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
for _p in (REPO_ROOT, REPO_ROOT / "tools"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import check_citation_metadata as CCM  # noqa: E402
import check_citation_retraction as CCR  # noqa: E402
import check_citations as CC  # noqa: E402

from app.sources.pubmed import PubMedClient  # noqa: E402
from app.sources.retraction_chain import RetractionChain  # noqa: E402

TRANG_THAI_LA = ["rate_limited", None, "", "timeout", "OK", "ok "]


class _FakeRW:
    """Nền Retraction Watch chưa tải (không bao giờ nói gì)."""

    def san_sang(self) -> bool:
        return False

    def tra(self, pmid):  # pragma: no cover - không được gọi khi chưa sẵn sàng
        return None


class _FakeClient:
    """Client giả: trả đúng `ket_qua` (có thể không phải dict) và ghi lại PMID đã được hỏi."""

    def __init__(self, ket_qua) -> None:
        self._kq = ket_qua
        self.called_with: list[list[str]] = []

    def check_retraction_status(self, pmids):
        self.called_with.append(list(pmids))
        if not isinstance(self._kq, dict):
            return self._kq
        return {p: self._kq[p] for p in pmids if p in self._kq}

    def fetch_metadata(self, pmids):  # pragma: no cover - chỉ gọi khi có thông báo rút bài
        return {}

    def fetch_notice_titles(self, pmids):  # pragma: no cover
        return {}


def _chuoi(pm_kq, ep_kq=None):
    pm = _FakeClient(pm_kq)
    ep = _FakeClient(ep_kq if ep_kq is not None else {})
    return RetractionChain(rw=_FakeRW(), pubmed=pm, europepmc=ep), pm, ep


# ================================================================ (1) la_van_de

def test_chi_ok_la_sach():
    assert CCR.la_van_de({"status": "ok"}) is False
    assert CCR.la_van_de({"status": "ok", "ghi_chu": "x", "source": "pubmed"}) is False


@pytest.mark.parametrize("tt", TRANG_THAI_LA)
def test_trang_thai_la_la_van_de(tt):
    assert CCR.la_van_de({"status": tt}) is True


@pytest.mark.parametrize("info", [None, "ok", ["ok"], 0, {}, {"reason": "thiếu khoá status"}])
def test_ban_ghi_khong_dung_dinh_dang_la_van_de(info):
    assert CCR.la_van_de(info) is True


@pytest.mark.parametrize("tt", ["retracted", "expression_of_concern", "unresolved",
                                "unknown_mock_or_no_email", "unknown_fetch_error"])
def test_trang_thai_da_biet_khong_sach_van_la_van_de(tt):
    assert CCR.la_van_de({"status": tt}) is True


def test_nhan_trang_thai_la_khong_in_chuoi_tho():
    assert "TRẠNG THÁI LẠ" in CCR.nhan_trang_thai("rate_limited")
    assert "TRẠNG THÁI LẠ" in CCR.nhan_trang_thai(None)
    assert CCR.nhan_trang_thai("ok") == CCR._STATUS_LABEL["ok"]


# ================================================================ receipt (ký — G10 chỉ đọc all_clean)

def _doc_receipt(monkeypatch, tmp_path, pmids, results):
    monkeypatch.setattr(CCR, "REPO_ROOT", tmp_path)
    path = CCR.write_retraction_receipt("PYTEST-A12-WL", pmids, results)
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("tt", TRANG_THAI_LA)
def test_receipt_trang_thai_la_khong_sach(monkeypatch, tmp_path, tt):
    r = _doc_receipt(monkeypatch, tmp_path, ["1", "2"], {"1": {"status": "ok"}, "2": {"status": tt}})
    assert r["all_clean"] is False


def test_receipt_ban_ghi_khong_phai_dict_khong_sach(monkeypatch, tmp_path):
    r = _doc_receipt(monkeypatch, tmp_path, ["1"], {"1": None})
    assert r["all_clean"] is False


def test_receipt_lo_rong_khong_bao_gio_sach(monkeypatch, tmp_path):
    r = _doc_receipt(monkeypatch, tmp_path, [], {})
    assert r["all_clean"] is False


def test_receipt_doi_chung_moi_pmid_ok_thi_sach(monkeypatch, tmp_path):
    r = _doc_receipt(monkeypatch, tmp_path, ["1", "2"], {"1": {"status": "ok"}, "2": {"status": "ok"}})
    assert r["all_clean"] is True


# ================================================================ CLI check_citation_retraction

class _ChuoiTraThang:
    """Chuỗi giả trả NGUYÊN kết quả (bỏ qua lớp chuẩn hoá của RetractionChain) — để khoá riêng lớp CLI."""

    def __init__(self, kq) -> None:
        self._kq = kq

    def check(self, pmids):
        return self._kq


def _chay_ccr(monkeypatch, capsys, argv, chuoi):
    monkeypatch.setattr(CCR, "RetractionChain", lambda: chuoi)
    monkeypatch.setattr(sys, "argv", ["check_citation_retraction.py", *argv])
    rc = CCR.main()
    return rc, capsys.readouterr()


@pytest.mark.parametrize("tt", TRANG_THAI_LA)
def test_cli_van_ban_trang_thai_la_thoat_1(monkeypatch, capsys, tt):
    rc, out = _chay_ccr(monkeypatch, capsys, ["--pmids", "1"], _ChuoiTraThang({"1": {"status": tt}}))
    assert rc == 1
    assert "Không phát hiện" not in out.out
    assert "TRẠNG THÁI LẠ" in out.out


@pytest.mark.parametrize("tt", TRANG_THAI_LA)
def test_cli_json_trang_thai_la_thoat_1(monkeypatch, capsys, tt):
    rc, out = _chay_ccr(monkeypatch, capsys, ["--pmids", "1", "--json"],
                        _ChuoiTraThang({"1": {"status": tt}}))
    assert rc == 1
    json.loads(out.out)


def test_cli_ban_ghi_khong_phai_dict_thoat_1_khong_sap(monkeypatch, capsys):
    rc, _ = _chay_ccr(monkeypatch, capsys, ["--pmids", "1"], _ChuoiTraThang({"1": None}))
    assert rc == 1


def test_cli_json_pmid_vang_mat_thoat_1(monkeypatch, capsys):
    rc, _ = _chay_ccr(monkeypatch, capsys, ["--pmids", "1,2", "--json"],
                      _ChuoiTraThang({"1": {"status": "ok"}}))
    assert rc == 1


def test_cli_doi_chung_ok_thoat_0(monkeypatch, capsys):
    rc, out = _chay_ccr(monkeypatch, capsys, ["--pmids", "1"], _ChuoiTraThang({"1": {"status": "ok"}}))
    assert rc == 0
    assert "Không phát hiện" in out.out


@pytest.mark.parametrize("pm_kq", [
    {"1": {"status": "rate_limited"}},
    {"1": {"status": None}},
    {"1": {"status": ""}},
    {"1": "không phải dict"},
    None,
])
def test_cli_qua_chuoi_that_ghi_receipt_khong_sach(monkeypatch, capsys, tmp_path, pm_kq):
    """Đầu–cuối qua RetractionChain THẬT (client giả): receipt không sạch, CLI thoát 1."""
    chuoi, _, _ = _chuoi(pm_kq)
    monkeypatch.setattr(CCR, "REPO_ROOT", tmp_path)
    rc, _ = _chay_ccr(monkeypatch, capsys, ["--pmids", "1", "--study", "PYTEST-A12-WL-E2E"], chuoi)
    assert rc == 1
    r = json.loads((tmp_path / "exports" / "PYTEST-A12-WL-E2E" / "A12_RETRACTION_RECEIPT.json")
                   .read_text(encoding="utf-8"))
    assert r["all_clean"] is False
    assert r["results"]["1"]["status"] == "unknown_fetch_error"


# ================================================================ CLI check_citations (một efetch, hai receipt)

_META_OK = {"status": "resolved", "title": "t", "authors": "a", "journal": "j", "year": "2020", "doi": None}


def _chay_cc(monkeypatch, capsys, argv, both):
    monkeypatch.setattr(PubMedClient, "check_citations", lambda self, pmids: both)
    monkeypatch.setattr(sys, "argv", ["check_citations.py", *argv])
    return CC.main(), capsys.readouterr()


@pytest.mark.parametrize("tt", TRANG_THAI_LA)
@pytest.mark.parametrize("json_flag", [[], ["--json"]])
def test_check_citations_rut_bai_trang_thai_la_thoat_1(monkeypatch, capsys, tt, json_flag):
    rc, _ = _chay_cc(monkeypatch, capsys, ["--pmids", "1", *json_flag],
                     {"retraction": {"1": {"status": tt}}, "metadata": {"1": dict(_META_OK)}})
    assert rc == 1


@pytest.mark.parametrize("meta", [{"status": "resolved_partial"}, {"status": None}, None, {}])
def test_check_citations_metadata_chi_resolved_la_sach(monkeypatch, capsys, meta):
    rc, _ = _chay_cc(monkeypatch, capsys, ["--pmids", "1"],
                     {"retraction": {"1": {"status": "ok"}}, "metadata": {"1": meta}})
    assert rc == 1


def test_check_citations_pmid_vang_mat_thoat_1(monkeypatch, capsys):
    rc, _ = _chay_cc(monkeypatch, capsys, ["--pmids", "1,2", "--json"],
                     {"retraction": {"1": {"status": "ok"}}, "metadata": {"1": dict(_META_OK),
                                                                           "2": dict(_META_OK)}})
    assert rc == 1


def test_check_citations_ghi_receipt_khong_sach(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(CCR, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(CCM, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(CC, "REPO_ROOT", tmp_path)
    rc, _ = _chay_cc(monkeypatch, capsys, ["--pmids", "1", "--study", "PYTEST-CC-WL"],
                     {"retraction": {"1": {"status": "rate_limited"}}, "metadata": {"1": dict(_META_OK)}})
    assert rc == 1
    r = json.loads((tmp_path / "exports" / "PYTEST-CC-WL" / "A12_RETRACTION_RECEIPT.json")
                   .read_text(encoding="utf-8"))
    assert r["all_clean"] is False


def test_check_citations_doi_chung_sach_thoat_0(monkeypatch, capsys):
    rc, _ = _chay_cc(monkeypatch, capsys, ["--pmids", "1"],
                     {"retraction": {"1": {"status": "ok"}}, "metadata": {"1": dict(_META_OK)}})
    assert rc == 0


# ================================================================ (3) RetractionChain phòng thủ

@pytest.mark.parametrize("tt", ["rate_limited", None, "", "timeout"])
def test_chuoi_trang_thai_la_hoi_europepmc_roi_chuan_hoa(tt):
    chuoi, pm, ep = _chuoi({"1": {"status": tt, "reason": "gốc"}})
    kq = chuoi.check(["1"])["1"]
    assert ep.called_with == [["1"]], "trạng thái lạ của PubMed phải được hỏi Europe PMC"
    assert kq["status"] == "unknown_fetch_error"
    assert repr(tt) in kq["reason"]
    assert "europepmc" in kq["sources_tried"]


def test_chuoi_trang_thai_la_europepmc_ok_thi_ok_tu_europepmc():
    chuoi, _, _ = _chuoi({"1": {"status": "rate_limited"}}, {"1": {"status": "ok"}})
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "ok"
    assert kq["source"] == "europepmc"


def test_chuoi_ca_hai_nguon_trang_thai_la_van_chuan_hoa():
    chuoi, _, _ = _chuoi({"1": {"status": "rate_limited"}}, {"1": {"status": "weird"}})
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "unknown_fetch_error"


@pytest.mark.parametrize("pm_kq", [{"1": "không phải dict"}, {"1": None}, None, "hỏng", ["1"]])
def test_chuoi_ket_qua_hong_khong_sap_va_fail_closed(pm_kq):
    chuoi, _, ep = _chuoi(pm_kq)
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "unknown_fetch_error"
    assert ep.called_with == [["1"]]


def test_chuoi_europepmc_tra_hong_khong_sap():
    chuoi, _, _ = _chuoi({"1": {"status": "unknown_fetch_error", "reason": "NCBI chặn"}}, "hỏng")
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "unknown_fetch_error"


def test_chuoi_doi_chung_ok_khong_hoi_europepmc():
    chuoi, _, ep = _chuoi({"1": {"status": "ok"}})
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "ok"
    assert ep.called_with == []


def test_chuoi_doi_chung_khong_biet_giu_nguyen_ten():
    """KHONG_BIET đã biết giữ nguyên tên và lý do gốc, không bị gắn nhãn «trạng thái lạ»."""
    chuoi, _, _ = _chuoi({"1": {"status": "unknown_mock_or_no_email", "reason": "thiếu NCBI_EMAIL"}})
    kq = chuoi.check(["1"])["1"]
    assert kq["status"] == "unknown_mock_or_no_email"
    assert "trạng thái lạ" not in kq["reason"]


def test_gop_nhanh_3_chuan_hoa_truc_tiep():
    kq = RetractionChain._gop("1", None, {"status": "rate_limited", "reason": "r"}, None, ["pubmed"])
    assert kq["status"] == "unknown_fetch_error"
    assert "'rate_limited'" in kq["reason"]
