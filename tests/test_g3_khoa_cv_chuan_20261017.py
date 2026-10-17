"""Khoá CV cỡ cụm CHUẨN trong study_meta là `cluster_size_cv` (PI khai 14/10, G3-AUTO-12 đọc) — 17/10/2026.

Bản 16/10 (#147, F1) cho run_g3_auto đọc/ghim `cluster_cv` ⇒ CV PI đã chốt cho C1a (1,0) bị bỏ qua, G3 vẫn ghi DE 1,38 /
N 626 trong khi đề cương nộp ghi 1,78 / 808 (K5 của kiem_de_cuong_nop_hoi_dong bắt được) và cổng không thấy lệch.
"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g3_quality_gate as G3Q  # noqa: E402
import gate_contract as GC  # noqa: E402
import run_g3_auto as R  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402

ARGV_C1A = ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--cluster-size", "20", "--dropout", "0.15"]
_META = {"icc_source": "Adams 2004, PMID 15485730", "n_clusters": 50}


def _chay(tmp_path, monkeypatch, study, argv, meta_g3):
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True,
                       them_meta={"G3": meta_g3})
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    with contextlib.redirect_stdout(io.StringIO()):
        R.main()
    return d, json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8"))


def _a12(bao_cao):
    return next(c for c in bao_cao["automatic_criteria"] if c["id"] == "G3-AUTO-12")


def test_g3_doc_cv_pi_da_khai_o_khoa_chuan(tmp_path, monkeypatch):
    meta = {**_META, "cluster_size_cv": 1.0, "unequal_cluster_adjustment": "Eldridge 2006 (doi:10.1093/ije/dyl129)"}
    _d, cp = _chay(tmp_path, monkeypatch, "S-CV-CHUAN", [*ARGV_C1A, "--confirmed-n", "1000"], meta)
    assert cp["cluster_cv"] == 1.0
    assert cp["design_effect"] == pytest.approx(1.78)
    assert cp["n_adjusted"] == 808, "385 × 1,78 → 686 ÷ 0,85 → 808 như đề cương nộp"


def test_cv_tu_dong_lenh_ghim_vao_khoa_chuan(tmp_path, monkeypatch):
    d, cp = _chay(tmp_path, monkeypatch, "S-CV-CLI", [*ARGV_C1A, "--cluster-cv", "0.5"], dict(_META))
    g3 = GC.load_study_meta(d)["gate_params"]["G3"]
    assert g3.get("cluster_size_cv") == 0.5 and "cluster_cv" not in g3
    assert cp["design_effect"] == pytest.approx(1 + ((0.5 ** 2 + 1) * 20 - 1) * 0.02)


def test_cong_bat_de_cu_khi_pi_khai_cv_sau(tmp_path, monkeypatch):
    """G3 chạy khi chưa khai CV (DE 1,38), sau đó PI khai cluster_size_cv = 1,0 ⇒ cổng phải thấy DE lệch, không PASS."""
    d, _cp = _chay(tmp_path, monkeypatch, "S-CV-SAU", [*ARGV_C1A, "--confirmed-n", "1000"], dict(_META))
    meta_p = d / "study_meta.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8"))
    meta["gate_params"]["G3"].update({"cluster_size_cv": 1.0, "unequal_cluster_adjustment": "Eldridge 2006"})
    meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8", newline="\n")
    CS.xoa_dem()
    a12 = _a12(G3Q.evaluate_study("S-CV-SAU", d, write=False))
    assert a12["status"] != "PASS" and "1.78" in a12["evidence"], a12


def test_cong_bat_cv_lech_giua_checkpoint_va_meta(tmp_path, monkeypatch):
    meta = {**_META, "cluster_size_cv": 1.0, "unequal_cluster_adjustment": "Eldridge 2006"}
    argv = [*ARGV_C1A, "--cluster-cv", "0.5", "--confirmed-n", "1000"]
    d, _cp = _chay(tmp_path, monkeypatch, "S-CV-LECH", argv, meta)
    CS.xoa_dem()
    a12 = _a12(G3Q.evaluate_study("S-CV-LECH", d, write=False))
    assert a12["status"] != "PASS" and "CV cỡ chùm lệch: checkpoint 0.5 ≠ study_meta 1" in a12["evidence"], a12
