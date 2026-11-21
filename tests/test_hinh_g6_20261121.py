"""Tự sinh biểu đồ kết quả G6 (`hinh_g6.py`, chặng 6b chương trình biểu đồ, bác sĩ 21/11/2026).

Dữ liệu là bộ giả lập TẤT ĐỊNH (numpy, hạt giống cố định) dựng cho test — không phải dữ liệu đề tài. Bộ nạp dữ liệu
được thay bằng hàm giả để test không phụ thuộc khoá G5; đường thật dùng `phan_tich_thiet_ke_dac_thu._doc_df_khoa`.
Kiểm: đúng loại hình theo kết cục × phơi nhiễm; số trên hình gộp/kinh tế TRÙNG số G6 đã tính; một hình lỗi không làm
hỏng hình khác; kiểm danh mục thiết kế báo hình bắt buộc còn thiếu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))

import hinh_g6 as HG  # noqa: E402
import phan_tich_thiet_ke_dac_thu as PT  # noqa: E402


@pytest.fixture(scope="module")
def du_lieu():
    import numpy as np
    import pandas as pd

    rng = np.random.default_rng(20261121)
    n = 240
    tuoi = rng.normal(55, 12, n).round(0)
    nhom = rng.choice(["A", "B", "C"], n)
    gioi = rng.integers(0, 2, n)
    cho = rng.gamma(4, 12, n).round(0)
    lp = -2 + 0.03 * (tuoi - 55) + 0.8 * (nhom == "B") + 0.015 * cho
    y_bin = (rng.random(n) < 1 / (1 + np.exp(-lp))).astype(int)
    y_ord = np.digitize(lp + rng.logistic(size=n), [-1.5, 0.0]) + 1
    y_cont = (120 + 0.5 * tuoi + 6 * (nhom == "C") + rng.normal(0, 10, n)).round(1)
    tg = rng.exponential(300, n).round(0) + 1
    bc = (rng.random(n) < 0.6).astype(int)
    benh = (rng.random(n) < 0.3).astype(int)
    xn = (benh * 1.2 + rng.normal(0, 1, n)).round(3)
    nhanh = rng.integers(0, 2, n)
    chi_phi = (2_000_000 + 600_000 * nhanh + rng.normal(0, 300_000, n)).round(0)
    hieu_qua = (0.70 + 0.05 * nhanh + rng.normal(0, 0.1, n)).round(4)
    ca = pd.DataFrame({"y_bin": y_bin, "y_ord": y_ord, "y_cont": y_cont, "nhom": nhom, "tuoi": tuoi, "gioi": gioi,
                       "cho": cho, "tg": tg, "bc": bc, "benh": benh, "xn": xn, "nhanh": nhanh, "chi_phi": chi_phi,
                       "hieu_qua": hieu_qua})
    ca.loc[[3, 17, 40], "tuoi"] = np.nan
    gop = pd.DataFrame({"nc": [f"NC{i}" for i in range(1, 7)], "a": [12, 8, 20, 5, 30, 9],
                        "n1": [100, 80, 150, 60, 200, 90],
                        "c": [20, 10, 28, 9, 41, 15], "n0": [100, 82, 148, 61, 205, 88]})
    return {"ca": ca, "gop": gop}


def _nap(du):
    def nap(study, can, loc):
        df = du["gop"] if "nc" in can else du["ca"]
        thieu = [c for c in can if c not in df.columns]
        if thieu:
            raise KeyError(f"thiếu cột {thieu}")
        return df.copy()

    return nap


PHAN_TICH = [
    {"id": "MT1_chinh", "vai": "chinh", "tham_so": {"outcome": "y_bin", "group": "nhom", "covariates": ["tuoi", "gioi"],
                                                    "hiep_bien_phan_loai": ["gioi"], "outcome_type": "binary"}},
    {"id": "SPL", "vai": "do_nhay", "tham_so": {"outcome": "y_bin", "group": "cho", "covariates": ["tuoi"]}},
    {"id": "ORD", "vai": "phu", "tham_so": {"outcome": "y_ord", "group": "cho", "covariates": ["tuoi"],
                                            "outcome_type": "ordinal"}},
    {"id": "ORDG", "vai": "phu", "tham_so": {"outcome": "y_ord", "group": "nhom", "outcome_type": "ordinal"}},
    {"id": "CONT", "vai": "phu", "tham_so": {"outcome": "y_cont", "group": "nhom", "outcome_type": "continuous"}},
    {"id": "SURV", "vai": "phu", "tham_so": {"time": "tg", "event": "bc", "group": "nhom"}},
    {"id": "TYLE", "vai": "mo_ta", "tham_so": {"ty_le": ["y_bin", "bc", "benh"]}},
    {"id": "CD", "vai": "phu", "tham_so": {"loai_dac_thu": "chan_doan", "tham_chieu": "benh", "chi_so": "xn",
                                           "nguong": 0.5}},
    {"id": "DB", "vai": "phu", "tham_so": {"loai_dac_thu": "du_bao", "outcome": "y_bin",
                                           "covariates": ["cho", "gioi"]}},
    {"id": "GOP", "vai": "phu", "tham_so": {"loai_dac_thu": "gop", "nhan_nghien_cuu": "nc", "su_kien_can_thiep": "a",
                                            "n_can_thiep": "n1", "su_kien_chung": "c", "n_chung": "n0"}},
    {"id": "KT", "vai": "phu", "tham_so": {"loai_dac_thu": "kinh_te", "nhom": "nhanh", "chi_phi": "chi_phi",
                                           "hieu_qua": "hieu_qua", "nguong_wtp": 20_000_000}},
    {"id": "LOI", "vai": "phu", "tham_so": {"outcome": "khong_co_cot", "group": "nhom"}},
    {"id": "TAY", "vai": "do_nhay", "chua_tu_dong": "partial PO — thống kê viên làm tay"},
]
CHI_MUC = {"phan_tich": [
    {"id": "MT1_chinh", "vai": "chinh", "mo_ta": "Tỷ lệ kết cục theo nhóm",
     "uoc_luong": {"or_tho": {"uoc_luong": 2.1, "ci_95": [1.2, 3.6], "p": 0.01},
                   "da_bien": {"variable": "nhom", "OR_adj": 2.3, "CI_95": [1.3, 4.0], "p": 0.004}}},
    {"id": "PR", "vai": "phu", "mo_ta": "Tỷ số tỷ lệ hiện mắc",
     "uoc_luong": {"poisson_pr": {"variable": "nhom", "PR_adj": 1.6, "CI_95": [1.1, 2.2], "p": 0.01}}},
]}


@pytest.fixture(scope="module")
def ket_qua(du_lieu, tmp_path_factory):
    d = tmp_path_factory.mktemp("de_tai")
    kq = HG.sinh("gia_lap_test", d, PHAN_TICH, CHI_MUC, "cross_sectional", nap=_nap(du_lieu))
    return d, kq


def _loai_cua(kq, pid):
    return {h["loai"] for h in kq["hinh"] if h["id"] == pid and h["trang_thai"] == "DA_VE"}


def test_dung_loai_hinh_theo_ket_cuc_va_phoi_nhiem(ket_qua):
    _, kq = ket_qua
    assert _loai_cua(kq, "MT1_chinh") == {"cot-ktc", "thieu"}
    assert _loai_cua(kq, "SPL") == {"spline"}
    assert _loai_cua(kq, "ORD") == {"xac-suat-thu-tu"}
    assert _loai_cua(kq, "ORDG") == {"likert"}
    assert _loai_cua(kq, "CONT") == {"phan-bo"}
    assert _loai_cua(kq, "SURV") == {"km"}
    assert _loai_cua(kq, "TYLE") == {"cot-ktc"}
    assert _loai_cua(kq, "CD") == {"roc", "phan-bo", "fagan"}
    assert _loai_cua(kq, "DB") == {"hieu-chuan", "roc", "dca"}
    assert _loai_cua(kq, "GOP") == {"forest", "bo-tung-nc"}  # < 10 nghiên cứu ⇒ không vẽ phễu
    assert _loai_cua(kq, "KT") == {"ce-plane", "ceac"}
    assert not any(h["id"] == "TAY" for h in kq["hinh"])


def test_hinh_loi_khong_lam_hong_hinh_khac_va_tep_ghi_du(ket_qua):
    d, kq = ket_qua
    loi = [h for h in kq["hinh"] if h["trang_thai"] == "LOI"]
    assert [h["id"] for h in loi] == ["LOI"] and "khong_co_cot" in loi[0]["ly_do"]
    for h in kq["hinh"]:
        if h["trang_thai"] == "DA_VE":
            png = d / h["tep"]
            assert png.exists() and png.with_suffix(".pdf").exists() and png.with_suffix(".json").exists(), h
    assert json.loads((d / HG.TEP_KQ).read_text(encoding="utf-8"))["dem"] == kq["dem"]


def test_forest_tho_hieu_chinh_tach_or_va_pr(ket_qua):
    d, kq = ket_qua
    tep = {h["tep"] for h in kq["hinh"] if h["id"] == "G6"}
    assert tep == {"bieu-bang/g6-tho-hieu-chinh.png", "bieu-bang/g6-tho-hieu-chinh-pr.png"}
    j_or = json.loads((d / "bieu-bang/g6-tho-hieu-chinh.json").read_text(encoding="utf-8"))
    assert j_or["thuoc_do"] == "OR" and {x["mo_hinh"] for x in j_or["dong"]} == {"Thô", "Hiệu chỉnh"}
    j_pr = json.loads((d / "bieu-bang/g6-tho-hieu-chinh-pr.json").read_text(encoding="utf-8"))
    assert j_pr["thuoc_do"] == "PR" and [x["uoc_luong"] for x in j_pr["dong"]] == [1.6]


def test_forest_hr_cox_va_beta_tuyen_tinh_moi_thuoc_do_mot_truc(tmp_path):
    """Thuần tập Cox (HR) và kết cục liên tục (β) — mỗi thước đo một hình, số đúng chỉ mục G6, β trên trục cộng."""
    cm = {"phan_tich": [
        {"id": "MT1_chinh", "vai": "chinh", "uoc_luong": {"hr_hieu_chinh": {"HR": 0.72, "CI_95": [0.6, 0.86],
                                                                             "p": 0.0004}}},
        {"id": "NC_nam", "vai": "nhom_con", "uoc_luong": {"hr_hieu_chinh": {"HR": 0.8, "CI_95": [0.6, 1.07],
                                                                             "p": 0.13}}},
        {"id": "HR_loi", "vai": "do_nhay", "uoc_luong": {"hr_hieu_chinh": {"HR": 0.9, "CI_95": [None, 1.2]}}},
        {"id": "LT", "vai": "phu", "uoc_luong": {"da_bien": {"variable": "nhom", "beta": -2.4,
                                                              "CI_95": [-3.9, -0.9], "p": 0.002}}}]}
    kq = HG.sinh("x", tmp_path, [], cm, None, nap=lambda s, c, loc: None)
    tep = {h["tep"] for h in kq["hinh"] if h["loai"] == "forest-uoc-luong"}
    assert tep == {"bieu-bang/g6-tho-hieu-chinh-hr.png", "bieu-bang/g6-tho-hieu-chinh-beta.png"}
    j_hr = json.loads((tmp_path / "bieu-bang/g6-tho-hieu-chinh-hr.json").read_text(encoding="utf-8"))
    assert j_hr["thuoc_do"] == "HR" and [x["uoc_luong"] for x in j_hr["dong"]] == [0.72, 0.8]  # KTC thiếu ⇒ bỏ
    j_b = json.loads((tmp_path / "bieu-bang/g6-tho-hieu-chinh-beta.json").read_text(encoding="utf-8"))
    assert j_b["thuoc_do"] == "β" and [x["uoc_luong"] for x in j_b["dong"]] == [-2.4]


def test_forest_gop_trung_rr_gop_cua_g6(ket_qua, du_lieu):
    d, _ = ket_qua
    g6 = PT.gop(du_lieu["gop"].to_dict("records"), "nc", "a", "n1", "c", "n0")
    j = json.loads((d / "bieu-bang/g6-gop-forest.json").read_text(encoding="utf-8"))
    assert abs(j["gop"]["uoc_luong"] - g6["rr_gop_ngau_nhien"]) < 1e-10
    assert abs(j["gop"]["ktc"][0] - g6["ci_95"][0]) < 1e-10 and abs(j["gop"]["ktc"][1] - g6["ci_95"][1]) < 1e-10


def test_forest_gop_dung_dl_nhu_g6_khi_co_khong_dong_nhat(tmp_path):
    """Dữ liệu KHÔNG đồng nhất (τ² > 0) — DL và REML cho kết quả khác nhau, forest phải trùng DL của G6."""
    import pandas as pd

    gop = pd.DataFrame({"nc": [f"NC{i}" for i in range(1, 7)], "a": [5, 30, 10, 40, 8, 25], "n1": [100] * 6,
                        "c": [20, 15, 30, 20, 25, 18], "n0": [100] * 6})
    pt = [{"id": "GOP", "vai": "phu", "tham_so": {"loai_dac_thu": "gop", "nhan_nghien_cuu": "nc",
                                                  "su_kien_can_thiep": "a", "n_can_thiep": "n1",
                                                  "su_kien_chung": "c", "n_chung": "n0"}}]
    HG.sinh("x", tmp_path, pt, None, None, nap=lambda s, c, loc: gop.copy())
    g6 = PT.gop(gop.to_dict("records"), "nc", "a", "n1", "c", "n0")
    j = json.loads((tmp_path / "bieu-bang/g6-gop-forest.json").read_text(encoding="utf-8"))
    assert j["gop"]["phuong_phap"] == "DL" and j["gop"]["tau2"] > 0.1
    assert abs(j["gop"]["uoc_luong"] - g6["rr_gop_ngau_nhien"]) < 1e-10


def _gop_rob(tmp_path, rob=(1, 1, 2, 3, 1, 2), tu_dien=True):
    import pandas as pd

    gop = pd.DataFrame({"nc": [f"NC{i}" for i in range(1, 7)], "a": [12, 8, 20, 5, 30, 9],
                        "n1": [100, 80, 150, 60, 200, 90], "c": [20, 10, 28, 9, 41, 15],
                        "n0": [100, 82, 148, 61, 205, 88], "rob2_tong": list(rob)})
    if tu_dien:
        (tmp_path / "G5_REDCap_dictionary_x.csv").write_text(
            "Variable / Field Name,Field Type,Field Label,\"Choices, Calculations, OR Slider Labels\"\n"
            "rob2_tong,radio,RoB 2 — đánh giá chung,\"1, Thấp | 2, Có lo ngại | 3, Cao\"\n", encoding="utf-8",
            newline="\n")
    pt = [{"id": "GOP", "vai": "chinh", "tham_so": {"loai_dac_thu": "gop", "nhan_nghien_cuu": "nc",
                                                    "su_kien_can_thiep": "a", "n_can_thiep": "n1",
                                                    "su_kien_chung": "c", "n_chung": "n0"}}]
    return HG.sinh("x", tmp_path, pt, None, "sr_ma", nap=lambda s, c, loc: gop.copy()), gop


def test_rob_tu_cot_rob_nhan_tu_dien_va_trong_so_forest(tmp_path):
    kq, gop = _gop_rob(tmp_path)
    assert _loai_cua(kq, "GOP") >= {"forest", "rob"}
    assert "rob" not in kq["kiem_danh_muc"]["thieu_bat_buoc"]  # sr_ma bắt buộc RoB — nay đã có
    j = json.loads((tmp_path / "bieu-bang/g6-gop-rob.json").read_text(encoding="utf-8"))
    f = json.loads((tmp_path / "bieu-bang/g6-gop-forest.json").read_text(encoding="utf-8"))
    assert j["cong_cu"] == "RoB 2" and j["mien"] == ["RoB 2 — đánh giá chung"]
    assert j["danh_gia"]["NC4"] == {"RoB 2 — đánh giá chung": "cao"}  # mã 3 → «Cao» theo từ điển G5
    w = {x["nghien_cuu"]: x["trong_so_pt"] for x in f["nghien_cuu"]}
    thap = sum(w[n] for n, v in zip(gop["nc"], gop["rob2_tong"]) if v == 1)
    assert abs(j["tom_tat_pt"]["RoB 2 — đánh giá chung"]["thap"] - thap) < 1e-6  # thanh tổng hợp có trọng số forest


def test_rob_loi_khong_lam_mat_forest(tmp_path):
    kq, _ = _gop_rob(tmp_path, rob=(1, 1, 9, 3, 1, 2), tu_dien=False)  # mã 9 không có nhãn ⇒ không nhận ra mức
    ds = {(h["loai"], h["trang_thai"]) for h in kq["hinh"] if h["id"] == "GOP"}
    assert ("forest", "DA_VE") in ds and ("rob", "LOI") in ds and ("rob", "DA_VE") not in ds
    assert (tmp_path / "bieu-bang/g6-gop-forest.png").is_file()


def test_mat_phang_ce_dung_cung_lan_lap_bootstrap_cua_g6(ket_qua, du_lieu):
    d, _ = ket_qua
    g6 = PT.kinh_te(du_lieu["ca"].to_dict("records"), "nhanh", "chi_phi", "hieu_qua", 20_000_000)
    j = json.loads((d / "bieu-bang/g6-kt-ce-plane.json").read_text(encoding="utf-8"))
    assert j["lap"] == g6["bootstrap"]["so_lap"]
    tai_1 = next(x for x in g6["ceac"] if x["boi_so"] == 1.0)["ty_le_chi_phi_hieu_qua"]
    assert abs(j["p_hieu_qua_chi_phi"] - tai_1) < 1e-12
    assert "lap" not in g6  # mặc định không trả các lần lặp (chỉ khi hinh_g6 xin)


def test_kiem_danh_muc_bao_so_do_luong_con_thieu_va_md(ket_qua):
    _, kq = ket_qua
    assert kq["kiem_danh_muc"]["thieu_bat_buoc"] == ["so_do_luong"]
    md = HG.md_bieu_do(kq)
    assert "## Biểu đồ kết quả (tự sinh)" in md and "so-do-luong" in md and "LỖI" in md


def test_loai_bien():
    import pandas as pd

    assert HG.loai_bien(pd.Series([0, 1, 1, None])) == "nhi_phan"
    assert HG.loai_bien(pd.Series([1, 2, 3, 2])) == "phan_loai"
    assert HG.loai_bien(pd.Series([0, 1, 2, 1])) == "phan_loai"  # 0/1/2 không phải nhị phân
    assert HG.loai_bien(pd.Series(["Nam", "Nữ"])) == "phan_loai"
    assert HG.loai_bien(pd.Series([1.5, 2.25, 3.0, 4.1, 5, 6, 7, 8, 9, 10])) == "lien_tuc"


def test_de_tai_mo_ta_ty_le_van_co_hinh_du_lieu_thieu_va_khong_doi_forest(du_lieu, tmp_path):
    pt = [{"id": "MT1_ty_le", "vai": "chinh", "tham_so": {"ty_le": ["y_bin", "bc"], "vars": ["tuoi"]}}]
    kq = HG.sinh("x", tmp_path, pt, None, "cross_sectional", nap=_nap(du_lieu))
    assert _loai_cua(kq, "MT1_ty_le") == {"cot-ktc", "thieu"}
    assert kq["kiem_danh_muc"]["thieu_bat_buoc"] == ["so_do_luong"]  # mô tả thuần: forest hồi quy chỉ «khi phù hợp»


def test_chu_thich_mang_mo_ta_phan_tich_sap(du_lieu, tmp_path):
    pt = [{"id": "NC_nam", "vai": "nhom_con", "mo_ta": "Nhóm nhỏ tiền định: nam",
           "tham_so": {"outcome": "y_bin", "group": "nhom"}},
          {"id": "NC_nu", "vai": "nhom_con", "mo_ta": "Nhóm nhỏ tiền định: nữ",
           "tham_so": {"outcome": "y_bin", "group": "nhom"}}]
    kq = HG.sinh("x", tmp_path, pt, None, None, nap=_nap(du_lieu))
    mt = [h["mo_ta"] for h in kq["hinh"] if h["trang_thai"] == "DA_VE"]
    assert mt[0].startswith("Nhóm nhỏ tiền định: nam — ") and mt[1].startswith("Nhóm nhỏ tiền định: nữ — ")
    assert len(set(mt)) == 2, "hai nhóm nhỏ không được trùng chú thích"


def test_thiet_ke_ngoai_danh_muc_khong_kiem(du_lieu, tmp_path):
    kq = HG.sinh("x", tmp_path, PHAN_TICH[:1], None, "thiet_ke_khac", nap=_nap(du_lieu))  # định tính nay có danh mục
    assert "ghi_chu" in kq["kiem_danh_muc"] and kq["dem"]["DA_VE"] == 2
