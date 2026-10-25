"""Hồi quy 25/10/2026 — engine KHÔNG xếp tier A cho bản lưu trên kho lưu trữ đa năng (câu trả lời AI trên Zenodo).

Sự cố 18/10/2026: OpenAlex trả các câu trả lời AI «Trip Database Ask» lưu trên Zenodo (DOI 10.5281/zenodo.*). Bộ suy
thiết kế đọc chữ «guidelines» trong tiêu đề ⇒ `study_type = guideline`; tên KDIGO/AUA nằm trong CÂU HỎI bị đọc thành tổ
chức phát hành ⇒ điểm chất lượng 90–93 ⇒ tier A «actionable» ⇒ cầu nối đưa 4 bản vào hub EBM_MASTER thành thẻ «guideline
tier A». Bản vá #175 chỉ chặn nạp lại 5 khoá đã biết; bản vá này chặn GỐC ở bốn lớp: suy thiết kế, điểm chất lượng,
tier + phân loại, cầu nối (hàng DB chấm trước luật mới). Bốn tiêu đề dưới đây chép đúng DB engine. Ngoại tuyến
hoàn toàn.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.scoring.evidence_quality import evidence_quality_score
from app.services.filtering import classify
from app.services.pipeline import score_item
from app.sources.classify_meta import infer_study_type
from app.utils.kho_luu_tru import kho_luu_tru_da_nang

REPO_ROOT = Path(__file__).resolve().parent.parent
ZENODO = "Zenodo (CERN European Organization for Nuclear Research)"
SU_CO = [  # (tiêu đề, DOI) — 4 bản tier A «actionable» trong DB engine (đo 25/10/2026)
    ("What are the key recommendations in the KDIGO 2025 guidelines for managing nephrotic syndrome in children?",
     "10.5281/zenodo.20280180"),
    ("What are the recommended estrogen-based treatments for preventing recurrent urinary tract infections in "
     "postmenopausal women according to the AUA/CUA/SUFU guideline?", "10.5281/zenodo.20562270"),
    ("What do the KDIGO guidelines recommend for anemia management?", "10.5281/zenodo.20834906"),
    ("What are the recommended guidelines for restarting anticoagulation therapy in patients with deep vein thrombosis "
     "after an upper gastrointestinal bleed?", "10.5281/zenodo.22664442"),
]


@pytest.mark.parametrize("doi, noi_luu, ky_vong", [
    ("10.5281/zenodo.20834906", None, "Zenodo"),
    ("https://doi.org/10.5281/ZENODO.1", None, "Zenodo"),
    (None, ZENODO, "Zenodo"),
    ("10.6084/m9.figshare.1", None, "figshare"),
    (None, "Figshare", "figshare"),
    (None, "Open Science Framework", "OSF"),
    (None, "OSF", "OSF"),
    (None, "OSF Registries", "OSF"),
    ("10.17605/osf.io/abcd", None, "OSF"),
    (None, "Dryad Digital Repository", "Dryad"),
    (None, "Harvard Dataverse", "Harvard Dataverse"),
    ("10.17632/xyz.1", "Mendeley Data", "Mendeley Data"),
    # Tạp chí THẬT có chữ «Open Science» — không phải kho lưu trữ
    (None, "European Urology Open Science", None),
    (None, "Biological Psychiatry Global Open Science", None),
    ("10.1016/j.kint.2025.01.001", "Kidney International", None),
    (None, None, None),
])
def test_nhan_dien_kho_luu_tru_theo_tien_to_doi_va_ten_noi_luu(doi, noi_luu, ky_vong):
    assert kho_luu_tru_da_nang(doi, noi_luu) == ky_vong


def test_suy_thiet_ke_khong_doc_chu_trong_tieu_de_cua_ban_luu_tren_kho():
    for tieu_de, doi in SU_CO:
        assert infer_study_type(tieu_de, "article", ZENODO, doi=doi) != "guideline", tieu_de
        assert infer_study_type(tieu_de, "article", None, doi=doi) != "guideline", "chỉ có DOI vẫn nhận ra kho"
    # Đối chứng: cùng tiêu đề ở tạp chí thật vẫn là guideline (luật cũ không đổi)
    assert infer_study_type(SU_CO[2][0], "article", "Kidney International") == "guideline"
    assert infer_study_type("Statins: a systematic review and meta-analysis", "article", "Figshare") is None
    assert infer_study_type("A randomized controlled trial of X", "dataset", "Harvard Dataverse") is None
    # Tín hiệu không phải thiết kế mạnh vẫn xét như thường
    assert infer_study_type("A case report of Y", "article", ZENODO) == "case_series"
    assert infer_study_type("Preprint: Z", "article", ZENODO) == "preprint"


@pytest.mark.parametrize("tieu_de, doi", SU_CO)
def test_bon_ban_ghi_su_co_khong_con_tier_a_hay_actionable(tieu_de, doi):
    # Hàng DB cũ còn lưu study_type «guideline» (suy trước luật mới) ⇒ lớp chấm điểm phải tự chặn, không dựa vào
    # lớp suy.
    item = {"title": tieu_de, "journal_or_organization": ZENODO, "doi": doi, "study_type": "guideline",
            "document_type": "article", "source_type": "article"}
    score_item(item)
    phan_loai, actionable, ly_do_a, ly_do_x = classify(item)
    assert item["reliability_tier"] == "C" and not actionable and phan_loai == "watch_only"
    assert "kho lưu trữ đa năng Zenodo" in ly_do_x and not ly_do_a
    bd = item["_score_breakdown"]["evidence_quality"]
    assert bd["kho_luu_tru_da_nang"] == -bd["base_design"] and "official_guideline" not in bd
    assert "_detected_org" not in item, "tên tổ chức nằm trong CÂU HỎI không phải nơi phát hành"


def test_doi_chung_cung_tieu_de_o_tap_chi_that_van_tier_a():
    item = {"title": SU_CO[2][0], "journal_or_organization": "Kidney International",
            "doi": "10.1016/j.kint.2025.01.001", "study_type": "guideline", "document_type": "article",
            "source_type": "article"}
    score_item(item)
    assert item["reliability_tier"] == "A" and classify(item)[1] is True


def test_thiet_ke_khong_manh_tren_kho_khong_bi_tru_nen_diem():
    eq, bd = evidence_quality_score({"title": "A case report", "journal_or_organization": ZENODO,
                                     "study_type": "case_series"})
    assert "kho_luu_tru_da_nang" not in bd and bd["base_design"] == 25


def test_ban_tren_kho_da_loai_thi_van_loai():
    item = {"title": "Preprint on Zenodo", "journal_or_organization": ZENODO, "doi": "10.5281/zenodo.1",
            "study_type": "preprint"}
    score_item(item)
    assert item["reliability_tier"] == "D" and classify(item)[0] == "excluded"


def test_cham_lai_db_mang_doi_vao_luat_kho_luu_tru():
    spec = importlib.util.spec_from_file_location("rescore_kho_luu_tru", REPO_ROOT / "scripts" / "rescore.py")
    rescore = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rescore)
    assert "doi" in rescore.INPUT_FIELDS
    hang = SimpleNamespace(**{f: None for f in rescore.INPUT_FIELDS}, reason_for_exclusion=None)
    hang.title, hang.study_type, hang.doi = SU_CO[2][0], "guideline", SU_CO[2][1]  # nguồn không ghi tên nơi lưu
    item = rescore._item_tu_hang(hang)
    score_item(item)
    assert item["reliability_tier"] == "C"


# ── cầu nối engine → hub: hàng DB chấm TRƯỚC luật mới vẫn mang tier A ─────────────────────────────────────────────────

_COT = ["is_mock", "is_actionable", "reliability_tier", "practice_change_score", "evidence_quality_score",
        "journal_or_organization", "source", "title", "url", "pmid", "doi", "source_type", "study_type",
        "publication_date", "update_date", "clinical_area", "population", "intervention", "comparator",
        "outcomes", "practice_impact", "safety_signal", "actionable_reason", "reason_for_exclusion",
        "official_grade", "operational_evidence_level", "synthesis", "last_run_id"]


@pytest.fixture()
def bridge(monkeypatch):
    gia = types.ModuleType("ledger_ids")
    gia.assert_unique = lambda cards: None
    gia.max_seq = lambda cards: len(cards)
    monkeypatch.setitem(sys.modules, "ledger_ids", gia)
    spec = importlib.util.spec_from_file_location("bridge_kho_luu_tru",
                                                  REPO_ROOT / "scripts" / "bridge_to_ebm_master.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_cau_noi_bo_qua_hang_tren_kho_luu_tru_ke_ca_khi_db_con_tier_a(bridge, tmp_path, monkeypatch, capsys):
    hub = tmp_path / "EBM_MASTER"
    hub.mkdir()
    (hub / "EBM_MASTER.json").write_text(json.dumps({"meta": {"counts": {"evidence_cards": 0}}, "evidence_cards": []}),
                                         encoding="utf-8", newline="\n")
    db = tmp_path / "medical_ebm.db"
    con = sqlite3.connect(db)
    con.execute("CREATE TABLE evidence_items (%s)" % ", ".join(_COT))
    hang = [{"title": t, "doi": d, "journal_or_organization": ZENODO} for t, d in SU_CO]
    hang += [{"title": "Một guideline mới thật", "pmid": "99999999", "journal_or_organization": "Kidney International"},
             {"title": "Bản Zenodo không ghi tên nơi lưu", "doi": "10.5281/zenodo.99"}]
    for h in hang:
        day = {c: None for c in _COT}
        day.update({"is_mock": 0, "is_actionable": 1, "reliability_tier": "A", "practice_change_score": 60,
                    "evidence_quality_score": 93, "study_type": "guideline"})
        day.update(h)
        con.execute("INSERT INTO evidence_items VALUES (%s)" % ", ".join("?" * len(_COT)), [day[c] for c in _COT])
    con.commit()
    con.close()
    monkeypatch.setattr(bridge, "HUB", str(hub))
    monkeypatch.setattr(sys, "argv", ["bridge", "--today", "2026-10-25", "--db", str(db)])
    assert bridge.main() == 0
    the = json.loads((hub / "EBM_MASTER.json").read_text(encoding="utf-8"))["evidence_cards"]
    assert [c["source"]["pmid"] for c in the] == ["99999999"], "chỉ mục thật vào hub"
    assert "5 bỏ qua vì nằm trên kho lưu trữ đa năng" in capsys.readouterr().out


def test_tran_tier_c_cho_moi_duong_goi_reliability_tier():
    """Lớp phòng thủ: người gọi tự tính điểm (vd `app/research/dossier.py`) vẫn không đưa bản trên kho lên A/B."""
    from app.scoring.reliability import reliability_tier
    for item in ({"study_type": "guideline", "doi": SU_CO[0][1]},
                 {"study_type": "cohort", "journal_or_organization": "Figshare"}):
        assert reliability_tier(item, 95.0, 80.0) == "C"
    assert reliability_tier({"study_type": "guideline", "journal_or_organization": "Kidney International"},
                            95.0, 80.0) == "A", "đối chứng: nơi phát hành thật vẫn lên A"
