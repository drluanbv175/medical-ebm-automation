"""Hồi quy 10/10/2026 — G0-T3/G0-T4 theo hai biên bản đánh giá chéo của hội đồng cổng G0 (C1a, 07/10/2026).

Biên bản G0-DG-…-0b213597 (G0-T3) và G0-DG-…-79f9a227 (G0-T4) trả về sửa vì A1: chỉ hiện 5/12 PMID; khẳng định phủ định
(«chưa có SR/guideline») không ghi phạm vi rồi lan sang G1/G10; gợi ý RCT/CONSORT cho câu hỏi mô tả; khối bàn giao thiếu
khoá bộ chấm đòi (lý do FINER, dau_van_tay_chot, registry_manual_checked); không sàng lọc mức liên quan; không bảng
guideline/văn bản quy phạm, phát biểu khoảng trống, mức tính mới, trạng thái nguồn; «~13%» không nguồn; ô «[suy ra từ
topic]» trái «hệ KHÔNG suy PICO». Mỗi test neo một lỗi đó — KIỂM HÀNH VI, không gọi mạng.
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _p in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_tong_hop as GT  # noqa: E402
import gate_contract as GC  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import research_study_spec as RS  # noqa: E402
import run_g0_auto as G0  # noqa: E402

PMIDS = ["34445940", "36439278", "16148334"]
STUDY = "S-G0TH"


class _Rec:
    def __init__(self, pmid, year="2025"):
        self.pmid = pmid
        self.title = f"Title {pmid}"
        self.publication_date = year
        self.journal_or_organization = "J Test"
        self.authors = "Author A"
        self.url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _results(n_obs: int = 12, year_obs: str = "2025") -> dict:
    obs = [_Rec(str(30000000 + i), year_obs) for i in range(n_obs)]
    return {"sr_ma": [], "rct": [], "guideline": [], "recent": [], "observational": obs,
            "all_pmids": [r.pmid for r in obs], "total": n_obs,
            "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": n_obs, "recent": 0},
            "query_errors": {}}


META_MO_TA = {"gate_params": {"G0": {"question_type": "descriptive"}, "G1": {}}}
META_GHIM = {"design_code": "cross_sectional", "gate_params": {"G0": {}, "G1": {"design": "cross_sectional"}}}
META_DIEU_TRI = {"gate_params": {"G0": {"question_type": "treatment"}, "G1": {}}}


def _tong_hop_hop_le() -> dict:
    return {
        "schema": GT.SCHEMA_TONG_HOP, "nguoi_soan": "tong-quan-y-van", "ngay_soan": "2026-10-10",
        "sang_loc": [
            {"pmid": "34445940", "thiet_ke_that": "cắt ngang", "lien_quan": "truc_tiep",
             "tom_tat": "Hài lòng ngoại trú"},
            {"pmid": "36439278", "thiet_ke_that": "cắt ngang", "lien_quan": "gian_tiep",
             "tom_tat": "Phòng khám đa khoa"},
            {"pmid": "16148334", "thiet_ke_that": "cắt ngang", "lien_quan": "khong", "tom_tat": "PTSD",
             "ly_do": "khớp chữ Vietnam, khác chủ đề"},
        ],
        "nguon_bo_sung": [{"pmid": "32992600", "tieu_de": "SR", "thiet_ke_that": "tổng quan hệ thống",
                           "lien_quan": "truc_tiep", "tom_tat": "Yếu tố liên quan",
                           "cach_tim": "PubMed · MeSH · 2026-10-10"}],
        "tong_hop": "Thời gian chờ đi kèm hài lòng thấp hơn (PMID 34445940; PMID 32992600).",
        "rut_bai": {"ngay": "2026-10-10", "cong_cu": "check_citation_retraction.py", "ket_qua": "0 rút"},
    }


def _khoang_trong_hop_le() -> dict:
    return {
        "schema": GT.SCHEMA_KHOANG_TRONG, "nguoi_soan": "khoang-trong-nghien-cuu", "ngay_soan": "2026-10-10",
        "guideline_lien_quan": [{"ten": "Văn bản hướng dẫn đo hài lòng", "nam": "2024", "nguon": "Bộ Y tế",
                                 "noi_dung": "Phương pháp đo hài lòng", "muc": ""}],
        "phat_bieu_khoang_trong": "Chưa tìm thấy dữ liệu công bố tại chính khoa trong phạm vi đã tra.",
        "loai_khoang_trong": ["boi_canh", "cong_cu_do"],
        "muc_novelty": {"muc": "nhan_rong_co_kiem_chung", "y_nghia": "Dữ liệu nền tại chỗ"},
        "trang_thai_nguon": {"pubmed": "day_du", "clinicaltrials_gov": "day_du", "who_ictrp": "chua_tra"},
        "nhap_finer": {"finer_feasible": "CẦN PI QUYẾT — rủi ro tỷ lệ đồng ý", "finer_interesting": "ĐỀ XUẤT ĐẠT — …",
                       "finer_novel": "ĐỀ XUẤT ĐẠT — …", "finer_ethical": "CẦN PI QUYẾT — riêng tư",
                       "finer_relevant": "ĐỀ XUẤT ĐẠT — …"},
    }


# ── 1. Khoảng trống của máy ghi PHẠM VI; câu hỏi không can thiệp không bị khuyên RCT ──────────────────────────────

def test_khoang_trong_phu_dinh_ghi_pham_vi_khong_tuyet_doi():
    gaps = G0.analyze_evidence_gaps(_results(), "x", meta=META_MO_TA, base_query="patient satisfaction Vietnam")
    van = " | ".join(gaps["gaps"])
    assert "Chưa có systematic review" not in van and "Chưa có guideline" not in van
    assert "«patient satisfaction Vietnam»" in van and "KHÔNG phải kết luận" in van
    assert "Bộ Y tế" in van, "dòng guideline phải nhắc văn bản quy phạm không nằm trên PubMed"


def test_cau_hoi_mo_ta_khong_bi_neu_thieu_rct_va_khong_goi_y_rct():
    gaps = G0.analyze_evidence_gaps(_results(), "x", meta=META_MO_TA)
    assert not any("RCT" in g and "Không thấy RCT" in g for g in gaps["gaps"])
    assert "cross_sectional" in gaps["design_hint"] and "RCT" not in gaps["design_hint"]
    dt = G0.analyze_evidence_gaps(_results(), "x", meta=META_DIEU_TRI)
    assert any(g.startswith("Không thấy RCT") for g in dt["gaps"]), "câu hỏi điều trị vẫn phải nêu thiếu RCT"
    assert "RCT" in dt["design_hint"]


def test_thiet_ke_da_ghim_di_truoc_goi_y_theo_so_hit():
    gaps = G0.analyze_evidence_gaps(_results(), "x", meta=META_GHIM)
    assert gaps["design_hint"].startswith("Thiết kế `cross_sectional` theo thiết kế đã ghim ở G1")


def test_nam_moi_nhat_tinh_ca_nhanh_quan_sat():
    assert G0.analyze_evidence_gaps(_results(year_obs="2025"), "x")["most_recent_year"] == 2025


def test_muc_bang_chung_quan_sat_noi_chua_sang_loc():
    lvl = G0.analyze_evidence_gaps(_results(), "x", base_query="q")["evidence_level"]
    assert "CHƯA sàng lọc mức liên quan" in lvl and "«q»" in lvl


# ── 2. A1: đủ PMID, đúng khoá bàn giao, không văn mẫu vô nguồn ─────────────────────────────────────────────────

def _a1(meta=None, out_dir=None, res=None) -> str:
    res = res or _results()
    gaps = G0.analyze_evidence_gaps(res, "x", meta=meta, base_query="q")
    return G0.generate_a1_artifact("x", STUDY, {"base": "q"}, res, gaps, "2026-10-10 09:00", meta=meta,
                                   out_dir=out_dir)


def test_a1_liet_ke_du_moi_pmid():
    art = _a1()
    for i in range(12):
        assert f"PMID: {30000000 + i}" in art
    assert "bài khác" not in art and "liệt kê đủ 12 bài" in art


def test_a1_khoi_ban_giao_dung_khoa_bo_cham():
    art = _a1(meta=META_MO_TA)
    for khoa in ("registry_manual_checked", "dau_van_tay_chot", "«ĐẠT — <lý do>»", "--dung-lai-a1",
                 "hoi_dong_cong.py cham-song"):
        assert khoa in art, khoa


def test_a1_khong_con_van_mau_sai():
    art = _a1()
    assert "[suy ra từ topic" not in art and "~13%" not in art and "PMIDs đã được xác minh" not in art
    assert "khoảng trống (§5)" not in art and "ở §5 chỉ đúng" not in art
    assert art.index("### 3.4 Nghiên cứu QUAN SÁT") < art.index("### 3.5 SR/MA")


def test_a1_ghi_chu_thiet_ke_da_ghim():
    assert "Đã có quyết định thiết kế:** `cross_sectional`" in _a1(meta=META_GHIM)
    assert "Đã có quyết định thiết kế" not in _a1()


def test_a1_thieu_tep_agent_thi_nhan_can_dung_agent():
    art = _a1(out_dir=None)
    assert "[CẦN `tong-quan-y-van` LẬP `G0_TONG_HOP_BANG_CHUNG_S-G0TH.json`]" in art
    assert "[CẦN `khoang-trong-nghien-cuu` LẬP `G0_KHOANG_TRONG_S-G0TH.json`]" in art
    assert "## PHẦN 4b" in art


def test_a1_trinh_bay_hai_tep_agent(tmp_path):
    res = _results(n_obs=0)
    res["observational"] = [_Rec(p) for p in PMIDS]
    res["all_pmids"] = list(PMIDS)
    (tmp_path / GT.TEP_TONG_HOP.format(study=STUDY)).write_text(
        json.dumps(_tong_hop_hop_le(), ensure_ascii=False), encoding="utf-8", newline="\n")
    (tmp_path / GT.TEP_KHOANG_TRONG.format(study=STUDY)).write_text(
        json.dumps(_khoang_trong_hop_le(), ensure_ascii=False), encoding="utf-8", newline="\n")
    art = _a1(out_dir=tmp_path, res=res)
    assert "| 34445940 | cắt ngang | trực tiếp |" in art
    assert art.index("| 34445940 |") < art.index("| 16148334 |"), "liên quan trực tiếp phải đứng trước"
    assert "| 32992600 |" in art and "PubMed · MeSH · 2026-10-10" in art
    assert "Văn bản hướng dẫn đo hài lòng" in art and "nhan_rong_co_kiem_chung" in art
    assert "`finer_feasible`: CẦN PI QUYẾT" in art
    assert "còn lỗi cấu trúc" not in art
    # Tệp hợp lệ không được làm A1 vấp mẫu «ngày dd/mm/yyyy» của guardrail R2 (đo thật trên C1a 10/10/2026).
    import re
    assert re.search(r"\b\d{2}[/-]\d{2}[/-](19|20)\d{2}\b", art) is None


# ── 3. Bộ kiểm hai tệp agent ─────────────────────────────────────────────────────────────────────────────────

def test_kiem_tong_hop_hop_le_va_tung_vi_pham():
    assert GT.kiem_tong_hop(_tong_hop_hop_le(), PMIDS) == []
    ca = {
        "thiếu PMID nền": lambda d: d["sang_loc"].pop(),
        "PMID lạ trong sàng lọc": lambda d: d["sang_loc"].append(
            {"pmid": "99999999", "thiet_ke_that": "x", "lien_quan": "khong", "tom_tat": "x", "ly_do": "x"}),
        "liên quan sai": lambda d: d["sang_loc"][0].update(lien_quan="co"),
        "không liên quan thiếu lý do": lambda d: d["sang_loc"][2].pop("ly_do"),
        "thiếu thiết kế thật": lambda d: d["sang_loc"][1].update(thiet_ke_that=""),
        "tóm lược không dẫn PMID trực tiếp": lambda d: d.update(tong_hop="Có liên quan (PMID 36439278)."),
        "thiếu rút bài": lambda d: d.pop("rut_bai"),
        "nguồn bổ sung thiếu cách tìm": lambda d: d["nguon_bo_sung"][0].pop("cach_tim"),
        "nguồn bổ sung trùng nền": lambda d: d["nguon_bo_sung"][0].update(pmid="34445940"),
        "ngày tương lai": lambda d: d.update(ngay_soan=(date.today() + timedelta(days=3)).isoformat()),
        "sai schema": lambda d: d.update(schema="x"),
        "PII": lambda d: d["sang_loc"][0].update(tom_tat="liên hệ 0912345678"),
        "ngày dd/mm/yyyy (guardrail R2 chặn A1)": lambda d: d.update(tong_hop=d["tong_hop"] + " Tra 31/07/2026."),
    }
    for ten, sua in ca.items():
        d = _tong_hop_hop_le()
        sua(d)
        assert GT.kiem_tong_hop(d, PMIDS), f"không bắt được: {ten}"


def test_kiem_khoang_trong_hop_le_va_tung_vi_pham():
    assert GT.kiem_khoang_trong(_khoang_trong_hop_le()) == []
    ca = {
        "agent tự đánh giá F": lambda d: d["nhap_finer"].update(finer_feasible="ĐẠT — đủ người"),
        "agent tự đánh giá E": lambda d: d["nhap_finer"].update(finer_ethical="ĐẠT — tối thiểu"),
        "FINER là cờ": lambda d: d["nhap_finer"].update(finer_novel=True),
        "thiếu khoá FINER": lambda d: d["nhap_finer"].pop("finer_relevant"),
        "tuyệt đối hoá": lambda d: d.update(phat_bieu_khoang_trong="Đây là nghiên cứu lần đầu tiên tại Việt Nam."),
        "bảng guideline rỗng": lambda d: d.update(guideline_lien_quan=[]),
        "guideline thiếu nguồn": lambda d: d["guideline_lien_quan"][0].update(nguon=""),
        "loại khoảng trống lạ": lambda d: d.update(loai_khoang_trong=["moi"]),
        "mức tính mới lạ": lambda d: d["muc_novelty"].update(muc="cao"),
        "trạng thái nguồn thiếu ICTRP": lambda d: d["trang_thai_nguon"].pop("who_ictrp"),
        "phát biểu quá dài": lambda d: d.update(phat_bieu_khoang_trong="x" * 701),
        "ngày dd/mm/yyyy": lambda d: d["guideline_lien_quan"][0].update(nam="ngày 08/01/2024"),
    }
    for ten, sua in ca.items():
        d = _khoang_trong_hop_le()
        sua(d)
        assert GT.kiem_khoang_trong(d), f"không bắt được: {ten}"


def test_tep_hong_bao_loi_doc_khong_coi_la_vang(tmp_path):
    (tmp_path / GT.TEP_TONG_HOP.format(study=STUDY)).write_text("{hỏng", encoding="utf-8", newline="\n")
    du_lieu, loi = GT.doc(tmp_path, GT.TEP_TONG_HOP, STUDY)
    assert du_lieu is None and loi and "không đọc được" in loi
    assert GT.doc(tmp_path, GT.TEP_KHOANG_TRONG, STUDY) == (None, None)


# ── 4. Bảng trách nhiệm: đầu ra + kiểm máy cấp nhiệm vụ ─────────────────────────────────────────────────────

def test_hop_dong_nhiem_vu_g0_t3_t4():
    nv = {n["ma"]: n for n in HD.NHIEM_VU["G0"]}
    assert "G0_TONG_HOP_BANG_CHUNG_<mã>.json" in nv["G0-T3"]["dau_ra"]
    assert "G0_KHOANG_TRONG_<mã>.json" in nv["G0-T4"]["dau_ra"]
    assert {"G0-T3", "G0-T4"} <= set(HD.KIEM_NHIEM_VU)


def test_kiem_may_g0_t3_doi_chieu_pmid_checkpoint(tmp_path):
    (tmp_path / "G0_checkpoint.json").write_text(json.dumps({"pubmed_results": {"all_pmids": PMIDS}}),
                                                 encoding="utf-8", newline="\n")
    p = tmp_path / GT.TEP_TONG_HOP.format(study=STUDY)
    p.write_text(json.dumps(_tong_hop_hop_le(), ensure_ascii=False), encoding="utf-8", newline="\n")
    assert HD.KIEM_NHIEM_VU["G0-T3"][1](tmp_path, STUDY) == []
    d = _tong_hop_hop_le()
    d["sang_loc"].pop()
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8", newline="\n")
    assert any("chưa sàng lọc" in x for x in HD.KIEM_NHIEM_VU["G0-T3"][1](tmp_path, STUDY))
    k = tmp_path / GT.TEP_KHOANG_TRONG.format(study=STUDY)
    k.write_text("[]", encoding="utf-8", newline="\n")
    assert HD.KIEM_NHIEM_VU["G0-T4"][1](tmp_path, STUDY)


def test_khoi_trach_nhiem_agent_hien_kiem_may():
    import sinh_tai_lieu_trach_nhiem as SL

    for van in (SL.khoi_agent("tong-quan-y-van"),
                (REPO_ROOT / ".claude/agents/tong-quan-y-van.md").read_text(encoding="utf-8")):
        dong = next(x for x in van.splitlines() if x.startswith("| `G0-T3`"))
        assert "kiểm máy cấp nhiệm vụ" in dong and "G0_TONG_HOP_BANG_CHUNG_<mã>.json" in dong
    dong = next(x for x in SL.khoi_agent("khoang-trong-nghien-cuu").splitlines() if x.startswith("| `G0-T4`"))
    assert "G0-AUTO-06 + kiểm máy cấp nhiệm vụ" in dong and "G0_KHOANG_TRONG_<mã>.json" in dong


# ── 5. StudySpec: khoảng trống do NGƯỜI viết thắng câu suy của máy ─────────────────────────────────────────

def test_studyspec_uu_tien_khoang_trong_nguoi_viet():
    meta = {"gate_params": {"G0": {}, "G1": {"knowledge_gap": "Khoảng trống PI viết"}}}
    cps = {"G0": {"research_gaps": ["Không thấy SR/MA trong PubMed"]}}
    assert RS.build_study_spec("S", cps, meta)["rationale"]["evidence_gap"] == "Khoảng trống PI viết"
    assert RS.build_study_spec("S", cps, {"gate_params": {}})["rationale"]["evidence_gap"] == \
        ["Không thấy SR/MA trong PubMed"]


# ── 6. Dựng lại A1 từ dữ liệu đã lưu — không tra lại PubMed, giữ nguyên tập PMID ───────────────────────────

def _de_tai(tmp_path) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    raw = {"sr_ma": [], "rct": [], "guideline": [], "recent": [],
           "observational": [{"pmid": p, "title": f"T {p}", "year": "2025", "journal": "J", "url": "u"}
                             for p in PMIDS],
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 3, "recent": 0}}
    cp = {"study": STUDY, "gate": "G0", "topic": "x", "base_query": "q",
          "pubmed_results": {"all_pmids": PMIDS, "total_found": 3},
          "research_gaps": ["Chưa có systematic review tổng hợp bằng chứng"],
          "registry_check": {"checked": True, "n_trials": 0, "n_active": 0, "trials": []}}
    (d / "G0_pubmed_raw.json").write_text(json.dumps(raw), encoding="utf-8", newline="\n")
    (d / "G0_checkpoint.json").write_text(json.dumps(cp), encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(json.dumps(META_GHIM), encoding="utf-8", newline="\n")
    (d / f"G0_A1_PICO_FINER_{STUDY}.md").write_text("A1 cũ\n", encoding="utf-8", newline="\n")
    return d


def test_dung_lai_a1_tu_du_lieu_da_luu(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    monkeypatch.setattr(G0, "_REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(G0, "guardrail_check_g0", lambda *_a, **_k: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(G0, "PubMedClient", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    ma = G0.dung_lai_a1(STUDY, d)
    assert ma in (GC.EXIT_OK, GC.EXIT_BLOCKED, GC.EXIT_GUARDRAIL_FAIL)
    a1 = (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")
    assert all(f"PMID: {p}" in a1 for p in PMIDS)
    assert list(d.glob(f"G0_A1_PICO_FINER_{STUDY}.bak-*.md")), "phải sao lưu A1 cũ"
    cp = json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8"))
    assert cp["pubmed_results"]["all_pmids"] == PMIDS, "dựng lại KHÔNG được đổi tập PMID"
    assert not any(g.startswith("Chưa có") for g in cp["research_gaps"])
    assert "cross_sectional" in cp["design_suggestion"] and cp.get("a1_dung_lai_luc")
    assert not Path(cp["artifacts"]["A1_markdown"]).is_absolute(), "checkpoint không được lộ đường dẫn tuyệt đối"


def test_dung_lai_a1_thieu_nen_thi_dung_khong_ghi(tmp_path):
    d = tmp_path / STUDY
    d.mkdir()
    assert G0.dung_lai_a1(STUDY, d) == GC.EXIT_BLOCKED
    assert list(d.iterdir()) == []


def test_cli_thieu_topic_ma_khong_dung_lai_thi_tu_choi(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "argv", ["run_g0_auto.py", "--study", STUDY, "--repo-root", str(tmp_path)])
    with pytest.raises(SystemExit) as e:
        G0.main()
    assert e.value.code == 2
    assert not (tmp_path / "exports").exists(), "thiếu --topic không được ghi checkpoint BLOCKED"
