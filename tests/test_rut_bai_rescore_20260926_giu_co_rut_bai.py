"""Hồi quy rà phản biện nhóm m1 (26/09/2026) cho bản vá synthesis #4 và #6.

(1) `scripts/rescore.py --apply` chấm lại hàng DB CHỈ từ INPUT_FIELDS (cố ý không mang lý do cũ).
    Sau bản vá #4, tín hiệu rút bài chỉ còn trên DB ở `reason_for_exclusion` (tiền tố hợp đồng
    «⛔ Bài đã bị rút»). Không giữ tín hiệu ⇒ `--apply` xoá lý do rút, tier lên A, actionable trở
    lại ⇒ bài ĐÃ BỊ RÚT lọt lại bản tin/EBM_MASTER (fail-open mới do bản vá tạo trạng thái mà
    rescore xoá). Tương tự EoC không được lên Tier A/actionable.
(2) `research/dossier._cham_diem_ban_ghi` tự chấm tier, không qua `pipeline.score_item` ⇒ phải
    áp cùng trần EoC (không Tier A).
(3) Cổng GỬI `notify.ly_do_chan_gui`: lượt mới nhất không phải live ⇒ chặn, KỂ CẢ khi stats ghi
    source_health PASS (nhánh mode độc lập với nhánh source_health — đột biến bỏ nhánh mode
    trước đây sống sót vì lượt mock luôn mang DEMO).

Kiểm đột biến: bỏ `_item_tu_hang` (dùng lại dict INPUT_FIELDS trần) ⇒ nhóm (1) đỏ; bỏ trần EoC ở
dossier ⇒ (2) đỏ; bỏ nhánh mode ở `ly_do_chan_gui` ⇒ (3) đỏ.
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import pytest  # noqa: E402

from app.config import settings  # noqa: E402
from app.database import session_scope  # noqa: E402
from app.models import EvidenceItem, PipelineRun  # noqa: E402
from app.services.filtering import (  # noqa: E402
    TIEN_TO_LY_DO_EOC,
    la_ly_do_rut_bai,
    ly_do_rut_bai,
)
from app.sources.base import RawRecord  # noqa: E402

TIEU_DE = ("2025 guideline for the management of heart failure in outpatient primary care: "
           "recommendations for older adults with CKD")
TOM_TAT = ("We recommend first-line therapy and dose adjustment in renal impairment; "
           "clinicians should no longer use the previous regimen.")


@pytest.fixture()
def db_tam(monkeypatch, tmp_path):
    """DB SQLite tạm RIÊNG (không đụng DB thật)."""
    import app.database as db_mod
    from app.database import init_db

    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{tmp_path / 'rescore.db'}")
    monkeypatch.setattr(settings, "data_dir", tmp_path / "data")
    settings.ensure_dirs()
    init_db()
    yield
    monkeypatch.setattr(db_mod, "_engine", None, raising=False)
    monkeypatch.setattr(db_mod, "_SessionLocal", None, raising=False)


def _chen_hang(reason, *, title=TIEU_DE, pmid="41110921") -> int:
    with session_scope() as s:
        it = EvidenceItem(source="pubmed", source_type="article", title=title, abstract=TOM_TAT,
                          study_type="guideline", journal_or_organization="Circulation",
                          publication_date="2025", pmid=pmid, is_primary_record=True,
                          classification="excluded" if la_ly_do_rut_bai(reason) else
                          "need_full_text",
                          reliability_tier="D" if la_ly_do_rut_bai(reason) else "B",
                          reason_for_exclusion=reason, is_actionable=False)
        s.add(it)
        s.flush()
        return it.id


def _doc(hang_id: int) -> dict:
    with session_scope() as s:
        o = s.get(EvidenceItem, hang_id)
        return {"classification": o.classification, "tier": o.reliability_tier,
                "actionable": bool(o.is_actionable), "reason": o.reason_for_exclusion}


def _rescore():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    import importlib

    import rescore as mod  # type: ignore
    importlib.reload(mod)
    return mod


# ---------------------------------------------------------------------------
# (1) rescore --apply giữ tín hiệu rút bài / EoC
# ---------------------------------------------------------------------------

def test_doi_chung_hang_sach_duoc_cham_tier_a_actionable(db_tam):
    """Đối chứng: cùng nội dung KHÔNG có tín hiệu ⇒ rescore chấm tier A/actionable. Nếu đối chứng
    này không lên A thì các ca dưới không chứng minh được gì (fixture sai)."""
    hang = _chen_hang(None, pmid="40000001")
    _rescore().rescore(apply=True)
    kq = _doc(hang)
    assert kq["tier"] == "A" and kq["actionable"], f"fixture sai, đối chứng không lên A: {kq}"


def test_rescore_apply_giu_bai_da_rut_bi_loai(db_tam):
    ly_do = ly_do_rut_bai("PubMed", [{"pmid": "41999999"}])
    hang = _chen_hang(ly_do)
    _rescore().rescore(apply=True)
    kq = _doc(hang)
    assert kq["classification"] == "excluded", kq
    assert kq["tier"] == "D", kq
    assert not kq["actionable"], kq
    assert la_ly_do_rut_bai(kq["reason"]), f"lý do rút bài bị xoá/ghi đè: {kq['reason']!r}"
    assert "41999999" in (kq["reason"] or ""), "mất PMID thông báo rút"


def test_rescore_dry_run_dem_dung_bai_da_rut_khong_doi(db_tam):
    hang = _chen_hang(ly_do_rut_bai("Europe PMC"))
    res = _rescore().rescore(apply=False)
    assert res["after_actionable"] == 0, res
    assert res["after"].get("excluded") == 1, res
    assert _doc(hang)["classification"] == "excluded"


def test_rescore_apply_eoc_khong_tier_a_khong_actionable(db_tam):
    ly_do = f"{TIEN_TO_LY_DO_EOC} (thông báo quan ngại của tạp chí) — đọc toàn văn."
    hang = _chen_hang(ly_do, pmid="40000009")
    _rescore().rescore(apply=True)
    kq = _doc(hang)
    assert kq["tier"] != "A", kq
    assert not kq["actionable"], kq
    assert kq["classification"] in ("need_full_text", "watch_only", "excluded"), kq


# ---------------------------------------------------------------------------
# (2) dossier áp cùng trần EoC
# ---------------------------------------------------------------------------

def _rec(raw):
    return RawRecord(source="pubmed", source_type="article", title=TIEU_DE, abstract=TOM_TAT,
                     journal_or_organization="Circulation", publication_date="2025",
                     pmid="40000010", study_type="guideline", raw=raw)


def test_dossier_doi_chung_sach_tier_a():
    from app.research.dossier import _cham_diem_ban_ghi
    kq = _cham_diem_ban_ghi(_rec({}))
    assert kq is not None and kq["reliability_tier"] == "A", f"fixture sai: {kq}"


def test_dossier_eoc_khong_tier_a():
    from app.research.dossier import _cham_diem_ban_ghi
    kq = _cham_diem_ban_ghi(_rec({"rut_bai": "eoc", "rut_bai_nguon": "PubMed"}))
    assert kq is not None
    assert kq["reliability_tier"] != "A", kq["reliability_tier"]
    assert kq["classification"] != "actionable"


def test_dossier_bai_da_rut_bi_loai():
    from app.research.dossier import _cham_diem_ban_ghi
    assert _cham_diem_ban_ghi(_rec({"rut_bai": "retracted", "rut_bai_nguon": "PubMed"})) is None


# ---------------------------------------------------------------------------
# (3) cổng GỬI: nhánh mode độc lập với nhánh source_health
# ---------------------------------------------------------------------------

def test_notify_chan_luot_moi_nhat_mock_du_stats_ghi_pass(db_tam):
    from app.services import notify as notify_mod
    moc = datetime.now(timezone.utc)
    with session_scope() as s:
        s.add(PipelineRun(mode="mock", status="ok", started_at=moc, finished_at=moc,
                          stats={"source_health": {"status": "PASS"}}))
    ly_do = notify_mod.ly_do_chan_gui()
    assert ly_do and "khong_phai_live" in ly_do, ly_do


def test_notify_doi_chung_live_pass_cho_gui(db_tam):
    from app.services import notify as notify_mod
    moc = datetime.now(timezone.utc)
    with session_scope() as s:
        s.add(PipelineRun(mode="live", status="ok", started_at=moc, finished_at=moc,
                          stats={"source_health": {"status": "PASS"}}))
    assert notify_mod.ly_do_chan_gui() is None
