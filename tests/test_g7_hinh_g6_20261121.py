"""§6 Hình kết quả của nháp G7 lấy từ G6_bieu_do.json (21/11/2026) — chỉ khi hình sinh cùng lượt chạy SAP."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import run_g7_auto as G7  # noqa: E402


def _dung(d: Path, chi_muc_bieu_do=None, hinh=None, thieu=None, tao_tep=True):
    cm = {"phan_tich": []}
    if chi_muc_bieu_do is not None:
        cm["bieu_do"] = chi_muc_bieu_do
    (d / "G6_SAP_ket_qua.json").write_text(json.dumps(cm), encoding="utf-8", newline="\n")
    hinh = hinh if hinh is not None else [
        {"id": "MT1", "loai": "cot-ktc", "tep": "bieu-bang/g6-MT1-cot-ktc.png", "mo_ta": "Tỷ lệ kiểm soát",
         "trang_thai": "DA_VE"},
        # hình LỖI ở lượt này nhưng còn tệp cũ của lượt trước trên đĩa — không được liệt kê
        {"id": "HQ", "loai": "spline", "tep": "bieu-bang/g6-HQ-spline.png", "trang_thai": "LOI", "ly_do": "x"},
        {"id": "KM", "loai": "km", "tep": "bieu-bang/g6-KM-km.png", "mo_ta": "Kaplan–Meier", "trang_thai": "DA_VE"}]
    (d / "bieu-bang").mkdir(exist_ok=True)
    if tao_tep:
        for h in hinh:
            if h.get("tep"):
                (d / h["tep"]).write_bytes(b"png")
    (d / "G6_bieu_do.json").write_text(json.dumps({"hinh": hinh, "kiem_danh_muc": {"thieu_bat_buoc": thieu or []}}),
                                       encoding="utf-8", newline="\n")


def test_liet_ke_hinh_da_ve_dung_thu_tu_va_bo_hinh_loi(tmp_path):
    _dung(tmp_path, {"tep": "G6_bieu_do.json", "dem": {"DA_VE": 2, "LOI": 1}}, thieu=["so_do_luong"])
    dong = G7.dung_hinh_g6(tmp_path)
    van = "\n".join(dong)
    assert "![Hình 1. Tỷ lệ kiểm soát](bieu-bang/g6-MT1-cot-ktc.png)" in dong
    assert "**Hình 1. Tỷ lệ kiểm soát**" in dong and "**Hình 2. Kaplan–Meier**" in dong
    assert "`bieu-bang/g6-KM-km.json`" in van
    assert "spline" not in van and "Hình 3" not in van
    assert "so_do_luong" in van and "[CẦN" not in van  # ghi chú, không thêm ô chờ


def test_khong_liet_ke_khi_chi_muc_khong_ghi_bieu_do_hoac_loi(tmp_path):
    _dung(tmp_path, None)  # chạy --khong-ve: hình cũ có thể lệch dữ liệu
    assert G7.dung_hinh_g6(tmp_path) == []
    _dung(tmp_path, {"loi": "RuntimeError: x"})
    assert G7.dung_hinh_g6(tmp_path) == []


def test_word_g7_nhung_anh_that(tmp_path):
    """§6 qua md2docx_vn ⇒ bản Word chứa ảnh thật (không phải dòng chữ đường dẫn)."""
    import zipfile

    from PIL import Image

    _dung(tmp_path, {"tep": "G6_bieu_do.json"}, tao_tep=False)
    for ten, mau in (("g6-MT1-cot-ktc", "white"), ("g6-KM-km", "navy")):  # khác nội dung: docx gộp ảnh trùng
        Image.new("RGB", (300, 200), mau).save(tmp_path / "bieu-bang" / f"{ten}.png", dpi=(300, 300))
    md = "\n".join(["## III. KẾT QUẢ", "", *G7.dung_hinh_g6(tmp_path)])
    import md2docx_vn as M2D

    ra = tmp_path / "G7_thu.docx"
    M2D.markdown_to_docx(md, ra)
    with zipfile.ZipFile(ra) as z:
        anh = [n for n in z.namelist() if n.startswith("word/media/")]
        xml = z.read("word/document.xml").decode("utf-8")
    assert len(anh) == 2, anh
    assert "Hình 2. Kaplan–Meier" in xml and "Thiếu tệp hình" not in xml


def test_bo_hinh_mat_tep(tmp_path):
    _dung(tmp_path, {"tep": "G6_bieu_do.json"}, tao_tep=False)
    assert G7.dung_hinh_g6(tmp_path) == []
