"""Hồi quy — connector Consensus API (consensus.app), thêm 19/09/2026 (vòng 2 sau bình duyệt độc lập).

Tất cả test OFFLINE (mock `http.get_json` / adapter giả / máy chủ cục bộ 127.0.0.1, không gọi mạng ngoài,
không dùng khoá thật). Điều cần bảo vệ:
  1. Thiếu khoá ⇒ NỔ TO trước khi tốn lượt; khoá dị dạng (ký tự vô hình) nổ to bằng thông điệp CỐ ĐỊNH và
     không bao giờ vào header/log; khoá đi bằng HEADER, không trong query/URL/cache key, và bị gỡ khi chuyển hướng.
  2. Quyết định lưu trữ (bác sĩ, 19/09/2026): KHÔNG lưu abstract/takeaway/full_text_chunks vào bản ghi,
     KHÔNG ghi payload ra đĩa; cache chỉ trong bộ nhớ.
  3. Hạn mức tháng nội bộ FAIL-CLOSED: chạm trần / sổ hỏng / cap≤0 ⇒ RuntimeError; đếm theo YÊU CẦU THẬT (kể
     cả retry của HttpClient); an toàn đa luồng + đa TIẾN TRÌNH; sổ NGOÀI cây repo.
  4. Lỗi khoá/gói/tham số/hạn mức (400/401/402/403/422/429) nổ to; 5xx/timeout mới trả [] kèm cảnh báo;
     ngoại lệ lạ KHÔNG bị nuốt thành «ok, rỗng».
  5. Phản hồi hỏng (thiếu `results`, mọi dòng vô dụng, không bản nào có DOI) KHÔNG được đọc thành «0 kết quả».
  6. Bản ghi vào kho là ứng viên KHÁM PHÁ có DOI: không tự gán loại thiết kế (không lên Tier A nhờ từ «guideline»
     trong tiêu đề); quét định kỳ bỏ qua nguồn này (Free chỉ 30 lượt/tháng).
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests
import requests.adapters

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.sources import consensus_api as cs  # noqa: E402
from app.sources.classify_meta import infer_study_type  # noqa: E402
from app.sources.consensus_api import ConsensusClient  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

KHOA = "KHOA_GIA_CONSENSUS_0123456789"
TAKEAWAY = "TAKEAWAY_DO_AI_SINH_KHONG_DUOC_LUU"
ABSTRACT = "ABSTRACT_NGUYEN_VAN_KHONG_DUOC_LUU"
CHUNK = "Section: Methods | DOAN_TOAN_VAN_KHONG_DUOC_LUU"


@pytest.fixture(autouse=True)
def _co_lap(monkeypatch, tmp_path):
    """Cô lập khỏi .env thật + đặt data_dir và SỔ ĐẾM vào thư mục tạm (không chạm dữ liệu/sổ thật)."""
    monkeypatch.setattr(settings, "consensus_api_key", "")
    monkeypatch.setattr(settings, "consensus_monthly_call_cap", 20)
    monkeypatch.setattr(settings, "consensus_trong_quet_dinh_ky", False)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    monkeypatch.setattr(settings, "consensus_quota_path", str(tmp_path / "state" / "consensus_quota.json"))
    cs.xoa_bo_nho()
    yield
    cs.xoa_bo_nho()


def _bai(i: int = 1, **thay) -> Dict[str, Any]:
    d = {
        "title": f"Bai thu {i}", "authors": ["A Nguyen", "B Tran"], "publish_year": 2024,
        "journal_name": "Lancet", "publisher_name": "Elsevier", "doi": f"10.1000/x{i}",
        "url": f"https://consensus.app/papers/{i}/", "citation_count": 12,
        "sjr_best_quartile": 1, "abstract": ABSTRACT, "takeaway": TAKEAWAY,
        "full_text_chunks": [CHUNK], "study_type": "rct", "is_preprint": False,
    }
    d.update(thay)
    return d


def _client(monkeypatch, response: Optional[Any] = None, *, loi: Optional[Exception] = None,
            khoa: str = KHOA):
    """Client live; `http.get_json` bị mock — ghi lại từng lần gọi, hoặc ném `loi`."""
    monkeypatch.setattr(settings, "consensus_api_key", khoa)
    c = ConsensusClient()
    c.use_mock = False
    c.cac_lan: List[dict] = []

    def gia(url, params=None, use_cache=True):
        c.cac_lan.append({"url": url, "params": dict(params or {}), "use_cache": use_cache})
        if loi is not None:
            raise loi
        return response if response is not None else {"results": [_bai(1), _bai(2)]}

    monkeypatch.setattr(c.http, "get_json", gia)
    return c


def _loi_http(ma: int) -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = ma
    resp.url = "https://api.consensus.app/v1/search?query=x"
    resp._content = b"{}"
    return requests.HTTPError(f"{ma} for url", response=resp)


class TestKhoaVaTieuDe:
    def test_mock_mode_tra_ban_ghi_gan_nhan_mock(self):
        c = ConsensusClient()
        assert c.use_mock is True
        recs = c.search("atrial fibrillation", clinical_area="Tim mạch")
        assert recs and all(r.source == "consensus" and r.raw.get("_mock") for r in recs)

    def test_thieu_khoa_thi_no_to_va_khong_ton_luot(self, monkeypatch):
        c = ConsensusClient()
        c.use_mock = False
        called = []
        monkeypatch.setattr(c.http, "get_json", lambda *a, **k: called.append(1))
        with pytest.raises(RuntimeError, match="CONSENSUS_API_KEY"):
            c.search("aspirin")
        assert not called
        assert cs.so_lan_goi_thang_nay() == 0

    def test_khoa_di_bang_header_khong_bao_gio_trong_params(self, monkeypatch):
        c = _client(monkeypatch)
        assert c.http.session.headers.get("x-api-key") == KHOA
        c.search("aspirin")
        gui = c.cac_lan[0]
        assert KHOA not in json.dumps(gui)
        assert gui["url"] == "https://api.consensus.app/v1/search"

    def test_khong_co_khoa_thi_khong_co_header(self):
        assert "x-api-key" not in ConsensusClient().http.session.headers

    def test_http_client_khong_cache_dia(self, monkeypatch):
        c = _client(monkeypatch)
        assert c.http.cache_ttl == 0
        assert c.http.min_interval >= 1.0      # 1 yêu cầu/giây trên mọi gói tự phục vụ
        c.search("aspirin")
        assert c.cac_lan[0]["use_cache"] is False

    @pytest.mark.parametrize("khoa_xau", ["KHOA\u200b", "KHOA\u2019XYZ", "khóa", "ab cd", "ab\tcd", "ab\x00cd"])
    def test_khoa_di_bao_no_to_thong_diep_co_dinh_khong_ton_luot(self, monkeypatch, caplog, khoa_xau):
        """Ký tự vô hình/ngoài ASCII (hay dính khi copy từ web) từng làm http.client ném UnicodeEncodeError,
        bị nuốt thành «ok, 0 bản ghi» sau khi đã trừ lượt (phát hiện của bình duyệt độc lập)."""
        c = _client(monkeypatch, khoa=khoa_xau)
        with caplog.at_level("DEBUG"):
            with pytest.raises(RuntimeError, match="ký tự không hợp lệ") as ei:
                c.search("aspirin")
        assert khoa_xau not in str(ei.value) and khoa_xau not in caplog.text
        assert "x-api-key" not in c.http.session.headers      # khoá dị dạng không được nạp vào header
        assert not c.cac_lan and cs.so_lan_goi_thang_nay() == 0

    def test_khoa_co_khoang_trang_hai_dau_duoc_cat(self, monkeypatch):
        c = _client(monkeypatch, khoa=f"  {KHOA}\n")
        assert c.http.session.headers.get("x-api-key") == KHOA
        assert c.search("aspirin")


class TestThamSo:
    def test_tham_so_chuan(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("Aspirin in CKD", max_results=10, since_date="2026-03-15")
        p = c.cac_lan[0]["params"]
        # LUÔN xin trần 20 (1 lượt = 100 bài) rồi cắt ở phía trả về
        assert p == {"query": "Aspirin in CKD", "page_size": 20, "medical_mode": "true",
                     "exclude_preprints": "true", "year_min": 2026}
        # boolean phải là CHUỖI thường (đã xác nhận với API thật ở PR ToolUniverse #568)
        assert isinstance(p["medical_mode"], str) and isinstance(p["exclude_preprints"], str)

    def test_khong_since_date_thi_khong_year_min(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x")
        assert "year_min" not in c.cac_lan[0]["params"]

    @pytest.mark.parametrize("yeu_cau,ky_vong", [(500, 20), (20, 20), (7, 7), (0, 1), (-3, 1)])
    def test_cat_so_ban_ghi_o_phia_tra_ve_khong_doi_page_size(self, monkeypatch, yeu_cau, ky_vong):
        c = _client(monkeypatch, {"results": [_bai(i) for i in range(1, 21)]})
        recs = c.search("x", max_results=yeu_cau)
        assert len(recs) == ky_vong
        assert c.cac_lan[0]["params"]["page_size"] == 20

    def test_since_date_sai_dinh_dang_khong_lam_no(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x", since_date="khong-phai-ngay")
        assert "year_min" not in c.cac_lan[0]["params"]


class TestChiGiuTruongToiThieu:
    def test_khong_luu_abstract_takeaway_toan_van(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1)]})
        recs = c.search("aspirin", clinical_area="Tim mạch")
        assert len(recs) == 1
        r = recs[0]
        assert r.abstract is None
        toan_bo = json.dumps(asdict(r), ensure_ascii=False)
        for cam in (ABSTRACT, TAKEAWAY, CHUNK, "full_text_chunks", "takeaway"):
            assert cam not in toan_bo
        assert set(r.raw) == {"vai_tro", "citation_count", "sjr_quartile"}
        assert r.raw["vai_tro"] == "kham_pha_can_xac_minh_doi"

    def test_anh_xa_truong_co_ban(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, doi="https://doi.org/10.1000/ABC")]})
        r = c.search("aspirin", clinical_area="Tim mạch")[0]
        assert r.source == "consensus" and r.pmid is None
        assert r.authors == "A Nguyen, B Tran"
        assert r.journal_or_organization == "Lancet" and r.publication_date == "2024"
        assert r.doi == "10.1000/ABC"          # bỏ tiền tố URL, giữ nguyên chữ hoa/thường
        assert r.url == "https://consensus.app/papers/1/"
        assert r.clinical_area == "Tim mạch" and r.ingest_query == "aspirin"
        assert r.api_endpoint == cs.SEARCH
        assert r.raw["citation_count"] == 12 and r.raw["sjr_quartile"] == 1

    def test_thieu_url_thi_dung_url_doi(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, url=None)]})
        assert c.search("x")[0].url == "https://doi.org/10.1000/x1"

    def test_bo_qua_bai_khong_tieu_de_va_dong_khong_phai_dict(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, title="  "), "rac", None, _bai(2)]})
        recs = c.search("x")
        assert [r.title for r in recs] == ["Bai thu 2"]

    def test_tac_gia_dang_chuoi_hoac_thieu(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, authors="Nguyen A et al."), _bai(2, authors=None)]})
        a, b = c.search("x")
        assert a.authors == "Nguyen A et al." and b.authors is None

    def test_so_lieu_sai_kieu_khong_lam_no(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, citation_count="nhieu", sjr_best_quartile=True,
                                                   publish_year=None)]})
        r = c.search("x")[0]
        assert r.raw["citation_count"] is None and r.raw["sjr_quartile"] is None
        assert r.publication_date is None

    def test_preprint_duoc_gan_co_ppr_cho_phan_loai(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, is_preprint=True)]})
        r = c.search("x")[0]
        assert r.study_type == infer_study_type("Bai thu 1", None, "Lancet", "PPR")
        assert r.study_type is not None

    def test_is_preprint_dang_chuoi_false_khong_bi_coi_la_preprint(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, is_preprint="false")]})
        assert c.search("x")[0].study_type is None

    @pytest.mark.parametrize("tieu_de", [
        "Commentary on the 2024 guideline recommendations for atrial fibrillation: should therapy change?",
        "A randomized controlled trial of empagliflozin", "Systematic review and meta-analysis of statins",
    ])
    def test_khong_tu_gan_loai_thiet_ke_tu_tieu_de_hay_nhan_cua_consensus(self, monkeypatch, tieu_de):
        c = _client(monkeypatch, {"results": [_bai(1, title=tieu_de, study_type="rct")]})
        r = c.search("x")[0]
        assert r.study_type is None
        assert "rct" not in json.dumps(r.raw)

    def test_khong_len_tier_a_actionable_chi_nho_tu_khoa_trong_tieu_de(self, monkeypatch):
        """Bản ghi Consensus (không abstract) từng lên Tier A + actionable nhờ 'guideline' trong tiêu đề
        (đo bằng normalize→score_item→classify của pipeline thật). Nay phải rơi vào Tier C / watch_only."""
        from app.services.filtering import classify
        from app.services.normalization import normalize
        from app.services.pipeline import score_item
        c = _client(monkeypatch, {"results": [_bai(1, title=(
            "Commentary on the 2024 guideline recommendations for atrial fibrillation: "
            "should first-line therapy change in elderly outpatients?"))]})
        item = normalize(c.search("x")[0])
        score_item(item)
        phan_loai, actionable, _, _ = classify(item)
        assert item["reliability_tier"] != "A"
        assert phan_loai == "watch_only" and actionable is False


class TestDoiBatBuoc:
    def test_bo_ban_ghi_khong_doi_va_dem_trong_chan_doan(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1), _bai(2, doi=None), _bai(3, doi="khong-phai-doi")]})
        recs = c.search("x")
        assert [r.doi for r in recs] == ["10.1000/x1"]
        assert c.chan_doan["so_ban_ghi_bo_vi_thieu_doi"] == 2

    def test_khong_ban_nao_co_doi_thi_no_to_kem_ten_truong(self, monkeypatch):
        """Tài liệu Consensus ghi «Enterprise includes doi» ⇒ gói Free có thể không trả DOI. Không được đọc
        thành «không có gì mới» (BH27) cũng không được nhét ứng viên không truy ngược được vào kho."""
        c = _client(monkeypatch, {"results": [_bai(1, doi=None), _bai(2, doi=None)]})
        with pytest.raises(RuntimeError, match="KHÔNG bản nào có DOI") as ei:
            c.search("x")
        assert "title" in str(ei.value) and ABSTRACT not in str(ei.value)   # chỉ TÊN trường
        assert cs.so_lan_goi_thang_nay() == 1                               # lượt đã tốn được ghi nhận

    @pytest.mark.parametrize("doi_vao,doi_ra", [
        ("doi:10.1000/abc", "10.1000/abc"), ("DOI: 10.1000/abc", "10.1000/abc"),
        ("http://dx.doi.org/10.1000/abc", "10.1000/abc"), (" 10.1000/abc ", "10.1000/abc"),
    ])
    def test_chuan_hoa_doi(self, monkeypatch, doi_vao, doi_ra):
        c = _client(monkeypatch, {"results": [_bai(1, doi=doi_vao)]})
        assert c.search("x")[0].doi == doi_ra


class TestPhanHoiHong:
    def test_thieu_mang_results_thi_no_to_khong_doc_thanh_khong_ket_qua(self, monkeypatch):
        c = _client(monkeypatch, {"loi": "khong co results"})
        with pytest.raises(RuntimeError, match="results"):
            c.search("x")

    def test_results_khong_phai_danh_sach_no_to(self, monkeypatch):
        with pytest.raises(RuntimeError, match="results"):
            _client(monkeypatch, {"results": "rong"}).search("x")

    def test_phan_hoi_khong_phai_dict_no_to(self, monkeypatch):
        with pytest.raises(RuntimeError, match="results"):
            _client(monkeypatch, ["a"]).search("x")

    def test_results_rong_hop_le_tra_rong(self, monkeypatch):
        assert _client(monkeypatch, {"results": []}).search("x") == []

    def test_co_dong_nhung_khong_dong_nao_dung_duoc_thi_no_to(self, monkeypatch):
        """Schema đổi tên `title` ⇒ trước đây thành «ok, 0 bản ghi» im lặng."""
        c = _client(monkeypatch, {"results": [{"paper_title": "T"}, {"paper_title": "T2"}]})
        with pytest.raises(RuntimeError, match="KHÔNG dòng nào dùng được"):
            c.search("x")

    def test_mot_dong_hong_kieu_khong_huy_ca_lo(self, monkeypatch):
        c = _client(monkeypatch, {"results": [
            _bai(1), _bai(2, journal_name={"x": 1}, doi=["10.1/x"], publish_year=2024.0, authors=[{"n": 1}, "A"]),
            _bai(3, publish_year="2023"),
        ]})
        recs = c.search("x")
        assert [r.title for r in recs] == ["Bai thu 1", "Bai thu 3"]      # dòng 2 không DOI hợp lệ ⇒ bỏ
        assert recs[1].publication_date == "2023"

    def test_mot_dong_nem_ngoai_le_thi_bo_dong_do_giu_cac_dong_khac(self, monkeypatch):
        """Vòng bọc từng dòng là lớp phòng thủ cuối (Scopus cũng có): một dòng làm `_mot_dong` ném lỗi
        không được huỷ cả lô đã tốn lượt."""
        goc = cs._mot_dong

        def hong_o_dong_xau(item):
            if isinstance(item, dict) and item.get("title") == "Bai thu 2":
                raise TypeError("dong hong")
            return goc(item)

        monkeypatch.setattr(cs, "_mot_dong", hong_o_dong_xau)
        c = _client(monkeypatch, {"results": [_bai(1), _bai(2), _bai(3)]})
        assert [r.title for r in c.search("x")] == ["Bai thu 1", "Bai thu 3"]

    def test_kieu_du_lieu_la_duoc_ep_chat(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, journal_name=["Lancet"], publish_year=2024.0,
                                                   url="ftp://x", authors=[{"n": 1}, "A", None])]})
        r = c.search("x")[0]
        assert r.journal_or_organization is None
        assert r.publication_date == "2024"          # float nguyên → '2024', không phải '2024.0'
        assert r.url == "https://doi.org/10.1000/x1"  # url không phải http(s) ⇒ dùng url DOI
        assert r.authors == "A"


class TestLoiHttp:
    @pytest.mark.parametrize("ma", [400, 401, 402, 403, 422, 429])
    def test_ma_loi_khoa_goi_tham_so_han_muc_thi_no_to(self, monkeypatch, ma):
        c = _client(monkeypatch, loi=_loi_http(ma))
        with pytest.raises(RuntimeError, match=f"HTTP {ma}"):
            c.search("x")

    @pytest.mark.parametrize("ma", [500, 502, 503, 404])
    def test_ma_loi_khac_tra_rong_kem_canh_bao(self, monkeypatch, ma, caplog):
        c = _client(monkeypatch, loi=_loi_http(ma))
        with caplog.at_level("WARNING"):
            assert c.search("x") == []
        assert f"HTTP {ma}" in caplog.text
        assert KHOA not in caplog.text

    def test_loi_ket_noi_cuoi_cung_cua_httpclient_tra_rong(self, monkeypatch):
        c = _client(monkeypatch, loi=RuntimeError("Gọi API thất bại sau 4 lần"))
        assert c.search("x") == []

    def test_ngoai_le_la_khong_bi_nuot_thanh_ok_rong(self, monkeypatch):
        """UnicodeEncodeError/ValueError… không phải RequestException nên không qua bộ đếm lỗi của
        HttpClient — nuốt chúng = Source Log `ok` + 0 bản ghi. Phải nổ ra ngoài để `_fetch` ghi `error`."""
        c = _client(monkeypatch, loi=ValueError("la"))
        with pytest.raises(ValueError):
            c.search("x")

    def test_khoa_khong_lot_vao_thong_bao_no_to(self, monkeypatch):
        c = _client(monkeypatch, loi=_loi_http(401))
        with pytest.raises(RuntimeError) as ei:
            c.search("x")
        assert KHOA not in str(ei.value)

    def test_http_client_that_khong_de_lo_khoa_qua_header(self, monkeypatch, caplog):
        """Đường THẬT (HttpClient + requests.Response thật): 401 ⇒ khoá không xuất hiện trong lỗi/log."""
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)
        c = ConsensusClient()
        c.use_mock = False

        def phan_hoi(method, url, params=None, timeout=None, **kw):
            r = requests.Response()
            r.status_code = 401
            r.reason = "Unauthorized"
            r.url = f"{url}?query=x"
            r._content = b'{"error": "invalid key"}'
            r.request = requests.Request("GET", r.url, headers=dict(kw.get("headers") or {})).prepare()
            return r

        monkeypatch.setattr(c.http.session, "request", phan_hoi)
        with caplog.at_level("DEBUG"):
            with pytest.raises(RuntimeError) as ei:
                c.search("x")
        assert KHOA not in str(ei.value)
        assert KHOA not in caplog.text
        assert KHOA not in c.http.last_error


class _AdapterDem(requests.adapters.BaseAdapter):
    """Adapter giả ở tầng thấp nhất: đếm từng yêu cầu THẬT mà HttpClient gửi (kể cả retry)."""

    def __init__(self, trang_thai: Optional[int] = None, loi: Optional[Exception] = None):
        super().__init__()
        self.n = 0
        self._trang_thai, self._loi = trang_thai, loi

    def send(self, request, **kw):
        self.n += 1
        if self._loi is not None:
            raise self._loi
        r = requests.Response()
        r.status_code = self._trang_thai
        r.url = request.url
        r._content = b"{}"
        r.request = request
        return r

    def close(self):
        pass


class TestDemYeuCauThat:
    """HttpClient tự retry (429/5xx 1 lần; lỗi kết nối tới `http_max_retries`) nhưng `request_count` chỉ
    đếm mỗi get_json — sổ đếm từng đếm THIẾU tới 5 lần so với yêu cầu thật (bình duyệt độc lập)."""

    def _client_that(self, monkeypatch, adapter):
        monkeypatch.setattr("app.utils.http.time.sleep", lambda s: None)   # bỏ backoff
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)
        c = ConsensusClient()
        c.use_mock = False
        c.http.session.mount("https://", adapter)
        return c

    def test_timeout_lien_tuc_so_dem_bang_so_yeu_cau_that(self, monkeypatch):
        ad = _AdapterDem(loi=requests.Timeout("cham"))
        c = self._client_that(monkeypatch, ad)
        assert c.search("x") == []
        assert ad.n >= 2                                   # có retry thật (test có nghĩa)
        assert cs.so_lan_goi_thang_nay() == ad.n

    def test_5xx_thu_lai_mot_lan_so_dem_bang_hai(self, monkeypatch):
        ad = _AdapterDem(trang_thai=503)
        c = self._client_that(monkeypatch, ad)
        assert c.search("x") == []
        assert ad.n == 2 and cs.so_lan_goi_thang_nay() == 2

    def test_429_nổ_to_va_dem_du_so_yeu_cau(self, monkeypatch):
        ad = _AdapterDem(trang_thai=429)
        c = self._client_that(monkeypatch, ad)
        with pytest.raises(RuntimeError, match="HTTP 429"):
            c.search("x")
        assert cs.so_lan_goi_thang_nay() == ad.n == 2

    def test_thanh_cong_ngay_lan_dau_dem_dung_mot(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x")
        assert cs.so_lan_goi_thang_nay() == 1


class _MayChuGhiHeader(BaseHTTPRequestHandler):
    da_thay: Dict[int, str] = {}
    chuyen_toi: str = ""

    def do_GET(self):  # noqa: N802
        cong = self.server.server_address[1]
        _MayChuGhiHeader.da_thay[cong] = self.headers.get("x-api-key") or ""
        if self.path == "/a":
            self.send_response(302)
            self.send_header("Location", _MayChuGhiHeader.chuyen_toi)
            self.end_headers()
            return
        body = b'{"results": []}'
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):  # im lặng
        pass


class TestKhoaKhongDiTheoChuyenHuong:
    def test_khoa_bi_go_khi_may_chu_chuyen_huong_sang_host_khac(self, monkeypatch):
        """`requests` chỉ gỡ `Authorization` khi đổi host, KHÔNG gỡ header tuỳ biến ⇒ `x-api-key` từng lộ
        sang host đích của chuyển hướng (đo thật bằng hai máy chủ cục bộ)."""
        a, b = HTTPServer(("127.0.0.1", 0), _MayChuGhiHeader), HTTPServer(("127.0.0.1", 0), _MayChuGhiHeader)
        for s in (a, b):
            threading.Thread(target=s.serve_forever, daemon=True).start()
        try:
            cong_a, cong_b = a.server_address[1], b.server_address[1]
            _MayChuGhiHeader.da_thay = {}
            _MayChuGhiHeader.chuyen_toi = f"http://localhost:{cong_b}/b"      # đổi host (127.0.0.1 → localhost)
            monkeypatch.setattr(settings, "consensus_api_key", KHOA)
            c = ConsensusClient()
            c.http.get_json(f"http://127.0.0.1:{cong_a}/a", use_cache=False)
            assert _MayChuGhiHeader.da_thay[cong_a] == KHOA        # host gốc nhận khoá
            assert _MayChuGhiHeader.da_thay[cong_b] == ""          # host đích chuyển hướng KHÔNG nhận
        finally:
            a.shutdown()
            b.shutdown()


class TestHanMucThang:
    def test_moi_lan_goi_that_tang_so_dem_va_ben_qua_client(self, monkeypatch):
        c1 = _client(monkeypatch)
        c1.search("a")
        c1.search("b")
        assert cs.so_lan_goi_thang_nay() == 2
        c2 = _client(monkeypatch)             # client mới, cùng sổ bền
        c2.search("c")
        assert cs.so_lan_goi_thang_nay() == 3

    def test_cham_tran_thi_no_to_truoc_khi_goi_mang(self, monkeypatch):
        monkeypatch.setattr(settings, "consensus_monthly_call_cap", 2)
        c = _client(monkeypatch)
        c.search("a")
        c.search("b")
        with pytest.raises(RuntimeError, match="2/2"):
            c.search("c")
        assert len(c.cac_lan) == 2            # lần thứ 3 KHÔNG chạm mạng
        assert cs.so_lan_goi_thang_nay() == 2

    @pytest.mark.parametrize("tran", [0, -5])
    def test_tran_khong_hoac_am_chan_hoan_toan(self, monkeypatch, tran):
        monkeypatch.setattr(settings, "consensus_monthly_call_cap", tran)
        c = _client(monkeypatch)
        with pytest.raises(RuntimeError, match="CONSENSUS_MONTHLY_CALL_CAP"):
            c.search("x")
        assert not c.cac_lan

    def test_sang_thang_moi_thi_dat_lai(self, monkeypatch):
        monkeypatch.setattr(settings, "consensus_monthly_call_cap", 1)
        monkeypatch.setattr(cs, "_thang_hien_tai", lambda: "2026-09")
        c = _client(monkeypatch)
        c.search("a")
        with pytest.raises(RuntimeError):
            c.search("b")
        monkeypatch.setattr(cs, "_thang_hien_tai", lambda: "2026-10")
        assert cs.so_lan_goi_thang_nay() == 0
        c.search("c")                         # tháng mới ⇒ được gọi lại
        assert cs.so_lan_goi_thang_nay() == 1

    @pytest.mark.parametrize("noi_dung", ["khong phai json", "{}", '{"thang": "2026-09", "so_lan": "5"}',
                                          '{"thang": "2026-09", "so_lan": -1}',
                                          '{"thang": 9, "so_lan": 1}', '[1]'])
    def test_so_dem_hong_thi_no_to_khong_doan(self, monkeypatch, noi_dung):
        path = cs._duong_quota()
        path.parent.mkdir(parents=True)
        path.write_text(noi_dung, encoding="utf-8")
        c = _client(monkeypatch)
        with pytest.raises(RuntimeError, match="sổ đếm"):
            c.search("x")
        assert not c.cac_lan

    def test_loi_5xx_van_ton_luot_dem_thua_con_hon_dem_thieu(self, monkeypatch):
        c = _client(monkeypatch, loi=_loi_http(503))
        assert c.search("x") == []
        assert cs.so_lan_goi_thang_nay() == 1

    def test_khong_ghi_duoc_so_dem_thi_dung_lai_va_khong_de_lai_file_tam(self, monkeypatch):
        c = _client(monkeypatch)

        def hong(*a, **k):
            raise OSError("dia day")

        monkeypatch.setattr(cs.os, "replace", hong)
        with pytest.raises(RuntimeError, match="không ghi được sổ đếm"):
            c.search("x")
        assert not c.cac_lan
        assert not list(cs._duong_quota().parent.glob(".cq-*.tmp"))

    def test_dong_thoi_nhieu_luong_khong_bao_gio_vuot_tran(self, monkeypatch):
        """30 luồng tranh 10 chỗ ⇒ đúng 10 thành công (khoá + ghi nguyên tử)."""
        monkeypatch.setattr(settings, "consensus_monthly_call_cap", 10)
        ket_qua: List[bool] = []
        lock = threading.Lock()

        def thu(_):
            try:
                cs._giu_cho_luot_goi()
                ok = True
            except RuntimeError:
                ok = False
            with lock:
                ket_qua.append(ok)

        with ThreadPoolExecutor(max_workers=16) as pool:
            list(pool.map(thu, range(30)))
        assert sum(ket_qua) == 10
        assert cs.so_lan_goi_thang_nay() == 10

    def test_dong_thoi_nhieu_TIEN_TRINH_khong_mat_luot_va_khong_loi_gia(self, monkeypatch, tmp_path):
        """4 tiến trình Python thật × 15 lần, trần 40: khoá luồng không đủ (đo được: 3 tiến trình × 300 lần
        cấp 497 nhưng sổ chỉ ghi 392, còn 403 RuntimeError giả do đè file tạm cố định)."""
        so_path = tmp_path / "shared" / "consensus_quota.json"
        ma = (
            "import sys\n"
            f"sys.path.insert(0, {str(REPO_ROOT)!r})\n"
            "from app.config import settings\n"
            "from app.sources import consensus_api as cs\n"
            "settings.consensus_quota_path = sys.argv[1]\n"
            "settings.consensus_monthly_call_cap = 40\n"
            "cap = loi_la = 0\n"
            "for _ in range(15):\n"
            "    try:\n"
            "        cs._giu_cho_luot_goi(); cap += 1\n"
            "    except RuntimeError as e:\n"
            "        if 'đã dùng' not in str(e): loi_la += 1\n"
            "print(cap, loi_la)\n"
        )
        cac = [subprocess.Popen([sys.executable, "-c", ma, str(so_path)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True) for _ in range(4)]
        ket_qua = []
        for p in cac:
            out, err = p.communicate(timeout=120)
            assert p.returncode == 0, err
            ket_qua.append(tuple(int(x) for x in out.split()))
        assert sum(c for c, _ in ket_qua) == 40         # đúng bằng trần: không cấp thừa
        assert sum(le for _, le in ket_qua) == 0        # không có lỗi giả do đè file tạm
        monkeypatch.setattr(settings, "consensus_quota_path", str(so_path))
        assert cs.so_lan_goi_thang_nay() == 40          # sổ không mất lượt nào

    def test_so_mac_dinh_nam_ngoai_cay_repo_va_chung_moi_worktree(self, monkeypatch, tmp_path):
        monkeypatch.setattr(settings, "consensus_quota_path", "")
        monkeypatch.setenv("HOME", str(tmp_path / "home"))
        p = cs._duong_quota()
        assert p == tmp_path / "home" / ".ebm-state" / "consensus_quota.json"
        assert REPO_ROOT not in p.parents

    def test_bien_moi_truong_doi_duong_dan_so(self, monkeypatch, tmp_path):
        monkeypatch.setattr(settings, "consensus_quota_path", str(tmp_path / "khac" / "q.json"))
        assert cs._duong_quota() == tmp_path / "khac" / "q.json"


class TestCacheBoNho:
    def test_cung_truy_van_hai_lan_chi_ton_mot_luot(self, monkeypatch):
        c = _client(monkeypatch)
        a = c.search("Aspirin", clinical_area="Tim mạch")
        b = c.search("  aspirin ", clinical_area="Thận")     # cùng truy vấn (chuẩn hoá), khác chuyên khoa
        assert len(c.cac_lan) == 1 and cs.so_lan_goi_thang_nay() == 1
        assert [r.title for r in a] == [r.title for r in b]
        # bản ghi tái dựng theo NGƯỜI GỌI, không rò chuyên khoa/truy vấn của lần trước
        assert a[0].clinical_area == "Tim mạch" and b[0].clinical_area == "Thận"
        assert b[0].ingest_query == "  aspirin "

    def test_khac_nam_la_khoa_khac_nhung_khac_max_results_thi_dung_chung(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x", since_date="2025-01-01")
        c.search("x", since_date="2026-01-01")
        assert len(c.cac_lan) == 2
        c.search("x", since_date="2026-01-01", max_results=5)   # 1 lượt = 100 bài: cùng truy vấn dùng chung
        c.search("x", since_date="2026-01-01", max_results=12)
        assert len(c.cac_lan) == 2 and cs.so_lan_goi_thang_nay() == 2

    def test_het_han_thi_goi_lai(self, monkeypatch):
        gio = [1000.0]
        monkeypatch.setattr(cs, "_dong_ho", lambda: gio[0])
        c = _client(monkeypatch)
        c.search("x")
        gio[0] += cs._TTL_BO_NHO_GIAY - 1
        c.search("x")
        assert len(c.cac_lan) == 1
        gio[0] += 2
        c.search("x")
        assert len(c.cac_lan) == 2

    def test_cache_khong_giu_abstract_va_khoa_cache_khong_chua_khoa_api(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("aspirin")
        with cs._khoa_bo_nho:
            noi_dung = json.dumps([[list(k), v] for k, v in cs._BO_NHO.items()], default=str)
        for cam in (ABSTRACT, TAKEAWAY, CHUNK, KHOA):
            assert cam not in noi_dung

    def test_loi_khong_duoc_cache(self, monkeypatch):
        c = _client(monkeypatch, loi=_loi_http(503))
        c.search("x")
        c.search("x")
        assert len(c.cac_lan) == 2

    def test_hai_luong_cung_truy_van_cung_luc_chi_ton_mot_luot(self, monkeypatch):
        """Single-flight: trước đây cache trống + hai luồng đồng thời ⇒ 2 lần gọi HTTP + 2 lượt."""
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)
        c = ConsensusClient()
        c.use_mock = False
        so_lan: List[int] = []
        rao = threading.Barrier(2)

        def cham(url, params=None, use_cache=True):
            so_lan.append(1)
            threading.Event().wait(0.3)
            return {"results": [_bai(1)]}

        monkeypatch.setattr(c.http, "get_json", cham)

        def chay(_):
            rao.wait()
            return c.search("Heart Failure")

        with ThreadPoolExecutor(max_workers=2) as pool:
            a, b = list(pool.map(chay, range(2)))
        assert len(so_lan) == 1 and cs.so_lan_goi_thang_nay() == 1
        assert [r.title for r in a] == [r.title for r in b] == ["Bai thu 1"]


class TestKhongGhiDia:
    def test_khong_goi_save_raw_va_khong_tao_thu_muc_raw(self, monkeypatch, tmp_path):
        c = _client(monkeypatch)

        def cam(*a, **k):
            raise AssertionError("consensus KHÔNG được gọi save_raw")

        monkeypatch.setattr(ConsensusClient, "save_raw", cam)
        c.search("aspirin")
        assert not (tmp_path / "raw").exists()
        # chỉ có sổ đếm (số nguyên) + file khoá, không có payload, không sót file tạm
        tep = sorted(p.name for p in tmp_path.rglob("*") if p.is_file())
        assert tep == ["consensus_quota.json", "consensus_quota.lock"]


class TestChanDoan:
    def test_chi_ten_truong_va_so_dem_khong_gia_tri(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1), _bai(2, doi=None)], "page": 0, "is_end": True})
        c.search("aspirin")
        d = c.chan_doan
        assert d["tong_ban_ghi"] == 2 and d["so_ban_ghi_co_doi"] == 1
        assert d["so_ban_ghi_bo_vi_thieu_doi"] == 1 and d["so_dong_bo_vi_sai_dinh_dang"] == 0
        assert "doi" in d["truong_ban_ghi_dau"] and "takeaway" in d["truong_ban_ghi_dau"]
        assert set(d["truong_goc"]) == {"is_end", "page", "results"}
        toan_bo = json.dumps(d, ensure_ascii=False)
        for cam in (ABSTRACT, TAKEAWAY, CHUNK, "Bai thu", "10.1000"):
            assert cam not in toan_bo

    def test_chan_doan_phan_hoi_la_la_khong_no(self):
        assert cs._chan_doan(None) == {}
        assert cs._chan_doan({"results": None})["tong_ban_ghi"] is None


class TestDangKyNguon:
    def test_mac_dinh_tat(self):
        from app.sources import get_enabled_sources
        assert all(s.name != "consensus" for s in get_enabled_sources())

    def test_bat_thi_co_mat(self, monkeypatch):
        from app.sources import get_enabled_sources
        monkeypatch.setattr(settings, "enable_consensus", True)
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)
        assert "consensus" in [s.name for s in get_enabled_sources()]

    def test_co_trong_ban_do_test_live(self):
        from app.main import _build_source_map
        assert _build_source_map()["consensus"] is ConsensusClient

    def test_ingestion_ghi_nhan_loi_nguon_khi_cham_tran(self, monkeypatch):
        """Nối vào pipeline thật: chạm trần ⇒ Source Log `error` (không phải `ok` + 0 bản ghi)."""
        from app.services.ingestion import _fetch
        monkeypatch.setattr(settings, "consensus_monthly_call_cap", 1)
        c = _client(monkeypatch)
        recs, log = _fetch(c, "aspirin", "Tim mạch", 10)
        assert recs and log["status"] == "ok"
        recs2, log2 = _fetch(c, "warfarin", "Tim mạch", 10)
        assert recs2 == [] and log2["status"] == "error"
        assert "1/1" in log2["error_message"]

    def test_ingestion_ghi_error_khi_ngoai_le_la_thay_vi_ok_rong(self, monkeypatch):
        from app.services.ingestion import _fetch
        c = _client(monkeypatch, loi=ValueError("la"))
        recs, log = _fetch(c, "aspirin", "Tim mạch", 10)
        assert recs == [] and log["status"] == "error"


class TestQuetDinhKy:
    """Free chỉ 30 lượt/tháng: lượt quét ~53 truy vấn cạn trần 20 ở vài chuyên khoa ĐẦU và không bao giờ
    chạm tới các chuyên khoa sau. Mặc định quét định kỳ BỎ QUA Consensus; dossier/tài liệu nền vẫn dùng."""

    class _NguonKhac:
        name = "khac"

    def test_mac_dinh_quet_dinh_ky_bo_qua_consensus_nhung_giu_nguon_khac(self, monkeypatch):
        from app.services.ingestion import chon_nguon_quet_dinh_ky
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)
        c, khac = ConsensusClient(), self._NguonKhac()
        assert c.chi_theo_yeu_cau is True
        assert chon_nguon_quet_dinh_ky([khac, c]) == [khac]

    def test_bat_co_trong_quet_dinh_ky_thi_gom_lai(self, monkeypatch):
        from app.services.ingestion import chon_nguon_quet_dinh_ky
        monkeypatch.setattr(settings, "consensus_trong_quet_dinh_ky", True)
        c = ConsensusClient()
        assert c.chi_theo_yeu_cau is False
        assert chon_nguon_quet_dinh_ky([c]) == [c]

    def test_ingest_all_that_khong_goi_consensus(self, monkeypatch):
        """Đi qua ingest_all thật (DB tạm): nguồn Consensus bật nhưng KHÔNG bị gọi, sổ đếm vẫn 0."""
        from app.services import ingestion
        c = _client(monkeypatch)
        monkeypatch.setattr(ingestion, "get_enabled_sources", lambda: [c])
        monkeypatch.setattr(settings, "enable_openfda", False)
        monkeypatch.setattr(ingestion, "sweep_source",
                            lambda client, *a, **k: pytest.fail(f"sweep_source bị gọi cho {client.name}"))
        from app.database import init_db
        init_db()
        ingestion.ingest_all(max_results_per_query=1, areas=[])
        assert not c.cac_lan and cs.so_lan_goi_thang_nay() == 0


class TestTestLive:
    def test_test_live_consensus_bao_chan_doan_khong_lo_khoa(self, monkeypatch):
        from app.main import cmd_test_live
        monkeypatch.setattr(settings, "consensus_api_key", KHOA)

        def gia(self, url, params=None, use_cache=True):
            return {"results": [_bai(1)], "page": 0}

        monkeypatch.setattr(HttpClient, "get_json", gia)
        out = cmd_test_live(source="consensus", query="aspirin")
        cd = out["consensus_chan_doan"]
        assert cd["so_lan_goi_thang_nay"] == 1 and cd["tran_noi_bo"] == 20
        assert cd["so_ban_ghi_co_doi"] == 1 and "doi" in cd["truong_ban_ghi_dau"]
        assert out["count"] == 1 and out["results"][0]["is_mock"] is False
        assert KHOA not in json.dumps(out, ensure_ascii=False)
