"""Kiểm BẬC THANG DỰ PHÒNG (`app/services/fallback_ladder.py`) và các điểm nối của nó — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT) và BẢN ĐỒ MÃ (CODE MAP) của giai đoạn nghiên cứu,
KHÔNG đọc mã cài đặt, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

Ý nghĩa nghiệp vụ. Consensus (tầng 1) và SerpApi Google Scholar (tầng 2) là nguồn DỰ PHÒNG có cổng: KHÔNG được tham
gia quét song song; chỉ chạy SAU khi các nguồn miễn phí đã trả lời và chỉ cho (nhóm, truy vấn) còn THIẾU chứng cứ ĐÁNG
TIN, theo bậc thang: sau mỗi tầng, phát hiện đã xác minh được gộp vào, mọi truy vấn vừa chạm được đánh giá lại, và chỉ
truy vấn VẪN thiếu mới lên tầng kế. Những điều được canh chặt:

  * thứ tự "tệ nhất trước" (ít bài đáng tin nhất), hoà thì theo thứ tự nhóm/truy vấn; quyết định cho MỌI truy vấn với
    bốn giá trị `du | thieu | chua_ket_luan | bo_qua_cu_phap_pubmed`; sập nguồn lõi = "chưa kết luận được"
    (KHÔNG leo thang);
  * tầng 1 sửa được truy vấn thì tầng 2 KHÔNG được gọi cho truy vấn đó; tầng 1 tắt thì chỉ tầng 2; cả hai tắt
    hoặc chế độ
    mock thì KHÔNG một lời gọi nào và đầu ra không đổi;
  * lỗi CHỐT (key_sai, thanh_toan_qua_han, tinh_nang_khong_cho_phep, het_quota, het_ngan_sach ...) dừng tầng đó cho phần
    còn lại của lượt chạy và báo phần còn lại là bị bỏ qua, còn tầng kia vẫn chạy tiếp; lỗi không-chốt thì tầng
    vẫn chạy;
  * truy vấn cú pháp PubMed / có dấu hiệu PII không bao giờ bị gửi; Consensus cách nhau >= 1,1 giây (`ngu_fn`
    tiêm được);
  * dòng SourceLog thêm chỉ có ĐÚNG 7 khoá (`SourceLog(**lg)` không try/except — khoá thừa làm sập cả lượt);
  * `ingest_all`: bậc thang chạy SAU mọi lượt quét chính; sức khoẻ nguồn CHÍNH không bị bậc thang ảnh hưởng
    (lỗi dự phòng
    không biến PASS thành FAIL và không che lỗi nguồn chính); lỗi của bậc thang không bao giờ thoát ra khỏi
    `ingest_all`;
    cờ tắt / mock => KHÔNG thêm lời gọi, dòng log nào, khoá chẩn đoán nào (ngoài dấu inert tuỳ chọn);
  * `get_enabled_sources()` không trả tầng dự phòng; `get_fallback_sources()` chỉ trả tầng đang BẬT, theo
    `fallback_order`,
    tên lạ => ValueError.

Mọi test OFFLINE (socket bị chặn, mọi tầng là đối tượng giả hoặc lớp thật đã thay `search`). Dữ liệu là DỮ LIỆU
GIẢ RÕ RÀNG
(DOI tiền tố 10.5555, PMID số nhỏ) — không phải bài báo thật.
"""
from __future__ import annotations

import copy
import importlib
import json
import socket
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Callable, Dict, List, Optional

import pytest
import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.services.fallback_ladder as fl  # noqa: E402


@pytest.fixture(autouse=True)
def _dat_lai_nhip_tang():
    """Nhịp gọi tầng tính THEO TIẾN TRÌNH (module-level): mỗi test bắt đầu sạch, không nhiễm đồng hồ giả của test trước."""
    fl._LAN_GOI_CUOI.clear()
    yield
    fl._LAN_GOI_CUOI.clear()
import app.services.fallback_verification as fv  # noqa: E402
import app.services.ingestion as ing  # noqa: E402
import app.sources as sources_pkg  # noqa: E402
from app.config import CLINICAL_AREAS, Settings, settings  # noqa: E402
from app.models import EvidenceItem, SourceLog  # noqa: E402
from app.services.fallback_ladder import (  # noqa: E402
    bo_sung_neu_thieu,
    chay_du_phong_ingest,
    chon_truy_van_can_bo_sung,
)
from app.services.fallback_verification import KetQuaXacMinh  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402

CLE_SENTINEL = "SENTINEL_CONSENSUS_KEY_0123"
VOCAB_QUYET_DINH = {"du", "thieu", "chua_ket_luan", "bo_qua_cu_phap_pubmed"}
KHOA_SUMMARY = {"active", "so_truy_van", "du", "thieu", "chua_ket_luan", "bo_qua_cu_phap_pubmed", "du_sau_du_phong",
                "van_thieu", "tang", "scite", "quyet_dinh"}
KHOA_TANG = {"da_goi", "tim_thay", "xac_minh_duoc", "bi_loai_chua_xac_minh", "bi_loai_rut_bai", "loi_xac_minh",
             "bo_qua_ngan_sach", "loi_chot"}
KHOA_SCITE = {"da_kiem", "khong_kiem_duoc", "co_thong_bao_bien_tap", "nhieu_trich_dan_phan_bac"}
KHOA_LOG = {"source", "api_endpoint", "query", "record_count", "status", "error_message", "mode"}
LOI_CHOT_CHUNG = ["key_sai", "thanh_toan_qua_han", "tinh_nang_khong_cho_phep", "het_quota", "het_ngan_sach"]
LOI_KHONG_CHOT = ["gioi_han_toc_do", "tham_so_sai", "phan_hoi_khong_hop_le", "khac"]

KHU_A = "Khu thử nghiệm A"
KHU_B = "Khu thử nghiệm B"
QA1 = "sglt2 inhibitors heart failure hospitalisation"
QA2 = "colchicine after myocardial infarction outcomes"
QA3 = "dapt duration after percutaneous coronary intervention"
QA4 = "anticoagulation atrial fibrillation elderly frailty"
QB1 = "steroids community acquired pneumonia mortality"
QB2 = "high flow nasal oxygen bronchiolitis infants"
# Số bài đáng tin lượt này của từng truy vấn (ngưỡng mặc định 3): QA3 đủ, còn lại thiếu.
SO_TIN_CAY = {QA1: 1, QA2: 0, QA3: 3, QA4: 2, QB1: 2, QB2: 0}
# Thứ tự "tệ nhất trước" kỳ vọng: 0 bài (QA2 rồi QB2 theo thứ tự nhóm), 1 bài (QA1), 2 bài (QA4 rồi QB1).
THU_TU_KY_VONG = [QA2, QB2, QA1, QA4, QB1]


# ════════════════════════════════════════════════════════════════════════════
# Môi trường cô lập + helper dùng chung
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def moi_truong(monkeypatch, tmp_path):
    """Live-mode, mọi tầng dự phòng TẮT, ngưỡng tường minh (không phụ thuộc `.env`), không mạng, không ngủ thật."""
    for khoa, gia_tri in dict(
        fallback_min_trusted=3, fallback_min_evidence=60, fallback_keep_unverified=False,
        enable_consensus=False, enable_serpapi_scholar=False, enable_scite_verification=True,
        fallback_order="consensus,serpapi_scholar", use_mock_sources=False, consensus_api_key="",
        serpapi_api_key="", enable_openfda=False, consensus_max_calls_per_month=1000,
        consensus_max_calls_per_run=1000, serpapi_max_calls_per_run=1000,
    ).items():
        monkeypatch.setattr(settings, khoa, gia_tri)
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    (tmp_path / "data" / "raw").mkdir(parents=True, exist_ok=True)
    ngu_that: List[float] = []
    monkeypatch.setattr(time, "sleep", lambda s: ngu_that.append(float(s)))

    def _cam(*_a, **_k):
        raise AssertionError("test bậc thang KHÔNG được mở kết nối mạng")

    monkeypatch.setattr(socket.socket, "connect", _cam)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam)
    return SimpleNamespace(ngu_that=ngu_that)


@pytest.fixture()
def db_rieng(monkeypatch, tmp_path):
    """DB SQLite tạm RIÊNG cho từng test (theo mẫu tests/test_pipeline_workflow_20260905_...)."""
    import app.database as db_mod

    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'bac_thang.db'}")
    db_mod.init_db()
    yield db_mod
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


_DEM = {"n": 0}


def _dat_khu_vuc(monkeypatch, khu: Optional[Dict[str, List[str]]] = None) -> List[str]:
    """Đặt danh mục (nhóm -> truy vấn) THAY TẠI CHỖ vào CLINICAL_AREAS (mọi module dùng chung MỘT dict)."""
    khu = khu or {KHU_A: [QA1, QA2, QA3, QA4], KHU_B: [QB1, QB2]}
    for ten, ds in khu.items():
        monkeypatch.setitem(CLINICAL_AREAS, ten, list(ds))
    return list(khu.keys())


def _khu_cua(truy_van: str) -> str:
    return next(k for k, ds in {KHU_A: [QA1, QA2, QA3, QA4], KHU_B: [QB1, QB2]}.items() if truy_van in ds)


def _bai_tin_cay(truy_van: str, khu: str, nguon: str = "pubmed") -> RawRecord:
    """Bản ghi thô ĐÁNG TIN (systematic_review có tóm tắt, PMID + DOI riêng): điểm 85, tier C theo công cụ chấm thật."""
    _DEM["n"] += 1
    n = _DEM["n"]
    return RawRecord(
        source=nguon, title=f"Fake ladder study number {n} on {truy_van}", pmid=str(700000 + n),
        doi=f"10.5555/fake.ladder.{n}", study_type="systematic_review", publication_date="2025-03-01",
        journal_or_organization="The Lancet",
        abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).",
        clinical_area=khu, ingest_query=truy_van,
    )


def _log(nguon: str, khu: str, truy_van: str, trang_thai: str = "ok") -> dict:
    return dict(source=nguon, api_endpoint="https://fake.example.org/", query=f"[{khu}] {truy_van}", record_count=0,
                status=trang_thai, error_message=None, mode="mock" if trang_thai == "mock" else "live")


def _logs_lanh(khu_truy_van: Dict[str, List[str]]) -> List[dict]:
    return [_log(n, k, q) for k, ds in khu_truy_van.items() for q in ds for n in ("pubmed", "europepmc", "crossref")]


def _kich_ban(monkeypatch, so_tin_cay: Optional[Dict[str, int]] = None, khu: Optional[Dict[str, List[str]]] = None):
    """Dựng (areas, all_records, all_logs) cho danh mục thử nghiệm với số bài đáng tin cho trước."""
    khu = khu or {KHU_A: [QA1, QA2, QA3, QA4], KHU_B: [QB1, QB2]}
    areas = _dat_khu_vuc(monkeypatch, khu)
    dem = SO_TIN_CAY if so_tin_cay is None else so_tin_cay
    records = [_bai_tin_cay(q, k) for k, ds in khu.items() for q in ds for _ in range(dem.get(q, 0))]
    return areas, records, _logs_lanh(khu)


def _kho_rong(truy_van, *_a, **_k):
    return set()


class LoiGia(RuntimeError):
    """Lỗi có thuộc tính `loai` (đúng khuôn lỗi đã phân loại của các connector thật)."""

    def __init__(self, loai: str, thong_diep: Optional[str] = None) -> None:
        super().__init__(thong_diep or f"[gia] loi {loai}")
        self.loai = loai


class TangGia:
    """Tầng dự phòng giả: ghi lại từng lời gọi `search`, trả phát hiện / ném lỗi theo kịch bản."""

    def __init__(self, ten: str, *, hits: Optional[Dict[str, List[RawRecord]]] = None,
                 loi: Optional[Dict[Any, Any]] = None, dong_ho: Optional[Callable[[], float]] = None) -> None:
        self.name = ten
        self.endpoint = f"https://{ten}.example.org/v1/search"
        self.use_mock = False
        self.hits = hits or {}
        self.loi = loi or {}          # khoá: số thứ tự lần gọi (1-based) hoặc chuỗi truy vấn -> loai | Exception
        self.dong_ho = dong_ho
        self.calls: List[Dict[str, Any]] = []

    def search(self, query, clinical_area=None, max_results=20, since_date=None):
        self.calls.append(dict(query=query, area=clinical_area, max_results=max_results, since_date=since_date,
                               t=self.dong_ho() if self.dong_ho else None))
        loi = self.loi.get(len(self.calls), self.loi.get(query))
        if isinstance(loi, BaseException):
            raise loi
        if loi:
            raise LoiGia(loi)
        return [copy.copy(r) for r in self.hits.get(query, [])]

    @property
    def truy_van_da_goi(self) -> List[str]:
        return [c["query"] for c in self.calls]


def _hits(nguon: str, truy_van: str, so: int) -> List[RawRecord]:
    ra = []
    for _ in range(so):
        _DEM["n"] += 1
        n = _DEM["n"]
        ra.append(RawRecord(source=nguon, title=f"Fallback hit {n} for {truy_van}", authors="Alice Nguyen",
                            publication_date="2025", doi=f"10.5555/fake.hit.{n}", ingest_query=truy_van,
                            clinical_area=_khu_cua(truy_van) if truy_van in SO_TIN_CAY else None))
    return ra


def _ban_ghi_dang_tin(hit: RawRecord, raw_them: Optional[dict] = None) -> RawRecord:
    """Bản ghi 'của cơ quan đăng ký' như `xac_minh_ban_ghi` sẽ trả: đáng tin khi chấm (PMID+DOI, SR, tóm tắt).
    CỐ Ý để trống `ingest_query`/`clinical_area`: việc gắn vào truy vấn là phần của bậc thang."""
    _DEM["n"] += 1
    raw = {"phat_hien_boi": hit.source,
           "xac_minh": {"phuong_phap": "gia", "do_giong": 1.0, "doi": (hit.doi or "").lower()},
           "scite": {"da_kiem": True, "tally": {"supporting": 1, "contradicting": 0}, "nguon": "api.scite.ai",
                     "ngay": "2026-09-20"}}
    raw.update(raw_them or {})
    return RawRecord(source="pubmed", title=hit.title, pmid=str(800000 + _DEM["n"]), doi=(hit.doi or "").lower(),
                     study_type="systematic_review", publication_date="2025-03-01",
                     journal_or_organization="The Lancet",
                     abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).", raw=raw)


class XacMinhGia:
    """`xac_minh_fn` giả: kết quả theo DOI của phát hiện (mặc định xác minh được)."""

    def __init__(self, theo_doi: Optional[Dict[str, str]] = None, mac_dinh: str = "xac_minh_duoc",
                 raw_them: Optional[Dict[str, dict]] = None) -> None:
        self.theo_doi = theo_doi or {}
        self.mac_dinh = mac_dinh
        self.raw_them = raw_them or {}
        self.calls: List[RawRecord] = []

    def __call__(self, rec, **_kw):
        self.calls.append(rec)
        kq = self.theo_doi.get(rec.doi, self.mac_dinh)
        if kq == "xac_minh_duoc":
            return KetQuaXacMinh(_ban_ghi_dang_tin(rec, self.raw_them.get(rec.doi)), kq)
        return KetQuaXacMinh(None, kq)


def _chay(records, logs, areas, clients, *, xac=None, kho=None, ngu=None, since_date=None, max_results=10):
    return chay_du_phong_ingest(records, logs, areas, max_results, since_date, clients=clients,
                                khoa_kho_fn=kho or _kho_rong, xac_minh_fn=xac or XacMinhGia(),
                                ngu_fn=ngu or (lambda _s: None))


def _theo_truy_van(danh_sach: List[dict]) -> Dict[str, dict]:
    return {d["query"]: d for d in danh_sach}


def _luu(db_mod, *hang: EvidenceItem) -> None:
    with db_mod.session_scope() as s:
        s.add_all(list(hang))


def _hang_tin_cay(truy_van: str, so: int, khu: str = KHU_A) -> List[EvidenceItem]:
    ra = []
    for _ in range(so):
        _DEM["n"] += 1
        ra.append(EvidenceItem(
            source="pubmed", source_type="article", title=f"Stored ladder study {_DEM['n']}",
            pmid=str(900000 + _DEM["n"]), evidence_quality_score=85.0, reliability_tier="C",
            ingest_query=truy_van, is_primary_record=True, classification="actionable", is_mock=False,
            clinical_area=khu))
    return ra


# ════════════════════════════════════════════════════════════════════════════
# chon_truy_van_can_bo_sung: thứ tự, quyết định cho MỌI truy vấn, bốn trạng thái
# ════════════════════════════════════════════════════════════════════════════

def test_candidates_are_ordered_worst_first_then_by_area_and_query_order(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    ung_vien, _ = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    assert [c["query"] for c in ung_vien] == THU_TU_KY_VONG
    assert [c["so_tin_cay"] for c in ung_vien] == [0, 0, 1, 2, 2]
    assert {c["query"]: c["area"] for c in ung_vien} == {QA2: KHU_A, QB2: KHU_B, QA1: KHU_A, QA4: KHU_A, QB1: KHU_B}


def test_every_query_gets_a_decision_with_the_promised_fields(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    _, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    assert len(quyet_dinh) == 6
    theo = _theo_truy_van(quyet_dinh)
    assert set(theo) == set(SO_TIN_CAY)
    for q, d in theo.items():
        assert d["quyet_dinh"] in VOCAB_QUYET_DINH, d
        assert d["area"] == _khu_cua(q)
        assert d["so_tin_cay"] == SO_TIN_CAY[q] and d["nguong"] == 3
        assert isinstance(d["ly_do"], str) and d["ly_do"].strip()
    assert theo[QA3]["quyet_dinh"] == "du"
    assert all(theo[q]["quyet_dinh"] == "thieu" for q in (QA1, QA2, QA4, QB1, QB2))


def test_a_sufficient_query_is_never_a_candidate(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    ung_vien, _ = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    assert QA3 not in [c["query"] for c in ung_vien]


def test_incremental_window_zero_new_but_enough_stored_is_sufficient_not_a_candidate(monkeypatch):
    """CA CHÍNH: primary sources chỉ trả bài MỚI. QA2 có 0 bài mới nhưng kho đã có 3 bài đáng tin => ĐỦ."""
    areas, records, logs = _kich_ban(monkeypatch)
    kho = {QA2: {"pmid:9001", "pmid:9002", "doi:10.5555/stored.three"}}
    ung_vien, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas,
                                                     khoa_kho_fn=lambda q, *_a, **_k: kho.get(q, set()))
    assert _theo_truy_van(quyet_dinh)[QA2]["quyet_dinh"] == "du"
    assert QA2 not in [c["query"] for c in ung_vien]
    assert [c["query"] for c in ung_vien] == [QB2, QA1, QA4, QB1]


def test_default_stored_lookup_reads_reliable_rows_of_the_database(monkeypatch, db_rieng):
    """`khoa_kho_fn` mặc định phải tra DB: 3 bài đáng tin đã lưu cho QA2 => QA2 đủ dù lượt này 0 bài."""
    areas, records, logs = _kich_ban(monkeypatch)
    _luu(db_rieng, *_hang_tin_cay(QA2, 3))
    ung_vien, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas)
    assert _theo_truy_van(quyet_dinh)[QA2]["quyet_dinh"] == "du"
    assert QA2 not in [c["query"] for c in ung_vien]


def test_stored_rows_that_are_mock_or_from_fallback_tiers_do_not_make_a_query_sufficient(monkeypatch, db_rieng):
    areas, records, logs = _kich_ban(monkeypatch)
    ghi = _hang_tin_cay(QA2, 3)
    ghi[0].is_mock = True
    ghi[1].source = "consensus"
    ghi[2].source = "serpapi_scholar"
    _luu(db_rieng, *ghi)
    _, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas)
    assert _theo_truy_van(quyet_dinh)[QA2]["quyet_dinh"] == "thieu"


def test_core_outage_means_no_conclusion_not_insufficiency(monkeypatch):
    """Không có dòng log ok/degraded của pubmed/europepmc/crossref cho truy vấn => 'chưa kết luận' (KHÔNG leo thang)."""
    areas, records, logs = _kich_ban(monkeypatch)
    logs = [lg for lg in logs if not lg["query"].endswith(QA1)]                           # vắng dòng log (bị cắt sớm)
    logs = [dict(lg, status="error") if lg["query"].endswith(QA2) else lg for lg in logs]  # lỗi hoàn toàn
    ung_vien, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    theo = _theo_truy_van(quyet_dinh)
    assert theo[QA1]["quyet_dinh"] == "chua_ket_luan"
    assert theo[QA2]["quyet_dinh"] == "chua_ket_luan"
    assert "chưa kết luận được" in theo[QA1]["ly_do"] and "chưa kết luận được" in theo[QA2]["ly_do"]
    assert {QA1, QA2}.isdisjoint(c["query"] for c in ung_vien)
    assert [c["query"] for c in ung_vien] == [QB2, QA4, QB1]


def test_only_non_core_sources_healthy_is_still_no_conclusion(monkeypatch):
    areas, records, _ = _kich_ban(monkeypatch)
    logs = [_log("openalex", k, q) for k, ds in {KHU_A: [QA1, QA2, QA3, QA4], KHU_B: [QB1, QB2]}.items() for q in ds]
    ung_vien, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    assert ung_vien == []
    assert {d["quyet_dinh"] for d in quyet_dinh} <= {"du", "chua_ket_luan"}


@pytest.mark.parametrize("the", ["[ta]", "[pt]", "[cn]", "[tiab]", "[mh]", "[majr]", "[dp]"])
def test_pubmed_field_tag_queries_are_classified_and_never_candidates(monkeypatch, the):
    truy_van_the = f'"Lancet"{the} AND randomized'
    khu = {KHU_A: [QA1, truy_van_the]}
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA1: 0}, khu=khu)
    ung_vien, quyet_dinh = chon_truy_van_can_bo_sung(records, logs, areas, khoa_kho_fn=_kho_rong)
    theo = _theo_truy_van(quyet_dinh)
    assert theo[truy_van_the]["quyet_dinh"] == "bo_qua_cu_phap_pubmed"
    assert truy_van_the not in [c["query"] for c in ung_vien]
    assert theo[QA1]["quyet_dinh"] == "thieu", "truy vấn thường cạnh nó vẫn được đánh giá bình thường"


def test_pubmed_syntax_queries_are_never_sent_to_any_tier(monkeypatch):
    the_ta = '"Cochrane Database Syst Rev"[ta]'
    the_cn = 'NICE guidance[ti] OR "National Institute for Health and Care Excellence"[cn]'
    khu = {KHU_A: [QA1, the_ta, the_cn]}
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA1: 0}, khu=khu)
    t1, t2 = TangGia("consensus"), TangGia("serpapi_scholar")
    _, _, tom_tat = _chay(records, logs, areas, [t1, t2])
    for tang in (t1, t2):
        assert tang.truy_van_da_goi == [QA1]
    assert tom_tat["bo_qua_cu_phap_pubmed"] == 2
    ket_qua = _theo_truy_van(tom_tat["quyet_dinh"])
    assert ket_qua[the_ta]["ket_qua"] == "bo_qua_cu_phap_pubmed" and ket_qua[the_cn]["ket_qua"] == "bo_qua_cu_phap_pubmed"


# ════════════════════════════════════════════════════════════════════════════
# chay_du_phong_ingest: bậc thang
# ════════════════════════════════════════════════════════════════════════════

def _kich_ban_bac_thang(monkeypatch):
    """Tầng 1 sửa QA2, QA1; sửa dở QB2 (0 -> 1 bài); không sửa QA4, QB1. Tầng 2 sửa QB2, không sửa QA4, QB1."""
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus", hits={QA2: _hits("consensus", QA2, 3), QA1: _hits("consensus", QA1, 2),
                                    QB2: _hits("consensus", QB2, 1)})
    t2 = TangGia("serpapi_scholar", hits={QB2: _hits("serpapi_scholar", QB2, 2)})
    return areas, records, logs, t1, t2


def test_tier_one_fixing_a_query_means_tier_two_is_never_called_for_it(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    _chay(records, logs, areas, [t1, t2])
    assert t1.truy_van_da_goi == THU_TU_KY_VONG, "tầng 1 hỏi mọi truy vấn thiếu, tệ nhất trước"
    assert set(t2.truy_van_da_goi) == {QB2, QA4, QB1}
    assert QA2 not in t2.truy_van_da_goi and QA1 not in t2.truy_van_da_goi
    assert QA3 not in t1.truy_van_da_goi + t2.truy_van_da_goi, "truy vấn đã ĐỦ không bao giờ bị hỏi"


def test_a_partial_fix_by_tier_one_still_escalates_that_query_and_both_tiers_additions_are_merged(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    them, _, tom_tat = _chay(records, logs, areas, [t1, t2])
    assert QB2 in t2.truy_van_da_goi                       # 0 + 1 bài xác minh vẫn < 3
    theo = _theo_truy_van(tom_tat["quyet_dinh"])
    assert theo[QB2]["ket_qua"] == "du_sau_serpapi_scholar"
    assert theo[QB2]["tang_da_thu"] == ["consensus", "serpapi_scholar"]
    nguon_phat_hien = sorted((r.raw or {}).get("phat_hien_boi") for r in them if r.ingest_query == QB2)
    assert nguon_phat_hien == ["consensus", "serpapi_scholar", "serpapi_scholar"]


def test_decisions_and_counters_after_the_ladder(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    them, extra_logs, tom_tat = _chay(records, logs, areas, [t1, t2])
    theo = _theo_truy_van(tom_tat["quyet_dinh"])
    assert theo[QA3]["ket_qua"] == "du" and theo[QA3]["tang_da_thu"] == []
    assert theo[QA2]["ket_qua"] == "du_sau_consensus" and theo[QA2]["tang_da_thu"] == ["consensus"]
    assert theo[QA1]["ket_qua"] == "du_sau_consensus"
    assert theo[QA4]["ket_qua"] == "van_thieu" and theo[QA4]["tang_da_thu"] == ["consensus", "serpapi_scholar"]
    assert theo[QB1]["ket_qua"] == "van_thieu"
    assert tom_tat["active"] is True
    assert (tom_tat["so_truy_van"], tom_tat["du"], tom_tat["thieu"]) == (6, 1, 5)
    assert tom_tat["chua_ket_luan"] == 0 and tom_tat["bo_qua_cu_phap_pubmed"] == 0
    assert tom_tat["du_sau_du_phong"] == 3 and tom_tat["van_thieu"] == 2
    assert tom_tat["thieu"] == tom_tat["du_sau_du_phong"] + tom_tat["van_thieu"]
    c, s = tom_tat["tang"]["consensus"], tom_tat["tang"]["serpapi_scholar"]
    assert (c["da_goi"], c["tim_thay"], c["xac_minh_duoc"]) == (5, 6, 6)
    assert (s["da_goi"], s["tim_thay"], s["xac_minh_duoc"]) == (3, 2, 2)
    assert c["loi_chot"] is None and s["loi_chot"] is None
    assert len(them) == 8 and len(extra_logs) == 8


def test_verified_additions_are_registry_records_attached_to_their_query_and_area(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    them, _, _ = _chay(records, logs, areas, [t1, t2])
    assert them
    for r in them:
        assert r.source not in {"consensus", "serpapi_scholar"}, "bản thêm phải là bản ghi của cơ quan đăng ký"
        assert (r.raw or {}).get("phat_hien_boi") in {"consensus", "serpapi_scholar"}
        assert r.ingest_query in SO_TIN_CAY, "phải gắn vào truy vấn đã tìm ra nó (ingest_query)"
        assert r.clinical_area == _khu_cua(r.ingest_query)


def test_the_ladder_does_not_mutate_its_inputs(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    truoc = ([r.to_dict() for r in records], copy.deepcopy(logs))
    _chay(records, logs, areas, [t1, t2])
    assert ([r.to_dict() for r in records], logs) == truoc, "người gọi (ingest_all) mới là bên nối bản thêm vào"


def test_queries_are_sent_with_area_since_date_and_max_results(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus")
    _chay(records, logs, areas, [t1], since_date="2026-01-01", max_results=7)
    assert t1.calls
    for c in t1.calls:
        assert c["area"] == _khu_cua(c["query"])
        assert c["since_date"] == "2026-01-01"
        assert 1 <= c["max_results"] <= 7


def test_the_same_query_string_in_two_areas_is_sent_only_once_to_a_paid_tier(monkeypatch):
    khu = {KHU_A: [QA1, QA2], KHU_B: [QA2]}
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA1: 3, QA2: 0}, khu=khu)
    t1 = TangGia("consensus")
    _chay(records, logs, areas, [t1])
    assert t1.truy_van_da_goi.count(QA2) == 1


def test_an_outage_query_is_never_sent_to_any_tier(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    logs = [lg for lg in logs if not lg["query"].endswith(QA4)]
    t1 = TangGia("consensus")
    _, _, tom_tat = _chay(records, logs, areas, [t1])
    assert QA4 not in t1.truy_van_da_goi
    assert _theo_truy_van(tom_tat["quyet_dinh"])[QA4]["ket_qua"] == "chua_ket_luan"
    assert tom_tat["chua_ket_luan"] == 1


def test_stored_evidence_prevents_calls_in_the_ladder_too(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    kho = {QA2: {"pmid:1", "pmid:2", "pmid:3"}, QB2: {"pmid:4", "pmid:5", "pmid:6"}}
    t1 = TangGia("consensus")
    _chay(records, logs, areas, [t1], kho=lambda q, *_a, **_k: kho.get(q, set()))
    assert t1.truy_van_da_goi == [QA1, QA4, QB1]


# ── Tầng tắt / cả hai tắt / mock ────────────────────────────────────────────────────────

def test_only_tier_two_runs_when_tier_one_is_absent(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    t2 = TangGia("serpapi_scholar", hits={QA2: _hits("serpapi_scholar", QA2, 3)})
    _, _, tom_tat = _chay(records, logs, areas, [t2])
    assert t2.truy_van_da_goi == THU_TU_KY_VONG
    assert "consensus" not in tom_tat["tang"] or tom_tat["tang"]["consensus"]["da_goi"] == 0


def test_no_tiers_means_zero_calls_and_unchanged_outputs(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    truoc = ([r.to_dict() for r in records], copy.deepcopy(logs))
    them, extra_logs, tom_tat = chay_du_phong_ingest(records, logs, areas, 10, None, clients=[])
    assert them == [] and extra_logs == []
    assert tom_tat["active"] is False
    assert KHOA_SUMMARY <= set(tom_tat)
    assert ([r.to_dict() for r in records], logs) == truoc


def test_both_flags_off_makes_zero_client_calls_through_the_real_registry(monkeypatch):
    """Đường THẬT: `clients=None` => get_fallback_sources() => [] khi cả hai cờ tắt; mọi `search` thật đều bị cấm."""
    areas, records, logs = _kich_ban(monkeypatch)

    def cam(self, *a, **k):
        raise AssertionError("cờ tắt mà vẫn gọi tầng dự phòng")

    monkeypatch.setattr(sources_pkg.ConsensusClient, "search", cam)
    monkeypatch.setattr(sources_pkg.SerpApiScholarClient, "search", cam)
    them, extra_logs, tom_tat = chay_du_phong_ingest(records, logs, areas, 10, None, khoa_kho_fn=_kho_rong)
    assert them == [] and extra_logs == [] and tom_tat["active"] is False


def test_real_registry_with_only_serpapi_enabled_calls_only_serpapi(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    goi: Dict[str, List[str]] = {"consensus": [], "serpapi_scholar": []}

    def gia(ten):
        def search(self, query, clinical_area=None, max_results=20, since_date=None):
            goi[ten].append(query)
            return []
        return search

    monkeypatch.setattr(sources_pkg.ConsensusClient, "search", gia("consensus"))
    monkeypatch.setattr(sources_pkg.SerpApiScholarClient, "search", gia("serpapi_scholar"))
    chay_du_phong_ingest(records, logs, areas, 10, None, khoa_kho_fn=_kho_rong, xac_minh_fn=XacMinhGia(),
                         ngu_fn=lambda _s: None)
    assert goi["consensus"] == []
    assert goi["serpapi_scholar"] == THU_TU_KY_VONG


def test_real_registry_with_both_enabled_asks_consensus_first(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    su_kien: List[str] = []

    def gia(ten):
        def search(self, query, clinical_area=None, max_results=20, since_date=None):
            su_kien.append(ten)
            return []
        return search

    monkeypatch.setattr(sources_pkg.ConsensusClient, "search", gia("consensus"))
    monkeypatch.setattr(sources_pkg.SerpApiScholarClient, "search", gia("serpapi_scholar"))
    chay_du_phong_ingest(records, logs, areas, 10, None, khoa_kho_fn=_kho_rong, xac_minh_fn=XacMinhGia(),
                         ngu_fn=lambda _s: None)
    assert su_kien[0] == "consensus"
    assert su_kien.count("consensus") == 5 and su_kien.count("serpapi_scholar") == 5
    assert su_kien.index("serpapi_scholar") > max(i for i, t in enumerate(su_kien) if t == "consensus"), \
        "tầng 1 chạy XONG mọi truy vấn rồi mới tới tầng 2"


def test_mock_mode_makes_zero_calls_and_unchanged_outputs(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    monkeypatch.setattr(settings, "use_mock_sources", True)
    t1, t2 = TangGia("consensus"), TangGia("serpapi_scholar")
    them, extra_logs, tom_tat = _chay(records, logs, areas, [t1, t2])
    assert t1.calls == [] and t2.calls == []
    assert them == [] and extra_logs == []
    assert tom_tat["active"] is False


def test_a_mock_status_log_row_in_the_run_disables_the_ladder(monkeypatch):
    """PubMed trả MOCK ngay cả ở live khi thiếu NCBI_EMAIL: lượt đó sắp FAIL, không được đốt hạn mức trả phí."""
    areas, records, logs = _kich_ban(monkeypatch)
    logs = logs + [_log("pubmed", KHU_A, QA2, trang_thai="mock")]
    t1 = TangGia("consensus")
    them, extra_logs, tom_tat = _chay(records, logs, areas, [t1])
    assert t1.calls == [] and them == [] and extra_logs == [] and tom_tat["active"] is False


def test_a_tier_flagged_as_mock_is_never_called(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus")
    t1.use_mock = True
    them, extra_logs, _ = _chay(records, logs, areas, [t1])
    assert t1.calls == [] and them == [] and extra_logs == []


# ── Lỗi CHỐT dừng tầng đó; lỗi không-chốt thì không ──────────────────────────────────────────

@pytest.mark.parametrize("ten,loai", [("consensus", x) for x in LOI_CHOT_CHUNG]
                         + [("serpapi_scholar", x) for x in LOI_CHOT_CHUNG + ["thieu_key", "cam_truy_cap"]])
def test_a_chot_error_stops_that_tier_and_reports_the_rest_as_skipped(monkeypatch, ten, loai):
    areas, records, logs = _kich_ban(monkeypatch)
    hong, lanh = TangGia(ten, loi={2: loai}), TangGia("serpapi_scholar" if ten == "consensus" else "consensus")
    tang = [hong, lanh] if ten == "consensus" else [lanh, hong]
    _, extra_logs, tom_tat = _chay(records, logs, areas, tang)
    if ten == "consensus":
        assert len(hong.calls) == 2, f"lỗi chốt {loai}: tầng phải dừng NGAY sau lần gọi lỗi"
        assert lanh.truy_van_da_goi == THU_TU_KY_VONG, "tầng kia vẫn chạy tiếp cho mọi truy vấn còn thiếu"
    else:
        assert len(lanh.calls) == 5
        assert len(hong.calls) == 2
    ts = tom_tat["tang"][ten]
    assert ts["loi_chot"] and loai in str(ts["loi_chot"])
    # Phần còn lại phải được BÁO là bị bỏ qua: lỗi kiểu "hết hạn mức" đếm ở bo_qua_ngan_sach, các lỗi chốt khác
    # (khoá sai, thanh toán quá hạn, tính năng không cho phép...) đếm ở bo_qua_do_loi_chot — tổng vẫn phải đủ 3..5.
    bo_qua = ts["bo_qua_ngan_sach"] + ts["bo_qua_do_loi_chot"]
    assert 3 <= bo_qua <= 5, "phần còn lại phải được BÁO là bị bỏ qua"
    khoa_dung = "bo_qua_ngan_sach" if loai in ("het_ngan_sach", "het_quota") else "bo_qua_do_loi_chot"
    assert ts[khoa_dung] == bo_qua, f"lỗi chốt {loai} phải đếm vào {khoa_dung}"
    assert tom_tat["tang"][lanh.name]["loi_chot"] is None
    hang_hong = [lg for lg in extra_logs if lg["source"] == ten]
    assert len(hang_hong) == 2, "chỉ các lời gọi THẬT mới có dòng log"
    assert hang_hong[-1]["status"] == "error" and hang_hong[-1]["error_message"]
    assert all(d["ket_qua"] == "van_thieu" for d in tom_tat["quyet_dinh"] if d["ket_qua"] != "du")


@pytest.mark.parametrize("ten", ["consensus", "serpapi_scholar"])
@pytest.mark.parametrize("loai", LOI_KHONG_CHOT)
def test_a_non_chot_error_does_not_stop_the_tier(monkeypatch, ten, loai):
    areas, records, logs = _kich_ban(monkeypatch)
    tang = TangGia(ten, loi={2: loai})
    _, extra_logs, tom_tat = _chay(records, logs, areas, [tang])
    assert len(tang.calls) == 5
    assert tom_tat["tang"][ten]["loi_chot"] is None
    assert tom_tat["tang"][ten]["bo_qua_ngan_sach"] == 0
    assert [lg["status"] for lg in extra_logs].count("error") == 1


def test_an_unclassified_exception_never_escapes_and_the_other_tier_still_runs(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus", loi={1: ValueError("boom không có thuộc tính loai")})
    t2 = TangGia("serpapi_scholar")
    _, extra_logs, tom_tat = _chay(records, logs, areas, [t1, t2])
    assert len(t2.calls) >= 1, "một tầng hỏng không được làm sập bậc thang"
    assert isinstance(tom_tat, dict) and KHOA_SUMMARY <= set(tom_tat)
    assert any(lg["source"] == "consensus" and lg["status"] == "error" for lg in extra_logs)


def test_the_extra_source_log_rows_have_exactly_the_seven_source_log_keys(monkeypatch):
    """`SourceLog(**lg)` không có try/except: khoá thừa => TypeError SAU khi đã tốn xong mọi lời gọi mạng."""
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    t2.loi = {1: "khac"}
    _, extra_logs, _ = _chay(records, logs, areas, [t1, t2])
    assert extra_logs
    for lg in extra_logs:
        assert set(lg) == KHOA_LOG, set(lg) ^ KHOA_LOG
        assert lg["status"] in {"ok", "degraded", "error"}, "KHÔNG BAO GIỜ ghi dòng mock trong live"
        assert lg["mode"] == "live"
        assert lg["source"] in {"consensus", "serpapi_scholar"}
        assert lg["query"].startswith("[") and "] " in lg["query"]
    goi = {(lg["source"], lg["query"]) for lg in extra_logs}
    assert ("consensus", f"[{KHU_A}] {QA2}") in goi
    with pytest.raises(Exception) if False else _khong_loi():
        SourceLog(**extra_logs[0])


class _khong_loi:
    def __enter__(self):
        return self

    def __exit__(self, *_a):
        return False


# ── Bản ghi không xác minh / rút bài / bộ đếm ─────────────────────────────────────────────────

def _kich_ban_xac_minh(monkeypatch):
    """Một tầng, 6 phát hiện cho QA2 (0 bài đáng tin): kết quả xác minh khác nhau theo DOI."""
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA2: 0}, khu={KHU_A: [QA2]})
    hits = _hits("consensus", QA2, 6)
    doi = [h.doi for h in hits]
    xac = XacMinhGia(theo_doi={doi[2]: "khong_khop", doi[3]: "mo_ho", doi[4]: "bi_rut_bai", doi[5]: "loi_xac_minh"})
    return areas, records, logs, TangGia("consensus", hits={QA2: hits}), xac, hits


def test_unverified_hits_are_dropped_and_counted_never_silently(monkeypatch):
    areas, records, logs, t1, xac, hits = _kich_ban_xac_minh(monkeypatch)
    them, _, tom_tat = _chay(records, logs, areas, [t1], xac=xac)
    c = tom_tat["tang"]["consensus"]
    assert c["tim_thay"] == 6 and c["xac_minh_duoc"] == 2
    assert c["bi_loai_chua_xac_minh"] == 2 and c["bi_loai_rut_bai"] == 1 and c["loi_xac_minh"] == 1
    assert len(them) == 2
    assert len(xac.calls) == 6, "MỌI phát hiện đều phải qua bước xác minh"
    assert not any(r.source == "consensus" for r in them)


def test_keep_unverified_keeps_only_flagged_hits_and_never_a_retracted_one(monkeypatch):
    monkeypatch.setattr(settings, "fallback_keep_unverified", True)
    areas, records, logs, t1, xac, hits = _kich_ban_xac_minh(monkeypatch)
    them, _, tom_tat = _chay(records, logs, areas, [t1], xac=xac)
    chua_xm = [r for r in them if (r.raw or {}).get("chua_xac_minh") is True]
    assert len(chua_xm) >= 2, "khong_khop và mo_ho được giữ kèm cờ chua_xac_minh"
    assert hits[4].doi not in {r.doi for r in them}, "bài đã BỊ RÚT không bao giờ được giữ"
    assert tom_tat["tang"]["consensus"]["bi_loai_rut_bai"] == 1
    for r in them:
        assert (r.raw or {}).get("chua_xac_minh") is True or r.source not in {"consensus", "serpapi_scholar"}


def test_kept_unverified_hits_never_make_a_query_sufficient(monkeypatch):
    """Tầng dự phòng không tự bảo chứng: 6 phát hiện CHƯA xác minh được giữ cũng không được coi là đủ chứng cứ."""
    monkeypatch.setattr(settings, "fallback_keep_unverified", True)
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA2: 0}, khu={KHU_A: [QA2]})
    t1 = TangGia("consensus", hits={QA2: _hits("consensus", QA2, 6)})
    t2 = TangGia("serpapi_scholar")
    _, _, tom_tat = _chay(records, logs, areas, [t1, t2], xac=XacMinhGia(mac_dinh="khong_khop"))
    assert t2.truy_van_da_goi == [QA2], "phát hiện chưa xác minh không làm truy vấn 'đủ' để khỏi lên tầng 2"
    assert _theo_truy_van(tom_tat["quyet_dinh"])[QA2]["ket_qua"] == "van_thieu"


def test_scite_counters_in_the_summary(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA2: 0}, khu={KHU_A: [QA2]})
    hits = _hits("consensus", QA2, 4)
    raw_them = {
        hits[0].doi: {"scite": {"da_kiem": True, "tally": {"supporting": 9, "contradicting": 0}, "nguon": "api.scite.ai",
                                "ngay": "2026-09-20"}},
        hits[1].doi: {"scite": {"da_kiem": True, "tally": {"supporting": 0, "contradicting": 7}, "nguon": "api.scite.ai",
                                "ngay": "2026-09-20"}, "co": ["nhieu_trich_dan_phan_bac"]},
        hits[2].doi: {"scite": {"da_kiem": False, "ly_do": "timeout"}},
        hits[3].doi: {"scite": {"da_kiem": True, "tally": {"supporting": 3, "contradicting": 0}, "nguon": "api.scite.ai",
                                "ngay": "2026-09-20"}, "co": ["co_thong_bao_bien_tap"]},
    }
    _, _, tom_tat = _chay(records, logs, areas, [TangGia("consensus", hits={QA2: hits})],
                          xac=XacMinhGia(raw_them=raw_them))
    scite = tom_tat["scite"]
    assert KHOA_SCITE <= set(scite)
    assert scite["da_kiem"] == 3 and scite["khong_kiem_duoc"] == 1
    assert scite["co_thong_bao_bien_tap"] == 1 and scite["nhieu_trich_dan_phan_bac"] == 1


# ── Khoảng cách >= 1,1 giây giữa hai lời gọi Consensus ──────────────────────────────────────

class DongHo:
    """Đồng hồ giả: CHỈ `ngu_fn` mới làm nó chạy (không có thời gian thật nào trôi)."""

    def __init__(self) -> None:
        self.t = 5000.0
        self.ngu: List[float] = []

    def __call__(self) -> float:
        return self.t

    def ngu_fn(self, giay: float) -> None:
        self.ngu.append(float(giay))
        self.t += float(giay)


def _dong_bang_thoi_gian(monkeypatch, dong_ho: DongHo) -> None:
    monkeypatch.setattr(time, "monotonic", dong_ho)
    monkeypatch.setattr(time, "time", dong_ho)
    monkeypatch.setattr(time, "perf_counter", dong_ho)


def test_consensus_requests_are_spaced_at_least_1_1_seconds_via_the_injected_sleep(monkeypatch, moi_truong):
    dh = DongHo()
    _dong_bang_thoi_gian(monkeypatch, dh)
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus", dong_ho=dh)
    _chay(records, logs, areas, [t1], ngu=dh.ngu_fn)
    thoi_diem = [c["t"] for c in t1.calls]
    assert len(thoi_diem) == 5
    for truoc, sau in zip(thoi_diem, thoi_diem[1:]):
        assert sau - truoc >= 1.1 - 1e-6, f"hai request Consensus cách nhau {sau - truoc:.3f}s < 1,1s"
    assert dh.ngu, "phải ngủ qua `ngu_fn` tiêm vào"
    assert moi_truong.ngu_that == [], "không được dùng time.sleep thật khi đã tiêm ngu_fn"


def test_consensus_spacing_also_holds_between_two_separate_on_demand_calls(monkeypatch):
    """Diễn giải chặt hợp đồng: giới hạn 1 request/giây của gói Free tính theo TIẾN TRÌNH, không theo từng lượt gọi."""
    dh = DongHo()
    _dong_bang_thoi_gian(monkeypatch, dh)
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus", dong_ho=dh)
    for q in (QA2, QB2):
        bo_sung_neu_thieu(q, _khu_cua(q), [], max_results=5, clients=[t1], khoa_kho_fn=_kho_rong,
                          xac_minh_fn=XacMinhGia(), ngu_fn=dh.ngu_fn)
    assert len(t1.calls) == 2
    assert t1.calls[1]["t"] - t1.calls[0]["t"] >= 1.1 - 1e-6


# ── Truy vấn PII không bao giờ được gửi (đường thật qua ConsensusClient) ─────────────────────

_TRUY_VAN_PII = ["mã bệnh nhân AB123456 HbA1c", "SĐT 0901234567 tăng huyết áp", "ngày sinh 15/07/1980 đái tháo đường"]


class _PhanHoiRong:
    status_code = 200
    headers: Dict[str, str] = {}
    text = json.dumps({"results": [], "page": 0, "is_end": True, "page_size": 20, "next_page": None})

    def __init__(self, url: str) -> None:
        self.url = url

    def raise_for_status(self) -> None:
        return None

    def json(self) -> Any:
        return json.loads(self.text)


def test_pii_queries_are_never_sent_and_do_not_stop_the_real_consensus_tier(monkeypatch, tmp_path):
    from app.utils import http as http_mod

    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    monkeypatch.setattr(settings, "http_cache_ttl", 0)
    monkeypatch.setattr(http_mod, "_CACHE_DIR", tmp_path / "http_cache")
    (tmp_path / "http_cache").mkdir(parents=True, exist_ok=True)
    goi: List[dict] = []

    def gia(self, method, url, params=None, timeout=None, **kw):
        goi.append({"url": url, "params": dict(params or {})})
        return _PhanHoiRong(url)

    monkeypatch.setattr(requests.Session, "request", gia)
    consensus_mod = importlib.reload(importlib.import_module("app.sources.consensus_api"))
    client = consensus_mod.ConsensusClient()
    client.use_mock = False
    client.http.min_interval = 0
    khu = {KHU_A: [QA1, *_TRUY_VAN_PII, QA2]}
    areas, records, logs = _kich_ban(monkeypatch, so_tin_cay={QA1: 0, QA2: 0}, khu=khu)
    _, _, tom_tat = _chay(records, logs, areas, [client])
    duoc_gui = json.dumps(goi, ensure_ascii=False)
    for pii in ("AB123456", "0901234567", "15/07/1980"):
        assert pii not in duoc_gui, "truy vấn có PII/PHI tuyệt đối không được rời máy"
    assert len(goi) == 2, "hai truy vấn chủ đề thường vẫn được gửi (PII không chốt cả tầng)"
    assert tom_tat["tang"]["consensus"]["loi_chot"] is None


# ════════════════════════════════════════════════════════════════════════════
# bo_sung_neu_thieu: biến thể MỘT truy vấn theo yêu cầu
# ════════════════════════════════════════════════════════════════════════════

def _bo_sung(truy_van, records, clients, **kw):
    kw.setdefault("khoa_kho_fn", _kho_rong)
    kw.setdefault("xac_minh_fn", XacMinhGia())
    kw.setdefault("ngu_fn", lambda _s: None)
    return bo_sung_neu_thieu(truy_van, KHU_A, records, max_results=10, clients=clients, **kw)


def test_on_demand_variant_asks_the_tier_for_an_insufficient_query(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus", hits={QA2: _hits("consensus", QA2, 3)})
    them, tom_tat = _bo_sung(QA2, [], [t1], since_date="2026-01-01")
    assert t1.truy_van_da_goi == [QA2]
    assert t1.calls[0]["area"] == KHU_A and t1.calls[0]["since_date"] == "2026-01-01"
    assert len(them) == 3 and all(r.source not in {"consensus", "serpapi_scholar"} for r in them)
    assert all(r.ingest_query == QA2 for r in them)
    assert tom_tat["active"] is True and tom_tat["so_truy_van"] == 1
    assert KHOA_SUMMARY <= set(tom_tat) and all(KHOA_TANG <= set(t) for t in tom_tat["tang"].values())
    assert tom_tat["quyet_dinh"][0]["ket_qua"] == "du_sau_consensus"


def test_on_demand_variant_makes_no_call_when_reliable_evidence_is_already_enough(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus")
    records = [_bai_tin_cay(QA2, KHU_A) for _ in range(3)]
    them, tom_tat = _bo_sung(QA2, records, [t1])
    assert t1.calls == [] and them == []
    assert tom_tat["du"] == 1 and tom_tat["thieu"] == 0


def test_on_demand_variant_counts_stored_evidence(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus")
    them, _ = _bo_sung(QA2, [], [t1], khoa_kho_fn=lambda q, *_a, **_k: {"pmid:1", "pmid:2", "pmid:3"})
    assert t1.calls == [] and them == []


def test_on_demand_variant_escalates_to_tier_two_only_when_tier_one_did_not_fix_it(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus", hits={QA2: _hits("consensus", QA2, 1)})
    t2 = TangGia("serpapi_scholar", hits={QA2: _hits("serpapi_scholar", QA2, 2)})
    them, tom_tat = _bo_sung(QA2, [], [t1, t2])
    assert t1.truy_van_da_goi == [QA2] and t2.truy_van_da_goi == [QA2]
    assert len(them) == 3 and tom_tat["quyet_dinh"][0]["ket_qua"] == "du_sau_serpapi_scholar"
    t3 = TangGia("consensus", hits={QA2: _hits("consensus", QA2, 3)})
    t4 = TangGia("serpapi_scholar")
    _bo_sung(QA2, [], [t3, t4])
    assert t4.calls == [], "tầng 1 đã sửa xong thì tầng 2 không được gọi"


def test_on_demand_variant_with_no_tiers_or_in_mock_mode_is_inert(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    them, tom_tat = _bo_sung(QA2, [], [])
    assert them == [] and tom_tat["active"] is False
    monkeypatch.setattr(settings, "use_mock_sources", True)
    t1 = TangGia("consensus")
    them, tom_tat = _bo_sung(QA2, [], [t1])
    assert t1.calls == [] and them == [] and tom_tat["active"] is False


def test_on_demand_variant_never_sends_a_pubmed_syntax_query(monkeypatch):
    truy_van_the = '"Cochrane Database Syst Rev"[ta]'
    monkeypatch.setitem(CLINICAL_AREAS, KHU_A, [truy_van_the])
    t1 = TangGia("consensus")
    them, tom_tat = _bo_sung(truy_van_the, [], [t1])
    assert t1.calls == [] and them == []
    assert tom_tat["bo_qua_cu_phap_pubmed"] == 1


def test_on_demand_variant_stops_a_tier_on_a_chot_error(monkeypatch):
    _dat_khu_vuc(monkeypatch)
    t1 = TangGia("consensus", loi={1: "het_quota"})
    t2 = TangGia("serpapi_scholar", hits={QA2: _hits("serpapi_scholar", QA2, 3)})
    them, tom_tat = _bo_sung(QA2, [], [t1, t2])
    assert tom_tat["tang"]["consensus"]["loi_chot"] and "het_quota" in str(tom_tat["tang"]["consensus"]["loi_chot"])
    assert len(them) == 3, "tầng 1 chốt lỗi thì tầng 2 vẫn được hỏi"


# ════════════════════════════════════════════════════════════════════════════
# Tóm tắt cho diagnostics: đủ khoá, thuần JSON
# ════════════════════════════════════════════════════════════════════════════

def test_summary_has_every_promised_key_and_is_plain_json(monkeypatch):
    areas, records, logs, t1, t2 = _kich_ban_bac_thang(monkeypatch)
    _, _, tom_tat = _chay(records, logs, areas, [t1, t2])
    assert KHOA_SUMMARY <= set(tom_tat)
    assert isinstance(tom_tat["active"], bool)
    for khoa in ("so_truy_van", "du", "thieu", "chua_ket_luan", "bo_qua_cu_phap_pubmed", "du_sau_du_phong", "van_thieu"):
        assert isinstance(tom_tat[khoa], int) and not isinstance(tom_tat[khoa], bool), khoa
    assert set(tom_tat["tang"]) == {"consensus", "serpapi_scholar"}
    for ten, ts in tom_tat["tang"].items():
        assert KHOA_TANG <= set(ts), ten
        for khoa in KHOA_TANG - {"loi_chot"}:
            assert isinstance(ts[khoa], int), (ten, khoa)
        assert ts["loi_chot"] is None or isinstance(ts["loi_chot"], str)
    assert KHOA_SCITE <= set(tom_tat["scite"])
    assert tom_tat["so_truy_van"] == len(tom_tat["quyet_dinh"])
    assert (tom_tat["du"] + tom_tat["thieu"] + tom_tat["chua_ket_luan"] + tom_tat["bo_qua_cu_phap_pubmed"]
            == tom_tat["so_truy_van"])
    for d in tom_tat["quyet_dinh"]:
        assert isinstance(d["tang_da_thu"], list)
        assert d["ket_qua"] in VOCAB_QUYET_DINH | {"du_sau_consensus", "du_sau_serpapi_scholar", "van_thieu"}
    json.dumps(tom_tat)


def test_summary_never_contains_a_secret(monkeypatch):
    areas, records, logs = _kich_ban(monkeypatch)
    t1 = TangGia("consensus", loi={1: "key_sai"})
    _, extra_logs, tom_tat = _chay(records, logs, areas, [t1])
    assert CLE_SENTINEL not in json.dumps([tom_tat, extra_logs], ensure_ascii=False, default=str)


# ════════════════════════════════════════════════════════════════════════════
# Tích hợp ingest_all
# ════════════════════════════════════════════════════════════════════════════

KHU_I = "Khu tích hợp"
Q_DU, Q_IT, Q_KHONG = ("empagliflozin chronic kidney disease progression", "spironolactone resistant hypertension",
                       "ivabradine stable angina outcomes")


class NguonChinhGia:
    """Nguồn chính giả (quét song song trong luồng riêng, đúng như ingest_all)."""

    def __init__(self, ten: str, su_kien: list, theo_truy_van: Dict[str, int], loi: bool = False) -> None:
        self.name, self.endpoint, self.use_mock = ten, f"https://{ten}.example.org/", False
        self._su_kien, self._theo_truy_van, self._loi = su_kien, theo_truy_van, loi

    def search(self, query, clinical_area=None, max_results=20, since_date=None):
        self._su_kien.append(("chinh", self.name, query))
        if self._loi:
            raise RuntimeError("nguồn chính giả bị sập")
        return [_bai_tin_cay(query, KHU_I, self.name) for _ in range(self._theo_truy_van.get(query, 0))]


class MoiTruongIngest:
    def __init__(self, monkeypatch, db_mod, so_tin_cay: Dict[str, int], *, chinh_loi: bool = False) -> None:
        self.db = db_mod
        self.su_kien: List[tuple] = []
        self.goi_du_phong: Dict[str, List[str]] = {"consensus": [], "serpapi_scholar": []}
        monkeypatch.setitem(CLINICAL_AREAS, KHU_I, [Q_DU, Q_IT, Q_KHONG])
        # mỗi truy vấn chỉ do pubmed trả (europepmc/crossref trả rỗng nhưng "ok" => nguồn lõi khoẻ)
        nguon = [NguonChinhGia("pubmed", self.su_kien, so_tin_cay, loi=chinh_loi),
                 NguonChinhGia("europepmc", self.su_kien, {}, loi=chinh_loi),
                 NguonChinhGia("crossref", self.su_kien, {}, loi=chinh_loi)]
        monkeypatch.setattr(ing, "get_enabled_sources", lambda: list(nguon))
        monkeypatch.setattr("app.sources.rss_feed.get_feed_clients", lambda *a, **k: [])
        monkeypatch.setattr(settings, "enable_openfda", False)
        monkeypatch.setattr(settings, "use_mock_sources", False)
        self.chup: Dict[str, Any] = {}
        goc = ing.summarize_source_health

        def boc(*a, **k):
            kq = goc(*a, **k)
            self.chup["ket_qua"] = kq
            return kq

        monkeypatch.setattr(ing, "summarize_source_health", boc)

    def bat_du_phong(self, monkeypatch, *, hits: Optional[Dict[str, Dict[str, int]]] = None,
                     loi: Optional[Dict[str, Dict[int, str]]] = None, ket_qua_xm: str = "xac_minh_duoc") -> None:
        monkeypatch.setattr(settings, "enable_consensus", True)
        monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
        hits, loi = hits or {}, loi or {}
        for ten, lop in (("consensus", sources_pkg.ConsensusClient), ("serpapi_scholar", sources_pkg.SerpApiScholarClient)):
            def dung(ten=ten):
                so_lan = {"n": 0}

                def search(self, query, clinical_area=None, max_results=20, since_date=None):
                    self.goi.append(query) if hasattr(self, "goi") else None
                    self_ = self
                    del self_
                    so_lan["n"] += 1
                    self_moi.goi_du_phong[ten].append(query)
                    self_moi.su_kien.append(("du_phong", ten, query))
                    if loi.get(ten, {}).get(so_lan["n"]):
                        raise LoiGia(loi[ten][so_lan["n"]])
                    return [RawRecord(source=ten, title=f"Fallback {ten} {query} {i}", doi=f"10.5555/fake.in.{ten}.{abs(hash(query)) % 9999}.{i}",
                                      ingest_query=query, clinical_area=KHU_I)
                            for i in range(hits.get(ten, {}).get(query, 0))]
                return search
            self_moi = self
            monkeypatch.setattr(lop, "search", dung())
        xac = XacMinhGia(mac_dinh=ket_qua_xm)
        monkeypatch.setattr(fv, "xac_minh_ban_ghi", xac)
        monkeypatch.setattr(fl, "xac_minh_ban_ghi", xac, raising=False)
        monkeypatch.setattr(ing, "xac_minh_ban_ghi", xac, raising=False)
        self.xac = xac


@pytest.fixture()
def ingest_env(monkeypatch, db_rieng):
    return lambda so_tin_cay=None, **kw: MoiTruongIngest(monkeypatch, db_rieng,
                                                         {Q_DU: 3, Q_IT: 1} if so_tin_cay is None else so_tin_cay, **kw)


def _dem_source_log(db_mod, nguon: Optional[str] = None) -> int:
    with db_mod.session_scope() as s:
        q = s.query(SourceLog)
        if nguon:
            q = q.filter(SourceLog.source == nguon)
        return q.count()


def test_flags_off_ingest_all_is_unchanged_no_extra_calls_rows_or_keys(monkeypatch, ingest_env, db_rieng):
    env = ingest_env()

    def cam(self, *a, **k):
        raise AssertionError("cờ tắt mà ingest_all vẫn gọi tầng dự phòng")

    monkeypatch.setattr(sources_pkg.ConsensusClient, "search", cam)
    monkeypatch.setattr(sources_pkg.SerpApiScholarClient, "search", cam)
    chan_doan: dict = {}
    ban_ghi = ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert len(ban_ghi) == 4 and {r.source for r in ban_ghi} == {"pubmed"}
    assert _dem_source_log(db_rieng) == 9, "đúng 3 nguồn x 3 truy vấn: KHÔNG thêm dòng Source Log nào"
    assert _dem_source_log(db_rieng, "consensus") == 0 and _dem_source_log(db_rieng, "serpapi_scholar") == 0
    assert set(chan_doan) - {"fallback"} == set(env.chup["ket_qua"])
    if "fallback" in chan_doan:
        assert chan_doan["fallback"]["active"] is False
    assert chan_doan["status"] == "PASS"


def test_mock_mode_ingest_all_never_touches_the_ladder(monkeypatch, ingest_env, db_rieng):
    env = ingest_env()
    env.bat_du_phong(monkeypatch, hits={"consensus": {Q_KHONG: 3}})
    monkeypatch.setattr(settings, "use_mock_sources", True)
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert env.goi_du_phong == {"consensus": [], "serpapi_scholar": []}
    assert _dem_source_log(db_rieng, "consensus") == 0
    assert set(chan_doan) - {"fallback"} == set(env.chup["ket_qua"])


def test_ladder_runs_after_all_primary_sweeps_and_only_for_insufficient_queries(monkeypatch, ingest_env, db_rieng):
    env = ingest_env()
    env.bat_du_phong(monkeypatch, hits={"consensus": {Q_KHONG: 3, Q_IT: 2}})
    chan_doan: dict = {}
    ban_ghi = ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    chinh = [i for i, e in enumerate(env.su_kien) if e[0] == "chinh"]
    du_phong = [i for i, e in enumerate(env.su_kien) if e[0] == "du_phong"]
    assert chinh and du_phong
    assert max(chinh) < min(du_phong), "bậc thang phải chạy SAU khi MỌI nguồn chính đã quét xong"
    assert env.goi_du_phong["consensus"] == [Q_KHONG, Q_IT], "chỉ truy vấn thiếu, tệ nhất trước; Q_DU đã đủ nên bị bỏ"
    tom_tat = chan_doan["fallback"]
    assert KHOA_SUMMARY <= set(tom_tat)
    assert tom_tat["tang"]["consensus"]["da_goi"] == 2 and tom_tat["tang"]["consensus"]["xac_minh_duoc"] == 5
    assert tom_tat["du_sau_du_phong"] == 2 and tom_tat["van_thieu"] == 0
    duoc_them = [r for r in ban_ghi if (r.raw or {}).get("phat_hien_boi") == "consensus"]
    assert len(duoc_them) == 5 and all(r.source not in {"consensus", "serpapi_scholar"} for r in duoc_them)
    assert len(ban_ghi) == 4 + 5
    assert _dem_source_log(db_rieng, "consensus") == 2, "đúng một dòng Source Log cho mỗi lời gọi THẬT"
    json.dumps(chan_doan["fallback"])


def test_primary_health_is_computed_from_primary_logs_only(monkeypatch, ingest_env, db_rieng):
    env = ingest_env()
    env.bat_du_phong(monkeypatch, loi={"consensus": {1: "key_sai"}})
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert chan_doan["status"] == "PASS", "tầng dự phòng lỗi không được biến PASS thành FAIL/PARTIAL"
    assert chan_doan["hard_fail_reasons"] == []
    assert set(chan_doan["sources"]) == {"pubmed", "europepmc", "crossref"}
    assert "consensus" not in json.dumps(chan_doan["sources"])
    tom_tat = chan_doan["fallback"]
    assert "key_sai" in str(tom_tat["tang"]["consensus"]["loi_chot"])
    assert tom_tat["van_thieu"] >= 1, "lỗi dự phòng phải được BÁO (còn thiếu), không được im lặng coi là ổn"
    assert _dem_source_log(db_rieng, "consensus") == 1


def test_a_failing_ladder_never_escapes_ingest_all_and_is_summarised(monkeypatch, ingest_env):
    env = ingest_env()
    env.bat_du_phong(monkeypatch)

    def no(*_a, **_k):
        raise RuntimeError("boom trong bậc thang")

    monkeypatch.setattr(fl, "chay_du_phong_ingest", no)
    monkeypatch.setattr(ing, "chay_du_phong_ingest", no, raising=False)
    chan_doan: dict = {}
    ban_ghi = ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert len(ban_ghi) == 4, "kết quả nguồn chính vẫn nguyên vẹn"
    assert chan_doan["status"] == "PASS"
    assert isinstance(chan_doan.get("fallback"), dict), "lỗi của bậc thang phải được TÓM TẮT, không được im lặng"
    json.dumps(chan_doan["fallback"])


def test_a_fallback_success_never_masks_a_primary_failure(monkeypatch, ingest_env):
    """Bẫy (F) của bản đồ mã: bản ghi dự phòng làm total_records > 0 che NO_RECORDS_FROM_ANY_SOURCE (FAIL -> PASS)."""
    env = ingest_env({})       # mọi nguồn chính 'ok' nhưng 0 bản ghi
    env.bat_du_phong(monkeypatch, hits={"consensus": {Q_DU: 3, Q_IT: 3, Q_KHONG: 3}})
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert chan_doan["status"] == "FAIL"
    assert "NO_RECORDS_FROM_ANY_SOURCE" in chan_doan["hard_fail_reasons"]


def test_primary_source_outage_is_not_hidden_and_does_not_trigger_paid_calls(monkeypatch, ingest_env):
    env = ingest_env(chinh_loi=True)
    env.bat_du_phong(monkeypatch, hits={"consensus": {Q_KHONG: 3}})
    chan_doan: dict = {}
    ing.ingest_all(max_results_per_query=5, areas=[KHU_I], diagnostics=chan_doan)
    assert chan_doan["status"] == "FAIL"
    assert env.goi_du_phong["consensus"] == [], "sập nguồn lõi = chưa kết luận được: KHÔNG leo thang, không đốt hạn mức"


# ════════════════════════════════════════════════════════════════════════════
# Đường nghiên cứu (dossier / manager) đi qua bo_sung_neu_thieu SAU vòng nguồn thường
# ════════════════════════════════════════════════════════════════════════════

TRUY_VAN_NC = "sepsis bundle outcomes in adults"
KHU_NC = "Nhiễm khuẩn"


class NguonThuongGia:
    def __init__(self, su_kien: list) -> None:
        self.name, self.endpoint, self.use_mock = "pubmed", "https://fake.example.org/", False
        self._su_kien = su_kien

    def search(self, query, clinical_area=None, max_results=20, since_date=None):
        self._su_kien.append("thuong")
        return [RawRecord(source="pubmed", title="Normal source paper A on sepsis bundles", pmid="710001",
                          doi="10.5555/fake.normal.a", study_type="systematic_review",
                          publication_date="2025-03-01", journal_or_organization="The Lancet",
                          abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).",
                          clinical_area=clinical_area, ingest_query=query)]


def _vá_bo_sung(monkeypatch, ham) -> None:
    """Thay `bo_sung_neu_thieu` ở MỌI nơi có thể được tham chiếu (import ở đầu module hay import muộn)."""
    from app.research import dossier as dossier_mod
    from app.research import manager as manager_mod

    monkeypatch.setattr(fl, "bo_sung_neu_thieu", ham)
    monkeypatch.setattr(dossier_mod, "bo_sung_neu_thieu", ham, raising=False)
    monkeypatch.setattr(manager_mod, "bo_sung_neu_thieu", ham, raising=False)


def _bo_sung_gia(su_kien: list, goi: list):
    def ham(truy_van, khu, records, **kw):
        su_kien.append("du_phong")
        goi.append(dict(query=truy_van, area=khu, records=list(records), kw=kw))
        xm = RawRecord(source="pubmed", title="Registry verified paper B on sepsis bundles", pmid="710002",
                       doi="10.5555/fake.verified.b", study_type="systematic_review", publication_date="2025-03-01",
                       journal_or_organization="The Lancet",
                       abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).",
                       raw={"phat_hien_boi": "consensus"})
        return [xm], {"active": True, "so_truy_van": 1, "du": 0, "thieu": 1, "chua_ket_luan": 0,
                      "bo_qua_cu_phap_pubmed": 0, "du_sau_du_phong": 1, "van_thieu": 0, "tang": {}, "scite": {},
                      "quyet_dinh": []}
    return ham


def test_dossier_asks_the_ladder_after_its_normal_source_loop(monkeypatch, db_rieng):
    from app.research import dossier as dossier_mod

    su_kien: List[str] = []
    goi: List[dict] = []
    monkeypatch.setattr(dossier_mod, "get_enabled_sources", lambda: [NguonThuongGia(su_kien)])
    _vá_bo_sung(monkeypatch, _bo_sung_gia(su_kien, goi))
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    ket_qua = dossier_mod.find_background_literature(TRUY_VAN_NC, KHU_NC, max_results=12)
    assert su_kien == ["thuong", "du_phong"], "bậc thang chạy SAU vòng nguồn thường, đúng một lần"
    assert goi[0]["query"] == TRUY_VAN_NC and goi[0]["area"] == KHU_NC
    assert "Normal source paper A on sepsis bundles" in [r.title for r in goi[0]["records"]]
    tieu_de = [x["title"] for x in ket_qua]
    assert "Normal source paper A on sepsis bundles" in tieu_de
    assert "Registry verified paper B on sepsis bundles" in tieu_de, "bản đã xác minh phải nằm trong kết quả"


def test_manager_asks_the_ladder_after_its_normal_source_loop(monkeypatch, db_rieng):
    from app.research import manager as manager_mod

    su_kien: List[str] = []
    goi: List[dict] = []
    monkeypatch.setattr(manager_mod, "get_enabled_sources", lambda: [NguonThuongGia(su_kien)])
    _vá_bo_sung(monkeypatch, _bo_sung_gia(su_kien, goi))
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    ket_qua = manager_mod.suggest_background_literature(TRUY_VAN_NC, KHU_NC, max_results=10)
    assert su_kien == ["thuong", "du_phong"]
    assert goi[0]["query"] == TRUY_VAN_NC and goi[0]["area"] == KHU_NC
    tieu_de = [x["title"] for x in ket_qua]
    assert "Normal source paper A on sepsis bundles" in tieu_de
    assert "Registry verified paper B on sepsis bundles" in tieu_de


def test_manager_database_hit_returns_before_any_source_or_ladder(monkeypatch, db_rieng):
    from app.research import manager as manager_mod

    _luu(db_rieng, EvidenceItem(source="pubmed", source_type="article", title="Stored tier A paper on sepsis",
                                reliability_tier="A", is_primary_record=True, clinical_area=KHU_NC,
                                evidence_quality_score=90.0, classification="actionable"))
    su_kien: List[str] = []
    goi: List[dict] = []
    monkeypatch.setattr(manager_mod, "get_enabled_sources", lambda: [NguonThuongGia(su_kien)])
    _vá_bo_sung(monkeypatch, _bo_sung_gia(su_kien, goi))
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    ket_qua = manager_mod.suggest_background_literature(TRUY_VAN_NC, KHU_NC, max_results=10)
    assert [x["title"] for x in ket_qua] == ["Stored tier A paper on sepsis"]
    assert su_kien == [] and goi == []


@pytest.mark.parametrize("duong", ["dossier", "manager"])
def test_research_paths_make_no_fallback_call_when_both_flags_are_off(monkeypatch, db_rieng, duong):
    def cam(self, *a, **k):
        raise AssertionError("cờ tắt mà đường nghiên cứu vẫn gọi tầng dự phòng")

    monkeypatch.setattr(sources_pkg.ConsensusClient, "search", cam)
    monkeypatch.setattr(sources_pkg.SerpApiScholarClient, "search", cam)
    su_kien: List[str] = []
    if duong == "dossier":
        from app.research import dossier as mod

        monkeypatch.setattr(mod, "get_enabled_sources", lambda: [NguonThuongGia(su_kien)])
        ket_qua = mod.find_background_literature(TRUY_VAN_NC, KHU_NC, max_results=12)
    else:
        from app.research import manager as mod

        monkeypatch.setattr(mod, "get_enabled_sources", lambda: [NguonThuongGia(su_kien)])
        ket_qua = mod.suggest_background_literature(TRUY_VAN_NC, KHU_NC, max_results=10)
    assert su_kien == ["thuong"]
    assert [x["title"] for x in ket_qua] == ["Normal source paper A on sepsis bundles"]


# ════════════════════════════════════════════════════════════════════════════
# Đăng ký nguồn: get_enabled_sources() vs get_fallback_sources()
# ════════════════════════════════════════════════════════════════════════════

_CO_ENABLE_CU = ("enable_pubmed", "enable_europe_pmc", "enable_crossref", "enable_clinicaltrials", "enable_openalex",
                 "enable_semantic_scholar", "enable_scopus", "enable_core", "enable_epistemonikos")


def test_get_enabled_sources_never_returns_a_fallback_tier(monkeypatch):
    for co in _CO_ENABLE_CU:
        monkeypatch.setattr(settings, co, True if co in {"enable_pubmed", "enable_europe_pmc"} else False)
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    ten = [c.name for c in sources_pkg.get_enabled_sources()]
    assert "consensus" not in ten and "serpapi_scholar" not in ten
    assert not any(isinstance(c, (sources_pkg.ConsensusClient, sources_pkg.SerpApiScholarClient))
                   for c in sources_pkg.get_enabled_sources())


def test_get_fallback_sources_is_empty_when_both_tiers_are_off():
    assert sources_pkg.get_fallback_sources() == []


def test_get_fallback_sources_returns_only_enabled_tiers(monkeypatch):
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    ds = sources_pkg.get_fallback_sources()
    assert [c.name for c in ds] == ["consensus"] and isinstance(ds[0], sources_pkg.ConsensusClient)
    monkeypatch.setattr(settings, "enable_consensus", False)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    ds = sources_pkg.get_fallback_sources()
    assert [c.name for c in ds] == ["serpapi_scholar"] and isinstance(ds[0], sources_pkg.SerpApiScholarClient)


def test_get_fallback_sources_follows_fallback_order(monkeypatch):
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", CLE_SENTINEL)
    assert [c.name for c in sources_pkg.get_fallback_sources()] == ["consensus", "serpapi_scholar"]
    monkeypatch.setattr(settings, "fallback_order", "serpapi_scholar,consensus")
    assert [c.name for c in sources_pkg.get_fallback_sources()] == ["serpapi_scholar", "consensus"]


def test_fallback_order_only_orders_it_does_not_enable(monkeypatch):
    monkeypatch.setattr(settings, "fallback_order", "serpapi_scholar,consensus")
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    assert [c.name for c in sources_pkg.get_fallback_sources()] == ["consensus"]


@pytest.mark.parametrize("gia_tri", ["consensus,bogus", "bogus", "consensus,serpapi_scholar,dynamed"])
@pytest.mark.parametrize("bat", [True, False], ids=["tang-bat", "tang-tat"])
def test_unknown_names_in_fallback_order_are_a_loud_value_error(monkeypatch, gia_tri, bat):
    monkeypatch.setattr(settings, "enable_consensus", bat)
    monkeypatch.setattr(settings, "consensus_api_key", CLE_SENTINEL)
    monkeypatch.setattr(settings, "fallback_order", gia_tri)
    with pytest.raises(ValueError):
        sources_pkg.get_fallback_sources()


def test_get_fallback_sources_builds_clients_without_network_or_key_errors(monkeypatch):
    """Dựng client không được nổ dù thiếu key (kiểm key nằm ở search()): get_fallback_sources() đứng NGOÀI mọi try."""
    monkeypatch.setattr(settings, "enable_consensus", True)
    monkeypatch.setattr(settings, "consensus_api_key", "")
    monkeypatch.setattr(settings, "enable_serpapi_scholar", True)
    monkeypatch.setattr(settings, "serpapi_api_key", "")
    assert [c.name for c in sources_pkg.get_fallback_sources()] == ["consensus", "serpapi_scholar"]


def test_both_fallback_tiers_are_selectable_by_test_live():
    from app.main import _build_source_map

    smap = _build_source_map()
    assert smap["consensus"] is sources_pkg.ConsensusClient
    assert smap["serpapi_scholar"] is sources_pkg.SerpApiScholarClient


# ════════════════════════════════════════════════════════════════════════════
# Cấu hình của bậc thang (tên và mặc định theo hợp đồng)
# ════════════════════════════════════════════════════════════════════════════

_BIEN_MOI_TRUONG = ("FALLBACK_ORDER", "FALLBACK_MIN_TRUSTED", "FALLBACK_MIN_EVIDENCE", "ENABLE_SCITE_VERIFICATION",
                    "FALLBACK_KEEP_UNVERIFIED")


def test_fallback_settings_defaults_when_env_absent(monkeypatch):
    for ten in _BIEN_MOI_TRUONG:
        monkeypatch.delenv(ten, raising=False)
    s = Settings()
    assert s.fallback_order == "consensus,serpapi_scholar"
    assert s.fallback_min_trusted == 3
    assert s.fallback_min_evidence == 60
    assert s.enable_scite_verification is True
    assert s.fallback_keep_unverified is False


def test_fallback_settings_read_from_env(monkeypatch):
    monkeypatch.setenv("FALLBACK_ORDER", "serpapi_scholar,consensus")
    monkeypatch.setenv("FALLBACK_MIN_TRUSTED", "5")
    monkeypatch.setenv("FALLBACK_MIN_EVIDENCE", "70")
    monkeypatch.setenv("ENABLE_SCITE_VERIFICATION", "false")
    monkeypatch.setenv("FALLBACK_KEEP_UNVERIFIED", "true")
    s = Settings()
    assert s.fallback_order == "serpapi_scholar,consensus"
    assert s.fallback_min_trusted == 5
    assert s.fallback_min_evidence == 70
    assert s.enable_scite_verification is False
    assert s.fallback_keep_unverified is True
