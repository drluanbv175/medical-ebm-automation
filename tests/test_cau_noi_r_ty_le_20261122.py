"""Cầu nối R — bản đối chiếu của Bảng 1b: tỷ lệ + KTC 95 % Wilson, độc lập và theo cụm (việc G, 22/11/2026).

Trước đây mọi phân tích cắt ngang chỉ mô tả (tỷ lệ Wilson) ghi kiểm chéo «không áp dụng»: cả hai cầu nối không có bản
tái lập. Nay script R tính lại ĐỘC LẬP — KTC Wilson lấy từ `stats::prop.test(correct = FALSE)` (cài đặt riêng của R),
DE từ phương sai tuyến tính hoá theo cụm, hiệu chỉnh bậc tự do (z/t_{K−1})² (Dean & Pagano 2015) — và `doi_chieu` so
với dung sai bằng ĐƠN VỊ LÀM TRÒN của tóm tắt Python (phép tất định: không có sai số Monte Carlo). `kiem_cheo_g6` chấm
được: R khớp ⇒ cả lượt KHỚP. Bản SPSS (23/11/2026): tests/test_cau_noi_spss_ty_le_20261123.py.
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
pytest.importorskip("scipy")
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402


# ───────────────────────────── đặc tả ─────────────────────────────
def test_ty_le_tu_tom_tat_doc_dac_ta_moi_va_suy_tu_tom_tat_cu():
    assert R.ty_le_tu_tom_tat({"dac_ta_phan_tich": {"ty_le": ["g1"], "nguong_ty_le": 4.0}}) == (["g1"], 4.0)
    cu = {"dac_ta_phan_tich": {"outcome": None},
          "ty_le": [{"cot": "g1", "dinh_nghia": "g1 ≥ 4"}, {"cot": "g2", "dinh_nghia": "g2 ≥ 4"}]}
    assert R.ty_le_tu_tom_tat(cu) == (["g1", "g2"], 4.0)
    assert R.ty_le_tu_tom_tat({"ty_le": [{"cot": "kiem_soat_ha", "dinh_nghia": "kiem_soat_ha = 1"}]}) == (
        ["kiem_soat_ha"], None)
    assert R.ty_le_tu_tom_tat({}) == ([], None)


def test_dac_ta_chi_ty_le_hop_le_con_ket_cuc_thieu_nhom_van_tu_choi():
    R._dac_ta_hop_le({"ty_le": ["kiem_soat_ha"]})  # không nổ
    with pytest.raises(R.TuChoi):
        R._dac_ta_hop_le({})
    with pytest.raises(R.TuChoi, match="--group"):
        R._dac_ta_hop_le({"outcome": "y", "ty_le": ["x"]})


def test_khoi_r_ty_le_dung_prop_test_va_hieu_chinh_bac_tu_do():
    a = R.MAU_R.index("# ── 5c. Tỷ lệ")
    khoi = R.MAU_R[a:R.MAU_R.index("# ── 6. Sống còn")]
    assert "stats::prop.test(e, n, correct = FALSE)" in khoi
    assert "K / (K - 1) * sum((t_c - p * m_c)^2) / n^2" in khoi
    assert "(stats::qnorm(0.975) / stats::qt(0.975, K - 1))^2" in khoi
    assert "max(1, var_lin / var_srs)" in khoi


# ───────────────────────────── đối chiếu ─────────────────────────────
def _du_lieu(seed=5, so_cum=30, m=20, p=0.35, sd_cum=0.6) -> "pd.DataFrame":
    rng = np.random.default_rng(seed)
    cum = np.repeat(np.arange(so_cum), m)
    lp = np.log(p / (1 - p)) + rng.normal(0, sd_cum, so_cum)[cum]
    return pd.DataFrame({"y": rng.binomial(1, 1 / (1 + np.exp(-lp))), "cum": cum})


def _phia_r_doc_lap(df: "pd.DataFrame", bo_k_tren_k_tru_1: bool = False) -> dict:
    """«Phía R» dựng bằng đường KHÁC Python: Wilson của statsmodels, DE từ phương sai tỷ số theo cụm tính thẳng."""
    from scipy import stats as st
    from statsmodels.stats.proportion import proportion_confint

    y, c = df["y"].to_numpy(), df["cum"].to_numpy()
    n, e = len(y), int(y.sum())
    p = e / n
    t_c = pd.Series(y).groupby(c).sum().to_numpy()
    m_c = pd.Series(y).groupby(c).size().to_numpy()
    k = len(m_c)
    he = 1.0 if bo_k_tren_k_tru_1 else k / (k - 1)
    de = max(1.0, he * float(((t_c - p * m_c) ** 2).sum()) / n**2 / (p * (1 - p) / n))
    n_hd = n / de * (st.norm.ppf(0.975) / st.t.ppf(0.975, k - 1)) ** 2
    return {"y": {"n": n, "so_su_kien": e, "ty_le": p, "so_cum": k, "de": de,
                  "ci_doc_lap": list(proportion_confint(e, n, method="wilson")),
                  "ci": list(proportion_confint(p * n_hd, n_hd, method="wilson"))}}


def _cac_dong(df: "pd.DataFrame", **kw) -> list[dict]:
    import run_stats_analysis as RSA

    tom = {"ty_le": [RSA.ty_le_wilson_cum(df, "y", None, "cum")]}
    return R._ty_le(tom, {"ty_le": _phia_r_doc_lap(df, **kw)}, {})


def test_ty_le_cum_khop_den_don_vi_lam_tron():
    ds = _cac_dong(_du_lieu())
    assert [x["muc"].split(" — ")[0] for x in ds] == [
        "Tỷ lệ + KTC Wilson độc lập", "Tỷ lệ + KTC Wilson theo cụm (n/DE·(z/t)²)", "Hiệu ứng thiết kế (DE)"]
    assert all(x["trang_thai"] == "khop" for x in ds), [(x["muc"], x["kiem"], x["python"], x["r"]) for x in ds]


def test_bo_he_so_k_tren_k_tru_1_la_lech_dung_sai_chung_khong_bat_duoc():
    """Bỏ K/(K−1) chỉ dời cận KTC cụm ~0,001: dung sai chung (1,5 %) để lọt, dung sai làm tròn bắt được."""
    df = _du_lieu()
    ds = {x["muc"].split(" — ")[0]: x for x in _cac_dong(df, bo_k_tren_k_tru_1=True)}
    cum = ds["Tỷ lệ + KTC Wilson theo cụm (n/DE·(z/t)²)"]
    assert cum["trang_thai"] == "lech" and cum["kiem"]["ci"] is False, cum
    assert ds["Hiệu ứng thiết kế (DE)"]["trang_thai"] == "lech"
    assert all(S._gan(a, b, S.TOL_CI) for a, b in zip(cum["r"]["ci"], cum["python"]["ci"]))  # chung: lọt


def test_so_ca_khac_la_lech():
    import run_stats_analysis as RSA

    df = _du_lieu()
    r = _phia_r_doc_lap(df)
    r["y"]["n"] += 1
    ds = R._ty_le({"ty_le": [RSA.ty_le_wilson_cum(df, "y", None, "cum")]}, {"ty_le": r}, {})
    assert all(x["trang_thai"] == "lech" and "SỐ CA KHÁC" in x["ghi_chu"] for x in ds), ds


def test_ty_le_lech_qua_don_vi_lam_tron_la_lech():
    """Lệch 0,0002 (gấp 4 nửa đơn vị làm tròn) — dung sai chung 0,5 % để lọt — phải là LỆCH."""
    import run_stats_analysis as RSA

    df = _du_lieu()
    r = _phia_r_doc_lap(df)
    r["y"]["ty_le"] += 2e-4
    ds = R._ty_le({"ty_le": [RSA.ty_le_wilson_cum(df, "y", None, "cum")]}, {"ty_le": r}, {})
    assert ds[0]["trang_thai"] == "lech" and ds[0]["kiem"]["uoc_luong"] is False, ds[0]


def test_r_khong_ra_ty_le_la_khong_so_duoc_kem_ly_do():
    ds = R._ty_le({"ty_le": [{"cot": "y", "ty_le": 0.3, "n": 100}]}, {}, {"ty_le": "«y» phải là số"})
    assert len(ds) == 1 and ds[0]["trang_thai"] == R.DONG_KHONG_SO_DUOC and "phải là số" in ds[0]["ghi_chu"]
    ds = R._ty_le({"ty_le": [{"cot": "y", "error": "không có cột «y»"}]}, {"ty_le": {}}, {})
    assert ds[0]["trang_thai"] == R.DONG_KHONG_SO_DUOC and "Python lỗi" in ds[0]["ghi_chu"]
    assert R._ty_le({}, {}, {}) == []


def test_doi_chieu_goi_ty_le():
    df = _du_lieu()
    import run_stats_analysis as RSA

    tom = {"ty_le": [RSA.ty_le_wilson_cum(df, "y", None, "cum")], "dac_ta_phan_tich": {"cot_cum": "cum"}}
    muc = [x["muc"] for x in R.doi_chieu(tom, {"ket_qua": {"ty_le": _phia_r_doc_lap(df)}})]
    assert any(m.startswith("Tỷ lệ + KTC Wilson theo cụm") for m in muc), muc


def test_dac_ta_lech_so_ca_cot_ty_le_va_nguong():
    lech = R._dac_ta_lech({"ty_le": ["g1"], "nguong_ty_le": 4.0}, {"ty_le": ["g2"], "nguong_ty_le": 3.0})
    assert any(x.startswith("ty_le") for x in lech) and any(x.startswith("nguong_ty_le") for x in lech), lech


# ───────────────────────────── chạy thật với R ─────────────────────────────
def _co_r() -> bool:
    try:
        return bool(R.ung_vien_rscript()) and not R.kiem_moi_truong(R.tim_r())["thieu"]
    except Exception:  # noqa: BLE001
        return False


CAN_R = pytest.mark.skipif(not _co_r(), reason="máy không có Rscript hoặc thiếu gói R của cầu nối")


def _khung(tmp_path: Path, monkeypatch, study: str, df: "pd.DataFrame", tham_so: list[str]) -> Path:
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
        w.writerow(["Variable / Field Name", "Field Type", "Field Label", "Identifier?"])
        w.writerows([[c, "text", c, ""] for c in df.columns])
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(p), "--study", study, "--gate", "G6",
                                      *tham_so])
    with contextlib.redirect_stdout(io.StringIO()):
        RSA.main()
    return d


def _chay_cau_noi(study: str) -> dict:
    with contextlib.redirect_stdout(io.StringIO()):
        ma = {lenh: R.main([lenh, "--study", study]) for lenh in ("cu-phap", "chay", "doi-chieu")}
    assert ma == {"cu-phap": 0, "chay": 0, "doi-chieu": 0}, ma
    return json.loads((S.EXPORTS / study / "G6_r_doi_chieu.json").read_text(encoding="utf-8"))


def _tim_lai(py_hay_r: dict, that: float) -> bool:
    """|p̂ − p thật| ≤ 3,5 SE (SE = nửa độ rộng KTC / 1,96) — tiêu chí chọn TRƯỚC khi chạy."""
    lo, hi = py_hay_r["ci"]
    return abs(py_hay_r["uoc_luong"] - that) <= 3.5 * (hi - lo) / (2 * 1.96)


@CAN_R
def test_that_ty_le_cum_co_nguong_python_khop_r_va_kiem_cheo_g6_khop(tmp_path, monkeypatch):
    """Điểm hài lòng 1–5 trên 40 cụm (hiệu ứng cụm thật); tỷ lệ «≥ 4» thật = 0,60 (sinh trực tiếp). Lọc quần thể
    `gioi == 2` (biểu thức F3) để R phải lọc như Python. Mọi dòng Bảng 1b khớp tới đơn vị làm tròn, cả hai tìm lại tỷ lệ
    thật, `kiem_cheo_g6` chấm R KHỚP ⇒ cả lượt KHỚP (trước đây «không áp dụng»)."""
    import kiem_cheo_g6 as KC

    rng = np.random.default_rng(22)
    so_cum, m = 40, 30
    cum = np.repeat(np.arange(so_cum), m)
    lp = np.log(0.6 / 0.4) + rng.normal(0, 0.5, so_cum)[cum]
    dat = rng.binomial(1, 1 / (1 + np.exp(-lp)))
    diem = np.where(dat == 1, rng.integers(4, 6, len(cum)), rng.integers(1, 4, len(cum)))
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(len(cum))], "g1": diem.astype(float),
                       "gioi": rng.integers(1, 3, len(cum)), "cum": cum})
    df.loc[rng.random(len(cum)) < 0.05, "g1"] = np.nan
    _khung(tmp_path, monkeypatch, "TY-CUM", df,
           ["--ty-le", "g1", "--nguong-ty-le", "4", "--cot-cum", "cum", "--loc", "gioi == 2"])
    dc = _chay_cau_noi("TY-CUM")
    ty = [x for x in dc["dong"] if x["muc"].startswith(("Tỷ lệ", "Hiệu ứng thiết kế"))]
    assert len(ty) == 3 and all(x["trang_thai"] == "khop" for x in ty), [(x["muc"], x["kiem"], x["ghi_chu"])
                                                                          for x in ty]
    assert dc["dem"]["lech"] == 0 and dc["dem"]["khong_so_duoc"] == 0, dc["dem"]
    cum_dong = next(x for x in ty if "theo cụm" in x["muc"])
    n_nu = int(((df["gioi"] == 2) & df["g1"].notna()).sum())
    assert cum_dong["n"] == {"python": n_nu, "r": n_nu}
    for phia in ("python", "r"):
        assert _tim_lai(cum_dong[phia], 0.6), (phia, cum_dong[phia])
    monkeypatch.setattr(KC, "EXPORTS", S.EXPORTS)
    with contextlib.redirect_stdout(io.StringIO()):  # phần SPSS: tests/test_cau_noi_spss_ty_le_20261123.py
        assert KC.main(["chay", "--study", "TY-CUM", "--chi", "r"]) == 0
    kc = json.loads((S.EXPORTS / "TY-CUM" / "G6_kiem_cheo.json").read_text(encoding="utf-8"))
    assert kc["trang_thai"] == KC.KHOP and kc["phan_mem"]["r"]["trang_thai"] == KC.KHOP, kc


@CAN_R
def test_that_ty_le_doc_lap_cot_0_1(tmp_path, monkeypatch):
    """Không cụm, cột 0/1: chỉ một dòng Wilson độc lập, khớp; tỷ lệ thật 0,25 được tìm lại."""
    rng = np.random.default_rng(9)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(500)], "kiem_soat_ha": rng.binomial(1, 0.25, 500)})
    _khung(tmp_path, monkeypatch, "TY-DL", df, ["--ty-le", "kiem_soat_ha"])
    dc = _chay_cau_noi("TY-DL")
    ty = [x for x in dc["dong"] if x["muc"].startswith(("Tỷ lệ", "Hiệu ứng thiết kế"))]
    assert len(ty) == 1 and ty[0]["trang_thai"] == "khop", ty
    assert _tim_lai(ty[0]["python"], 0.25) and _tim_lai(ty[0]["r"], 0.25)



@CAN_R
def test_that_cum_dong_deu_de_chan_duoi_1(tmp_path, monkeypatch):
    """Mỗi cụm đúng 3/10 sự kiện ⇒ phương sai giữa cụm ≈ 0 ⇒ DE thô < 1, cả hai phía phải chặn về 1 (không để gom cụm
    làm KTC hẹp hơn giả định độc lập)."""
    rng = np.random.default_rng(3)
    y = np.concatenate([rng.permutation([1, 1, 1, 0, 0, 0, 0, 0, 0, 0]) for _ in range(30)])
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(300)], "co": y, "cum": np.repeat(np.arange(30), 10)})
    _khung(tmp_path, monkeypatch, "TY-DEU", df, ["--ty-le", "co", "--cot-cum", "cum"])
    dc = _chay_cau_noi("TY-DEU")
    de = next(x for x in dc["dong"] if x["muc"].startswith("Hiệu ứng thiết kế"))
    assert de["trang_thai"] == "khop" and de["python"]["uoc_luong"] == 1.0 and de["r"]["uoc_luong"] == 1.0, de
    assert all(x["trang_thai"] == "khop" for x in dc["dong"] if x["muc"].startswith("Tỷ lệ")), dc["dong"]


def test_cot_ty_le_vang_trong_du_lieu_khoa_thi_tu_choi(tmp_path, monkeypatch):
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"record_id": [f"R{i}" for i in range(50)], "co": rng.binomial(1, 0.3, 50)})
    d = _khung(tmp_path, monkeypatch, "TY-VANG", df, ["--ty-le", "co"])
    p = d / "G6_analysis_summary.json"
    tom = json.loads(p.read_text(encoding="utf-8"))
    assert tom["dac_ta_phan_tich"]["ty_le"] == ["co"] and tom["dac_ta_phan_tich"]["nguong_ty_le"] is None
    tom["dac_ta_phan_tich"]["ty_le"] = ["khong_co"]
    p.write_text(json.dumps(tom, ensure_ascii=False), encoding="utf-8", newline="\n")
    ra = io.StringIO()
    with contextlib.redirect_stdout(ra):
        assert R.main(["cu-phap", "--study", "TY-VANG"]) == R.MA_TU_CHOI
    assert "không có cột: khong_co" in ra.getvalue()



# ───────────────────────────── chỉ mục G6 ─────────────────────────────
def test_chi_muc_g6_ghi_phan_tram_va_ktc_tu_tom_tat_that():
    """Tóm tắt ghi tỷ lệ 0–1 + «CI_95»/«CI_95_wilson_doc_lap»; chỉ mục phải đổi sang PHẦN TRĂM + «ci_95» — bản cũ chép
    thẳng nên dòng ước lượng ra «Tỷ lệ 0,4%» và mất KTC."""
    import chay_sap_g6 as CS6
    import run_stats_analysis as RSA

    df = _du_lieu()
    for cum in ("cum", None):
        x = RSA.ty_le_wilson_cum(df, "y", None, cum)
        u = CS6._tom_tat_uoc_luong({"n_total": len(df), "ty_le": [x]})
        ci = x["CI_95"] if cum else x["CI_95_wilson_doc_lap"]
        assert u["ty_le"][0]["ty_le"] == round(100 * x["ty_le"], 2)
        assert u["ty_le"][0]["ci_95"] == [round(100 * v, 2) for v in ci]
        dong = CS6.dinh_dang_uoc_luong(u)
        assert dong == (f"Tỷ lệ {100 * x['ty_le']:.1f}% (KTC 95% {100 * ci[0]:.1f}–{100 * ci[1]:.1f}); "
                        f"n = {x['n']}").replace(".", ","), dong
