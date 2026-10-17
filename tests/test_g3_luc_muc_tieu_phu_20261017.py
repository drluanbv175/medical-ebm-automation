"""Lực cho MỤC TIÊU PHỤ (hồi quy logistic thứ tự — Whitehead 1993) ở G3 A4 PHẦN 2c và SAP §12 — 17/10/2026.

Hội đồng G0 C1a (DP-G0-1, biên bản G0-TB-20261017T100650-107f4acb): đề cương nộp §4.4.1 Bảng 4.2 đã tính OR nhỏ nhất
phát hiện được cho Mục tiêu 2, nhưng G3 A4 không có phép tính này và SAP §12 vẫn ghi «Power: không dùng»; phép tính
cũng chưa hiệu chỉnh gom cụm. Các test dưới đây khoá: (1) công thức tái lập ĐÚNG Bảng 4.2; (2) cột thận trọng chia DE;
(3) mục này KHÔNG đổi N, KHÔNG đổi dấu vân tay chốt G3; (4) SAP §12 in cùng câu mà không làm bộ chấm G4 đọc ra
«Power: N%» sai khung cho thiết kế theo độ chính xác.
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
import g4_quality_gate as G4Q  # noqa: E402
import run_g3_auto as R  # noqa: E402
import run_g4_auto as G4  # noqa: E402
from _chuoi_da_chot import dung_g0_g1_da_chot  # noqa: E402

PHAN_BO = {
    "Lệch về phía hài lòng mạnh": [0.01, 0.03, 0.11, 0.40, 0.45],
    "Lệch vừa": [0.02, 0.05, 0.18, 0.45, 0.30],
    "Lệch nhẹ": [0.03, 0.07, 0.25, 0.42, 0.23],
}
LUC_PHU = {
    "muc_tieu": "Mục tiêu 2", "ket_cuc": "G1", "phoi_nhiem": "thời gian chờ", "don_vi": "phút", "buoc": 15,
    "sd_gia_dinh": [20, 30, 40], "phan_bo_ket_cuc": PHAN_BO, "r2": 0.20,
    "nguon": "Đề cương nộp Hội đồng §4.4.1 Bảng 4.2 (giả định)",
}
ARGV_C1A = ["--prevalence", "0.5", "--precision", "0.05", "--icc", "0.02", "--cluster-size", "20", "--dropout", "0.15",
            "--confirmed-n", "1000"]
META_G3 = {"icc_source": "Adams 2004, PMID 15485730", "n_clusters": 50, "cluster_size_cv": 1.0,
           "unequal_cluster_adjustment": "Eldridge 2006 (doi:10.1093/ije/dyl129)"}


@pytest.mark.parametrize(("ten", "ky_vong"), [
    ("Lệch về phía hài lòng mạnh", (1.150, 1.098, 1.073)),
    ("Lệch vừa", (1.147, 1.096, 1.071)),
    ("Lệch nhẹ", (1.145, 1.095, 1.070)),
])
def test_whitehead_tai_lap_dung_bang_4_2_de_cuong(ten, ky_vong):
    tinh = tuple(round(R.or_nho_nhat_thu_bac(1000, PHAN_BO[ten], sd, 15, 0.20), 3) for sd in (20, 30, 40))
    assert tinh == ky_vong


def test_cot_than_trong_chia_de_va_tru_phieu_hong():
    kq = R.tinh_luc_muc_tieu_phu(LUC_PHU, 1000, 0.15, 1.78, 0.05, 0.80)
    assert kq["n_phan_tich"] == 850 and kq["n_hieu_dung"] == pytest.approx(850 / 1.78, abs=0.1)
    assert all(d["or_hieu_dung"] > d["or_danh_nghia"] for d in kq["bang"])
    hang = next(d for d in kq["bang"] if d["phan_bo"] == "Lệch vừa" and d["sd"] == 30)
    assert hang["or_hieu_dung"] == pytest.approx(R.or_nho_nhat_thu_bac(850 / 1.78, PHAN_BO["Lệch vừa"], 30, 15, 0.2),
                                                 abs=1e-3)
    # Không cụm, không bỏ cuộc ⇒ hai cột trùng nhau.
    kq1 = R.tinh_luc_muc_tieu_phu(LUC_PHU, 1000, 0.0, None, 0.05, 0.80)
    assert all(d["or_hieu_dung"] == d["or_danh_nghia"] for d in kq1["bang"])
    lo, hi = kq["khoang_or_hieu_dung"]
    assert kq["khoang_or_chieu_giam_hieu_dung"] == [round(1 / hi, 3), round(1 / lo, 3)]


@pytest.mark.parametrize("cfg", [
    {**LUC_PHU, "phan_bo_ket_cuc": {"x": [0.5, 0.2]}},  # tổng ≠ 1
    {**LUC_PHU, "sd_gia_dinh": []},
    {**LUC_PHU, "r2": 1.0},
    "không phải đối tượng",
])
def test_khai_bao_sai_bao_loi_khong_doan(cfg):
    kq = R.tinh_luc_muc_tieu_phu(cfg, 1000, 0.15, 1.78, 0.05, 0.80)
    assert kq.get("loi")
    assert R.dong_luc_muc_tieu_phu(kq) is None
    assert any("[CẦN SỬA khai báo" in d for d in R._phan_luc_muc_tieu_phu(kq))


def _chay_g3(tmp_path, monkeypatch, study, meta_g3):
    monkeypatch.setattr(R, "BASE", tmp_path)
    d = tmp_path / "exports" / study
    dung_g0_g1_da_chot(d, study, thiet_ke="cross_sectional", mau_hieu_qua=[], chot_g1=True,
                       them_meta={"G3": meta_g3})
    CS.xoa_dem()
    monkeypatch.setattr(sys, "argv", ["run_g3_auto.py", "--study", study, *ARGV_C1A])
    with contextlib.redirect_stdout(io.StringIO()):
        R.main()
    cp = json.loads((d / "G3_checkpoint.json").read_text(encoding="utf-8"))
    a4 = (d / f"G3_A4_SAMPLE_SIZE_{study}.md").read_text(encoding="utf-8")
    return d, cp, a4


def test_dau_cuoi_g3_khai_luc_phu_khong_doi_n_khong_doi_dau_van_tay(tmp_path, monkeypatch):
    _d0, cp0, a40 = _chay_g3(tmp_path / "khong", monkeypatch, "S-KHONG", dict(META_G3))
    _d1, cp1, a41 = _chay_g3(tmp_path / "co", monkeypatch, "S-CO", {**META_G3, "luc_muc_tieu_phu": LUC_PHU})
    assert "PHẦN 2c" not in a40 and "luc_muc_tieu_phu" not in cp0
    assert "## PHẦN 2c — LỰC CHO MỤC TIÊU PHỤ" in a41
    assert a41.index("PHẦN 2c") < a41.index("PHÂN TÍCH ĐỘ NHẠY"), "bảng độ nhạy vẫn đọc được sau mục mới"
    khoi_de_cuong = a41[a41.index("PHẦN 4"):a41.index("## PHẦN 5")]
    assert "Lực cho Mục tiêu 2 (hồi quy logistic thứ tự" in khoi_de_cuong
    kq = cp1["luc_muc_tieu_phu"]
    assert kq["n_danh_nghia"] == 1000 and kq["design_effect"] == pytest.approx(1.78)
    # Không đổi N và không đổi dấu vân tay PI chốt ở G3.
    assert (cp1["n_adjusted"], cp1["confirmed_n"]) == (cp0["n_adjusted"], cp0["confirmed_n"]) == (808, 1000)
    assert G3Q.dau_van_tay_g3(cp1) == G3Q.dau_van_tay_g3(cp0)
    assert "luc_muc_tieu_phu" not in G3Q.KHOA_DAU_VAN_TAY_G3
    errors, _w = R.guardrail_check(a41, cp1["n_adjusted"], cp1["effect_val"])
    assert not errors


def _sap(g3):
    return G4.generate("S", "Hài lòng ngoại trú", "cross_sectional", "Cắt ngang", "STROBE", 1000, 0.05, 0.80,
                       0.5, "PREVALENCE", "2026-10-17", hypothesis_type="descriptive_precision", g3=g3)


def test_sap_muc_12_in_luc_phu_ma_khong_sai_khung_power():
    g3 = {"precision": 0.05, "effect_val": 0.5, "dropout": 0.15, "icc": 0.02, "cluster_size": 20,
          "design_effect": 1.78}
    sap0 = _sap(g3)
    sap1 = _sap({**g3, "luc_muc_tieu_phu": R.tinh_luc_muc_tieu_phu(LUC_PHU, 1000, 0.15, 1.78, 0.05, 0.80)})
    assert "Lực cho mục tiêu phụ" not in sap0
    muc12 = sap1[sap1.index("### §12"):]
    assert "- **Lực cho mục tiêu phụ:** Mục tiêu 2 (hồi quy logistic thứ tự" in muc12
    assert "mục tiêu phụ xem dòng «Lực cho mục tiêu phụ»" in muc12
    # Bộ chấm G4 không được đọc ra «Power: N%» (sai khung với thiết kế theo độ chính xác).
    assert G4Q.parse_signed_numbers(sap1)["power_pct"] is None
    assert G4Q.parse_signed_numbers(sap0)["power_pct"] is None
