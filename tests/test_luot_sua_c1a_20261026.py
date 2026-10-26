# -*- coding: utf-8 -*-
"""Hồi quy 26/10/2026 — bốn lỗi máy lộ ra khi thi công lượt sửa C1a (phương án A: CV cỡ chùm 0,14) và diễn tập đường PI.

1. G10-AUTO-03 (gói TRƯỚC dữ liệu): checkpoint G5 dự thảo (có từ 24/10) sinh trước G1–G4 vừa chạy lại ⇒ «G5 cũ» chặn
   gói trình Hội đồng Y đức, trong khi gói không mang tài liệu G5–G9 và G5 chỉ chạy lại được sau khi G4 KÝ (vòng chặn).
2. A4 của G3: bảng độ nhạy in «DE = 1.39 (= 1+(m−1)×ICC…)» — con số là công thức Eldridge có CV, nhãn là công thức
   cụm đều.
3. A2 của G1: «hệ số thiết kế 1.38784» — in thô số G3 lưu đủ chữ số.
4. Hội đồng: «không áp dụng (thiết kế can thiệp (RCT))» đọc như thể đề tài cắt ngang LÀ RCT.
Ngoại tuyến, dữ liệu tổng hợp.
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "tools", ROOT / "tests"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cong_song as CS  # noqa: E402
import g10_quality_gate as G10Q  # noqa: E402
import hoi_dong_cong as HD  # noqa: E402
import run_g1_auto as G1A  # noqa: E402
import run_g3_auto as R3  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402

# ── 1. Độ tươi của gói trước dữ liệu ─────────────────────────────────────────────────────────────────────────────────

def test_loc_do_tuoi_truoc_du_lieu_bo_g5_g9_giu_g0_g4():
    van_de = [
        {"gate": "G5", "kind": "stale", "offending_upstream": ["G1", "G2", "G3"]},
        {"gate": "G10", "kind": "orphan_downstream", "offending_upstream": ["G6", "G7", "G8", "G9"]},
        {"gate": "G10", "kind": "stale", "offending_upstream": ["G5"]},
        {"gate": "G3", "kind": "stale", "offending_upstream": ["G1"]},
        {"gate": "G10", "kind": "stale", "offending_upstream": ["G3", "G5"]},
        {"gate": "G4", "kind": "orphan_downstream", "offending_upstream": ["G3"]},
    ]
    con = G10Q.loc_do_tuoi_truoc_du_lieu(van_de)
    assert con == [van_de[3], van_de[4], van_de[5]], "vấn đề của G0–G4, và của G10 do G0–G4, vẫn chặn"
    assert G10Q.loc_do_tuoi_truoc_du_lieu([]) == []


def _nap_g10_hoan_thien():
    sp = importlib.util.spec_from_file_location("_g10_hoan_thien_luot_sua",
                                                ROOT / "tests" / "test_g10_hoan_thien_20261005.py")
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def _lui_moc(tep: Path, giay: float) -> None:
    t = time.time() - giay
    os.utime(tep, (t, t))


def test_goi_truoc_irb_khong_bi_chan_boi_g5_du_thao_cu_nhung_van_chan_g3_cu(tmp_path, monkeypatch):
    H = _nap_g10_hoan_thien()
    study, out, goc = H._de_tai_truoc_irb(tmp_path, monkeypatch)
    assert H._cham10(study, out, goc)["status"] == G10Q.STATUS_READY
    g5 = out / "G5_checkpoint.json"  # G5 dự thảo có từ trước (như C1a 24/10), sinh TRƯỚC G1–G4
    g5.write_text(json.dumps({"gate": "G5", "status": "DRAFT_READY_NEEDS_REAL_DATA"}), encoding="utf-8", newline="\n")
    _lui_moc(g5, 86_400)
    CS.xoa_dem()
    bao = H._cham10(study, out, goc)
    assert bao["status"] == G10Q.STATUS_READY, H._chua_dat(bao)
    assert H._ck(bao, "G10-AUTO-03")["status"] == "PASS"
    # Đối chứng: một cổng G0–G4 cũ hơn thượng nguồn (G3 trước G1) vẫn chặn gói.
    _lui_moc(out / "G3_checkpoint.json", 2 * 86_400)
    CS.xoa_dem()
    a03 = H._ck(H._cham10(study, out, goc), "G10-AUTO-03")
    assert a03["status"] == "BLOCK" and "'gate': 'G3'" in a03["evidence"], a03


# ── 2. Nhãn công thức DE trong bảng độ nhạy của G3 ──────────────────────────────────────────────────────────────────

def _chay_g3(tmp_path, monkeypatch, study, argv):
    monkeypatch.setattr(R3, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True)
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *argv])
    with contextlib.redirect_stdout(io.StringIO()):
        R3.main()
    a4 = (d / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
    return next(dong for dong in a4.splitlines() if dong.startswith("Bảng: tỷ lệ ước lượng p"))


_ARGV = ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--cluster-size", "20", "--dropout", "0.15"]


def test_bang_do_nhay_ghi_dung_cong_thuc_de(tmp_path, monkeypatch):
    co_cv = _chay_g3(tmp_path / "a", monkeypatch, "G3-CV", _ARGV + ["--cluster-cv", "0.14"])
    assert "DE = 1.39 (= 1+((CV²+1)×m−1)×ICC, CV = 0.14, m = 20, ICC = 0.02)" in co_cv, co_cv
    deu = _chay_g3(tmp_path / "b", monkeypatch, "G3-DEU", _ARGV)
    assert "DE = 1.38 (= 1+(m−1)×ICC, m = 20, ICC = 0.02)" in deu, deu


# ── 3. A2 của G1 in DE làm tròn ─────────────────────────────────────────────────────────────────────────────────────

def test_cau_co_mau_g1_lam_tron_he_so_thiet_ke(tmp_path):
    (tmp_path / "G3_checkpoint.json").write_text(json.dumps({"n_adjusted": 630, "confirmed_n": 1000,
                                                             "design_effect": 1.38784}), encoding="utf-8",
                                                  newline="\n")
    cau = G1A._cau_co_mau_g3(tmp_path)
    assert "hệ số thiết kế 1.39" in cau and "1.38784" not in cau, cau


# ── 4. Câu «không áp dụng» của hội đồng ─────────────────────────────────────────────────────────────────────────────

def test_ly_do_khong_ap_dung_noi_ro_pham_vi_nhiem_vu(tmp_path):
    study = "HD-CAT-NGANG"
    out = tmp_path / "exports" / study
    dung_g0_g1_da_chot(out, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True)
    CS.xoa_dem()
    hs = HD.ho_so_cong(study, "G2", out)
    t2 = next(n for n in hs["nhiem_vu"] if n["ma"] == "G2-T2")
    assert t2["tinh_trang"] == "khong_ap_dung"
    assert t2["ly_do"].startswith("không áp dụng — nhiệm vụ chỉ dành cho "), t2["ly_do"]
    assert "(thiết kế can thiệp" not in t2["ly_do"].split("—")[0]
