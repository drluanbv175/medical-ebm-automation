"""Biểu đồ mô tả (chặng 4a chương trình biểu đồ, bác sĩ 21/11/2026).

Giá trị chuẩn từ R 4.6: binom.test, prop.test(correct = FALSE), t.test, cor/cor.test, qqnorm, qqline — trên
datasets::mtcars (công khai) và các dãy số nhỏ. Bộ khảo sát Likert là dữ liệu TẤT ĐỊNH dựng cho test (số đếm mỗi mức
cố định, % biết trước), không phải dữ liệu đề tài.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import bieu_do_chung as BC  # noqa: E402
import bieu_do_mo_ta as MT  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"
MTC = FX / "mtcars_r.csv"
LK = FX / "khao_sat_likert_tat_dinh.csv"
MUC = [("1", "Rất không hài lòng"), ("2", "Không hài lòng"), ("3", "Bình thường"), ("4", "Hài lòng"),
       ("5", "Rất hài lòng")]
X10 = [5.1, 6.2, 4.8, 7.0, 5.5, 6.1, 5.9, 4.4, 6.8, 5.0]


def _gan(a, b, tuong_doi=1e-9, tuyet_doi=1e-10):
    return abs(a - b) <= max(tuyet_doi, tuong_doi * abs(b))


def test_ktc_ty_le_khop_binom_va_prop_test():
    lo, hi = MT.ktc_ty_le(18, 40, "wilson")
    assert _gan(lo, 0.307053078109049) and _gan(hi, 0.601709082010679)
    lo, hi = MT.ktc_ty_le(20, 25)
    assert _gan(lo, 0.592962567721) and _gan(hi, 0.931688535988)
    with pytest.raises(BC.LoiBieuDo):
        MT.ktc_ty_le(1, 5, "wald")
    with pytest.raises(BC.LoiBieuDo):
        MT.ktc_ty_le(0, 0)


def test_ktc_trung_binh_khop_t_test():
    k = MT.ktc_trung_binh(X10)
    assert _gan(k["duoi"], 5.0611255424681) and _gan(k["tren"], 6.2988744575319) and k["n"] == 10
    with pytest.raises(BC.LoiBieuDo):
        MT.ktc_trung_binh([1.0])


def test_tuong_quan_khop_cor_va_cor_test():
    dong = MT.doc_csv(MTC)
    m = MT.ma_tran_tuong_quan(dong, ["mpg", "wt"])
    assert _gan(m["r"][("mpg", "wt")], -0.867659376517228) and _gan(m["p"][("mpg", "wt")], 1.29395870135049e-10, 1e-6)
    s = MT.ma_tran_tuong_quan(dong, ["mpg", "hp"], "spearman")
    assert _gan(s["r"][("mpg", "hp")], -0.894664645749963)
    assert m["r"][("mpg", "mpg")] == 1.0 and m["n"][("mpg", "wt")] == 32


def test_tuong_quan_loai_thieu_theo_cap():
    dong = [{"a": str(i), "b": str(i * i), "c": "" if i % 3 == 0 else str(-i)} for i in range(1, 13)]
    m = MT.ma_tran_tuong_quan(dong, ["a", "b", "c"])
    assert m["n"][("a", "b")] == 12 and m["n"][("a", "c")] == 8


def test_qq_diem_ly_thuyet_va_duong_nhu_qqnorm_qqline():
    q = MT.qq_so_lieu(X10)
    for a, b in zip(q["ly_thuyet"][:3], (-1.54663527139923, -1.00049054561931, -0.655423505234427)):
        assert _gan(a, b)
    assert _gan(q["chan"], 5.6, 1e-12) and _gan(q["doc"], 0.852496275640721)
    x32 = [float(r["mpg"]) for r in MT.doc_csv(MTC)]
    q32 = MT.qq_so_lieu(x32)
    assert _gan(q32["ly_thuyet"][0], -2.15387469406146) and _gan(q32["ly_thuyet"][1], -1.67593972277344)
    for lo, hi, z in zip(q32["dai_duoi"], q32["dai_tren"], q32["ly_thuyet"]):
        assert lo < q32["chan"] + q32["doc"] * z < hi


def test_likert_phan_tram_thuan_loi_va_thu_tu():
    dong = MT.doc_csv(LK)
    tl = MT.ty_le_likert(dong, ["q1", "q2"], [m for m, _ in MUC])
    assert tl["q1"]["n"] == 50 and [round(tl["q1"]["pt"][m], 9) for m in "12345"] == [4.0, 12.0, 20.0, 44.0, 20.0]
    assert tl["q2"]["n"] == 49 and tl["q2"]["thieu"] == 1 and tl["q2"]["dem"]["3"] == 9


def test_likert_trung_lap_chia_doi_qua_truc_0(tmp_path):
    kq = MT.ve_likert(MT.doc_csv(LK), ["q1", "q2", "q3", "q4"], MUC, tmp_path / "l")
    q1 = kq["cau_hoi"]["q1"]
    assert _gan(q1["thuan_loi"], 64.0) and _gan(q1["bat_loi"], 16.0)
    assert _gan(q1["bat_dau"], -(4 + 12 + 20 / 2))  # bất lợi sang trái + nửa trung lập
    assert kq["thu_tu_ve"][-1] == "q3"  # thuận lợi cao nhất ở trên cùng
    assert _gan(kq["cau_hoi"]["q4"]["thuan_loi"], 100 * 20 / 49)


def test_likert_thang_chan_khong_co_trung_lap_va_gia_tri_la_bi_tu_choi(tmp_path):
    dong = [{"c": v} for v in "1123444"]
    kq = MT.ve_likert(dong, ["c"], [("1", "a"), ("2", "b"), ("3", "c"), ("4", "d")], tmp_path / "l")
    assert _gan(kq["cau_hoi"]["c"]["bat_dau"], -100 * 3 / 7)
    with pytest.raises(BC.LoiBieuDo):
        # «6» lẫn giữa các câu trả lời hợp lệ: phải báo lỗi, không âm thầm bỏ
        MT.ty_le_likert([{"c": "1"}, {"c": "4"}, {"c": "6"}], ["c"], ["1", "2", "3", "4", "5"])


def test_thu_tu_nhom_so_tang_dan_chu_giu_nguyen():
    assert MT.thu_tu_nhom(["6", "4", "8", "4", None]) == ["4", "6", "8"]
    assert MT.thu_tu_nhom(["Nữ", "Nam"]) == ["Nữ", "Nam"]


def test_cot_ktc_ty_le_va_trung_binh(tmp_path):
    dong = MT.doc_csv(MTC)
    kq = MT.ve_cot_ktc(dong, "am", tmp_path / "c", muc="1", cot_nhom="cyl")
    assert list(kq["nhom"]) == ["4", "6", "8"] and (kq["nhom"]["4"]["k"], kq["nhom"]["4"]["n"]) == (8, 11)
    kq2 = MT.ve_cot_ktc(dong, "mpg", tmp_path / "d", trung_binh=True)
    assert _gan(kq2["nhom"][""]["trung_binh"], 20.090625)
    with pytest.raises(BC.LoiBieuDo):
        MT.ve_cot_ktc(dong, "am", tmp_path / "e")


def test_du_lieu_thieu_dem_dung(tmp_path):
    kq = MT.ve_thieu(MT.doc_csv(LK), tmp_path / "t")
    assert kq["N"] == 50 and kq["du_lieu_day_du"] == 48 and _gan(kq["pt_thieu"]["q2"], 2.0)
    assert sorted(len(t["thieu"]) for t in kq["to_hop"]) == [0, 1, 1]


def test_theo_thoi_gian_trung_binh_moi_moc(tmp_path):
    dong = MT.doc_csv(LK)
    kq = MT.ve_theo_thoi_gian(dong, "lan", "thoi_gian_cho", tmp_path / "g")
    v1 = [float(r["thoi_gian_cho"]) for r in dong if r["lan"] == "1"]
    assert kq["moc"] == [1.0, 2.0, 3.0] and _gan(kq["nhom"][""][0]["trung_binh"], sum(v1) / len(v1))


def _dpi(p: Path):
    from PIL import Image

    with Image.open(p) as im:
        return im.info.get("dpi")


@pytest.mark.parametrize("them", [
    ["cot-ktc", "--du-lieu", str(MTC), "--bien", "am", "--muc", "1", "--nhom", "cyl"],
    ["cot-ktc", "--du-lieu", str(MTC), "--bien", "mpg", "--trung-binh", "--nhom", "am"],
    ["likert", "--du-lieu", str(LK), "--cot", "q1,q2,q3,q4", "--muc", ",".join(f"{a}={b}" for a, b in MUC)],
    ["phan-bo", "--du-lieu", str(MTC), "--bien", "mpg", "--nhom", "am", "--kieu", "violin"],
    ["phan-bo", "--du-lieu", str(MTC), "--bien", "mpg"],
    ["qq", "--du-lieu", str(MTC), "--bien", "mpg"],
    ["tuong-quan", "--du-lieu", str(MTC), "--cot", "mpg,wt,hp,qsec", "--phuong-phap", "spearman"],
    ["thieu", "--du-lieu", str(LK)],
    ["theo-thoi-gian", "--du-lieu", str(LK), "--thoi-diem", "lan", "--bien", "thoi_gian_cho", "--nhom", "gioi"],
])
def test_dong_lenh_ghi_hinh(tmp_path, them):
    ra = tmp_path / "h"
    assert MT.main([*them, "--ra", str(ra)]) == 0
    assert round(_dpi(ra.with_suffix(".png"))[0]) == 300
    assert ra.with_suffix(".pdf").read_bytes()[:5] == b"%PDF-"
    assert json.loads(ra.with_suffix(".json").read_text(encoding="utf-8"))["loai"] == them[0].replace("-", "_")


def test_ma_thoat(tmp_path):
    assert MT.main(["qq", "--du-lieu", str(MTC), "--ra", str(tmp_path / "x")]) == 3
    assert MT.main(["likert", "--du-lieu", str(LK), "--cot", "q1", "--ra", str(tmp_path / "x")]) == 3
    assert MT.main(["qq", "--du-lieu", str(MTC), "--bien", "khong_co", "--ra", str(tmp_path / "x")]) == 2


@pytest.mark.skipif(shutil.which("Rscript") is None, reason="máy không có R")
def test_song_kiem_cheo_r():
    import tempfile

    dong = MT.doc_csv(MTC)

    with tempfile.TemporaryDirectory() as td:
        k1 = MT.ve_cot_ktc(dong, "am", Path(td) / "c", muc="1", cot_nhom="cyl")
        k2 = MT.ve_cot_ktc(dong, "am", Path(td) / "d", muc="1", cot_nhom="cyl", ktc="wilson")
    assert MT.kiem_cheo_r_cot(k1, "clopper-pearson")["trang_thai"] == "khop"
    assert MT.kiem_cheo_r_cot(k2, "wilson")["trang_thai"] == "khop"
    assert MT.kiem_cheo_r_tuong_quan(dong, ["mpg", "wt", "hp"], "spearman")["trang_thai"] == "khop"
