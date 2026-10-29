"""Trục ① của kiểm chi tiết theo MỤC ĐÍCH phát hành G10 — 29/10/2026.

Lỗi đã đo trên C1a: gói ETHICS_SUBMISSION (chỉ dựa G0–G4) vẫn bị tô vàng «MỒ CÔI (thượng nguồn thiếu: G6, G7, G8,
G9)» và xếp vào việc của người thật. Test chốt: gói trước dữ liệu ⇒ bỏ vấn đề của G10 mà nguyên nhân CHỈ nằm ở G5–G9,
giữ vấn đề của G10 do G0–G4 và giữ vấn đề của chính G5–G9; mục đích khác/không đọc được ⇒ giữ nguyên.
Ngoại tuyến, dữ liệu giả.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (str(ROOT / "tools"), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import kiem_chi_tiet_he_nghien_cuu as KCT  # noqa: E402

MO_COI = {"gate": "G10", "kind": "orphan_downstream", "reason": "thiếu G6–G9",
          "offending_upstream": ["G6", "G7", "G8", "G9"]}
G10_CU = {"gate": "G10", "kind": "stale", "reason": "cũ hơn G3", "offending_upstream": ["G3"]}
G5_CU = {"gate": "G5", "kind": "stale", "reason": "cũ hơn G1", "offending_upstream": ["G1"]}


def _tuoi():
    return {"issues": [MO_COI, G10_CU, G5_CU], "fresh": False}


def _readiness(tmp_path: Path, purpose) -> Path:
    rd = {"status": "x", "release": {"purpose": purpose}} if purpose is not None else {"status": "x"}
    (tmp_path / "G10_RELEASE_READINESS.json").write_text(json.dumps(rd), encoding="utf-8", newline="\n")
    return tmp_path


def test_goi_truoc_du_lieu_bo_mo_coi_do_g5_g9(tmp_path):
    for md in ("ETHICS_SUBMISSION", "registry_update"):
        kq = KCT._do_tuoi_theo_muc_dich_g10(_tuoi(), _readiness(tmp_path, md))
        assert MO_COI not in kq["issues"], md
        assert G10_CU in kq["issues"] and G5_CU in kq["issues"], "giữ vấn đề do G0–G4 và vấn đề của G5"


def test_muc_dich_khac_hoac_khong_doc_duoc_giu_nguyen(tmp_path):
    assert KCT._do_tuoi_theo_muc_dich_g10(_tuoi(), _readiness(tmp_path, "JOURNAL_SUBMISSION"))["issues"] == \
        [MO_COI, G10_CU, G5_CU]
    assert KCT._do_tuoi_theo_muc_dich_g10(_tuoi(), _readiness(tmp_path, None))["issues"] == [MO_COI, G10_CU, G5_CU]
    trong = tmp_path / "khong_co"
    trong.mkdir()
    assert KCT._do_tuoi_theo_muc_dich_g10(_tuoi(), trong)["issues"] == [MO_COI, G10_CU, G5_CU]
    (trong / "G10_RELEASE_READINESS.json").write_text("{hỏng", encoding="utf-8", newline="\n")
    assert KCT._do_tuoi_theo_muc_dich_g10(_tuoi(), trong)["issues"] == [MO_COI, G10_CU, G5_CU]
