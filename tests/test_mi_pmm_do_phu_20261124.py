"""Bộ gán đa trị PMM (24/11/2026) — kết quả không phụ thuộc CPU hay thứ tự hàng, độ phủ KTC 95 % đúng danh nghĩa.

Lỗi đo được ở bộ gán cũ (statsmodels 0.14 `MICEData.impute_pmm`) khi biến dự báo rời rạc (trung bình dự đoán chỉ vài
mức, trùng hàng loạt): `np.argsort` không ổn định (sắp xếp SIMD theo CPU) + cửa sổ `searchsorted ± k` chung cho cả nhóm
trùng + so khớp kiểu 2 ⇒ λ_x1 = 0,15 / 0,29 / 0,59 trên SkylakeX / Mac Accelerate / Haswell (cùng dữ liệu, cùng hạt
giống); chỉ đảo thứ tự hàng ⇒ λ 0,10–0,49. Bộ gán mới `BoGanPMM`: PMM kiểu 1 tham số bootstrap, k = 10 người cho chọn
RIÊNG từng ca, phá thế trùng ngẫu nhiên (Morris, White & Royston 2014, PMID 24903709); dự báo rời rạc quy về ABB theo ô
(Rubin & Schenker 1986, doi:10.1080/01621459.1986.10478280) ⇒ λ ≈ tỷ lệ thiếu khi bộ gán không thêm thông tin.

Phân xử bằng mô phỏng 500 lần lặp (dự báo rời rạc/liên tục × có/không cụm; so bộ gán cũ, mới, ABB theo ô, R mice):
kịch bản và bảng ở báo cáo nhánh; test dưới đây là bản NHẸ cho CI, có hạt giống. Dữ liệu đều mô phỏng; không PII.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import run_stats_analysis as RSA  # noqa: E402
from test_run_stats_mi_nhanh_poisson_cum_20261122 import _mo_phong_cum  # noqa: E402


# ───────────────────────────── chọn người cho: k gần nhất, phá thế trùng riêng từng ca ─────────────────────────────
def test_nhom_trung_lon_hon_cua_so_moi_ca_chon_deu_trong_ca_nhom():
    """Mọi người cho cùng trung bình dự đoán (dự báo rời rạc): MỖI ca nhận chọn đều trong TOÀN BỘ nhóm trùng — không
    phải trong một cửa sổ ±k chung cho cả nhóm (lỗi cũ: cả ô dùng chung ~20 người cho)."""
    n_cho = 400
    v = RSA._chon_nguoi_cho(np.zeros(n_cho), np.arange(n_cho, dtype=float), np.zeros(8000), 10,
                            np.random.default_rng(1))
    dem = np.bincount(v.astype(int), minlength=n_cho)
    assert (dem > 0).sum() > 390  # kỳ vọng 400·(1 − e^−20) ≈ 400 người cho khác nhau
    assert dem.max() < 50  # đều: trung bình 20 lần/người


def test_k_nguoi_gan_nhat_va_chon_deu_trong_k():
    """Trung bình dự đoán phân biệt: ca nhận 50,2 ⇒ 10 người gần nhất là 46…55, mỗi người ~1/10."""
    v = RSA._chon_nguoi_cho(np.arange(100, dtype=float), np.arange(100, dtype=float), np.full(20000, 50.2), 10,
                            np.random.default_rng(2))
    assert set(np.unique(v)) == set(range(46, 56))
    ty_le = np.bincount(v.astype(int) - 46, minlength=10) / len(v)
    assert np.allclose(ty_le, 0.1, atol=0.012)


def test_trung_o_khoang_cach_thu_k_xac_suat_dung():
    """3 người gần hơn hẳn + 50 người trùng ở đúng khoảng cách thứ k (vượt ra ngoài cửa sổ ±k): P(chọn người gần hơn)
    = 3/10, phần còn lại chia đều cho cả 50 người trùng."""
    du_cho = np.r_[np.zeros(3), np.ones(50)]
    v = RSA._chon_nguoi_cho(du_cho, np.arange(53, dtype=float), np.zeros(40000), 10, np.random.default_rng(3))
    assert np.mean(v < 3) == pytest.approx(0.3, abs=0.01)
    dem_trung = np.bincount(v[v >= 3].astype(int) - 3, minlength=50)
    assert (dem_trung > 0).all() and dem_trung.max() / dem_trung.mean() < 1.4


def test_bo_gan_tat_dinh_theo_hat_giong_va_rut_gia_tri_co_that():
    """Cùng hạt giống ⇒ cùng giá trị gán trên MỌI máy (số ghi dưới đo trên Mac/Accelerate; CI Linux/OpenBLAS phải ra
    đúng như vậy — bộ gán cũ cho λ khác nhau theo CPU). Giá trị gán là giá trị quan sát có thật; biến phân loại ra mã
    có thật."""
    rng = np.random.default_rng(3)
    n = 60
    k = pd.DataFrame({"a": rng.binomial(1, 0.5, n).astype(float), "b": rng.integers(0, 3, n).astype(float),
                      "x": rng.normal(size=n)})
    k.loc[::5, "x"] = np.nan
    k.loc[1::7, "b"] = np.nan
    bo = RSA.BoGanPMM(k, None, ["b"], rng=np.random.default_rng(11)).mot_bo()
    vx = bo.loc[k["x"].isna(), "x"].to_numpy()
    vb = bo.loc[k["b"].isna(), "b"].to_numpy()
    assert [round(float(x), 6) for x in vx] == [-0.305144, 1.370072, -0.555866, 0.13424, 0.817207, -0.608611,
                                                0.65764, -0.813772, 0.767503, 0.293234, -1.335011, -0.340317]
    assert vb.tolist() == [2.0, 2.0, 2.0, 2.0, 0.0, 2.0, 0.0, 0.0, 1.0]
    assert set(np.round(vx, 12)) <= set(np.round(k["x"].dropna(), 12)) and set(vb) <= {0.0, 1.0, 2.0}
    assert bo.notna().all().all() and bo.loc[k["x"].notna(), "x"].equals(k.loc[k["x"].notna(), "x"])


# ───────────────────────────── bất biến theo thứ tự hàng ─────────────────────────────
def test_bat_bien_theo_thu_tu_hang():
    """Cùng dữ liệu, cùng hạt giống, chỉ hoán vị hàng: λ_x1 và PR_x1 chỉ dao động trong sai số Monte Carlo. λ̂ với
    m = 40: B̂ ~ B·χ²(39)/39 ⇒ SD ≈ λ·√(2/39) ≈ 0,045 quanh λ ≈ 0,2 (x1 thiếu 20 %, bộ gán không thêm thông tin).
    Bộ gán cũ: 0,10–0,49 qua 10 hoán vị (ngoài khoảng)."""
    df = _mo_phong_cum(3000, 60, 1)
    lam, pr = [], []
    for k in range(5):
        d = df if k == 0 else df.iloc[np.random.default_rng(500 + k).permutation(len(df))].reset_index(drop=True)
        mi = RSA.multiple_imputation_model(d, "y", "x2", ["x1"], "poisson_pr", 40, "cum", {}, hat_giong=20261122)
        lam.append(mi["ty_le_thong_tin_thieu"]["x1"])
        pr.append(next(r for r in mi["results"] if r["variable"] == "x1")["PR_adj"])
    assert all(0.08 < x < 0.36 for x in lam), lam  # 0,2 ± ~3 SD
    assert max(lam) - min(lam) < 0.2, lam
    assert max(pr) - min(pr) < 0.03, pr  # cũ: 1,265–1,330


# ───────────────────────────── độ phủ (bản nhẹ cho CI) ─────────────────────────────
def test_do_phu_va_ty_le_thong_tin_thieu_dung_ly_thuyet():
    """100 lần lặp (300 người, 30 cụm, x1 thiếu 20 % MCAR, dự báo của x1 nhị phân, m = 10): độ phủ KTC 95 % của log
    PR(x1) ≥ 0,88 (SD nhị thức 0,022) và λ̄_x1 trong 0,2 ± 2,7 SE (SD λ̂ ≈ 0,074 ⇒ SE ≈ 0,0074): ABB theo ô đúng lý
    thuyết cho λ ≈ tỷ lệ thiếu. Đột biến «cửa sổ chung cho nhóm trùng» cho λ̄ 0,31, «không bootstrap» (gán không
    đúng — improper) cho 0,18 ⇒ đều đỏ."""
    phu, lam = 0, []
    for lan in range(100):
        mi = RSA.multiple_imputation_model(_mo_phong_cum(300, 30, 300 + lan), "y", "x2", ["x1"], "poisson_pr", 10,
                                           "cum", {}, hat_giong=900 + lan)
        r = next(x for x in mi["results"] if x["variable"] == "x1")
        phu += r["CI_95"][0] <= 1.3 <= r["CI_95"][1]
        lam.append(mi["ty_le_thong_tin_thieu"]["x1"])
    assert phu / 100 >= 0.88, phu
    assert 0.185 < float(np.mean(lam)) < 0.225, float(np.mean(lam))


def test_moi_duong_gan_dung_cung_bo_gan():
    """Ba đường gán đa trị (Poisson/logistic/tuyến tính không cụm, Poisson cụm, ghép cặp) đều qua BoGanPMM và ghi
    phương pháp gán + hạt giống vào đầu ra (tái lập)."""
    df = _mo_phong_cum(600, 30, 4)
    for kq in (RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "binary", 5),
               RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "poisson_pr", 5, "cum", {}),
               RSA.multiple_imputation_model(df.assign(x3=df["x1"]), "x3", "x2", ["y"], "continuous", 5)):
        assert kq["bo_may"] == "tu_lap" and kq["phuong_phap_gan"] == RSA.NGUON_PMM, kq
        assert kq["hat_giong"] == RSA.HAT_GIONG_MI
    a = RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "poisson_pr", 5, "cum", {})
    b = RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "poisson_pr", 5, "cum", {})
    assert a["results"] == b["results"]  # chạy lại ⇒ đúng cùng kết quả


def test_moi_bo_gan_la_chuoi_doc_lap():
    """Hai biến thiếu cùng hàng, tương quan ~0,9 với nhau: nếu các bộ gán là các bước liền nhau của MỘT chuỗi (cách của
    MICE dựng sẵn) thì giá trị gán của hai bộ kề nhau tương quan mạnh (đo: 0,83 so với 0,46 cho bộ cách ≥ 3 bước) ⇒ B
    bị ước lượng thấp. Chuỗi độc lập: tương quan bộ kề = bộ xa ≈ 0."""
    rng = np.random.default_rng(5)
    n = 1000
    z = rng.normal(size=n)
    k = pd.DataFrame({"a": rng.binomial(1, 0.5, n).astype(float), "x1": z + 0.3 * rng.normal(size=n),
                      "x3": z + 0.3 * rng.normal(size=n)})
    ca = rng.random(n) < 0.3
    k.loc[ca, ["x1", "x3"]] = np.nan
    bg = RSA.BoGanPMM(k, None, [], rng=np.random.default_rng(1))
    c = np.corrcoef(np.array([bg.mot_bo().loc[ca, "x1"].to_numpy() for _ in range(12)]))
    ke = np.mean([c[i, i + 1] for i in range(11)])
    xa = np.mean([c[i, j] for i in range(12) for j in range(12) if j - i >= 3])
    assert abs(ke) < 0.1 and abs(ke - xa) < 0.05, (ke, xa)


# ───────────────────────────── phía R: cùng phương pháp («pmmboot» của mice) ─────────────────────────────
import cau_noi_r as R  # noqa: E402


def test_script_r_gan_bang_pmmboot_o_moi_khoi():
    """Mọi khối gán đa trị của script R (Bảng 5 và phân tích bổ sung thứ tự) dùng method «pmmboot» định nghĩa ở khối hàm
    dùng chung — không phải «pmm» mặc định của mice (tách đồng hạng theo thứ tự cố định, tham số không bootstrap)."""
    assert "mice.impute.pmmboot <- function(y, ry, x, wy = NULL, donors = 10L, ...)" in R.R_HAM_MO_HINH
    assert 'method = "pmmboot", predictorMatrix = pred' in R.MAU_R and 'method = "pmm"' not in R.MAU_R
    bo_sung = R.kich_ban_bo_sung("thu_tu")
    assert '"pmmboot", ""), cot_gan)' in bo_sung and "mice.impute.pmmboot" in bo_sung and '"pmm", ""' not in bo_sung


def _co_r() -> bool:
    try:
        return bool(R.ung_vien_rscript()) and not R.kiem_moi_truong(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


@pytest.mark.skipif(not _co_r(), reason="máy không có Rscript hoặc thiếu gói R của cầu nối")
def test_that_r_pmmboot_chon_rieng_tung_ca_trong_ca_nhom_trung(tmp_path):
    """Hàm R (đúng mã script sinh ra): 400 người cho cùng trung bình dự đoán ⇒ 8.000 ca nhận chọn đều trong CẢ
    mẫu bootstrap của nhóm (kỳ vọng ≈ 400·(1 − e⁻¹) ≈ 253 giá trị khác nhau; lỗi cửa sổ chung cho cả nhóm chỉ ra ≤ ~20);
    dự báo phân biệt ⇒ chỉ người gần nhất."""
    a = R.R_HAM_MO_HINH.index("mice.impute.pmmboot <- function")
    b = R.R_HAM_MO_HINH.index("}, numeric(1))\n}", a) + len("}, numeric(1))\n}")
    ma = R.ascii_hoa_chuoi_r(R.R_HAM_MO_HINH[a:b]) + """
set.seed(1)
y <- c(seq_len(400), rep(NA, 8000)); ry <- !is.na(y); x <- matrix(rep(1, 8400), ncol = 1)
v1 <- mice.impute.pmmboot(y, ry, x)
y2 <- c(0:99, rep(NA, 5000)); ry2 <- !is.na(y2); x2 <- matrix(c(0:99, rep(50.2, 5000)), ncol = 1)
v2 <- mice.impute.pmmboot(y2, ry2, x2)
jsonlite::write_json(list(khac = length(unique(v1)), lon_nhat = max(table(v1)), tap = sort(unique(v2))), "ra.json",
                     auto_unbox = TRUE)
"""
    (tmp_path / "t.R").write_text(ma, encoding="utf-8", newline="\n")
    kq = R.chay_r(R.tim_r(), [str(tmp_path / "t.R")], thu_muc=tmp_path, thoi_han=120)
    assert kq[0] == 0, kq[2]
    import json

    ra = json.loads((tmp_path / "ra.json").read_text(encoding="utf-8"))
    assert ra["khac"] > 230 and ra["lon_nhat"] < 150, ra  # trung bình 20 lần/ô bootstrap, ô lặp 5–6 lần ⇒ ~100
    # bootstrap người cho ⇒ 10 người gần nhất lấy trong mẫu bootstrap: giá trị quanh 50 (không xa hơn ±10)
    assert all(40 <= v <= 60 for v in ra["tap"]) and len(ra["tap"]) >= 5, ra  # 10 ô bootstrap, có ô trùng


def test_hat_giong_sap_qua_dac_ta_g6_toi_engine(tmp_path, monkeypatch):
    """SAP khai «Random seed» ⇒ đặc tả G6 ghi `hat_giong` ⇒ `chay_sap_g6` truyền `--hat-giong` ⇒ engine dùng đúng số đó
    cho bộ gán và ghi vào Bảng 5 (chạy lại cho cùng kết quả)."""
    import json

    import chay_sap_g6 as CS
    from test_poisson_phan_loai_20261114 import _main

    assert CS.doi_so_run_stats({"tham_so": {"n_imputations": 20, "hat_giong": 20260830}}) == [
        "--n-imputations", "20", "--hat-giong", "20260830"]
    assert CS._kiem_gia_tri("hat_giong", "nguyen", 20260830) == []
    assert CS._kiem_gia_tri("hat_giong", "nguyen", -1) and CS._kiem_gia_tri("hat_giong", "nguyen", 1.5)
    ket = []
    for i, hg in enumerate((20260830, 20260830, 7)):
        d, _ra = _main(tmp_path / str(i), monkeypatch, ["--outcome", "y", "--group", "g", "--covariates", "tuoi",
                                                       "--outcome-type", "poisson_pr", "--hat-giong", str(hg)])
        mi = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))["multiple_imputation"]
        assert mi["hat_giong"] == hg, mi
        ket.append(mi["results"])
    assert ket[0] == ket[1] and ket[0] != ket[2]
