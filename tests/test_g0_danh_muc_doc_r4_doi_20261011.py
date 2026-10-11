"""Hồi quy 11/10/2026 — hai quyết định của bác sĩ sau sự cố chốt G0 của C1a.

(1) Dấu vân tay G0 băm DANH MỤC ĐỌC BỔ SUNG (ngoài PubMed): PI chốt tính mới trên bản nháp bỏ sót 5 DOI trong nước mà
    hội đồng đã giao, rồi khi danh mục được bổ sung thì cổng vẫn PASS vì dấu chỉ băm chủ đề + PMID PubMed + gate_params.
    Nay run_g0_auto ghi `danh_muc_doc_bo_sung` vào checkpoint lúc dựng A1; danh mục đổi ⇒ dấu đổi ⇒ PI chốt lại; sửa
    tệp tổng hợp mà chưa dựng lại A1 ⇒ G0-AUTO-05 REVIEW.
(2) Guardrail R4 của G1 nhận DOI ĐÚNG ĐỊNH DẠNG đứng gần hiệu số: tạp chí trong nước không lập chỉ mục PubMed nên chỉ có
    DOI; chữ «doi» trơn hay DOI sai dạng vẫn không tính là nguồn.
Không test nào gọi mạng.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import cong_song as CS  # noqa: E402
import g0_quality_gate as G0Q  # noqa: E402
import g0_tong_hop as GT  # noqa: E402
import run_g0_auto as G0  # noqa: E402
import run_g1_auto as G1A  # noqa: E402

STUDY = "S-G0DM"
PMIDS = ["34445940", "36439278", "16148334"]
DOI_108 = "10.52163/yhc.v67icd5.5018"


def _ghi(p: Path, du_lieu) -> None:
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(du_lieu if isinstance(du_lieu, str) else json.dumps(du_lieu, ensure_ascii=False))


def _tong_hop(*bo_sung: dict) -> dict:
    return {"schema": GT.SCHEMA_TONG_HOP, "nguon_bo_sung": list(bo_sung)}


def _de_tai(tmp_path: Path, tong_hop=None) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    raw = {"sr_ma": [], "rct": [], "guideline": [], "recent": [],
           "observational": [{"pmid": p, "title": f"T {p}", "year": "2025", "journal": "J", "url": "u"}
                             for p in PMIDS],
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 3, "recent": 0}}
    cp = {"study": STUDY, "gate": "G0", "topic": "x", "base_query": "q",
          "pubmed_results": {"all_pmids": PMIDS, "total_found": 3},
          "registry_check": {"checked": True, "n_trials": 0, "n_active": 0, "trials": []}}
    _ghi(d / "G0_pubmed_raw.json", raw)
    _ghi(d / "G0_checkpoint.json", cp)
    _ghi(d / "study_meta.json", {"design_code": "cross_sectional",
                                 "gate_params": {"G0": {}, "G1": {"design": "cross_sectional"}}})
    _ghi(d / f"G0_A1_PICO_FINER_{STUDY}.md", "A1 cũ\n")
    if tong_hop is not None:
        _ghi(d / GT.TEP_TONG_HOP.format(study=STUDY), tong_hop)
    return d


def _dung_lai(d: Path, monkeypatch) -> dict:
    monkeypatch.setattr(G0, "_REPO_ROOT", d.parent.parent)
    monkeypatch.setattr(G0, "guardrail_check_g0", lambda *_a, **_k: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(G0, "PubMedClient", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    G0.dung_lai_a1(STUDY, d)
    return json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))


def _auto05(d: Path) -> dict:
    r = G0Q.evaluate_study(STUDY, d, write=False)
    return next(c for c in r["automatic_criteria"] if c["id"] == "G0-AUTO-05")


# ── (1) Danh mục đọc bổ sung ─────────────────────────────────────────────────────────────────────────────────────

def test_ma_danh_muc_chuan_hoa_bo_trung_bo_sai_dang():
    du_lieu = _tong_hop({"pmid": "42625778"}, {"doi": "10.52163/YHC.V67ICD5.5018"}, {"doi": DOI_108},
                        {"doi": "khong-phai-doi"}, {"pmid": "12"}, "rác")
    assert GT.ma_danh_muc_bo_sung(du_lieu) == [f"doi:{DOI_108}", "pmid:42625778"]
    assert GT.ma_danh_muc_bo_sung(None) == [] and GT.ma_danh_muc_bo_sung({"nguon_bo_sung": "x"}) == []


def test_doc_danh_muc_vang_la_rong_hong_la_khong_do_duoc(tmp_path):
    assert GT.doc_danh_muc_bo_sung(tmp_path, STUDY) == ([], None)
    _ghi(tmp_path / GT.TEP_TONG_HOP.format(study=STUDY), "{hỏng")
    ds, loi = GT.doc_danh_muc_bo_sung(tmp_path, STUDY)
    assert ds is None and loi


def test_dau_van_tay_bam_danh_muc_nhung_rong_thi_y_nhu_cu():
    meta = {"gate_params": {"G0": {"population": "người bệnh ngoại trú"}}}
    cp = {"topic": "x", "pubmed_results": {"all_pmids": PMIDS}}
    cu = CS.dau_van_tay("x", sorted(PMIDS), {"population": "người bệnh ngoại trú"})
    assert G0Q.dau_van_tay_g0(cp, meta) == cu, "đề tài chưa có danh mục bổ sung: xác nhận cũ KHÔNG bị vô hiệu oan"
    assert G0Q.dau_van_tay_g0({**cp, "danh_muc_doc_bo_sung": []}, meta) == cu
    co = G0Q.dau_van_tay_g0({**cp, "danh_muc_doc_bo_sung": ["pmid:42625778"]}, meta)
    them = G0Q.dau_van_tay_g0({**cp, "danh_muc_doc_bo_sung": ["pmid:42625778", f"doi:{DOI_108}"]}, meta)
    assert len({cu, co, them}) == 3, "danh mục đọc đổi ⇒ dấu đổi ⇒ PI chốt lại"


def test_dung_lai_a1_ghi_danh_muc_va_auto05_bat_a1_cu(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, _tong_hop({"pmid": "42625778"}))
    cp = _dung_lai(d, monkeypatch)
    assert cp["danh_muc_doc_bo_sung"] == ["pmid:42625778"]
    assert _auto05(d)["status"] == "PASS"
    dau_truoc = G0Q.dau_van_tay_g0(cp, json.loads((d / "study_meta.json").read_text(encoding="utf-8")))

    # Agent bổ sung DOI vào danh mục mà CHƯA dựng lại A1 ⇒ AUTO-05 đòi dựng lại.
    _ghi(d / GT.TEP_TONG_HOP.format(study=STUDY), _tong_hop({"pmid": "42625778"}, {"doi": DOI_108}))
    a5 = _auto05(d)
    assert a5["status"] == "REVIEW" and "1 mục lúc dựng, 2 mục hiện hành" in a5["evidence"]
    assert "--dung-lai-a1" in a5["action"] and "PI chốt lại" in a5["action"]

    # Dựng lại ⇒ AUTO-05 sạch, dấu vân tay ĐỔI (xác nhận cũ hết hiệu lực).
    cp2 = _dung_lai(d, monkeypatch)
    assert cp2["danh_muc_doc_bo_sung"] == [f"doi:{DOI_108}", "pmid:42625778"]
    assert _auto05(d)["status"] == "PASS"
    assert G0Q.dau_van_tay_g0(cp2, json.loads((d / "study_meta.json").read_text(encoding="utf-8"))) != dau_truoc


def test_tep_tong_hop_hong_thi_auto05_khong_do_duoc(tmp_path, monkeypatch):
    d = _de_tai(tmp_path, _tong_hop({"pmid": "42625778"}))
    _dung_lai(d, monkeypatch)
    _ghi(d / GT.TEP_TONG_HOP.format(study=STUDY), "{hỏng")
    a5 = _auto05(d)
    assert a5["status"] == "REVIEW" and "không đối chiếu được" in a5["evidence"]


def test_khong_co_tep_tong_hop_thi_auto05_nhu_cu(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    cp = _dung_lai(d, monkeypatch)
    assert cp["danh_muc_doc_bo_sung"] == []
    assert _auto05(d)["status"] == "PASS"



class _Rec:
    def __init__(self, pmid):
        self.pmid, self.title, self.publication_date = pmid, f"Title {pmid}", "2025"
        self.journal_or_organization, self.authors = "J Test", "Author A"
        self.url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def test_luot_day_du_cung_ghi_danh_muc(tmp_path):
    """Lượt G0 đầy đủ (có tra PubMed) cũng ghi danh mục mà A1 trình bày — không chỉ đường dựng lại A1."""
    _ghi(tmp_path / GT.TEP_TONG_HOP.format(study="S"), _tong_hop({"doi": DOI_108}))
    obs = [_Rec(p) for p in PMIDS]
    res = {"sr_ma": [], "rct": [], "guideline": [], "recent": [], "observational": obs,
           "all_pmids": PMIDS, "total": 3, "query_errors": {},
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 3, "recent": 0}}
    cp_path = G0.write_checkpoint("S", tmp_path, res, G0.analyze_evidence_gaps(res, "x"),
                                  {"passed": True, "errors": []}, tmp_path / "a.md", None, topic="x", base_query="x")
    assert json.loads(cp_path.read_text(encoding="utf-8"))["danh_muc_doc_bo_sung"] == [f"doi:{DOI_108}"]

# ── (2) R4 của G1 nhận DOI đúng định dạng ────────────────────────────────────────────────────────────────────────

def _loi_r4(van_ban: str) -> list:
    return [e for e in G1A.guardrail_check_g1(van_ban, [])["errors"] if e.startswith("R4")]


def test_r4_nhan_doi_dung_dang_gan_hieu_so():
    assert _loi_r4(f"Hài lòng với thời gian chờ (OR=29,5; 95%CI 12,9–67,2; doi:{DOI_108}).") == []
    assert _loi_r4("Hài lòng (OR=2.59; PMID 34445940).") == [], "PMID vẫn được nhận"
    assert _loi_r4("Hài lòng (OR=2.59 [CẦN BÁC SĨ KIỂM]).") == [], "nhãn [CẦN…] vẫn được nhận"


def test_r4_van_chan_khi_khong_co_nguon_that():
    assert _loi_r4("Hài lòng (OR=29,5).")
    assert _loi_r4("Hài lòng (OR=29,5; doi: đang tìm)."), "chữ «doi» trơn không phải nguồn"
    assert _loi_r4("Hài lòng (OR=29,5; doi:10.12/abc)."), "DOI sai dạng (tiền tố < 4 số) không phải nguồn"
    xa = "Hài lòng (OR=29,5)." + " x" * 60 + f" doi:{DOI_108}"
    assert _loi_r4(xa), "DOI ngoài cửa sổ ±80 ký tự không gắn được với hiệu số"
