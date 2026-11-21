"""Biểu đồ chẩn đoán & mô hình dự báo (chặng 2 chương trình biểu đồ, bác sĩ 21/11/2026).

Giá trị chuẩn do R 4.6 tính trên dữ liệu công khai:
  - pROC::aSAH (113 ca xuất huyết dưới nhện; dấu ấn s100b, ndka) — roc, ci.auc(delong), roc.test(delong),
    coords("best", youden), var/cov(delong);
  - dcurves::df_binary (750 người, cancer ~ cancerpredmarker, famhistory) — rms::val.prob, glm offset (CITL),
    lowess(iter = 0), dcurves::dca.
"""
from __future__ import annotations

import json
import math
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_chan_doan as C  # noqa: E402
import bieu_do_chung as BC  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
ASAH = FX / "asah_proc.csv"
DFB = FX / "df_binary_dcurves.csv"


def _gan(a: float, b: float, tuong_doi: float = 1e-9, tuyet_doi: float = 1e-10) -> bool:
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _asah():
    return C.doc_du_lieu(ASAH, "ket_cuc", ["s100b", "ndka"])


def _dfb(lech: bool = False):
    import numpy as np

    d = C.doc_du_lieu(DFB, "cancer", ["cancerpredmarker", "famhistory"])
    p = d["x"]["cancerpredmarker"]
    if lech:
        p = 1 / (1 + np.exp(-(0.5 + 1.5 * np.log(p / (1 - p)))))
    return d["y"], p, d["x"]["famhistory"]


# ── ROC ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_auc_va_ktc_delong_khop_proc():
    d = _asah()
    kq = C.phan_tich_roc(d["y"], d["x"])
    s, n = kq["xet_nghiem"]["s100b"], kq["xet_nghiem"]["ndka"]
    assert _gan(s["auc"], 0.731368563686) and _gan(n["auc"], 0.61195799458)
    assert _gan(s["ktc"][0], 0.630118211762) and _gan(s["ktc"][1], 0.83261891561)
    assert _gan(n["ktc"][0], 0.501244999272) and _gan(n["ktc"][1], 0.722670989888)
    assert _gan(s["se_auc"] ** 2, 0.00266868245717)
    assert kq["m_benh"] == 41 and kq["n_khong_benh"] == 72


def test_so_sanh_delong_khop_roc_test():
    d = _asah()
    s = C.phan_tich_roc(d["y"], d["x"])["so_sanh"][0]
    assert (s["a"], s["b"]) == ("s100b", "ndka")
    assert _gan(s["z"], 1.39077002574) and _gan(s["p"], 0.164295175223)
    assert _gan(s["cov"], -0.000756164938057)


def test_youden_khop_coords_best():
    d = _asah()
    yd = C.phan_tich_roc(d["y"], d["x"])["xet_nghiem"]["s100b"]["youden"]
    assert _gan(yd["nguong"], 0.205) and _gan(yd["do_nhay"], 0.634146341463) and _gan(yd["do_dac_hieu"], 0.805555555556)


def test_huong_thap_dao_auc():
    d = _asah()
    a = C.phan_tich_roc(d["y"], {"ndka": d["x"]["ndka"]}, "thap")["xet_nghiem"]["ndka"]["auc"]
    assert _gan(a, 1 - 0.61195799458)
    with pytest.raises(BC.LoiBieuDo):
        C.phan_tich_roc(d["y"], d["x"], "ngang")


def test_auc_bang_xac_suat_mann_whitney_khi_co_trung():
    import numpy as np

    y = np.array([1, 1, 1, 0, 0, 0, 0])
    x = np.array([3.0, 2.0, 2.0, 2.0, 1.0, 1.0, 0.5])
    dem = sum((a > b) + 0.5 * (a == b) for a in x[y == 1] for b in x[y == 0])
    assert _gan(float(C.delong(y, [x])["auc"][0]), dem / 12)


def test_precision_recall_ap_tinh_tay():
    import numpy as np

    r = C.precision_recall(np.array([1, 0, 1, 0]), np.array([0.9, 0.8, 0.7, 0.1]))
    assert _gan(r["ap"], 0.5 * 1 + 0.5 * 2 / 3) and r["ty_le_hien_mac"] == 0.5


# ── Hiệu chuẩn ──────────────────────────────────────────────────────────────────────────────────────────────────────
def test_hieu_chuan_khop_val_prob_mo_hinh_dung():
    y, p, _ = _dfb()
    h = C.hieu_chuan(y, p)
    assert _gan(h["c"], 0.860627537837) and _gan(h["brier"], 0.084929097797)
    assert abs(h["chan_hieu_chuan_lai"]) < 1e-6 and abs(h["do_doc"] - 1) < 1e-6
    assert _gan(h["emax"], 0.0458497674599, 1e-6)


def test_hieu_chuan_khop_val_prob_va_citl_mo_hinh_lech():
    y, p, _ = _dfb(lech=True)
    h = C.hieu_chuan(y, p)
    assert _gan(h["brier"], 0.0859452848386)
    assert _gan(h["chan_hieu_chuan_lai"], -0.333333302599, 1e-6) and _gan(h["do_doc"], 0.666666685803, 1e-6)
    assert _gan(h["citl"], 0.0867433714609, 1e-7)
    assert _gan(h["e_tren_o"], 0.958925758882)
    assert h["do_doc_ktc"][0] < 0.6667 < h["do_doc_ktc"][1] < 1  # KTC độ dốc không chứa 1 — mô hình quá khớp


def test_lowess_khop_r_iter_0():
    y, p, _ = _dfb(lech=True)
    lx, ly = C._lowess(p, y)
    chuan = ((8.6824844026e-06, 0.0131033277206), (0.00575496593895, 0.0238911595118),
             (0.0798843030481, 0.0852833898768), (0.999849809678, 0.818848723133))
    for i, (xr, yr) in zip((0, 199, 499, 749), chuan):
        assert _gan(float(lx[i]), xr, 1e-8) and _gan(float(ly[i]), yr, 1e-6), i


def test_nhom_hieu_chuan_du_10_nhom_va_ktc_bao_quan_sat():
    y, p, _ = _dfb()
    h = C.hieu_chuan(y, p, 10)
    assert len(h["nhom"]) == 10 and sum(g["n"] for g in h["nhom"]) == 750
    assert all(g["ktc"][0] <= g["quan_sat"] <= g["ktc"][1] for g in h["nhom"])


def test_hieu_chuan_tu_choi_xac_suat_ngoai_0_1():
    import numpy as np

    with pytest.raises(BC.LoiBieuDo):
        C.hieu_chuan(np.array([0, 1, 1]), np.array([0.2, 1.0, 0.5]))


# ── DCA ─────────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_dca_khop_dcurves():
    y, p, fam = _dfb()
    ng = [0.05, 0.1, 0.2, 0.3, 0.5]
    d = C.dca(y, {"cancerpredmarker": p, "famhistory": fam}, ng)
    R_ALL = [0.09473684210526, 0.04444444444444, -0.075, -0.22857142857143, -0.72]
    R_M = [0.10554385964912, 0.08740740740741, 0.06733333333333, 0.05466666666667, 0.02133333333333]
    R_F = [0.02561403508772, 0.01851851851852, 0.00166666666667, -0.02, -0.08933333333333]
    for k in range(5):
        assert _gan(d["tat_ca"][k], R_ALL[k], 1e-11, 1e-12)
        assert _gan(d["mo_hinh"]["cancerpredmarker"][k], R_M[k], 1e-11, 1e-12)
        assert _gan(d["mo_hinh"]["famhistory"][k], R_F[k], 1e-11, 1e-12)
    assert d["khong"] == [0.0] * 5
    with pytest.raises(BC.LoiBieuDo):
        C.dca(y, {"m": p}, [0.0, 0.5])


def test_nguong_dca_doc_tu_chuoi():
    assert C._nguong("0.05:0.25:0.05") == [0.05, 0.1, 0.15, 0.2, 0.25]
    with pytest.raises(BC.LoiBieuDo):
        C._nguong("0:0.5:0.1")


# ── Fagan ───────────────────────────────────────────────────────────────────────────────────────────────────────────
def test_fagan_hau_nghiem_va_hinh_hoc_duong_thang(tmp_path):
    assert _gan(C.hau_nghiem(0.3, 5.2), (0.3 / 0.7 * 5.2) / (1 + 0.3 / 0.7 * 5.2))
    kq = C.ve_fagan(0.3, 5.2, 0.25, tmp_path / "f")
    lg = lambda q: math.log(q / (1 - q))  # noqa: E731
    for k, lr in (("lr_duong", 5.2), ("lr_am", 0.25)):
        post = kq[k]["hau_nghiem"]
        # đường thẳng (−1, −logit tiền) → (1, logit hậu) cắt trục giữa đúng tại log(LR)/2
        assert _gan((-lg(0.3) + lg(post)) / 2, math.log(lr) / 2, 1e-12)
    with pytest.raises(BC.LoiBieuDo):
        C.hau_nghiem(1.2, 2.0)


# ── Đọc dữ liệu ─────────────────────────────────────────────────────────────────────────────────────────────────────
def test_doc_du_lieu_nhan_true_false_va_dem_dong_thieu(tmp_path):
    p = tmp_path / "d.csv"
    p.write_text("kq,x\nTRUE,1.5\nfalse,0.2\nCó,2\nkhông,\n1,NA\n0,0.1\n", encoding="utf-8", newline="\n")
    d = C.doc_du_lieu(p, "kq", ["x"])
    assert d["y"].tolist() == [1, 0, 1, 0] and d["loai"] == 2
    q = tmp_path / "e.csv"
    q.write_text("kq,x\n1,1\n1,2\n", encoding="utf-8", newline="\n")
    with pytest.raises(BC.LoiBieuDo):
        C.doc_du_lieu(q, "kq", ["x"])
    with pytest.raises(BC.LoiBieuDo):
        C.doc_du_lieu(p, "kq", ["khong_co"])


# ── Dòng lệnh: hình 300 dpi + PDF + JSON ────────────────────────────────────────────────────────────────────────────
def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("lenh,them", [
    ("roc", ["--du-lieu", str(ASAH), "--ket-cuc", "ket_cuc", "--diem", "s100b,ndka"]),
    ("pr", ["--du-lieu", str(ASAH), "--ket-cuc", "ket_cuc", "--diem", "s100b"]),
    ("hieu-chuan", ["--du-lieu", str(DFB), "--ket-cuc", "cancer", "--diem", "cancerpredmarker"]),
    ("dca", ["--du-lieu", str(DFB), "--ket-cuc", "cancer", "--diem", "cancerpredmarker,famhistory"]),
    ("fagan", ["--tien-nghiem", "0.3", "--lr-duong", "5.2", "--lr-am", "0.25"]),
    ("phan-bo", ["--du-lieu", str(ASAH), "--ket-cuc", "ket_cuc", "--diem", "s100b", "--diem-cat", "0.205"]),
])
def test_dong_lenh_ghi_hinh(tmp_path, lenh, them):
    ra = tmp_path / lenh
    assert C.main([lenh, *them, "--ra", str(ra)]) == 0
    assert round(_dpi(ra.with_suffix(".png"))[0]) == 300
    assert ra.with_suffix(".pdf").read_bytes()[:5] == b"%PDF-"
    assert json.loads(ra.with_suffix(".json").read_text(encoding="utf-8"))["loai"] == lenh.replace("-", "_")


def test_ma_thoat_tham_so(tmp_path):
    assert C.main(["roc", "--ra", str(tmp_path / "x")]) == 3
    assert C.main(["hieu-chuan", "--du-lieu", str(DFB), "--ket-cuc", "cancer", "--diem", "cancerpredmarker,famhistory",
                   "--ra", str(tmp_path / "x")]) == 3
    assert C.main(["roc", "--du-lieu", str(ASAH), "--ket-cuc", "ket_cuc", "--diem", "khong_co",
                   "--ra", str(tmp_path / "x")]) == 2


def _co_r(goi: str) -> bool:
    if shutil.which("Rscript") is None:
        return False
    kq = BC.chay_r_kiem_cheo(f'cat("KQ ok", as.numeric(requireNamespace("{goi}", quietly=TRUE)), "\\n")')
    return kq["kq"].get("ok") == 1.0


@pytest.mark.skipif(not (_co_r("pROC") and _co_r("rms") and _co_r("dcurves")), reason="thiếu R/pROC/rms/dcurves")
def test_song_kiem_cheo_r():
    d = _asah()
    assert C.kiem_cheo_roc_r(d["y"], d["x"])["trang_thai"] == "khop"
    y, p, fam = _dfb(lech=True)
    assert C.kiem_cheo_hieu_chuan_r(y, p)["trang_thai"] == "khop"
    assert C.kiem_cheo_dca_r(y, {"m": p, "f": fam}, [0.05, 0.2, 0.4])["trang_thai"] == "khop"
