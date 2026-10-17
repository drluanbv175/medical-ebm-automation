"""Sổ bằng chứng G1 (A2b) dùng lại sàng lọc G0-T3 + đường `--dung-lai-ho-tro` không tra PubMed — 17/10/2026.

Hoàn thiện G1 của C1a: sổ A2b là 36 dòng «[CẦN TRÍCH XUẤT]/[CẦN XÁC NHẬN NỘI DUNG]» sinh từ kết quả PubMed THÔ của G0,
kể cả bài G0-T3 đã sàng là lạc đề — đẩy lại cho người thật một việc agent G0 đã làm. Test chốt: ① bài có sàng lọc G0 ⇒
thiết kế + tóm tắt + trạng thái điền từ sàng lọc, RoB vẫn [CẦN]; ② bài lạc đề ⇒ ra khỏi bảng, vào mục riêng kèm lý
do; ③ không có tệp sàng lọc ⇒ giữ nhãn [CẦN] như cũ; ④ giới hạn/recall trỏ gói PRISMA-S khi có; ⑤ `--dung-lai-ho-tro`
không gọi PubMed và không sinh lại A2.
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
import g1_quality_gate as G1Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g1_auto as G1  # noqa: E402

STUDY = "S-G1SO"


def _de_tai(tmp_path: Path, *, sang_loc: bool = True, prisma: bool = False) -> Path:
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    cp0 = {"study": STUDY, "gate": "G0", "base_query": "q", "pubmed_results": {"all_pmids": ["11111111", "22222222"]},
           "danh_muc_doc_bo_sung": ["pmid:33333333", "doi:10.1/abc"], "research_gaps": ["khoảng trống"]}
    (d / "G0_checkpoint.json").write_text(json.dumps(cp0), encoding="utf-8", newline="\n")
    (d / "study_meta.json").write_text(json.dumps({"topic": "T", "gate_params": {"G1": {}}}), encoding="utf-8",
                                       newline="\n")
    (d / "G1_checkpoint.json").write_text(json.dumps({"design": {"primary": "Cắt ngang"}, "effect_size_samples": []}),
                                          encoding="utf-8", newline="\n")
    if sang_loc:
        th = {"schema": GT.SCHEMA_TONG_HOP,
              "sang_loc": [{"pmid": "11111111", "thiet_ke_that": "cắt ngang n=300", "lien_quan": "truc_tiep",
                            "tom_tat": "Hài lòng 80%"},
                           {"pmid": "22222222", "thiet_ke_that": "phẫu thuật", "lien_quan": "khong",
                            "tom_tat": "x", "ly_do": "khác chủ đề — phẫu thuật nhi"}],
              "nguon_bo_sung": [{"pmid": "33333333", "tieu_de": "Bài bổ sung", "thiet_ke_that": "cắt ngang",
                                 "lien_quan": "gian_tiep", "tom_tat": "Thời gian chờ", "cach_tim": "PubMed"},
                                {"doi": "10.1/ABC", "tieu_de": "Bài trong nước", "thiet_ke_that": "cắt ngang",
                                 "lien_quan": "truc_tiep", "tom_tat": "Hài lòng 70%", "cach_tim": "Crossref"}]}
        (d / GT.TEP_TONG_HOP.format(study=STUDY)).write_text(json.dumps(th, ensure_ascii=False), encoding="utf-8",
                                                             newline="\n")
    if prisma:
        (d / f"G0_TIM_BO_SUNG_PRISMA_S_{STUDY}.md").write_text("# PRISMA-S\n", encoding="utf-8", newline="\n")
    return d


def _so(d: Path) -> str:
    G1Q.build_supporting_artifacts(study=STUDY, topic="T", out_dir=d, design={"primary": "Cắt ngang"},
                                   g0_checkpoint=json.loads((d / "G0_checkpoint.json").read_text(encoding="utf-8")),
                                   effects=[], meta={"gate_params": {"G1": {}}}, generated_at="2026-10-17 10:00")
    return (d / f"G1_A2b_EVIDENCE_LEDGER_{STUDY}.md").read_text(encoding="utf-8")


def test_dong_co_sang_loc_lay_tu_g0(tmp_path):
    so = _so(_de_tai(tmp_path, prisma=True))
    dong = next(x for x in so.splitlines() if x.startswith("| PMID:11111111"))
    assert "cắt ngang n=300" in dong and "Hài lòng 80% (theo tóm tắt)" in dong
    assert "[CẦN THẨM ĐỊNH RoB — đọc toàn văn]" in dong and "Đã sàng ở G0-T3" in dong and "TRỰC TIẾP" in dong
    doi = next(x for x in so.splitlines() if x.startswith("| DOI:10.1/abc"))
    assert "Bài trong nước" in doi and "Hài lòng 70%" in doi, "DOI so khớp không phân biệt hoa thường"
    assert "Giới hạn truy xuất/recall: xem `G0_TIM_BO_SUNG_PRISMA_S_" in so


def test_bai_lac_de_ra_khoi_bang_vao_muc_rieng(tmp_path):
    so = _so(_de_tai(tmp_path))
    assert not any(x.startswith("| PMID:22222222") for x in so.splitlines())
    assert "## Đã sàng ở G0 — lạc đề (không vào sổ)\n- PMID:22222222 — khác chủ đề — phẫu thuật nhi" in so
    assert "Giới hạn truy xuất/recall: [CẦN XÁC NHẬN]" in so, "không có gói PRISMA-S thì giữ nhãn"


def test_khong_co_tep_sang_loc_thi_giu_nhan_cu(tmp_path):
    so = _so(_de_tai(tmp_path, sang_loc=False))
    dong = next(x for x in so.splitlines() if x.startswith("| PMID:11111111"))
    assert dong.count("[CẦN TRÍCH XUẤT]") == 2 and "[CẦN XÁC NHẬN NỘI DUNG]" in dong
    assert "Đã sàng ở G0" not in so


def test_dung_lai_ho_tro_khong_tra_pubmed_khong_sinh_lai_a2(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    a2 = d / f"G1_A2_PROTOCOL_DESIGN_{STUDY}.md"
    a2.write_text("A2 của PI\n", encoding="utf-8", newline="\n")
    monkeypatch.setattr(G1, "search_for_effect_sizes", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    monkeypatch.setattr(G1Q, "evaluate_study", lambda *_a, **_k: {"status": "X"})
    assert G1.dung_lai_ho_tro(STUDY, d) == GC.EXIT_OK
    assert a2.read_text(encoding="utf-8") == "A2 của PI\n"
    assert "Đã sàng ở G0-T3" in (d / f"G1_A2b_EVIDENCE_LEDGER_{STUDY}.md").read_text(encoding="utf-8")


def test_dung_lai_ho_tro_thieu_checkpoint_thi_dung(tmp_path):
    d = tmp_path / "exports" / STUDY
    d.mkdir(parents=True)
    assert G1.dung_lai_ho_tro(STUDY, d) == GC.EXIT_BLOCKED
    assert list(d.iterdir()) == []
