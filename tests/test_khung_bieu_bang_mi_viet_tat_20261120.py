"""Ba lỗi bộ sinh biểu bảng do phản biện máy đề cương BTM bắt (20/11/2026).

1. Nhãn biến chèn giữa câu bị `.lower()` CẢ chuỗi ⇒ «xét nghiệm đủ uacr» (viết tắt bị hạ). Nay chỉ hạ chữ cái đầu.
2. Ghi chú bảng nhóm nhỏ in cứng «kèm kiểm định tương tác» ⇒ mâu thuẫn SAP BTM («mô tả, không kiểm định tương tác»)
   lẫn C1a («không có số hạng tương tác định trước»). Nay không tự khẳng định.
3. Phân tích có gán đa trị (`n_imputations`) mà bảng đa biến chỉ có MỘT cột ⇒ đề cương thiếu phân tích trên ca đủ dữ
   liệu (ĐN8 của BTM). Nay thêm cột «ca đủ dữ liệu» + ghi chú; không gán đa trị thì bảng giữ nguyên.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import khung_bieu_bang as KBB  # noqa: E402


def _ngu_canh(n_gan=None) -> KBB.NguCanh:
    bien = {
        "xn_du": KBB.Bien("xn_du", "Được xét nghiệm đủ UACR và creatinin năm 2026", "nhi_phan",
                          [("1", "Có"), ("0", "Không")]),
        "tuoi": KBB.Bien("tuoi", "Tuổi", "lien_tuc", [], "năm"),
        "gioi": KBB.Bien("gioi", "Giới", "nhi_phan", [("1", "Nam"), ("2", "Nữ")]),
    }
    ma_tran = [
        {"muc_tieu": "1", "khai_niem": "được xét nghiệm đủ", "vai_tro": "ket_cuc_chinh", "bien": "xn_du",
         "kieu": "nhi_phan"},
        {"muc_tieu": "1", "khai_niem": "tuổi", "vai_tro": "yeu_to", "bien": "tuoi", "kieu": "lien_tuc"},
        {"muc_tieu": "1", "khai_niem": "giới", "vai_tro": "yeu_to", "bien": "gioi", "kieu": "nhi_phan"},
    ]
    ts = {"outcome": "xn_du", "group": "tuoi", "covariates": ["gioi"], "outcome_type": "poisson_pr"}
    if n_gan is not None:
        ts["n_imputations"] = n_gan
    pt = [{"id": "MT1", "vai": "chinh", "mo_ta": "Phân tích chính", "tham_so": ts},
          {"id": "NC_nam", "vai": "nhom_con", "mo_ta": "Tỷ lệ xn_du — gioi = 1 (nam)"},
          {"id": "NC_nu", "vai": "nhom_con", "mo_ta": "Tỷ lệ xn_du — gioi = 2 (nữ)"},
          {"id": "DN1", "vai": "do_nhay", "mo_ta": "ĐN1 — dạng albumin niệu"}]
    return KBB.NguCanh("cross_sectional", ["Yếu tố liên quan đến việc được xét nghiệm đủ"], bien, ma_tran, pt, 385)


def _chuong(n_gan=None) -> str:
    dong, loi = KBB.ve_chuong(KBB.dung_khung(_ngu_canh(n_gan)), 5, None, False)
    assert not loi, loi
    return "\n".join(dong)


def test_nhan_bien_giu_viet_tat_khi_chen_giua_cau():
    ch = _chuong()
    assert "uacr" not in ch
    assert "được xét nghiệm đủ UACR và creatinin năm 2026" in ch


def test_ghi_chu_nhom_nho_khong_tu_khang_dinh_kiem_dinh_tuong_tac():
    ch = _chuong()
    assert "kèm kiểm định tương tác" not in ch
    assert "phân tích nhóm nhỏ chỉ mang tính thăm dò." in ch


def test_gan_da_tri_them_cot_ca_du_du_lieu():
    ch = _chuong(20)
    assert "hiệu chỉnh (KTC 95%), gán đa trị" in ch
    assert "hiệu chỉnh (KTC 95%), ca đủ dữ liệu" in ch
    assert "gán đa trị (20 bộ dữ liệu)" in ch
    assert "trình bày ở cột cuối bảng mô hình đa biến" in ch


def test_khong_gan_da_tri_bang_giu_nguyen():
    ch = _chuong()
    assert "ca đủ dữ liệu" not in ch and "gán đa trị" not in ch


def test_n_imputations_khong_hop_le_khong_them_cot():
    for sai in (0, True, "20", -3):
        assert "ca đủ dữ liệu" not in _chuong(sai)
