"""Kiểm connector SerpApi Google Scholar (`app/sources/serpapi_scholar.py`) — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT) và ĐẶC TẢ (SPEC) của giai đoạn
nghiên cứu, KHÔNG đọc mã connector, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

Tất cả test OFFLINE, không có key SerpApi thật và KHÔNG BAO GIỜ gọi serpapi.com:
  * chế độ mock mặc định (conftest ép USE_MOCK_SOURCES=true);
  * chế độ live: monkeypatch `client.http.get_json` (đúng khuôn tests/test_scopus.py), hoặc
    thay `client.http.session` bằng session giả để chạy NGUYÊN lớp HttpClient thật (retry,
    bộ đếm health, che secret) mà không mở socket nào.

Fixture phản hồi dựng theo cấu trúc tài liệu SerpApi (trường `organic_results[]`,
`publication_info.summary`, `inline_links.cited_by`, ...). Chuỗi `summary` và chuỗi
"không có kết quả" là nguyên văn từ tài liệu; các giá trị còn lại là dữ liệu giả rõ ràng
(example-*.org), KHÔNG phải DOI/PMID/bài báo thật.

Key giả `SENTINEL_SERPAPI_KEY_0123` được rải khắp nơi để chứng minh nó không lọt ra log,
exception, health_snapshot, RawRecord hay tệp `save_raw` ghi xuống đĩa.

Trạng thái ngân sách (`serpapi_max_calls_per_run`) là theo TIẾN TRÌNH, nên mỗi test nạp lại
module connector (importlib.reload) để đếm từ 0 và không nhiễm chéo giữa các test.
"""
from __future__ import annotations

import importlib
import json
import logging
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
from urllib.parse import urlencode

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.sources as sources_pkg  # noqa: E402
import app.sources.serpapi_scholar as serpapi_mod  # noqa: E402
from app.config import Settings, settings  # noqa: E402
from app.services.filtering import classify  # noqa: E402
from app.services.normalization import normalize  # noqa: E402
from app.services.pipeline import score_item  # noqa: E402
from app.sources.authority import authority_breakdown_for  # noqa: E402
from app.sources.base import SourceClient  # noqa: E402
from app.utils import http as http_mod  # noqa: E402
from app.utils.http import HttpClient  # noqa: E402

CLE_SENTINEL = "SENTINEL_SERPAPI_KEY_0123"
ENDPOINT = "https://serpapi.com/search.json"
# Nguyên văn theo tài liệu SerpApi: tín hiệu "không có kết quả" hợp lệ (HTTP 200).
LOI_KHONG_CO_KET_QUA = "Google hasn't returned any results for this query."
# Nguyên văn theo tài liệu SerpApi (mẫu snippet của kết quả "Machine learning").
SNIPPET = "… from data is called learning or training. The … machine learning is to find or approximate grou…"

# Các cờ bật/tắt nguồn mà get_enabled_sources() đọc — tắt hết để chỉ còn nguồn đang kiểm.
_CO_ENABLE_CU = (
    "enable_pubmed", "enable_europe_pmc", "enable_crossref", "enable_clinicaltrials",
    "enable_openalex", "enable_semantic_scholar", "enable_scopus", "enable_core",
    "enable_epistemonikos",
)


# ════════════════════════════════════════════════════════════════════════════
# Fixture + helper dùng chung
# ════════════════════════════════════════════════════════════════════════════

def _nap_lai_lop():
    """Nạp lại module connector để bộ đếm ngân sách theo tiến trình về 0."""
    return importlib.reload(serpapi_mod).SerpApiScholarClient


@pytest.fixture(autouse=True)
def _cach_ly_moi_truong(monkeypatch, tmp_path):
    """Cô lập test khỏi .env thật của máy chạy test.

    * key rỗng, nguồn tắt, ngân sách cực lớn (test ngân sách tự đặt trần riêng);
    * `data_dir` trỏ vào thư mục tạm để `save_raw` không ghi vào data/raw thật.
    """
    monkeypatch.setattr(settings, "serpapi_api_key", "")
    monkeypatch.setattr(settings, "enable_serpapi_scholar", False)
    monkeypatch.setattr(settings, "serpapi_max_calls_per_run", 10**6)
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 10**6)
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    yield
    # Dọn trạng thái theo tiến trình: trả trần về rất lớn rồi nạp lại module, để test ngân sách
    # (trần nhỏ, đếm dở) không làm nhiễm các test chạy sau.
    monkeypatch.setattr(settings, "serpapi_max_calls_per_run", 10**6)
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 10**6)
    _nap_lai_lop()


@pytest.fixture
def client_cls(_cach_ly_moi_truong) -> Any:
    """Lớp connector mới nạp: bộ đếm ngân sách theo tiến trình bắt đầu từ 0."""
    return _nap_lai_lop()


def _lop_voi_tran(monkeypatch, tran: int):
    """Đặt trần ngân sách rồi nạp lại module (phòng trường hợp trần được đọc lúc import)."""
    monkeypatch.setattr(settings, "serpapi_max_calls_per_run", tran)
    return _nap_lai_lop()


def _muc(xoa: Tuple[str, ...] = (), **ghi_de: Any) -> Dict[str, Any]:
    """Một phần tử `organic_results[]` dựng theo cấu trúc tài liệu SerpApi (dữ liệu giả)."""
    muc: Dict[str, Any] = {
        "position": 0,
        "title": "Population biology of plants and seed dispersal in fields",
        "result_id": "abcDEF123456",
        "type": "Book",
        "link": "https://example-journal.org/articles/pbp-1983",
        "snippet": SNIPPET,
        "publication_info": {
            "summary": "PJ DiMaggio, WW Powell - American sociological review, 1983 - JSTOR",
            "authors": [
                {
                    "name": "PJ DiMaggio",
                    "link": "https://scholar.google.com/citations?user=aaa",
                    "author_id": "aaa",
                    "serpapi_scholar_link": (
                        "https://serpapi.com/search.json?author_id=aaa&engine=google_scholar_author&hl=en"
                    ),
                },
                {"name": "WW Powell"},
            ],
        },
        "resources": [
            {"title": "example-univ.edu", "file_format": "PDF", "link": "https://example-univ.edu/files/pbp.pdf"},
        ],
        "inline_links": {
            "serpapi_cite_link": "https://serpapi.com/search.json?engine=google_scholar_cite&hl=en&q=abcDEF123456",
            "cited_by": {
                "total": 12,
                "link": "https://scholar.google.com/scholar?cites=1",
                "cites_id": "1",
                "serpapi_scholar_link": (
                    "https://serpapi.com/search.json?as_sdt=80005&cites=1&engine=google_scholar&hl=en"
                ),
            },
            "related_pages_link": "https://scholar.google.com/scholar?q=related:abcDEF123456",
        },
    }
    muc.update(ghi_de)
    for khoa in xoa:
        muc.pop(khoa, None)
    return muc


def _phan_hoi_thanh_cong(*ket_qua: Dict[str, Any], **them: Any) -> Dict[str, Any]:
    """Phản hồi HTTP 200 / status Success có `organic_results`."""
    body: Dict[str, Any] = {
        "search_metadata": {
            "id": "5f1e0c0a1b2c3d4e5f6a7b8c",
            "status": "Success",
            "json_endpoint": "https://serpapi.com/searches/abc/5f1e0c0a1b2c3d4e5f6a7b8c.json",
        },
        "search_parameters": {"engine": "google_scholar", "q": "x", "hl": "en"},
        "search_information": {
            "organic_results_state": "Results for exact spelling",
            "total_results": 1234,
            "query_displayed": "x",
        },
        "organic_results": list(ket_qua),
    }
    body.update(them)
    return body


def _phan_hoi_khong_ket_qua(**them: Any) -> Dict[str, Any]:
    """Tín hiệu 'không có kết quả' hợp lệ theo tài liệu: 200 + Success + error chuẩn + không organic_results."""
    body: Dict[str, Any] = {
        "search_metadata": {"id": "abc", "status": "Success"},
        "search_parameters": {"engine": "google_scholar", "q": "x"},
        "search_information": {"organic_results_state": "Fully empty"},
        "error": LOI_KHONG_CO_KET_QUA,
    }
    body.update(them)
    return body


_MAC_DINH = object()  # phân biệt "không truyền response" với "response là None"


def _client_live(lop, monkeypatch, response: Any = _MAC_DINH, api_key: str = CLE_SENTINEL):
    """Client use_mock=False, `http.get_json` bị thay để ghi lại từng lời gọi thay vì gọi mạng.

    `response` là giá trị trả về (kể cả None/list/chuỗi), hoặc một exception để ném ra.
    Không truyền thì trả 1 kết quả hợp lệ."""
    monkeypatch.setattr(settings, "serpapi_api_key", api_key)
    client = lop()
    client.use_mock = False
    ghi: Dict[str, Any] = {"calls": []}

    def fake_get_json(url, params=None, **kwargs):
        ghi["calls"].append({"url": url, "params": dict(params or {}), "kwargs": kwargs})
        if isinstance(response, BaseException):
            raise response
        return _phan_hoi_thanh_cong(_muc()) if response is _MAC_DINH else response

    monkeypatch.setattr(client.http, "get_json", fake_get_json)
    return client, ghi


def _mot_ban_ghi(lop, monkeypatch, muc: Dict[str, Any], **kwargs: Any):
    """Cho connector đọc đúng MỘT kết quả và trả về RawRecord duy nhất."""
    client, _ = _client_live(lop, monkeypatch, response=_phan_hoi_thanh_cong(muc))
    recs = client.search("chronic kidney disease", **kwargs)
    assert len(recs) == 1, f"kỳ vọng 1 bản ghi, nhận {len(recs)}"
    return recs[0]


def _chay(client, *args: Any, **kwargs: Any):
    """Chạy search() và tách (kết quả, ngoại lệ) để phân loại hành vi."""
    try:
        return client.search(*args, **kwargs), None
    except Exception as exc:
        return None, exc


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


def _raw_json(rec) -> str:
    return json.dumps(rec.raw, ensure_ascii=False, default=str)


def _ra_loi_hoac_rong_kem_canh_bao(client, caplog, *args: Any, **kwargs: Any) -> None:
    """Hành vi chấp nhận được với tình huống MƠ HỒ: hoặc ném lỗi to, hoặc trả [] KÈM cảnh báo.

    Không bao giờ được trả [] im lặng (nguyên tắc 'im lặng khác an toàn') và không bao giờ
    được trả bản ghi nào."""
    caplog.set_level(logging.DEBUG)
    ket_qua, loi = _chay(client, *args, **kwargs)
    if loi is not None:
        return
    assert ket_qua == []
    assert any(r.levelno >= logging.WARNING for r in caplog.records), (
        "trả [] mà không có cảnh báo nào — đây là kiểu rỗng im lặng cần tránh"
    )


def _noi_dung_moi_tep(thu_muc: Path) -> List[Tuple[Path, str]]:
    ra: List[Tuple[Path, str]] = []
    if thu_muc.exists():
        for p in sorted(thu_muc.rglob("*")):
            if p.is_file():
                ra.append((p, p.read_text(encoding="utf-8", errors="replace")))
    return ra


# ── Session giả để chạy NGUYÊN lớp HttpClient thật (retry, health, che secret) ─────────────

class _PhanHoiGia:
    """Giả `requests.Response`: raise_for_status() nhúng URL ĐẦY ĐỦ (kèm api_key) như requests thật."""

    def __init__(self, status_code: int, body: Any, url: str) -> None:
        self.status_code = status_code
        self._body = body
        self.text = json.dumps(body, ensure_ascii=False)
        self.headers: Dict[str, str] = {}
        self.url = url

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            err = requests.HTTPError(f"{self.status_code} Client Error: reason for url: {self.url}")
            err.response = self  # type: ignore[assignment]
            raise err

    def json(self) -> Any:
        return self._body


class _PhienGia:
    """`session.request()` giả: mỗi lần gọi ghi lại URL đầy đủ rồi hỏi `kich_ban` (trả response hoặc ném)."""

    def __init__(self, kich_ban) -> None:
        self.kich_ban = kich_ban
        self.calls: List[str] = []

    def request(self, method, url, params=None, timeout=None, **extra):
        query = urlencode(params or {}, doseq=True)
        day_du = f"{url}?{query}" if query else url
        self.calls.append(day_du)
        return self.kich_ban(day_du)


def _client_http_that(lop, monkeypatch, tmp_path, kich_ban):
    """Client live dùng HttpClient THẬT nhưng session giả; không cache đĩa, không ngủ thật."""
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    monkeypatch.setattr(http_mod.time, "sleep", lambda _s: None)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    client = lop()
    client.use_mock = False
    client.http.cache_ttl = 0
    client.http.min_interval = 0
    client.http.session = _PhienGia(kich_ban)
    return client


def _kiem_khong_ro_khoa(client, caplog, loi: Optional[BaseException]) -> None:
    """Key không được lọt vào log, exception hay telemetry của HttpClient."""
    assert CLE_SENTINEL not in caplog.text
    assert CLE_SENTINEL not in json.dumps(client.http.health_snapshot(), default=str)
    if loi is not None:
        assert CLE_SENTINEL not in str(loi)
        assert CLE_SENTINEL not in repr(loi)
        assert all(CLE_SENTINEL not in str(a) for a in loi.args)


# ════════════════════════════════════════════════════════════════════════════
# Danh tính, cấu hình và đăng ký (HỢP ĐỒNG mục "Registered ..." + settings mới)
# ════════════════════════════════════════════════════════════════════════════

def test_client_identity_name_endpoint_and_http_attribute(client_cls):
    assert client_cls.name == "serpapi_scholar"
    assert client_cls.endpoint == ENDPOINT
    assert issubclass(client_cls, SourceClient)
    client = client_cls()
    # Test phải monkeypatch được client.http.get_json như tests/test_scopus.py.
    assert isinstance(client.http, HttpClient)


def test_settings_defaults_when_env_absent(monkeypatch):
    """Không đặt biến môi trường: key rỗng, nguồn TẮT, ngân sách mặc định 8 (theo spec nghiên cứu)."""
    for ten in ("SERPAPI_API_KEY", "ENABLE_SERPAPI_SCHOLAR", "SERPAPI_MAX_CALLS_PER_RUN"):
        monkeypatch.delenv(ten, raising=False)
    s = Settings()
    assert s.serpapi_api_key == ""
    assert s.enable_serpapi_scholar is False
    assert isinstance(s.serpapi_max_calls_per_run, int)
    assert s.serpapi_max_calls_per_run == 8


def test_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("SERPAPI_API_KEY", "TEST_ENV_KEY")
    monkeypatch.setenv("ENABLE_SERPAPI_SCHOLAR", "true")
    monkeypatch.setenv("SERPAPI_MAX_CALLS_PER_RUN", "3")
    s = Settings()
    assert s.serpapi_api_key == "TEST_ENV_KEY"
    assert s.enable_serpapi_scholar is True
    assert s.serpapi_max_calls_per_run == 3


def test_registered_in_sources_package():
    assert sources_pkg.SerpApiScholarClient is not None
    assert sources_pkg.SerpApiScholarClient.name == "serpapi_scholar"
    assert issubclass(sources_pkg.SerpApiScholarClient, SourceClient)
    assert "SerpApiScholarClient" in sources_pkg.__all__


def test_get_enabled_sources_excludes_serpapi_by_default(monkeypatch):
    for co in _CO_ENABLE_CU:
        monkeypatch.setattr(settings, co, False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", False)
    assert [c.name for c in sources_pkg.get_enabled_sources()] == []


def test_serpapi_is_a_fallback_tier_not_an_enabled_source_when_enabled_with_key(monkeypatch):
    """HỢP ĐỒNG mục 5 (20/09/2026): Scholar KHÔNG còn tham gia vòng quét song song — chỉ `get_fallback_sources()`
    trả nó (khi cờ bật), để bậc thang dự phòng quyết định khi nào mới được gọi."""
    for co in _CO_ENABLE_CU:
        monkeypatch.setattr(settings, co, False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "enable_consensus", False)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    assert [c.name for c in sources_pkg.get_enabled_sources()] == []
    ds = sources_pkg.get_fallback_sources()
    assert [c.name for c in ds] == ["serpapi_scholar"]
    assert isinstance(ds[0], sources_pkg.SerpApiScholarClient)


def test_enabling_without_key_does_not_crash_at_construction_but_search_fails_loudly(monkeypatch):
    """Kiểm key phải nằm trong search() (không trong __init__) — nếu không, get_enabled_sources()
    làm sập cả ingest_all() và để PipelineRun kẹt 'running'."""
    for co in _CO_ENABLE_CU:
        monkeypatch.setattr(settings, co, False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "enable_consensus", False)
    monkeypatch.setattr(settings, "serpapi_api_key", "")
    ds = sources_pkg.get_fallback_sources()
    assert [c.name for c in ds] == ["serpapi_scholar"]
    ds[0].use_mock = False
    with pytest.raises(RuntimeError, match="SERPAPI_API_KEY"):
        ds[0].search("chronic kidney disease")


def test_serpapi_is_never_in_enabled_sources_even_with_other_sources_on(monkeypatch):
    """Trước 20/09/2026 test này đòi Scholar ĐỨNG CUỐI get_enabled_sources() (để dedup không đè bản PubMed).
    Nay Scholar không nằm trong danh sách quét song song nữa (HỢP ĐỒNG mục 5): phát hiện của nó chỉ vào kho
    SAU khi được Crossref/PubMed xác minh, và luôn được nối vào CUỐI all_records của lượt quét."""
    for co in _CO_ENABLE_CU:
        monkeypatch.setattr(settings, co, False)
    for co in ("enable_scopus", "enable_core", "enable_epistemonikos"):
        monkeypatch.setattr(settings, co, True)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    ten = [c.name for c in sources_pkg.get_enabled_sources()]
    assert "serpapi_scholar" not in ten
    assert "consensus" not in ten
    assert [c.name for c in sources_pkg.get_fallback_sources()][-1:] == ["serpapi_scholar"]


def test_main_source_map_contains_serpapi_scholar():
    from app.main import _build_source_map

    smap = _build_source_map()
    assert "serpapi_scholar" in smap
    assert smap["serpapi_scholar"] is sources_pkg.SerpApiScholarClient


def test_cmd_test_live_without_key_fails_loudly(monkeypatch):
    """`python run.py test-live serpapi_scholar <từ khoá>` thiếu key phải nổ RuntimeError rõ ràng."""
    from app.main import cmd_test_live

    monkeypatch.setattr(settings, "serpapi_api_key", "")
    with pytest.raises(RuntimeError, match="SERPAPI_API_KEY"):
        cmd_test_live("serpapi_scholar", "chronic kidney disease")


def test_cmd_test_live_offline_end_to_end_no_key_in_output(monkeypatch):
    """Chạy test-live đầu-cuối với get_json giả ở cấp lớp: có kết quả, không cờ mock, không lộ key."""
    from app.main import cmd_test_live

    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    calls: List[Dict[str, Any]] = []

    def fake_get_json(self, url, params=None, **kwargs):
        calls.append({"url": url, "params": dict(params or {})})
        return _phan_hoi_thanh_cong(_muc(), search_parameters={"engine": "google_scholar", "api_key": CLE_SENTINEL})

    monkeypatch.setattr(HttpClient, "get_json", fake_get_json)
    out = cmd_test_live("serpapi_scholar", "chronic kidney disease", limit=5)
    assert out["source"] == "serpapi_scholar"
    assert out["live"] is True
    assert out["count"] == 1
    assert all(not r["is_mock"] for r in out["results"])
    assert len(calls) == 1
    assert int(calls[0]["params"]["num"]) == 5
    assert CLE_SENTINEL not in json.dumps(out, ensure_ascii=False, default=str)


# ════════════════════════════════════════════════════════════════════════════
# (1) Chế độ mock
# ════════════════════════════════════════════════════════════════════════════

def test_mock_mode_returns_records_tagged_correctly_without_network_or_key(client_cls, monkeypatch):
    client = client_cls()
    assert client.use_mock is True

    def khong_duoc_goi(*a, **kw):
        raise AssertionError("chế độ mock KHÔNG được gọi HTTP")

    monkeypatch.setattr(client.http, "get_json", khong_duoc_goi)
    recs = client.search("atrial fibrillation", clinical_area="Tim mạch")
    assert recs, "mock phải trả dữ liệu minh hoạ cho từ khoá này"
    assert all(r.source == "serpapi_scholar" for r in recs)
    assert all(r.raw.get("_mock") for r in recs)


# ════════════════════════════════════════════════════════════════════════════
# (2) Fail-closed: bật nguồn live mà thiếu key phải nổ RÕ, không trả rỗng im lặng
# ════════════════════════════════════════════════════════════════════════════

def test_live_without_key_raises_clear_error_not_silent_empty(client_cls, monkeypatch):
    client = client_cls()
    client.use_mock = False
    calls: List[Any] = []
    monkeypatch.setattr(client.http, "get_json", lambda *a, **kw: calls.append((a, kw)) or {})
    with pytest.raises(RuntimeError, match="SERPAPI_API_KEY"):
        client.search("atrial fibrillation")
    assert calls == [], "thiếu key thì không được gửi bất kỳ request nào (mỗi request là một search tính phí)"


# ════════════════════════════════════════════════════════════════════════════
# (3) Tham số request: đúng engine/q/api_key/num/as_ylo, đúng MỘT request mỗi search()
# ════════════════════════════════════════════════════════════════════════════

def test_request_params_engine_q_api_key_and_endpoint(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("chronic kidney disease")
    assert len(ghi["calls"]) == 1
    goi = ghi["calls"][0]
    assert goi["url"] == ENDPOINT
    assert goi["params"]["engine"] == "google_scholar"
    assert goi["params"]["q"] == "chronic kidney disease"
    assert goi["params"]["api_key"] == CLE_SENTINEL


def test_api_key_travels_only_as_query_param_not_in_url_or_headers(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("chronic kidney disease")
    goi = ghi["calls"][0]
    assert "?" not in goi["url"] and CLE_SENTINEL not in goi["url"]
    assert CLE_SENTINEL not in json.dumps(goi["kwargs"], default=str)
    assert all(CLE_SENTINEL not in str(v) for v in client.http.session.headers.values())


def test_query_with_quotes_passes_through_unchanged(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch)
    truy_van = '"SGLT2 inhibitors" AND "chronic kidney disease"'
    client.search(truy_van)
    assert ghi["calls"][0]["params"]["q"] == truy_van


@pytest.mark.parametrize("max_results, ky_vong", [(None, 20), (5, 5), (20, 20), (21, 20), (100, 20)])
def test_num_param_is_min_of_max_results_and_20(client_cls, monkeypatch, max_results, ky_vong):
    client, ghi = _client_live(client_cls, monkeypatch)
    if max_results is None:
        client.search("diabetes")  # mặc định của SourceClient.search là 20
    else:
        client.search("diabetes", max_results=max_results)
    assert int(ghi["calls"][0]["params"]["num"]) == ky_vong


@pytest.mark.parametrize("since, nam", [("2023-06-01", 2023), ("2024-01-01", 2024), ("2019-12-31", 2019)])
def test_since_date_becomes_as_ylo_year_inclusive(client_cls, monkeypatch, since, nam):
    """as_ylo là năm BAO GỒM: since_date 2023-06-01 -> 2023 (không trừ 1 như PUBYEAR AFT của Scopus)."""
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("heart failure", since_date=since)
    assert str(ghi["calls"][0]["params"]["as_ylo"]) == str(nam)


def test_no_as_ylo_when_since_date_is_none(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("heart failure")
    assert "as_ylo" not in ghi["calls"][0]["params"]


@pytest.mark.parametrize("hong", ["not-a-date", "", "abcd-ef-gh"])
def test_malformed_since_date_does_not_crash_and_adds_no_as_ylo(client_cls, monkeypatch, hong):
    client, ghi = _client_live(client_cls, monkeypatch)
    recs = client.search("copd", since_date=hong)
    assert len(ghi["calls"]) == 1
    assert "as_ylo" not in ghi["calls"][0]["params"]
    assert len(recs) == 1


def test_never_uses_no_cache_or_async_or_non_json_output(client_cls, monkeypatch):
    """no_cache=true tốn thêm 1 search; async/output khác json làm hỏng dòng ingestion đồng bộ."""
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("chronic kidney disease", since_date="2023-01-01")
    params = ghi["calls"][0]["params"]
    assert str(params.get("no_cache", "false")).lower() not in {"true", "1"}
    assert str(params.get("async", "false")).lower() not in {"true", "1"}
    assert str(params.get("output", "json")).lower() == "json"


def test_exactly_one_http_call_per_search_even_when_more_pages_exist(client_cls, monkeypatch):
    """Mỗi request là một search tính phí: KHÔNG phân trang tự động dù serpapi_pagination.next có mặt."""
    hai_muoi = [_muc(title=f"Kết quả số {i} về bệnh thận mạn") for i in range(20)]
    body = _phan_hoi_thanh_cong(
        *hai_muoi,
        serpapi_pagination={"current": 1, "next": f"{ENDPOINT}?engine=google_scholar&q=x&start=20"},
    )
    client, ghi = _client_live(client_cls, monkeypatch, response=body)
    recs = client.search("chronic kidney disease", max_results=20)
    assert len(ghi["calls"]) == 1
    assert len(recs) == 20


def test_each_search_call_maps_to_exactly_one_http_call(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch)
    client.search("a")
    client.search("b")
    client.search("c")
    assert [g["params"]["q"] for g in ghi["calls"]] == ["a", "b", "c"]


def test_search_returns_no_more_than_max_results(client_cls, monkeypatch):
    sau = [_muc(title=f"Kết quả số {i} về suy tim") for i in range(6)]
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(*sau))
    assert len(client.search("heart failure", max_results=3)) <= 3


# ════════════════════════════════════════════════════════════════════════════
# (4) Tín hiệu "không có kết quả" -> []; mọi lỗi API khác KHÔNG được rỗng im lặng
# ════════════════════════════════════════════════════════════════════════════

def test_documented_no_results_signal_returns_empty_list(client_cls, monkeypatch):
    client, ghi = _client_live(client_cls, monkeypatch, response=_phan_hoi_khong_ket_qua())
    assert client.search("truy van rat hiem khong co ket qua") == []
    assert len(ghi["calls"]) == 1


def test_no_results_signal_without_organic_results_state_still_returns_empty(client_cls, monkeypatch):
    """`organic_results_state` chưa được kiểm cho Scholar nên không được BẮT BUỘC (spec)."""
    body = _phan_hoi_khong_ket_qua()
    del body["search_information"]
    client, _ = _client_live(client_cls, monkeypatch, response=body)
    assert client.search("truy van rat hiem") == []


def test_no_results_signal_with_empty_organic_results_list_returns_empty(client_cls, monkeypatch):
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_khong_ket_qua(organic_results=[]))
    assert client.search("truy van rat hiem") == []


def test_no_results_error_but_organic_results_present_prefers_data(client_cls, monkeypatch):
    """Bẫy lịch sử (spec): 200 + chuỗi no-results NHƯNG organic_results có dữ liệu -> ưu tiên dữ liệu."""
    body = _phan_hoi_khong_ket_qua(organic_results=[_muc()])
    client, _ = _client_live(client_cls, monkeypatch, response=body)
    recs = client.search("chronic kidney disease")
    assert [r.title for r in recs] == [_muc()["title"]]


def test_no_results_string_with_status_error_is_a_failure_not_empty(client_cls, monkeypatch):
    """Tín hiệu hợp lệ đòi search_metadata.status == 'Success'; status 'Error' là thất bại phải nổ to."""
    body = _phan_hoi_khong_ket_qua()
    body["search_metadata"]["status"] = "Error"
    client, _ = _client_live(client_cls, monkeypatch, response=body)
    with pytest.raises(Exception):
        client.search("chronic kidney disease")


_PAYLOAD_LOI_HTTP_200 = [
    pytest.param(
        {"error": "Invalid API key. Your API key should be here: https://serpapi.com/manage-api-key"},
        id="khoa-sai",
    ),
    pytest.param({"error": "Your account has run out of searches."}, id="het-quota"),
    pytest.param({"error": "Missing query `q` parameter."}, id="thieu-tham-so"),
    pytest.param({"error": "Một thông điệp lỗi hoàn toàn mới mà SerpApi vừa đổi lời"}, id="loi-la"),
    pytest.param(
        {
            "error": "We couldn't get valid results for this search. Please try again later.",
            "search_metadata": {"id": "abc", "status": "Error"},
        },
        id="google-phia-sau-loi",
    ),
    pytest.param({"search_metadata": {"id": "abc", "status": "Error"}}, id="status-error-khong-co-khoa-error"),
]


@pytest.mark.parametrize("payload", _PAYLOAD_LOI_HTTP_200)
def test_api_error_payload_on_http_200_is_never_silently_empty(client_cls, monkeypatch, caplog, payload):
    """HttpClient coi HTTP 200 là thành công nên KHÔNG lộ lỗi trong payload: connector PHẢI tự ném,
    nếu không Source Log ghi 'ok / 0 bản ghi' và nguồn hỏng trông như nguồn không có bài."""
    caplog.set_level(logging.DEBUG)
    client, ghi = _client_live(client_cls, monkeypatch, response=payload)
    with pytest.raises(Exception) as ei:
        client.search("chronic kidney disease")
    assert len(ghi["calls"]) == 1, "lỗi API không được kích hoạt thêm request (mỗi request tính phí)"
    assert str(ei.value).strip(), "thông báo lỗi không được rỗng"
    assert CLE_SENTINEL not in str(ei.value)
    assert CLE_SENTINEL not in caplog.text


@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"search_metadata": {"status": "Success"}}, id="success-khong-error-khong-organic"),
        pytest.param({"search_metadata": {"status": "Queued"}}, id="con-queued"),
        pytest.param({"search_metadata": {"status": "Processing"}}, id="con-processing"),
        pytest.param(
            {"search_metadata": {"status": "Success"}, "organic_results": "hong"}, id="organic-khong-phai-list",
        ),
        pytest.param(None, id="payload-none"),
        pytest.param([], id="payload-la-list"),
        pytest.param("khong phai json", id="payload-la-chuoi"),
    ],
)
def test_ambiguous_or_malformed_payload_is_loud_not_silently_empty(client_cls, monkeypatch, caplog, payload):
    """Success nhưng không có lỗi lẫn kết quả ('empty_unconfirmed'), còn Queued/Processing ở chế độ
    đồng bộ, hoặc payload không phải dict: hoặc ném lỗi, hoặc trả [] KÈM cảnh báo — không rỗng im lặng."""
    client, _ = _client_live(client_cls, monkeypatch, response=payload)
    _ra_loi_hoac_rong_kem_canh_bao(client, caplog, "chronic kidney disease")


# ── Lỗi cấp HTTP (401/429/5xx/mạng) chạy qua HttpClient THẬT với session giả ────────────────

def test_http_401_invalid_key_is_loud_and_disables_further_calls(client_cls, monkeypatch, tmp_path, caplog):
    """401 = lỗi cấu hình: không retry, tắt nguồn, báo to. Lần search kế tiếp trong cùng run phải nổ
    ngay mà KHÔNG gửi thêm request nào (spec: 'tắt nguồn và báo to')."""
    caplog.set_level(logging.DEBUG)
    thong_bao = {"error": "Invalid API key. Your API key should be here: https://serpapi.com/manage-api-key"}
    client = _client_http_that(
        client_cls, monkeypatch, tmp_path, lambda url: _PhanHoiGia(401, thong_bao, url)
    )
    with pytest.raises(Exception) as ei:
        client.search("chronic kidney disease")
    _kiem_khong_ro_khoa(client, caplog, ei.value)
    so_goi = len(client.http.session.calls)
    assert so_goi >= 1
    with pytest.raises(Exception) as ei2:
        client.search("heart failure")
    assert len(client.http.session.calls) == so_goi, "nguồn phải tự tắt sau 401, không thử lại"
    _kiem_khong_ro_khoa(client, caplog, ei2.value)


def _tep_thang() -> Path:
    return settings.raw_dir / "_state" / "serpapi_usage.json"


def _da_goi_thang() -> int:
    return json.loads(_tep_thang().read_text(encoding="utf-8"))["da_goi"]


def test_monthly_cap_blocks_without_any_http_request_and_releases_the_process_budget(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 2)
    client, ghi = _client_live(_nap_lai_lop(), monkeypatch)
    client.search("q1")
    client.search("q2")
    with pytest.raises(RuntimeError) as ei:
        client.search("q3")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert len(ghi["calls"]) == 2, "chạm trần THÁNG thì không được gửi request nào nữa"
    assert serpapi_mod._NGAN_SACH["da_goi"] == 2, "lượt bị từ chối phải NHẢ chỗ theo tiến trình đã giữ"
    assert _da_goi_thang() == 2


def test_monthly_count_persists_across_processes_unlike_the_per_process_budget(monkeypatch):
    """Nạp lại module = tiến trình MỚI (bộ đếm theo tiến trình về 0) nhưng tệp tháng vẫn còn."""
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 3)
    c1, _ = _client_live(_nap_lai_lop(), monkeypatch)
    c1.search("a")
    c1.search("b")
    c2, ghi2 = _client_live(_nap_lai_lop(), monkeypatch)
    c2.search("c")
    with pytest.raises(RuntimeError) as ei:
        c2.search("d")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert len(ghi2["calls"]) == 1


def test_a_corrupt_monthly_state_file_blocks_fail_closed_and_is_never_overwritten(monkeypatch):
    client, ghi = _client_live(_nap_lai_lop(), monkeypatch)
    _tep_thang().parent.mkdir(parents=True, exist_ok=True)
    _tep_thang().write_text("{khong phai json", encoding="utf-8", newline="\n")
    with pytest.raises(RuntimeError) as ei:
        client.search("q")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert ghi["calls"] == [], "bộ đếm hỏng thì KHÔNG được gửi request tính phí"
    assert _tep_thang().read_text(encoding="utf-8") == "{khong phai json", "không được ghi đè bằng suy đoán"


def test_a_zero_monthly_cap_locks_the_source_completely(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 0)
    client, ghi = _client_live(_nap_lai_lop(), monkeypatch)
    with pytest.raises(RuntimeError) as ei:
        client.search("q")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert ghi["calls"] == []


@pytest.mark.parametrize("gia_tri", ["200", None, True, 1.5])
def test_a_garbled_monthly_cap_setting_locks_fail_closed(monkeypatch, gia_tri):
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", gia_tri)
    client, ghi = _client_live(_nap_lai_lop(), monkeypatch)
    with pytest.raises(RuntimeError) as ei:
        client.search("q")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert ghi["calls"] == []


def test_refunding_a_local_cache_hit_also_refunds_the_monthly_counter(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 5)
    mod = importlib.reload(serpapi_mod)
    mod._giu_cho_ngan_sach(10)
    mod._BO_DEM_THANG.giu_cho(5)
    assert _da_goi_thang() == 1
    mod._hoan_ngan_sach()
    assert _da_goi_thang() == 0
    assert mod._NGAN_SACH["da_goi"] == 0


def test_quota_exhausted_response_marks_the_whole_month_so_other_processes_stop(monkeypatch):
    client, _ = _client_live(
        _nap_lai_lop(), monkeypatch,
        response={"search_metadata": {"status": "Error"}, "error": "Your account has run out of searches."})
    with pytest.raises(RuntimeError) as ei:
        client.search("q1")
    assert getattr(ei.value, "loai", None) == "het_quota"
    tiep, ghi2 = _client_live(_nap_lai_lop(), monkeypatch)   # tiến trình khác, cùng tháng
    with pytest.raises(RuntimeError) as ei2:
        tiep.search("q2")
    assert getattr(ei2.value, "loai", None) == "het_ngan_sach"
    assert ghi2["calls"] == [], "SerpApi đã báo hết quota tháng: tiến trình khác không được gửi thêm"


def test_doc_ngan_sach_reports_the_month_without_mutating_anything(monkeypatch):
    monkeypatch.setattr(settings, "serpapi_max_calls_per_month", 4)
    client, _ = _client_live(_nap_lai_lop(), monkeypatch)
    client.search("q1")
    truoc = _tep_thang().read_text(encoding="utf-8")
    anh = serpapi_mod.doc_ngan_sach()
    assert (anh["tran_thang"], anh["da_goi_thang"], anh["con_lai_thang"]) == (4, 1, 3)
    assert anh["trang_thai_hong"] is False
    assert _tep_thang().read_text(encoding="utf-8") == truoc


def test_http_429_run_out_of_searches_is_loud_and_stops_remaining_calls(client_cls, monkeypatch, tmp_path, caplog):
    """429 kèm 'run out of searches' = hết quota tháng: fatal, dừng mọi gọi còn lại trong run."""
    caplog.set_level(logging.DEBUG)
    thong_bao = {"error": "Your account has run out of searches."}
    client = _client_http_that(
        client_cls, monkeypatch, tmp_path, lambda url: _PhanHoiGia(429, thong_bao, url)
    )
    with pytest.raises(Exception) as ei:
        client.search("chronic kidney disease")
    _kiem_khong_ro_khoa(client, caplog, ei.value)
    so_goi = len(client.http.session.calls)
    with pytest.raises(Exception) as ei2:
        client.search("heart failure")
    assert len(client.http.session.calls) == so_goi, "hết quota thì không được gọi thêm"
    _kiem_khong_ro_khoa(client, caplog, ei2.value)


def _kich_ban_429_khac(url):
    return _PhanHoiGia(429, {"error": "Too many requests per hour."}, url)


def _kich_ban_503(url):
    body = {
        "error": "We couldn't get valid results for this search. Please try again later.",
        "search_metadata": {"status": "Error"},
    }
    return _PhanHoiGia(503, body, url)


def _kich_ban_mang(url):
    raise requests.ConnectionError(
        "HTTPSConnectionPool(host='serpapi.com', port=443): Max retries exceeded with url: "
        f"{url.replace('https://serpapi.com', '')} (Caused by NewConnectionError('giả lập mất mạng'))"
    )


@pytest.mark.parametrize(
    "kich_ban",
    [
        pytest.param(_kich_ban_429_khac, id="429-rate-limit-theo-gio"),
        pytest.param(_kich_ban_503, id="503-serpapi-phia-sau-loi"),
        pytest.param(_kich_ban_mang, id="loi-mang-thuan"),
    ],
)
def test_transient_http_failures_are_never_silent_and_never_leak_key(
    client_cls, monkeypatch, tmp_path, caplog, kich_ban,
):
    """Lỗi tạm thời: ném lỗi, HOẶC trả [] nhưng bộ đếm failure của HttpClient phải tăng để ingestion
    ghi 'error'. Không bao giờ trả bản ghi (đặc biệt không rơi về mock — bài học D1)."""
    caplog.set_level(logging.DEBUG)
    client = _client_http_that(client_cls, monkeypatch, tmp_path, kich_ban)
    ket_qua, loi = _chay(client, "chronic kidney disease")
    if loi is None:
        assert ket_qua == []
        assert client.http.health_snapshot()["failure_count"] > 0, "lỗi HTTP thành [] im lặng"
    _kiem_khong_ro_khoa(client, caplog, loi)


def test_raw_exception_with_key_in_message_is_scrubbed_defensively(client_cls, monkeypatch, caplog):
    """Phòng thủ chiều sâu: dù exception thô của requests chứa nguyên URL kèm api_key (đúng rủi ro spec
    nêu), key vẫn không được ra khỏi connector qua exception hay log."""
    caplog.set_level(logging.DEBUG)
    loi_tho = requests.ConnectionError(
        "HTTPSConnectionPool(host='serpapi.com'): Max retries exceeded with url: "
        f"/search.json?engine=google_scholar&q=x&api_key={CLE_SENTINEL} (Caused by timeout)"
    )
    client, _ = _client_live(client_cls, monkeypatch, response=loi_tho)
    ket_qua, loi = _chay(client, "chronic kidney disease")
    if loi is None:
        assert ket_qua == []
    _kiem_khong_ro_khoa(client, caplog, loi)


def test_error_text_echoing_key_is_not_leaked(client_cls, monkeypatch, caplog):
    caplog.set_level(logging.DEBUG)
    payload = {"error": f"Invalid API key {CLE_SENTINEL}. Your API key should be here"}
    client, _ = _client_live(client_cls, monkeypatch, response=payload)
    ket_qua, loi = _chay(client, "chronic kidney disease")
    assert loi is not None, "payload lỗi phải nổ to"
    _kiem_khong_ro_khoa(client, caplog, loi)


# ════════════════════════════════════════════════════════════════════════════
# (5) Ánh xạ RawRecord theo spec: không bịa DOI/PMID/abstract, snippet KHÔNG phải abstract
# ════════════════════════════════════════════════════════════════════════════

def test_full_result_maps_all_core_fields(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc())
    assert r.source == "serpapi_scholar"
    assert r.title == "Population biology of plants and seed dispersal in fields"
    assert r.url == "https://example-journal.org/articles/pbp-1983"
    assert r.publication_date == "1983"
    assert "DiMaggio" in (r.authors or "") and "Powell" in (r.authors or "")
    # Nhãn 'is_mock' không được gắn cho bản ghi live.
    assert not r.raw.get("_mock")


def test_unicode_title_is_preserved(client_cls, monkeypatch):
    tieu_de = "Hiệu quả của thuốc ức chế SGLT2 trên bệnh thận mạn: tổng quan"
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(title=tieu_de))
    assert r.title == tieu_de


def test_snippet_is_never_the_abstract_and_is_kept_in_raw(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc())
    assert r.abstract is None
    assert SNIPPET in _raw_json(r)


def test_missing_snippet_gives_abstract_none_not_the_title(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(xoa=("snippet",)))
    assert r.abstract is None


def test_no_doi_or_pmid_is_fabricated_from_title_snippet_or_numeric_url(client_cls, monkeypatch):
    """DOI/PMID chỉ được trích khi link THẬT sự mang chúng. Chuỗi giống DOI trong tiêu đề/snippet,
    hay URL kết thúc bằng dãy số, không phải bằng chứng."""
    muc = _muc(
        title="Trial X reported at 10.1000/khong-phai-doi and PMID 38000001",
        snippet="… doi:10.1234/abcd.5678 … PMID: 38000002 …",
        link="https://www.example-publisher.org/article/38000000",
    )
    r = _mot_ban_ghi(client_cls, monkeypatch, muc)
    assert r.doi is None
    assert r.pmid is None


@pytest.mark.parametrize("link", [
    "https://doi.org/10.1016/j.kint.2024.01.001",
    "https://dx.doi.org/10.1016/j.kint.2024.01.001",
])
def test_doi_carried_in_a_doi_org_link_is_extracted(client_cls, monkeypatch, link):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link=link))
    assert r.doi is not None
    assert r.doi.lower() == "10.1016/j.kint.2024.01.001"
    assert r.pmid is None


def test_doi_carried_in_publisher_doi_path_is_extracted(client_cls, monkeypatch):
    link = "https://www.example-publisher.org/doi/full/10.1056/NEJMoa2204233"
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link=link))
    assert r.doi is not None
    assert r.doi.lower() == "10.1056/nejmoa2204233"


def test_pmid_carried_in_a_pubmed_link_is_extracted(client_cls, monkeypatch):
    link = "https://pubmed.ncbi.nlm.nih.gov/38000000/"
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link=link))
    assert r.pmid == "38000000"
    assert r.doi is None


@pytest.mark.parametrize("link", [
    "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1234567/",
    "https://example.org/article/12345678",
    "https://pubmed.ncbi.nlm.nih.gov/?term=kidney",
])
def test_non_pubmed_links_do_not_yield_a_pmid(client_cls, monkeypatch, link):
    """PMC id không phải PMID; số cuối URL bất kỳ không phải PMID; trang tìm PubMed không có PMID."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link=link))
    assert r.pmid is None


def test_pdf_resource_is_not_promoted_to_url_or_doi_and_is_kept_in_raw(client_cls, monkeypatch):
    """resources[].link là bản PDF bên phải (title là TÊN MIỀN), không phải URL chính thức hay DOI."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc())
    assert r.url == "https://example-journal.org/articles/pbp-1983"
    assert r.doi is None and r.pmid is None
    assert "https://example-univ.edu/files/pbp.pdf" in _raw_json(r)


def test_citation_only_result_without_link_is_kept_flagged_and_never_given_a_made_up_url(client_cls, monkeypatch):
    """Kết quả '[CITATION]' thường không có link: coi link là tuỳ chọn, ghi cờ no_link,
    tuyệt đối không tự dựng URL (vd từ result_id) và không bịa định danh."""
    muc = _muc(
        title="Một trích dẫn không có liên kết bấm được",
        xoa=("link", "resources"),
        type="Citation",
    )
    r = _mot_ban_ghi(client_cls, monkeypatch, muc)
    assert r.url is None
    assert r.doi is None and r.pmid is None and r.abstract is None
    assert "no_link" in _raw_json(r)


def test_missing_publication_info_gives_no_year_no_authors_and_no_crash(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(xoa=("publication_info",)))
    assert r.publication_date is None
    assert not r.authors
    assert r.journal_or_organization is None


@pytest.mark.parametrize("hong", [
    pytest.param({"summary": ""}, id="summary-rong"),
    pytest.param({"summary": None}, id="summary-none"),
    pytest.param({"summary": 12345}, id="summary-la-so"),
    pytest.param({"summary": ["x"]}, id="summary-la-list"),
    pytest.param({}, id="khong-summary"),
    pytest.param("chuoi-lung-tung", id="publication-info-la-chuoi"),
    pytest.param([], id="publication-info-la-list"),
    pytest.param(None, id="publication-info-none"),
])
def test_malformed_publication_info_never_crashes_and_never_guesses_year(client_cls, monkeypatch, hong):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(publication_info=hong))
    assert r.publication_date is None
    assert not r.authors


_NAM_HIEN_TAI = date.today().year

_CA_TRICH_NAM = [
    # 6 chuỗi NGUYÊN VĂN từ tài liệu SerpApi
    ("JL Harper - Population biology of plants., 1977 - cabdirect.org", "1977"),
    ("H Lodish, A Berk, CA Kaiser, M Krieger, MP Scott… - 2008 - books.google.com", "2008"),
    ("MT Madigan, JM Martinko, J Parker - 1997 - researchgate.net", "1997"),
    ("PJ DiMaggio, WW Powell - American sociological review, 1983 - JSTOR", "1983"),
    ("ZH Zhou - 2021 - books.google.com", "2021"),
    ("772 F. 3d 709 - Court of Appeals, Federal Circuit, 2014 - Google Scholar", "2014"),
    # Ca dựng theo định dạng: tên hội nghị chứa năm, tạp chí có ' - ' bên trong
    ("A Smith - Proceedings of the 2019 Conference on Renal Care, 2020 - dl.acm.org", "2020"),
    ("A Smith - Journal of Foo - Part A, 2018 - example.org", "2018"),
    ("A Smith - Nature 2023;5(2):1-9, 2021 - example.org", "2021"),
    ("AB Cd - Journal of Things, 2020 - www.nature.com", "2020"),
    # Dự phòng: năm nằm ở CUỐI chuỗi, không có ' - tên miền'
    ("A Smith - Nature Medicine, 2023", "2023"),
    # Biên năm hợp lệ: 1500 <= năm <= năm hiện tại + 1
    (f"A Smith - Journal of Foo, {_NAM_HIEN_TAI + 1} - example.org", str(_NAM_HIEN_TAI + 1)),
    # Không được đoán: năm ngoài biên, hoặc chỉ là số lẫn trong tên tạp chí
    (f"A Smith - Journal of Foo, {_NAM_HIEN_TAI + 2} - example.org", None),
    ("A Smith - 2500 - example.org", None),
    ("A Smith - 1200 - example.org", None),
    ("A Smith - Journal of Foo - example.org", None),
    ("A Smith - Vol 3019, page 2020 issue - example.org", None),
    ("A Smith - Some Journal, 12023 - example.org", None),
    ("", None),
]


@pytest.mark.parametrize("summary, nam", _CA_TRICH_NAM)
def test_year_parsed_from_publication_info_summary(client_cls, monkeypatch, summary, nam):
    """Quy tắc trích năm ĐÁNG TIN theo spec: KHÔNG lấy 4 chữ số đầu tiên; không khớp thì None."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(publication_info={"summary": summary}))
    assert r.publication_date == nam


def test_publication_date_is_year_only_never_a_made_up_month_or_day(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc())
    assert r.publication_date is not None
    assert re.fullmatch(r"\d{4}", r.publication_date)


def test_unparseable_year_is_flagged_year_unknown_in_raw(client_cls, monkeypatch):
    muc = _muc(publication_info={"summary": "A Smith - Journal of Foo - example.org"})
    r = _mot_ban_ghi(client_cls, monkeypatch, muc)
    assert r.publication_date is None
    assert "year_unknown" in _raw_json(r)


def test_year_unknown_result_is_not_dropped_when_since_date_is_given(client_cls, monkeypatch):
    """as_ylo đã lọc phía server: bài không rõ năm KHÔNG được loại lặng lẽ ở phía client."""
    khong_ro_nam = _muc(
        title="Bài không suy ra được năm xuất bản",
        publication_info={"summary": "A Smith - Journal of Foo - example.org"},
    )
    co_nam = _muc(
        title="Bài có năm xuất bản rõ ràng",
        publication_info={"summary": "A Smith - Journal of Foo, 2024 - example.org"},
    )
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(khong_ro_nam, co_nam))
    tieu_de = [r.title for r in client.search("kidney", since_date="2023-01-01")]
    assert "Bài không suy ra được năm xuất bản" in tieu_de
    assert "Bài có năm xuất bản rõ ràng" in tieu_de


def test_authors_are_split_from_venue_and_summary_is_not_pasted_into_journal(client_cls, monkeypatch):
    """Dán nguyên publication_info.summary vào journal_or_organization làm tên tác giả khớp nhầm alias
    tổ chức uy tín (đã chứng minh ở giai đoạn nghiên cứu): tác giả và venue phải tách riêng."""
    summary = "PJ DiMaggio, WW Powell - American sociological review, 1983 - JSTOR"
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(publication_info={
        "summary": summary,
        "authors": [{"name": "PJ DiMaggio"}, {"name": "WW Powell"}],
    }))
    assert "DiMaggio" in r.authors and "Powell" in r.authors
    if r.journal_or_organization is not None:
        assert r.journal_or_organization != summary
        assert "DiMaggio" not in r.journal_or_organization
        assert "Powell" not in r.journal_or_organization
        assert " - " not in r.journal_or_organization


def test_author_names_matching_authority_aliases_do_not_create_false_authority_match(client_cls, monkeypatch):
    """Tên tác giả 'Gold'/'Nice' trùng alias GOLD/NICE: nếu summary bị dán vào journal thì bản ghi bị coi
    là của tổ chức guideline (dương tính giả uy tín). Với venue tách đúng thì không khớp gì."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(
        title="Local dispersal of seeds in fields",
        publication_info={
            "summary": "A Gold, B Nice - Local Journal of Medicine, 2023 - example.org",
            "authors": [{"name": "A Gold"}, {"name": "B Nice"}],
        },
    ))
    nguon, _ = authority_breakdown_for((r.journal_or_organization, r.source, r.authors, r.title))
    assert nguon is None


def test_author_entries_without_name_do_not_crash(client_cls, monkeypatch):
    muc = _muc(publication_info={
        "summary": "A Smith - Journal of Foo, 2024 - example.org",
        "authors": [{"link": "https://scholar.google.com/citations?user=zzz"}, {"name": "A Smith"}, None, "B Jones"],
    })
    r = _mot_ban_ghi(client_cls, monkeypatch, muc)
    assert "A Smith" in (r.authors or "")


def test_cited_by_total_is_preserved_in_raw_when_present(client_cls, monkeypatch):
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc())
    assert any("cited" in "/".join(p).lower() and str(v) == "12" for p, v in _duyet(r.raw)), (
        "số lần trích dẫn Google Scholar phải còn trong raw"
    )


def test_missing_cited_by_is_not_coerced_to_zero(client_cls, monkeypatch):
    """Khi 0 trích dẫn Scholar thường không có khối cited_by: lưu None/'không rõ', không ép thành 0."""
    muc = _muc(inline_links={"serpapi_cite_link": "https://serpapi.com/search.json?engine=google_scholar_cite"})
    r = _mot_ban_ghi(client_cls, monkeypatch, muc)
    bi_ep_thanh_0 = [
        (p, v) for p, v in _duyet(r.raw)
        if "cited" in "/".join(p).lower() and (v == "0" or (type(v) is int and v == 0))
    ]
    assert bi_ep_thanh_0 == []


def test_one_bad_result_does_not_wipe_out_the_others(client_cls, monkeypatch):
    """Cùng họ lỗi đã vá ở scopus/openalex: MỘT phần tử hỏng không được xoá sạch cả trang."""
    tot = _muc(title="Bài hoàn toàn bình thường")
    hong = [
        None,
        "chuoi-lung-tung",
        42,
        {"link": "https://example.org/khong-co-tieu-de"},
        {"title": "Bài có dữ liệu con hỏng", "publication_info": "rac", "link": 12345,
         "resources": "rac", "inline_links": []},
        tot,
    ]
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(*hong))
    recs = client.search("chronic kidney disease")
    tieu_de_co_nghia = [r.title for r in recs if r.title]
    assert "Bài hoàn toàn bình thường" in tieu_de_co_nghia
    assert set(tieu_de_co_nghia) <= {"Bài hoàn toàn bình thường", "Bài có dữ liệu con hỏng"}, "không được bịa tiêu đề"
    assert all(r.source == "serpapi_scholar" for r in recs)
    for r in recs:
        assert r.url is None or (isinstance(r.url, str) and r.url.startswith(("http://", "https://")))


def test_records_come_only_from_the_response_nothing_fabricated(client_cls, monkeypatch):
    dau_vao = [
        _muc(title="Bài thứ nhất về tăng huyết áp", link="https://example-a.org/1"),
        _muc(title="Bài thứ hai về đái tháo đường", link="https://example-b.org/2"),
        _muc(title="Bài thứ ba về suy tim", link="https://example-c.org/3"),
    ]
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(*dau_vao))
    recs = client.search("chronic disease")
    assert [r.title for r in recs] == [m["title"] for m in dau_vao]
    assert [r.url for r in recs] == [m["link"] for m in dau_vao]
    assert all(r.doi is None and r.pmid is None and r.abstract is None for r in recs)
    assert all(not r.raw.get("_mock") for r in recs)


_TIEU_DE_RUI_RO = [
    "Effect of SGLT2 inhibitors on mortality: a systematic review and meta-analysis",
    "Protocol for a systematic review of statin recommendations",
    "Systematic review: recommendations on eGFR cut-off score for dose adjustment in elderly outpatients with CKD",
    "Parents' recommendations for school nutrition",
]


def _phan_hoi_rui_ro():
    return _phan_hoi_thanh_cong(*[
        _muc(
            title=t,
            xoa=("resources", "type"),
            publication_info={"summary": "A Smith - 2023 - example.org", "authors": [{"name": "A Smith"}]},
        )
        for t in _TIEU_DE_RUI_RO
    ])


def test_title_only_records_get_no_study_type_inferred_from_title(client_cls, monkeypatch):
    """Không đủ tín hiệu sạch (không venue/document_type) thì study_type=None: suy từ tiêu đề làm bản ghi
    'systematic review'/'recommendations' được chấm như bằng chứng mạnh dù không có abstract/định danh."""
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_rui_ro())
    recs = client.search("kidney")
    assert len(recs) == len(_TIEU_DE_RUI_RO)
    assert all(r.study_type is None for r in recs)


def test_title_only_records_can_never_be_tier_a_or_actionable(client_cls, monkeypatch):
    """Hồi quy chấm điểm (đã chứng minh offline ở giai đoạn nghiên cứu): bản ghi chỉ có tiêu đề+link+năm
    không được thành Tier A / actionable — nếu không sẽ chảy vào alert_digest, email/webhook và EBM_MASTER."""
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_rui_ro())
    recs = client.search("kidney")
    assert recs
    for r in recs:
        item = normalize(r)
        score_item(item)
        phan_loai, actionable, _, _ = classify(item)
        assert item["reliability_tier"] != "A", r.title
        assert actionable is False, r.title
        assert phan_loai != "actionable", r.title


# ════════════════════════════════════════════════════════════════════════════
# (7) Key giả không được lọt ra log / exception / health / RawRecord / tệp save_raw
# ════════════════════════════════════════════════════════════════════════════

def _phan_hoi_vang_vong_khoa() -> Dict[str, Any]:
    """Phản hồi 'xấu nhất': mọi chỗ có thể echo đều chứa key (spec: không thể loại trừ tuyệt đối)."""
    key_qs = f"api_key={CLE_SENTINEL}"
    muc = _muc(
        # Năm 2024 để bản ghi sống sót nếu connector lọc lại theo since_date phía client.
        publication_info={"summary": "PJ DiMaggio - Journal of Foo, 2024 - example.org"},
        inline_links={
            "cited_by": {"total": 3, "serpapi_scholar_link": f"{ENDPOINT}?cites=1&engine=google_scholar&{key_qs}"},
            "serpapi_cite_link": f"{ENDPOINT}?engine=google_scholar_cite&q=abc&{key_qs}",
        },
    )
    body = _phan_hoi_thanh_cong(
        muc,
        search_parameters={"engine": "google_scholar", "q": "x", "api_key": CLE_SENTINEL},
        serpapi_pagination={"current": 1, "next": f"{ENDPOINT}?engine=google_scholar&start=10&{key_qs}"},
    )
    body["search_metadata"] = {
        "id": "abc",
        "status": "Success",
        "json_endpoint": f"https://serpapi.com/searches/abc/1.json?{key_qs}",
    }
    return body


def test_key_does_not_leak_into_records_files_logs_or_health(client_cls, monkeypatch, caplog, tmp_path):
    caplog.set_level(logging.DEBUG)
    client, ghi = _client_live(client_cls, monkeypatch, response=_phan_hoi_vang_vong_khoa())
    recs = client.search("chronic kidney disease", since_date="2023-01-01")
    assert len(ghi["calls"]) == 1
    assert recs, "test vô nghĩa nếu không có bản ghi nào để kiểm"
    dump = json.dumps([r.to_dict() for r in recs], ensure_ascii=False, default=str)
    assert CLE_SENTINEL not in dump, "api_key lọt vào trường của RawRecord"
    for duong, noi_dung in _noi_dung_moi_tep(tmp_path / "data"):
        assert CLE_SENTINEL not in noi_dung, f"api_key lọt vào tệp save_raw: {duong.name}"
    _kiem_khong_ro_khoa(client, caplog, None)


def test_key_does_not_leak_through_real_httpclient_success_path(client_cls, monkeypatch, tmp_path, caplog):
    """Chạy NGUYÊN HttpClient (session giả) ở đường thành công với phản hồi echo key."""
    caplog.set_level(logging.DEBUG)
    body = _phan_hoi_vang_vong_khoa()
    client = _client_http_that(client_cls, monkeypatch, tmp_path, lambda url: _PhanHoiGia(200, body, url))
    recs = client.search("chronic kidney disease")
    assert recs
    assert client.http.session.calls, "phải đi qua HttpClient thật"
    assert f"api_key={CLE_SENTINEL}" in client.http.session.calls[0], "key phải đi bằng tham số tên api_key"
    assert CLE_SENTINEL not in json.dumps([r.to_dict() for r in recs], ensure_ascii=False, default=str)
    for duong, noi_dung in _noi_dung_moi_tep(tmp_path / "data"):
        assert CLE_SENTINEL not in noi_dung, f"api_key lọt vào tệp save_raw: {duong.name}"
    _kiem_khong_ro_khoa(client, caplog, None)


# ════════════════════════════════════════════════════════════════════════════
# (6) Ngân sách lời gọi theo tiến trình: serpapi_max_calls_per_run, hết là NỔ TO
# ════════════════════════════════════════════════════════════════════════════

def test_budget_exhaustion_is_loud_and_sends_no_further_request(monkeypatch):
    lop = _lop_voi_tran(monkeypatch, 3)
    client, ghi = _client_live(lop, monkeypatch)
    for i in range(3):
        assert client.search(f"truy van {i}")
    assert len(ghi["calls"]) == 3
    with pytest.raises(Exception) as ei:
        client.search("truy van vuot tran")
    assert len(ghi["calls"]) == 3, "hết ngân sách thì không được gửi thêm request tính phí"
    thong_bao = str(ei.value)
    assert re.search(r"(?i)serpapi_max_calls_per_run|budget|ngân sách|hạn mức", thong_bao), thong_bao
    assert CLE_SENTINEL not in thong_bao
    with pytest.raises(Exception):
        client.search("van vuot tran lan nua")
    assert len(ghi["calls"]) == 3, "vẫn phải nổ to ở mọi lần sau, không tự hồi phục im lặng"


def test_budget_is_shared_per_process_across_client_instances(monkeypatch):
    """Ingestion tạo instance mới mỗi lượt và research/manager.py, dossier.py tạo instance riêng:
    trần phải tính cho cả TIẾN TRÌNH, không phải mỗi instance."""
    lop = _lop_voi_tran(monkeypatch, 3)
    a, ghi_a = _client_live(lop, monkeypatch)
    b, ghi_b = _client_live(lop, monkeypatch)
    a.search("q1")
    a.search("q2")
    assert b.search("q3")
    assert len(ghi_a["calls"]) + len(ghi_b["calls"]) == 3
    with pytest.raises(Exception):
        b.search("q4")
    with pytest.raises(Exception):
        a.search("q5")
    assert len(ghi_a["calls"]) + len(ghi_b["calls"]) == 3


def test_mock_searches_do_not_consume_the_billed_call_budget(monkeypatch):
    lop = _lop_voi_tran(monkeypatch, 1)
    mock_client = lop()
    assert mock_client.use_mock is True
    for _ in range(5):
        assert mock_client.search("atrial fibrillation", clinical_area="Tim mạch")
    live, ghi = _client_live(lop, monkeypatch)
    assert live.search("chronic kidney disease")
    assert len(ghi["calls"]) == 1
    with pytest.raises(Exception):
        live.search("truy van thu hai")


# ════════════════════════════════════════════════════════════════════════════
# Vòng sửa lỗi sau rà soát 20/09/2026: DOI dính đuôi URL, lệch schema im lặng, rò khoá qua cache đĩa
# và __context__, truy vấn cú pháp PubMed / PII / max_results <= 0. Mọi DOI/URL dưới đây là DỮ LIỆU GIẢ.
# ════════════════════════════════════════════════════════════════════════════

_CA_DOI_URL_NXB = [
    # bioRxiv/medRxiv: 'vN' là dấu phiên bản của URL, KHÔNG thuộc DOI (tiền tố 10.1101).
    ("https://www.medrxiv.org/content/10.1101/2099.01.02.999001v1.full", "10.1101/2099.01.02.999001"),
    ("https://www.medrxiv.org/content/10.1101/2099.01.02.999001v2.full.pdf", "10.1101/2099.01.02.999001"),
    ("https://www.medrxiv.org/content/10.1101/2099.01.02.999001v1.full-text", "10.1101/2099.01.02.999001"),
    ("https://www.biorxiv.org/content/10.1101/2099.03.04.999002v1", "10.1101/2099.03.04.999002"),
    ("https://www.biorxiv.org/content/10.1101/2099.03.04.999002v2.abstract", "10.1101/2099.03.04.999002"),
    # Springer: đuôi /tables/N, /figures/N, /fulltext.html.
    ("https://link.springer.com/article/10.1007/s00000-099-00001-x/tables/1", "10.1007/s00000-099-00001-x"),
    ("https://link.springer.com/article/10.1007/s00000-099-00001-x/figures/2", "10.1007/s00000-099-00001-x"),
    ("https://link.springer.com/article/10.1007/s00000-099-00001-x/fulltext.html", "10.1007/s00000-099-00001-x"),
    # Nền tảng Silverchair (OUP...): mã bài toàn chữ số + tên tệp đứng SAU DOI.
    ("https://academic.oup.com/example-j/advance-article/doi/10.1093/example-j/abc123/7000001",
     "10.1093/example-j/abc123"),
    ("https://academic.oup.com/example-j/advance-article-pdf/doi/10.1093/example-j/abc123/7000002/abc123.pdf",
     "10.1093/example-j/abc123"),
    ("https://academic.oup.com/example-j/article/doi/10.1093/example-j/abc123/7000003?login=false",
     "10.1093/example-j/abc123"),
    # doi.org: đường dẫn CHÍNH LÀ DOI; chỉ bỏ hậu tố phiên bản của 10.1101.
    ("https://doi.org/10.1101/2099.03.04.999002v1", "10.1101/2099.03.04.999002"),
    # ĐỐI CHỨNG — không được cắt sai DOI hợp lệ.
    ("https://academic.oup.com/example-j/article/doi/10.1093/example-j/abc123", "10.1093/example-j/abc123"),
    ("https://www.example-publisher.org/doi/full/10.1016/S0140-6736(20)30183-5", "10.1016/S0140-6736(20)30183-5"),
    ("https://www.example-publisher.org/doi/full/10.5555/abcv2", "10.5555/abcv2"),
    ("https://www.example-publisher.org/doi/10.1000/182", "10.1000/182"),
    ("https://www.example-publisher.org/doi/10.1000/full.2099", "10.1000/full.2099"),
    ("https://doi.org/10.1000/summary.2099", "10.1000/summary.2099"),
]


@pytest.mark.parametrize("link, doi_dung", _CA_DOI_URL_NXB)
def test_doi_from_publisher_or_preprint_url_carries_no_url_tail(client_cls, monkeypatch, link, doi_dung):
    """DOI trích từ URL không được dính dấu phiên bản 'vN', mã bài, đuôi trang hay tên tệp: DOI sai vẫn
    hợp cú pháp nên lọt vào cột doi + khoá dedup và không tra ngược được ('không bịa DOI')."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link=link))
    assert r.doi == doi_dung


def test_publisher_url_without_doi_string_still_yields_no_doi(client_cls, monkeypatch):
    """Bản sửa đuôi URL không được biến thành 'đoán DOI': mã bài nhà xuất bản không chứa 10.xxxx thì doi=None."""
    r = _mot_ban_ghi(client_cls, monkeypatch, _muc(link="https://academic.oup.com/example-j/article/44/1/1/7000004"))
    assert r.doi is None


@pytest.mark.parametrize("gia_tri", [{"title": "khong-phai-danh-sach"}, "hong", 42], ids=["dict", "chuoi", "so"])
def test_organic_results_of_wrong_type_raises_schema_error_not_empty(client_cls, monkeypatch, gia_tri):
    """`organic_results` HIỆN DIỆN nhưng sai kiểu = nghi SerpApi đổi schema: phải NÉM (đã tốn 1 search),
    không được coi là 'rỗng' rồi để Source Log ghi ok/0."""
    client, ghi = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(organic_results=gia_tri))
    with pytest.raises(RuntimeError) as ei:
        client.search("chronic kidney disease")
    assert ei.value.loai == "phan_hoi_khong_hop_le"
    assert len(ghi["calls"]) == 1
    assert CLE_SENTINEL not in str(ei.value)


def _muc_doi_ten_truong():
    """Kết quả mà SerpApi 'đổi tên' trường title -> name (kịch bản trôi schema)."""
    m = _muc()
    m["name"] = m.pop("title")
    return m


@pytest.mark.parametrize("trang", [
    pytest.param([_muc_doi_ten_truong() for _ in range(3)], id="doi-ten-title-thanh-name"),
    pytest.param([_muc(xoa=("title",)) for _ in range(3)], id="thieu-title"),
    pytest.param([None, "chuoi", 7], id="khong-phai-dict"),
])
def test_page_where_every_item_is_dropped_raises_instead_of_silent_ok_zero(client_cls, monkeypatch, caplog, trang):
    """200/Success có organic_results KHÔNG rỗng nhưng không phần tử nào dùng được: trả [] sẽ thành
    'ok / 0 bản ghi' im lặng dù đã tốn 1 search và nguồn hỏng vĩnh viễn (spec: 'im lặng khác an toàn')."""
    caplog.set_level(logging.DEBUG)
    client, ghi = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(*trang))
    with pytest.raises(RuntimeError) as ei:
        client.search("chronic kidney disease")
    assert ei.value.loai == "phan_hoi_khong_hop_le"
    assert len(ghi["calls"]) == 1
    assert "3" in str(ei.value), "thông báo nên nêu số phần tử bị bỏ"
    _kiem_khong_ro_khoa(client, caplog, ei.value)


def test_non_dict_items_are_counted_in_stats(client_cls, monkeypatch):
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(_muc(), None, "chuoi", 7))
    assert len(client.search("chronic kidney disease")) == 1
    assert client.stats["bo_qua_khong_phai_dict"] == 3


def test_mixed_page_with_some_good_items_still_returns_the_good_ones(client_cls, monkeypatch):
    """Đối chứng: trang lẫn phần tử tốt/xấu vẫn trả phần tốt (thiết kế 'bỏ 1 phần tử hỏng, giữ phần còn lại')."""
    trang = [_muc_doi_ten_truong() for _ in range(9)] + [_muc()]
    client, _ = _client_live(client_cls, monkeypatch, response=_phan_hoi_thanh_cong(*trang))
    assert [r.title for r in client.search("chronic kidney disease")] == [_muc()["title"]]


def test_http_cache_file_on_disk_never_holds_an_echoed_api_key(client_cls, monkeypatch, tmp_path):
    """HttpClient ghi NGUYÊN payload vào data/raw/_http_cache TRƯỚC khi connector che khoá; nếu phản hồi
    echo api_key thì khoá nằm trong thư mục OneDrive. Tệp cache phải được che nhưng vẫn dùng lại được
    (không đốt thêm search)."""
    body = _phan_hoi_vang_vong_khoa()
    client = _client_http_that(client_cls, monkeypatch, tmp_path, lambda url: _PhanHoiGia(200, body, url))
    client.http.cache_ttl = 3600  # bật cache thật (helper tắt để test khác đơn giản)
    assert client.search("chronic kidney disease")
    tep_cache = _noi_dung_moi_tep(tmp_path / "http_cache")
    assert tep_cache, "test vô nghĩa nếu HttpClient không hề ghi cache"
    for duong, noi_dung in tep_cache:
        assert CLE_SENTINEL not in noi_dung, f"api_key nằm trong tệp cache HTTP: {duong.name}"
    # Lần 2 trúng cache (bản đã che vẫn parse được): không request mới rời máy.
    assert client.search("chronic kidney disease")
    assert len(client.http.session.calls) == 1
    assert client.http.cache_hit_count == 1


@pytest.mark.parametrize("max_results", [0, -5])
def test_non_positive_max_results_makes_no_billed_call_and_returns_nothing(monkeypatch, max_results):
    lop = _lop_voi_tran(monkeypatch, 1)
    client, ghi = _client_live(lop, monkeypatch)
    assert client.search("chronic kidney disease", max_results=max_results) == []
    assert ghi["calls"] == [], "max_results <= 0 không được tốn 1 search"
    assert client.search("chronic kidney disease", max_results=5), "ngân sách không được bị trừ oan"
    assert len(ghi["calls"]) == 1


@pytest.mark.parametrize("truy_van", [
    '"N Engl J Med"[ta] AND (guideline[pt] OR practice guideline[pt] OR meta-analysis[pt])',
    "kidney disease[tiab] AND mortality[mh]",
    "atrial fibrillation[dp] anticoagulant[majr]",
    "Lancet[cn] heart failure",
], ids=["ta-pt", "tiab-mh", "dp-majr", "cn"])
def test_pubmed_field_tag_queries_are_skipped_without_billing_the_budget(monkeypatch, caplog, truy_van):
    """Thẻ trường PubMed vô nghĩa với Google Scholar: bỏ qua CÓ cảnh báo + đếm ở stats, không gọi HTTP,
    không trừ ngân sách (mỗi request là 1 search tính phí)."""
    caplog.set_level(logging.DEBUG)
    lop = _lop_voi_tran(monkeypatch, 1)
    client, ghi = _client_live(lop, monkeypatch)
    assert client.search(truy_van) == []
    assert ghi["calls"] == []
    assert client.stats["bo_qua_cu_phap_pubmed"] == 1
    assert any(r.levelno >= logging.WARNING for r in caplog.records), "bỏ qua phải có cảnh báo, không im lặng"
    assert client.search("heart failure"), "truy vấn chủ đề thường vẫn chạy và ngân sách còn nguyên"
    assert len(ghi["calls"]) == 1


def test_pubmed_tag_query_in_mock_mode_is_untouched(monkeypatch):
    """Chế độ mock không đổi hành vi: mọi truy vấn vẫn nhận mock (demo/seed)."""
    lop = _lop_voi_tran(monkeypatch, 1)
    client = lop()
    assert client.use_mock is True
    truy_van = "atrial fibrillation[ta]"
    ket_qua = client.search(truy_van, clinical_area="Tim mạch")
    assert ket_qua, "mock vẫn trả bản ghi cho truy vấn có thẻ PubMed (đối chứng: cùng truy vấn ở chế độ live bị bỏ qua)"
    assert client.stats["bo_qua_cu_phap_pubmed"] == 0


_TRUY_VAN_PII = [
    pytest.param("Nguyen Van A CCCD 012345678901 email bacsi@example.org HbA1c", id="ten-cccd-email"),
    pytest.param("bacsi@example.org SGLT2 inhibitors", id="email"),
    pytest.param("mã bệnh nhân AB123456 HbA1c", id="ma-benh-nhan"),
    pytest.param("SĐT 0901234567 tăng huyết áp", id="sdt"),
    pytest.param("ngày sinh 15/07/1980 đái tháo đường", id="ngay-sinh"),
]


@pytest.mark.parametrize("truy_van", _TRUY_VAN_PII)
def test_query_with_pii_is_refused_before_any_billed_call(monkeypatch, caplog, truy_van):
    """Truy vấn đi qua SerpApi tới Google và bị lưu 31 ngày (ToS): chặn PII/PHI TRƯỚC khi gửi, không tốn
    ngân sách, không nhét truy vấn vào thông báo/log, và một truy vấn xấu không được khoá cả nguồn."""
    caplog.set_level(logging.DEBUG)
    lop = _lop_voi_tran(monkeypatch, 1)
    client, ghi = _client_live(lop, monkeypatch)
    with pytest.raises(RuntimeError) as ei:
        client.search(truy_van)
    assert ei.value.loai == "tham_so_sai"
    assert ghi["calls"] == []
    assert truy_van not in str(ei.value)
    assert "bacsi@example.org" not in str(ei.value) and "bacsi@example.org" not in caplog.text
    assert client.search("SGLT2 inhibitors chronic kidney disease mortality"), "PII không được chốt nguồn"
    assert len(ghi["calls"]) == 1


@pytest.mark.parametrize("truy_van", [
    "SGLT2 inhibitors chronic kidney disease mortality",
    "trials 2015 2016 2017 2018 atrial fibrillation",
    "NCT01234567 semaglutide 2.4 mg",
    "HbA1c 7.5% patients aged 65-74 years",
])
def test_topic_queries_are_not_mistaken_for_pii(client_cls, monkeypatch, truy_van):
    client, ghi = _client_live(client_cls, monkeypatch)
    assert client.search(truy_van)
    assert len(ghi["calls"]) == 1


def _kich_ban_http(status: int, body: Dict[str, Any]):
    return lambda url: _PhanHoiGia(status, body, url)


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_kich_ban_http(401, {"error": "Invalid API key. Your API key should be here"}), id="401"),
    pytest.param(_kich_ban_http(429, {"error": "Your account has run out of searches."}), id="429-het-quota"),
    pytest.param(_kich_ban_http(429, {"error": "Hourly throughput limit exceeded."}), id="429-theo-gio"),
    pytest.param(_kich_ban_http(503, {"error": "We couldn't get valid results. Please try again later."}), id="503"),
    pytest.param(_kich_ban_http(400, {"error": "Missing query `q` parameter."}), id="400"),
    pytest.param(_kich_ban_http(403, {"error": "Forbidden"}), id="403"),
])
def test_http_error_exception_chain_does_not_keep_the_raw_httperror_with_key(
    client_cls, monkeypatch, tmp_path, caplog, kich_ban,
):
    """`raise ... from None` chỉ đặt __suppress_context__: __context__ vẫn trỏ tới requests.HTTPError có
    response.url chứa nguyên api_key. Trình ghi lỗi duyệt chuỗi nguyên nhân sẽ lấy được khoá — exception
    của connector không được giữ tham chiếu nào tới nó."""
    caplog.set_level(logging.DEBUG)
    client = _client_http_that(client_cls, monkeypatch, tmp_path, kich_ban)
    with pytest.raises(RuntimeError) as ei:
        client.search("chronic kidney disease")
    e: Optional[BaseException] = ei.value
    assert e.__context__ is None and e.__cause__ is None
    while e is not None:
        assert CLE_SENTINEL not in str(e) and CLE_SENTINEL not in repr(e)
        assert CLE_SENTINEL not in str(getattr(getattr(e, "response", None), "url", ""))
        e = e.__context__ or e.__cause__
    _kiem_khong_ro_khoa(client, caplog, ei.value)


# ════════════════════════════════════════════════════════════════════════════
# (3) ĐÚNG MỘT request HTTP cho mỗi search() — trên MỌI đường, không riêng đường thành công
# ════════════════════════════════════════════════════════════════════════════
# Bản đầu chỉ đo đường thành công và 401: HttpClient có vòng retry riêng (429/5xx thử lại 1 lần, timeout/
# mất mạng/JSON hỏng thử lại tới http_max_retries=4 lần) nên một truy vấn lỗi gửi 2-5 request tính phí trong
# khi bộ đếm ngân sách chỉ ghi 1. Các test dưới đây chạy NGUYÊN HttpClient với session giả và đếm request.

def _kich_ban_timeout(url):
    raise requests.Timeout(f"Read timed out. (read timeout=30) url={url}")


def _kich_ban_json_hong(url):
    class _Hong(_PhanHoiGia):
        def json(self):
            raise ValueError("Expecting value: line 1 column 1 (char 0)")

    return _Hong(200, {}, url)


@pytest.mark.parametrize("kich_ban", [
    pytest.param(_kich_ban_http(200, {"organic_results": [{"title": "Bai thu nghiem"}]}), id="200-thanh-cong"),
    pytest.param(_kich_ban_http(200, {"error": LOI_KHONG_CO_KET_QUA}), id="200-khong-co-ket-qua"),
    pytest.param(_kich_ban_http(401, {"error": "Invalid API key. Your API key should be here"}), id="401"),
    pytest.param(_kich_ban_http(429, {"error": "Your account has run out of searches."}), id="429-het-quota"),
    pytest.param(_kich_ban_http(429, {"error": "Hourly throughput limit exceeded."}), id="429-theo-gio"),
    pytest.param(_kich_ban_http(500, {"error": "Internal error"}), id="500"),
    pytest.param(_kich_ban_http(503, {"error": "We couldn't get valid results. Please try again later."}),
                 id="503"),
    pytest.param(_kich_ban_http(400, {"error": "Missing query `q` parameter."}), id="400"),
    pytest.param(_kich_ban_http(403, {"error": "Forbidden"}), id="403"),
    pytest.param(_kich_ban_timeout, id="timeout"),
    pytest.param(_kich_ban_mang, id="mat-mang"),
    pytest.param(_kich_ban_json_hong, id="200-json-hong"),
])
def test_exactly_one_http_request_per_search_on_every_path(client_cls, monkeypatch, tmp_path, caplog, kich_ban):
    caplog.set_level(logging.DEBUG)
    client = _client_http_that(client_cls, monkeypatch, tmp_path, kich_ban)
    _chay(client, "chronic kidney disease")
    assert len(client.http.session.calls) == 1, (
        f"mỗi request là 1 search tính phí: nhận {len(client.http.session.calls)} request cho 1 search()"
    )
    assert client.http.request_count == 1


def test_transport_failure_is_not_retried_and_does_not_sleep_needlessly(client_cls, monkeypatch, tmp_path):
    """Timeout/mất mạng: không thử lại và không ngủ backoff vô ích; vẫn tăng failure_count để ingestion ghi
    Source Log = 'error' (không im lặng) và vẫn trả [] chứ không bịa mock (D1)."""
    ngu: List[float] = []
    client = _client_http_that(client_cls, monkeypatch, tmp_path, _kich_ban_timeout)
    monkeypatch.setattr(http_mod.time, "sleep", lambda s: ngu.append(s))
    assert client.search("chronic kidney disease") == []
    assert len(client.http.session.calls) == 1
    assert ngu == [], f"không được ngủ backoff khi không còn lượt thử lại: {ngu}"
    snap = client.http.health_snapshot()
    assert snap["failure_count"] == 1 and snap["success_count"] == 0
    assert CLE_SENTINEL not in json.dumps(snap, default=str)


def test_http_client_of_connector_has_retry_cap_zero(client_cls):
    client = client_cls()
    assert client.http.max_retries == 0


def test_budget_counts_one_per_search_even_on_failure_paths(monkeypatch, tmp_path):
    """Số request thật phải KHỚP số lượt ngân sách đã trừ: 3 search lỗi 503 với trần 2 -> đúng 2 request
    rời máy, lần thứ 3 nổ het_ngan_sach mà không gửi gì."""
    monkeypatch.setattr(settings, "serpapi_max_calls_per_run", 2)
    lop = _nap_lai_lop()
    client = _client_http_that(lop, monkeypatch, tmp_path, _kich_ban_503)
    monkeypatch.setattr(settings, "serpapi_max_calls_per_run", 2)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            client.search("chronic kidney disease")
    assert len(client.http.session.calls) == 2
    with pytest.raises(RuntimeError) as ei:
        client.search("heart failure")
    assert getattr(ei.value, "loai", None) == "het_ngan_sach"
    assert len(client.http.session.calls) == 2
