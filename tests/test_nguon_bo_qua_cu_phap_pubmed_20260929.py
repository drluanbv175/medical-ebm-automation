"""Nguồn không hiểu thẻ trường PubMed BỎ QUA truy vấn đó — có ghi nhận, không tính là lỗi, không khoẻ giả (29/09/2026).

SỰ CỐ GỐC (data/archive/launchd_weekly.log, lượt weekly_safety.sh 29/09/2026 19:12): app.sources.clinicaltrials ghi
3 lần «400 Client Error: Bad Request» cho `query.term="N Engl J Med"[ta] AND ...` (rồi "Lancet"[ta], "JAMA"[ta]);
source_health của clinicaltrials: requests 48, error 3, health ok. Nguyên nhân: CLINICAL_AREAS có 8 truy vấn quét theo
tạp chí/tổ chức viết bằng cú pháp PubMed, và `sweep_source` gửi MỌI truy vấn tới MỌI nguồn. Đo thêm trên payload thật
đã lưu (data/raw/): Europe PMC, Crossref, OpenAlex trả 200 nhưng là RÁC cho chính các truy vấn đó.

Các test ở đây OFFLINE hoàn toàn (conftest chặn mạng): client thật + HttpClient thật, chỉ thay `session.request`
hoặc `http.get_json`; thư mục dữ liệu/cache chuyển sang tmp_path.
"""
from __future__ import annotations

import ast
import json
import logging
import re
from pathlib import Path
from types import SimpleNamespace

import pytest
import requests

from app.config import CLINICAL_AREAS, settings
from app.services import fallback_ladder
from app.services import ingestion as ing
from app.sources import base
from app.sources.base import LY_DO_BO_QUA_CU_PHAP_PUBMED, la_truy_van_cu_phap_pubmed
from app.sources.clinicaltrials import ClinicalTrialsClient
from app.sources.consensus_api import ConsensusClient
from app.sources.core_api import CoreClient
from app.sources.crossref import CrossrefClient
from app.sources.epistemonikos import EpistemonikosClient
from app.sources.europepmc import EuropePMCClient
from app.sources.openalex import OpenAlexClient
from app.sources.pubmed import PubMedClient
from app.sources.scopus import ScopusClient
from app.sources.semantic_scholar import SemanticScholarClient
from app.sources.serpapi_scholar import SerpApiScholarClient
from app.utils import http as http_mod

REPO_ROOT = Path(__file__).resolve().parent.parent

# Nguyên văn 3 truy vấn trong log sự cố (lấy thẳng từ CLINICAL_AREAS để không lệch khi config đổi chữ).
_TRUY_VAN_SU_CO = [q for q in CLINICAL_AREAS["Tạp chí hàng đầu"]
                   if q.startswith(('"N Engl J Med"[ta]', '"Lancet"[ta]', '"JAMA"[ta]'))]
_TAT_CA_CU_PHAP = [q for a in CLINICAL_AREAS for q in CLINICAL_AREAS[a] if la_truy_van_cu_phap_pubmed(q)]
_TRUY_VAN_CHU_DE = "type 2 diabetes guideline"   # truy vấn chủ đề thường — đối chứng: VẪN phải được gửi

# 8 connector nguồn KHÔNG hiểu thẻ trường PubMed (đo 29/09: 400 hoặc rác; hoặc đọc mã: nhét nguyên chuỗi vào
# cú pháp riêng). PubMed là nguồn duy nhất hiểu (test riêng bên dưới).
_NGUON_KHONG_HIEU = [ClinicalTrialsClient, EuropePMCClient, CrossrefClient, OpenAlexClient,
                     SemanticScholarClient, CoreClient, ScopusClient, EpistemonikosClient]


@pytest.fixture(autouse=True)
def _co_lap(monkeypatch, tmp_path):
    """Cô lập: dữ liệu/cache HTTP về tmp_path, không chờ throttle, khoá giả cho nguồn đòi khoá, tắt proxy khoá.

    `_CACHE_DIR` là hằng module chốt LÚC IMPORT (không theo settings.data_dir) — phải vá riêng, nếu không test
    ghi cache GET 24 giờ vào data/raw/_http_cache/ của cây làm việc."""
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    (tmp_path / "http_cache").mkdir()
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    monkeypatch.setattr(http_mod, "_throttle", lambda url, min_interval: 0.0)
    monkeypatch.setattr(settings, "khoa_qua_proxy", "")
    monkeypatch.setattr(settings, "scopus_api_key", "KHOA_GIA_SCOPUS")
    monkeypatch.setattr(settings, "scopus_insttoken", "")
    monkeypatch.setattr(settings, "scopus_bind_interface", "")
    monkeypatch.setattr(settings, "epistemonikos_api_token", "TOKEN_GIA")
    monkeypatch.setattr(settings, "core_api_key", "KHOA_GIA_CORE")
    monkeypatch.setattr(settings, "serpapi_api_key", "KHOA_GIA_SERPAPI")
    monkeypatch.setattr(settings, "consensus_api_key", "KHOA_GIA_CONSENSUS")
    yield


class _DaGoiMang(Exception):
    """Ném từ get_json giả SAU KHI đã ghi lại lời gọi — connector nào cũng bắt Exception quanh get_json."""


def _client_live(cls, monkeypatch):
    """Client thật ở chế độ live; `http.get_json` bị thay để GHI LẠI lời gọi rồi ném (không rời máy)."""
    client = cls()
    client.use_mock = False
    goi: list = []

    def get_json_gia(url, params=None, **kwargs):
        goi.append((url, dict(params or {})))
        raise _DaGoiMang("mạng bị chặn trong test")

    monkeypatch.setattr(client.http, "get_json", get_json_gia)
    return client, goi


def _phan_hoi(status: int, url: str, payload: dict) -> requests.Response:
    """requests.Response THẬT (để raise_for_status() thật sinh đúng chuỗi «400 Client Error: Bad Request»)."""
    r = requests.Response()
    r.status_code = status
    r.url = url
    r.reason = "Bad Request" if status == 400 else "OK"
    r._content = json.dumps(payload).encode("utf-8")
    r.headers["Content-Type"] = "application/json"
    r.encoding = "utf-8"
    return r


def _clinicaltrials_voi_may_chu_gia(monkeypatch):
    """ClinicalTrialsClient + HttpClient THẬT; máy chủ giả mô phỏng API v2: `query.term` có thẻ «[..]» => HTTP 400
    (tiêu chí độc lập với mã đang kiểm), còn lại 200 {"studies": []}. Trả (client, danh sách query.term đã rời máy)."""
    client = ClinicalTrialsClient()
    client.use_mock = False
    da_gui: list = []

    def request_gia(method, url, params=None, timeout=None, **kwargs):
        term = str((params or {}).get("query.term", ""))
        da_gui.append(term)
        url_day_du = requests.Request(method, url, params=params).prepare().url
        if "[" in term:
            return _phan_hoi(400, url_day_du, {"message": "bad query"})
        return _phan_hoi(200, url_day_du, {"studies": []})

    monkeypatch.setattr(client.http.session, "request", request_gia)
    return client, da_gui


# ════════════════════════════════════════════════════════════════════════════
# 1. MỘT định nghĩa nhận diện duy nhất
# ════════════════════════════════════════════════════════════════════════════

def _regex_the_pubmed_trong(duong_dan: Path) -> int:
    """Đếm lời gọi re.compile(<chuỗi chứa 'ta|' và 'pt|'>) — khớp trên AST (dòng THI HÀNH), bình luận không tính."""
    cay = ast.parse(duong_dan.read_text(encoding="utf-8"))
    dem = 0
    for nut in ast.walk(cay):
        if (isinstance(nut, ast.Call) and isinstance(nut.func, ast.Attribute) and nut.func.attr == "compile"
                and isinstance(nut.func.value, ast.Name) and nut.func.value.id == "re" and nut.args
                and isinstance(nut.args[0], ast.Constant) and isinstance(nut.args[0].value, str)
                and "ta|" in nut.args[0].value and "pt|" in nut.args[0].value):
            dem += 1
    return dem


def test_chi_mot_regex_the_truong_pubmed_trong_toan_app():
    """Trước 29/09/2026 có 3 bản chép trôi lệch (serpapi 7 thẻ, consensus 12, fallback_ladder 17); nay chỉ base.py."""
    noi_co = {str(p.relative_to(REPO_ROOT)): n for p in sorted((REPO_ROOT / "app").rglob("*.py"))
              if (n := _regex_the_pubmed_trong(p))}
    assert noi_co == {"app/sources/base.py": 1}, f"regex thẻ trường PubMed bị chép lại ở: {noi_co}"
    for mod in ("app.sources.serpapi_scholar", "app.sources.consensus_api", "app.services.fallback_ladder"):
        m = __import__(mod, fromlist=["_"])
        assert not hasattr(m, "_CU_PHAP_PUBMED_RE"), f"{mod} còn giữ bản regex riêng"
    assert fallback_ladder.la_truy_van_cu_phap_pubmed is base.la_truy_van_cu_phap_pubmed


def test_moi_truy_van_co_the_ngoac_trong_clinical_areas_deu_duoc_nhan_dien():
    """Bất biến trên CẤU HÌNH SỐNG: truy vấn được nhận diện KHI VÀ CHỈ KHI có thẻ dạng «[chữ]». Ai thêm truy vấn
    dùng thẻ mới (vd [mh:noexp], [Title/Abstract]) sẽ làm test này đỏ — buộc cập nhật CU_PHAP_PUBMED_RE."""
    the_ngoac = re.compile(r"\[[A-Za-z][A-Za-z0-9 /:~-]*\]")
    lech = [q for a in CLINICAL_AREAS for q in CLINICAL_AREAS[a]
            if bool(the_ngoac.search(q)) != la_truy_van_cu_phap_pubmed(q)]
    assert lech == []
    assert len(_TRUY_VAN_SU_CO) == 3 and all(la_truy_van_cu_phap_pubmed(q) for q in _TRUY_VAN_SU_CO)
    assert len(_TAT_CA_CU_PHAP) >= 8, "đối chứng không rỗng: CLINICAL_AREAS có ít nhất 8 truy vấn cú pháp PubMed"


@pytest.mark.parametrize("truy_van,ky_vong", [
    ('"heart failure"[ti]', True),           # [ti] đơn lẻ — bản chép 7 thẻ của serpapi trước đây để lọt
    ('"Lancet"[jour] AND statin', True),     # [jour] — bản 12 thẻ của consensus trước đây để lọt
    ("asthma[TIAB]", True),                  # không phân biệt hoa/thường
    ("FIRST_PDATE:[2020-01-01 TO 2021-01-01]", False),  # cú pháp khoảng GỐC của Europe PMC, không phải thẻ PubMed
    ("COVID-19 [review]", False),
    ("heart failure guideline", False),
    ("", False),
    (None, False),
])
def test_nhan_dien_the_truong(truy_van, ky_vong):
    assert la_truy_van_cu_phap_pubmed(truy_van) is ky_vong


# ════════════════════════════════════════════════════════════════════════════
# 2. Connector: chỉ PubMed nhận; nguồn khác không gọi mạng — kể cả khi gọi search() ngoài ingestion
# ════════════════════════════════════════════════════════════════════════════

def test_pubmed_la_nguon_duy_nhat_hieu_cu_phap_pubmed():
    """PubMed mà bỏ qua thì quét theo tạp chí mất sạch — chốt ngược chiều."""
    client = PubMedClient()
    client.use_mock = False
    assert client.hieu_cu_phap_pubmed is True
    assert all(client.ly_do_bo_qua_truy_van(q) is None for q in _TAT_CA_CU_PHAP)
    assert all(ing._ly_do_bo_qua(client, q) is None for q in _TAT_CA_CU_PHAP)


@pytest.mark.parametrize("cls", _NGUON_KHONG_HIEU, ids=lambda c: c.name)
def test_nguon_khong_hieu_bo_qua_khong_goi_mang_va_van_gui_truy_van_thuong(cls, monkeypatch, caplog):
    caplog.set_level(logging.INFO)
    client, goi = _client_live(cls, monkeypatch)
    assert client.hieu_cu_phap_pubmed is False
    for q in _TAT_CA_CU_PHAP:
        assert client.ly_do_bo_qua_truy_van(q) == LY_DO_BO_QUA_CU_PHAP_PUBMED
        assert client.search(q, clinical_area="Tạp chí hàng đầu", max_results=8, since_date="2026-09-19") == []
    assert goi == [], f"{cls.name}: truy vấn cú pháp PubMed đã rời máy: {goi[:2]}"
    ghi = [r for r in caplog.records if "cú pháp PubMed" in r.getMessage()]
    assert ghi and all(r.levelno == logging.INFO for r in ghi), "bỏ qua phải có log INFO nêu rõ, không phải cảnh báo"
    # Đối chứng: truy vấn chủ đề thường VẪN được gửi (chốt không chặn nhầm).
    assert client.ly_do_bo_qua_truy_van(_TRUY_VAN_CHU_DE) is None
    client.search(_TRUY_VAN_CHU_DE, clinical_area="Nội tiết - Chuyển hóa", max_results=8)
    assert len(goi) == 1, f"{cls.name}: truy vấn thường phải gọi mạng đúng 1 lần"


# ════════════════════════════════════════════════════════════════════════════
# 3. _fetch: dòng SourceLog status="skipped"
# ════════════════════════════════════════════════════════════════════════════

def test_fetch_ghi_skipped_khong_goi_mang_khong_dung_telemetry(monkeypatch):
    client, da_gui = _clinicaltrials_voi_may_chu_gia(monkeypatch)
    q = _TRUY_VAN_SU_CO[0]
    ban_ghi, log = ing._fetch(client, q, "Tạp chí hàng đầu", 8, "2026-09-19")
    assert ban_ghi == [] and da_gui == []
    assert log["status"] == "skipped" and log["mode"] == "live" and log["record_count"] == 0
    assert log["source"] == "clinicaltrials" and log["query"] == f"[Tạp chí hàng đầu] {q}"
    assert log["error_message"].startswith(f"{LY_DO_BO_QUA_CU_PHAP_PUBMED}:")
    assert client.http.health_snapshot()["request_count"] == 0


def test_fetch_che_do_mock_khong_bo_qua():
    """Chế độ mock giữ nguyên hành vi demo/seed (cùng quy ước serpapi_scholar): không bao giờ ra "skipped"."""
    client = ClinicalTrialsClient()
    client.use_mock = True
    _ban_ghi, log = ing._fetch(client, _TRUY_VAN_SU_CO[0], "Tạp chí hàng đầu", 8)
    assert log["status"] == "mock"


def test_fetch_client_khong_khai_nang_luc_giu_hanh_vi_cu():
    """Test double/wrapper cũ không có ly_do_bo_qua_truy_van: _fetch gọi search() như trước."""
    goi: list = []
    client = SimpleNamespace(name="gia", endpoint="http://gia/", use_mock=False,
                             search=lambda q, **kw: goi.append(q) or [])
    _ban_ghi, log = ing._fetch(client, _TRUY_VAN_SU_CO[0], "Tạp chí hàng đầu", 8)
    assert goi == [_TRUY_VAN_SU_CO[0]] and log["status"] == "ok"


# ════════════════════════════════════════════════════════════════════════════
# 4. Tái hiện lượt weekly 29/09/2026 (HttpClient thật, máy chủ giả trả 400 cho truy vấn có thẻ)
# ════════════════════════════════════════════════════════════════════════════

def test_tai_hien_luot_weekly_29_09_truoc_va_sau_ban_va(monkeypatch, tmp_path):
    khu_vuc = list(CLINICAL_AREAS.keys())
    tong = sum(len(CLINICAL_AREAS[a]) for a in khu_vuc)
    so_cu_phap = len(_TAT_CA_CU_PHAP)

    # Đối chứng «TRƯỚC bản vá»: cùng client nhưng ép khai là hiểu cú pháp PubMed => gửi hết như cũ.
    goc, da_gui_goc = _clinicaltrials_voi_may_chu_gia(monkeypatch)
    goc.hieu_cu_phap_pubmed = True
    _r, logs_goc = ing.sweep_source(goc, khu_vuc, max_results_per_query=8, since_date="2026-09-19")
    loi = [lg for lg in logs_goc if lg["status"] == "error"]
    assert len(loi) == ing._MAX_CONSECUTIVE_ERRORS
    assert all("400 Client Error: Bad Request" in lg["error_message"] for lg in loi)
    assert [lg["query"].split("] ", 1)[1] for lg in loi] == _TRUY_VAN_SU_CO   # NEJM, Lancet, JAMA — đúng log
    suc_khoe_goc = ing.summarize_source_health(logs_goc, expected_api_sources=["clinicaltrials"],
                                               expected_feed_sources=[], safety_enabled=False)
    hang_goc = suc_khoe_goc["sources"]["clinicaltrials"]
    # Khớp nguyên văn số liệu của lượt weekly: requests 48, error 3, health ok (breaker cắt 5 truy vấn cuối).
    assert (hang_goc["requests"], hang_goc["error"], hang_goc["health"]) == (tong - 5, 3, "ok")

    # SAU bản vá: không truy vấn có thẻ nào rời máy, không lỗi, không bị breaker cắt, sức khoẻ đo trên đúng số đã gửi.
    # Cache MỚI: cache GET 24 giờ của nhánh đối chứng sẽ trả thay mạng cho 45 truy vấn chủ đề.
    (tmp_path / "http_cache_sau").mkdir()
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache_sau")
    moi, da_gui = _clinicaltrials_voi_may_chu_gia(monkeypatch)
    _r, logs = ing.sweep_source(moi, khu_vuc, max_results_per_query=8, since_date="2026-09-19")
    assert not any("[" in t for t in da_gui)
    assert len(da_gui) == tong - so_cu_phap
    assert len(logs) == tong
    assert [lg for lg in logs if lg["status"] == "error"] == []
    assert sum(lg["status"] == "skipped" for lg in logs) == so_cu_phap
    hang = ing.summarize_source_health(logs, expected_api_sources=["clinicaltrials"], expected_feed_sources=[],
                                       safety_enabled=False)["sources"]["clinicaltrials"]
    assert (hang["requests"], hang["skipped"], hang["error"], hang["health"]) == (tong - so_cu_phap, so_cu_phap,
                                                                                  0, "ok")


def test_sweep_ghi_mot_dong_info_tong_ket_bo_qua(monkeypatch, caplog):
    caplog.set_level(logging.INFO, logger="app.services.ingestion")
    client, _da_gui = _clinicaltrials_voi_may_chu_gia(monkeypatch)
    ing.sweep_source(client, list(CLINICAL_AREAS.keys()), max_results_per_query=8)
    dong = [r for r in caplog.records if r.name == "app.services.ingestion" and "BỎ QUA" in r.getMessage()]
    assert len(dong) == 1 and dong[0].levelno == logging.INFO
    assert f"{LY_DO_BO_QUA_CU_PHAP_PUBMED}×{len(_TAT_CA_CU_PHAP)}" in dong[0].getMessage()


# ════════════════════════════════════════════════════════════════════════════
# 5. Circuit-breaker: dòng skipped TRUNG TÍNH (không là lỗi, cũng không là hồi phục)
# ════════════════════════════════════════════════════════════════════════════

def _sweep_theo_mau(mau: list) -> list:
    luot = iter(mau)

    def fetch(client, query, area, max_results, since_date=None):
        return [], dict(source=client.name, status=next(luot, "ok"), record_count=0, error_message="x")

    _r, logs = ing.sweep_source(SimpleNamespace(name="gia", use_mock=False, endpoint=""),
                                list(CLINICAL_AREAS.keys()), max_results_per_query=8, fetch_fn=fetch)
    return logs


def test_skipped_khong_reset_bo_dem_loi_lien_tiep():
    logs = _sweep_theo_mau(["error", "skipped", "error", "skipped", "error"])
    assert len(logs) == 5, "3 lỗi xen giữa bởi dòng bỏ qua vẫn là 3 lỗi LIÊN TIẾP — breaker phải cắt"


def test_skipped_khong_tinh_la_loi():
    logs = _sweep_theo_mau(["error", "error"] + ["skipped"] * 6 + ["ok"])
    assert len(logs) == sum(len(v) for v in CLINICAL_AREAS.values()), "dòng bỏ qua không được đẩy breaker"


# ════════════════════════════════════════════════════════════════════════════
# 6. summarize_source_health: không pha loãng, không khoẻ giả, không đỏ giả
# ════════════════════════════════════════════════════════════════════════════

def _dong(source: str, status: str, n: int = 1, records: int = 0) -> list:
    return [dict(source=source, status=status, record_count=records, error_message=None) for _ in range(n)]


def test_skipped_khong_pha_loang_ti_le_loi():
    logs = _dong("clinicaltrials", "ok", 3, 1) + _dong("clinicaltrials", "error", 2) + _dong("clinicaltrials",
                                                                                            "skipped", 20)
    hang = ing.summarize_source_health(logs, expected_api_sources=["clinicaltrials"], expected_feed_sources=[],
                                       safety_enabled=False)["sources"]["clinicaltrials"]
    # 2/5 = 0.4 > 0.2 => degraded. Nếu tính 20 dòng bỏ qua là request: 2/25 = 0.08 => "ok" (xanh giả).
    assert (hang["requests"], hang["skipped"], hang["error_rate"], hang["health"]) == (5, 20, 0.4, "degraded")


def _loi_ok(n: int = 2) -> list:
    return _dong("pubmed", "ok", n, 5) + _dong("europepmc", "ok", n, 5) + _dong("crossref", "ok", n, 5)


def test_nguon_tuy_chon_bi_bo_qua_sach_la_not_queried():
    logs = _loi_ok() + _dong("clinicaltrials", "skipped", 8)
    kq = ing.summarize_source_health(logs, expected_api_sources=["pubmed", "europepmc", "crossref", "clinicaltrials"],
                                     expected_feed_sources=[], safety_enabled=False)
    hang = kq["sources"]["clinicaltrials"]
    assert hang["health"] == "not_queried", "bỏ qua sạch: không phải 'ok' (xanh giả), không phải 'unavailable' (đỏ giả)"
    assert (hang["requests"], hang["skipped"], hang["error"]) == (0, 8, 0)
    assert kq["status"] == "PASS", "nguồn TUỲ CHỌN không đo được không được hạ trạng thái lượt chạy"


def test_nguon_bat_buoc_bi_bo_qua_sach_thi_partial_khong_pass():
    logs = _dong("pubmed", "ok", 2, 5) + _dong("europepmc", "ok", 2, 5) + _dong("crossref", "skipped", 8)
    kq = ing.summarize_source_health(logs, expected_api_sources=["pubmed", "europepmc", "crossref"],
                                     expected_feed_sources=[], safety_enabled=False)
    assert kq["sources"]["crossref"]["health"] == "not_queried"
    assert "crossref" not in kq["discovery_core"]["healthy"]
    assert kq["hard_fail_reasons"] == []
    assert "REQUIRED_SOURCE_NOT_QUERIED:crossref" in kq["warnings"]
    assert kq["status"] == "PARTIAL"


# ════════════════════════════════════════════════════════════════════════════
# 7. Hệ quả gom regex: hai tầng TÍNH PHÍ nay bỏ qua cả thẻ mà bản chép riêng từng để lọt
# ════════════════════════════════════════════════════════════════════════════

def _ghi_moi_request(client, monkeypatch) -> list:
    goi: list = []

    def request_gia(*a, **kw):
        goi.append((a, kw))
        raise AssertionError("không được gọi mạng")

    monkeypatch.setattr(client.http.session, "request", request_gia)
    return goi


def test_serpapi_bo_qua_the_ti_truoc_day_lot_qua(monkeypatch):
    client = SerpApiScholarClient()
    client.use_mock = False
    goi = _ghi_moi_request(client, monkeypatch)
    assert client.search('"heart failure"[ti]') == []
    assert goi == [] and client.stats["bo_qua_cu_phap_pubmed"] == 1


def test_consensus_bo_qua_the_jour_truoc_day_lot_qua(monkeypatch):
    client = ConsensusClient()
    client.use_mock = False
    goi = _ghi_moi_request(client, monkeypatch)
    assert client.search('"Lancet"[jour] AND statin') == []
    assert goi == [] and client.stats["bo_qua_cu_phap_pubmed"] == 1
