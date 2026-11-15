"""Chạy G2 không được làm mất xác nhận G1 của chủ nhiệm (15/11/2026).

Kiểm toàn hệ: chạy `run_g2_auto` cho BTM (chưa ghim `study_meta.design_code`) ⇒ G2 gieo khoá đó ⇒ dấu vân tay quyết
định G1 (`g1_quality_gate.dau_van_tay_g1`) đổi ⇒ G1 PASS → cần xem (G1-HUMAN-08), G3 → G3-AUTO-01, G4 → G4-AUTO-12, dù
thiết kế không đổi. Mỗi test khoá MỘT hành vi.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import g1_quality_gate as G1Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g2_auto as G2  # noqa: E402

DESIGN = {"internal_code": "cross_sectional"}


def _de_tai(tmp_path: Path, meta: dict) -> Path:
    d = tmp_path / "exports" / "ZZTEST-G2-DESIGN-20261115"
    d.mkdir(parents=True)
    (d / "study_meta.json").write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    return d


def test_hat_giong_g2_khong_co_design_code():
    assert "design_code" not in G2.hat_giong_meta_g2("Chủ đề")


def test_gieo_meta_g2_giu_nguyen_dau_van_tay_g1(tmp_path):
    meta = {"title": "Tên chính thức", "gate_params": {"G1": {"design": "cross_sectional", "population": "Người lớn"}}}
    d = _de_tai(tmp_path, meta)
    truoc = G1Q.dau_van_tay_g1(meta, DESIGN)
    sau_meta = GC.ensure_study_meta(d, seed=G2.hat_giong_meta_g2("Chủ đề G0"))
    assert "design_code" not in sau_meta
    assert sau_meta["title"] == "Tên chính thức"  # chỉ điền chỗ trống
    assert G1Q.dau_van_tay_g1(sau_meta, DESIGN) == truoc
