"""Nhịp riêng cho CORE + minh bạch độ phủ khi cầu dao cắt (30/09/2026).

SỰ CỐ GỐC (data/archive/launchd_weekly.log, lượt weekly_safety.sh 29/09/2026 20:13, run #44): nguồn `core` nhận 3 lần
«429 Client Error: Too Many Requests» liên tiếp ⇒ cầu dao của `sweep_source` cắt 20 truy vấn còn lại (33/53), trong khi
hàng sức khoẻ vẫn `health: ok` (error_rate 3/33 < 20%) nên không ai thấy phần chưa từng được gửi. Đối chiếu cache HTTP
cho thấy trong 30 truy vấn «ok» có 25 lần trúng cache — chỉ 5 request thật trước khi bị 429.

Căn cứ của các con số trong test: docstring `app/sources/core_api.py`, mục «GIỚI HẠN NHỊP» (header thật đo 30/09/2026:
`x-ratelimit-limit: 10`, `x-ratelimit-remaining: 9`, `x-ratelimit-retry-after: 2026-09-30T12:16:23+0000`).

Mọi test OFFLINE: client thật + HttpClient thật + `_throttle` THẬT chạy trên đồng hồ giả (không ngủ thật); máy chủ CORE
giả cài đúng cơ chế cửa sổ token mà tài liệu mô tả; thư mục dữ liệu/cache chuyển sang tmp_path.
"""
from __future__ import annotations

import json
import logging
import math
import sys
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(REPO_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "tools"))

import bao_cao_giam_sat_chi_doc as BC  # noqa: E402

from app.config import CLINICAL_AREAS, Settings, settings  # noqa: E402
from app.services import ingestion as ing  # noqa: E402
from app.sources import core_api  # noqa: E402
from app.sources.base import la_truy_van_cu_phap_pubmed  # noqa: E402
from app.sources.core_api import CoreClient  # noqa: E402
from app.sources.pubmed import PubMedClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import HttpClient, RateLimitHeaders  # noqa: E402

URL = "https://api.core.ac.uk/v3/search/works"
KHU_VUC = list(CLINICAL_AREAS.keys())
KE_HOACH = [(a, q) for a in KHU_VUC for q in CLINICAL_AREAS[a]]
CHU_DE = [(a, q) for a, q in KE_HOACH if not la_truy_van_cu_phap_pubmed(q)]   # CORE gửi
CU_PHAP = [(a, q) for a, q in KE_HOACH if la_truy_van_cu_phap_pubmed(q)]      # CORE bỏ qua có chủ đích
# Năm nhóm đầu của CLINICAL_AREAS: đúng phần mà năm lượt quét trước cùng tối 29/09 đã để lại trong cache HTTP.
KHU_VUC_DA_CACHE = KHU_VUC[:5]
SO_DA_CACHE = sum(len(CLINICAL_AREAS[a]) for a in KHU_VUC_DA_CACHE)
# 20:13:29 giờ VN 29/09/2026 — lúc run #44 bắt đầu gửi request CORE thật.
GOC_GIO = datetime(2026, 9, 29, 13, 13, 29, tzinfo=timezone.utc)
CHINH_SACH = RateLimitHeaders(retry_after="X-RateLimit-Retry-After", remaining="X-RateLimit-Remaining",
                              limit="X-RateLimit-Limit", max_wait=65.0, wait_429_without_hint=60.0)


# ════════════════════════════════════════════════════════════════════════════
# Dụng cụ: cô lập, đồng hồ giả, máy chủ CORE giả
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _co_lap(monkeypatch, tmp_path):
    """Dữ liệu/cache HTTP về tmp_path; trạng thái throttle theo host làm mới; cấu hình nhịp về đúng mặc định của mã
    (máy chạy test có thể đặt biến môi trường riêng).

    `_throttle` CỐ Ý không bị thay bằng hàm rỗng như ở các tệp test khác: giãn cách tối thiểu chính là hành vi được
    kiểm. Thay vào đó `time.sleep` bị CẤM mặc định — test nào gửi request phải dùng `_DongHo` (đồng hồ giả), nên
    không test nào trong tệp này ngủ thật. Vi phạm được kiểm lại lúc dọn fixture vì connector bắt `Exception` quanh
    lời gọi mạng (lỗi ném ở đây có thể bị nuốt)."""
    ngu_that: list = []

    def cam_ngu_that(giay):
        ngu_that.append(giay)
        raise AssertionError(f"test ngủ THẬT {giay} giây — mọi test có gửi request phải dùng _DongHo (đồng hồ giả)")

    monkeypatch.setattr(http_mod.time, "sleep", cam_ngu_that)
    (tmp_path / "du_lieu").mkdir()
    monkeypatch.setattr(settings, "data_dir", tmp_path / "du_lieu")
    (tmp_path / "http_cache").mkdir()
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    monkeypatch.setattr(http_mod, "_last_request_at", {})
    monkeypatch.setattr(http_mod, "_throttle_host_locks", {})
    monkeypatch.setattr(settings, "khoa_qua_proxy", "")
    monkeypatch.setattr(settings, "core_api_key", "KHOA_GIA_CORE")
    monkeypatch.setattr(settings, "http_min_interval", 0.34)
    monkeypatch.setattr(settings, "http_backoff_factor", 1.5)
    monkeypatch.setattr(settings, "http_max_retries", 4)
    monkeypatch.setattr(settings, "http_cache_ttl", 86400)
    monkeypatch.setattr(settings, "core_min_interval", 6.5)
    monkeypatch.setattr(settings, "core_rate_limit_max_wait", 65.0)
    yield
    assert not ngu_that, f"test đã gọi time.sleep thật {ngu_that} — thiếu _DongHo"


class _DongHo:
    """Đồng hồ giả: `time.sleep` không ngủ thật mà đẩy `time.monotonic` đi đúng số giây đã xin."""

    def __init__(self, monkeypatch, bat_dau: float = 1000.0) -> None:
        self.t0 = bat_dau
        self.t = bat_dau
        self.ngu: list = []
        monkeypatch.setattr(http_mod.time, "monotonic", lambda: self.t)
        monkeypatch.setattr(http_mod.time, "sleep", self._ngu)

    def _ngu(self, giay: float) -> None:
        assert giay >= 0, f"time.sleep nhận số âm: {giay}"
        self.ngu.append(giay)
        self.t += giay

    @property
    def da_troi(self) -> float:
        return self.t - self.t0


def _iso(moc: datetime) -> str:
    """Đúng dạng CORE trả thật: cắt phần giây lẻ, múi giờ `+0000`."""
    return moc.strftime("%Y-%m-%dT%H:%M:%S+0000")


def _phan_hoi(status: int, payload: dict, headers: dict, url: str = URL, params: dict = None) -> requests.Response:
    """requests.Response THẬT (raise_for_status() thật sinh đúng chuỗi «429 Client Error: Too Many Requests»)."""
    r = requests.Response()
    r.status_code = status
    r.url = requests.Request("GET", url, params=params).prepare().url
    r.reason = {200: "OK", 429: "Too Many Requests", 503: "Service Unavailable"}.get(status, "")
    r._content = json.dumps(payload).encode("utf-8")
    r.headers["Content-Type"] = "application/json"
    for ten, gia_tri in headers.items():
        r.headers[ten] = gia_tri
    r.encoding = "utf-8"
    return r


class _MayChuCore:
    """Máy chủ CORE giả: cửa sổ token CỐ ĐỊNH `cua_so` giây, mở ở request đầu tiên sau khi cửa sổ trước hết hạn; hết
    `tran` lượt thì mọi request bị 429 tới khi cửa sổ mở lại (tài liệu CORE: «Once this value reaches zero, additional
    requests will be blocked until the window resets»).

    header=False: không gửi header giới hạn nhịp nào. moc_khi_het=False: phản hồi 200 cuối cửa sổ vẫn ghi mốc = bây
    giờ (trạng thái CHƯA quan sát được ở máy chủ thật — test cả hai khả năng)."""

    def __init__(self, dong_ho: _DongHo, *, tran: int, cua_so: float = 60.0, do_tre: float = 1.5,
                 header: bool = True, moc_khi_het: bool = True) -> None:
        self.dong_ho, self.tran, self.cua_so, self.do_tre = dong_ho, tran, cua_so, do_tre
        self.header, self.moc_khi_het = header, moc_khi_het
        self.mo = None
        self.dung = 0
        self.nhat_ky: list = []   # (giây kể từ đầu, truy vấn, mã trạng thái)

    def _gio(self, t: float) -> datetime:
        return GOC_GIO + timedelta(seconds=t - self.dong_ho.t0)

    def _header(self, con_lai: int, moc: float) -> dict:
        h = {"Date": format_datetime(self._gio(self.dong_ho.t).replace(microsecond=0), usegmt=True)}
        if self.header:
            h.update({"X-RateLimit-Limit": str(self.tran), "X-RateLimit-Remaining": str(con_lai),
                      "X-RateLimit-Retry-After": _iso(self._gio(moc))})
        return h

    def request(self, method, url, params=None, timeout=None, **kwargs):
        den = self.dong_ho.t
        self.dong_ho.t += self.do_tre                     # thời gian máy chủ xử lý
        if self.mo is None or den >= self.mo + self.cua_so:
            self.mo, self.dung = den, 0
        het_han = self.mo + self.cua_so
        q = str((params or {}).get("q", ""))
        if self.dung >= self.tran:
            self.nhat_ky.append((round(den - self.dong_ho.t0, 2), q, 429))
            return _phan_hoi(429, {"message": "Too many requests"}, self._header(0, het_han), url, params)
        self.dung += 1
        con_lai = self.tran - self.dung
        self.nhat_ky.append((round(den - self.dong_ho.t0, 2), q, 200))
        moc = het_han if (con_lai == 0 and self.moc_khi_het) else self.dong_ho.t
        return _phan_hoi(200, {"totalHits": 1, "limit": 8, "offset": 0,
                               "results": [{"id": len(self.nhat_ky), "title": f"Bài {len(self.nhat_ky)}"}]},
                         self._header(con_lai, moc), url, params)

    @property
    def so_429(self) -> int:
        return sum(1 for _t, _q, ma in self.nhat_ky if ma == 429)

    @property
    def so_200(self) -> int:
        return sum(1 for _t, _q, ma in self.nhat_ky if ma == 200)


def _core(monkeypatch, may_chu: _MayChuCore) -> CoreClient:
    client = CoreClient()
    client.use_mock = False
    monkeypatch.setattr(client.http.session, "request", may_chu.request)
    return client


def _lam_am_cache(monkeypatch, dong_ho: _DongHo) -> None:
    """Để lại trong cache HTTP đúng phần năm lượt quét trước cùng tối 29/09 đã lấy được (năm nhóm đầu)."""
    am = _core(monkeypatch, _MayChuCore(dong_ho, tran=10_000, do_tre=0.0))
    am.http.min_interval = 0
    _r, logs = ing.sweep_source(am, KHU_VUC_DA_CACHE, max_results_per_query=8, since_date="2026-09-19")
    assert [lg["status"] for lg in logs] == ["ok"] * SO_DA_CACHE


def _hang(logs: list, coverage: dict) -> dict:
    return ing.summarize_source_health(logs, expected_api_sources=["core"], expected_feed_sources=[],
                                       safety_enabled=False, coverage=coverage)["sources"]["core"]


def _khach(dong_ho, phan_hoi: list, **kw) -> tuple:
    """HttpClient thật với phiên trả lần lượt `phan_hoi`; trả (client, danh sách thời điểm máy chủ nhận request)."""
    client = HttpClient(cache_ttl=0, **kw)
    kich_ban, nhan = list(phan_hoi), []

    def request(method, url, params=None, timeout=None, **kwargs):
        nhan.append(round(dong_ho.da_troi, 3))
        assert kich_ban, "hết kịch bản phản hồi mà vẫn bị gọi thêm"
        tao = kich_ban.pop(0)
        return tao() if callable(tao) else tao

    client.session.request = request
    return client, nhan


def _h(dong_ho: _DongHo, *, con_lai=None, sau: float = None, tran: int = 10, moc: str = None) -> dict:
    """Header giới hạn nhịp dựng theo GIỜ MÁY CHỦ (= GOC_GIO + thời gian đã trôi trên đồng hồ giả)."""
    bay_gio = GOC_GIO + timedelta(seconds=dong_ho.da_troi)
    h = {"Date": format_datetime(bay_gio.replace(microsecond=0), usegmt=True), "X-RateLimit-Limit": str(tran)}
    if con_lai is not None:
        h["X-RateLimit-Remaining"] = str(con_lai)
    if moc is not None:
        h["X-RateLimit-Retry-After"] = moc
    elif sau is not None:
        h["X-RateLimit-Retry-After"] = _iso(bay_gio + timedelta(seconds=sau))
    return h


OK = {"totalHits": 0, "results": []}


# ════════════════════════════════════════════════════════════════════════════
# 1. Tái hiện run #44 (HttpClient thật, máy chủ giả) — TRƯỚC và SAU bản vá
# ════════════════════════════════════════════════════════════════════════════

def test_tai_hien_run_44_truoc_ban_va_cau_dao_cat_va_do_phu_lo_ra(monkeypatch, caplog):
    """Đối chứng «TRƯỚC bản vá»: cùng client nhưng ép về nhịp chung 0,34 giây và không đọc header giới hạn nhịp."""
    caplog.set_level(logging.WARNING, logger="app.services.ingestion")
    dong_ho = _DongHo(monkeypatch)
    _lam_am_cache(monkeypatch, dong_ho)
    may_chu = _MayChuCore(dong_ho, tran=5)          # tối 29/09: mỗi cửa sổ chỉ nhận 5 request
    cu = _core(monkeypatch, may_chu)
    cu.http.min_interval = settings.http_min_interval
    cu.http.rate_limit_headers = None
    phu: dict = {}
    _r, logs = ing.sweep_source(cu, KHU_VUC, max_results_per_query=8, since_date="2026-09-19", coverage=phu)

    # Khớp lượt thật: 5 request thật được nhận, rồi 3 truy vấn liên tiếp mỗi truy vấn 2 lần 429 ⇒ cầu dao cắt.
    assert (may_chu.so_200, may_chu.so_429) == (5, 6)
    da_toi = SO_DA_CACHE + 5 + ing._MAX_CONSECUTIVE_ERRORS
    assert len(logs) == da_toi
    assert [lg["status"] for lg in logs[-3:]] == ["error"] * 3
    assert all("429 Client Error: Too Many Requests" in lg["error_message"] for lg in logs[-3:])
    assert not any(la_truy_van_cu_phap_pubmed(q) for _a, q in KE_HOACH[:da_toi]), "tiền đề: chưa tới truy vấn [ta]/[pt]"

    hang = _hang(logs, phu)
    # Đúng điều bác sĩ quan sát: lỗi 3/33 < 20% ⇒ health «ok»; nay hàng có thêm con số phần CHƯA TỪNG được thử.
    assert (hang["requests"], hang["ok"], hang["error"], hang["health"]) == (da_toi, da_toi - 3, 3, "ok")
    assert hang["not_attempted"] == len(CHU_DE) - da_toi
    assert phu["core"]["unreached_skippable"] == len(CU_PHAP)
    assert sum(hang["not_attempted_areas"].values()) == hang["not_attempted"]
    assert set(hang["not_attempted_areas"]) <= set(KHU_VUC[5:]), "phần mất là các chuyên khoa xếp cuối CLINICAL_AREAS"
    # Cấu hình ngày sự cố (53 truy vấn): đúng log «… 20 truy vấn còn lại» = 12 lẽ ra được gửi + 8 vốn không gửi.
    assert (len(KE_HOACH), da_toi, hang["not_attempted"], len(CU_PHAP)) == (53, 33, 12, 8)
    dong = [r.getMessage() for r in caplog.records if "lỗi/chậm liên tiếp" in r.getMessage()]
    assert len(dong) == 1 and "KHÔNG THỬ 20 truy vấn còn lại" in dong[0]
    assert "12 truy vấn lẽ ra được gửi" in dong[0] and "8 truy vấn nguồn này vốn không gửi" in dong[0]


@pytest.mark.parametrize("moc_khi_het", [True, False], ids=["may-chu-neu-moc-khi-het-luot", "chi-neu-moc-o-429"])
def test_tai_hien_run_44_sau_ban_va_gui_het_khong_bi_cat(monkeypatch, moc_khi_het):
    dong_ho = _DongHo(monkeypatch)
    _lam_am_cache(monkeypatch, dong_ho)
    may_chu = _MayChuCore(dong_ho, tran=5, moc_khi_het=moc_khi_het)
    moi = _core(monkeypatch, may_chu)
    assert moi.http.min_interval == 6.5 and moi.http.rate_limit_headers is not None
    phu: dict = {}
    bat_dau = dong_ho.da_troi
    _r, logs = ing.sweep_source(moi, KHU_VUC, max_results_per_query=8, since_date="2026-09-19", coverage=phu)

    assert len(logs) == len(KE_HOACH), "không bị cầu dao cắt"
    assert [lg for lg in logs if lg["status"] == "error"] == []
    hang = _hang(logs, phu)
    assert (hang["requests"], hang["skipped"], hang["error"], hang["not_attempted"]) == (len(CHU_DE), len(CU_PHAP),
                                                                                         0, 0)
    assert "not_attempted_areas" not in hang
    assert may_chu.so_200 == len(CHU_DE) - SO_DA_CACHE, "mọi truy vấn chủ đề chưa có trong cache đều tới máy chủ"
    so_cua_so = math.ceil(may_chu.so_200 / 5)
    if moc_khi_het:
        assert may_chu.so_429 == 0, "máy chủ nêu mốc ngay khi hết lượt ⇒ không request nào bị từ chối"
        assert hang["degraded"] == 0
    else:
        # Máy chủ chỉ nêu mốc ở 429: mỗi lần hết cửa sổ tốn đúng MỘT 429 rồi hồi phục — không thành lỗi, không cắt.
        assert may_chu.so_429 == so_cua_so - 1
        assert hang["degraded"] == so_cua_so - 1
    # Không request nào tới sớm hơn giãn cách tối thiểu 6,5 giây so với request trước đó.
    moc = [t for t, _q, _ma in may_chu.nhat_ky]
    assert min(b - a for a, b in zip(moc, moc[1:])) >= 6.5 - 1e-6
    thoi_gian = dong_ho.da_troi - bat_dau
    assert (so_cua_so - 1) * 60 <= thoi_gian <= so_cua_so * 60 + 30, f"thời gian lượt quét bất thường: {thoi_gian}"


def test_may_chu_khong_gui_header_nao_429_thi_cho_tron_mot_cua_so(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    _lam_am_cache(monkeypatch, dong_ho)
    may_chu = _MayChuCore(dong_ho, tran=5, header=False)
    moi = _core(monkeypatch, may_chu)
    phu: dict = {}
    _r, logs = ing.sweep_source(moi, KHU_VUC, max_results_per_query=8, since_date="2026-09-19", coverage=phu)
    hang = _hang(logs, phu)
    assert len(logs) == len(KE_HOACH) and (hang["error"], hang["not_attempted"]) == (0, 0)
    assert 60.0 in dong_ho.ngu, "429 không có mốc ⇒ chờ trọn một cửa sổ (60 giây), không phải backoff 1,5 giây"
    assert 1.5 not in dong_ho.ngu


def test_nhip_6_5_giay_tu_no_khong_vuot_tran_10_moi_phut(monkeypatch):
    """Trần đo được 30/09 (10 lượt/cửa sổ). Máy chủ KHÔNG gửi header nào ⇒ chỉ còn giãn cách tối thiểu bảo vệ."""
    dong_ho = _DongHo(monkeypatch)
    may_chu = _MayChuCore(dong_ho, tran=10, header=False, do_tre=0.2)
    moi = _core(monkeypatch, may_chu)
    phu: dict = {}
    _r, logs = ing.sweep_source(moi, KHU_VUC, max_results_per_query=8, since_date="2026-09-19", coverage=phu)
    assert may_chu.so_429 == 0 and may_chu.so_200 == len(CHU_DE)
    assert _hang(logs, phu)["not_attempted"] == 0

    # Đối chứng: cũng máy chủ đó, nhịp chung 0,34 giây ⇒ request thứ 11 đã bị từ chối.
    monkeypatch.setattr(http_mod, "_CACHE_DIR", settings.data_dir / "cache_doi_chung")
    (settings.data_dir / "cache_doi_chung").mkdir()
    doi_chung = _MayChuCore(dong_ho, tran=10, header=False, do_tre=0.2)
    cu = _core(monkeypatch, doi_chung)
    cu.http.min_interval = settings.http_min_interval
    ing.sweep_source(cu, KHU_VUC, max_results_per_query=8, since_date="2026-09-19")
    assert doi_chung.so_429 > 0


# ════════════════════════════════════════════════════════════════════════════
# 2. CoreClient: nhịp riêng lấy từ settings, có mặc định an toàn
# ════════════════════════════════════════════════════════════════════════════

def test_core_dung_nhip_rieng_va_chinh_sach_header():
    http = CoreClient().http
    assert http.min_interval == 6.5
    cs = http.rate_limit_headers
    assert (cs.retry_after, cs.remaining, cs.limit) == ("X-RateLimit-Retry-After", "X-RateLimit-Remaining",
                                                        "X-RateLimit-Limit")
    assert (cs.max_wait, cs.wait_429_without_hint, cs.margin) == (65.0, 60.0, 1.0)


def test_nguon_khac_khong_bi_doi_nhip():
    http = PubMedClient().http
    assert http.min_interval == settings.http_min_interval and http.rate_limit_headers is None


def test_mac_dinh_va_bien_moi_truong(monkeypatch):
    monkeypatch.delenv("CORE_MIN_INTERVAL_SECONDS", raising=False)
    monkeypatch.delenv("CORE_RATE_LIMIT_MAX_WAIT_SECONDS", raising=False)
    mac_dinh = Settings()
    assert (mac_dinh.core_min_interval, mac_dinh.core_rate_limit_max_wait) == (6.5, 65.0)
    assert (core_api.KHOANG_CACH_MAC_DINH_GIAY, core_api.TRAN_CHO_MAC_DINH_GIAY) == (6.5, 65.0)
    monkeypatch.setenv("CORE_MIN_INTERVAL_SECONDS", "2.5")
    monkeypatch.setenv("CORE_RATE_LIMIT_MAX_WAIT_SECONDS", "40")
    rieng = Settings()
    assert (rieng.core_min_interval, rieng.core_rate_limit_max_wait) == (2.5, 40.0)
    monkeypatch.setenv("CORE_MIN_INTERVAL_SECONDS", "khong-phai-so")
    assert Settings().core_min_interval == 6.5


@pytest.mark.parametrize("cau_hinh,ky_vong", [
    (2.5, 2.5),                 # khoá hạng 25 lượt/phút: bác sĩ hạ nhịp
    (0.0, 0.34),                # không bao giờ thấp hơn nhịp chung
    (-3.0, 0.34),
    (float("nan"), 6.5),        # NaN lọt vào throttle sẽ tắt giãn cách ⇒ về mặc định an toàn
    (float("inf"), 6.5),
    ("6.5", 6.5),               # sai kiểu (gán tay một chuỗi) ⇒ mặc định
])
def test_khoang_cach_khong_thap_hon_nhip_chung_va_chiu_duoc_gia_tri_hong(monkeypatch, cau_hinh, ky_vong):
    monkeypatch.setattr(settings, "core_min_interval", cau_hinh)
    assert CoreClient().http.min_interval == ky_vong


@pytest.mark.parametrize("tran,ky_vong", [(0.0, None), (-1.0, None), (40.0, 40.0), (float("nan"), 65.0)])
def test_tran_cho_be_hon_hoac_bang_0_la_tat_doc_header(monkeypatch, tran, ky_vong):
    monkeypatch.setattr(settings, "core_rate_limit_max_wait", tran)
    cs = CoreClient().http.rate_limit_headers
    assert (cs.max_wait if cs is not None else None) == ky_vong


# ════════════════════════════════════════════════════════════════════════════
# 3. HttpClient: chờ đúng mốc máy chủ nêu
# ════════════════════════════════════════════════════════════════════════════

def test_doc_dung_dang_moc_core_tra_that():
    """Nguyên văn header đo 30/09/2026 (mốc bằng `Date` khi còn lượt ⇒ 0 giây)."""
    r = _phan_hoi(200, OK, {"Date": "Wed, 30 Sep 2026 12:16:23 GMT", "x-ratelimit-limit": "10",
                            "x-ratelimit-remaining": "9", "x-ratelimit-retry-after": "2026-09-30T12:16:23+0000"})
    nhip = http_mod._read_rate_limit(r, CHINH_SACH)
    assert (nhip["remaining"], nhip["wait"]) == (9, 0.0)
    assert nhip["raw"] == {"X-RateLimit-Limit": "10", "X-RateLimit-Remaining": "9",
                           "X-RateLimit-Retry-After": "2026-09-30T12:16:23+0000"}


_BAY_GIO = datetime(2026, 9, 30, 12, 16, 23, tzinfo=timezone.utc)


@pytest.mark.parametrize("gia_tri,ky_vong", [
    ("2026-09-30T12:17:00+0000", 37.0),            # dạng CORE trả thật
    ("2026-09-30T12:17:00+00:00", 37.0),
    ("2026-09-30T12:17:00Z", 37.0),
    ("2026-09-30T19:17:00+0700", 37.0),            # múi giờ khác, cùng thời điểm
    ("2026-09-30T12:17:00", 37.0),                 # không ghi múi giờ ⇒ coi là UTC
    ("2026-09-30T12:17:00.500+00:00", 37.5),
    ("Wed, 30 Sep 2026 12:17:00 GMT", 37.0),       # HTTP-date
    (str(int(_BAY_GIO.timestamp()) + 37), 37.0),   # epoch giây
    (str((int(_BAY_GIO.timestamp()) + 37) * 1000), 37.0),   # epoch mili-giây
    ("37", 37.0),                                  # số giây tương đối
    ("2026-09-30T12:16:00+0000", -23.0),           # mốc đã qua ⇒ số âm (người gọi coi là «không ở tương lai»)
    ("", None), ("sap-toi", None), ("nan", None), ("inf", None), (None, None),
])
def test_doi_gia_tri_header_thanh_so_giay(gia_tri, ky_vong):
    assert http_mod._seconds_until(gia_tri, _BAY_GIO) == ky_vong


def test_429_cho_toi_dung_moc_may_chu_neu_roi_thu_lai(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="app.utils.http")
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, con_lai=0, sau=37)),
        lambda: _phan_hoi(200, {"ok": True}, _h(dong_ho, con_lai=9, sau=0)),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    assert client.get_json(URL) == {"ok": True}
    assert dong_ho.ngu == [38.0], "37 giây tới mốc + 1 giây lề; KHÔNG phải backoff 1,5 giây"
    assert nhan == [0.0, 38.0]
    assert (client.transient_failure_count, client.failure_count) == (1, 0)
    assert client.paced_wait_seconds == 0.0, "chờ sau 429 là backoff (tín hiệu trục trặc), không phải chờ nhịp chủ động"
    dong = [r.getMessage() for r in caplog.records if "thử lại sau" in r.getMessage()]
    assert len(dong) == 1 and "thử lại sau 38.0s" in dong[0]
    assert "X-RateLimit-Limit=10" in dong[0] and "X-RateLimit-Remaining=0" in dong[0]
    assert "X-RateLimit-Retry-After=2026-09-29T13:14:06+0000" in dong[0]


def test_le_1_giay_bu_cho_header_chi_chinh_xac_toi_giay(monkeypatch):
    """Cửa sổ mở lại ở giây 36,99 nhưng header cắt còn 36 ⇒ không có lề thì tới sớm 0,99 giây và ăn 429 lần nữa."""
    dong_ho = _DongHo(monkeypatch)
    mo_lai = 36.99

    def may_chu():
        if dong_ho.da_troi < mo_lai:
            return _phan_hoi(429, {}, _h(dong_ho, con_lai=0, moc=_iso(GOC_GIO + timedelta(seconds=mo_lai))))
        return _phan_hoi(200, {"ok": True}, _h(dong_ho, con_lai=9, sau=0))

    client, nhan = _khach(dong_ho, [may_chu, may_chu], min_interval=0, rate_limit_headers=CHINH_SACH)
    assert client.get_json(URL) == {"ok": True}
    assert nhan == [0.0, 37.0]


def test_moc_xa_hon_tran_thi_bo_truy_van_ngay_khong_ngu(monkeypatch, caplog):
    """Máy chủ hẹn 600 giây (vd hết hạn mức theo ngày) > trần 65 giây: ngủ tới trần rồi gửi lại chắc chắn vẫn 429."""
    caplog.set_level(logging.WARNING, logger="app.utils.http")
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, con_lai=0, sau=600)),
        lambda: _phan_hoi(200, OK, {}),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    with pytest.raises(requests.HTTPError):
        client.get_json(URL)
    assert nhan == [0.0] and dong_ho.ngu == [], "đúng MỘT request, không ngủ, không gửi lại"
    assert (client.failure_count, client.transient_failure_count) == (1, 0)
    assert client._not_before is None
    assert any("SAU trần chờ 65s" in r.getMessage() for r in caplog.records)
    client.get_json(URL, params={"q": "2"})
    assert nhan == [0.0, 0.0] and client.paced_wait_seconds == 0.0, "truy vấn kế tiếp không bị giữ lại vô ích"


def test_moc_xa_hon_tran_chi_lam_hong_phan_hoi_429(monkeypatch, caplog):
    """Mốc quá trần đi kèm phản hồi KHÔNG phải 429 thì không được biến phản hồi đó thành lỗi: 200 vẫn là thành công
    (chỉ không đặt mốc chờ), 503 vẫn thử lại theo backoff thường."""
    caplog.set_level(logging.WARNING, logger="app.utils.http")
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [
        lambda: _phan_hoi(200, {"ok": 1}, _h(dong_ho, con_lai=0, sau=600)),
        lambda: _phan_hoi(503, {}, _h(dong_ho, con_lai=0, sau=600)),
        lambda: _phan_hoi(200, {"ok": 2}, _h(dong_ho, con_lai=5, sau=0)),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    assert client.get_json(URL) == {"ok": 1}
    assert client._not_before is None and dong_ho.ngu == []
    assert not [r for r in caplog.records if "SAU trần chờ" in r.getMessage()]
    assert client.get_json(URL, params={"q": "2"}) == {"ok": 2}
    assert dong_ho.ngu == [1.5] and nhan == [0.0, 0.0, 1.5]
    assert client.failure_count == 0


@pytest.mark.parametrize("sau,ky_vong_ngu", [(64, [65.0]), (65, [])], ids=["vua-bang-tran-thi-cho", "qua-tran-thi-bo"])
def test_ranh_gioi_tran_cho(monkeypatch, sau, ky_vong_ngu):
    dong_ho = _DongHo(monkeypatch)
    client, _nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, con_lai=0, sau=sau)),
        lambda: _phan_hoi(200, OK, {}),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    if ky_vong_ngu:
        client.get_json(URL)
    else:
        with pytest.raises(requests.HTTPError):
            client.get_json(URL)
    assert dong_ho.ngu == ky_vong_ngu


def test_backoff_khong_bao_gio_tra_vo_cuc():
    """Lưới cuối: dù ai đó gọi thẳng `_backoff_wait` với «mốc quá trần» thì cũng ra một số hữu hạn để ngủ."""
    client = HttpClient(cache_ttl=0, min_interval=0, rate_limit_headers=CHINH_SACH)
    assert client._backoff_wait(0, _phan_hoi(429, {}, {}), math.inf) == 60.0
    assert client._backoff_wait(0, _phan_hoi(429, {}, {}), 12.0) == 12.0


def test_het_han_muc_dai_han_thi_hong_nhanh_roi_cau_dao_cat_khong_treo(monkeypatch):
    """Còn 2 token, cửa sổ mở lại sau 6 giờ (kiểu hạn mức theo NGÀY). Trước khi có nhánh «bỏ ngay», mỗi truy vấn hỏng
    ngủ 65 giây chờ nhịp + 65 giây backoff ⇒ ≈ 6,5 phút mới tới lượt cầu dao; nay ba truy vấn hỏng trong vài giây."""
    dong_ho = _DongHo(monkeypatch)
    may_chu = _MayChuCore(dong_ho, tran=2, cua_so=6 * 3600.0)
    moi = _core(monkeypatch, may_chu)
    phu: dict = {}
    _r, logs = ing.sweep_source(moi, KHU_VUC, max_results_per_query=8, since_date="2026-09-19", coverage=phu)
    assert (may_chu.so_200, may_chu.so_429) == (2, 3), "mỗi truy vấn hỏng chỉ tốn MỘT request"
    assert [lg["status"] for lg in logs] == ["ok", "ok", "error", "error", "error"]
    assert max(dong_ho.ngu) <= 6.5 and dong_ho.da_troi < 60, f"lượt quét bị treo: {dong_ho.da_troi} giây"
    assert phu["core"]["not_attempted"] == len(CHU_DE) - 5


@pytest.mark.parametrize("header_429", [
    {},                                                         # không có header nào
    {"X-RateLimit-Remaining": "0"},                             # thiếu mốc
    {"X-RateLimit-Retry-After": "khong-doc-duoc"},
    "moc-bang-bay-gio",                                         # mốc không ở tương lai (như trạng thái còn lượt)
    "moc-da-qua",
], ids=["khong-header", "thieu-moc", "moc-hong", "moc-bang-bay-gio", "moc-da-qua"])
def test_429_khong_co_moc_dung_duoc_thi_cho_tron_cua_so(monkeypatch, header_429):
    dong_ho = _DongHo(monkeypatch)
    if header_429 == "moc-bang-bay-gio":
        header_429 = _h(dong_ho, con_lai=0, sau=0)
    elif header_429 == "moc-da-qua":
        header_429 = _h(dong_ho, con_lai=0, sau=-30)
    client, _nhan = _khach(dong_ho, [_phan_hoi(429, {}, header_429), _phan_hoi(200, OK, {})],
                           min_interval=0, rate_limit_headers=CHINH_SACH)
    client.get_json(URL)
    assert dong_ho.ngu == [60.0]


def test_chinh_sach_khong_khai_cho_mac_dinh_thi_ve_backoff_cu(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    khong_mac_dinh = RateLimitHeaders(retry_after="X-RateLimit-Retry-After", max_wait=65.0)
    client, _nhan = _khach(dong_ho, [_phan_hoi(429, {}, {}), _phan_hoi(200, OK, {})],
                           min_interval=0, rate_limit_headers=khong_mac_dinh)
    client.get_json(URL)
    assert dong_ho.ngu == [1.5]


def test_client_khong_khai_chinh_sach_giu_nguyen_hanh_vi_cu(monkeypatch):
    """Header riêng của CORE không được đổi cách chờ của nguồn KHÁC; `Retry-After` chuẩn vẫn như cũ (trần 30 giây)."""
    dong_ho = _DongHo(monkeypatch)
    client, _nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, con_lai=0, sau=37)),
        lambda: _phan_hoi(200, OK, _h(dong_ho, con_lai=0, sau=37)),
        lambda: _phan_hoi(200, OK, {}),
        lambda: _phan_hoi(429, {}, {"Retry-After": "600"}),
        lambda: _phan_hoi(200, OK, {}),
    ], min_interval=0)
    client.get_json(URL)
    client.get_json(URL, params={"q": "2"})
    client.get_json(URL, params={"q": "3"})
    assert dong_ho.ngu == [1.5, 30.0]
    assert client.last_rate_limit == {} and client._not_before is None


def test_loi_5xx_cua_nguon_co_chinh_sach_van_backoff_thuong(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    client, _nhan = _khach(dong_ho, [_phan_hoi(503, {}, {}), _phan_hoi(200, OK, {})],
                           min_interval=0, rate_limit_headers=CHINH_SACH)
    client.get_json(URL)
    assert dong_ho.ngu == [1.5], "chính sách chỉ áp cho 429; 5xx không được chờ 60 giây"


def test_dung_gio_may_chu_khong_dung_dong_ho_may_nay(monkeypatch):
    """`Date` của phản hồi là 29/09; đồng hồ máy chạy test là một ngày khác — khoảng chờ vẫn phải đúng 37 + 1 giây."""
    dong_ho = _DongHo(monkeypatch)
    client, _nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, con_lai=0, sau=37)),
        lambda: _phan_hoi(200, OK, {}),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    assert abs((datetime.now(timezone.utc) - GOC_GIO).total_seconds()) > 3600, "tiền đề: hai đồng hồ lệch nhau"
    client.get_json(URL)
    assert dong_ho.ngu == [38.0]


def test_khong_co_date_thi_dung_gio_utc_cua_may(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    moc = _iso(datetime.now(timezone.utc) + timedelta(seconds=40))
    client, _nhan = _khach(dong_ho, [_phan_hoi(429, {}, {"X-RateLimit-Retry-After": moc}),
                                     _phan_hoi(200, OK, {})], min_interval=0, rate_limit_headers=CHINH_SACH)
    client.get_json(URL)
    assert len(dong_ho.ngu) == 1 and 38.0 <= dong_ho.ngu[0] <= 41.0


def test_het_luot_kem_moc_tuong_lai_thi_request_ke_tiep_cho_truoc_khi_gui(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="app.utils.http")
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [
        lambda: _phan_hoi(200, OK, _h(dong_ho, con_lai=0, sau=33)),
        lambda: _phan_hoi(200, OK, _h(dong_ho, con_lai=9, sau=0)),
    ], min_interval=0, rate_limit_headers=CHINH_SACH)
    client.get_json(URL)
    assert dong_ho.ngu == [], "request đã thành công thì không chờ gì thêm trong chính lời gọi đó"
    client.get_json(URL, params={"q": "2"})
    assert nhan == [0.0, 34.0] and dong_ho.ngu == [34.0]
    assert client.paced_wait_seconds == 34.0 and client.health_snapshot()["paced_wait_seconds"] == 34.0
    assert client.transient_failure_count == 0, "chờ trước khi gửi ⇒ không có request nào bị từ chối"
    assert any("chờ 34.0s tới mốc được gọi lại" in r.getMessage() and "X-RateLimit-Remaining=0" in r.getMessage()
               for r in caplog.records)


@pytest.mark.parametrize("header", [
    dict(con_lai=3, sau=33),     # CÒN lượt: mốc ở tương lai cũng không chờ
    dict(con_lai=0, sau=0),      # hết lượt nhưng mốc = bây giờ: không biết chờ bao lâu ⇒ không đoán
    dict(sau=33),                # không có header «còn lại» và không phải 429
], ids=["con-luot", "moc-bang-bay-gio", "khong-biet-con-lai"])
def test_khong_cho_khi_may_chu_khong_noi_ro_da_het_luot_va_bao_gio_mo_lai(monkeypatch, header):
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [lambda: _phan_hoi(200, OK, _h(dong_ho, **header)),
                                    lambda: _phan_hoi(200, OK, {})], min_interval=0, rate_limit_headers=CHINH_SACH)
    client.get_json(URL)
    client.get_json(URL, params={"q": "2"})
    assert nhan == [0.0, 0.0] and dong_ho.ngu == []


def test_sau_429_chot_truy_van_ke_tiep_cho_toi_moc_khong_gui_ngay(monkeypatch):
    """Hai lần 429 liền nhau (truy vấn hỏng). Truy vấn KẾ TIẾP không được bắn ngay — chính kiểu bắn ngay đó làm
    3 truy vấn hỏng liên tiếp ở run #44. Máy chủ ở đây không có header «còn lại»: nhận biết hết lượt qua mã 429."""
    dong_ho = _DongHo(monkeypatch)
    # Máy chủ «điều chỉnh động»: hẹn giây 20, tới nơi lại hẹn tiếp giây 39 (cả hai đều trong trần chờ).
    khong_con_lai = RateLimitHeaders(retry_after="X-RateLimit-Retry-After", max_wait=65.0,
                                     wait_429_without_hint=60.0)
    client, nhan = _khach(dong_ho, [
        lambda: _phan_hoi(429, {}, _h(dong_ho, moc=_iso(GOC_GIO + timedelta(seconds=20)))),
        lambda: _phan_hoi(429, {}, _h(dong_ho, moc=_iso(GOC_GIO + timedelta(seconds=39)))),
        lambda: _phan_hoi(200, {"ok": True}, _h(dong_ho, sau=0)),
    ], min_interval=0, rate_limit_headers=khong_con_lai)
    with pytest.raises(requests.HTTPError):
        client.get_json(URL)                      # thử lại đúng hẹn (giây 21) vẫn 429 ⇒ truy vấn này hỏng
    assert nhan == [0.0, 21.0] and dong_ho.ngu == [21.0]
    assert client.failure_count == 1 and client.paced_wait_seconds == 0.0
    assert client.get_json(URL, params={"q": "2"}) == {"ok": True}
    assert nhan == [0.0, 21.0, 40.0], "chờ tới mốc giây 39 + 1 giây lề rồi mới gửi truy vấn kế tiếp"
    assert client.paced_wait_seconds == 19.0, "lần chờ này là chờ nhịp chủ động (không làm cầu dao coi là chậm)"


def test_gian_cach_toi_thieu_duoc_tinh_la_cho_nhip_chu_dong(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    client, nhan = _khach(dong_ho, [_phan_hoi(200, OK, {})] * 3, min_interval=6.5)
    for i in range(3):
        client.get_json(URL, params={"q": str(i)})
    assert nhan == [0.0, 6.5, 13.0]
    assert client.paced_wait_seconds == 13.0


def test_gia_tri_header_vao_log_da_duoc_lam_sach():
    ban = "0\x1b[31m" + "x" * 200
    nhip = http_mod._read_rate_limit(_phan_hoi(429, {}, {"X-RateLimit-Remaining": ban}), CHINH_SACH)
    gia_tri = nhip["raw"]["X-RateLimit-Remaining"]
    assert len(gia_tri) == 60 and "\x1b" not in gia_tri and nhip["remaining"] is None


@pytest.mark.parametrize("sai", [
    dict(retry_after=""), dict(retry_after="X", max_wait=0), dict(retry_after="X", max_wait=float("nan")),
    dict(retry_after="X", margin=-1), dict(retry_after="X", wait_429_without_hint=-5),
])
def test_chinh_sach_sai_no_to_luc_dung(sai):
    with pytest.raises(ValueError):
        RateLimitHeaders(**sai)


def test_http_client_tu_choi_chinh_sach_sai_kieu():
    with pytest.raises(ValueError):
        HttpClient(cache_ttl=0, rate_limit_headers={"retry_after": "X"})


# ════════════════════════════════════════════════════════════════════════════
# 4. Cầu dao: chờ nhịp chủ động không phải «độ trễ bất thường»
# ════════════════════════════════════════════════════════════════════════════

def _khach_gia(dong_ho: _DongHo, cho_nhip: float, mang: float):
    """Client giả: mỗi truy vấn chờ nhịp `cho_nhip` giây (có ghi vào telemetry) rồi mất `mang` giây cho mạng."""
    da_cho = {"s": 0.0}
    client = SimpleNamespace(name="gia", use_mock=False, endpoint="",
                             http=SimpleNamespace(health_snapshot=lambda: {"paced_wait_seconds": da_cho["s"]}))

    def fetch(c, query, area, max_results, since_date=None):
        da_cho["s"] += cho_nhip
        dong_ho.t += cho_nhip + mang
        return [], dict(source=c.name, status="ok", record_count=0, error_message=None)

    return client, fetch


def test_cho_nhip_chu_dong_khong_lam_cau_dao_cat(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    client, fetch = _khach_gia(dong_ho, cho_nhip=11.5, mang=0.5)      # tổng 12 giây/truy vấn, vượt ngưỡng chậm 10 giây
    _r, logs = ing.sweep_source(client, KHU_VUC, max_results_per_query=8, fetch_fn=fetch)
    assert len(logs) == len(KE_HOACH)


def test_cham_that_van_lam_cau_dao_cat(monkeypatch):
    dong_ho = _DongHo(monkeypatch)
    client, fetch = _khach_gia(dong_ho, cho_nhip=0.5, mang=11.5)      # cùng 12 giây nhưng là mạng chậm thật
    phu: dict = {}
    _r, logs = ing.sweep_source(client, KHU_VUC, max_results_per_query=8, fetch_fn=fetch, coverage=phu)
    assert len(logs) == ing._MAX_CONSECUTIVE_ERRORS
    assert phu["gia"]["not_attempted"] == len(KE_HOACH) - ing._MAX_CONSECUTIVE_ERRORS


def test_nhip_rieng_dai_hon_nguong_cham_khong_tu_cat_chinh_minh(monkeypatch):
    """Bác sĩ đặt CORE_MIN_INTERVAL_SECONDS=12 (> ngưỡng chậm 10 giây): chuỗi thật CoreClient → _fetch → sweep."""
    monkeypatch.setattr(settings, "core_min_interval", 12.0)
    dong_ho = _DongHo(monkeypatch)
    may_chu = _MayChuCore(dong_ho, tran=10, do_tre=1.0)
    client = _core(monkeypatch, may_chu)
    _r, logs = ing.sweep_source(client, KHU_VUC, max_results_per_query=8)
    assert len(logs) == len(KE_HOACH) and may_chu.so_200 == len(CHU_DE)


def test_telemetry_hong_khong_lam_sap_luot_quet():
    hong = SimpleNamespace(name="gia", http=SimpleNamespace(health_snapshot=lambda: 1 / 0))
    la = SimpleNamespace(name="gia", http=SimpleNamespace(health_snapshot=lambda: {"paced_wait_seconds": "abc"}))
    assert ing._paced_seconds(hong) == 0.0 and ing._paced_seconds(la) == 0.0
    assert ing._paced_seconds(SimpleNamespace(name="gia")) == 0.0


# ════════════════════════════════════════════════════════════════════════════
# 5. Độ phủ: `not_attempted` tách khỏi `skipped`, không đổi health/status
# ════════════════════════════════════════════════════════════════════════════

def _quet_theo_mau(client, mau: list) -> tuple:
    luot = iter(mau)

    def fetch(c, query, area, max_results, since_date=None):
        ly_do = ing._ly_do_bo_qua(c, query)
        if ly_do:
            return [], dict(source=c.name, status="skipped", record_count=0, error_message=f"{ly_do}: x")
        return [], dict(source=c.name, status=next(luot, "ok"), record_count=1, error_message="x")

    phu: dict = {}
    _r, logs = ing.sweep_source(client, KHU_VUC, max_results_per_query=8, fetch_fn=fetch, coverage=phu)
    return logs, phu


def test_quet_het_thi_not_attempted_bang_0_va_skipped_giu_nguyen():
    client = CoreClient()
    client.use_mock = False
    logs, phu = _quet_theo_mau(client, [])
    assert phu == {"core": {"not_attempted": 0, "unreached_skippable": 0, "not_attempted_areas": {}}}
    hang = _hang(logs, phu)
    assert (hang["requests"], hang["skipped"], hang["not_attempted"]) == (len(CHU_DE), len(CU_PHAP), 0)


def test_truy_van_nguon_von_khong_gui_khong_bi_tinh_la_mat_do_phu():
    """Cắt sau 3 lỗi đầu: CORE mất 42 truy vấn chủ đề; 8 truy vấn [ta]/[pt] phía sau vốn không gửi ⇒ đếm riêng.
    PubMed hiểu cú pháp đó ⇒ với PubMed cả 50 truy vấn còn lại đều là độ phủ bị mất."""
    core = CoreClient()
    core.use_mock = False
    logs, phu = _quet_theo_mau(core, ["error"] * 3)
    assert len(logs) == 3
    assert (phu["core"]["not_attempted"], phu["core"]["unreached_skippable"]) == (len(CHU_DE) - 3, len(CU_PHAP))
    pubmed = PubMedClient()
    pubmed.use_mock = False
    logs_pm, phu_pm = _quet_theo_mau(pubmed, ["error"] * 3)
    assert (phu_pm["pubmed"]["not_attempted"], phu_pm["pubmed"]["unreached_skippable"]) == (len(KE_HOACH) - 3, 0)
    assert sum(phu_pm["pubmed"]["not_attempted_areas"].values()) == len(KE_HOACH) - 3


def test_loi_lien_tiep_xen_dong_skipped_diem_cat_tinh_dung():
    """Điểm cắt tính theo vị trí trong kế hoạch, không theo số dòng «lỗi»."""
    gia = SimpleNamespace(name="gia", use_mock=False, endpoint="")
    luot = iter(["ok", "error", "skipped", "error", "skipped", "error"])

    def fetch(c, query, area, max_results, since_date=None):
        return [], dict(source=c.name, status=next(luot), record_count=0, error_message="x")

    phu: dict = {}
    _r, logs = ing.sweep_source(gia, KHU_VUC, max_results_per_query=8, fetch_fn=fetch, coverage=phu)
    assert len(logs) == 6 and phu["gia"]["not_attempted"] == len(KE_HOACH) - 6


def _dong(source: str, status: str, n: int = 1, records: int = 0) -> list:
    return [dict(source=source, status=status, record_count=records, error_message=None) for _ in range(n)]


def _loi_ok() -> list:
    return _dong("pubmed", "ok", 2, 5) + _dong("europepmc", "ok", 2, 5) + _dong("crossref", "ok", 2, 5)


def test_not_attempted_chi_la_so_do_khong_doi_health_hay_status():
    logs = _loi_ok() + _dong("core", "ok", 30, 1) + _dong("core", "error", 3)
    api = ["pubmed", "europepmc", "crossref", "core"]
    goc = ing.summarize_source_health(logs, expected_api_sources=api, expected_feed_sources=[], safety_enabled=False)
    phu = {"core": {"not_attempted": 12, "unreached_skippable": 8, "not_attempted_areas": {"Tâm thần": 4}},
           "pubmed": {"not_attempted": 40, "unreached_skippable": 0, "not_attempted_areas": {"Thận": 5}},
           "crossref": {"not_attempted": 0, "unreached_skippable": 0, "not_attempted_areas": {}}}
    moi = ing.summarize_source_health(logs, expected_api_sources=api, expected_feed_sources=[], safety_enabled=False,
                                      coverage=phu)
    assert goc["status"] == moi["status"] == "PASS"
    for khoa in ("hard_fail_reasons", "warnings", "mirror_notices", "degraded_required_sources", "discovery_core",
                 "optional_enhanced_failed"):
        assert goc[khoa] == moi[khoa], khoa
    for ten in api:
        assert moi["sources"][ten]["health"] == goc["sources"][ten]["health"] == "ok"
        assert moi["sources"][ten]["error_rate"] == goc["sources"][ten]["error_rate"]
    assert moi["sources"]["core"]["not_attempted"] == 12
    assert moi["sources"]["core"]["not_attempted_areas"] == {"Tâm thần": 4}
    assert moi["sources"]["pubmed"]["not_attempted"] == 40
    assert moi["sources"]["crossref"]["not_attempted"] == 0 and "not_attempted_areas" not in moi["sources"]["crossref"]
    assert moi["not_attempted_by_source"] == {"core": 12, "pubmed": 40}, "chỉ liệt kê nguồn thật sự bị cắt"
    assert goc["not_attempted_by_source"] == {}


def test_khong_do_thi_khong_hien_thanh_0():
    """Người gọi không truyền độ phủ, hoặc nguồn không đi qua sweep_source (feed) ⇒ hàng KHÔNG có khoá."""
    logs = _loi_ok() + _dong("feed_gina", "ok", 1, 1)
    khong = ing.summarize_source_health(logs, expected_api_sources=["pubmed", "europepmc", "crossref"],
                                        expected_feed_sources=["feed_gina"], safety_enabled=False)
    assert all("not_attempted" not in hang for hang in khong["sources"].values())
    co = ing.summarize_source_health(logs, expected_api_sources=["pubmed", "europepmc", "crossref"],
                                     expected_feed_sources=["feed_gina"], safety_enabled=False,
                                     coverage={"pubmed": {"not_attempted": 0}})
    assert co["sources"]["pubmed"]["not_attempted"] == 0
    assert "not_attempted" not in co["sources"]["feed_gina"] and "not_attempted" not in co["sources"]["europepmc"]


def test_ingest_all_noi_do_phu_tu_sweep_toi_chan_doan(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="app.services.ingestion")

    class _NguonHong:
        name, endpoint, use_mock = "nguon_hong_gia", "http://gia/", False

        def search(self, query, clinical_area=None, max_results=20, since_date=None):
            raise RuntimeError("nguồn sập")

    class _NguonKhoe(_NguonHong):
        name = "nguon_khoe_gia"

        def search(self, query, clinical_area=None, max_results=20, since_date=None):
            return []

    monkeypatch.setattr(ing, "get_enabled_sources", lambda: [_NguonHong(), _NguonKhoe()])
    monkeypatch.setattr("app.sources.rss_feed.get_feed_clients", lambda *a, **k: [])
    monkeypatch.setattr(settings, "enable_openfda", False)
    monkeypatch.setattr(settings, "enable_consensus", False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", False)
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=1, diagnostics=chan_doan)
    mat = len(KE_HOACH) - ing._MAX_CONSECUTIVE_ERRORS
    assert chan_doan["sources"]["nguon_hong_gia"]["not_attempted"] == mat
    assert chan_doan["sources"]["nguon_khoe_gia"]["not_attempted"] == 0
    assert chan_doan["not_attempted_by_source"] == {"nguon_hong_gia": mat}
    dong = [r.getMessage() for r in caplog.records if "Ingestion độ phủ truy vấn" in r.getMessage()]
    assert len(dong) == 1 and f"'nguon_hong_gia': {mat}" in dong[0] and "nguon_khoe_gia" not in dong[0]


def test_khong_nguon_nao_bi_cat_thi_khong_co_dong_canh_bao_do_phu(monkeypatch, caplog):
    caplog.set_level(logging.WARNING, logger="app.services.ingestion")

    class _NguonKhoe:
        name, endpoint, use_mock = "nguon_khoe_gia", "http://gia/", False

        def search(self, query, clinical_area=None, max_results=20, since_date=None):
            return []

    monkeypatch.setattr(ing, "get_enabled_sources", lambda: [_NguonKhoe()])
    monkeypatch.setattr("app.sources.rss_feed.get_feed_clients", lambda *a, **k: [])
    monkeypatch.setattr(settings, "enable_openfda", False)
    monkeypatch.setattr(settings, "enable_consensus", False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", False)
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=1, diagnostics=chan_doan)
    assert chan_doan["not_attempted_by_source"] == {}
    assert not [r for r in caplog.records if "Ingestion độ phủ truy vấn" in r.getMessage()]


# ════════════════════════════════════════════════════════════════════════════
# 6. Báo cáo chỉ-đọc: PASS cũng phải nói ra phần chưa từng được gửi
# ════════════════════════════════════════════════════════════════════════════

def _xuat_gia(ngay):
    ra = {}
    for khoa in BC.TEN_BAO_CAO:
        p = settings.reports_dir / f"{khoa}.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(f"# {khoa}\n", encoding="utf-8", newline="\n")
        ra[khoa] = p
    return ra


def test_bao_cao_chi_doc_neu_truy_van_chua_thu(tmp_path):
    def chay(max_q, ngay):
        return {"source_health": {"status": "PASS", "total_records": 42,
                                  "not_attempted_by_source": {"semantic_scholar": 34, "core": 12}}, "new_items": 5}

    t = BC.chay_bao_cao_chi_doc(tmp_path / "ra", 10, 3, _chay_pipeline=chay, _xuat=_xuat_gia)
    assert t["trang_thai_nguon"] == "PASS" and t["truy_van_chua_thu"] == {"semantic_scholar": 34, "core": 12}
    md = (tmp_path / "ra" / "TOM-TAT.md").read_text(encoding="utf-8")
    assert "CHƯA TỪNG được gửi vì cầu dao cắt" in md and "core 12, semantic_scholar 34" in md
    assert json.loads((tmp_path / "ra" / "tom_tat.json").read_text(encoding="utf-8"))["truy_van_chua_thu"] == {
        "semantic_scholar": 34, "core": 12}


def test_bao_cao_chi_doc_khong_co_gi_bi_cat_thi_khong_them_dong(tmp_path):
    def chay(max_q, ngay):
        return {"source_health": {"status": "PASS", "total_records": 42}, "new_items": 5}

    t = BC.chay_bao_cao_chi_doc(tmp_path / "ra", 10, 3, _chay_pipeline=chay, _xuat=_xuat_gia)
    assert t["truy_van_chua_thu"] == {}
    assert "CHƯA TỪNG được gửi" not in (tmp_path / "ra" / "TOM-TAT.md").read_text(encoding="utf-8")
