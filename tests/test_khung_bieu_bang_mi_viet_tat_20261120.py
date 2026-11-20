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


# ── Soát hình 20/11/2026: sơ đồ hồi cứu hồ sơ, forest nhóm nhỏ là tỷ lệ, nhãn không trùng ─────────────────────────
def _khung_ten(ngu, ten_chua):
    return next(k for m in KBB.dung_khung(ngu) for k in m.khung if ten_chua in (k.ten or ""))


def test_so_do_hoi_cuu_ho_so_khong_co_moi_va_tu_choi():
    ngu = _ngu_canh()
    ngu.hoi_cuu = True
    chu = str(_khung_ten(ngu, "Sơ đồ chọn").dac_ta)
    assert "mời tham gia" not in chu and "Từ chối" not in chu and "Hồ sơ trong khung chọn mẫu" in chu
    # khảo sát tiến cứu giữ nguyên các bước mời/từ chối
    assert "Từ chối tham gia" in str(_khung_ten(_ngu_canh(), "Sơ đồ chọn").dac_ta)


def test_forest_nhom_nho_ty_le_truc_phan_tram_va_nhan_khong_trung():
    ngu = _ngu_canh()
    ngu.phan_tich = [p for p in ngu.phan_tich if p["vai"] != "nhom_con"] + [
        {"id": f"NC{i}", "vai": "nhom_con", "tham_so": {"ty_le": ["xn_du"]},
         "mo_ta": f"Tỷ lệ KẾT CỤC CHÍNH — được xét nghiệm đủ UACR và creatinin năm 2026 — nhóm {i}"} for i in range(3)]
    kh = _khung_ten(ngu, "theo nhóm nhỏ")
    d = kh.dac_ta
    assert d["phan_tram"] is True and d["log"] is False and d["ref"] is None
    assert d["nhan"][:3] == ["Nhóm 0", "Nhóm 1", "Nhóm 2"] and len(set(d["nhan"])) == len(d["nhan"])
    assert kh.ten.startswith("Tỷ lệ được xét nghiệm đủ UACR")


def test_ngat_giu_lien_so_luong():
    assert "(n = …)" in KBB._ngat("Thiếu dữ liệu kết cục chính (n = …)", 30)


# ── Soát định dạng bảng 20/11/2026 (chiều): đơn vị, cột thừa, ghi chú nội bộ, cột so sánh, tiêu đề mục ──────────
def test_buoc_tang_theo_dac_ta_va_bien_chia_thang():
    tuoi = KBB.Bien("tuoi", "Tuổi (năm) tại lượt khám đầu tiên", "lien_tuc", [], "")
    assert KBB._buoc_tang(tuoi, {"group": "tuoi", "don_vi_phoi_nhiem": 10}, "tuoi") == "mỗi 10 năm tăng thêm"
    assert KBB._buoc_tang(tuoi, {}, "tuoi") == "mỗi năm tăng thêm"
    bmi = KBB.Bien("bmi_5", "BMI", "lien_tuc", [], "đơn vị 5 kg/m²")
    assert KBB._buoc_tang(bmi, {}, "bmi_5") == "mỗi 5 kg/m² tăng thêm"
    dem = KBB.Bien("so_luot", "Số lượt khám", "dem", [], "")
    assert KBB._buoc_tang(dem, {"don_vi_phoi_nhiem": True, "group": "so_luot"}, "so_luot") == "mỗi đơn vị tăng thêm"


def test_bang_lien_quan_ghi_buoc_tang_va_bo_ghi_chu_noi_bo():
    ngu = _ngu_canh()
    ngu.bien["xn_du"] = KBB.Bien("xn_du", "Không được xét nghiệm đủ", "nhi_phan", [("1", "Có"), ("0", "Không")],
                                 "biến phụ thuộc của MT3")
    ngu.bien["tuoi"] = KBB.Bien("tuoi", "Tuổi (năm) tại lượt khám đầu tiên", "lien_tuc", [], "")
    ngu.phan_tich[0]["tham_so"]["don_vi_phoi_nhiem"] = 10
    ch = "\n".join(KBB.ve_chuong(KBB.dung_khung(ngu), 5, None, False)[0])
    assert "biến phụ thuộc" not in ch
    assert "| Tuổi | mỗi 10 năm tăng thêm |" in ch and "mỗi đơn vị tăng" not in ch
    assert "| Có kết cục | Không có kết cục |" in ch and "Có kết cục: n (%)" not in ch


def test_bang_mo_ta_dung_don_vi_goc():
    ngu = _ngu_canh()
    ngu.bien["bmi_5"] = KBB.Bien("bmi_5", "BMI", "lien_tuc", [], "đơn vị 5 kg/m²")
    assert KBB._dong_mo_ta(ngu, "bmi_5", "BMI", 1)[0][0] == "BMI (kg/m²), TB ± ĐLC hoặc trung vị [KTPV]"


def test_bang_chi_ty_le_bo_cot_trung_bình_trung_vi():
    ngu = _ngu_canh()
    ngu.bien["egfr_nhom"] = KBB.Bien("egfr_nhom", "Nhóm eGFR", "thu_tu",
                                     [("1", "G1 (eGFR ≥ 90)"), ("2", "G2 (eGFR 60–89)")])
    kq = [{"bien": "xn_du", "khai_niem": ""}, {"bien": "egfr_nhom", "khai_niem": ""}]
    bang = KBB._khung_mo_ta_kq(ngu, 1, "Mô tả", kq)[0]
    assert bang.cot == ["Chỉ số", "n/N", "Tỷ lệ (%)", "KTC 95%"]
    assert all(len(d) == 4 for d in bang.dong)
    assert any("eGFR tính bằng mL/phút/1,73 m²" in g for g in bang.ghi_chu)
    kq_lt = kq + [{"bien": "tuoi", "khai_niem": ""}]
    assert "Trung vị [KTPV]" in KBB._khung_mo_ta_kq(ngu, 1, "Mô tả", kq_lt)[0].cot


def test_cot_so_sanh_ty_le_ghi_chenh_diem_phan_tram():
    ngu = _ngu_canh()
    ngu.phan_tich = [p for p in ngu.phan_tich if p["vai"] != "do_nhay"] + [
        {"id": "DN1", "vai": "do_nhay", "mo_ta": "ĐN1 — kết cục chính tính cả dạng khác",
         "tham_so": {"ty_le": ["xn_du"]}},
        {"id": "DN9", "vai": "do_nhay", "mo_ta": "ĐN9 — MT3 với biến chia nhóm",
         "tham_so": {"outcome": "xn_du", "outcome_type": "poisson_pr"}}]
    ch = _chuong_tu(ngu)
    dong_dn1 = next(d for d in ch.split("\n") if d.startswith("| ĐN1"))
    dong_dn9 = next(d for d in ch.split("\n") if d.startswith("| ĐN9"))
    assert "chênh … điểm %" in dong_dn1 and "cùng chiều" not in dong_dn1
    assert "cùng chiều / khác chiều" in dong_dn9
    assert "Cột cuối: với tỷ lệ ghi chênh lệch (điểm phần trăm)" in ch


def test_tieu_de_muc_tieu_ngan():
    assert KBB._ten_muc_tieu_ngan("MT1: Mô tả A (từ 2 lượt) tại B — tỷ lệ C (kết cục chính).") == "Mô tả A tại B"
    assert KBB._ten_muc_tieu_ngan("Phân tích yếu tố liên quan (thăm dò)") == "Phân tích yếu tố liên quan"


def test_mo_ta_dac_ta_doi_ngoac_kep_tieng_viet():
    ra = KBB._lam_sach_mo_ta(_ngu_canh(), "ĐN7 — tính cả thuốc ghi «đang dùng»")
    assert ra == "ĐN7 — tính cả thuốc ghi “đang dùng”"


def _chuong_tu(ngu) -> str:
    dong, loi = KBB.ve_chuong(KBB.dung_khung(ngu), 5, None, False)
    assert not loi, loi
    return "\n".join(dong)


def test_bang_da_bien_chi_gom_bien_mo_hinh_va_thu_bac_dang_so():
    ngu = _ngu_canh()
    ngu.bien["cho"] = KBB.Bien("cho", "Số quầy phải qua", "dem", [], "")
    ngu.bien["sk"] = KBB.Bien("sk", "Tự đánh giá sức khỏe", "thu_tu",
                              [("1", "Rất kém"), ("2", "Kém"), ("3", "Trung bình"), ("4", "Tốt"), ("5", "Rất tốt")])
    ngu.ma_tran += [{"muc_tieu": "1", "khai_niem": "số quầy", "vai_tro": "yeu_to", "bien": "cho", "kieu": "dem"},
                    {"muc_tieu": "1", "khai_niem": "tự đánh giá sức khỏe", "vai_tro": "yeu_to", "bien": "sk",
                     "kieu": "thu_tu"}]
    ts = ngu.phan_tich[0]["tham_so"]
    ts["covariates"] = ["gioi", "sk"]
    ts["hiep_bien_phan_loai"] = ["gioi"]
    kh = [k for m in KBB.dung_khung(ngu) for k in m.khung]
    da_bien = next(k for k in kh if k.ten.startswith("Mô hình đa biến"))
    don_bien = next(k for k in kh if k.ten.startswith("Phân tích đơn biến"))
    assert not any(d[0] == "Số quầy" for d in da_bien.dong)  # biến ngoài mô hình chỉ ở bảng đơn biến
    assert any(d[0] == "Số quầy" for d in don_bien.dong)
    assert ["Tự đánh giá sức khỏe", "mỗi mức tăng thêm"] == da_bien.dong[-1][:2]
    fp = next(k for k in kh if k.loai == "bieu_do" and "hiệu chỉnh" in k.ten)
    assert "Tự đánh giá sức khỏe (mỗi mức)" in fp.dac_ta["nhan"]
