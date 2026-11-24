"""Cầu nối R — bản R của Bảng 5 (gán đa trị theo nhánh + Poisson vững theo cụm, gộp Rubin) và đối chiếu theo sai số
Monte Carlo (22/11/2026).

Trước đây `cau_noi_r.doi_chieu` không có dòng nào cho Bảng 5: kiểm chéo G6 «khớp» mà MI chưa từng được R tái lập.
Nay: script R tái lập MI (mice pmm → mô hình trên từng bộ → Rubin; cụm ⇒ CR1 + t(G−1)); đối chiếu theo dung sai Monte
Carlo (không đòi khớp từng bộ gán vì thuật toán và hạt giống khác nhau) và đòi CẢ HAI phía tìm lại tham số thật trên dữ
liệu mô phỏng. Máy không có R/mice ⇒ test chạy thật tự bỏ qua; dòng đối chiếu khi R không ra Bảng 5 là «không so được».
Dữ liệu mô phỏng, không PII.
"""

from __future__ import annotations

import contextlib
import csv
import hashlib
import io
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402


# ───────────────────────────── dịch nhánh và khối tham số ─────────────────────────────
def test_nhanh_sang_r_dung_ngu_phap_chung():
    assert R.nhanh_sang_r("[co_hba1c] = '1'") == 'function(d) (suppressWarnings(as.numeric(d[["co_hba1c"]])) == 1.0)'
    vb = R.nhanh_sang_r("[a] <> '2' and ([b(3)] = '1' or [c] >= 5)")
    assert '!= 2.0 & (' in vb and 'd[["b___3"]]' in vb and "| suppressWarnings" in vb and ">= 5.0" in vb
    import nhap_lieu_excel as NLE

    with pytest.raises(NLE.LogicKhongHo):
        R.nhanh_sang_r("[nghe] = 'khac'")


def test_khoi_mi_tat_khi_python_khong_chay_mi():
    for mi in (None, {"skipped": True, "reason": "x"}, {"error": "y"}):
        vb = R.khoi_mi_r({"multiple_imputation": mi} if mi else {}, Path("."), Path("k.csv"))
        assert "MI_CO <- FALSE" in vb and "MI_KHONG_DUNG_DUOC <- NA_character_" in vb


def test_khoi_mi_bat_dung_mo_hinh_va_bien():
    tom = {"multiple_imputation": {"model": "poisson_cluster_mi", "n_imputations": 20, "results": [{"variable": "x"}]},
           "dac_ta_phan_tich": {"outcome": "y", "group": "x2", "covariates": ["x3", "k"],
                                "hiep_bien_phan_loai": {"k": {"muc": [1, 2], "ten": ["k_2"]}}}}
    vb = R.khoi_mi_r(tom, Path("."), Path("k.csv"))
    assert "MI_CO <- TRUE" in vb and "MI_M <- 20L" in vb and 'MI_LOAI <- "poisson"' in vb
    assert 'MI_BIEN_PT <- c("y", "x2", "x3", "k")' in vb and 'MI_PHAN_LOAI <- c("k")' in vb


# ───────────────────────────── sai số Monte Carlo của Python ─────────────────────────────
@pytest.mark.parametrize("cum", [True, False])
def test_mcse_python_bang_do_dao_dong_that_giua_cac_luot_gan(cum):
    """mcse = √(B/m) mà Python ghi phải xấp xỉ độ lệch chuẩn THẬT của ước lượng gộp giữa các lượt gán độc lập (cùng
    dữ liệu, hạt giống khác) — căn cứ của dung sai đối chiếu R. Hai mô hình: Poisson cụm và logistic không cụm
    (24/11/2026: cả hai qua bộ gán BoGanPMM; hạt giống là tham số `hat_giong`, không còn đọc bộ sinh toàn cục)."""
    import run_stats_analysis as RSA

    rng = np.random.default_rng(8)
    n = 800
    cum_v = np.repeat(np.arange(40), n // 40)
    x3 = rng.normal(0, 1, n)
    x1 = 0.5 * x3 + np.sqrt(0.75) * rng.normal(0, 1, n)
    p = np.clip(0.2 * np.exp(0.3 * x1 + 0.1 * x3 + rng.normal(0, 0.2, 40)[cum_v]), 0, 0.99)
    df = pd.DataFrame({"y": rng.binomial(1, p), "x3": x3, "x1": x1, "cum": cum_v})
    df.loc[rng.random(n) < 0.3, "x1"] = np.nan
    b, mcse = [], []
    for lan in range(8):
        mi = (RSA.multiple_imputation_model(df, "y", "x3", ["x1"], "poisson_pr", 20, "cum", {}, hat_giong=100 + lan)
              if cum else RSA.multiple_imputation_model(df, "y", "x3", ["x1"], "binary", 20, hat_giong=100 + lan))
        r = next(x for x in mi["results"] if x["variable"] == "x1")
        b.append(r["b"])
        mcse.append(r["mcse"])
    ty_le = float(np.std(b, ddof=1) / np.mean(mcse))
    assert 0.4 < ty_le < 2.5, (ty_le, b, mcse)  # 8 lượt: SD mẫu dao động ±~50 %; mcse sai ×√m sẽ ra ngoài khoảng


# ───────────────────────────── đối chiếu theo sai số Monte Carlo ─────────────────────────────
def _tom(b=0.30, se=0.07, mcse=0.006, cum=True, m=20, **them) -> dict:
    ci = [round(float(np.exp(b - 2.02 * se)), 4), round(float(np.exp(b + 2.02 * se)), 4)]
    kq = {"variable": "x1", "PR_adj": round(float(np.exp(b)), 4), "CI_95": ci, "p": 0.001, "b": b, "se": se,
          "mcse": mcse, **them}
    mi = {"model": "poisson_cluster_mi" if cum else "poisson_hc0_mi", "n_imputations": m, "n_total": 1200,
          "results": [kq]}
    if cum:
        mi["cluster"] = {"cot": "cum", "so_cum": 40}
    return {"multiple_imputation": mi}


def _r(b=0.31, se=0.071, mcse=0.007, suy="t(G-1)", m=20, n=1200) -> dict:
    ci = [float(np.exp(b - 2.02 * se)), float(np.exp(b + 2.02 * se))]
    return {"mi": {"mo_hinh": "poisson_cluster_mi", "m": m, "n": n, "suy_luan": suy,
                   "he_so": {"x1": {"uoc_luong": float(np.exp(b)), "ci": ci, "p": 0.001, "b": b, "se": se,
                                    "mcse": mcse}}}}


def _dong(tom, kq) -> dict:
    ds = R._mi(tom, kq, {})
    assert len(ds) == 1, ds
    return ds[0]


def test_mi_khop_trong_dung_sai_monte_carlo():
    d = _dong(_tom(), _r())
    assert d["trang_thai"] == "khop", d
    assert "sai số Monte Carlo" in d["ghi_chu"] and d["dung_sai"]["df"] == 19


def test_mi_lech_uoc_luong_vuot_dung_sai():
    # dung sai b ≈ 4,9·√(2·20·0,007²/20) ≈ 0,048 ⇒ lệch 0,10 là LỆCH
    d = _dong(_tom(), _r(b=0.40))
    assert d["trang_thai"] == "lech" and d["kiem"]["b"] is False, d


def test_mi_lech_sai_so_chuan_vuot_dung_sai():
    d = _dong(_tom(mcse=0.001), _r(se=0.090, mcse=0.001))
    assert d["trang_thai"] == "lech" and d["kiem"]["se"] is False, d


def test_mi_cach_suy_luan_khac_la_lech():
    d = _dong(_tom(), _r(suy="z"))
    assert d["trang_thai"] == "lech" and "SUY LUẬN KHÁC" in d["ghi_chu"], d


def test_mi_so_ca_khac_la_lech():
    d = _dong(_tom(), _r(n=1100))
    assert d["trang_thai"] == "lech" and "SỐ CA KHÁC" in d["ghi_chu"], d


def test_mi_r_khong_ra_bang_5_la_khong_so_duoc_kem_ly_do():
    d = _dong(_tom(), {})
    assert d["trang_thai"] == R.DONG_KHONG_SO_DUOC and "R KHÔNG ra Bảng 5" in d["ghi_chu"]
    d = _dong(_tom(), {"mi_khong_dung_duoc": "so sánh chữ chưa hỗ trợ"})
    assert "so sánh chữ chưa hỗ trợ" in d["ghi_chu"]


def test_mi_m_qua_it_la_khong_so_duoc():
    d = _dong(_tom(m=5), _r(m=5))
    assert d["trang_thai"] == R.DONG_KHONG_SO_DUOC and "m = 5 < 10" in d["ghi_chu"], d


def test_mi_tom_tat_cu_khong_co_mcse_la_khong_so_duoc():
    tom = _tom()
    del tom["multiple_imputation"]["results"][0]["mcse"]
    d = _dong(tom, _r())
    assert d["trang_thai"] == R.DONG_KHONG_SO_DUOC and "b/se/mcse" in d["ghi_chu"], d


def test_dung_sai_mi_dung_cong_thuc():
    from scipy import stats as st

    ds = R.dung_sai_mi({"b": 0, "se": 0.1, "mcse": 0.01}, {"b": 0, "se": 0.1, "mcse": 0.02}, 20, 20)
    c = st.t.ppf(1 - 1e-4 / 2, 19)
    b_lon = 20 * 0.02 ** 2  # B lớn hơn của hai phía
    assert ds["tol_b"] == pytest.approx(c * (2 * b_lon / 20) ** 0.5 + 1e-6)
    lam = (1 + 1 / 20) * b_lon / 0.1 ** 2
    assert ds["tol_se_tuong_doi"] == pytest.approx(c * 2 ** 0.5 * 0.5 * lam * (2 / 19) ** 0.5 + R.MI_SAN_SE)


# ───────────────────────────── chạy THẬT: Python → cu-phap → chay R → doi-chieu ─────────────────────────────
def _chay_ham_r(tmp_path: Path, vao: dict, than: str) -> dict:
    """Khối «ham-kiem-thu» của MAU_R (đúng mã script sinh ra dùng) chạy với dữ liệu `vao`."""
    a, b = R.MAU_R.index("# >>> ham-kiem-thu"), R.MAU_R.index("# <<< ham-kiem-thu")
    (tmp_path / "vao.json").write_text(json.dumps(vao), encoding="utf-8", newline="\n")
    ma = ("suppressPackageStartupMessages(library(survival))\n" + R.ascii_hoa_chuoi_r(R.MAU_R[a:b])
          + 'V <- jsonlite::read_json("vao.json", simplifyVector = TRUE)\n' + than
          + '\njsonlite::write_json(RA, "ra.json", auto_unbox = TRUE, digits = NA, na = "null")\n')
    (tmp_path / "t.R").write_text(ma, encoding="utf-8", newline="\n")
    kq = R.chay_r(R.tim_r(), [str(tmp_path / "t.R")], thu_muc=tmp_path, thoi_han=120)
    assert kq[0] == 0, kq[2]
    return json.loads((tmp_path / "ra.json").read_text(encoding="utf-8"))



def _co_r_mice() -> bool:
    try:
        return bool(R.ung_vien_rscript()) and not R.kiem_moi_truong(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


CO_R = _co_r_mice()
CAN_R = pytest.mark.skipif(not CO_R, reason="máy không có Rscript hoặc thiếu gói R của cầu nối (gồm mice)")


def _khung_main(tmp_path: Path, monkeypatch, study: str, df: "pd.DataFrame", tu_dien: list[list[str]],
                tham_so: list[str], them_tep=None) -> tuple[Path, dict]:
    import run_stats_analysis as RSA

    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(S, "EXPORTS", tmp_path / "exports")
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda st, g: {"g2_status": "LOCKED", "g5_status": "LOCKED"})
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda st: (True, "giả lập: G4 khoá sống"))
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    d = tmp_path / "exports" / study
    (d / "05_clean_locked").mkdir(parents=True)
    p = d / "05_clean_locked" / "k.csv"
    df.to_csv(p, index=False)
    man = {"locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
           "lock_date": "2026-11-22", "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}
    (d / "DATA_LOCK_manifest.json").write_text(json.dumps(man), encoding="utf-8", newline="\n")
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda st, _d: man)
    with open(d / f"G5_REDCap_dictionary_{study}.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerows(tu_dien)
    if them_tep:
        them_tep(d)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(p), "--study", study, "--gate", "G6",
                                      "--n-imputations", "20", *tham_so])
    np.random.seed(20261122)
    with contextlib.redirect_stdout(io.StringIO()):
        RSA.main()
        ma = {lenh: R.main([lenh, "--study", study]) for lenh in ("cu-phap", "chay", "doi-chieu")}
    assert ma == {"cu-phap": 0, "chay": 0, "doi-chieu": 0}, ma
    return d, json.loads((d / "G6_r_doi_chieu.json").read_text(encoding="utf-8"))


def _mi_cua(dc: dict) -> dict:
    return {x["muc"].split(" — ")[-1]: x for x in dc["dong"] if x["muc"].startswith("Gán đa trị")}


def _tim_lai(x: dict, that: float) -> bool:
    """«Tìm lại tham số thật»: |log PR − log PR thật| ≤ 3,5 SE (SE suy từ nửa độ rộng KTC 95 %; xác suất trượt khi ước
    lượng không chệch ≈ 0,05 % mỗi hệ số — tiêu chí chọn TRƯỚC khi chạy, không chọn hạt giống theo kết quả)."""
    lo, hi = x["ci"]
    se = (np.log(hi) - np.log(lo)) / (2 * 1.96)
    return abs(np.log(x["uoc_luong"]) - np.log(that)) <= 3.5 * se


@CAN_R
@pytest.mark.parametrize("df_t", [39, None])
def test_luat_rubin_cua_r_trung_python(tmp_path, df_t):
    """`gop_rubin` của script R ra ĐÚNG số của `run_stats_analysis._gop_rubin` + suy luận t(G−1)/z (cùng đầu vào)."""
    import run_stats_analysis as RSA
    from scipy import stats as st

    rng = np.random.default_rng(3)
    Q = rng.normal(0, 0.1, (12, 3))
    U = []
    for _ in range(12):
        a = rng.normal(0, 0.05, (3, 3))
        U.append(a @ a.T + np.eye(3) * 0.01)
    ra = _chay_ham_r(tmp_path, {"Q": Q.tolist(), "U": [u.tolist() for u in U]},
                     "RA <- gop_rubin(V$Q, lapply(seq_len(dim(V$U)[1]), function(i) V$U[i, , ]), "
                     + ("Inf" if df_t is None else str(df_t)) + ")")
    q_bar, se, lam = RSA._gop_rubin(Q, U)
    assert np.allclose(ra["b"], q_bar) and np.allclose(ra["se"], se)
    b_giua = np.var(Q, axis=0, ddof=1)
    assert np.allclose(ra["mcse"], np.sqrt(b_giua / 12))
    q = st.t.ppf(0.975, df_t) if df_t else st.norm.ppf(0.975)
    assert np.allclose(ra["lo"], q_bar - q * se) and np.allclose(ra["hi"], q_bar + q * se)
    assert ra["suy_luan"] == ("t(G-1)" if df_t else "z")


@CAN_R
def test_that_mi_poisson_cum_python_khop_r_va_ca_hai_tim_lai_tham_so(tmp_path, monkeypatch):
    """PR thật: x1 1,3 · x2 1,5 (mức cụm) · x3 e^0,1; x1 thiếu 20 % (MCAR); 40 cụm. Mọi dòng (cả Bảng 5) khớp; CẢ Python
    lẫn R tìm lại tham số thật (`_tim_lai`)."""
    rng = np.random.default_rng(70)
    n, so_cum = 1200, 40
    cum = np.repeat(np.arange(so_cum), n // so_cum)
    u = rng.normal(0, 0.4, so_cum)[cum]
    x3 = rng.normal(0, 1, n)
    x1 = 0.5 * x3 + np.sqrt(0.75) * rng.normal(0, 1, n)
    x2 = rng.binomial(1, 0.4, so_cum)[cum]  # mức cụm ⇒ SE theo cụm khác hẳn HC0 (bắt R bỏ hiệu chỉnh cụm)
    p = np.clip(0.15 * np.exp(np.log(1.3) * x1 + np.log(1.5) * x2 + 0.1 * x3 + u), 0, 0.99)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(n)], "y": rng.binomial(1, p), "x2": x2, "x3": x3,
                       "x1": x1, "cum": cum})
    df.loc[rng.random(n) < 0.2, "x1"] = np.nan
    tu_dien = [["Variable / Field Name", "Field Type", "Field Label", "Identifier?"]]
    tu_dien += [[c, "text", c, ""] for c in df.columns]
    _d, dc = _khung_main(tmp_path, monkeypatch, "MI-CUM", df, tu_dien,
                         ["--outcome", "y", "--group", "x2", "--covariates", "x3,x1", "--outcome-type", "poisson_pr",
                          "--cot-cum", "cum"])
    assert dc["dem"]["lech"] == 0 and dc["dem"]["khong_so_duoc"] == 0, dc["dem"]
    mi = _mi_cua(dc)
    assert set(mi) == {"x1", "x2", "x3"} and all(x["trang_thai"] == "khop" for x in mi.values()), mi
    for v, that in (("x1", 1.3), ("x2", 1.5), ("x3", float(np.exp(0.1)))):
        for phia in ("python", "r"):
            assert _tim_lai(mi[v][phia], that), (v, phia, mi[v][phia])
    assert all("t(G" not in x["ghi_chu"] or "SUY LUẬN KHÁC" not in x["ghi_chu"] for x in mi.values())


@CAN_R
def test_that_mi_gan_theo_nhanh_python_khop_r(tmp_path, monkeypatch):
    """hba1c_gt chỉ có khi co_hba1c = 1 (Branching Logic); hba1c_3muc = neu(co_hba1c == 0, 3, neu(hba1c_gt < 7, 1, 2))
    là hiệp biến phân loại. R gán hba1c_gt trong đúng nhóm con rồi tính lại hba1c_3muc như Python: không mã 3 nào được
    gán cho người đã làm HbA1c; cả hai phía tìm lại PR thật của nhom (1,5); mọi dòng khớp."""
    rng = np.random.default_rng(11)
    n = 1500
    tuoi = rng.normal(60, 10, n)
    nhom = rng.binomial(1, 0.5, n)
    co = rng.binomial(1, 0.7, n)
    gt = np.where(co == 1, rng.normal(7.2 + 0.04 * (tuoi - 60), 1.0, n), np.nan)
    muc = np.where(co == 0, 3, np.where(gt < 7, 1, 2))
    p = np.clip(0.2 * np.exp(np.log(1.5) * nhom + 0.25 * (muc == 2) + 0.4 * (muc == 3) + 0.01 * (tuoi - 60)), 0, .99)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(n)], "y": rng.binomial(1, p), "nhom": nhom,
                       "tuoi": np.round(tuoi, 1), "co_hba1c": co, "hba1c_gt": np.round(gt, 2)})
    df.loc[(df["co_hba1c"] == 1) & (rng.random(n) < 0.3), "hba1c_gt"] = np.nan
    an = df.index[df["co_hba1c"] == 0][:5]
    df.loc[an, "hba1c_gt"] = 99.0  # trường ẩn mà có giá trị (mâu thuẫn nhánh) — không được làm dữ liệu gán
    nhanh = "[co_hba1c] = '1'"
    tu_dien = [["Variable / Field Name", "Form Name", "Field Type", "Field Label",
                "Choices, Calculations, OR Slider Labels", "Text Validation Type OR Show Slider Number",
                "Identifier?", "Branching Logic (Show field only if...)"]]
    loai = {"record_id": ("text", "", ""), "y": ("yesno", "", ""), "nhom": ("yesno", "", ""),
            "tuoi": ("text", "", "number"), "co_hba1c": ("radio", "1, Có | 0, Không", ""),
            "hba1c_gt": ("text", "", "number")}
    for c, (ft, lc, kt) in loai.items():
        tu_dien.append([c, "f", ft, c, lc, kt, "", nhanh if c == "hba1c_gt" else ""])

    def them(d: Path) -> None:
        (d / "study_meta.json").write_text(json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8",
                                           newline="\n")
        with open(d / "_bien-phai-sinh.csv", "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["ten_bien", "nhan", "kieu", "dinh_nghia", "bien_nguon", "quy_tac_ma_thieu", "dung_o", "nguon",
                        "cong_thuc", "lap_k", "nhan_gia_tri", "nguoi_duyet"])
            w.writerow(["hba1c_3muc", "HbA1c 3 mức", "Phân loại", "", "co_hba1c hba1c_gt", "", "", "",
                        "neu(co_hba1c == 0, 3, neu(hba1c_gt < 7, 1, 2))", "", "1, < 7 | 2, ≥ 7 | 3, Không làm", ""])

    d, dc = _khung_main(tmp_path, monkeypatch, "MI-NHANH", df, tu_dien,
                        ["--outcome", "y", "--group", "nhom", "--covariates", "tuoi,hba1c_3muc",
                         "--outcome-type", "poisson_pr", "--hiep-bien-phan-loai", "hba1c_3muc"], them)
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert set(tom["multiple_imputation"]["gan_theo_nhanh"]["bien"]["hba1c_3muc"]["ma_da_gan"]) <= {"1", "2"}
    rr = json.loads((d / "G6_r_ket_qua.json").read_text(encoding="utf-8"))["ket_qua"]["mi"]
    assert set(rr["ma_da_gan"]["hba1c_3muc"]) <= {"1", "2"}, rr["ma_da_gan"]  # R cũng không gán mã 3
    kn = rr["kiem_nhanh"]["hba1c_gt"]
    assert kn["so_hang_ngoai_nhanh"] == int((df["co_hba1c"] == 0).sum())
    assert kn["con_gia_tri_ngoai_nhanh"] == 0 and kn["so_cot_dung_lam_du_bao"] == 0, kn
    mi = _mi_cua(dc)
    assert set(mi) == {"nhom", "tuoi", "hba1c_3muc_2", "hba1c_3muc_3"}, mi
    assert all(x["trang_thai"] == "khop" for x in mi.values()), [x["ghi_chu"] for x in mi.values()]
    for phia in ("python", "r"):
        assert _tim_lai(mi["nhom"][phia], 1.5), (phia, mi["nhom"][phia])


@CAN_R
def test_that_mi_du_bao_roi_rac_pmm_khong_phong_phuong_sai_giua_bo(tmp_path, monkeypatch):
    """Mọi biến dự báo của x1 đều nhị phân (y, x2) ⇒ trung bình dự đoán của PMM chỉ có 4 giá trị. mice 3.19 mặc định
    (matchindex) tách đồng hạng theo thứ tự cố định ⇒ SD giữa bộ ≈ 3 lần Python (đo 23/11/2026: 0,068 so 0,022). Từ
    24/11/2026 cả hai phía dùng CÙNG phương pháp (PMM kiểu 1 tham số bootstrap, 10 người cho chọn riêng từng ca, phá thế
    trùng ngẫu nhiên — Python BoGanPMM, R mice method "pmmboot") — SD giữa bộ phải cùng cỡ.
    Ngưỡng 2,1 lần: B̂ ~ B·χ²(m−1)/(m−1), m = 20 ⇒ SD log(√B̂_R/√B̂_Py) ≈ 0,23; 3,3 SD ≈ log 2,1 (chọn TRƯỚC khi chạy)."""
    rng = np.random.default_rng(70)
    n = 1200
    x2 = rng.binomial(1, 0.4, n)
    x1 = 0.8 * x2 + rng.normal(0, 1, n)
    p = np.clip(0.15 * np.exp(np.log(1.3) * x1 + np.log(1.5) * x2), 0, 0.99)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(n)], "y": rng.binomial(1, p), "x2": x2, "x1": x1})
    df.loc[rng.random(n) < 0.185, "x1"] = np.nan
    tu_dien = [["Variable / Field Name", "Field Type", "Field Label", "Identifier?"]]
    tu_dien += [[c, "text", c, ""] for c in df.columns]
    d, dc = _khung_main(tmp_path, monkeypatch, "MI-ROI-RAC", df, tu_dien,
                        ["--outcome", "y", "--group", "x2", "--covariates", "x1", "--outcome-type", "poisson_pr"])
    assert _mi_cua(dc)["x1"]["trang_thai"] == "khop", _mi_cua(dc)["x1"]
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    mc_py = next(x["mcse"] for x in tom["multiple_imputation"]["results"] if x["variable"] == "x1")
    mc_r = json.loads((d / "G6_r_ket_qua.json").read_text(encoding="utf-8"))["ket_qua"]["mi"]["he_so"]["x1"]["mcse"]
    assert 1 / 2.1 < mc_r / mc_py < 2.1, (mc_r, mc_py)
