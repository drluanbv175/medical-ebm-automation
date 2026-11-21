"""Biểu đồ hồi quy (chặng 4b chương trình biểu đồ, bác sĩ 21/11/2026).

Giá trị chuẩn do R 4.6 tính trên MASS::birthwt (189 trẻ sơ sinh, công khai): rms::lrm + rcs(lwt, 4) + Predict(ref.zero)
+ anova; MASS::polr predict(type = "probs"); stats::lm hatvalues/cooks.distance/rstandard. Hai bảng ước lượng mẫu là OR
thật của glm trên cùng bộ dữ liệu.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_chung as BC  # noqa: E402
import bieu_do_hoi_quy as HQ  # noqa: E402
import bieu_do_mo_ta as MT  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
BW = FX / "birthwt_mass.csv"
BANG = FX / "bang_or_birthwt.csv"
NHOM = FX / "bang_nhom_nho_birthwt.csv"


def _gan(a, b, tuong_doi=1e-9, tuyet_doi=1e-10):
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _bw(*cot):
    import numpy as np

    dong = MT.doc_csv(BW)
    return [np.array([float(r[c]) for r in dong]) for c in cot]


def test_nut_harrell_khop_rcspline_eval_va_quy_tac_n_duoi_100():
    (lwt,) = _bw("lwt")
    assert HQ.nut_harrell(lwt, 4) == pytest.approx([94.4, 115.0, 130.2, 188.2], abs=1e-12)
    x = list(range(1, 61))
    nut = HQ.nut_harrell(x, 4)
    assert nut[0] == 5 and nut[-1] == 56  # n < 100: nút ngoài = giá trị thứ 5 từ hai đầu
    with pytest.raises(BC.LoiBieuDo):
        HQ.nut_harrell([1, 1, 1, 2, 2, 2] * 20, 4)
    with pytest.raises(BC.LoiBieuDo):
        HQ.nut_harrell(lwt, 9)


def test_spline_or_ktc_va_phi_tuyen_khop_rms():
    low, lwt, smoke = _bw("low", "lwt", "smoke")
    s = HQ.spline(lwt, low.astype(int), smoke[:, None], 4)
    assert s["tham_chieu"] == 121.0
    u, lo, hi = HQ.du_doan_spline(s, [100, 150, 200], ktc=True)
    for a, b in zip(u, (1.84730896237064, 0.943526061709022, 0.5019556428244)):
        assert _gan(a, b, 1e-6)
    for a, b in zip(lo, (1.01617524800936, 0.443433068856614, 0.143516767965163)):
        assert _gan(a, b, 1e-6)
    for a, b in zip(hi, (3.3582301961595, 2.00761172688273, 1.75560996067314)):
        assert _gan(a, b, 1e-6)
    assert _gan(s["phi_tuyen"]["chi2"], 1.69141854258022, 1e-6) and _gan(s["phi_tuyen"]["p"], 0.429252793531365, 1e-6)
    assert s["phi_tuyen"]["df"] == 2


def test_spline_tai_tham_chieu_bang_1_va_tu_choi_ket_cuc_khong_nhi_phan():
    import numpy as np

    low, lwt = _bw("low", "lwt")
    s = HQ.spline(lwt, low.astype(int), None, 3, tham_chieu=130)
    assert _gan(HQ.du_doan_spline(s, [130])[0], 1.0, 1e-12)
    with pytest.raises(BC.LoiBieuDo):
        HQ.spline(lwt, np.round(lwt / 50).astype(int), None, 4)


def test_ty_le_chenh_thu_tu_khop_polr():
    import numpy as np

    bwt3, lwt, smoke = _bw("bwt3", "lwt", "smoke")
    y = bwt3.astype(int) - 1
    m = HQ.ty_le_chenh_thu_tu(y, np.column_stack([lwt, smoke]))
    assert _gan(m["beta"][0], 0.0149528609580286, 1e-5) and _gan(m["beta"][1], -0.672689922834493, 1e-5)
    assert _gan(m["zeta"][0], 0.819935808792937, 1e-5) and _gan(m["zeta"][1], 1.72350369345992, 1e-5)
    P = HQ.xac_suat_thu_tu(m, [[100, 0], [150, 0], [200, 0]])
    R = [[0.337299859180649, 0.219508191568832, 0.443191949250519],
         [0.194192751965666, 0.178793840481695, 0.627013407552639],
         [0.102418516627759, 0.117340973216541, 0.7802405101557]]
    for hp, hr in zip(P, R):
        assert _gan(sum(hp), 1.0, 1e-12)
        for a, b in zip(hp, hr):
            assert _gan(a, b, 1e-5)
    with pytest.raises(BC.LoiBieuDo):
        HQ.ty_le_chenh_thu_tu(np.array([0, 1, 0, 1]), np.ones((4, 1)))


def test_chan_doan_lm_khop_hatvalues_cooks_rstandard():
    import numpy as np

    bwt, lwt, smoke, age = _bw("bwt", "lwt", "smoke", "age")
    d = HQ.chan_doan_lm(np.column_stack([lwt, smoke, age]), bwt)
    for i, (h, c, r) in zip((0, 49, 188), ((0.030654371950333, 0.00809809991501545, -1.01207961536614),
                                           (0.0241476528897786, 0.00313045201937729, 0.711357827700413),
                                           (0.0143204656101372, 0.000536681579688011, -0.384394921024379))):
        assert _gan(d["hat"][i], h) and _gan(d["cook"][i], c) and _gan(d["rstandard"][i], r)
    assert _gan(sum(d["hat"]), 4.0, 1e-9)  # vết ma trận mũ = số tham số


def test_bang_uoc_luong_doc_dung_va_tu_choi_so_sai():
    b = HQ.doc_bang_uoc_luong(MT.doc_csv(BANG), "OR")
    assert b["mo_hinh"] == ["Thô", "Hiệu chỉnh"]
    hut = b["bien"]["Hút thuốc"]
    assert hut["Không"]["Thô"]["u"] is None and _gan(hut["Có"]["Hiệu chỉnh"]["u"], 2.870363, 1e-6)
    with pytest.raises(BC.LoiBieuDo):
        HQ.doc_bang_uoc_luong([{"bien": "a", "muc": "b", "uoc_luong": "2", "duoi": "2.5", "tren": "3"}], "OR")
    with pytest.raises(BC.LoiBieuDo):
        HQ.doc_bang_uoc_luong([{"bien": "a", "muc": "b", "uoc_luong": "0.5", "duoi": "-1", "tren": "3"}], "OR")
    assert HQ.doc_bang_uoc_luong([{"bien": "a", "muc": "b", "uoc_luong": "0.5", "duoi": "-1", "tren": "3"}], "B")


def test_forest_va_nhom_nho_json(tmp_path):
    kq = HQ.ve_forest_uoc_luong(MT.doc_csv(BANG), "OR", tmp_path / "f")
    assert sum(1 for d in kq["dong"] if d.get("tham_chieu")) == 4
    assert len([d for d in kq["dong"] if not d.get("tham_chieu")]) == 6
    k2 = HQ.ve_forest_uoc_luong(MT.doc_csv(NHOM), "OR", tmp_path / "n", nhom_nho=True)
    assert k2["loai"] == "nhom_nho" and len(k2["dong"]) == 3


def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("them", [
    ["forest-uoc-luong", "--du-lieu", str(BANG), "--do", "OR"],
    ["nhom-nho", "--du-lieu", str(NHOM), "--do", "OR"],
    ["spline", "--du-lieu", str(BW), "--ket-cuc", "low", "--phoi-nhiem", "lwt", "--bien-kem", "smoke"],
    ["spline", "--du-lieu", str(BW), "--ket-cuc", "bwt", "--phoi-nhiem", "lwt", "--tuyen-tinh", "--so-nut", "3"],
    ["xac-suat-thu-tu", "--du-lieu", str(BW), "--ket-cuc", "bwt3", "--phoi-nhiem", "lwt", "--bien-kem", "smoke",
     "--gia-tri-kem", "smoke=0"],
    ["chan-doan-lm", "--du-lieu", str(BW), "--ket-cuc", "bwt", "--bien-doc-lap", "lwt,smoke,age"],
])
def test_dong_lenh_ghi_hinh(tmp_path, them):
    ra = tmp_path / "h"
    assert HQ.main([*them, "--ra", str(ra)]) == 0
    assert round(_dpi(ra.with_suffix(".png"))[0]) == 300
    assert ra.with_suffix(".pdf").read_bytes()[:5] == b"%PDF-"
    assert json.loads(ra.with_suffix(".json").read_text(encoding="utf-8"))["loai"] == them[0].replace("-", "_")


def test_ma_thoat(tmp_path):
    assert HQ.main(["spline", "--du-lieu", str(BW), "--ra", str(tmp_path / "x")]) == 3
    assert HQ.main(["chan-doan-lm", "--du-lieu", str(BW), "--ket-cuc", "bwt", "--ra", str(tmp_path / "x")]) == 3
    assert HQ.main(["spline", "--du-lieu", str(BW), "--ket-cuc", "khong_co", "--phoi-nhiem", "lwt",
                    "--ra", str(tmp_path / "x")]) == 2


def _co_r(goi: str) -> bool:
    if shutil.which("Rscript") is None:
        return False
    return BC.chay_r_kiem_cheo(f'cat("KQ ok", as.numeric(requireNamespace("{goi}", quietly=TRUE)), "\\n")'
                               )["kq"].get("ok") == 1.0


@pytest.mark.skipif(not (_co_r("rms") and _co_r("MASS")), reason="thiếu R/rms/MASS")
def test_song_kiem_cheo_r():
    import numpy as np

    low, lwt, smoke, bwt3, bwt, age = _bw("low", "lwt", "smoke", "bwt3", "bwt", "age")
    assert HQ.kiem_cheo_spline_r(lwt, low.astype(int), smoke[:, None], ["smoke"], 4, None, False,
                                 [100, 130, 180])["trang_thai"] == "khop"
    assert HQ.kiem_cheo_spline_r(lwt, bwt, None, [], 3, 125.0, True, [100, 150])["trang_thai"] == "khop"
    assert HQ.kiem_cheo_polr_r([str(int(v)) for v in bwt3], lwt, smoke[:, None], [[110, 1], [160, 1]]
                               )["trang_thai"] == "khop"
    assert HQ.kiem_cheo_lm_r(np.column_stack([lwt, smoke, age]), bwt)["trang_thai"] == "khop"
