"""Kiểm connector Consensus (`app/sources/consensus_api.py`, lớp `ConsensusClient`) — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT) và các SỰ KIỆN API đọc từ docs.consensus.app ngày
20/09/2026, KHÔNG đọc mã connector, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

Consensus là tầng DỰ PHÒNG số 1 của bậc thang (không tham gia quét song song). Các quy tắc được canh chặt:

  * `GET https://api.consensus.app/v1/search`, khoá đi ở HEADER `x-api-key` (KHÔNG BAO GIỜ ở params/URL); request chỉ
    gồm `query`, `page_size = min(max_results, 20)`, `medical_mode=true`, `exclude_preprints=true`, `year_min` — không
    `page >= 1`, không `include_full_text_chunks`, không `study_types` hay tính năng trả phí khác (sẽ ra HTTP
    403 ở gói Free);
  * ĐÚNG MỘT request HTTP cho mỗi `search()` trên MỌI đường (thành công lẫn mọi lỗi) — `HttpClient(max_retries=0)`;
  * lỗi được phân loại vào `loai` của một `RuntimeError`: thieu_key, key_sai (401), thanh_toan_qua_han (402),
    tinh_nang_khong_cho_phep (403), het_quota (429 "used all included searches"), gioi_han_toc_do (429 "Too many
    requests"), tham_so_sai (422), het_ngan_sach (ngân sách nội bộ), phan_hoi_khong_hop_le, khac. Năm loại đầu
    (không kể thieu_key/gioi_han_toc_do/tham_so_sai...) là lỗi CHỐT: bậc thang dừng tầng đó — được kiểm cả ở đây (phân
    loại) lẫn ở cầu nối với `chay_du_phong_ingest` (hành vi dừng);
  * `takeaway` là kết luận do AI của Consensus viết: KHÔNG phải abstract, KHÔNG phải chứng cứ — chỉ nằm ở `raw`;
    nhãn `study_type` của Consensus chỉ nằm ở `raw`, không bao giờ nâng `RawRecord.study_type` (chỉ `is_preprint` =>
    "preprint");
  * ngân sách gọi: bộ đếm THÁNG bền vững (tệp JSON trạng thái, ghi nguyên tử, sống qua khởi động lại, sang tháng lịch
    thì về 0, tệp hỏng => coi như chạm trần và NỔ TO) + bộ đếm theo TIẾN TRÌNH cho mỗi lượt chạy; lượt trúng cache
    HTTP được hoàn lại cho cả hai; lượt lỗi trước khi Consensus tính (401/402/403/422/lỗi mạng) không tính vào
    tháng; 429 "hết quota" đặt bộ đếm tháng về đúng trần;
  * khoá không bao giờ lọt ra log, exception, RawRecord, tệp `save_raw`, cache HTTP hay tệp trạng thái ngân sách;
    truy vấn có PII và truy vấn cú pháp PubMed không bao giờ được gửi.

Mọi test OFFLINE (socket bị chặn): chạy NGUYÊN lớp `HttpClient` thật (retry, cache, telemetry, che secret) nhưng
`session.request` của instance bị thay bằng bản giả. Dữ liệu là DỮ LIỆU GIẢ RÕ RÀNG (DOI tiền tố 10.5555, ví dụ
example-*.org) — KHÔNG phải bài báo thật. Khoá giả `SENTINEL_CONSENSUS_KEY_0123` được rải khắp nơi để chứng minh nó
không rò ra đâu cả. Trạng thái theo TIẾN TRÌNH được reset bằng `importlib.reload` (mô phỏng "khởi động lại"), còn tệp
trạng thái tháng nằm trong thư mục tạm của test (`settings.data_dir`) nên không đụng dữ liệu thật của bác sĩ.

KHÔNG có test nào gọi consensus.app thật; các điều KHÔNG kiểm chứng được (điều khoản lưu trữ/cache kết quả, hình dạng
thân 422, định dạng header retry-after, `publish_date` có luôn ISO không, cách Consensus gán `study_type`) được ghi ở
`docs`, không được giả định ở đây.
"""
from __future__ import annotations

import contextlib
import datetime as _dt
import importlib
import json
import logging
import re
import socket
import sys
import time
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.sources as sources_pkg  # noqa: E402
import app.sources.consensus_api as consensus_mod  # noqa: E402
from app.config import CLINICAL_AREAS, Settings, settings  # noqa: E402
from app.core.policy_engine import contains_pii_text  # noqa: E402
from app.services.fallback_ladder import chay_du_phong_ingest  # noqa: E402
from app.services.fallback_verification import KetQuaXacMinh  # noqa: E402
from app.services.filtering import classify  # noqa: E402
from app.services.normalization import normalize  # noqa: E402
from app.services.pipeline import score_item  # noqa: E402
from app.sources.base import RawRecord, SourceClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

CLE_SENTINEL = "SENTINEL_CONSENSUS_KEY_0123"
ENDPOINT = "https://api.consensus.app/v1/search"

LOAI_HOP_LE = {
    "thieu_key", "key_sai", "thanh_toan_qua_han", "tinh_nang_khong_cho_phep", "het_quota", "gioi_han_toc_do",
    "tham_so_sai", "het_ngan_sach", "phan_hoi_khong_hop_le", "khac",
}
LOAI_CHOT = {"key_sai", "thanh_toan_qua_han", "tinh_nang_khong_cho_phep", "het_quota", "het_ngan_sach"}
# Tham số request được phép theo hợp đồng: không gì khác (page>=1, full text, study_types... đều bị cấm).
THAM_SO_DUOC_PHEP = {"query", "page_size", "medical_mode", "exclude_preprints", "year_min"}
KHOA_THAM_SO_KHOA = {"api_key", "apikey", "key", "token", "access_token", "x-api-key", "x_api_key"}

_DATETIME_THAT = _dt.datetime
_DATE_THAT = _dt.date

# Thân 429 theo tài liệu (hai loại khác nhau, cách xử lý khác nhau).
MSG_HET_QUOTA = "You have used all included searches for this month."
MSG_QUA_NHANH = "Too many requests. Please slow down."


# ════════════════════════════════════════════════════════════════════════════
# Môi trường cô lập + phản hồi giả + helper dùng chung
# ════════════════════════════════════════════════════════════════════════════

def _rebind_lop_da_nap_lai() -> None:
    """Sau `importlib.reload` lớp trong module là lớp MỚI: trỏ `app.sources.ConsensusClient` về nó để các file test
    khác (đi qua `sources_pkg.ConsensusClient`) và `get_fallback_sources()` cùng thấy MỘT lớp duy nhất."""
    modul = importlib.reload(consensus_mod)
    if getattr(sources_pkg, "ConsensusClient", None) is not None:
        sources_pkg.ConsensusClient = modul.ConsensusClient


@pytest.fixture(autouse=True)
def moi_truong(monkeypatch, tmp_path):
    """Live-mode tường minh (không phụ thuộc `.env`), ngân sách rất lớn, dữ liệu vào thư mục tạm, không mạng, không ngủ thật."""
    for khoa, gia_tri in dict(
        consensus_api_key="", enable_consensus=False, enable_serpapi_scholar=False,
        consensus_max_calls_per_month=10 ** 6, consensus_max_calls_per_run=10 ** 6,
        consensus_lookback_years=10, use_mock_sources=True,
        fallback_min_trusted=3, fallback_min_evidence=60, fallback_keep_unverified=False,
        enable_scite_verification=True,
    ).items():
        monkeypatch.setattr(settings, khoa, gia_tri)
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    ngu: List[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: ngu.append(float(s)))

    def _cam(*_a, **_k):
        raise AssertionError("test connector KHÔNG được mở kết nối mạng")

    monkeypatch.setattr(socket.socket, "connect", _cam)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam)
    yield SimpleNamespace(ngu=ngu)
    # Trả trần về rất lớn rồi nạp lại module: bộ đếm theo tiến trình về 0, không nhiễm chéo giữa các test.
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 10 ** 6)
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 10 ** 6)
    _rebind_lop_da_nap_lai()


class _JsonHong:
    """Đánh dấu thân phản hồi HTTP 200 mà `.json()` không parse được."""


JSON_HONG = _JsonHong()


class _PhanHoiGia:
    """Giả `requests.Response`: `raise_for_status()` nhúng URL ĐẦY ĐỦ như requests thật."""

    def __init__(self, status_code: int, body: Any, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        self.status_code = status_code
        self._body = body
        self.text = "<html>khong phai json</html>" if isinstance(body, _JsonHong) else json.dumps(
            body, ensure_ascii=False, default=str)
        self.headers: Dict[str, str] = dict(headers or {})
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Client Error: reason for url: {self.url}")
            err.response = self  # type: ignore[assignment]
            raise err

    def json(self) -> Any:
        if isinstance(self._body, _JsonHong):
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._body


def _hit(xoa: Tuple[str, ...] = (), **ghi_de: Any) -> Dict[str, Any]:
    """Một phần tử `results[]` dựng theo trường tài liệu Consensus (dữ liệu GIẢ, DOI tiền tố test 10.5555)."""
    hit: Dict[str, Any] = {
        "title": "Effect of fake drug on fake outcome: a synthetic consensus test paper",
        "authors": ["Alice Nguyen", "Bob Tran"],
        "journal_name": "Journal of Synthetic Testing",
        "publisher_name": "Example Publisher",
        "publish_year": 2023,
        "publish_date": "2023-05-01",
        "doi": "10.5555/consensus.test.001",
        "url": "https://example-journal.org/articles/consensus-test-001",
        "abstract": "Background: synthetic. Results: hazard ratio 0.80 (95% CI 0.70-0.90). Conclusion: synthetic.",
        "pages": "1-10",
        "volume": "12",
        "citation_count": 42,
        "semantic_score": 0.91,
        "study_type": "rct",
        "takeaway": "Consensus AI takeaway: the fake drug clearly works in everyone.",
        "sjr_best_quartile": 1,
        "sample_size": 300,
        "study_count": 1,
        "population_type": "adults",
        "is_preprint": False,
        "countries_of_study": ["Vietnam"],
        "study_duration_days": 365,
        "influential_citation_count": 5,
        "institutions": ["Example University"],
    }
    hit.update(ghi_de)
    for khoa in xoa:
        hit.pop(khoa, None)
    return hit


def _phan_hoi(*hits: Any, **them: Any) -> Dict[str, Any]:
    body: Dict[str, Any] = {"results": list(hits), "page": 0, "is_end": True, "page_size": 20, "next_page": None}
    body.update(them)
    return body


def _tra(status: int, body: Any, headers: Optional[Dict[str, str]] = None) -> Callable[[Any], Any]:
    return lambda goi: _PhanHoiGia(status, body, goi.full_url, headers)


def _tra_thanh_cong(*hits: Any) -> Callable[[Any], Any]:
    return _tra(200, _phan_hoi(*(hits or (_hit(),))))


def _loi_mang(goi: Any) -> Any:
    raise requests.ConnectionError(
        "HTTPSConnectionPool(host='api.consensus.app', port=443): Max retries exceeded (Caused by "
        "NewConnectionError('giả lập mất mạng'))")


def _loi_timeout(goi: Any) -> Any:
    raise requests.Timeout("Read timed out. (read timeout=30)")


def _theo_thu_tu(*cac_kich_ban: Callable[[Any], Any]) -> Callable[[Any], Any]:
    """Lần gọi thứ n dùng kịch bản thứ n (kịch bản cuối lặp lại)."""
    def _chon(goi):
        return cac_kich_ban[min(goi.so_thu_tu, len(cac_kich_ban)) - 1](goi)
    return _chon


def _gop_tham_so(url: str, params: Any) -> Tuple[str, Dict[str, str]]:
    """Tách URL thành (nền, tham số gộp) để test không phụ thuộc connector nhét query vào URL hay vào `params`."""
    p = urlsplit(url)
    gop: Dict[str, str] = dict(parse_qsl(p.query, keep_blank_values=True))
    for k, v in dict(params or {}).items():
        gop[str(k)] = str(v)
    return f"{p.scheme}://{p.netloc}{p.path}", gop


def _cai_phien_gia(client: Any, kich_ban: Callable[[Any], Any]) -> SimpleNamespace:
    """Thay `session.request` CỦA INSTANCE (giữ nguyên header mặc định trên session) bằng bản giả ghi lại lời gọi."""
    phien = client.http.session
    ghi = SimpleNamespace(calls=[])

    def request(method, url, params=None, timeout=None, **extra):
        header = {str(k).lower(): str(v) for k, v in dict(phien.headers).items()}
        header.update({str(k).lower(): str(v) for k, v in dict(extra.get("headers") or {}).items()})
        nen, tham_so = _gop_tham_so(url, params)
        full = f"{nen}?{urlencode(tham_so)}" if tham_so else nen
        goi = SimpleNamespace(
            so_thu_tu=len(ghi.calls) + 1, method=method, url=url, base=nen, params=tham_so, headers=header,
            extra={k: v for k, v in extra.items() if k != "headers"}, full_url=full)
        ghi.calls.append(goi)
        return kich_ban(goi)

    phien.request = request  # type: ignore[method-assign]
    return ghi


def _client(monkeypatch, tmp_path, kich_ban: Optional[Callable[[Any], Any]] = None, *, cache: bool = False,
            key: str = CLE_SENTINEL, nap_lai: bool = True) -> Tuple[Any, SimpleNamespace]:
    """Client live dùng HttpClient THẬT với session giả. `nap_lai=True` mô phỏng một TIẾN TRÌNH mới (bộ đếm theo
    tiến trình về 0; tệp trạng thái tháng vẫn còn)."""
    monkeypatch.setattr(settings, "consensus_api_key", key)
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    if nap_lai:
        _rebind_lop_da_nap_lai()
    client = consensus_mod.ConsensusClient()
    client.use_mock = False
    client.http.cache_ttl = 3600 if cache else 0
    client.http.min_interval = 0
    ghi = _cai_phien_gia(client, kich_ban or _tra_thanh_cong())
    return client, ghi


def _chay(client: Any, *args: Any, **kwargs: Any) -> Tuple[Optional[List[RawRecord]], Optional[BaseException]]:
    """Chạy search() và tách (kết quả, ngoại lệ) để phân loại hành vi."""
    try:
        return client.search(*args, **kwargs), None
    except Exception as exc:  # noqa: BLE001 - test cần phân loại MỌI ngoại lệ
        return None, exc


def _khang_dinh_loi_phan_loai(loi: BaseException) -> str:
    assert isinstance(loi, RuntimeError), f"lỗi connector phải là RuntimeError, nhận {type(loi).__name__}: {loi}"
    loai = getattr(loi, "loai", None)
    assert loai in LOAI_HOP_LE, f"loai={loai!r} không nằm trong các lớp lỗi của hợp đồng"
    assert str(loi).strip(), "thông báo lỗi không được rỗng"
    return loai


def _ro_hoac_rong_co_canh_bao(client: Any, caplog: Any, *args: Any, **kwargs: Any) -> Optional[str]:
    """Tình huống MƠ HỒ/hỏng: hoặc ném lỗi phân loại, hoặc trả [] KÈM dấu vết (cảnh báo hoặc failure_count) —
    không bao giờ trả [] IM LẶNG ('im lặng khác an toàn') và không bao giờ trả bản ghi."""
    caplog.set_level(logging.DEBUG)
    ket_qua, loi = _chay(client, *args, **kwargs)
    if loi is not None:
        return _khang_dinh_loi_phan_loai(loi)
    assert ket_qua == []
    co_canh_bao = any(r.levelno >= logging.WARNING for r in caplog.records)
    co_that_bai = client.http.health_snapshot().get("failure_count", 0) > 0
    assert co_canh_bao or co_that_bai, "trả [] mà không có cảnh báo hay failure_count nào — kiểu rỗng im lặng cần tránh"
    return None


def _mot_ban_ghi(monkeypatch, tmp_path, hit: Dict[str, Any], **kwargs: Any) -> RawRecord:
    client, _ = _client(monkeypatch, tmp_path, _tra_thanh_cong(hit))
    recs = client.search("chronic kidney disease", **kwargs)
    assert len(recs) == 1, f"kỳ vọng 1 bản ghi, nhận {len(recs)}"
    return recs[0]


def _noi_dung_moi_tep(thu_muc: Path) -> List[Tuple[Path, str]]:
    ra: List[Tuple[Path, str]] = []
    if thu_muc.exists():
        for p in sorted(thu_muc.rglob("*")):
            if p.is_file():
                ra.append((p, p.read_text(encoding="utf-8", errors="replace")))
    return ra


def _duyet(obj: Any, duong: Tuple[str, ...] = ()) -> Iterator[Tuple[Tuple[str, ...], Any]]:
    """Duyệt đệ quy dict/list, trả (đường-dẫn-khoá, giá-trị-lá)."""
    if isinstance(obj, dict):
        for khoa, gia_tri in obj.items():
            yield from _duyet(gia_tri, duong + (str(khoa),))
    elif isinstance(obj, (list, tuple)):
        for i, gia_tri in enumerate(obj):
            yield from _duyet(gia_tri, duong + (str(i),))
    else:
        yield duong, obj


def _kiem_khong_ro_khoa(client: Any, caplog: Any, loi: Optional[BaseException], goc: Path) -> None:
    """Khoá không được lọt vào log, exception (cả chuỗi nguyên nhân + traceback), telemetry hay MỌI tệp đã ghi."""
    assert CLE_SENTINEL not in caplog.text
    assert CLE_SENTINEL not in json.dumps(client.http.health_snapshot(), default=str)
    if loi is not None:
        e: Optional[BaseException] = loi
        da_thay = set()
        while e is not None and id(e) not in da_thay:
            da_thay.add(id(e))
            assert CLE_SENTINEL not in str(e) and CLE_SENTINEL not in repr(e)
            assert all(CLE_SENTINEL not in str(a) for a in e.args)
            assert CLE_SENTINEL not in str(getattr(getattr(e, "response", None), "url", ""))
            e = e.__cause__ or e.__context__
        dau_vet = "".join(traceback.format_exception(type(loi), loi, loi.__traceback__))
        assert CLE_SENTINEL not in dau_vet
    for duong, noi_dung in _noi_dung_moi_tep(goc):
        assert CLE_SENTINEL not in noi_dung, f"khoá lọt vào tệp {duong.name}"


_RAW_PAYLOAD = re.compile(r"^\d{8}T\d+")


def _ung_vien_tep_trang_thai(goc: Path) -> List[Path]:
    """Các tệp JSON KHÔNG phải cache HTTP, không phải payload `save_raw` (tên bắt đầu bằng dấu thời gian)."""
    ra: List[Path] = []
    for p in sorted(goc.rglob("*")):
        if not p.is_file() or p.suffix != ".json":
            continue
        if "http_cache" in p.parts or "_http_cache" in p.parts or _RAW_PAYLOAD.match(p.name):
            continue
        ra.append(p)
    return ra


def _tep_trang_thai(goc: Path) -> Path:
    ung_vien = _ung_vien_tep_trang_thai(goc)
    if len(ung_vien) > 1:
        ung_vien = [p for p in ung_vien if "consensus" in p.name.lower()] or ung_vien
    assert len(ung_vien) == 1, (
        f"không tìm thấy đúng MỘT tệp trạng thái ngân sách tháng dưới settings.data_dir: {ung_vien}. Tệp phải nằm dưới "
        "settings.data_dir để test cô lập được (và để test không ghi đè bộ đếm thật của bác sĩ)")
    return ung_vien[0]


@contextlib.contextmanager
def _thoi_diem(nam: int, thang: int, ngay: int = 15) -> Iterator[None]:
    """Đóng băng đồng hồ tại `nam-thang-ngay 12:00` (datetime/date/time). Phải nạp lại module TRONG khối này để các
    tên `from datetime import ...` của connector trỏ vào lớp giả."""
    that_dt, that_date = _DATETIME_THAT, _DATE_THAT
    epoch = that_dt(nam, thang, ngay, 12, 0, 0).timestamp()
    that_localtime, that_gmtime, that_strftime = time.localtime, time.gmtime, time.strftime

    class _DatetimeGia(that_dt):  # type: ignore[misc, valid-type]
        @classmethod
        def now(cls, tz=None):
            return cls(nam, thang, ngay, 12, 0, 0, tzinfo=tz)

        @classmethod
        def utcnow(cls):
            return cls(nam, thang, ngay, 12, 0, 0)

        @classmethod
        def today(cls):
            return cls(nam, thang, ngay, 12, 0, 0)

    class _DateGia(that_date):  # type: ignore[misc, valid-type]
        @classmethod
        def today(cls):
            return cls(nam, thang, ngay)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(_dt, "datetime", _DatetimeGia)
        mp.setattr(_dt, "date", _DateGia)
        mp.setattr(time, "time", lambda: epoch)
        mp.setattr(time, "localtime", lambda s=None: that_localtime(epoch if s is None else s))
        mp.setattr(time, "gmtime", lambda s=None: that_gmtime(epoch if s is None else s))
        mp.setattr(time, "strftime", lambda fmt, *a: that_strftime(fmt, *(a or (that_localtime(epoch),))))
        yield


# ════════════════════════════════════════════════════════════════════════════
# Danh tính, cấu hình và đăng ký (HỢP ĐỒNG mục 4 + 6)
# ════════════════════════════════════════════════════════════════════════════

def test_client_identity_name_endpoint_and_http_client():
    client = consensus_mod.ConsensusClient()
    assert consensus_mod.ConsensusClient.name == "consensus"
    assert consensus_mod.ConsensusClient.endpoint == ENDPOINT
    assert isinstance(client, SourceClient)
    assert isinstance(client.http, HttpClient)


def test_http_client_of_connector_has_retry_cap_zero():
    """Mỗi request có thể tính vào quota tháng của Consensus: KHÔNG retry ngầm (max_retries=0)."""
    assert consensus_mod.ConsensusClient().http.max_retries == 0


def test_constructing_the_client_without_a_key_never_raises():
    """Kiểm khoá phải nằm trong search(), không trong __init__: `get_fallback_sources()` dựng client ngoài mọi `try`."""
    assert settings.consensus_api_key == ""
    assert consensus_mod.ConsensusClient() is not None


def test_settings_defaults_when_env_absent(monkeypatch):
    for ten in ("ENABLE_CONSENSUS", "CONSENSUS_API_KEY", "CONSENSUS_MAX_CALLS_PER_MONTH",
                "CONSENSUS_MAX_CALLS_PER_RUN", "CONSENSUS_LOOKBACK_YEARS"):
        monkeypatch.delenv(ten, raising=False)
    s = Settings()
    assert s.enable_consensus is False
    assert s.consensus_api_key == ""
    assert s.consensus_max_calls_per_month == 10
    assert s.consensus_max_calls_per_run == 5
    assert s.consensus_lookback_years == 10
    for ten in ("consensus_max_calls_per_month", "consensus_max_calls_per_run", "consensus_lookback_years"):
        assert isinstance(getattr(s, ten), int) and not isinstance(getattr(s, ten), bool)


def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("ENABLE_CONSENSUS", "true")
    monkeypatch.setenv("CONSENSUS_API_KEY", "TEST_ENV_KEY")
    monkeypatch.setenv("CONSENSUS_MAX_CALLS_PER_MONTH", "20")
    monkeypatch.setenv("CONSENSUS_MAX_CALLS_PER_RUN", "3")
    monkeypatch.setenv("CONSENSUS_LOOKBACK_YEARS", "0")
    s = Settings()
    assert s.enable_consensus is True
    assert s.consensus_api_key == "TEST_ENV_KEY"
    assert s.consensus_max_calls_per_month == 20
    assert s.consensus_max_calls_per_run == 3
    assert s.consensus_lookback_years == 0


def test_registered_in_sources_package_but_never_a_parallel_source(monkeypatch):
    assert sources_pkg.ConsensusClient is not None
    assert sources_pkg.ConsensusClient.name == "consensus"
    assert issubclass(sources_pkg.ConsensusClient, SourceClient)
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    assert "consensus" not in [c.name for c in sources_pkg.get_enabled_sources()]
    assert "consensus" in [c.name for c in sources_pkg.get_fallback_sources()]


# ════════════════════════════════════════════════════════════════════════════
# Chế độ mock
# ════════════════════════════════════════════════════════════════════════════

def test_mock_mode_returns_mock_records_without_network_key_state_or_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 1)
    _rebind_lop_da_nap_lai()
    client = consensus_mod.ConsensusClient()
    assert client.use_mock is True

    def khong_duoc_goi(*a, **kw):
        raise AssertionError("chế độ mock KHÔNG được gọi HTTP")

    monkeypatch.setattr(client.http.session, "request", khong_duoc_goi)
    for _ in range(4):
        recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
        assert recs, "mock phải trả dữ liệu minh hoạ cho từ khoá này"
        assert all(r.source == "consensus" for r in recs)
        assert all(r.raw.get("_mock") for r in recs)
        assert all(r.ingest_query == "atrial fibrillation" for r in recs)
    assert _ung_vien_tep_trang_thai(tmp_path / "data") == [], "mock không được động vào bộ đếm ngân sách bền vững"
    # Mock không tiêu ngân sách: lượt live duy nhất (trần 1) vẫn còn.
    live, ghi = _client(monkeypatch, tmp_path, nap_lai=False)
    assert live.search("chronic kidney disease")
    assert len(ghi.calls) == 1


# ════════════════════════════════════════════════════════════════════════════
# Fail-closed khi thiếu khoá
# ════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("key", ["", "   ", "\t\n"], ids=["rong", "khoang-trang", "tab-xuong-dong"])
def test_live_without_a_key_raises_thieu_key_and_sends_nothing(monkeypatch, tmp_path, key):
    client, ghi = _client(monkeypatch, tmp_path, key=key)
    with pytest.raises(RuntimeError) as ei:
        client.search("atrial fibrillation")
    assert getattr(ei.value, "loai", None) == "thieu_key"
    assert re.search(r"(?i)CONSENSUS_API_KEY|consensus.*(key|khoá|khóa)", str(ei.value)), str(ei.value)
    assert ghi.calls == [], "thiếu khoá thì không được gửi bất kỳ request nào"


def test_missing_key_does_not_consume_any_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 1)
    client, _ = _client(monkeypatch, tmp_path, key="")
    for _ in range(3):
        with pytest.raises(RuntimeError):
            client.search("atrial fibrillation")
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    ket_qua = _client(monkeypatch, tmp_path, nap_lai=False)[0].search("chronic kidney disease")
    assert ket_qua, "lượt duy nhất còn lại của trần phải dùng được: thiếu khoá không được trừ ngân sách"


# ════════════════════════════════════════════════════════════════════════════
# Request: header khoá, tham số, năm
# ════════════════════════════════════════════════════════════════════════════

def test_request_is_a_get_to_the_documented_endpoint_with_the_key_in_the_x_api_key_header(monkeypatch, tmp_path):
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("hypertension guideline", clinical_area="Tim mạch", max_results=5)
    assert len(ghi.calls) == 1
    goi = ghi.calls[0]
    assert goi.method.upper() == "GET"
    assert goi.base == ENDPOINT
    assert goi.headers.get("x-api-key") == CLE_SENTINEL


def test_the_key_appears_only_in_the_x_api_key_header_never_in_params_or_url(monkeypatch, tmp_path):
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("hypertension guideline", max_results=5)
    goi = ghi.calls[0]
    assert CLE_SENTINEL not in goi.full_url and CLE_SENTINEL not in goi.url
    assert CLE_SENTINEL not in json.dumps(goi.params, default=str)
    assert not (KHOA_THAM_SO_KHOA & {k.lower() for k in goi.params}), goi.params
    header_khac = {k: v for k, v in goi.headers.items() if k != "x-api-key"}
    assert CLE_SENTINEL not in json.dumps(header_khac, default=str)
    assert CLE_SENTINEL not in json.dumps(goi.extra, default=str)


def test_request_params_are_exactly_the_documented_free_plan_set(monkeypatch, tmp_path):
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("hypertension guideline", max_results=5, since_date="2024-05-17")
    tham_so = ghi.calls[0].params
    assert tham_so["query"] == "hypertension guideline"
    assert str(tham_so["medical_mode"]).lower() == "true"
    assert str(tham_so["exclude_preprints"]).lower() == "true"
    thua = set(tham_so) - THAM_SO_DUOC_PHEP
    assert not thua, f"tham số ngoài hợp đồng (page>=1, full text, study_types... trả phí sẽ ra 403 ở gói Free): {thua}"


def test_never_asks_for_a_second_page_or_full_text_even_when_more_results_exist(monkeypatch, tmp_path):
    """Tài liệu: page>=1 cần gói trả phí (403 feature_not_allowed) và full text chỉ có ở gói trả phí."""
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi(_hit(), is_end=False, next_page=1, page_size=1)))
    client.search("hypertension guideline", max_results=1)
    assert len(ghi.calls) == 1, "đúng MỘT request cho mỗi search(), dù is_end=False"
    tham_so = ghi.calls[0].params
    assert "page" not in tham_so or str(tham_so["page"]) == "0"
    assert "include_full_text_chunks" not in tham_so
    assert "study_types" not in tham_so


@pytest.mark.parametrize("max_results, ky_vong", [(None, 20), (1, 1), (5, 5), (20, 20), (21, 20), (100, 20), (1000, 20)])
def test_page_size_is_min_of_max_results_and_20(monkeypatch, tmp_path, max_results, ky_vong):
    client, ghi = _client(monkeypatch, tmp_path)
    if max_results is None:
        client.search("diabetes")  # mặc định của SourceClient.search là 20
    else:
        client.search("diabetes", max_results=max_results)
    assert int(ghi.calls[0].params["page_size"]) == ky_vong


@pytest.mark.parametrize("max_results", [0, -3])
def test_non_positive_max_results_never_sends_an_invalid_page_size(monkeypatch, tmp_path, max_results):
    client, ghi = _client(monkeypatch, tmp_path)
    ket_qua, loi = _chay(client, "diabetes", max_results=max_results)
    if loi is not None:
        _khang_dinh_loi_phan_loai(loi)
    for goi in ghi.calls:
        assert int(goi.params["page_size"]) >= 1, "page_size < 1 sẽ ra 422 và vẫn tốn một lượt gọi"


def test_query_with_quotes_passes_through_unchanged(monkeypatch, tmp_path):
    client, ghi = _client(monkeypatch, tmp_path)
    truy_van = '"SGLT2 inhibitors" AND "chronic kidney disease" & more=1'
    client.search(truy_van)
    assert ghi.calls[0].params["query"] == truy_van


@pytest.mark.parametrize("since, nam", [("2024-05-17", 2024), ("2019-01-01", 2019), ("2025-12-31", 2025)])
def test_year_min_is_the_year_of_since_date(monkeypatch, tmp_path, since, nam):
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("diabetes", since_date=since)
    assert int(ghi.calls[0].params["year_min"]) == nam


def test_since_date_wins_over_the_lookback_window(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_lookback_years", 3)
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("diabetes", since_date="2021-02-03")
    assert int(ghi.calls[0].params["year_min"]) == 2021


@pytest.mark.parametrize("lookback", [10, 3, 1])
def test_without_since_date_year_min_is_current_year_minus_lookback(monkeypatch, tmp_path, lookback):
    monkeypatch.setattr(settings, "consensus_lookback_years", lookback)
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("diabetes")
    assert int(ghi.calls[0].params["year_min"]) == _DATE_THAT.today().year - lookback


def test_lookback_zero_means_no_year_filter_when_there_is_no_since_date(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_lookback_years", 0)
    client, ghi = _client(monkeypatch, tmp_path)
    client.search("diabetes")
    assert "year_min" not in ghi.calls[0].params


@pytest.mark.parametrize("since", ["khong-phai-ngay", "17/05/2024", "2024", "20240517"])
def test_a_malformed_since_date_never_crashes_the_connector_or_sends_garbage(monkeypatch, tmp_path, since):
    client, ghi = _client(monkeypatch, tmp_path)
    ket_qua, loi = _chay(client, "diabetes", since_date=since)
    if loi is not None:
        _khang_dinh_loi_phan_loai(loi)
    for goi in ghi.calls:
        if "year_min" in goi.params:
            assert re.fullmatch(r"\d{4}", str(goi.params["year_min"]))
            assert 1900 <= int(goi.params["year_min"]) <= _DATE_THAT.today().year


def test_every_record_carries_the_query_area_and_source(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path, _tra_thanh_cong(_hit(), _hit(title="Second synthetic paper")))
    recs = client.search("hypertension guideline", clinical_area="Tim mạch")
    assert len(recs) == 2
    assert all(r.source == "consensus" for r in recs)
    assert all(r.ingest_query == "hypertension guideline" for r in recs)
    assert all(r.clinical_area == "Tim mạch" for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# ĐÚNG MỘT request HTTP cho mỗi search(), trên MỌI đường
# ════════════════════════════════════════════════════════════════════════════

_KICH_BAN_MOT_REQUEST = [
    pytest.param(_tra_thanh_cong(), id="200-thanh-cong"),
    pytest.param(_tra(200, _phan_hoi()), id="200-khong-co-ket-qua"),
    pytest.param(_tra(401, {"detail": "Invalid API key"}), id="401"),
    pytest.param(_tra(402, {"detail": "Payment required"}), id="402"),
    pytest.param(_tra(403, {"detail": "feature_not_allowed"}), id="403"),
    pytest.param(_tra(422, {"detail": [{"loc": ["query", "year_min"], "msg": "invalid", "type": "value_error"}]}),
                 id="422"),
    pytest.param(_tra(429, {"detail": MSG_HET_QUOTA}), id="429-het-quota"),
    pytest.param(_tra(429, {"detail": MSG_QUA_NHANH}, {"Retry-After": "1"}), id="429-qua-nhanh-co-retry-after"),
    pytest.param(_tra(500, {"detail": "Internal error"}), id="500"),
    pytest.param(_tra(502, {"detail": "Bad gateway"}), id="502"),
    pytest.param(_tra(503, {"detail": "Service unavailable"}, {"Retry-After": "2"}), id="503-co-retry-after"),
    pytest.param(_loi_timeout, id="timeout"),
    pytest.param(_loi_mang, id="mat-mang"),
    pytest.param(_tra(200, JSON_HONG), id="200-json-hong"),
    pytest.param(_tra(200, ["khong", "phai", "dict"]), id="200-la-list"),
    pytest.param(_tra(200, {"results": "hong"}), id="200-results-khong-phai-list"),
]


@pytest.mark.parametrize("kich_ban", _KICH_BAN_MOT_REQUEST)
def test_exactly_one_http_request_per_search_on_every_path(monkeypatch, tmp_path, caplog, kich_ban):
    """Mỗi request có thể tốn một lượt của quota tháng dùng chung với MCP của bác sĩ: KHÔNG retry ngầm trên đường nào."""
    caplog.set_level(logging.DEBUG)
    client, ghi = _client(monkeypatch, tmp_path, kich_ban)
    _chay(client, "chronic kidney disease")
    assert len(ghi.calls) == 1, f"nhận {len(ghi.calls)} request cho một search()"


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_tra(429, {"detail": MSG_QUA_NHANH}, {"Retry-After": "1"}), id="429-retry-after"),
    pytest.param(_tra(503, {"detail": "unavailable"}, {"Retry-After": "2"}), id="503-retry-after"),
    pytest.param(_loi_timeout, id="timeout"),
    pytest.param(_loi_mang, id="mat-mang"),
])
def test_failures_are_not_retried_and_do_not_sleep_a_backoff(monkeypatch, tmp_path, moi_truong, kich_ban):
    client, ghi = _client(monkeypatch, tmp_path, kich_ban)
    _chay(client, "chronic kidney disease")
    assert len(ghi.calls) == 1
    assert moi_truong.ngu == [], f"không được ngủ backoff khi không còn lượt thử lại: {moi_truong.ngu}"


# ════════════════════════════════════════════════════════════════════════════
# Phân loại lỗi (`loai`) theo mã HTTP / thân phản hồi
# ════════════════════════════════════════════════════════════════════════════

_LOI_HTTP = [
    pytest.param(401, {"detail": "Invalid API key"}, {}, "key_sai", id="401-detail"),
    pytest.param(401, {"error": "Missing or invalid x-api-key"}, {}, "key_sai", id="401-error"),
    pytest.param(402, {"detail": "Payment required: billing is past due"}, {}, "thanh_toan_qua_han", id="402"),
    pytest.param(403, {"detail": "feature_not_allowed"}, {}, "tinh_nang_khong_cho_phep", id="403-detail"),
    pytest.param(403, {"error": {"code": "feature_not_allowed", "message": "Pagination needs a paid plan"}}, {},
                 "tinh_nang_khong_cho_phep", id="403-long-nhau"),
    pytest.param(429, {"detail": MSG_HET_QUOTA}, {}, "het_quota", id="429-het-quota-detail"),
    pytest.param(429, {"error": MSG_HET_QUOTA}, {}, "het_quota", id="429-het-quota-error"),
    pytest.param(429, {"message": MSG_HET_QUOTA}, {}, "het_quota", id="429-het-quota-message"),
    pytest.param(429, {"detail": MSG_QUA_NHANH}, {"Retry-After": "1"}, "gioi_han_toc_do", id="429-qua-nhanh-retry-after"),
    pytest.param(429, {"error": MSG_QUA_NHANH}, {}, "gioi_han_toc_do", id="429-qua-nhanh-khong-header"),
    pytest.param(422, {"detail": [{"loc": ["query", "year_min"], "msg": "value is not a valid integer",
                                   "type": "type_error.integer"}]}, {}, "tham_so_sai", id="422-fastapi"),
    pytest.param(422, {"error": "validation error"}, {}, "tham_so_sai", id="422-error"),
]


@pytest.mark.parametrize("status, body, headers, loai", _LOI_HTTP)
def test_http_error_maps_to_the_documented_loai(monkeypatch, tmp_path, caplog, status, body, headers, loai):
    caplog.set_level(logging.DEBUG)
    client, ghi = _client(monkeypatch, tmp_path, _tra(status, body, headers))
    with pytest.raises(RuntimeError) as ei:
        client.search("chronic kidney disease")
    assert getattr(ei.value, "loai", None) == loai, f"HTTP {status} phải là loai={loai}, nhận {getattr(ei.value, 'loai', None)}"
    _khang_dinh_loi_phan_loai(ei.value)
    assert len(ghi.calls) == 1
    _kiem_khong_ro_khoa(client, caplog, ei.value, tmp_path)


@pytest.mark.parametrize("payload", [
    pytest.param(["khong", "phai", "dict"], id="la-list"),
    pytest.param(None, id="none"),
    pytest.param("khong phai json", id="la-chuoi"),
    pytest.param({}, id="khong-co-khoa-results"),
    pytest.param({"results": None}, id="results-none"),
    pytest.param({"results": "hong"}, id="results-la-chuoi"),
    pytest.param({"results": {"0": _hit()}}, id="results-la-dict"),
    pytest.param({"message": "ok"}, id="chi-co-message"),
])
def test_http_200_with_a_malformed_body_is_loud_not_silently_empty(monkeypatch, tmp_path, caplog, payload):
    """HttpClient coi HTTP 200 là thành công: connector PHẢI tự nổ, nếu không Source Log ghi 'ok / 0 bản ghi' và một
    tầng dự phòng hỏng trông như tầng không có bài."""
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, payload))
    loai = _ro_hoac_rong_co_canh_bao(client, caplog, "chronic kidney disease")
    assert len(ghi.calls) == 1
    if loai is not None:
        assert loai == "phan_hoi_khong_hop_le"


def test_http_200_with_unparseable_json_is_loud(monkeypatch, tmp_path, caplog):
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, JSON_HONG))
    loai = _ro_hoac_rong_co_canh_bao(client, caplog, "chronic kidney disease")
    assert len(ghi.calls) == 1
    if loai is not None:
        assert loai in {"phan_hoi_khong_hop_le", "khac"}


def test_an_empty_results_list_is_a_valid_answer_not_an_error(monkeypatch, tmp_path):
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi()))
    assert client.search("a very rare topic") == []
    assert len(ghi.calls) == 1


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_tra(500, {"detail": "Internal error"}), id="500"),
    pytest.param(_tra(502, {"detail": "Bad gateway"}), id="502"),
    pytest.param(_tra(503, {"detail": "unavailable"}), id="503"),
    pytest.param(_loi_timeout, id="timeout"),
    pytest.param(_loi_mang, id="mat-mang"),
])
def test_server_and_transport_failures_are_never_silent_and_never_a_chot_error(monkeypatch, tmp_path, caplog, kich_ban):
    """Lỗi tạm thời: ném lỗi phân loại (không chốt), HOẶC trả [] nhưng `failure_count` của HttpClient tăng để ingestion
    ghi 'error'. Không bao giờ trả bản ghi, không bao giờ rơi về mock."""
    caplog.set_level(logging.DEBUG)
    client, _ = _client(monkeypatch, tmp_path, kich_ban)
    ket_qua, loi = _chay(client, "chronic kidney disease")
    if loi is None:
        assert ket_qua == []
        assert client.http.health_snapshot()["failure_count"] > 0, "lỗi HTTP thành [] im lặng"
    else:
        assert _khang_dinh_loi_phan_loai(loi) not in LOAI_CHOT


# ════════════════════════════════════════════════════════════════════════════
# Ánh xạ RawRecord: không bịa, `takeaway` không phải abstract, nhãn Consensus chỉ ở raw
# ════════════════════════════════════════════════════════════════════════════

def test_full_hit_maps_all_core_fields(monkeypatch, tmp_path):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit())
    assert r.source == "consensus"
    assert r.title == "Effect of fake drug on fake outcome: a synthetic consensus test paper"
    assert r.authors == "Alice Nguyen, Bob Tran"
    assert r.journal_or_organization == "Journal of Synthetic Testing"
    assert r.publication_date == "2023-05-01"
    assert r.doi == "10.5555/consensus.test.001"
    assert r.url == "https://example-journal.org/articles/consensus-test-001"
    assert r.abstract == _hit()["abstract"]
    assert r.pmid is None, "Consensus không cung cấp PMID: không được bịa"
    assert not r.raw.get("_mock"), "bản ghi live không được gắn nhãn mock"


def test_takeaway_is_never_the_abstract_and_only_lives_in_raw(monkeypatch, tmp_path):
    hit = _hit()
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    assert hit["takeaway"] not in (r.abstract or "")
    assert r.raw.get("takeaway") == hit["takeaway"], "takeaway phải còn trong raw để truy vết"
    khac_raw = {f: getattr(r, f) for f in ("title", "authors", "journal_or_organization", "abstract", "url", "doi")}
    assert hit["takeaway"] not in json.dumps(khac_raw, ensure_ascii=False)


def test_a_hit_without_an_abstract_never_falls_back_to_the_takeaway(monkeypatch, tmp_path):
    hit = _hit(xoa=("abstract",))
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    assert not r.abstract
    assert hit["takeaway"] not in json.dumps(normalize(r).get("abstract") or "")


@pytest.mark.parametrize("abstract", [None, "", 123, ["a", "b"], {"text": "x"}], ids=["none", "rong", "so", "list", "dict"])
def test_abstract_is_kept_only_when_it_is_a_real_string(monkeypatch, tmp_path, abstract):
    hit = _hit(abstract=abstract)
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    assert not r.abstract, f"abstract={abstract!r} không phải chuỗi thật, không được thành abstract"
    assert hit["takeaway"] not in (r.abstract or "")


def test_takeaway_never_reaches_the_normalized_abstract_used_for_scoring(monkeypatch, tmp_path):
    hit = _hit()
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    item = normalize(r)
    assert hit["takeaway"] not in (item.get("abstract") or "")


@pytest.mark.parametrize("nhan", [
    "rct", "systematic review", "meta-analysis", "cohort study", "case report", "literature review",
    "commentary or perspective", "non-randomized experimental study", "animal", "other", "RCT",
])
def test_consensus_study_type_label_stays_in_raw_and_never_upgrades_the_record(monkeypatch, tmp_path, nhan):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(study_type=nhan))
    assert r.study_type is None, "nhãn của Consensus chỉ có thể HẠ, không được nâng study_type của pipeline"
    assert r.raw.get("consensus_study_type") == nhan


def test_is_preprint_true_makes_the_study_type_preprint_even_with_a_strong_label(monkeypatch, tmp_path):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(is_preprint=True, study_type="rct"))
    assert r.study_type == "preprint"
    assert r.raw.get("consensus_study_type") == "rct"


@pytest.mark.parametrize("gia_tri", [False, None], ids=["false", "none"])
def test_a_non_preprint_hit_gets_no_study_type(monkeypatch, tmp_path, gia_tri):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(is_preprint=gia_tri))
    assert r.study_type is None


def test_missing_is_preprint_key_gets_no_study_type(monkeypatch, tmp_path):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(xoa=("is_preprint",)))
    assert r.study_type is None


def test_raw_carries_the_consensus_specific_fields(monkeypatch, tmp_path):
    hit = _hit()
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    assert r.raw.get("takeaway") == hit["takeaway"]
    assert r.raw.get("consensus_study_type") == hit["study_type"]
    assert r.raw.get("citation_count") == hit["citation_count"]
    assert r.raw.get("sjr_best_quartile") == hit["sjr_best_quartile"]
    assert r.raw.get("sample_size") == hit["sample_size"]
    assert r.raw, "raw phải mang dấu vết nguồn gốc (provenance)"


def test_missing_optional_numeric_fields_are_not_coerced_to_zero(monkeypatch, tmp_path):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(xoa=("citation_count", "sample_size", "sjr_best_quartile")))
    bi_ep_thanh_0 = [(p, v) for p, v in _duyet(r.raw)
                     if p and p[-1] in {"citation_count", "sample_size", "sjr_best_quartile"} and v in (0, "0")]
    assert bi_ep_thanh_0 == [], "thiếu thì để None/vắng, không được ép thành 0"


@pytest.mark.parametrize("doi_vao, doi_ra", [
    ("10.5555/CONSENSUS.TEST.001", "10.5555/consensus.test.001"),
    ("https://doi.org/10.5555/Consensus.Test.001", "10.5555/consensus.test.001"),
    ("http://dx.doi.org/10.5555/Consensus.Test.001", "10.5555/consensus.test.001"),
    ("doi:10.5555/Consensus.Test.001", "10.5555/consensus.test.001"),
    ("  10.5555/consensus.test.001  ", "10.5555/consensus.test.001"),
    ("", None), (None, None), (12345, None), (["10.5555/x"], None), ("khong phai doi", None),
], ids=["hoa", "https-doi-org", "http-dx", "tien-to-doi", "khoang-trang", "rong", "none", "so", "list", "rac"])
def test_doi_is_cleaned_lowercased_and_never_invented(monkeypatch, tmp_path, doi_vao, doi_ra):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(doi=doi_vao))
    assert r.doi == doi_ra


def test_missing_doi_and_abstract_are_handled_and_stay_none(monkeypatch, tmp_path):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(xoa=("doi", "abstract", "url", "journal_name", "authors")))
    assert r.doi is None and r.pmid is None
    assert not r.abstract
    assert r.url is None
    assert r.journal_or_organization in (None, "")
    assert not r.authors
    assert r.title


@pytest.mark.parametrize("nam, ngay, ky_vong", [
    (2023, "2023-05-01", "2023-05-01"),
    (2023, None, "2023"),
    ("2023", None, "2023"),
    (2023, "May 2023", "2023"),
    (2023, "khong-phai-ngay", "2023"),
    (None, "2021-03-15", "2021-03-15"),
    (None, None, None),
], ids=["nam+ngay-iso", "chi-nam", "nam-la-chuoi", "ngay-khong-iso", "ngay-rac", "chi-ngay-iso", "khong-co-gi"])
def test_publication_date_is_the_year_or_the_iso_date_never_invented(monkeypatch, tmp_path, nam, ngay, ky_vong):
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit(publish_year=nam, publish_date=ngay))
    assert r.publication_date == ky_vong


def _ngay_hop_ly(gia_tri: Optional[str]) -> bool:
    if gia_tri is None:
        return True
    if not isinstance(gia_tri, str) or not re.fullmatch(r"\d{4}(-\d{2}(-\d{2})?)?", gia_tri):
        return False
    return 1800 <= int(gia_tri[:4]) <= _DATE_THAT.today().year + 1


_HIT_LA = [
    pytest.param({"authors": "Alice Nguyen"}, id="authors-la-chuoi"),
    pytest.param({"authors": None}, id="authors-none"),
    pytest.param({"authors": []}, id="authors-rong"),
    pytest.param({"authors": ["Alice Nguyen", None, 42, {"name": "Bob"}, ""]}, id="authors-pha-tap"),
    pytest.param({"authors": {"0": "Alice"}}, id="authors-la-dict"),
    pytest.param({"publish_year": "2019", "publish_date": None}, id="nam-la-chuoi"),
    pytest.param({"publish_year": "abc", "publish_date": None}, id="nam-rac"),
    pytest.param({"publish_year": None, "publish_date": None}, id="khong-nam"),
    pytest.param({"publish_year": 2019.0, "publish_date": None}, id="nam-float"),
    pytest.param({"publish_year": True, "publish_date": None}, id="nam-bool"),
    pytest.param({"publish_year": 99999, "publish_date": None}, id="nam-phi-ly"),
    pytest.param({"publish_year": -5, "publish_date": None}, id="nam-am"),
    pytest.param({"publish_year": None, "publish_date": 20230501}, id="ngay-la-so"),
    pytest.param({"publish_date": "khong-phai-ngay"}, id="ngay-rac"),
    pytest.param({"doi": 12345}, id="doi-la-so"),
    pytest.param({"doi": ["10.5555/x"]}, id="doi-la-list"),
    pytest.param({"url": 123}, id="url-la-so"),
    pytest.param({"url": {"a": 1}}, id="url-la-dict"),
    pytest.param({"journal_name": {"name": "x"}}, id="journal-la-dict"),
    pytest.param({"journal_name": None}, id="journal-none"),
    pytest.param({"abstract": 123}, id="abstract-la-so"),
    pytest.param({"abstract": ["a", "b"]}, id="abstract-la-list"),
    pytest.param({"takeaway": None}, id="takeaway-none"),
    pytest.param({"takeaway": 5}, id="takeaway-la-so"),
    pytest.param({"study_type": None}, id="study-type-none"),
    pytest.param({"study_type": 7}, id="study-type-la-so"),
    pytest.param({"study_type": ["rct"]}, id="study-type-la-list"),
    pytest.param({"is_preprint": "true"}, id="preprint-la-chuoi"),
    pytest.param({"citation_count": "many"}, id="citation-la-chuoi"),
    pytest.param({"sample_size": {"n": 3}}, id="sample-size-la-dict"),
    pytest.param({"unexpected_field": {"deep": [1, 2, 3]}}, id="truong-la"),
]


@pytest.mark.parametrize("ghi_de", _HIT_LA)
def test_weird_field_types_never_crash_and_never_break_the_record(monkeypatch, tmp_path, ghi_de):
    hit = _hit(**ghi_de)
    r = _mot_ban_ghi(monkeypatch, tmp_path, hit)
    assert r.title == hit["title"]
    for ten in ("authors", "journal_or_organization", "doi", "url", "abstract"):
        gia_tri = getattr(r, ten)
        assert gia_tri is None or isinstance(gia_tri, str), f"{ten}={gia_tri!r} phải là chuỗi hoặc None"
    assert _ngay_hop_ly(r.publication_date), f"publication_date={r.publication_date!r} không hợp lý"
    assert r.study_type in (None, "preprint")
    if "doi" in ghi_de and not isinstance(ghi_de["doi"], str):
        assert r.doi is None, "DOI không phải chuỗi thì không được bịa"
    if "abstract" in ghi_de and not isinstance(ghi_de["abstract"], str):
        assert not r.abstract
    if "url" in ghi_de and not isinstance(ghi_de["url"], str):
        assert r.url is None
    if ghi_de.get("authors") == "Alice Nguyen":
        assert "Alice Nguyen" in (r.authors or "")
    if isinstance(ghi_de.get("authors"), list) and "Alice Nguyen" in ghi_de["authors"]:
        assert "Alice Nguyen" in (r.authors or "")


def test_one_bad_result_does_not_wipe_out_the_others(monkeypatch, tmp_path):
    """Cùng họ lỗi đã vá ở scopus/openalex/serpapi: MỘT phần tử hỏng không được xoá sạch cả trang."""
    tot = _hit(title="Bài hoàn toàn bình thường", doi="10.5555/consensus.test.002")
    hong = [None, "chuoi-lung-tung", 42, [1, 2], {"url": "https://example.org/khong-co-tieu-de"},
            {"title": None}, {"title": ""}, {"title": "Bài có dữ liệu con hỏng", "authors": 5, "publish_year": {"x": 1},
                                            "doi": {"x": 1}}, tot]
    client, _ = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi(*hong)))
    recs = client.search("chronic kidney disease")
    tieu_de = [r.title for r in recs]
    assert "Bài hoàn toàn bình thường" in tieu_de
    assert all(t for t in tieu_de), "không được có bản ghi không tiêu đề (không bịa)"
    assert set(tieu_de) <= {"Bài hoàn toàn bình thường", "Bài có dữ liệu con hỏng"}, "không được bịa tiêu đề"
    assert all(r.source == "consensus" for r in recs)


def test_records_come_only_from_the_response_nothing_fabricated(monkeypatch, tmp_path):
    dau_vao = [
        _hit(title="Bài thứ nhất về tăng huyết áp", doi="10.5555/c.1", url="https://example-a.org/1"),
        _hit(title="Bài thứ hai về đái tháo đường", doi="10.5555/c.2", url="https://example-b.org/2"),
        _hit(title="Bài thứ ba về suy tim", doi="10.5555/c.3", url="https://example-c.org/3"),
    ]
    client, _ = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi(*dau_vao)))
    recs = client.search("chronic disease")
    assert [r.title for r in recs] == [h["title"] for h in dau_vao]
    assert [r.doi for r in recs] == [h["doi"] for h in dau_vao]
    assert [r.url for r in recs] == [h["url"] for h in dau_vao]
    assert all(r.pmid is None for r in recs)
    assert all(not r.raw.get("_mock") for r in recs)


_TIEU_DE_RUI_RO = [
    "A randomized controlled trial of SGLT2 inhibitors on mortality: a systematic review and meta-analysis",
    "Protocol for a systematic review of statin recommendations",
    "Randomised placebo-controlled double-blind trial of a fake drug",
    "Practice guideline recommendations for a fake condition",
]


def test_title_only_records_get_no_study_type_and_can_never_be_tier_a_or_actionable(monkeypatch, tmp_path):
    """Không bao giờ suy study_type từ tiêu đề: bản ghi chỉ có tiêu đề (không tóm tắt, không DOI, không tạp chí) mà
    bị chấm như bằng chứng mạnh sẽ chảy vào alert_digest, email/webhook và EBM_MASTER."""
    hits = [_hit(title=t, xoa=("abstract", "doi", "journal_name", "publisher_name"), study_type="rct",
                 takeaway="Consensus AI takeaway: strong evidence.") for t in _TIEU_DE_RUI_RO]
    client, _ = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi(*hits)))
    recs = client.search("kidney")
    assert len(recs) == len(_TIEU_DE_RUI_RO)
    for r in recs:
        assert r.study_type is None
        item = normalize(r)
        score_item(item)
        phan_loai, actionable, _, _ = classify(item)
        assert item["reliability_tier"] != "A", r.title
        assert actionable is False, r.title
        assert phan_loai != "actionable", r.title


def test_a_consensus_record_never_carries_a_grade_or_decision(monkeypatch, tmp_path):
    """Connector chỉ khám phá: không được tự đặt gradeLevel/decision hay điểm."""
    r = _mot_ban_ghi(monkeypatch, tmp_path, _hit())
    thu_muc = json.dumps(r.to_dict(), ensure_ascii=False, default=str).lower()
    assert '"gradelevel"' not in thu_muc and '"decision"' not in thu_muc
    assert r.official_grade is None


# ════════════════════════════════════════════════════════════════════════════
# PII và cú pháp PubMed KHÔNG BAO GIỜ được gửi
# ════════════════════════════════════════════════════════════════════════════

_TRUY_VAN_PII = [
    "mã bệnh nhân AB123456 HbA1c",
    "SĐT 0901234567 tăng huyết áp",
    "ngày sinh 15/07/1980 đái tháo đường",
    "john.doe@gmail.com hypertension",
    "MRN 12345678 heart failure",
]
_TRUY_VAN_CU_PHAP_PUBMED = [
    '"Cochrane Database Syst Rev"[ta]',
    'hypertension[tiab] AND "randomized controlled trial"[pt]',
    '"NICE guidance"[ti] OR "National Institute for Health and Care Excellence"[cn]',
    '"Diabetes Mellitus"[mh]',
    "heart failure[majr]",
    "2024[dp] AND statin",
]


def test_the_pii_examples_are_really_pii_by_the_repos_own_detector():
    """Đối chứng: các truy vấn dưới đây thật sự là PII theo `contains_pii_text` của repo (không tự chế tiêu chí)."""
    assert all(contains_pii_text(q) for q in _TRUY_VAN_PII)
    assert not contains_pii_text("hypertension guideline")


@pytest.mark.parametrize("truy_van", _TRUY_VAN_PII)
def test_pii_queries_are_never_sent_and_never_a_chot_error(monkeypatch, tmp_path, truy_van):
    client, ghi = _client(monkeypatch, tmp_path)
    ket_qua, loi = _chay(client, truy_van)
    assert ghi.calls == [], "truy vấn có PII/PHI tuyệt đối không được rời máy"
    if loi is None:
        assert ket_qua == []
    else:
        assert _khang_dinh_loi_phan_loai(loi) not in LOAI_CHOT, "PII không được chốt cả tầng"
    assert CLE_SENTINEL not in json.dumps(ghi.calls, default=str) and truy_van not in json.dumps(ghi.calls, default=str)


@pytest.mark.parametrize("truy_van", _TRUY_VAN_CU_PHAP_PUBMED)
def test_pubmed_field_tag_queries_are_never_sent(monkeypatch, tmp_path, truy_van):
    client, ghi = _client(monkeypatch, tmp_path)
    ket_qua, loi = _chay(client, truy_van)
    assert ghi.calls == [], "truy vấn cú pháp PubMed (truy vấn theo tạp chí/tổ chức) không dịch được sang văn bản thường"
    if loi is None:
        assert ket_qua == []
    else:
        assert _khang_dinh_loi_phan_loai(loi) not in LOAI_CHOT


def test_skipped_queries_do_not_consume_the_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 1)
    client, ghi = _client(monkeypatch, tmp_path)
    for truy_van in _TRUY_VAN_PII + _TRUY_VAN_CU_PHAP_PUBMED:
        _chay(client, truy_van)
    assert ghi.calls == []
    assert client.search("chronic kidney disease"), "lượt duy nhất còn nguyên: truy vấn bị bỏ qua không được trừ ngân sách"
    assert len(ghi.calls) == 1


# ════════════════════════════════════════════════════════════════════════════
# Ngân sách: trần theo tiến trình (mỗi lượt chạy)
# ════════════════════════════════════════════════════════════════════════════

_MSG_NGAN_SACH = re.compile(r"(?i)consensus_max_calls_per_(month|run)|ngân sách|hạn mức|budget")


def test_per_run_cap_exhaustion_is_loud_and_sends_no_further_request(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 3)
    client, ghi = _client(monkeypatch, tmp_path)
    for i in range(3):
        assert client.search(f"truy van {i}")
    assert len(ghi.calls) == 3
    with pytest.raises(RuntimeError) as ei:
        client.search("truy van vuot tran")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert _MSG_NGAN_SACH.search(str(ei.value)), str(ei.value)
    assert CLE_SENTINEL not in str(ei.value)
    assert len(ghi.calls) == 3, "hết ngân sách thì không được gửi thêm request"
    with pytest.raises(RuntimeError) as ei2:
        client.search("van vuot tran lan nua")
    assert getattr(ei2.value, "loai", None) == "het_ngan_sach", "vẫn nổ to ở mọi lần sau, không tự hồi phục im lặng"
    assert len(ghi.calls) == 3


def test_per_run_cap_is_shared_across_client_instances_of_the_same_process(monkeypatch, tmp_path):
    """Ingestion, `research/manager.py` và `research/dossier.py` đều dựng instance riêng: trần tính cho cả TIẾN TRÌNH."""
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 3)
    a, ghi_a = _client(monkeypatch, tmp_path)
    b, ghi_b = _client(monkeypatch, tmp_path, nap_lai=False)
    a.search("q1")
    a.search("q2")
    assert b.search("q3")
    assert len(ghi_a.calls) + len(ghi_b.calls) == 3
    for client in (a, b):
        with pytest.raises(RuntimeError) as ei:
            client.search("q4")
        assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert len(ghi_a.calls) + len(ghi_b.calls) == 3


def test_the_per_run_counter_resets_with_a_new_process_but_the_monthly_one_does_not(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 2)
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 3)
    c1, ghi1 = _client(monkeypatch, tmp_path)
    c1.search("q1")
    c1.search("q2")
    with pytest.raises(RuntimeError) as ei:
        c1.search("q3")
    assert ei.value.loai == "het_ngan_sach"
    c2, ghi2 = _client(monkeypatch, tmp_path)          # tiến trình mới: lượt-chạy về 0, tháng còn 1
    assert c2.search("q3")
    assert len(ghi2.calls) == 1
    with pytest.raises(RuntimeError) as ei2:
        c2.search("q4")
    assert ei2.value.loai == "het_ngan_sach"
    assert len(ghi2.calls) == 1


# ════════════════════════════════════════════════════════════════════════════
# Ngân sách: bộ đếm THÁNG bền vững (tệp JSON trạng thái)
# ════════════════════════════════════════════════════════════════════════════

def test_monthly_counter_persists_across_process_restarts(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 3)
    c1, ghi1 = _client(monkeypatch, tmp_path)
    for i in range(3):
        assert c1.search(f"q{i}")
    assert len(ghi1.calls) == 3
    c2, ghi2 = _client(monkeypatch, tmp_path)          # khởi động lại
    with pytest.raises(RuntimeError) as ei:
        c2.search("q3")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert _MSG_NGAN_SACH.search(str(ei.value)), str(ei.value)
    assert ghi2.calls == [], "hết ngân sách tháng thì không được gửi request nào, kể cả sau khi khởi động lại"


def test_the_default_monthly_cap_leaves_most_of_the_free_plan_for_the_doctors_own_mcp_use(monkeypatch):
    """Trần mặc định 10 trên 30 lượt của gói Free: phần còn lại dành cho MCP của bác sĩ (cùng một hạn mức)."""
    monkeypatch.delenv("CONSENSUS_MAX_CALLS_PER_MONTH", raising=False)
    monkeypatch.delenv("CONSENSUS_MAX_CALLS_PER_RUN", raising=False)
    s = Settings()
    assert s.consensus_max_calls_per_month <= 10
    assert s.consensus_max_calls_per_run <= s.consensus_max_calls_per_month


def test_the_state_file_lives_under_data_dir_is_json_written_atomically_and_holds_no_secret(monkeypatch, tmp_path):
    client, _ = _client(monkeypatch, tmp_path)
    for i in range(4):
        client.search(f"q{i}")
    tep = _tep_trang_thai(tmp_path / "data")
    du_lieu = json.loads(tep.read_text(encoding="utf-8"))
    assert isinstance(du_lieu, (dict, list))
    assert any(v == 4 and not isinstance(v, bool) for _, v in _duyet(du_lieu)), (
        f"tệp trạng thái phải ghi số lượt đã tính (4): {du_lieu}")
    assert CLE_SENTINEL not in tep.read_text(encoding="utf-8")
    con_lai = [p for p in (tmp_path / "data").rglob("*") if p.is_file() and (
        p.suffix in {".tmp", ".part", ".temp"} or p.name.endswith("~") or ".tmp" in p.name)]
    assert con_lai == [], f"ghi nguyên tử không được để lại tệp tạm: {con_lai}"


def test_no_state_file_means_a_fresh_month_not_a_corruption(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 2)
    assert _ung_vien_tep_trang_thai(tmp_path / "data") == []
    client, ghi = _client(monkeypatch, tmp_path)
    assert client.search("q1") and client.search("q2")
    assert len(ghi.calls) == 2


@pytest.mark.parametrize("noi_dung", [
    "{not json", "", "{\"da_goi\": ", "[]", "\"mot chuoi\"", "null", "\x00\x01\x02 rac nhi phan",
], ids=["json-hong", "rong", "cut-cut", "list-rong", "chuoi", "null", "nhi-phan"])
def test_a_corrupt_state_file_means_cap_reached_and_is_loud(monkeypatch, tmp_path, caplog, noi_dung):
    """Tệp hỏng là 'không biết đã dùng bao nhiêu': fail-closed = coi như CHẠM TRẦN và nổ to, không đoán là 0."""
    caplog.set_level(logging.DEBUG)
    c1, _ = _client(monkeypatch, tmp_path)
    assert c1.search("q1")
    _tep_trang_thai(tmp_path / "data").write_text(noi_dung, encoding="utf-8", newline="\n")
    c2, ghi2 = _client(monkeypatch, tmp_path)
    with pytest.raises(RuntimeError) as ei:
        c2.search("q2")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert ghi2.calls == [], "tệp trạng thái hỏng thì không được gửi request tính phí"
    assert CLE_SENTINEL not in str(ei.value)


def test_a_corrupt_state_file_is_never_silently_reset_to_zero_on_the_next_call(monkeypatch, tmp_path):
    c1, _ = _client(monkeypatch, tmp_path)
    c1.search("q1")
    _tep_trang_thai(tmp_path / "data").write_text("{not json", encoding="utf-8", newline="\n")
    for _ in range(3):
        c2, ghi2 = _client(monkeypatch, tmp_path)
        with pytest.raises(RuntimeError) as ei:
            c2.search("q2")
        assert ei.value.loai == "het_ngan_sach"
        assert ghi2.calls == []


@pytest.mark.parametrize("nam1, thang1, nam2, thang2", [(2026, 9, 2026, 10), (2026, 12, 2027, 1), (2026, 1, 2026, 2)],
                         ids=["9-sang-10", "12-sang-1-nam-sau", "1-sang-2"])
def test_monthly_counter_rolls_over_at_the_calendar_month_change(monkeypatch, tmp_path, nam1, thang1, nam2, thang2):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 2)
    with _thoi_diem(nam1, thang1, 3):
        c, ghi = _client(monkeypatch, tmp_path)
        assert c.search("q1") and c.search("q2")
        with pytest.raises(RuntimeError) as ei:
            c.search("q3")
        assert ei.value.loai == "het_ngan_sach" and len(ghi.calls) == 2
    with _thoi_diem(nam1, thang1, 27):                 # cùng tháng, tiến trình mới: vẫn chạm trần
        c, ghi = _client(monkeypatch, tmp_path)
        with pytest.raises(RuntimeError) as ei:
            c.search("q4")
        assert ei.value.loai == "het_ngan_sach" and ghi.calls == []
    with _thoi_diem(nam2, thang2, 2):                  # sang tháng lịch mới: về 0
        c, ghi = _client(monkeypatch, tmp_path)
        assert c.search("q5") and c.search("q6")
        assert len(ghi.calls) == 2
        with pytest.raises(RuntimeError) as ei:
            c.search("q7")
        assert ei.value.loai == "het_ngan_sach" and len(ghi.calls) == 2


def test_a_month_change_inside_one_process_lifetime_is_not_needed_but_never_reads_a_stale_month_as_current(
        monkeypatch, tmp_path):
    """Tệp còn số của THÁNG TRƯỚC (tiến trình mới sau khi sang tháng): không được chặn oan."""
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    with _thoi_diem(2026, 8, 20):
        c, _ = _client(monkeypatch, tmp_path)
        assert c.search("q1")
    with _thoi_diem(2026, 9, 5):
        c, ghi = _client(monkeypatch, tmp_path)
        assert c.search("q2"), "số của tháng 8 không được tính vào tháng 9"
        assert len(ghi.calls) == 1


# ── Lượt trúng cache được hoàn lại; lượt lỗi trước khi Consensus tính thì không tính vào tháng ────────

@pytest.mark.parametrize("tran", ["consensus_max_calls_per_month", "consensus_max_calls_per_run"],
                         ids=["tran-thang", "tran-lan-chay"])
def test_a_call_answered_from_the_http_cache_is_refunded(monkeypatch, tmp_path, tran):
    monkeypatch.setattr(settings, tran, 2)
    client, ghi = _client(monkeypatch, tmp_path, cache=True)
    assert client.search("q-cache")
    assert len(ghi.calls) == 1
    assert client.search("q-cache")                                # trúng cache: không request mới
    assert len(ghi.calls) == 1 and client.http.cache_hit_count == 1
    assert client.search("q-khac")                                 # nếu không hoàn lại thì đây là lượt thứ 3 > trần 2
    assert len(ghi.calls) == 2
    with pytest.raises(RuntimeError) as ei:
        client.search("q-khac-nua")
    assert ei.value.loai == "het_ngan_sach"
    assert len(ghi.calls) == 2


def test_a_cache_hit_is_also_refunded_in_the_persistent_monthly_counter_across_restarts(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 2)
    c1, ghi1 = _client(monkeypatch, tmp_path, cache=True)
    c1.search("q-cache")
    c1.search("q-cache")                                           # cache
    c2, ghi2 = _client(monkeypatch, tmp_path, cache=True)          # khởi động lại: tháng phải còn 1 lượt
    assert c2.search("q-moi")
    assert len(ghi2.calls) == 1
    with pytest.raises(RuntimeError):
        c2.search("q-moi-nua")


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_tra(401, {"detail": "Invalid API key"}), id="401"),
    pytest.param(_tra(402, {"detail": "Payment required"}), id="402"),
    pytest.param(_tra(403, {"detail": "feature_not_allowed"}), id="403"),
    pytest.param(_tra(422, {"detail": [{"msg": "invalid", "type": "value_error"}]}), id="422"),
    pytest.param(_loi_mang, id="mat-mang"),
    pytest.param(_loi_timeout, id="timeout"),
])
def test_a_call_that_failed_before_consensus_counted_it_is_not_charged_to_the_month(monkeypatch, tmp_path, kich_ban):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    hong, ghi_hong = _client(monkeypatch, tmp_path, kich_ban)
    _chay(hong, "q-loi")
    assert len(ghi_hong.calls) == 1
    tot, ghi_tot = _client(monkeypatch, tmp_path)                  # tiến trình mới, cùng tệp trạng thái tháng
    assert tot.search("q-tot"), "lượt lỗi trước khi Consensus tính không được trừ vào hạn mức tháng"
    assert len(ghi_tot.calls) == 1
    with pytest.raises(RuntimeError) as ei:
        tot.search("q-vuot")
    assert ei.value.loai == "het_ngan_sach"
    assert len(ghi_tot.calls) == 1


def test_several_non_chot_failures_in_a_row_do_not_eat_the_monthly_budget(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 2)
    kich_ban = _theo_thu_tu(
        _tra(422, {"detail": [{"msg": "invalid"}]}), _loi_mang, _loi_timeout,
        _tra_thanh_cong(), _tra_thanh_cong(), _tra_thanh_cong())
    client, ghi = _client(monkeypatch, tmp_path, kich_ban)
    for i in range(3):
        _chay(client, f"loi-{i}")
    assert client.search("tot-1") and client.search("tot-2")
    with pytest.raises(RuntimeError) as ei:
        client.search("tot-3")
    assert ei.value.loai == "het_ngan_sach"
    assert len(ghi.calls) == 5


def test_429_used_all_included_searches_sets_the_monthly_counter_to_its_cap(monkeypatch, tmp_path):
    """Consensus báo đã hết hạn mức tháng (MCP của bác sĩ dùng chung): bộ đếm cục bộ phải nhảy lên đúng trần dù mới
    dùng 1 trên 10, để mọi lượt sau — kể cả sau khi khởi động lại — không gửi gì nữa."""
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 10)
    c1, ghi1 = _client(monkeypatch, tmp_path, _tra(429, {"detail": MSG_HET_QUOTA}))
    with pytest.raises(RuntimeError) as ei:
        c1.search("q1")
    assert ei.value.loai == "het_quota"
    c2, ghi2 = _client(monkeypatch, tmp_path)                       # tiến trình mới, server "đã hồi" trong giả lập
    with pytest.raises(RuntimeError) as ei2:
        c2.search("q2")
    # Hai lớp đều là lỗi CHỐT; hợp đồng chỉ đòi "đặt bộ đếm về trần" => không gửi gì nữa cho tới hết tháng.
    assert ei2.value.loai in {"het_ngan_sach", "het_quota"}, "bộ đếm tháng phải đã về trần sau 429 hết quota"
    assert ei2.value.loai in LOAI_CHOT
    assert ghi2.calls == []


def test_429_too_many_requests_does_not_touch_the_monthly_counter(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    c1, _ = _client(monkeypatch, tmp_path, _tra(429, {"detail": MSG_QUA_NHANH}, {"Retry-After": "1"}))
    with pytest.raises(RuntimeError) as ei:
        c1.search("q1")
    assert ei.value.loai == "gioi_han_toc_do"
    c2, ghi2 = _client(monkeypatch, tmp_path)
    assert c2.search("q2"), "429 'quá nhanh' không phải hết hạn mức tháng: không được chặn các lượt sau"
    assert len(ghi2.calls) == 1


def test_a_successful_call_with_a_full_page_is_charged_exactly_once(monkeypatch, tmp_path):
    """Consensus tính 1 lượt cho mỗi 100 bài trả về (làm tròn lên, tối thiểu 1): 20 bài vẫn là 1 lượt."""
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    hits = [_hit(title=f"Synthetic paper {i}", doi=f"10.5555/full.page.{i}") for i in range(20)]
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi(*hits)))
    assert len(client.search("q1", max_results=20)) == 20
    assert len(ghi.calls) == 1
    with pytest.raises(RuntimeError) as ei:
        client.search("q2")
    assert ei.value.loai == "het_ngan_sach"


def test_an_empty_answer_is_still_charged_one_call(monkeypatch, tmp_path):
    """Trả 0 bài vẫn tính tối thiểu 1 lượt ở phía Consensus: đếm cục bộ phải khớp."""
    monkeypatch.setattr(settings, "consensus_max_calls_per_month", 1)
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi()))
    assert client.search("q1") == []
    with pytest.raises(RuntimeError) as ei:
        client.search("q2")
    assert ei.value.loai == "het_ngan_sach"
    assert len(ghi.calls) == 1


# ════════════════════════════════════════════════════════════════════════════
# Khoá không bao giờ rò ra ngoài
# ════════════════════════════════════════════════════════════════════════════

def _phan_hoi_vang_vong_khoa() -> Dict[str, Any]:
    """Phản hồi 'xấu nhất': mọi chỗ KHÔNG ánh xạ vào bản ghi đều echo khoá (không thể loại trừ tuyệt đối)."""
    hit = _hit(institutions=[f"echo x-api-key: {CLE_SENTINEL}"], population_type=f"api_key={CLE_SENTINEL}")
    hit["debug"] = {"headers": {"x-api-key": CLE_SENTINEL}, "url": f"{ENDPOINT}?api_key={CLE_SENTINEL}"}
    body = _phan_hoi(hit)
    body["debug"] = f"x-api-key: {CLE_SENTINEL}"
    return body


def test_key_does_not_leak_through_the_success_path(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    client, ghi = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi_vang_vong_khoa()), cache=True)
    recs = client.search("chronic kidney disease")
    assert recs and ghi.calls, "phải đi qua HttpClient thật"
    assert ghi.calls[0].headers["x-api-key"] == CLE_SENTINEL, "khoá phải đi bằng header x-api-key"
    assert CLE_SENTINEL not in json.dumps([r.to_dict() for r in recs], ensure_ascii=False, default=str)
    assert _noi_dung_moi_tep(tmp_path / "http_cache"), "test vô nghĩa nếu HttpClient không hề ghi cache"
    _kiem_khong_ro_khoa(client, caplog, None, tmp_path)


def test_key_does_not_leak_through_save_raw_files_or_the_http_cache(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    client, _ = _client(monkeypatch, tmp_path, _tra(200, _phan_hoi_vang_vong_khoa()), cache=True)
    client.search("chronic kidney disease")
    client.search("chronic kidney disease")                         # lượt hai đọc lại từ cache: vẫn parse được
    assert client.http.cache_hit_count == 1
    for duong, noi_dung in _noi_dung_moi_tep(tmp_path / "http_cache"):
        assert CLE_SENTINEL not in noi_dung, f"khoá nằm trong tệp cache HTTP: {duong.name}"
    for duong, noi_dung in _noi_dung_moi_tep(tmp_path / "data"):
        assert CLE_SENTINEL not in noi_dung, f"khoá nằm trong tệp dữ liệu: {duong}"


@pytest.mark.parametrize("status, body, headers", [
    pytest.param(401, {"detail": f"Invalid API key {CLE_SENTINEL}"}, {}, id="401-echo-khoa"),
    pytest.param(403, {"detail": f"feature_not_allowed for x-api-key {CLE_SENTINEL}"}, {}, id="403-echo-khoa"),
    pytest.param(422, {"detail": [{"msg": f"bad header value {CLE_SENTINEL}"}]}, {}, id="422-echo-khoa"),
    pytest.param(429, {"detail": f"{MSG_HET_QUOTA} key={CLE_SENTINEL}"}, {}, id="429-echo-khoa"),
    pytest.param(500, {"detail": f"boom {CLE_SENTINEL}"}, {}, id="500-echo-khoa"),
])
def test_error_text_echoing_the_key_is_not_leaked(monkeypatch, tmp_path, caplog, status, body, headers):
    caplog.set_level(logging.DEBUG)
    client, _ = _client(monkeypatch, tmp_path, _tra(status, body, headers))
    ket_qua, loi = _chay(client, "chronic kidney disease")
    _kiem_khong_ro_khoa(client, caplog, loi, tmp_path)


@pytest.mark.parametrize("cach_loi", [
    pytest.param(lambda goi: (_ for _ in ()).throw(requests.ConnectionError(
        f"HTTPSConnectionPool(host='api.consensus.app'): failed, headers={{'x-api-key': '{CLE_SENTINEL}'}}")),
        id="mat-mang-kem-header"),
    pytest.param(lambda goi: (_ for _ in ()).throw(requests.Timeout(
        f"Read timed out; request headers: x-api-key: {CLE_SENTINEL}")), id="timeout-kem-header"),
])
def test_raw_transport_exception_carrying_the_key_is_scrubbed_defensively(monkeypatch, tmp_path, caplog, cach_loi):
    """Phòng thủ chiều sâu: dù exception thô của tầng vận chuyển chứa nguyên header kèm khoá, khoá vẫn không được ra khỏi
    connector qua exception hay log."""
    caplog.set_level(logging.DEBUG)
    client, _ = _client(monkeypatch, tmp_path, cach_loi)
    ket_qua, loi = _chay(client, "chronic kidney disease")
    if loi is None:
        assert ket_qua == []
    _kiem_khong_ro_khoa(client, caplog, loi, tmp_path)


def test_exception_messages_of_every_class_are_free_of_the_key(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    for i, (status, body, headers, _loai) in enumerate(p.values[:4] for p in _LOI_HTTP):
        client, _ = _client(monkeypatch, tmp_path, _tra(status, body, headers))
        _, loi = _chay(client, f"chronic kidney disease {i}")
        assert loi is not None
        _kiem_khong_ro_khoa(client, caplog, loi, tmp_path)


def test_the_budget_exhaustion_message_and_state_file_are_free_of_the_key(monkeypatch, tmp_path, caplog):
    caplog.set_level(logging.DEBUG)
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 1)
    client, _ = _client(monkeypatch, tmp_path)
    client.search("q1")
    _, loi = _chay(client, "q2")
    assert loi is not None and loi.loai == "het_ngan_sach"
    _kiem_khong_ro_khoa(client, caplog, loi, tmp_path)


# ════════════════════════════════════════════════════════════════════════════
# Cầu nối với bậc thang: lỗi CHỐT / không chốt quan sát được qua `chay_du_phong_ingest` (lớp Consensus THẬT)
# ════════════════════════════════════════════════════════════════════════════

KHU_CAU_NOI = "Khu kiểm cầu nối Consensus"
TRUY_VAN_CAU_NOI = [
    "heart failure sglt2 bridge query one",
    "colchicine myocardial infarction bridge query two",
    "dapt duration coronary bridge query three",
]


def _dung_kich_ban_bac_thang(monkeypatch) -> Tuple[List[str], List[dict]]:
    monkeypatch.setattr(settings, "use_mock_sources", False)   # ở mock bậc thang hoàn toàn trơ
    monkeypatch.setitem(CLINICAL_AREAS, KHU_CAU_NOI, list(TRUY_VAN_CAU_NOI))
    logs = [dict(source=s, api_endpoint="https://fake.example.org/", query=f"[{KHU_CAU_NOI}] {q}", record_count=0,
                 status="ok", error_message=None, mode="live")
            for q in TRUY_VAN_CAU_NOI for s in ("pubmed", "europepmc", "crossref")]
    return [KHU_CAU_NOI], logs


def _xac_minh_gia(rec: RawRecord, **_kw: Any) -> KetQuaXacMinh:
    """Cơ quan đăng ký giả: luôn xác minh được, trả bản ghi 'của PubMed' (đích tới là hành vi của connector, không của cổng)."""
    return KetQuaXacMinh(RawRecord(
        source="pubmed", title=rec.title, pmid="7000001", doi=(rec.doi or "").lower(), study_type="systematic_review",
        publication_date="2025-03-01", journal_or_organization="The Lancet",
        abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).",
        raw={"phat_hien_boi": rec.source, "xac_minh": {"phuong_phap": "gia", "do_giong": 1.0}}), "xac_minh_duoc")


def _chay_bac_thang(client: Any, areas: List[str], logs: List[dict]):
    return chay_du_phong_ingest([], logs, areas, 10, None, clients=[client], khoa_kho_fn=lambda q, *a, **k: set(),
                                xac_minh_fn=_xac_minh_gia, ngu_fn=lambda _s: None)


@pytest.mark.parametrize("status, body, headers, loai", [
    pytest.param(401, {"detail": "Invalid API key"}, {}, "key_sai", id="401"),
    pytest.param(402, {"detail": "Payment required"}, {}, "thanh_toan_qua_han", id="402"),
    pytest.param(403, {"detail": "feature_not_allowed"}, {}, "tinh_nang_khong_cho_phep", id="403"),
    pytest.param(429, {"detail": MSG_HET_QUOTA}, {}, "het_quota", id="429-het-quota"),
])
def test_a_chot_error_from_the_real_client_stops_the_tier_after_one_request(monkeypatch, tmp_path, status, body, headers,
                                                                          loai):
    areas, logs = _dung_kich_ban_bac_thang(monkeypatch)
    client, ghi = _client(monkeypatch, tmp_path, _tra(status, body, headers))
    ban_ghi, log_them, tom_tat = _chay_bac_thang(client, areas, logs)
    assert len(ghi.calls) == 1, "lỗi chốt: các truy vấn còn lại không được gửi"
    assert ban_ghi == []
    loi_chot = tom_tat["tang"]["consensus"]["loi_chot"]
    assert loi_chot and loai in str(loi_chot), loi_chot
    assert tom_tat["van_thieu"] == len(TRUY_VAN_CAU_NOI), "truy vấn bị bỏ qua phải được báo là VẪN thiếu, không im lặng"
    assert CLE_SENTINEL not in json.dumps(tom_tat, ensure_ascii=False, default=str)
    assert all(CLE_SENTINEL not in json.dumps(lg, default=str) for lg in log_them)


@pytest.mark.parametrize("status, body, headers, loai", [
    pytest.param(429, {"detail": MSG_QUA_NHANH}, {"Retry-After": "1"}, "gioi_han_toc_do", id="429-qua-nhanh"),
    pytest.param(422, {"detail": [{"msg": "invalid", "type": "value_error"}]}, {}, "tham_so_sai", id="422"),
    pytest.param(200, ["khong", "phai", "dict"], {}, "phan_hoi_khong_hop_le", id="200-hong"),
])
def test_a_non_chot_error_repeated_on_every_call_trips_only_the_consecutive_error_breaker(
        monkeypatch, tmp_path, status, body, headers, loai):
    """Lỗi KHÔNG chốt không dừng tầng ngay (một lỗi lẻ vẫn thử tiếp — xem test_fallback_ladder), nhưng nếu MỌI lời gọi
    đều lỗi thì cầu dao "3 lỗi liên tiếp" dừng tầng: phản hồi hỏng vẫn có thể bị Consensus tính lượt, nên không đốt
    hết quota tháng vô ích. Phải BÁO (loi_chot = loi_lien_tiep:<loai>), không im lặng."""
    areas, logs = _dung_kich_ban_bac_thang(monkeypatch)
    client, ghi = _client(monkeypatch, tmp_path, _tra(status, body, headers))
    _, _, tom_tat = _chay_bac_thang(client, areas, logs)
    assert len(ghi.calls) == 3, "cầu dao dừng tầng sau 3 lỗi liên tiếp, không thử hết 5 truy vấn"
    assert tom_tat["tang"]["consensus"]["loi_chot"] == f"loi_lien_tiep:{loai}"
    assert tom_tat["van_thieu"] == len(TRUY_VAN_CAU_NOI), "truy vấn chưa được bù phải được báo là VẪN thiếu"


def test_a_client_that_hits_its_own_budget_is_a_chot_error_for_the_ladder(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "consensus_max_calls_per_run", 1)
    areas, logs = _dung_kich_ban_bac_thang(monkeypatch)
    client, ghi = _client(monkeypatch, tmp_path)
    _, _, tom_tat = _chay_bac_thang(client, areas, logs)
    assert len(ghi.calls) == 1
    loi_chot = tom_tat["tang"]["consensus"]["loi_chot"]
    assert loi_chot and "het_ngan_sach" in str(loi_chot)
    assert tom_tat["van_thieu"] >= 1


def test_the_real_client_feeds_the_ladder_with_verifiable_hits(monkeypatch, tmp_path):
    areas, logs = _dung_kich_ban_bac_thang(monkeypatch)

    def _theo_truy_van(goi):
        n = TRUY_VAN_CAU_NOI.index(goi.params["query"]) + 1
        return _PhanHoiGia(200, _phan_hoi(_hit(title=f"Synthetic bridge paper {n}", doi=f"10.5555/bridge.{n}")),
                           goi.full_url)

    client, ghi = _client(monkeypatch, tmp_path, _theo_truy_van)
    ban_ghi, log_them, tom_tat = _chay_bac_thang(client, areas, logs)
    assert len(ghi.calls) == 3
    assert [g.params["query"] for g in ghi.calls] == TRUY_VAN_CAU_NOI, "gửi theo thứ tự tệ-nhất-trước = thứ tự truy vấn khi hoà"
    for goi in ghi.calls:
        assert goi.headers["x-api-key"] == CLE_SENTINEL and int(goi.params["page_size"]) <= 20
        assert str(goi.params["medical_mode"]).lower() == "true"
    c = tom_tat["tang"]["consensus"]
    assert c["da_goi"] == 3 and c["tim_thay"] == 3 and c["xac_minh_duoc"] == 3 and c["loi_chot"] is None
    assert len(ban_ghi) == 3 and all(r.source == "pubmed" for r in ban_ghi), "phát hiện vào kho là bản ghi của cơ quan đăng ký"
    assert all((r.raw or {}).get("phat_hien_boi") == "consensus" for r in ban_ghi)
    for lg in log_them:
        assert set(lg) == {"source", "api_endpoint", "query", "record_count", "status", "error_message", "mode"}
        assert lg["source"] == "consensus" and lg["mode"] == "live"
    assert CLE_SENTINEL not in json.dumps(tom_tat, ensure_ascii=False, default=str)


# ════════════════════════════════════════════════════════════════════════════
# KHOA_QUA_PROXY (24/09/2026): khoá do agent proxy của môi trường Cloud gắn vào header
# ════════════════════════════════════════════════════════════════════════════

def test_qua_proxy_thieu_khoa_van_goi_va_khong_gui_x_api_key_rong(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "khoa_qua_proxy", "consensus")
    client, ghi = _client(monkeypatch, tmp_path, key="")
    client.search("hypertension guideline", max_results=5)
    assert len(ghi.calls) == 1, "khai qua proxy thì không được chặn vì thiếu khoá"
    assert "x-api-key" not in {k.lower() for k in ghi.calls[0].headers}, "không gửi header khoá rỗng"


def test_khong_khai_proxy_thieu_khoa_van_chan(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "khoa_qua_proxy", "scopus")  # khai nguồn KHÁC
    client, ghi = _client(monkeypatch, tmp_path, key="")
    with pytest.raises(RuntimeError):
        client.search("atrial fibrillation")
    assert ghi.calls == []
