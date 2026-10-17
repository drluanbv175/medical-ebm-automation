"""G0-T3: nhánh KHÔNG lọc phải sàng đủ + mức bằng chứng SAU sàng lọc + A1 dựng lại thấy nhánh KHÔNG lọc — 17/10/2026.

Hội đồng G0 C1a (biên bản G0-DG-20261017T100649-43a39c66; người chấm chuyên môn và giám khảo cùng nêu): (1) kiểm máy
G0-T3 trả [] trong khi 13 PMID nhánh KHÔNG lọc (bộ lọc thiết kế đã loại) chưa ai sàng, 5 hit vượt trần chưa lấy về;
(2) A1 in «TRUNG BÌNH — có 1 SR/MA» từ số hit trong khi SR đó đã được sàng là lạc đề; (3) `--dung-lai-a1` in «Nhánh
KHÔNG lọc thiết kế: chưa có…» dù raw có nhánh đó (dung_lai_a1 không nạp provenance).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_tong_hop as GT  # noqa: E402
import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g0_auto as G0  # noqa: E402

STUDY = "S-G0KL"
NEN = ["34445940", "36439278"]
KHONG_LOC = {"so_hit_that": 6, "so_bai_lay_ve": 5, "tran_so_bai": 5,
             "pmid_lay_ve": ["34445940", "36439278", "42582692", "40453044", "33116425"],
             "pmid_bo_loc_da_loai": ["42582692", "40453044", "33116425"]}


def _tong_hop(**them) -> dict:
    du = {
        "schema": GT.SCHEMA_TONG_HOP, "nguoi_soan": "tong-quan-y-van", "ngay_soan": "2026-10-17",
        "sang_loc": [
            {"pmid": "34445940", "thiet_ke_that": "cắt ngang", "lien_quan": "truc_tiep", "tom_tat": "Hài lòng"},
            {"pmid": "36439278", "thiet_ke_that": "cắt ngang", "lien_quan": "gian_tiep", "tom_tat": "Phòng khám"},
        ],
        "nguon_bo_sung": [{"pmid": "42582692", "tieu_de": "SERVPERF", "thiet_ke_that": "cắt ngang",
                           "lien_quan": "truc_tiep", "tom_tat": "Ngoại trú bệnh viện huyện",
                           "cach_tim": "PubMed · nhánh khong_loc của truy vấn G0 · 2026-10-14"},
                          {"pmid": "33116425", "tieu_de": "Đau mạn", "thiet_ke_that": "cắt ngang",
                           "lien_quan": "gian_tiep", "tom_tat": "Người cao tuổi",
                           "cach_tim": "PubMed · nhánh khong_loc của truy vấn G0 · 2026-10-14"}],
        "sang_loc_khong_loc": [{"pmid": "40453044", "lien_quan": "khong", "ly_do": "telepharmacy, khác chủ đề"},
                               {"pmid": "10948789", "lien_quan": "khong", "ly_do": "người Mỹ gốc Việt"}],
        "khong_loc_vuot_tran": {"ngay": "2026-10-17", "pmid": ["10948789"], "cach": "connector PubMed, 35/35"},
        "muc_bang_chung_sau_sang_loc": "Sau sàng lọc: chỉ có khảo sát cắt ngang (PMID 34445940; PMID 42582692).",
        "tong_hop": "Khảo sát cắt ngang (PMID 34445940; PMID 42582692).",
        "rut_bai": {"ngay": "2026-10-17", "cong_cu": "check_citation_retraction.py", "ket_qua": "0 rút"},
    }
    du.update(them)
    return du


def test_khong_loc_sang_du_thi_dat():
    assert GT.kiem_tong_hop(_tong_hop(), NEN, KHONG_LOC) == []
    # Không truyền nhánh khong_loc ⇒ hành vi cũ (không đòi).
    du = _tong_hop(sang_loc_khong_loc=[], khong_loc_vuot_tran=None)
    assert GT.kiem_tong_hop(du, NEN) == []


def test_bo_sot_pmid_nhanh_khong_loc_bi_bat():
    du = _tong_hop(sang_loc_khong_loc=[{"pmid": "10948789", "lien_quan": "khong", "ly_do": "x"}])
    loi = GT.kiem_tong_hop(du, NEN, KHONG_LOC)
    assert any("còn 1/3 PMID bộ lọc đã loại chưa sàng" in x and "40453044" in x for x in loi), loi


def test_bai_lien_quan_khong_duoc_giau_o_sang_loc_khong_loc():
    du = _tong_hop(sang_loc_khong_loc=[{"pmid": "40453044", "lien_quan": "gian_tiep", "ly_do": "x"},
                                       {"pmid": "10948789", "lien_quan": "khong", "ly_do": "y"}])
    assert any("chỉ dành cho bài lạc đề" in x for x in GT.kiem_tong_hop(du, NEN, KHONG_LOC))


def test_vuot_tran_phai_lay_not_va_sang():
    loi = GT.kiem_tong_hop(_tong_hop(khong_loc_vuot_tran=None), NEN, KHONG_LOC)
    assert any("6 hit nhưng chỉ lấy về 5" in x for x in loi), loi
    du = _tong_hop(khong_loc_vuot_tran={"ngay": "2026-10-17", "pmid": ["99999999"], "cach": "x"})
    assert any("khong_loc_vuot_tran còn 1 PMID chưa sàng" in x for x in GT.kiem_tong_hop(du, NEN, KHONG_LOC))


def test_thieu_muc_sau_sang_loc_bi_bat():
    du = _tong_hop()
    du.pop("muc_bang_chung_sau_sang_loc")
    assert any("muc_bang_chung_sau_sang_loc" in x for x in GT.kiem_tong_hop(du, NEN, KHONG_LOC))


def test_muc_theo_so_hit_ghi_ro_chua_sang_loc():
    ket = {k: [] for k in ("sr_ma", "rct", "guideline", "recent", "observational")}
    ket["sr_ma"] = [G0._bai_tu_raw({"pmid": "22336833", "title": "SR", "year": "2012", "journal": "J", "url": "u"})]
    ket.update({"true_counts": {}, "all_pmids": ["22336833"], "total": 1, "query_errors": {}})
    gaps = G0.analyze_evidence_gaps(ket, "x", registry=None, meta={}, base_query="q")
    assert gaps["evidence_level"].startswith("TRUNG BÌNH — có 1 SR/MA") and "CHƯA sàng lọc" in gaps["evidence_level"]


def _de_tai(tmp_path: Path) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    raw = {"sr_ma": [], "rct": [], "guideline": [], "recent": [],
           "observational": [{"pmid": p, "title": f"T {p}", "year": "2025", "journal": "J", "url": "u"} for p in NEN],
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 2, "recent": 0},
           "search_provenance": {"nhanh": {"khong_loc": KHONG_LOC}}}
    cp = {"study": STUDY, "gate": "G0", "topic": "x", "base_query": "q",
          "pubmed_results": {"all_pmids": NEN, "total_found": 2},
          "registry_check": {"checked": True, "n_trials": 0, "n_active": 0, "trials": []}}
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": {}, "G1": {"design": "cross_sectional"}}}
    for ten, v in (("G0_pubmed_raw.json", raw), ("G0_checkpoint.json", cp), ("study_meta.json", meta),
                   (GT.TEP_TONG_HOP.format(study=STUDY), _tong_hop())):
        (d / ten).write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def test_dung_lai_a1_thay_nhanh_khong_loc_va_muc_sau_sang_loc(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    monkeypatch.setattr(G0, "_REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(G0, "guardrail_check_g0", lambda *_a, **_k: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(G0, "PubMedClient", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    assert G0.dung_lai_a1(STUDY, d) in (GC.EXIT_OK, GC.EXIT_BLOCKED, GC.EXIT_GUARDRAIL_FAIL)
    a1 = (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")
    assert "Nhánh KHÔNG lọc thiết kế (đối chiếu recall): 6 hit" in a1 and "chưa có trong lượt tìm này" not in a1
    assert "Mức bằng chứng SAU sàng lọc (agent `tong-quan-y-van`):** Sau sàng lọc: chỉ có khảo sát" in a1
    assert "PMID 40453044 (telepharmacy, khác chủ đề)" in a1, "bài lạc đề nhánh khong_loc phải hiện cho PI"
    assert "Tệp tổng hợp còn lỗi cấu trúc" not in a1


def test_kiem_may_hoi_dong_doc_nhanh_khong_loc_tu_raw(tmp_path):
    d = _de_tai(tmp_path)
    assert HD._kiem_tong_hop_g0(d, STUDY) == []
    th = d / GT.TEP_TONG_HOP.format(study=STUDY)
    du = json.loads(th.read_text(encoding="utf-8"))
    du["sang_loc_khong_loc"] = du["sang_loc_khong_loc"][1:]
    th.write_text(json.dumps(du, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert any("40453044" in x for x in HD._kiem_tong_hop_g0(d, STUDY))
