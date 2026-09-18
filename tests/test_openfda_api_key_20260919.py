"""Hồi quy — khoá API openFDA TUỲ CHỌN (OPENFDA_API_KEY), thêm 19/09/2026.

openFDA có 3 nơi gọi `api.fda.gov` (connector FAERS, tra nhãn thuốc, live adapter) và cả ba nay
đi qua MỘT hàm dùng chung `app.sources.openfda.get_json_openfda()` để không nơi nào quên khoá.

Điều cần bảo vệ (mỗi mục có ít nhất một phép đột biến ở đầu-ra đã chạy khi viết test):
  1. có khoá ⇒ MỌI lối gọi đều gửi `api_key`; không khoá ⇒ KHÔNG gửi `api_key` (hành vi cũ);
  2. khoá bị từ chối (401/403) ⇒ cảnh báo RÕ + thử lại KHÔNG khoá — vì `OpenFDAClient.search()`
     nuốt mọi lỗi và trả `[]`, nên nếu không lùi thì khoá gõ nhầm biến luồng đang chạy tốt
     thành «không có tín hiệu» một cách im lặng (họ lỗi BH27/BH08);
  3. chỉ 401/403 mới lùi — 404 («không khớp», drug_interactions dựa vào đó để thử trường kế) và
     5xx phải đi thẳng lên cho nơi gọi, không bị nuốt;
  4. khoá KHÔNG lọt vào log/thông báo lỗi;
  5. live adapter nay thoát dấu `"` trong tên thuốc (bị bỏ sót khỏi task #75/#77).
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.evidence.live_adapters.registry_adapters import OpenFDALiveAdapter  # noqa: E402
from app.integrations.drug_interactions import DrugSafetyChecker  # noqa: E402
from app.sources import openfda as ofda  # noqa: E402
from app.sources.openfda import OpenFDAClient, get_json_openfda  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

KHOA = "KHOA_GIA_DE_TEST_0123456789"


@pytest.fixture(autouse=True)
def _dat_lai_trang_thai(monkeypatch):
    monkeypatch.setattr(ofda, "trang_thai_khoa", None)


def _loi_http(ma: int, url: str = "https://api.fda.gov/drug/label.json") -> requests.HTTPError:
    resp = requests.Response()
    resp.status_code = ma
    resp.url = url
    resp.reason = "Forbidden" if ma == 403 else "Error"
    resp._content = b'{"error": {"code": "API_KEY_INVALID"}}'
    return requests.HTTPError(f"{ma} for url: {url}", response=resp)


class _Http:
    """HttpClient giả: ghi lại params từng lần gọi, và (tuỳ chọn) ném lỗi theo kịch bản."""

    def __init__(self, kich_ban=None, tra_ve=None):
        self.cac_lan: list = []
        self._kich_ban = list(kich_ban or [])
        self._tra_ve = tra_ve if tra_ve is not None else {"results": []}

    def get_json(self, url, params=None, use_cache=True):
        self.cac_lan.append(dict(params or {}))
        if self._kich_ban:
            buoc = self._kich_ban.pop(0)
            if isinstance(buoc, Exception):
                raise buoc
        return self._tra_ve


class TestKhoaDuocGanOMoiLoiGoi:
    def test_helper_co_khoa_thi_gui_api_key(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http()
        get_json_openfda(http, ofda.EVENT, {"search": "x", "limit": 1})
        assert http.cac_lan == [{"search": "x", "limit": 1, "api_key": KHOA}]
        assert ofda.trang_thai_khoa == "chap_nhan"

    def test_helper_khong_khoa_thi_khong_gui_api_key(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", "")
        http = _Http()
        get_json_openfda(http, ofda.EVENT, {"search": "x", "limit": 1})
        assert http.cac_lan == [{"search": "x", "limit": 1}]
        assert "api_key" not in http.cac_lan[0]
        assert ofda.trang_thai_khoa is None  # không có khoá thì không có «trạng thái khoá»

    def test_connector_faers_gui_khoa(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        c = OpenFDAClient()
        c.use_mock = False
        http = _Http()
        c.http = http
        monkeypatch.setattr(c, "save_raw", lambda *a, **k: None)
        c.search("aspirin")
        assert http.cac_lan[0]["api_key"] == KHOA
        assert http.cac_lan[0]["search"] == 'patient.drug.medicinalproduct:"aspirin"'

    def test_connector_faers_khong_khoa_giu_nguyen_hanh_vi_cu(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", "")
        c = OpenFDAClient()
        c.use_mock = False
        http = _Http()
        c.http = http
        monkeypatch.setattr(c, "save_raw", lambda *a, **k: None)
        c.search("aspirin")
        assert "api_key" not in http.cac_lan[0]

    def test_tra_nhan_thuoc_gui_khoa(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http(tra_ve={"results": [{"openfda": {"generic_name": ["aspirin"]}}]})
        DrugSafetyChecker(http=http).fetch_label("aspirin")
        assert http.cac_lan and all(p.get("api_key") == KHOA for p in http.cac_lan)

    def test_live_adapter_gui_khoa_va_thoat_dau_ngoac_kep(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        ad = OpenFDALiveAdapter()
        http = _Http()
        ad.http = http
        ad._lookup_live({"drug_name": 'aspirin" OR patient.patientdeath.patientdeathdate:*'})
        p = http.cac_lan[0]
        assert p["api_key"] == KHOA
        # TRƯỚC bản vá: dấu `"` trần đóng cụm Lucene sớm, phần sau rò ra thành cú pháp truy vấn.
        assert p["search"] == (
            'patient.drug.medicinalproduct:"aspirin\\" OR '
            'patient.patientdeath.patientdeathdate:*"'
        )


class TestKhoaBiTuChoiThiLuiVeKhongKhoa:
    @pytest.mark.parametrize("ma", [401, 403])
    def test_khoa_sai_thi_canh_bao_va_thu_lai_khong_khoa(self, monkeypatch, caplog, ma):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http(kich_ban=[_loi_http(ma)], tra_ve={"results": [{"term": "x", "count": 1}]})
        with caplog.at_level(logging.WARNING):
            kq = get_json_openfda(http, ofda.EVENT, {"search": "x"})
        assert kq == {"results": [{"term": "x", "count": 1}]}   # dữ liệu THẬT vẫn về
        assert len(http.cac_lan) == 2
        assert http.cac_lan[0].get("api_key") == KHOA            # lần 1 có khoá
        assert "api_key" not in http.cac_lan[1]                  # lần 2 KHÔNG khoá
        assert ofda.trang_thai_khoa == "bi_tu_choi"
        assert "OPENFDA_API_KEY" in caplog.text                  # cảnh báo nói rõ biến cần kiểm
        assert KHOA not in caplog.text                           # …mà không lộ giá trị khoá

    def test_khoa_sai_khong_lam_faers_tro_thanh_rong_im_lang(self, monkeypatch):
        """Ca lỗi thật cần tránh: khoá sai + connector nuốt lỗi ⇒ trả [] mà không ai biết."""
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        c = OpenFDAClient()
        c.use_mock = False
        c.http = _Http(kich_ban=[_loi_http(403)],
                       tra_ve={"results": [{"term": "NAUSEA", "count": 7}]})
        monkeypatch.setattr(c, "save_raw", lambda *a, **k: None)
        recs = c.search("aspirin")
        assert len(recs) == 1 and "NAUSEA" in recs[0].title

    @pytest.mark.parametrize("ma", [404, 429, 500, 503])
    def test_ma_loi_khac_di_thang_len_khong_lui(self, monkeypatch, ma):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http(kich_ban=[_loi_http(ma)])
        with pytest.raises(requests.HTTPError) as ei:
            get_json_openfda(http, ofda.EVENT, {"search": "x"})
        assert ei.value.response.status_code == ma
        assert len(http.cac_lan) == 1                           # KHÔNG thử lại
        assert ofda.trang_thai_khoa is None

    def test_404_o_tra_nhan_van_thu_truong_ke_tiep_khi_co_khoa(self, monkeypatch):
        """drug_interactions dựa vào 404 = «trường này không khớp» để thử brand_name — có khoá
        cũng không được làm hỏng hành vi đó (task #77)."""
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http(kich_ban=[_loi_http(404),
                               None],
                     tra_ve={"results": [{"openfda": {"brand_name": ["Lipitor"],
                                                      "generic_name": ["atorvastatin"]}}]})
        nhan = DrugSafetyChecker(http=http).fetch_label("Lipitor")
        assert nhan is not None
        assert len(http.cac_lan) == 2                            # generic 404 → brand khớp
        assert all(p.get("api_key") == KHOA for p in http.cac_lan)

    def test_khoa_bi_tu_choi_roi_khong_khoa_cung_loi_thi_ne_ra_loi_that(self, monkeypatch):
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = _Http(kich_ban=[_loi_http(403), _loi_http(403)])
        with pytest.raises(requests.HTTPError):
            get_json_openfda(http, ofda.EVENT, {"search": "x"})
        assert len(http.cac_lan) == 2


class TestKhoaKhongLotVaoLogHoacLoi:
    def test_httpclient_that_khong_de_lo_khoa_khi_bi_tu_choi(self, monkeypatch, caplog):
        """Đường THẬT (HttpClient + requests.Response thật): ngay cả khi proxy phản hồi 403 kèm
        URL chứa `api_key=<khoá>` ở CẢ HAI lần, khoá không được xuất hiện trong ngoại lệ hay log."""
        monkeypatch.setattr(settings, "openfda_api_key", KHOA)
        http = HttpClient(cache_ttl=0, min_interval=0)

        def _phan_hoi(method, url, params=None, timeout=None, **kw):
            resp = requests.Response()
            resp.status_code = 403
            resp.reason = "Forbidden"
            resp.url = f"{url}?search=x&api_key={KHOA}"
            resp._content = b'{"error": {"code": "API_KEY_INVALID"}}'
            return resp

        monkeypatch.setattr(http.session, "request", _phan_hoi)
        with caplog.at_level(logging.DEBUG):
            with pytest.raises(requests.HTTPError) as ei:
                get_json_openfda(http, ofda.EVENT, {"search": "x"})
        assert KHOA not in str(ei.value)
        assert KHOA not in caplog.text
        assert KHOA not in http.last_error
