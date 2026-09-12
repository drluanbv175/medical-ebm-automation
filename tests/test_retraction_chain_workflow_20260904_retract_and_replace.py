# -*- coding: utf-8 -*-
"""Hồi quy phát hiện HIGH của audit đối kháng 2026-09-04: cờ `retract_and_replace`
trong `app/sources/retraction_chain.py::_gop()` KHÔNG BAO GIỜ bật khi nguồn báo
"retracted" là PubMed hoặc Europe PMC — chỉ RẤT TÌNH CỜ bật khi Retraction Watch
(ngoại tuyến, làm mới 30 ngày/lần) có sẵn ĐÚNG cụm từ trong `reason`.

Nguyên nhân gốc, xác nhận bằng đọc mã + gọi thẳng `_gop()`:
  `la_rut_va_thay((rw or {}).get("reason", ""), kq.get("notice_title", ""),
                  kq.get("reason", ""))`
`kq` khi thắng ở nhánh PubMed/Europe PMC là `pm`/`ep` — CẢ HAI đều KHÔNG BAO GIỜ
ghi khoá "notice_title" hay "reason" cho trạng thái "retracted" (chỉ ghi
"retraction_notice": {"pmid":..., "citation":...}, một chuỗi trích dẫn THÔ không
mang tiêu đề). Hai trong ba tham số truyền cho la_rut_va_thay() vì thế là DEAD
CODE vĩnh viễn khi PubMed/Europe PMC là nguồn thắng — cờ chỉ còn phụ thuộc HOÀN
TOÀN vào rw.reason, và im lặng tắt (không phải False, mà là VẮNG MẶT hoàn toàn
khỏi kết quả) ngay khi RW chưa có/không dùng đúng cụm từ cho PMID đó.

Vá: tra thêm TIÊU ĐỀ của chính thông báo rút bài (PMID riêng) qua
`PubMedClient.fetch_metadata()` (đã có sẵn, dùng cho A12 metadata) và
`EuropePMCClient.fetch_notice_titles()` (mới thêm, cùng khuôn) — đúng cách
`crossref_retraction.py` đã làm THÀNH CÔNG cho DOI. status "retracted" vẫn luôn
đúng/fail-closed dù có vá hay không — bản vá chỉ phục hồi CÂU CHỮ phân biệt
"rút bỏ hẳn" với "rút rồi đăng lại bản đã sửa".
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.sources.europepmc import EuropePMCClient  # noqa: E402
from app.sources.retraction_chain import RetractionChain  # noqa: E402


class _FakeRW:
    def __init__(self, ready: bool = False, data: dict | None = None) -> None:
        self._ready = ready
        self._data = data or {}

    def san_sang(self) -> bool:
        return self._ready

    def tra(self, pmid: str):
        return self._data.get(pmid)


class _FakeClient:
    """Giả lập PubMedClient/EuropePMCClient — nay thêm fetch_metadata() (chỉ
    PubMed có thật) để test được nhánh tra tiêu đề thông báo mới thêm. Ghi lại
    lời gọi để test xác nhận ĐÃ HỎI ĐÚNG PMID thông báo, không chỉ kết quả cuối."""

    def __init__(self, responses: dict, metadata: dict | None = None,
                 notice_titles: dict | None = None) -> None:
        self._responses = responses
        self._metadata = metadata or {}
        self._notice_titles = notice_titles or {}
        self.called_with: list[list[str]] = []
        self.metadata_called_with: list[list[str]] = []
        self.notice_titles_called_with: list[list[str]] = []

    def check_retraction_status(self, pmids):
        self.called_with.append(list(pmids))
        return {p: self._responses[p] for p in pmids if p in self._responses}

    def fetch_metadata(self, pmids):
        self.metadata_called_with.append(list(pmids))
        return {p: self._metadata[p] for p in pmids if p in self._metadata}

    def fetch_notice_titles(self, pmids):
        self.notice_titles_called_with.append(list(pmids))
        return {p: self._notice_titles[p] for p in pmids if p in self._notice_titles}


def _retracted_with_notice(notice_pmid: str) -> dict:
    return {"status": "retracted",
            "retraction_notice": {"pmid": notice_pmid, "citation": "J Med. 2026;1:1"}}


def _ok() -> dict:
    return {"status": "ok"}


def _resolved_title(title: str) -> dict:
    return {"status": "resolved", "title": title}


class TestCoDoThangBiVoHieuHoaTruocBanVa:
    """★★ Ca chính, đúng nguyên văn phát hiện: PubMed báo "retracted" nhưng RW
    KHÔNG có bản ghi (PMID chưa được RW crawl) — trước bản vá, cờ sẽ IM LẶNG
    không bao giờ bật. Test này khoá HÀNH VI MỚI: tra thêm tiêu đề thông báo."""

    def test_pubmed_thang_rw_vang_mat_van_bat_duoc_co_qua_fetch_metadata(self):
        pubmed = _FakeClient(
            {"30267080": _retracted_with_notice("31021386")},
            metadata={"31021386": _resolved_title(
                "Notice of Retraction and Replacement. Choi JY, et al. "
                "Association of Antiviral Therapy With Hepatocellular Carcinoma "
                "Risk.")},
        )
        europepmc = _FakeClient({})
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        result = chain.check(["30267080"])

        assert result["30267080"]["status"] == "retracted"
        assert result["30267080"]["retract_and_replace"] is True
        assert pubmed.metadata_called_with == [["31021386"]]

    def test_khong_co_rw_khong_co_tieu_de_thi_khong_bat_co_gia(self):
        """Đối chứng BẮT BUỘC: không nguồn nào cho tiêu đề → cờ KHÔNG được bịa
        thành True. status vẫn 'retracted' (fail-closed nguyên vẹn) — chỉ thiếu
        phần câu chữ, không phải thiếu an toàn."""
        pubmed = _FakeClient(
            {"11111111": _retracted_with_notice("22222222")}, metadata={},
        )
        europepmc = _FakeClient({}, notice_titles={})
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        result = chain.check(["11111111"])

        assert result["11111111"]["status"] == "retracted"
        assert "retract_and_replace" not in result["11111111"]


class TestFallbackEuropePMCKhiPubMedKhongTraTieuDe:
    def test_pubmed_khong_giai_duoc_thi_hoi_europepmc(self):
        pubmed = _FakeClient(
            {"33333333": _retracted_with_notice("44444444")}, metadata={},  # metadata trống -> unresolved
        )
        europepmc = _FakeClient(
            {}, notice_titles={"44444444": "Retraction and replacement of the above article"},
        )
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        result = chain.check(["33333333"])

        assert result["33333333"]["retract_and_replace"] is True
        assert europepmc.notice_titles_called_with == [["44444444"]]

    def test_pubmed_da_giai_duoc_thi_khong_hoi_europepmc_them(self):
        """Đã có tiêu đề từ PubMed rồi thì KHÔNG cần hỏi Europe PMC nữa — tránh
        gọi mạng thừa (đúng nguyên tắc 'chỉ tốn thêm MỘT lời gọi' đã ghi trong
        crossref_retraction.py)."""
        pubmed = _FakeClient(
            {"55555555": _retracted_with_notice("66666666")},
            metadata={"66666666": _resolved_title("Retract and replace notice")},
        )
        europepmc = _FakeClient({}, notice_titles={"66666666": "should not be used"})
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        chain.check(["55555555"])

        assert europepmc.notice_titles_called_with == []


class TestKhongTraThuaChoPmidKhongRut:
    def test_khong_hoi_tieu_de_thong_bao_cho_pmid_status_ok(self):
        """Chỉ hỏi tiêu đề khi ĐÃ có tín hiệu rút bài thật — PMID 'ok' không
        được kích hoạt lệnh gọi mạng thừa nào."""
        pubmed = _FakeClient({"77777777": _ok()})
        europepmc = _FakeClient({})
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        chain.check(["77777777"])

        assert pubmed.metadata_called_with == []
        assert europepmc.notice_titles_called_with == []

    def test_khong_hoi_khi_retracted_nhung_khong_co_notice_pmid(self):
        """retraction_notice tồn tại nhưng không có "pmid" (vd chỉ có citation
        thô) — không có gì để tra, không được gọi fetch_metadata với PMID rỗng."""
        pubmed = _FakeClient(
            {"88888888": {"status": "retracted",
                          "retraction_notice": {"pmid": None, "citation": "x"}}},
        )
        europepmc = _FakeClient({})
        chain = RetractionChain(rw=_FakeRW(ready=False), pubmed=pubmed, europepmc=europepmc)

        chain.check(["88888888"])

        assert pubmed.metadata_called_with == []


class TestDoiChungRetractionWatchVanHoatDongNhuCu:
    """Regression: đường CŨ (RW cung cấp reason có sẵn cụm từ) vẫn phải hoạt
    động y nguyên sau bản vá — bản vá chỉ THÊM đường mới, không được thay thế
    đường cũ đang đúng."""

    def test_rw_co_reason_van_bat_co_nhu_truoc(self):
        rw = _FakeRW(ready=True, data={
            "30267080": {"status": "retracted", "nature": "Retraction",
                        "retraction_date": "2019-04-25",
                        "reason": "Error in Data; Retract and Replace;"},
        })
        pubmed = _FakeClient({"30267080": _ok()})
        europepmc = _FakeClient({})
        chain = RetractionChain(rw=rw, pubmed=pubmed, europepmc=europepmc)

        result = chain.check(["30267080"])

        assert result["30267080"]["source"] == "retraction_watch"
        assert result["30267080"]["retract_and_replace"] is True


class TestGopTrucTiepVoiNoticeTitles:
    """Kiểm _gop() ở mức đơn vị (không qua check()) — khớp đúng repro đã dùng
    khi điều tra phát hiện: gọi thẳng hàm gộp với notice_titles đã tra sẵn."""

    def test_notice_titles_duoc_doc_dung_theo_notice_pmid(self):
        pm = {"status": "retracted",
              "retraction_notice": {"pmid": "99999999", "citation": "x"}}
        ra = RetractionChain._gop(
            "30267080", rw=None, pm=pm, ep=None, da_thu=["pubmed"],
            notice_titles={"99999999": "Notice of Retraction and Replacement"},
        )
        assert ra["retract_and_replace"] is True

    def test_notice_titles_rong_khong_gay_loi_tuong_thich_nguoc(self):
        """Không truyền notice_titles (mặc định None) không được lỗi — hợp
        đồng cũ (trước khi thêm tham số) phải còn gọi được."""
        pm = {"status": "retracted",
              "retraction_notice": {"pmid": "1", "citation": "x"}}
        ra = RetractionChain._gop("p", rw=None, pm=pm, ep=None, da_thu=["pubmed"])
        assert ra["status"] == "retracted"
        assert "retract_and_replace" not in ra


class TestFetchNoticeTitlesEuropePMC:
    """Đơn vị cho hàm mới `EuropePMCClient.fetch_notice_titles()` — không gọi
    mạng thật, mock `http.get_json` để đọc query gửi đi và trả kết quả giả."""

    def test_mock_mode_tra_ve_rong_khong_gay_loi(self):
        client = EuropePMCClient()
        assert client.use_mock is True
        assert client.fetch_notice_titles(["12345678"]) == {}

    def test_danh_sach_rong_tra_ve_rong(self):
        client = EuropePMCClient()
        client.use_mock = False
        assert client.fetch_notice_titles([]) == {}

    def test_khong_co_pmid_hop_le_khong_goi_mang(self, monkeypatch):
        client = EuropePMCClient()
        client.use_mock = False
        goi_mang = {"count": 0}

        def fake_get_json(*a, **kw):
            goi_mang["count"] += 1
            return {"resultList": {"result": []}}

        monkeypatch.setattr(client.http, "get_json", fake_get_json)
        ra = client.fetch_notice_titles(["not-a-pmid", "1) OR (SRC:PPR"])
        assert ra == {}
        assert goi_mang["count"] == 0, "PMID toàn không hợp lệ thì không được gọi mạng"

    def test_doc_dung_tieu_de_tu_ket_qua_that(self, monkeypatch):
        client = EuropePMCClient()
        client.use_mock = False
        captured: dict = {}

        def fake_get_json(url, params=None, **kwargs):
            captured["query"] = params["query"]
            return {"resultList": {"result": [
                {"pmid": "31021386", "title": "Notice of Retraction and Replacement"},
                {"pmid": "99999999"},  # thiếu title -> phải bị bỏ qua, không KeyError
            ]}}

        monkeypatch.setattr(client.http, "get_json", fake_get_json)
        ra = client.fetch_notice_titles(["31021386", "99999999"])
        assert ra == {"31021386": "Notice of Retraction and Replacement"}
        assert captured["query"] == "(EXT_ID:31021386 OR EXT_ID:99999999) AND SRC:MED"

    def test_loi_mang_tra_ve_rong_khong_nem_ngoai_le(self, monkeypatch):
        client = EuropePMCClient()
        client.use_mock = False

        def fake_get_json(*a, **kw):
            raise RuntimeError("mất mạng")

        monkeypatch.setattr(client.http, "get_json", fake_get_json)
        assert client.fetch_notice_titles(["12345678"]) == {}


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
