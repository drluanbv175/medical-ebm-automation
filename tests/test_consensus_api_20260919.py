"""Hồi quy — connector Consensus API (consensus.app), thêm 19/09/2026.

Tất cả test OFFLINE (mock `http.get_json`, không gọi mạng, không dùng khoá thật). Điều cần bảo vệ:
  1. Thiếu khoá ⇒ NỔ TO trước khi tốn lượt; khoá đi bằng HEADER, không bao giờ trong query/URL/cache key.
  2. Quyết định lưu trữ (bác sĩ, 19/09/2026): KHÔNG lưu abstract/takeaway/full_text_chunks vào bản ghi,
     KHÔNG ghi payload ra đĩa (không save_raw, không cache HTTP đĩa); cache chỉ trong bộ nhớ.
  3. Hạn mức tháng nội bộ FAIL-CLOSED: chạm trần / sổ hỏng / cap≤0 ⇒ RuntimeError, không im lặng trả [].
  4. Lỗi khoá/gói/tham số/hạn mức (400/401/402/403/422/429) nổ to; 5xx/timeout mới trả [] kèm cảnh báo.
  5. Phản hồi không có mảng `results` KHÔNG được đọc thành «0 kết quả».
"""
from __future__ import annotations

import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
import requests

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
    """Cô lập khỏi .env thật + đặt data_dir tạm (sổ đếm/`raw` không chạm dữ liệu thật)."""
    monkeypatch.setattr(settings, "consensus_api_key", "")
    monkeypatch.setattr(settings, "consensus_monthly_call_cap", 20)
    monkeypatch.setattr(settings, "data_dir", tmp_path)
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


class TestThamSo:
    def test_tham_so_chuan(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("Aspirin in CKD", max_results=10, since_date="2026-03-15")
        p = c.cac_lan[0]["params"]
        assert p == {"query": "Aspirin in CKD", "page_size": 10, "medical_mode": "true",
                     "exclude_preprints": "true", "year_min": 2026}
        # boolean phải là CHUỖI thường (đã xác nhận với API thật ở PR ToolUniverse #568)
        assert isinstance(p["medical_mode"], str) and isinstance(p["exclude_preprints"], str)

    def test_khong_since_date_thi_khong_year_min(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x")
        assert "year_min" not in c.cac_lan[0]["params"]

    @pytest.mark.parametrize("yeu_cau,ky_vong", [(500, 20), (20, 20), (7, 7), (0, 1), (-3, 1)])
    def test_page_size_bi_chan_o_tran_goi_free(self, monkeypatch, yeu_cau, ky_vong):
        c = _client(monkeypatch)
        c.search("x", max_results=yeu_cau)
        assert c.cac_lan[0]["params"]["page_size"] == ky_vong

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

    def test_thieu_url_thi_dung_url_doi_thieu_ca_hai_thi_none(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1, url=None), _bai(2, url=None, doi=None)]})
        a, b = c.search("x")
        assert a.url == "https://doi.org/10.1000/x1"
        assert b.url is None and b.doi is None

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

    def test_study_type_cua_consensus_khong_duoc_dung_de_tu_gan_muc(self, monkeypatch):
        """Consensus tự gán `study_type` (AI). Hệ chỉ suy từ tiêu đề/tạp chí — không tin nhãn ngoài (R4)."""
        c = _client(monkeypatch, {"results": [_bai(1, study_type="rct", title="Mot bai binh thuong")]})
        r = c.search("x")[0]
        assert r.study_type == infer_study_type("Mot bai binh thuong", None, "Lancet", None)
        assert "rct" not in json.dumps(r.raw)


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

    def test_loi_ket_noi_tra_rong(self, monkeypatch):
        c = _client(monkeypatch, loi=RuntimeError("Gọi API thất bại sau 4 lần"))
        assert c.search("x") == []

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

    def test_khong_ghi_duoc_so_dem_thi_dung_lai(self, monkeypatch):
        c = _client(monkeypatch)

        def hong(*a, **k):
            raise OSError("dia day")

        monkeypatch.setattr(cs.os, "replace", hong)
        with pytest.raises(RuntimeError, match="không ghi được sổ đếm"):
            c.search("x")
        assert not c.cac_lan

    def test_dong_thoi_khong_bao_gio_vuot_tran(self, monkeypatch):
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

    def test_khac_nam_hoac_co_trang_la_khoa_khac(self, monkeypatch):
        c = _client(monkeypatch)
        c.search("x", since_date="2025-01-01")
        c.search("x", since_date="2026-01-01")
        c.search("x", since_date="2026-01-01", max_results=5)
        assert len(c.cac_lan) == 3

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


class TestKhongGhiDia:
    def test_khong_goi_save_raw_va_khong_tao_thu_muc_raw(self, monkeypatch, tmp_path):
        c = _client(monkeypatch)

        def cam(*a, **k):
            raise AssertionError("consensus KHÔNG được gọi save_raw")

        monkeypatch.setattr(ConsensusClient, "save_raw", cam)
        c.search("aspirin")
        assert not (tmp_path / "raw").exists()
        # chỉ có sổ đếm (số nguyên), không có payload
        tep = sorted(p.name for p in tmp_path.rglob("*") if p.is_file())
        assert tep == ["consensus_quota.json"]


class TestChanDoan:
    def test_chi_ten_truong_va_so_dem_khong_gia_tri(self, monkeypatch):
        c = _client(monkeypatch, {"results": [_bai(1), _bai(2, doi=None)], "page": 0, "is_end": True})
        c.search("aspirin")
        d = c.chan_doan
        assert d["tong_ban_ghi"] == 2 and d["so_ban_ghi_co_doi"] == 1
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
