"""Biểu đồ sống còn (chặng 3 chương trình biểu đồ, bác sĩ 21/11/2026).

Giá trị chuẩn do R 4.6 + survival 3.8.12 tính trên dữ liệu công khai:
  - survival::lung (228 bệnh nhân ung thư phổi; thời gian ngày; nhóm giới) — survfit (conf.type log-log và log),
    summary(times=), bảng trung vị, survdiff, coxph (Efron);
  - survival::mgus2 (1384 người; sự kiện 1 = tiến triển, 2 = tử vong, cạnh tranh) — survfit đa trạng thái
    (Aalen–Johansen).
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_chung as BC  # noqa: E402
import bieu_do_song_con as SC  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
LUNG = FX / "lung_survival.csv"
MGUS = FX / "mgus2_survival.csv"
MOC = [100, 365, 730]
R_KM = {  # nhóm: [(n_nguy_co, S, lo, hi)] tại 100, 365, 730 — survfit conf.type = "log-log"
    "Nam": [(114, 0.826086956522, 0.7518517229859, 0.879870543129), (35, 0.336087834639, 0.2527291433280,
                                                                      0.421302168223),
            (7, 0.078124091267, 0.0352038844508, 0.143389617998)],
    "Nữ": [(82, 0.922088353414, 0.8435052055954, 0.962077737666), (30, 0.526463030186, 0.4035798232667,
                                                                   0.635316232824),
           (6, 0.187232497905, 0.0846596532273, 0.320832676867)],
}


def _gan(a, b, tuong_doi=1e-9, tuyet_doi=1e-10):
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def _lung():
    return SC.doc_du_lieu(LUNG, "thoi_gian", "bien_co", "gioi")


def _nhom(d, k):
    m = d["g"] == k
    return d["t"][m], d["e"][m]


@pytest.mark.parametrize("k", ["Nam", "Nữ"])
def test_km_log_log_khop_survfit(k):
    t, e = _nhom(_lung(), k)
    km = SC.kaplan_meier(t, e, "log-log")
    for mm, (n, s, lo, hi) in zip(SC.tai_moc(km, t, MOC), R_KM[k]):
        assert mm["n_nguy_co"] == n
        assert _gan(mm["S"], s) and _gan(mm["lo"], lo) and _gan(mm["hi"], hi), (k, mm)


def test_km_ktc_log_khop_survfit():
    d = _lung()
    for k, lo_r in (("Nam", 0.260900503790), ("Nữ", 0.421486340829)):
        t, e = _nhom(d, k)
        assert _gan(SC.tai_moc(SC.kaplan_meier(t, e, "log"), t, [365])[0]["lo"], lo_r)
    with pytest.raises(BC.LoiBieuDo):
        SC.kaplan_meier(*_nhom(d, "Nam"), "arcsin")


def test_trung_vi_va_ktc_khop_bang_survfit():
    d = _lung()
    for k, (m, lo, hi) in (("Nam", (270, 210, 306)), ("Nữ", (426, 345, 524))):
        tv = SC.trung_vi(SC.kaplan_meier(*_nhom(d, k)))
        assert (tv["trung_vi"], tv["duoi"], tv["tren"]) == (m, lo, hi)


def test_trung_vi_bang_dung_05_lay_trung_diem():
    import numpy as np

    km = {"t": np.array([1.0, 2.0, 3.0]), "S": np.array([0.75, 0.5, 0.25]), "lo": np.array([0.5, 0.25, 0.1]),
          "hi": np.array([0.9, 0.8, 0.5])}
    assert SC.trung_vi(km)["trung_vi"] == 2.5


def test_log_rank_khop_survdiff():
    d = _lung()
    lr = SC.log_rank(d["t"], d["e"], d["g"])
    assert _gan(lr["chi2"], 10.3267419549, 1e-9) and _gan(lr["p"], 0.00131116452036, 1e-8) and lr["df"] == 1
    assert _gan(sum(lr["quan_sat"]), sum(lr["ky_vong"]), 1e-12)


def test_cox_efron_khop_coxph():
    d = _lung()
    h = SC.cox_nhom(d["t"], d["e"], d["g"], "Nam")["hr"]["Nữ"]
    assert _gan(h["hr"], 0.588002818564, 1e-8)
    assert _gan(h["ktc"][0], 0.423717830354, 1e-8) and _gan(h["ktc"][1], 0.815984813171, 1e-8)
    assert _gan(h["p"], 0.00149122920488, 1e-6)
    with pytest.raises(BC.LoiBieuDo):
        SC.cox_nhom(d["t"], d["e"], d["g"], "Khác")


def test_aalen_johansen_khop_survfit_da_trang_thai():
    d = SC.doc_du_lieu(MGUS, "thoi_gian", "su_kien", "gioi", ma_su_kien=True)
    R = {"Nam": [(0.0553102406482, 0.575178488879), (0.0956507550310, 0.748127889266),
                 (0.1044602299767, 0.799436406980)],
         "Nữ": [(0.0738856643759, 0.480490045775), (0.1049406741861, 0.695307803032),
                (0.1573903869344, 0.760281744788)]}
    for k, gia_tri in R.items():
        m = d["g"] == k
        for mm, (c1, c2) in zip(SC.cif_tai_moc(SC.aalen_johansen(d["t"][m], d["e"][m]), [120, 240, 360]), gia_tri):
            assert _gan(mm["cif_1"], c1) and _gan(mm["cif_2"], c2), (k, mm)
    m = d["g"] == "Nam"
    assert _gan(SC.cif_tai_moc(SC.aalen_johansen(d["t"][m], d["e"][m]), [120])[0]["khong_su_kien"], 0.3695112704724)


def test_cif_bat_dau_tu_0_va_tong_trang_thai_bang_1(tmp_path):
    d = SC.doc_du_lieu(MGUS, "thoi_gian", "su_kien", "gioi", ma_su_kien=True)
    kq = SC.ve_cif(d["t"], d["e"], d["g"], tmp_path / "c", moc=[0, 120, 240])
    for v in kq["nhom"].values():
        for duong in v["duong"].values():
            assert duong["cif"][0] == 0.0 and duong["t"][0] == 0.0
        for mm in v["tai_moc"]:
            assert _gan(mm["cif_1"] + mm["cif_2"] + mm["khong_su_kien"], 1.0, 1e-12)


def test_doc_du_lieu_tu_choi_ma_1_2_va_thoi_gian_khong_duong(tmp_path):
    p = tmp_path / "a.csv"
    p.write_text("t,e\n5,1\n6,2\n7,1\n", encoding="utf-8", newline="\n")
    with pytest.raises(BC.LoiBieuDo):
        SC.doc_du_lieu(p, "t", "e")
    q = tmp_path / "b.csv"
    q.write_text("t,e\n0,1\n6,0\n", encoding="utf-8", newline="\n")
    with pytest.raises(BC.LoiBieuDo):
        SC.doc_du_lieu(q, "t", "e")
    r = tmp_path / "c.csv"
    r.write_text("t,e,g\n5,1,A\n6,,A\n7,0,B\n8,1,B\n", encoding="utf-8", newline="\n")
    d = SC.doc_du_lieu(r, "t", "e", "g")
    assert d["loai"] == 1 and d["t"].tolist() == [5.0, 7.0, 8.0]


def test_so_nguy_co_tai_moc_trung_thoi_diem_quan_sat_tinh_ca_nguoi_tai_moc():
    import numpy as np

    t, e = np.array([1.0, 2.0, 2.0, 3.0, 4.0]), np.array([1, 1, 0, 1, 0])
    mm = SC.tai_moc(SC.kaplan_meier(t, e), t, [2.0, 2.5])
    assert [m["n_nguy_co"] for m in mm] == [4, 2]  # như summary(survfit, times=): n.risk = số người có t ≥ mốc
    assert _gan(mm[0]["S"], 0.8 * (1 - 1 / 4))


def test_moc_mac_dinh_tron_va_khong_qua_7_vach():
    m = SC._moc_mac_dinh(1022)
    assert m[0] == 0 and len(m) <= 8 and all(x % 100 == 0 for x in m)


def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("them", [
    ["km", "--du-lieu", str(LUNG), "--thoi-gian", "thoi_gian", "--bien-co", "bien_co", "--nhom", "gioi",
     "--moc", "0,100,365,730", "--don-vi", "ngày"],
    ["km", "--du-lieu", str(LUNG), "--thoi-gian", "thoi_gian", "--bien-co", "bien_co", "--dao"],
    ["loglog", "--du-lieu", str(LUNG), "--thoi-gian", "thoi_gian", "--bien-co", "bien_co", "--nhom", "gioi"],
    ["cif", "--du-lieu", str(MGUS), "--thoi-gian", "thoi_gian", "--su-kien", "su_kien", "--nhom", "gioi",
     "--nhan-su-kien", "1=Tiến triển,2=Tử vong"],
])
def test_dong_lenh_ghi_hinh(tmp_path, them):
    ra = tmp_path / "h"
    assert SC.main([*them, "--ra", str(ra)]) == 0
    assert round(_dpi(ra.with_suffix(".png"))[0]) == 300
    assert ra.with_suffix(".pdf").read_bytes()[:5] == b"%PDF-"
    assert json.loads(ra.with_suffix(".json").read_text(encoding="utf-8"))["loai"] == them[0]


def test_json_km_co_bang_so_nguy_co_va_log_rank(tmp_path):
    d = _lung()
    kq = SC.ve_km(d["t"], d["e"], d["g"], tmp_path / "k", moc=[0, 100, 365, 730])
    assert [m["n_nguy_co"] for m in kq["nhom"]["Nam"]["tai_moc"]] == [138, 114, 35, 7]
    assert "log_rank" in kq and "Nữ" in kq["cox"]["hr"]


def test_ma_thoat_tham_so(tmp_path):
    assert SC.main(["km", "--du-lieu", str(LUNG), "--thoi-gian", "thoi_gian", "--ra", str(tmp_path / "x")]) == 3
    assert SC.main(["loglog", "--du-lieu", str(LUNG), "--thoi-gian", "thoi_gian", "--bien-co", "bien_co",
                    "--ra", str(tmp_path / "x")]) == 3
    assert SC.main(["km", "--du-lieu", str(LUNG), "--thoi-gian", "khong_co", "--bien-co", "bien_co",
                    "--ra", str(tmp_path / "x")]) == 2


def _co_survival() -> bool:
    if shutil.which("Rscript") is None:
        return False
    return BC.chay_r_kiem_cheo('cat("KQ ok", as.numeric(requireNamespace("survival", quietly=TRUE)), "\\n")'
                               )["kq"].get("ok") == 1.0


@pytest.mark.skipif(not _co_survival(), reason="thiếu R/survival")
def test_song_kiem_cheo_r():
    d = _lung()
    assert SC.kiem_cheo_km_r(d["t"], d["e"], d["g"], [0, 100, 365, 730], "log-log")["trang_thai"] == "khop"
    assert SC.kiem_cheo_km_r(d["t"], d["e"], d["g"], [200, 500], "log", "Nữ")["trang_thai"] == "khop"
    m = SC.doc_du_lieu(MGUS, "thoi_gian", "su_kien", "gioi", ma_su_kien=True)
    assert SC.kiem_cheo_cif_r(m["t"], m["e"], m["g"], [60, 180])["trang_thai"] == "khop"
