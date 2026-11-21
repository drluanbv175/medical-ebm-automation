"""Cửa vào biểu đồ `ve_bieu_do.py` (chặng 6 chương trình biểu đồ, bác sĩ 21/11/2026): danh mục theo thiết kế phải
khớp ĐÚNG các lệnh có thật của bảy họ công cụ (chống trôi lệch tài liệu ↔ mã), và `kiem` bắt đúng hình bắt buộc còn
thiếu cùng lỗi tệp (dpi, PDF, ngôn ngữ).
"""
from __future__ import annotations

import ast
import json
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parent.parent / "tools"
sys.path.insert(0, str(TOOLS))

import bieu_do_mo_ta as MT  # noqa: E402
import ve_bieu_do as VB  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "bieu_do"


def _lenh_cua(tep: str) -> set:
    """Các lựa chọn của đối số «lenh» trong argparse của công cụ (đọc AST, không chạy)."""
    cay = ast.parse((TOOLS / tep).read_text(encoding="utf-8"))
    for nut in ast.walk(cay):
        if (isinstance(nut, ast.Call) and getattr(nut.func, "attr", "") == "add_argument" and nut.args
                and isinstance(nut.args[0], ast.Constant) and nut.args[0].value == "lenh"):
            for kw in nut.keywords:
                if kw.arg == "choices":
                    return {e.value for e in kw.value.elts}
    return set()


def test_moi_hinh_trong_danh_muc_la_lenh_co_that():
    for loai, (tep, lenh, _) in VB.HINH.items():
        assert (TOOLS / tep).exists(), tep
        assert lenh in _lenh_cua(tep), f"{tep} không có lệnh {lenh}"
        assert loai == lenh.replace("-", "_"), loai  # «loai» trong JSON = tên lệnh (test từng họ đã kiểm)


def test_moi_thiet_ke_chi_dung_hinh_hop_le_va_co_so_do_hoac_hinh_chinh():
    for tk, d in VB.DANH_MUC.items():
        for x in d["bat_buoc"] + d["khuyen_nghi"] + list(d["khi_phu_hop"]):
            assert x in VB.HINH, (tk, x)
        assert d["bat_buoc"], tk
        assert d["chuan"]
    for tk in ("rct", "cohort", "case_control", "cross_sectional", "diagnostic", "prediction", "sr_ma", "dta_ma"):
        assert VB.DANH_MUC[tk]["bat_buoc"][0] == "so_do_luong", tk
    assert {"sroc", "dta_forest"} <= set(VB.DANH_MUC["dta_ma"]["bat_buoc"])
    assert "hieu_chuan" in VB.DANH_MUC["prediction"]["bat_buoc"]
    assert "roc" in VB.DANH_MUC["diagnostic"]["bat_buoc"] and "forest" in VB.DANH_MUC["sr_ma"]["bat_buoc"]
    assert {"ce_plane", "ceac"} <= set(VB.DANH_MUC["economic"]["bat_buoc"])


def test_bi_danh_va_thiet_ke_la():
    assert VB.danh_muc("cat_ngang")["thiet_ke"] == "cross_sectional"
    with pytest.raises(SystemExit):
        VB.danh_muc("khong_co")
    assert VB.main(["danh-muc", "--thiet-ke", "khong_co"]) == 3
    assert VB.main(["danh-muc", "--thiet-ke", "rct"]) == 0
    assert VB.main(["kiem", "--thiet-ke", "rct"]) == 3


def test_kiem_thu_muc_bao_thieu_va_loi_tep(tmp_path, capsys):
    dong = MT.doc_csv(FX / "mtcars_r.csv")
    MT.ve_cot_ktc(dong, "am", tmp_path / "cot", muc="1", cot_nhom="cyl")
    kq = VB.kiem_thu_muc(tmp_path, "cross_sectional")
    assert kq["da_co"] == {"cot_ktc": ["cot"]} and kq["loi_tep"] == []
    assert set(kq["thieu_bat_buoc"]) == {"so_do_luong", "forest_uoc_luong"} and not kq["dat"]
    (tmp_path / "cot.pdf").unlink()
    d = json.loads((tmp_path / "cot.json").read_text(encoding="utf-8"))
    d["ngon_ngu"] = "en"
    (tmp_path / "cot.json").write_text(json.dumps(d), encoding="utf-8", newline="\n")
    loi = VB.kiem_thu_muc(tmp_path, "cross_sectional")["loi_tep"]
    assert any("PDF" in x for x in loi) and any("ngôn ngữ" in x for x in loi)
    assert VB.main(["kiem", "--thu-muc", str(tmp_path), "--thiet-ke", "cross_sectional"]) == 1


def test_kiem_dat_khi_du_hinh_bat_buoc(tmp_path):
    import bieu_do_bao_cao as BB
    import bieu_do_hoi_quy as HQ

    BB.ve_so_do_luong(MT.doc_csv(FX / "so_do_luong_mau.csv"), tmp_path / "luong")
    MT.ve_cot_ktc(MT.doc_csv(FX / "mtcars_r.csv"), "am", tmp_path / "cot", muc="1", cot_nhom="cyl")
    HQ.ve_forest_uoc_luong(MT.doc_csv(FX / "bang_or_birthwt.csv"), "OR", tmp_path / "or")
    kq = VB.kiem_thu_muc(tmp_path, "cross_sectional", ngon_ngu=None)
    assert kq["thieu_bat_buoc"] == [] and kq["loi_tep"] == [] and kq["dat"]


def test_png_duoi_300_dpi_bi_bat(tmp_path):
    from PIL import Image

    dong = MT.doc_csv(FX / "mtcars_r.csv")
    MT.ve_cot_ktc(dong, "am", tmp_path / "cot", muc="1", cot_nhom="cyl")
    with Image.open(tmp_path / "cot.png") as im:
        im.save(tmp_path / "cot.png", dpi=(96, 96))
    assert any("96 dpi" in x for x in VB.kiem_thu_muc(tmp_path, "cross_sectional")["loi_tep"])
    shutil.rmtree(tmp_path)
