"""A1 của G0 trình bày đúng cái PI ĐÃ CHỐT — 17/10/2026 (hội đồng G0 C1a: G0-T1 RQ5/RQ8, G0-T4 RQ8).

Trước đây: PHẦN 1/1b luôn là khung trống (người đọc A1/.docx không thấy câu hỏi đã chốt); PHẦN 6 toàn ô ☐ dù đã ghi
đủ; ô FINER-I/đối chiếu đăng ký nói «nguy cơ trùng đề tài thật» dù PI đã đánh giá không chồng lấn; checkpoint PASS vẫn
giữ câu «còn chờ bác sĩ/PI: …».
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT / "tests")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g0_quality_gate as G0Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g0_auto as G0  # noqa: E402

STUDY = "S-G0CHOT"
NEN = ["34445940", "36439278"]
G0_DA_GHI = {"population": "Người bệnh ngoại trú đã khám xong tại Khoa C1a", "intervention": "Thời gian chờ (HIS)",
             "comparison": "Thời gian chờ ngắn hơn", "primary_outcome": "Mức hài lòng chung G1 (Likert 1–5)",
             "primary_outcome_measure": "Câu G1 của phiếu", "primary_outcome_timepoint": "Sau khi khám xong",
             "question_type": "descriptive", "test_type": "descriptive",
             "hypothesis_h0": "OR chung = 1", "hypothesis_h1": "OR chung ≠ 1", "expected_direction": "giảm",
             "pico_confirmed": True, "reviewed_by_role": "PI", "reviewed_at": "2026-10-14T19:17:12+07:00",
             "dau_van_tay_chot": "4678a3407d3ccd57",
             "registry_overlap_assessment": "Không chồng lấn: 3 hồ sơ đang tuyển khác chủ đề (PI đọc 14/10/2026)."}


def _de_tai(tmp_path: Path, g0: dict) -> Path:
    d = tmp_path / STUDY
    d.mkdir()
    raw = {"sr_ma": [], "rct": [], "guideline": [], "recent": [],
           "observational": [{"pmid": p, "title": f"T {p}", "year": "2025", "journal": "J", "url": "u"} for p in NEN],
           "true_counts": {"sr_ma": 0, "rct": 0, "guideline": 0, "observational": 2, "recent": 0}}
    cp = {"study": STUDY, "gate": "G0", "topic": "x", "base_query": "q",
          "pubmed_results": {"all_pmids": NEN, "total_found": 2},
          "registry_check": {"checked": True, "n_trials": 3, "n_active": 3, "trials": []}}
    meta = {"design_code": "cross_sectional", "gate_params": {"G0": g0, "G1": {"design": "cross_sectional"}}}
    for ten, v in (("G0_pubmed_raw.json", raw), ("G0_checkpoint.json", cp), ("study_meta.json", meta)):
        (d / ten).write_text(json.dumps(v, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def _dung_lai(tmp_path, monkeypatch, g0: dict) -> str:
    d = _de_tai(tmp_path, g0)
    monkeypatch.setattr(G0, "_REPO_ROOT", tmp_path.parent)
    monkeypatch.setattr(G0, "guardrail_check_g0", lambda *_a, **_k: {"passed": True, "errors": [], "warnings": []})
    monkeypatch.setattr(G0, "PubMedClient", None)  # gọi PubMed ⇒ TypeError ⇒ test đỏ
    assert G0.dung_lai_a1(STUDY, d) in (GC.EXIT_OK, GC.EXIT_BLOCKED, GC.EXIT_GUARDRAIL_FAIL)
    return (d / f"G0_A1_PICO_FINER_{STUDY}.md").read_text(encoding="utf-8")


def test_a1_trinh_bay_pico_da_chot_va_o_tick(tmp_path, monkeypatch):
    a1 = _dung_lai(tmp_path, monkeypatch, G0_DA_GHI)
    phan1 = a1[a1.index("## PHẦN 1 —"):a1.index("## PHẦN 1b")]
    assert "**Đã ghi trong `study_meta.json → gate_params.G0`** — PI chốt lúc 2026-10-14T19:17:12+07:00" in phan1
    assert "- **P — Quần thể:** Người bệnh ngoại trú đã khám xong tại Khoa C1a" in phan1
    assert "- **H1:** OR chung ≠ 1" in phan1
    phan6 = a1[a1.index("## PHẦN 6"):]
    assert "☑ PICO/PECO 4 thành phần" in phan6 and "☑ Chốt PICO (vai trò" in phan6
    assert "☐ Tự tra WHO ICTRP" in phan6, "chưa ghi ICTRP thì không được đánh dấu"
    assert "PI đã chốt G0 lúc 2026-10-14T19:17:12+07:00" in phan6
    assert "PI ĐÃ ĐÁNH GIÁ chồng lấn (gate_params.G0.registry_overlap_assessment): Không chồng lấn" in a1


def test_chua_ghi_gi_thi_giu_khung_cu(tmp_path, monkeypatch):
    a1 = _dung_lai(tmp_path, monkeypatch, {})
    assert "Đã ghi trong `study_meta.json → gate_params.G0`" not in a1
    assert "☐ PICO/PECO 4 thành phần" in a1 and "PI đã chốt G0 lúc" not in a1
    assert "PI ĐÃ ĐÁNH GIÁ chồng lấn" not in a1


def test_nhan_can_khong_tinh_la_da_ghi():
    assert G0._o_tick({"population": "[CẦN BÁC SĨ VIẾT]"}, "population") == "☐"
    assert "P — Quần thể" not in G0._khoi_pico_da_chot({"population": "[CẦN BÁC SĨ VIẾT]", "intervention": "x"})


def test_thong_diep_needs_input_da_go_khi_pass():
    luc = "2026-10-14T19:20:00"
    assert G0Q._da_go("còn chờ bác sĩ/PI: G0-HUMAN-07", luc).startswith(f"ĐÃ GỠ ({luc}) — cổng đã PASS_G0_CONFIRMED")
    da = G0Q._da_go("còn chờ bác sĩ/PI: G0-HUMAN-07", luc)
    assert G0Q._da_go(da, "khác") == da, "không gắn tiền tố hai lần"
