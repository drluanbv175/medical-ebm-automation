"""Kiểm cổng "đủ chứng cứ đáng tin" (`app/services/evidence_sufficiency.py`) — thêm 20/09/2026.

Bộ test này do một tác giả ĐỘC LẬP viết từ HỢP ĐỒNG (CONTRACT) và BẢN ĐỒ MÃ (CODE MAP) của giai
đoạn nghiên cứu, KHÔNG đọc mã cài đặt, để bắt lệch giữa "điều đã hứa" và "điều đã làm".

Cổng này quyết định khi nào hệ được phép GỌI nguồn dự phòng có trả phí / giới hạn hạn mức
(Consensus, SerpApi Google Scholar). Vì vậy các quy tắc được canh chặt theo hướng AN TOÀN:

  * chỉ bằng chứng ĐÁNG TIN mới được đếm: không mock, không phải chính nguồn dự phòng (tầng
    dự phòng không được tự bảo chứng cho mình), có PMID hoặc DOI, tier khác D, điểm chất lượng
    đủ ngưỡng — tất cả tính trên bản ghi đã normalize + chấm điểm bằng đúng công cụ chấm điểm hiện có;
  * đếm theo KHOÁ ĐỊNH DANH khác nhau (cùng một bài từ PubMed lẫn Europe PMC chỉ tính một);
  * bản ghi ĐÃ LƯU trong cơ sở dữ liệu cũng được tính — ở chế độ tăng dần (incremental) nguồn chính
    chỉ trả bài MỚI kể từ lần chạy trước, nên "lượt này ít bài" KHÔNG được hiểu là "thiếu chứng cứ";
  * "im lặng khác an toàn": khi các nguồn khám phá lõi (pubmed / europepmc / crossref) đều không có
    dòng log ok/degraded cho truy vấn đó trong lượt này thì KHÔNG KẾT LUẬN được (`ket_luan_duoc=False`)
    và tuyệt đối không leo thang — một đợt sập nguồn không phải bằng chứng của việc thiếu chứng cứ.

Mọi test OFFLINE: không mạng (socket bị chặn), DB SQLite tạm riêng cho từng test cần DB, ngưỡng
đặt tường minh (không phụ thuộc `.env` của máy chạy test). Bản ghi thô đều là DỮ LIỆU GIẢ RÕ RÀNG
(DOI tiền tố 10.5555, PMID số nhỏ) — không phải bài báo thật.
"""
from __future__ import annotations

import copy
import dataclasses
import socket
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import app.services.evidence_sufficiency as es  # noqa: E402
from app.config import settings  # noqa: E402
from app.models import EvidenceItem  # noqa: E402
from app.services.evidence_sufficiency import (  # noqa: E402
    KetQuaDuChungCu,
    danh_gia_du_chung_cu,
    khoa_dinh_danh,
    khoa_tin_cay_trong_kho,
    la_tin_cay,
)
from app.services.normalization import normalize  # noqa: E402
from app.services.pipeline import score_item  # noqa: E402
from app.sources.base import RawRecord  # noqa: E402

TRUY_VAN = "sepsis early recognition"
KHU_VUC = "Cấp cứu ban đầu"
LOG_LOI_TRUY_VAN = f"[{KHU_VUC}] {TRUY_VAN}"


# ════════════════════════════════════════════════════════════════════════════
# Fixture + helper dùng chung
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture(autouse=True)
def _cach_ly(monkeypatch):
    """Cô lập khỏi `.env` của máy chạy test và CHẶN mạng: cổng này thuần logic, không được gọi mạng."""
    monkeypatch.setattr(settings, "fallback_min_trusted", 3)
    monkeypatch.setattr(settings, "fallback_min_evidence", 60)

    def _cam_mang(*_a, **_k):
        raise AssertionError("test cổng đủ-chứng-cứ KHÔNG được mở kết nối mạng")

    monkeypatch.setattr(socket.socket, "connect", _cam_mang)
    monkeypatch.setattr(socket.socket, "connect_ex", _cam_mang)
    yield


@pytest.fixture()
def db_rieng(monkeypatch, tmp_path):
    """DB SQLite tạm RIÊNG cho từng test (không dùng chung DB của conftest) — theo mẫu
    tests/test_pipeline_workflow_20260905_stale_fields_survive_duplicate_transition.py."""
    import app.database as db_mod

    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'du_chung_cu.db'}")
    db_mod.init_db()
    yield db_mod
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


_DEM = {"n": 0}


def _raw(source: str = "pubmed", *, pmid: Optional[str] = None, doi: Optional[str] = None,
         study_type: Optional[str] = "systematic_review", title: Optional[str] = None,
         query: str = TRUY_VAN, area: str = KHU_VUC, mock: bool = False) -> RawRecord:
    """Một bản ghi thô giả. Mặc định là systematic_review có tóm tắt: eq=85, tier C (đo bằng công cụ chấm điểm thật)."""
    _DEM["n"] += 1
    return RawRecord(
        source=source,
        title=title or f"Fake fallback sufficiency study number {_DEM['n']} on sepsis bundles",
        pmid=pmid, doi=doi, study_type=study_type,
        publication_date="2025-03-01", journal_or_organization="The Lancet",
        abstract="Background: fake. Results: hazard ratio 0.80 (95% CI 0.70-0.90).",
        clinical_area=area, ingest_query=query,
        raw={"_mock": True} if mock else {},
    )


def _dinh_danh_dang_tin(n: int, source: str = "pubmed") -> RawRecord:
    """Bản ghi đáng tin có PMID và DOI riêng theo số thứ tự n (n khác nhau => bài khác nhau)."""
    return _raw(source, pmid=str(1000 + n), doi=f"10.5555/fake.suf.{n}")


def _item(rec: RawRecord) -> Dict[str, Any]:
    """normalize + score_item đúng như pipeline — dùng để kiểm điều kiện đầu vào của từng test."""
    return score_item(normalize(rec))


def _log(nguon: str, trang_thai: str = "ok", *, truy_van: str = TRUY_VAN, khu_vuc: str = KHU_VUC,
         so_ban_ghi: int = 0) -> dict:
    """Một dòng SourceLog đúng khuôn của ingestion._fetch (query = '[khu vực] truy vấn')."""
    return dict(source=nguon, api_endpoint="https://fake.example.org/", query=f"[{khu_vuc}] {truy_van}",
                record_count=so_ban_ghi, status=trang_thai, error_message=None,
                mode="mock" if trang_thai == "mock" else "live")


def _logs_lanh() -> List[dict]:
    return [_log("pubmed"), _log("europepmc"), _log("crossref")]


def _danh_gia(records: List[RawRecord], **kw: Any) -> KetQuaDuChungCu:
    """Gọi cổng với log lành mạnh và kho rỗng, trừ khi test đặt khác."""
    kw.setdefault("logs", _logs_lanh())
    kw.setdefault("khoa_trong_kho", set())
    return danh_gia_du_chung_cu(records, TRUY_VAN, **kw)


def _hang(query: str = TRUY_VAN, **ghi_de: Any) -> EvidenceItem:
    """Một hàng EvidenceItem 'đáng tin' mặc định (bản chính, không mock, eq=85, tier C)."""
    _DEM["n"] += 1
    gia_tri: Dict[str, Any] = dict(
        source="pubmed", source_type="article", title=f"Stored fallback study {_DEM['n']}",
        pmid=None, doi=None, evidence_quality_score=85.0, reliability_tier="C",
        ingest_query=query, is_primary_record=True, classification="actionable",
        is_mock=False, clinical_area=KHU_VUC,
    )
    gia_tri.update(ghi_de)
    return EvidenceItem(**gia_tri)


def _luu(db_mod, *hang: EvidenceItem) -> None:
    with db_mod.session_scope() as s:
        s.add_all(list(hang))


# ════════════════════════════════════════════════════════════════════════════
# Điều kiện đầu vào: xác nhận công cụ chấm điểm thật cho ra đúng những gì test giả định
# ════════════════════════════════════════════════════════════════════════════

def test_premise_scoring_engine_matches_what_these_tests_assume():
    """Nếu ai đổi luật chấm điểm, các test bên dưới sẽ hỏng vì LÝ DO KHÁC — chốt giả định ở đây."""
    sr = _item(_raw(pmid="1", doi="10.5555/a"))
    assert sr["evidence_quality_score"] >= 60 and sr["reliability_tier"] != "D"
    preprint = _item(_raw(pmid="2", doi="10.5555/b", study_type="preprint"))
    assert preprint["reliability_tier"] == "D" and preprint["evidence_quality_score"] < 60
    ca_le = _item(_raw(pmid="3", doi="10.5555/c", study_type="case_report"))
    assert ca_le["reliability_tier"] != "D" and ca_le["evidence_quality_score"] < 60


# ════════════════════════════════════════════════════════════════════════════
# (1) khoa_dinh_danh — khoá định danh
# ════════════════════════════════════════════════════════════════════════════

def test_key_prefers_pmid_form():
    assert khoa_dinh_danh({"pmid": "12345", "doi": None, "title": "Some title"}) == "pmid:12345"


def test_key_from_doi_is_lowercased():
    assert khoa_dinh_danh({"pmid": None, "doi": "10.5555/ABC.Def", "title": "Some title"}) == "doi:10.5555/abc.def"


def test_key_for_same_paper_from_two_sources_is_identical():
    pubmed = normalize(_raw("pubmed", pmid="777", doi="10.5555/same.paper"))
    europepmc = normalize(_raw("europepmc", pmid="777", doi="10.5555/SAME.PAPER"))
    assert khoa_dinh_danh(pubmed) == khoa_dinh_danh(europepmc)


def test_key_falls_back_to_normalized_title_when_no_identifier():
    khoa = khoa_dinh_danh({"pmid": None, "doi": None, "title": "Sepsis Bundles, Revisited!"})
    assert isinstance(khoa, str) and khoa.startswith("title:")
    # khác hoa/thường, dấu câu, khoảng trắng thì cùng khoá; tiêu đề khác thì khác khoá
    khac_dang = khoa_dinh_danh({"pmid": None, "doi": None, "title": "  sepsis   bundles - revisited "})
    assert khoa == khac_dang
    assert khoa != khoa_dinh_danh({"pmid": None, "doi": None, "title": "Sepsis bundles, revisited again"})


def test_key_is_none_when_nothing_identifies_the_item():
    assert khoa_dinh_danh({"pmid": None, "doi": None, "title": ""}) is None
    assert khoa_dinh_danh({"pmid": None, "doi": None, "title": None}) is None
    assert khoa_dinh_danh({}) is None


@pytest.mark.parametrize("pmid_rong", ["", "   ", None])
def test_blank_pmid_is_not_an_identifier(pmid_rong):
    khoa = khoa_dinh_danh({"pmid": pmid_rong, "doi": "10.5555/x", "title": "T"})
    assert khoa == "doi:10.5555/x"


def test_key_accepts_a_real_normalized_item():
    khoa = khoa_dinh_danh(normalize(_raw(pmid="4242", doi="10.5555/z")))
    assert isinstance(khoa, str) and khoa.split(":", 1)[0] in {"pmid", "doi"}


# ════════════════════════════════════════════════════════════════════════════
# (2) la_tin_cay — một bản ghi đã normalize + chấm điểm có đáng tin không
# ════════════════════════════════════════════════════════════════════════════

def test_reliable_baseline_pubmed_with_pmid_and_doi():
    assert la_tin_cay(_item(_raw("pubmed", pmid="1", doi="10.5555/a"))) is True


@pytest.mark.parametrize("nguon", ["pubmed", "europepmc", "crossref", "openalex", "semantic_scholar", "scopus", "core"])
def test_reliable_for_every_source_that_is_not_a_fallback_tier(nguon):
    assert la_tin_cay(_item(_raw(nguon, pmid="11", doi="10.5555/b"))) is True


def test_reliable_with_only_a_pmid():
    assert la_tin_cay(_item(_raw("pubmed", pmid="21", doi=None))) is True


def test_reliable_with_only_a_doi():
    assert la_tin_cay(_item(_raw("crossref", pmid=None, doi="10.5555/c"))) is True


def test_no_pmid_and_no_doi_is_never_reliable_however_strong_the_score():
    item = _item(_raw("pubmed", pmid=None, doi=None))
    assert item["evidence_quality_score"] >= 60
    assert la_tin_cay(item) is False


@pytest.mark.parametrize("nguon", ["consensus", "serpapi_scholar"])
def test_fallback_tiers_never_vouch_for_themselves(nguon):
    item = _item(_raw(nguon, pmid="31", doi="10.5555/d"))
    assert item["evidence_quality_score"] >= 60 and item["reliability_tier"] != "D"
    assert la_tin_cay(item) is False


def test_mock_records_are_never_reliable():
    item = _item(_raw("pubmed", pmid="41", doi="10.5555/e", mock=True))
    assert item["is_mock"] is True
    assert la_tin_cay(item) is False


def test_tier_d_is_never_reliable_even_with_a_high_score():
    item = _item(_raw("pubmed", pmid="51", doi="10.5555/f"))
    item["reliability_tier"] = "D"
    item["evidence_quality_score"] = 95.0
    assert la_tin_cay(item) is False


@pytest.mark.parametrize("tier", ["A", "B", "C"])
def test_tiers_a_b_c_are_all_acceptable(tier):
    item = _item(_raw("pubmed", pmid="61", doi="10.5555/g"))
    item["reliability_tier"] = tier
    assert la_tin_cay(item) is True


def test_evidence_score_threshold_is_inclusive_at_60_and_exclusive_below():
    item = _item(_raw("pubmed", pmid="71", doi="10.5555/h"))
    item["evidence_quality_score"] = 60.0
    assert la_tin_cay(item) is True
    item["evidence_quality_score"] = 59.99
    assert la_tin_cay(item) is False


def test_unscored_item_is_not_reliable_and_does_not_crash():
    item = normalize(_raw("pubmed", pmid="81", doi="10.5555/i"))   # CHƯA score_item
    assert la_tin_cay(item) is False
    item["evidence_quality_score"] = None
    item["reliability_tier"] = None
    assert la_tin_cay(item) is False


def test_min_evidence_argument_overrides_the_setting():
    item = _item(_raw("pubmed", pmid="91", doi="10.5555/j"))     # eq = 85
    assert la_tin_cay(item, min_evidence=90) is False
    assert la_tin_cay(item, min_evidence=80) is True


def test_min_evidence_default_comes_from_settings(monkeypatch):
    item = _item(_raw("pubmed", pmid="92", doi="10.5555/k"))     # eq = 85
    monkeypatch.setattr(settings, "fallback_min_evidence", 90)
    assert la_tin_cay(item) is False
    monkeypatch.setattr(settings, "fallback_min_evidence", 85)
    assert la_tin_cay(item) is True


def test_low_score_alone_disqualifies_a_tier_c_item():
    item = _item(_raw("pubmed", pmid="93", doi="10.5555/l", study_type="case_report"))
    assert item["reliability_tier"] != "D" and item["evidence_quality_score"] < 60
    assert la_tin_cay(item) is False
    assert la_tin_cay(item, min_evidence=0) is True      # đối chứng: chỉ ngưỡng điểm mới là lý do loại


def test_tier_d_alone_disqualifies_even_when_the_score_threshold_is_zero():
    item = _item(_raw("pubmed", pmid="94", doi="10.5555/m", study_type="preprint"))
    assert item["reliability_tier"] == "D"
    assert la_tin_cay(item, min_evidence=0) is False


# ════════════════════════════════════════════════════════════════════════════
# (3) danh_gia_du_chung_cu — đếm khoá khác nhau, đáng tin, đủ / thiếu
# ════════════════════════════════════════════════════════════════════════════

def test_result_is_a_frozen_dataclass_with_the_promised_fields():
    kq = _danh_gia([])
    assert dataclasses.is_dataclass(kq)
    ten = {f.name for f in dataclasses.fields(KetQuaDuChungCu)}
    assert ten == {"du", "ket_luan_duoc", "so_tin_cay", "nguong", "tu_luot_nay", "tu_kho", "ly_do"}
    with pytest.raises(dataclasses.FrozenInstanceError):
        kq.du = True  # type: ignore[misc]
    assert isinstance(kq.du, bool) and isinstance(kq.ket_luan_duoc, bool)
    assert isinstance(kq.so_tin_cay, int) and isinstance(kq.nguong, int)
    assert isinstance(kq.ly_do, str) and kq.ly_do.strip()


def test_pubmed_and_europepmc_copies_of_one_paper_count_once():
    records = [_raw("pubmed", pmid="500", doi="10.5555/one.paper"),
               _raw("europepmc", pmid="500", doi="10.5555/one.paper")]
    kq = _danh_gia(records)
    assert kq.so_tin_cay == 1 and kq.tu_luot_nay == 1
    assert kq.du is False


def test_same_doi_in_different_case_counts_once():
    kq = _danh_gia([_raw("crossref", doi="10.5555/CaseTest"), _raw("openalex", doi="10.5555/casetest")])
    assert kq.so_tin_cay == 1


def test_three_distinct_reliable_papers_reach_the_default_threshold():
    kq = _danh_gia([_dinh_danh_dang_tin(1), _dinh_danh_dang_tin(2), _dinh_danh_dang_tin(3)])
    assert kq.so_tin_cay == 3 and kq.nguong == 3 and kq.du is True and kq.ket_luan_duoc is True


def test_two_distinct_reliable_papers_are_not_enough():
    kq = _danh_gia([_dinh_danh_dang_tin(1), _dinh_danh_dang_tin(2)])
    assert kq.so_tin_cay == 2 and kq.du is False
    assert kq.ket_luan_duoc is True, "nguồn lõi khoẻ mà thiếu chứng cứ => kết luận được là THIẾU (được phép leo thang)"


def test_records_without_pmid_or_doi_never_count():
    kq = _danh_gia([_raw("pubmed", pmid=None, doi=None) for _ in range(6)])
    assert kq.so_tin_cay == 0 and kq.du is False


def test_mock_records_never_count():
    kq = _danh_gia([_raw("pubmed", pmid=str(600 + i), doi=f"10.5555/m{i}", mock=True) for i in range(5)])
    assert kq.so_tin_cay == 0 and kq.du is False


@pytest.mark.parametrize("nguon", ["consensus", "serpapi_scholar"])
def test_fallback_tier_records_never_count_however_many(nguon):
    kq = _danh_gia([_raw(nguon, pmid=str(700 + i), doi=f"10.5555/t{i}") for i in range(6)])
    assert kq.so_tin_cay == 0 and kq.du is False


def test_tier_d_and_low_evidence_records_never_count():
    ban_ghi = ([_raw("pubmed", pmid=str(800 + i), doi=f"10.5555/p{i}", study_type="preprint") for i in range(3)]
               + [_raw("pubmed", pmid=str(810 + i), doi=f"10.5555/c{i}", study_type="case_report") for i in range(3)])
    kq = _danh_gia(ban_ghi)
    assert kq.so_tin_cay == 0 and kq.du is False


def test_min_evidence_argument_isolates_the_tier_d_rule():
    ban_ghi = [_raw("pubmed", pmid="820", doi="10.5555/p820", study_type="preprint"),
               _raw("pubmed", pmid="821", doi="10.5555/c821", study_type="case_report")]
    kq = _danh_gia(ban_ghi, min_evidence=0)
    assert kq.so_tin_cay == 1, "chỉ bản ghi tier C điểm thấp được tính khi ngưỡng điểm = 0; tier D vẫn bị loại"


def test_min_evidence_argument_raises_the_bar():
    kq = _danh_gia([_dinh_danh_dang_tin(1), _dinh_danh_dang_tin(2), _dinh_danh_dang_tin(3)], min_evidence=90)
    assert kq.so_tin_cay == 0 and kq.du is False


def test_threshold_defaults_to_the_setting_and_can_be_overridden(monkeypatch):
    ban_ghi = [_dinh_danh_dang_tin(1), _dinh_danh_dang_tin(2)]
    monkeypatch.setattr(settings, "fallback_min_trusted", 2)
    kq = _danh_gia(ban_ghi)
    assert kq.nguong == 2 and kq.du is True
    monkeypatch.setattr(settings, "fallback_min_trusted", 5)
    assert _danh_gia(ban_ghi).du is False
    ghi_de = _danh_gia(ban_ghi, nguong=1)
    assert ghi_de.nguong == 1 and ghi_de.du is True


def test_exactly_at_threshold_is_enough_and_one_below_is_not():
    assert _danh_gia([_dinh_danh_dang_tin(i) for i in range(1, 4)], nguong=3).du is True
    assert _danh_gia([_dinh_danh_dang_tin(i) for i in range(1, 3)], nguong=3).du is False


def test_stored_items_count_toward_sufficiency():
    ban_ghi = [_dinh_danh_dang_tin(1)]
    kho = {"pmid:9001", "doi:10.5555/stored.one"}
    kq = _danh_gia(ban_ghi, khoa_trong_kho=kho)
    assert kq.tu_luot_nay == 1 and kq.tu_kho == 2 and kq.so_tin_cay == 3
    assert kq.du is True


def test_incremental_window_zero_new_but_enough_stored_is_sufficient():
    """CA CHÍNH: ở chế độ incremental nguồn chính chỉ trả bài MỚI. 0 bài mới lượt này nhưng kho đã đủ
    => KHÔNG được coi là thiếu (nếu không cổng bắn nhầm hàng loạt và đốt hạn mức trả phí)."""
    kq = _danh_gia([], khoa_trong_kho={"pmid:9101", "pmid:9102", "doi:10.5555/stored.three"})
    assert kq.tu_luot_nay == 0 and kq.tu_kho == 3 and kq.so_tin_cay == 3
    assert kq.du is True and kq.ket_luan_duoc is True


def test_paper_present_both_this_run_and_stored_counts_once():
    rec = _raw("pubmed", pmid="9201", doi="10.5555/both")
    khoa = khoa_dinh_danh(normalize(rec))
    kq = _danh_gia([rec], khoa_trong_kho={khoa, "pmid:9202"})
    assert kq.so_tin_cay == 2, "cùng một bài ở lượt này và trong kho chỉ tính MỘT lần"


def test_nothing_this_run_and_nothing_stored_is_insufficient_but_conclusive():
    kq = _danh_gia([])
    assert kq.so_tin_cay == 0 and kq.du is False and kq.ket_luan_duoc is True
    assert kq.ly_do.strip()


def test_explicit_empty_stored_set_does_not_trigger_a_database_lookup(monkeypatch):
    """`khoa_trong_kho=set()` nghĩa là "kho không có gì" — KHÁC None ("hãy tự tra kho")."""
    def khong_duoc_goi(*_a, **_k):
        raise AssertionError("khoa_trong_kho=set() KHÔNG được kích hoạt tra DB")

    monkeypatch.setattr(es, "khoa_tin_cay_trong_kho", khong_duoc_goi)
    kq = danh_gia_du_chung_cu([_dinh_danh_dang_tin(1)], TRUY_VAN, logs=_logs_lanh(), khoa_trong_kho=set())
    assert kq.so_tin_cay == 1


def test_inputs_are_not_mutated():
    records = [_dinh_danh_dang_tin(1), _raw("consensus", pmid="5", doi="10.5555/q")]
    logs = _logs_lanh()
    khoa_kho = {"pmid:1"}
    truoc = (copy.deepcopy([r.to_dict() for r in records]), copy.deepcopy(logs), set(khoa_kho))
    _danh_gia(records, logs=logs, khoa_trong_kho=khoa_kho)
    assert ([r.to_dict() for r in records], logs, khoa_kho) == truoc


# ── Sập nguồn lõi => KHÔNG KẾT LUẬN (không leo thang) ─────────────────────────────────────

def test_all_core_sources_failed_means_no_conclusion_and_no_escalation():
    logs = [_log("pubmed", "error"), _log("europepmc", "error"), _log("crossref", "error")]
    kq = _danh_gia([], logs=logs)
    assert kq.ket_luan_duoc is False
    assert kq.du is False
    assert "chưa kết luận được" in kq.ly_do


def test_no_core_log_row_at_all_for_the_query_means_no_conclusion():
    """Circuit-breaker của sweep_source cắt sớm KHÔNG ghi log cho truy vấn bị bỏ: vắng dòng log = KHÔNG BIẾT."""
    kq = _danh_gia([], logs=[])
    assert kq.ket_luan_duoc is False and "chưa kết luận được" in kq.ly_do


def test_log_rows_of_other_queries_do_not_make_this_query_conclusive():
    logs = [_log("pubmed", truy_van="a totally different query"), _log("crossref", truy_van="another one")]
    assert _danh_gia([], logs=logs).ket_luan_duoc is False


def test_log_row_of_a_longer_query_ending_with_our_words_is_not_a_match():
    """'sepsis' KHÔNG được khớp với dòng log của truy vấn 'sepsis management' (khớp phải theo CHUỖI truy vấn đầy đủ)."""
    logs = [_log("pubmed", truy_van="sepsis management", khu_vuc="Nhiễm khuẩn"),
            _log("crossref", truy_van="sepsis management", khu_vuc="Nhiễm khuẩn")]
    assert danh_gia_du_chung_cu([], "sepsis", logs=logs, khoa_trong_kho=set()).ket_luan_duoc is False


def test_non_core_sources_alone_do_not_make_the_query_conclusive():
    logs = [_log("openalex"), _log("semantic_scholar"), _log("scopus")]
    assert _danh_gia([], logs=logs).ket_luan_duoc is False


@pytest.mark.parametrize("nguon", ["pubmed", "europepmc", "crossref"])
@pytest.mark.parametrize("trang_thai", ["ok", "degraded"])
def test_one_healthy_core_source_is_enough_to_conclude(nguon, trang_thai):
    logs = [_log("pubmed", "error"), _log("europepmc", "error"), _log("crossref", "error"), _log(nguon, trang_thai)]
    kq = _danh_gia([], logs=logs)
    assert kq.ket_luan_duoc is True and kq.du is False


def test_mock_status_on_core_rows_is_not_evidence_of_a_working_source():
    logs = [_log("pubmed", "mock"), _log("europepmc", "mock"), _log("crossref", "mock")]
    assert _danh_gia([], logs=logs).ket_luan_duoc is False


def test_no_log_information_at_all_is_judged_from_the_records_alone():
    """Biến thể một-truy-vấn theo yêu cầu (dossier/manager) không có SourceLog: `logs=None` không có
    nghĩa là 'sập nguồn' — nếu không, không bao giờ leo thang được ở đường đó."""
    kq = danh_gia_du_chung_cu([_dinh_danh_dang_tin(1)], TRUY_VAN, logs=None, khoa_trong_kho=set())
    assert kq.ket_luan_duoc is True and kq.so_tin_cay == 1 and kq.du is False


def test_outage_with_plenty_of_stored_evidence_never_asks_for_escalation():
    """Sập nguồn + kho đã đủ: ket_luan_duoc là False HOẶC du là True — dù cách nào cũng KHÔNG được ở trạng
    thái (ket_luan_duoc=True, du=False) là trạng thái duy nhất cho phép leo thang."""
    logs = [_log("pubmed", "error"), _log("europepmc", "error"), _log("crossref", "error")]
    kq = _danh_gia([], logs=logs, khoa_trong_kho={"pmid:1", "pmid:2", "pmid:3"})
    assert not (kq.ket_luan_duoc and not kq.du)


# ════════════════════════════════════════════════════════════════════════════
# (4) khoa_tin_cay_trong_kho — bản ghi đã lưu cùng ingest_query
# ════════════════════════════════════════════════════════════════════════════

def test_stored_reliable_keys_for_the_same_ingest_query(db_rieng):
    _luu(db_rieng,
         _hang(pmid="3001", doi="10.5555/S1"),
         _hang(pmid=None, doi="10.5555/S2"),
         _hang(pmid="3003"))
    khoa = khoa_tin_cay_trong_kho(TRUY_VAN)
    assert isinstance(khoa, set) and len(khoa) == 3
    assert all(isinstance(k, str) and k.split(":", 1)[0] in {"pmid", "doi"} for k in khoa)


def test_stored_keys_are_deduplicated_across_sources(db_rieng):
    _luu(db_rieng,
         _hang(source="pubmed", pmid="3101", doi="10.5555/dup"),
         _hang(source="europepmc", pmid="3101", doi="10.5555/dup"))
    assert len(khoa_tin_cay_trong_kho(TRUY_VAN)) == 1


def test_stored_keys_ignore_other_ingest_queries(db_rieng):
    _luu(db_rieng, _hang(query="sepsis management", pmid="3201"), _hang(query=TRUY_VAN, pmid="3202"))
    assert khoa_tin_cay_trong_kho(TRUY_VAN) == {khoa_dinh_danh({"pmid": "3202", "doi": None, "title": "x"})}


@pytest.mark.parametrize("ghi_de", [
    pytest.param(dict(is_mock=True), id="mock"),
    pytest.param(dict(source="consensus"), id="consensus"),
    pytest.param(dict(source="serpapi_scholar"), id="serpapi"),
    pytest.param(dict(reliability_tier="D"), id="tier-D"),
    pytest.param(dict(evidence_quality_score=59.0), id="diem-thap"),
    pytest.param(dict(evidence_quality_score=None, reliability_tier=None), id="chua-cham-diem"),
    pytest.param(dict(pmid=None, doi=None), id="khong-dinh-danh"),
    pytest.param(dict(classification="duplicate", is_primary_record=False, evidence_quality_score=None,
                      reliability_tier=None), id="ban-trung"),
])
def test_stored_rows_that_are_not_reliable_are_ignored(db_rieng, ghi_de):
    co_dinh_danh = dict(pmid="3301", doi="10.5555/ignored")
    co_dinh_danh.update(ghi_de)
    _luu(db_rieng, _hang(**co_dinh_danh))
    assert khoa_tin_cay_trong_kho(TRUY_VAN) == set()


def test_stored_threshold_follows_min_evidence_argument(db_rieng):
    _luu(db_rieng, _hang(pmid="3401", evidence_quality_score=75.0))
    assert len(khoa_tin_cay_trong_kho(TRUY_VAN)) == 1
    assert khoa_tin_cay_trong_kho(TRUY_VAN, min_evidence=80) == set()


def test_stored_keys_accept_an_existing_session(db_rieng):
    _luu(db_rieng, _hang(pmid="3501"))
    with db_rieng.session_scope() as s:
        assert len(khoa_tin_cay_trong_kho(TRUY_VAN, session=s)) == 1


def test_stored_keys_of_an_unknown_query_are_empty(db_rieng):
    assert khoa_tin_cay_trong_kho("a query nobody ever ran") == set()


def test_database_keys_feed_the_assessment_incremental_window_case(db_rieng):
    """Đường thật của cổng ở chế độ incremental: 0 bài mới lượt này + 3 bài đáng tin đã lưu trong DB => đủ,
    không leo thang. Khoá kho do `khoa_tin_cay_trong_kho` cấp phải cùng định dạng với khoá mà cổng tự tính.

    (Việc TỰ tra DB khi `khoa_trong_kho=None` KHÔNG được khẳng định ở đây: hợp đồng chỉ nói ladder truyền khoá
    kho qua `khoa_kho_fn` — phần đó được canh ở tests/test_fallback_ladder.py.)"""
    _luu(db_rieng, _hang(pmid="3601"), _hang(pmid="3602"), _hang(pmid="3603"))
    kho = khoa_tin_cay_trong_kho(TRUY_VAN)
    kq = danh_gia_du_chung_cu([], TRUY_VAN, logs=_logs_lanh(), khoa_trong_kho=kho)
    assert kq.tu_luot_nay == 0 and kq.tu_kho == 3 and kq.du is True and kq.ket_luan_duoc is True


def test_database_keys_and_this_run_are_counted_as_distinct_papers(db_rieng):
    _luu(db_rieng, _hang(pmid="3701"), _hang(pmid="3702"))
    moi = _raw("pubmed", pmid="3703", doi="10.5555/new.paper")
    kq = danh_gia_du_chung_cu([moi], TRUY_VAN, logs=_logs_lanh(), khoa_trong_kho=khoa_tin_cay_trong_kho(TRUY_VAN))
    assert kq.so_tin_cay == 3 and kq.du is True


def test_the_same_paper_stored_and_seen_this_run_is_not_double_counted(db_rieng):
    """Bài đã lưu (pmid 3751) và bản mới của CHÍNH bài đó lượt này chỉ tính một."""
    _luu(db_rieng, _hang(pmid="3751"), _hang(pmid="3752"))
    trung = _raw("europepmc", pmid="3751", doi=None)
    kq = danh_gia_du_chung_cu([trung], TRUY_VAN, logs=_logs_lanh(), khoa_trong_kho=khoa_tin_cay_trong_kho(TRUY_VAN))
    assert kq.so_tin_cay == 2 and kq.du is False


def test_assessment_ignores_database_rows_that_are_mock_or_from_fallback_tiers(db_rieng):
    _luu(db_rieng,
         _hang(pmid="3801", is_mock=True),
         _hang(pmid="3802", source="consensus"),
         _hang(pmid="3803", source="serpapi_scholar"))
    kq = danh_gia_du_chung_cu([], TRUY_VAN, logs=_logs_lanh(), khoa_trong_kho=khoa_tin_cay_trong_kho(TRUY_VAN))
    assert kq.so_tin_cay == 0 and kq.du is False and kq.ket_luan_duoc is True
