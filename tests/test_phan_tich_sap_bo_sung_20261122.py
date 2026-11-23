"""22/11/2026 — phân tích SAP trước đây «chờ làm tay» chạy bằng máy: tools/phan_tich_sap_bo_sung.py (+ mã R) và nối vào
tools/chay_sap_g6.py (loai_bo_sung/cau_hinh, quy tắc bỏ biến thưa, quy tắc giảm tham số theo EPV).

Bác sĩ (22/11/2026): «việc máy làm được thì làm trọn, không để lại danh sách việc treo». Dữ liệu giả, không PII. Phần R
bỏ qua khi máy không có Rscript (không bao giờ coi là đạt).
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import cau_noi_r as CNR  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import chay_sap_g6 as CS  # noqa: E402
import phan_tich_sap_bo_sung as P  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

CO_R = shutil.which("Rscript") is not None


# ───────────────────────── kiểm cấu hình ─────────────────────────
@pytest.mark.parametrize("loai,ch", [
    ("bang_cheo", {"hang": "nhom_g", "cot": "nhom_a", "nhan_thieu_hang": "Chưa có", "nhan_thieu_cot": "Chưa có"}),
    ("ty_le_khau", {"khau": [{"nhan": "a", "su_kien": "x == 1", "mau_so": "y == 1"}]}),
    ("ty_le_huu_han", {"bien": "xn_du", "tep_khung": "so_khung_mau.csv", "khoa_khung": "N_khung_mau"}),
    ("tin_cay", {"thang": {"A": ["a1", "a2"], "G": ["g1", "g2", "g3"]}, "omega": ["G"], "ma_thieu": [7, 8, 9]}),
    ("thu_tu", {"outcome": "g1", "x": "cho", "covariates": ["k"], "cum": "ban", "bien_the": "tuong_tac",
                "z": "kv", "z_don_vi": 15}),
    ("trong_so", {"che_do": "gioi_han_bo_ve", "outcome": "g1", "nguong_hai_long": 4, "nguong_lech": 0.2,
                  "n_toi_thieu": 10, "bien_ngay": "ngay", "bien_khung": "khung", "cum": "ban",
                  "tep_n_tang": "his_tong_hop/N_tang_HIS.csv", "tep_bo_ve": "his_tong_hop/bo_ve_HIS.csv"}),
])
def test_cau_hinh_hop_le(loai, ch):
    assert P.kiem_cau_hinh(loai, ch) == []


@pytest.mark.parametrize("loai,ch,mau", [
    ("bang_cheo", {"hang": "a", "la": 1}, "không áp dụng"),
    ("bang_cheo", {}, "thiếu «hang»"),
    ("ty_le_khau", {"khau": [{"nhan": "a", "su_kien": "x ==", "mau_so": "y == 1"}]}, "su_kien"),
    ("ty_le_huu_han", {"bien": "x", "tep_khung": "../ngoai.csv", "khoa_khung": "N"}, "TƯƠNG ĐỐI"),
    ("tin_cay", {"thang": {"G": ["g1", "g2"]}, "omega": ["G"]}, "đúng 3 câu"),
    ("thu_tu", {"outcome": "g1", "x": "c", "covariates": [], "cum": "b", "bien_the": "tuong_tac"}, "z và z_don_vi"),
    ("thu_tu", {"outcome": "g1", "x": "c", "covariates": ["k"], "cum": "b", "bien_the": "rcs", "mi": 5}, "mi"),
    ("thu_tu", {"outcome": "g1", "x": "c", "covariates": ["k"], "cum": "b", "bien_the": "gop_muc"}, "nguong_gop"),
    ("trong_so", {"che_do": "gioi_han_bo_ve", "outcome": "g1", "nguong_hai_long": 4, "nguong_lech": 0.2,
                  "n_toi_thieu": 10, "bien_ngay": "n", "bien_khung": "k", "cum": "b", "tep_n_tang": "a.csv"},
     "tep_bo_ve"),
    ("don_bien", {"ket_cuc": "g1", "kieu_ket_cuc": "khac"}, "kieu_ket_cuc"),
    ("loai_la", {}, "loai_bo_sung"),
])
def test_cau_hinh_sai_bi_bat(loai, ch, mau):
    assert any(mau in x for x in P.kiem_cau_hinh(loai, ch)), P.kiem_cau_hinh(loai, ch)


def test_cot_can_gom_danh_sach_bien_va_bien_thay_the_epv():
    """Mô phỏng trọn lượt 22/11/2026 bắt: vif/ty_le_theo_muc khai `bien` dạng danh sách và quy tắc EPV thay bằng biến
    gộp mức — các cột đó phải vào danh sách cần tính phái sinh, không thì KeyError trên dữ liệu khoá."""
    assert {"a", "b"} <= set(P.cot_can("vif", {"bien": ["a", "b"]}))
    assert {"x", "y"} <= set(P.cot_can("ty_le_theo_muc", {"bien": ["x"], "ket_cuc": "y"}))
    c = P.cot_can("poisson_chia_nhom", {"outcome": "o", "group": "g", "covariates": ["dt"], "chia_nhom": ["g"],
                                        "quy_tac_epv": {"nguong": 10, "buoc": [{"thay": {"dt": "dt2"}}]}})
    assert "dt2" in c


# ───────────────────────── tính toán thuần ─────────────────────────
def test_bang_cheo_mot_va_hai_chieu_giu_o_thieu():
    df = pd.DataFrame({"g": [1, 1, 2, None, 3, 2], "a": [1, None, 2, 1, 1, 2]})
    m = P.bang_cheo(df, "g", nhan_thieu_hang="Chưa có")
    assert m["N"] == 6 and [x["muc"] for x in m["muc"]] == ["1", "2", "3", "Chưa có"]
    assert m["muc"][0]["n"] == 2 and m["muc"][0]["ci_95"] == P.wilson(2, 6)
    h = P.bang_cheo(df, "g", "a", "Chưa có G", "Chưa có A")
    assert h["N"] == 6 and h["muc_cot"] == ["1", "2", "Chưa có A"]
    o = {(x["hang"], x["cot"]): x["n"] for x in h["o"]}
    assert o[("1", "Chưa có A")] == 1 and o[("Chưa có G", "1")] == 1 and sum(o.values()) == 6
    khong_nhan = P.bang_cheo(df, "g", "a")
    assert khong_nhan["N"] == 4 and khong_nhan["bo_vi_thieu"] == 2


def test_ty_le_khau_bieu_thuc_va_mau_so():
    df = pd.DataFrame({"x": [1, 0, 1, 1, 0, None], "y": [1, 1, 1, 0, 1, 1], "c": [None, 1, 0, 0, 0, 0]})
    kq = P.ty_le_khau(df, [{"nhan": "k", "su_kien": "x == 1", "mau_so": "y == 1"},
                           {"nhan": "k2", "su_kien": "x == 1", "mau_so": "y == 1 and (la_thieu(c) or c != 1)"}],
                      lambda bt: P.danh_gia(df, bt))
    assert (kq[0]["n"], kq[0]["N"]) == (2, 5)
    assert (kq[1]["n"], kq[1]["N"]) == (2, 4) and kq[1]["ci_95"] == P.wilson(2, 4)


def test_ty_le_huu_han_co_mau_hieu_dung():
    kq = P.ty_le_huu_han(96, 385, 2000)
    assert kq["n_hieu_dung"] == pytest.approx(385 * 1999 / 1615)
    assert kq["ci_95_fpc"] == pytest.approx(P.wilson(96 / 385 * kq["n_hieu_dung"], kq["n_hieu_dung"]))
    assert kq["ci_95_fpc"][1] - kq["ci_95_fpc"][0] < kq["ci_95_khong_fpc"][1] - kq["ci_95_khong_fpc"][0]
    with pytest.raises(P.TuChoi):
        P.ty_le_huu_han(10, 385, 300)


def test_gop_muc_ket_cuc_ve_phia_giua_khong_gop_muc_cao_nhat():
    y = [1] * 5 + [2] * 30 + [3] * 40 + [4] * 12 + [5] * 3
    g = P.gop_muc_ket_cuc(y, 20)
    assert g["anh_xa"]["1"] == "2" and g["anh_xa"]["4"] == "3" and g["anh_xa"]["5"] == "5"
    assert g["so_muc_sau"] == 3
    g2 = P.gop_muc_ket_cuc([1] * 5 + [2] * 6 + [3] * 50 + [4] * 40 + [5] * 30, 20)
    assert g2["anh_xa"]["1"] == "3" and g2["anh_xa"]["2"] == "3" and g2["so_muc_sau"] == 3
    assert P.gop_muc_ket_cuc([1] * 30 + [2] * 30 + [3] * 30 + [4] * 30 + [5] * 30, 20)["nhat_ky"] == []


def test_quy_tac_bien_thua_chi_theo_phan_bo_cua_bien():
    df = pd.DataFrame({"hen": [1] * 19 + [2] * 100, "ut": [1] * 20 + [2] * 99})
    kq = P.quy_tac_bien_thua(df, ["hen", "ut"], 20)
    assert kq["bo"] == ["hen"] and kq["giu"] == ["ut"]
    ch = P.ap_bien_thua({"covariates": ["a", "hen", "ut"], "phan_loai": ["hen", "ut"]}, kq)
    assert ch["covariates"] == ["a", "ut"] and ch["phan_loai"] == ["ut"]


def test_quy_tac_epv_giam_dan_dung_khi_dat():
    r = np.random.default_rng(1)
    n = 400
    df = pd.DataFrame({"y": (r.random(n) < 0.2).astype(float), "x": r.normal(size=n),
                       "dt": r.integers(1, 5, n), "dt2": r.integers(1, 3, n), "pk": r.integers(1, 4, n),
                       "pk2": r.integers(1, 3, n), "so": r.integers(0, 5, n)})
    ts = {"outcome": "y", "group": "x", "covariates": ["dt", "pk", "so"], "hiep_bien_phan_loai": ["dt", "pk"]}
    q = {"nguong": 10, "buoc": [{"thay": {"dt": "dt2"}}, {"thay": {"pk": "pk2"}}, {"bo": ["so"]}]}
    it = int(min(df.y.sum(), n - df.y.sum()))
    moi, nk = P.quy_tac_epv(df, ts, q)
    assert nk["cac_buoc"][0]["so_tham_so"] == 1 + 3 + 2 + 1
    # it/7 ≈ 11 ⇒ đã đạt ngay ⇒ không bước nào áp
    assert (it / 7 >= 10) == (nk["buoc_ap"] == 0)
    moi2, nk2 = P.quy_tac_epv(df, ts, dict(q, nguong=it / 4.5))  # đạt sau bước 2 (4 tham số)
    assert nk2["buoc_ap"] == 2 and moi2["covariates"] == ["dt2", "pk2", "so"]
    moi3, nk3 = P.quy_tac_epv(df, ts, dict(q, nguong=1e9))  # không bao giờ đạt ⇒ giữ mô hình sau bước cuối
    assert nk3["buoc_ap"] == 3 and moi3["covariates"] == ["dt2", "pk2"] and not nk3["dat_nguong"]


def test_omega_ba_cau_nghiem_dong_va_heywood():
    r = np.random.default_rng(3)
    f = r.normal(size=5000)
    x = np.column_stack([0.8 * f + 0.6 * r.normal(size=5000) for _ in range(3)])
    om = P.omega_ba_cau(x)
    assert om == pytest.approx(2.4 ** 2 / (2.4 ** 2 + 3 * 0.36), abs=0.02)
    y = np.column_stack([f, -f + 0.1 * r.normal(size=5000), f])
    assert P.omega_ba_cau(y) is None
    # hiệp phương sai đều dương nhưng λ₁² = 0,81/0,65 > s₁₁ ⇒ θ₁ âm (Heywood) ⇒ không bịa số
    hw = r.multivariate_normal([0, 0, 0], [[1, 0.9, 0.9], [0.9, 1, 0.65], [0.9, 0.65, 1]], size=20000)
    assert P.omega_ba_cau(hw) is None


def test_tuong_quan_ktc_chua_uoc_luong():
    r = np.random.default_rng(2)
    x = r.normal(size=200)
    df = pd.DataFrame({"a": x, "b": x + r.normal(size=200)})
    kq = P.tuong_quan(df, "a", "b")
    lo, hi = kq["spearman"]["ci_95"]
    assert lo < kq["spearman"]["rho"] < hi and kq["pearson"]["ci_95"][0] < kq["pearson"]["r"]
    with pytest.raises(P.TuChoi):
        P.tuong_quan(df.head(3), "a", "b")


def test_dap_ung_cong_thuc_ty_le():
    so = [{"loai_dong": "tong_hop", "so_duoc_chon": "60", "so_khong_vao_kham": "5", "so_khong_du_tieu_chuan": "3",
           "so_khong_gap": "4", "so_moi": "48", "so_dong_y": "40", "so_tu_choi": "2"},
          {"loai_dong": "tu_choi", "nhom_tuoi_uoc_luong": "1", "gioi": "2"},
          {"loai_dong": "tu_choi", "nhom_tuoi_uoc_luong": "3", "gioi": "1"}]
    df = pd.DataFrame({"hl": [1] * 36 + [0] * 3, "nt": [1, 2, 3] * 13, "gt": [1, 2, 1] * 13})
    ch = {"dieu_kien_hop_le": "hl == 1", "so_sanh": {"tuoi": {"mau": "nt", "so": "nhom_tuoi_uoc_luong"}}}
    kq = P.dap_ung(so, df, ch, lambda bt: P.danh_gia(df, bt))
    t = kq["ty_le"]
    assert t["khong_gap_duoc"]["ty_le"] == pytest.approx(4 / 55)
    assert t["dap_ung_chung"]["ty_le"] == pytest.approx(36 / 52)
    assert t["hoan_thanh_phieu"]["ty_le"] == pytest.approx(39 / 40) and "canh_bao" not in kq
    assert kq["so_sanh_tu_choi_tham_gia"]["tuoi"]["tu_choi"]["muc"]["1"]["n"] == 1
    with pytest.raises(P.KhongDoDuoc):
        P.dap_ung([{"loai_dong": "tu_choi"}], df, {"dieu_kien_hop_le": "hl == 1", "so_sanh": {}}, lambda b: None)


def test_dong_thuan_kappa_va_chi_so():
    a = pd.DataFrame({"id": range(10), "x": [1, 1, 1, 1, 0, 0, 0, 0, 1, 0], "d": [3, 2, 5, 1, 0, 4, 2, 2, 6, 1]})
    b = pd.DataFrame({"id": range(10), "x": [1, 1, 1, 0, 0, 0, 0, 1, 1, 0], "d": [3, 2, 4, 1, 0, 4, 2, 3, 6, 1]})
    kq = P.dong_thuan(a, b, {"khoa": "id", "bien_phan_loai": ["x"], "bien_dem": ["d"], "so_lap": 200, "hat_giong": 1})
    x = kq["bien_phan_loai"]["x"]
    assert x["dong_thuan"] == pytest.approx(0.8) and x["kappa"] == pytest.approx(0.6)
    assert x["dong_thuan_duong"] == pytest.approx(8 / 10) and x["dong_thuan_am"] == pytest.approx(8 / 10)
    assert x["chi_so_ty_le_hien_mac"] == 0 and x["chi_so_lech"] == 0
    assert kq["truong"]["d"]["dong_thuan"] == 8 and kq["bien_dem"]["d"]["icc_2_1"] > 0.8
    a["dtc"] = [1] * 8 + [0, 0]
    b["dtc"] = [1] * 8 + [0, 1]
    ch = {"khoa": "id", "bien_phan_loai": ["x"], "bien_dem": ["d"], "so_lap": 50, "hat_giong": 1,
          "dieu_kien_a": "dtc == 1", "nhom_phu": {"nhan": "sàng lọc lại", "dieu_kien_a": "dtc == 0", "bien": ["dtc"]}}
    k2 = P.dong_thuan(a, b, ch, lambda bt: P.danh_gia(a, bt))
    assert k2["n_cap"] == 8 and k2["bien_phan_loai"]["x"]["n"] == 8
    assert k2["nhom_phu"]["n"] == 2 and k2["nhom_phu"]["bien"]["dtc"] == {"dong_thuan": 1, "n": 2}


def test_don_bien_chon_dung_kiem_dinh_va_hieu_ung():
    r = np.random.default_rng(4)
    n = 300
    df = pd.DataFrame({"g1": r.integers(1, 6, n), "gt": r.integers(1, 3, n), "kg": r.integers(1, 5, n),
                       "t": r.normal(50, 10, n), "nhi": r.integers(0, 2, n)})
    kq = P.don_bien(df, {"ket_cuc": "g1", "kieu_ket_cuc": "thu_tu", "yeu_to_phan_loai": ["gt", "kg"],
                         "yeu_to_lien_tuc": ["t"], "so_lap": 50, "hat_giong": 1})
    assert kq["yeu_to"]["gt"]["kiem_dinh"]["ten"] == "Mann–Whitney"
    assert 0 < kq["yeu_to"]["gt"]["hieu_ung"]["uoc_luong"] < 1
    assert kq["yeu_to"]["kg"]["kiem_dinh"]["ten"] == "Kruskal–Wallis"
    assert kq["yeu_to"]["t"]["hieu_ung"]["ten"] == "ρ Spearman"
    k3 = P.don_bien(df.assign(t15=df.t), {"ket_cuc": "g1", "kieu_ket_cuc": "thu_tu", "yeu_to_phan_loai": ["kg"],
                                          "yeu_to_lien_tuc": ["t15"], "don_vi": {"t15": 10}, "nguong_hai_long": 4})
    assert set(k3["yeu_to"]["kg"]["cor_tho"]) == {"kg_2", "kg_3", "kg_4"}
    assert sum(v["N"] for v in k3["yeu_to"]["kg"]["hai_long_theo_muc"].values()) == n
    d10, _ = RSA.mo_rong_bien_gia(df.assign(t15=df.t / 10), [])
    ref = RSA.ordinal_model(d10, "g1", "t15", [])["results"][0]["OR_adj"]
    assert k3["yeu_to"]["t15"]["cor_tho"]["t15"]["uoc_luong"] == ref and k3["yeu_to"]["t15"]["cor_tho_don_vi"] == 10
    kb = P.don_bien(df, {"ket_cuc": "nhi", "kieu_ket_cuc": "nhi_phan", "yeu_to_phan_loai": ["gt"]})
    assert kb["yeu_to"]["gt"]["hieu_ung"]["ten"].startswith("OR")


def test_so_sanh_hai_nhom_ten_bien_rieng():
    df = pd.DataFrame({"dk": [1, 1, 0, 0, 0], "lt": [0, 0, 0, 0, 1], "tuoi": [60, 70, None, None, None],
                       "sl_tuoi": [None, None, None, None, 55], "gioi": [1, 2, None, None, None],
                       "sl_gioi": [None, None, None, None, 2]})
    ch = {"nhom_a": {"nhan": "loại", "dieu_kien": "lt == 1", "bien": {"tuoi": "sl_tuoi", "gioi": "sl_gioi"}},
          "nhom_b": {"nhan": "mẫu", "dieu_kien": "dk == 1", "bien": {"tuoi": "tuoi", "gioi": "gioi"}},
          "bien_phan_loai": ["gioi"], "bien_lien_tuc": ["tuoi"]}
    kq = P.so_sanh_hai_nhom(df, ch, lambda bt: P.danh_gia(df, bt))
    assert kq["nhom"]["nhom_a"]["n"] == 1 and kq["nhom"]["nhom_a"]["bien"]["tuoi"]["trung_vi"] == 55
    assert kq["nhom"]["nhom_b"]["bien"]["gioi"]["muc"]["1"]["n"] == 1


def test_vif_va_ty_le_theo_muc():
    r = np.random.default_rng(5)
    a = r.normal(size=300)
    df = pd.DataFrame({"a": a, "b": a + 0.05 * r.normal(size=300), "c": r.integers(1, 4, 300),
                       "y": (r.random(300) < 0.3).astype(float)})
    v = P.he_so_phong_dai_phuong_sai(df, ["a", "b", "c"], ["c"])
    assert v["vif"]["a"] > 5 and "a" in v["vif_tren_5"] and "c" in v["gvif"]
    t = P.ty_le_theo_muc(df, ["c"], "y")
    assert sum(m["N"] for m in t["bien"]["c"]) == 300


def test_poisson_chia_nhom_cung_tap_ca():
    r = np.random.default_rng(6)
    n = 500
    df = pd.DataFrame({"y": (r.random(n) < 0.6).astype(float), "tuoi": r.normal(60, 10, n).round(),
                       "bmi": r.normal(24, 3, n), "g": r.integers(1, 3, n)})
    df.loc[:10, "bmi"] = None
    kq = P.poisson_chia_nhom(df, {"outcome": "y", "group": "tuoi", "don_vi_phoi_nhiem": 10,
                                  "covariates": ["bmi", "g"], "hiep_bien_phan_loai": ["g"],
                                  "chia_nhom": ["tuoi", "bmi"]})
    assert kq["tuyen_tinh"]["n"] == kq["chia_nhom"]["n"] == kq["n_ca_du"] == n - 11
    assert {"tuoi_q_2", "bmi_q_4"} <= {x["variable"] for x in kq["chia_nhom"]["results"]}
    df["g2"] = (df["g"] == 2).astype(float)
    kq2 = P.poisson_chia_nhom(df, {"outcome": "y", "group": "tuoi", "covariates": ["bmi", "g"],
                                   "hiep_bien_phan_loai": ["g"], "chia_nhom": ["tuoi"],
                                   "quy_tac_epv": {"nguong": 1e9, "buoc": [{"bo": ["bmi"]}]}})
    assert kq2["quy_tac_epv"]["buoc_ap"] == 1 and kq2["n_ca_du"] == n
    assert "bmi" not in {x["variable"] for x in kq2["chia_nhom"]["results"]}


def test_diem_anh_huong_cook_va_gop_muc_thua():
    r = np.random.default_rng(7)
    n = 200
    df = pd.DataFrame({"y": r.integers(1, 6, n).astype(float), "x": r.normal(size=n)})
    df.loc[0, ["y", "x"]] = [5, 12.0]
    giu, ng = P.danh_dau_anh_huong(df, "y", ["x"], [])
    assert ng == pytest.approx(4 / n) and giu.iloc[0] == 0
    s = pd.Series([1, 2, 2, 7, 6, 6] + [3] * 30, dtype=float)
    moi, nk = P.gop_muc_thua_yeu_to(s, 2, {"1": "2", "7": "6"})
    assert moi.iloc[0] == 2.0 and moi.iloc[3] == 6.0 and len(nk) == 2


# ───────────────────────── nối vào chay_sap_g6 ─────────────────────────
COT_TD = ["Variable / Field Name", "Form Name", "Field Type", "Field Label", "Choices, Calculations, OR Slider Labels",
          "Text Validation Type OR Show Slider Number", "Identifier?", "Field Annotation"]


def _de_tai(goc: Path) -> Path:
    d = goc / "exports" / "BS"
    (d / "05_clean_locked").mkdir(parents=True)
    r = np.random.default_rng(22)
    n = 240
    df = pd.DataFrame({"g1": r.integers(1, 6, n), "cho": r.uniform(5, 150, n).round(1), "kg": r.integers(1, 4, n),
                       "hen": np.where(np.arange(n) < 10, 1, 2), "ban": r.integers(1, 21, n)})
    k = d / "05_clean_locked" / "k.csv"
    df.to_csv(k, index=False)
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps({
        "locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
        "lock_date": "2026-11-22", "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}), encoding="utf-8",
        newline="\n")
    with open(d / "G5_REDCap_dictionary_BS.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(COT_TD)
        for t, loai, lc in [("g1", "radio", "1, a | 2, b | 3, c | 4, d | 5, e"), ("cho", "text", ""),
                            ("kg", "radio", "1, a | 2, b | 3, c"), ("hen", "radio", "1, Có | 2, Không"),
                            ("ban", "text", "")]:
            w.writerow([t, "f", loai, t, lc, "", "", ""])
    (d / "G4_A5_SAP_FINAL_BS.md").write_text("# SAP\n### §4 PHÂN TÍCH CHÍNH\n- **Phương pháp:** thứ tự\n",
                                              encoding="utf-8", newline="\n")
    return d


def _dac_ta(d: Path, phan_tich: list) -> dict:
    sap = d / "G4_A5_SAP_FINAL_BS.md"
    dt = {"nguon_sap": sap.name, "sha256_sap": hashlib.sha256(sap.read_bytes()).hexdigest(), "phan_tich": phan_tich}
    dt["nguoi_duyet"] = f"THONG_KE_VIEN:T:2026-11-22:{CS.dau_dac_ta(dt)}"
    (d / CS.TEP_DAC_TA).write_text(json.dumps(dt, ensure_ascii=False), encoding="utf-8", newline="\n")
    return dt


CHINH = {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "thứ tự",
         "tham_so": {"outcome": "g1", "group": "cho", "covariates": ["kg", "hen"],
                     "hiep_bien_phan_loai": ["kg", "hen"], "outcome_type": "ordinal", "cot_cum": "ban",
                     "bien_thua": {"bien": ["hen"], "toi_thieu": 20}}}
BANG = {"id": "bang", "vai": "mo_ta", "sap_muc": "§3", "mo_ta": "phân bố G1",
        "tham_so": {"loai_bo_sung": "bang_cheo", "cau_hinh": {"hang": "g1"}}}


def test_kiem_dac_ta_nhan_loai_bo_sung_va_bat_sai(tmp_path):
    d = _de_tai(tmp_path)
    assert CS.kiem_dac_ta(d, _dac_ta(d, [CHINH, BANG]))["loi"] == []
    sai = dict(BANG, tham_so={"loai_bo_sung": "bang_cheo", "cau_hinh": {"hang": "g1"}, "outcome": "g1"})
    assert any("không áp dụng cho phân tích bổ sung" in x for x in CS.kiem_dac_ta(d, _dac_ta(d, [CHINH, sai]))["loi"])
    sai2 = dict(BANG, tham_so={"loai_bo_sung": "bang_cheo"})
    assert any("đi cùng nhau" in x for x in CS.kiem_dac_ta(d, _dac_ta(d, [CHINH, sai2]))["loi"])
    t = json.loads(json.dumps(CHINH))
    t["tham_so"]["bien_thua"]["bien"] = ["khac"]
    assert any("bien_thua chỉ áp" in x for x in CS.kiem_dac_ta(d, _dac_ta(d, [t, BANG]))["loi"])
    e = json.loads(json.dumps(CHINH))
    e["tham_so"]["quy_tac_epv"] = {"nguong": 10, "buoc": [{"bo": ["khong_co"]}]}
    assert any("quy_tac_epv thay/bỏ" in x for x in CS.kiem_dac_ta(d, _dac_ta(d, [e, BANG]))["loi"])


def test_doi_so_bo_sung_va_bo_qua_bien_thua():
    ds = CS.doi_so_run_stats(BANG)
    assert ds[:2] == ["--loai", "bang_cheo"] and json.loads(ds[3]) == {"hang": "g1"}
    assert "--bien-thua" not in " ".join(CS.doi_so_run_stats(CHINH)) and "bien_thua" not in " ".join(
        CS.doi_so_run_stats(CHINH))


def _vao_tien_trinh(monkeypatch, goc: Path, d: Path):
    man = json.loads((d / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", goc)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda s, g: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda study: (True, "giả lập"))
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda s, _d: man)
    monkeypatch.setattr(S, "EXPORTS", goc / "exports")
    monkeypatch.setattr(CS, "BASE", goc)
    goi: list[list[str]] = []

    def chay_trong(lenh, **kw):
        goi.append(lenh)
        out, err, ma = io.StringIO(), io.StringIO(), 0
        cu = sys.argv
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                if lenh[1].endswith("phan_tich_sap_bo_sung.py"):
                    ma = P.main(lenh[2:])
                else:
                    sys.argv = ["run_stats_analysis.py", *lenh[2:]]
                    RSA.main()
        except SystemExit as e:
            ma = e.code or 0
        finally:
            sys.argv = cu
        return subprocess.CompletedProcess(lenh, ma, out.getvalue(), err.getvalue())

    monkeypatch.setattr(CS.subprocess, "run", chay_trong)
    return goi


def test_chay_bien_thua_bo_bien_va_bo_sung_ghi_tom_tat(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    _dac_ta(d, [CHINH, BANG])
    goi = _vao_tien_trinh(monkeypatch, tmp_path, d)
    with contextlib.redirect_stdout(io.StringIO()):
        assert CS.main(["chay", "--study", "BS", "--khong-ve"]) == 0
    cm = json.loads((d / CS.TEP_KQ_JSON).read_text(encoding="utf-8"))
    chinh = next(x for x in cm["phan_tich"] if x["id"] == "chinh")
    assert chinh["bien_thua"]["bo"] == ["hen"] and chinh["trang_thai"] == "DA_CHAY"
    lenh_chinh = next(lenh for lenh in goi if lenh[1].endswith("run_stats_analysis.py"))
    assert lenh_chinh[lenh_chinh.index("--covariates") + 1] == "kg"
    assert lenh_chinh[lenh_chinh.index("--hiep-bien-phan-loai") + 1] == "kg"
    tom = json.loads((d / "G6_bang_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["loai_bo_sung"] == "bang_cheo" and tom["bo_sung"]["N"] == 240
    assert next(x for x in cm["phan_tich"] if x["id"] == "bang")["uoc_luong"]["bo_sung"]["loai"] == "bang_cheo"


def test_chay_quy_tac_epv_doi_bien_truoc_khi_chay(tmp_path, monkeypatch):
    d = _de_tai(tmp_path)
    t = {"id": "chinh", "vai": "chinh", "sap_muc": "§4", "mo_ta": "poisson",
         "tham_so": {"outcome": "nhi", "group": "cho", "covariates": ["kg", "hen"], "hiep_bien_phan_loai": ["kg"],
                     "outcome_type": "poisson_pr", "quy_tac_epv": {"nguong": 1e6, "buoc": [{"bo": ["hen"]}]}}}
    df = pd.read_csv(d / "05_clean_locked" / "k.csv")
    df["nhi"] = (df["g1"] >= 4).astype(int)
    k = d / "05_clean_locked" / "k.csv"
    df.to_csv(k, index=False)
    man = json.loads((d / "DATA_LOCK_manifest.json").read_text(encoding="utf-8"))
    man["sha256"] = hashlib.sha256(k.read_bytes()).hexdigest()
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps(man), encoding="utf-8", newline="\n")
    with open(d / "G5_REDCap_dictionary_BS.csv", "a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow(["nhi", "f", "radio", "nhi", "0, k | 1, c", "", "", ""])
    _dac_ta(d, [t])
    goi = _vao_tien_trinh(monkeypatch, tmp_path, d)
    with contextlib.redirect_stdout(io.StringIO()):
        CS.main(["chay", "--study", "BS", "--khong-ve"])
    cm = json.loads((d / CS.TEP_KQ_JSON).read_text(encoding="utf-8"))
    assert cm["phan_tich"][0]["quy_tac_epv"]["buoc_ap"] == 1
    lenh = goi[0]
    assert lenh[lenh.index("--covariates") + 1] == "kg"


# ───────────────────────── R (bỏ qua khi máy không có Rscript) ─────────────────────────
def _gia_lap(n=500, K=25, seed=1, x_m=-0.01):
    r = np.random.default_rng(seed)
    cum = r.integers(1, K + 1, n)
    u = r.normal(0, 0.6, K)[cum - 1]
    x = r.gamma(2, 20, n) + r.gamma(2, 15, K)[cum - 1]  # phơi nhiễm có thành phần theo cụm ⇒ sai số chuẩn cụm khác
    tuoi = r.normal(50, 15, n).round()
    gioi = r.integers(1, 3, n)
    m = np.digitize(x_m * x + r.logistic(size=n), [-2, -1, 0.5, 2]) + 1
    lat = -0.02 * x + 0.01 * tuoi + 0.3 * (gioi == 2) + 0.4 * m + u + r.logistic(size=n)
    y = np.digitize(lat, [-0.5, 0.5, 2, 3.5]) + 1
    return pd.DataFrame({"g1": y.astype(float), "cho": x, "tuoi": tuoi, "gioi": gioi.astype(float),
                         "ban": cum.astype(str), "m": m.astype(float), "nhi": (y >= 4).astype(float)})


def _chay_r(loai, ch, df, tmp_path):
    ch_r, df_r, cot, nk = P.chuan_bi_r(loai, ch, df)
    (tmp_path / "s.R").write_text(CNR.kich_ban_bo_sung(loai), encoding="utf-8", newline="\n")
    df_r[cot].to_csv(tmp_path / "d.csv", index=False)
    (tmp_path / "c.json").write_text(json.dumps(dict(ch_r, goi_can=list(CNR.GOI_CAN_BO_SUNG[loai]))), encoding="utf-8",
                                     newline="\n")
    r = subprocess.run(["Rscript", "--vanilla", str(tmp_path / "s.R"), str(tmp_path / "d.csv"),
                        str(tmp_path / "k.json"), str(tmp_path / "c.json")], capture_output=True, text=True)
    if r.returncode != 0 and P.goi_r_thieu(r.stderr):  # như máy không có R: không đo được, không phải «trượt»
        pytest.skip(f"R thiếu gói {P.goi_r_thieu(r.stderr)} — không đo được")
    assert r.returncode == 0, r.stderr[-1500:]
    return json.loads((tmp_path / "k.json").read_text(encoding="utf-8")), nk


CO_SO = {"outcome": "g1", "x": "cho", "x_don_vi": 15, "covariates": ["tuoi", "gioi"], "phan_loai": ["gioi"],
         "cum": "ban"}


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_r_thu_tu_thuong_khop_mo_hinh_chinh_python(tmp_path):
    df = _gia_lap()
    kq, _ = _chay_r("thu_tu", dict(CO_SO, bien_the="thuong", kiem_po=True), df, tmp_path)
    d, bg = RSA.mo_rong_bien_gia(df.assign(cho=df.cho / 15), ["gioi"])
    py = RSA.ordinal_model(d, "g1", "cho", ["tuoi", "gioi_2"], cluster_col="ban")
    or_py = next(x for x in py["results"] if x["variable"] == "cho")
    assert kq["x"]["cho"]["uoc_luong"] == pytest.approx(or_py["OR_adj"], abs=2e-3)
    t = float(__import__("scipy").stats.t.ppf(0.975, py["cluster"]["so_cum"] - 1))
    se_py = (math.log(or_py["CI_95"][1]) - math.log(or_py["CI_95"][0])) / (2 * t)
    assert kq["x"]["cho"]["se"] == pytest.approx(se_py, rel=0.03)  # sandwich theo cụm CR1 như Python
    assert set(kq["brant"]["theo_bien"]) == {"cho", "tuoi", "gioi_2"}


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_r_rcs_tuong_tac_va_phan_vi(tmp_path):
    df = _gia_lap()
    rcs, _ = _chay_r("thu_tu", dict(CO_SO, bien_the="rcs"), df, tmp_path)
    assert 0 <= rcs["p_phi_tuyen"] <= 1 and rcs["or_p75_so_p25"]["uoc_luong"] < 1
    assert rcs["diem_phan_vi"]["p50"] == pytest.approx(float(np.median(df.cho)), rel=1e-6)
    tt, _ = _chay_r("thu_tu", dict(CO_SO, bien_the="tuong_tac", z="tuoi", z_don_vi=10), df, tmp_path)
    assert set(tt["or_x_tai_z"]) == {"p25", "p50", "p75"}
    pv, nk = _chay_r("thu_tu", dict(CO_SO, bien_the="phan_vi"), df, tmp_path)
    assert list(pv["nhom_phan_vi"]) == ["Q2 so với Q1", "Q3 so với Q1", "Q4 so với Q1"]
    assert pv["nhom_phan_vi"]["Q4 so với Q1"]["uoc_luong"] < pv["nhom_phan_vi"]["Q2 so với Q1"]["uoc_luong"]


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_r_ppo_dau_he_so_danh_nghia_dung_chieu(tmp_path):
    """Dữ liệu sinh theo giả định tỷ lệ odds: ép giới «vi phạm» (ngưỡng Brant = 1) ⇒ OR theo từng ngưỡng của giới phải
    cùng chiều và gần OR chung (đúng dấu exp(−hệ số danh nghĩa))."""
    df = _gia_lap(n=1500)
    kq, _ = _chay_r("ppo", dict(CO_SO, nguong_brant=1.0, so_lap=20, hat_giong=1), df, tmp_path)
    theo = {k: v["or"] for k, v in kq["theo_nguong"].items() if k.startswith("gioi_2@")}
    assert len(theo) == 4 and all(v > 1 for v in theo.values())
    assert math.exp(0.3) * 0.5 < np.median(list(theo.values())) < math.exp(0.3) * 2


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_r_hon_hop_firth_va_trung_gian(tmp_path):
    df = _gia_lap()
    hh, _ = _chay_r("hon_hop", dict(CO_SO, nguong_cum=30), df, tmp_path)
    assert hh["so_cum"] == 25 and hh["la_phan_tich_chinh"] is True and 0 < hh["icc_tiem_an"] < 1
    fi, _ = _chay_r("firth", dict(CO_SO, outcome="nhi", muc_bien_co_epv=0, nguong_epv=1e6), df, tmp_path)
    assert fi["quy_tac"] == "firth" and fi["firth"]["uoc_luong"] < 1
    fi2, _ = _chay_r("firth", dict(CO_SO, outcome="nhi", muc_bien_co_epv=0, nguong_epv=1), df, tmp_path)
    assert fi2["quy_tac"] == "hop_ly_cuc_dai"
    tg, _ = _chay_r("trung_gian", dict(CO_SO, m="m", nguong_hai_long=4, so_mo_phong=100, hat_giong=1),
                    _gia_lap(x_m=-0.04), tmp_path)
    u = tg["uoc_luong"]
    # thời gian chờ ↑ ⇒ đánh giá so với mong đợi ↓ ⇒ hài lòng ↓: tác động gián tiếp âm ở CẢ hai mức phơi nhiễm
    assert u["acme_dieu_kien_x0"]["uoc_luong"] < 0 and u["acme_dieu_kien_x1"]["uoc_luong"] < 0
    assert u["tong"]["uoc_luong"] == pytest.approx(u["acme"]["uoc_luong"] + u["ade"]["uoc_luong"], abs=0.01)
    assert tg["do_nhay"]["100%"]["acme"]["uoc_luong"] == 0


@pytest.mark.skipif(not CO_R, reason="máy không có Rscript")
def test_r_trong_so_ba_che_do(tmp_path):
    df = _gia_lap()
    r = np.random.default_rng(9)
    df["ngay"] = r.integers(1, 6, len(df)).astype(float)
    df["khung"] = r.integers(1, 5, len(df)).astype(float)
    his = tmp_path / "N.csv"
    pd.DataFrame([{"ngay": a, "khung": b, "N_h": 300 if b != 4 else 900} for a in range(1, 6)
                  for b in range(1, 5)]).to_csv(his, index=False)
    bv = tmp_path / "bv.csv"
    pd.DataFrame([{"luot_lay_so": 10000, "luot_bo_ve": 500, "cho_trung_vi": 80, "cho_p25": 50,
                   "cho_p75": 120}]).to_csv(bv, index=False)
    ch = dict(CO_SO, nguong_hai_long=4, nguong_lech=0.2, n_toi_thieu=10, bien_ngay="ngay", bien_khung="khung",
              tep_n_tang=str(his), tep_bo_ve=str(bv))
    kh, _ = _chay_r("trong_so", dict(ch, che_do="kich_hoat"), df, tmp_path)
    assert kh["quy_tac"]["kich_hoat"] is True and "svyolr" in kh
    gh, _ = _chay_r("trong_so", dict(ch, che_do="gioi_han_bo_ve"), df, tmp_path)
    p = gh["ty_le_chinh"]["p"]
    assert gh["gioi_han_bo_ve"]["thap"] == pytest.approx(p * 0.95)
    assert gh["so_sanh_thoi_gian_cho"]["bo_ve"]["trung_vi"] == 80


@pytest.mark.parametrize("err, goi", [
    ("Error in library(jsonlite) : there is no package called ‘jsonlite’", "jsonlite"),   # R trên Mac, locale UTF-8
    ("Error in library(jsonlite) : there is no package called 'jsonlite'", "jsonlite"),   # R trên Windows (CI 23/11)
    ('Error : there is no package called "brant"', "brant"),
    ("Error in clm(...) : object 'x' not found", None),
    ("", None),
])
def test_goi_r_thieu_nhan_ca_hai_kieu_nhay_20261123(err, goi):
    """Thiếu gói R ⇒ «không đo được — cài gói», ở MỌI locale (trước 23/11: chỉ nhận nháy cong ⇒ Windows báo «R lỗi»)."""
    assert P.goi_r_thieu(err) == goi
