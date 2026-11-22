"""G3: RIS của tổng quan gộp tính lại từ tham số có cấu trúc; thiết kế không dùng lực mẫu không ghi số mặc định máy.

Đo thật 22/11/2026: checkpoint G3 tổng quan gộp ghi lực 0,8 · p0 0,3 (MẶC ĐỊNH MÁY) trong khi đề cương và lời chốt của
thống kê viên ghi lực 90% · tỷ lệ biến cố nhóm chứng 3%; tiêu chí G3-AUTO-07 «PASS» nhờ chính số mặc định đó."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import g3_quality_gate as G3Q  # noqa: E402
import run_g3_auto as G3  # noqa: E402


def test_ris_theo_cong_thuc_wetterslev():
    # p_chứng 3%, RRR 25%, α 0,05, lực 90%, D² 25%: 4·(1,959964+1,281552)²·0,02625·0,97375/0,0075² ÷ 0,75 ≈ 25 465,3
    assert G3.tinh_ris(0.03, 0.25, 0.05, 0.90, 0.25) == 25466
    assert G3.tinh_ris(0.03, 0.25, 0.05, 0.90, 0.0) < G3.tinh_ris(0.03, 0.25, 0.05, 0.90, 0.25)   # D² làm tăng RIS
    assert G3.tinh_ris(0.03, 0.25, 0.05, 0.80, 0.25) < G3.tinh_ris(0.03, 0.25, 0.05, 0.90, 0.25)  # lực cao ⇒ RIS lớn


@pytest.mark.parametrize("sai", [(0.0, 0.25, 0.25), (0.03, 1.0, 0.25), (0.03, 0.25, 1.0)])
def test_ris_tham_so_ngoai_mien_bi_tu_choi(sai):
    with pytest.raises(G3.InvalidEffectSizeError):
        G3.tinh_ris(sai[0], sai[1], 0.05, 0.90, sai[2])


def test_so_kieu_viet_nam():
    assert G3._so_vn(25466) == "25.466" and G3._so_vn(0.05, 2) == "0,05"


def _cp(design, power):
    return {"gate": "G3", "design_code": design, "alpha": 0.05, "power": power, "n_total": 0, "confirmed_n": 25462}


def _g3_auto_07(design, power, tmp_path):
    kq = G3Q.evaluate_g3_quality(study="ZZTEST", checkpoint=_cp(design, power), artifact_path=tmp_path / "khong.md",
                                 g0_checkpoint={}, g1_checkpoint={}, meta={})
    return next(c for c in kq["automatic_criteria"] if c["id"] == "G3-AUTO-07")


@pytest.mark.parametrize("design", sorted(G3Q.N_NOT_APPLICABLE_DESIGNS))
def test_g3_auto_07_khong_ap_dung_khi_khong_dung_luc_mau(design, tmp_path):
    tc = _g3_auto_07(design, None, tmp_path)
    assert tc["status"] == "PASS" and "không áp dụng" in tc["evidence"]


def test_g3_auto_07_van_doi_luc_mau_o_thiet_ke_thuong(tmp_path):
    tc = _g3_auto_07("rct", None, tmp_path)
    assert tc["status"] == "REVIEW" and "thiếu power" in tc["evidence"]


def test_g3_auto_07_tong_quan_gop_co_ris_van_kiem_luc(tmp_path):
    assert _g3_auto_07("sr_ma", 0.70, tmp_path)["status"] == "REVIEW"      # lực RIS dưới quy ước vẫn bị nêu


# ── đầu–cuối: run_g3_auto THẬT trên chuỗi G0→G1 đã chốt (tests/_chuoi_da_chot.py) ──
sys.path.insert(0, str(ROOT / "tests"))
from _chuoi_da_chot import dung_g0_g3_da_chot  # noqa: E402


def test_dinh_tinh_khong_ghi_luc_mau_mac_dinh(tmp_path):
    cp = dung_g0_g3_da_chot(tmp_path / "exports" / "E2E-QUAL", "E2E-QUAL", thiet_ke="qualitative")
    assert cp["power"] is None and cp["p0"] is None
    assert "power" not in cp["tham_so_mac_dinh_may"] and "p0" not in cp["tham_so_mac_dinh_may"]
    assert cp["nguon_tham_so"]["power"].startswith("không áp dụng")


_RIS = {"p0": 0.03, "power": 0.90, "ris_giam_nguy_co_tuong_doi": 0.25, "ris_d2": 0.25}


def test_tong_quan_gop_tinh_lai_ris_tu_tham_so_ghim(tmp_path):
    cp = dung_g0_g3_da_chot(tmp_path / "exports" / "E2E-SRMA", "E2E-SRMA", thiet_ke="sr_ma",
                            g3_argv=["--confirmed-n", "25462"], them_meta={"G3": _RIS})
    assert cp["ris"]["ris"] == 25466 and cp["ris"]["khop"] is True
    assert cp["power"] == 0.90 and cp["p0"] == 0.03
    assert "Wetterslev" in cp["formula_used"] and "25.466" in cp["formula_used"] and "khớp" in cp["formula_used"]


def test_tong_quan_gop_n_chot_lech_ris_thi_bao_lech(tmp_path):
    cp = dung_g0_g3_da_chot(tmp_path / "exports" / "E2E-SRMA2", "E2E-SRMA2", thiet_ke="sr_ma",
                            g3_argv=["--confirmed-n", "15"], them_meta={"G3": _RIS})
    assert cp["ris"]["khop"] is False and "LỆCH" in cp["formula_used"]


def test_bang_khung_co_mau_g10_khop_g3():
    import run_g10_assemble as R10
    assert R10._KHUNG_CO_MAU_KHONG_DUNG_LUC == G3.KHUNG_CO_MAU_THAY_THE
    assert set(R10._KHUNG_CO_MAU_KHONG_DUNG_LUC) == G3Q.N_NOT_APPLICABLE_DESIGNS


@pytest.mark.parametrize("design, cum", [("sr_ma", "RIS"), ("prediction", "Riley"), ("qualitative", "Bão hoà")])
def test_g10_khoi_co_mau_khong_in_luc_mac_dinh_hay_dau_hoi(design, cum):
    import run_g10_assemble as R10
    cps = {"G1": {}, "G3": {"design_code": design, "alpha": 0.05, "power": None, "n_total": 0, "n_adjusted": 0,
                           "confirmed_n": 120, "formula_used": ""}}
    meta = {"gate_params": {"G3": {"confirmed_n_method": "thống kê viên khai theo khung của thiết kế"}}}
    khoi = R10.sec_comau(cps, meta)
    assert cum in khoi and "Cỡ mẫu đã chốt: **120**" in khoi
    assert "lực mẫu (power) =" not in khoi and "?" not in khoi and "Công thức áp dụng" not in khoi


def test_g10_khoi_co_mau_thiet_ke_thuong_giu_nguyen():
    import run_g10_assemble as R10
    cps = {"G1": {}, "G3": {"design_code": "rct", "alpha": 0.05, "power": 0.8, "n_total": 200, "n_adjusted": 222,
                           "n_per_group": 100, "dropout": 0.1, "formula_used": "Hai tỷ lệ"}}
    khoi = R10.sec_comau(cps, {"gate_params": {"G3": {}}})
    assert "lực mẫu (power) = 0.8" in khoi and "Công thức áp dụng (tự động từ G3):** Hai tỷ lệ" in khoi
