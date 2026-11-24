"""run_stats_analysis — gán đa trị theo NHÁNH cho biến phái sinh và MI + Poisson vững theo CỤM (22/11/2026).

Hai giới hạn đo được ở đề tài BTM:
  (a) `hba1c_3muc` = neu(co_hba1c == 0, 3, neu(hba1c_gt < 7, 1, 2)) thiếu khi co_hba1c = 1 mà hba1c_gt trống. MICE
      dựng sẵn gán THẲNG biến phái sinh (pmm rút mã từ mọi người) ⇒ có thể gán mức 3 «không làm HbA1c» cho người ĐÃ
      làm. Nay: từ điển REDCap khai hba1c_gt «chỉ hiện khi [co_hba1c] = '1'» ⇒ gán hba1c_gt trong đúng nhóm con rồi
      tính lại hba1c_3muc từ công thức đã duyệt.
  (b) MI + Poisson vững theo cụm trả lỗi «chưa hỗ trợ». Nay: GLM Poisson + sandwich theo cụm trên từng bộ, gộp Rubin
      (White, Royston & Wood, Stat Med 2011, PMID 21225900), suy luận t(G−1). Kiểm bằng mô phỏng có tham số biết trước.
Dữ liệu đều là mô phỏng; không PII.
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

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import bien_phai_sinh as BPS  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

LOG_PR_X1, LOG_PR_X2 = np.log(1.3), np.log(1.5)


# ───────────────────────────── (b) MI + Poisson vững theo cụm ─────────────────────────────
def _mo_phong_cum(n: int, so_cum: int, seed: int, ty_le_thieu: float = 0.2) -> "pd.DataFrame":
    """Kết cục 0/1 với P(y=1) = 0,15·1,3^x1·1,5^x2·e^u (u ~ N(0; 0,2²) theo cụm, độc lập với x) ⇒ log PR biên của x1,
    x2 đúng bằng log 1,3 và log 1,5. x1 thiếu hoàn toàn ngẫu nhiên (MCAR) theo `ty_le_thieu`."""
    rng = np.random.default_rng(seed)
    cum = np.repeat(np.arange(so_cum), n // so_cum)
    u = rng.normal(0, 0.2, so_cum)[cum]
    x1 = rng.normal(0, 1, len(cum))
    x2 = rng.binomial(1, 0.4, len(cum))
    p = np.clip(0.15 * np.exp(LOG_PR_X1 * x1 + LOG_PR_X2 * x2 + u), 0, 0.99)
    df = pd.DataFrame({"y": rng.binomial(1, p), "x2": x2, "x1": x1, "cum": cum})
    df.loc[rng.random(len(df)) < ty_le_thieu, "x1"] = np.nan
    return df


def _uoc(mi: dict, bien: str) -> dict:
    return next(r for r in mi["results"] if r["variable"] == bien)


def test_mi_poisson_cum_tim_lai_tham_so_that():
    # 24/11/2026 — nguyên nhân THẬT của λ_x1 = 0,594 trên CI Ubuntu (Haswell), 0,147 (SkylakeX), 0,294 (Mac): bước PMM
    # của statsmodels MICEData (argsort không ổn định trên trung bình dự đoán chỉ 4 mức — sắp xếp SIMD theo CPU; cửa sổ
    # searchsorted ± k chung cho cả nhóm trùng; so khớp kiểu 2), KHÔNG phải nhiễu Monte Carlo hay OpenBLAS đa luồng như
    # chú thích 23/11 (m = 40 vẫn ra 0,594 trên Haswell). Bộ gán mới BoGanPMM (PMM kiểu 1 tham số bootstrap, người cho
    # chọn riêng từng ca, phá thế trùng ngẫu nhiên) cho λ đúng lý thuyết ≈ 0,2 (= tỷ lệ thiếu: bộ gán không thêm thông
    # tin về x1) và tất định theo hạt giống trên mọi máy: 16 hạt giống ⇒ λ 0,10–0,29, TB 0,193, SD 0,045
    # (≈ 0,2·√(2/39)).
    # m = 40 giữ để λ̂ đủ chính xác cho khẳng định dưới (m ≥ 100·λ ≈ 20 — White, Royston & Wood 2011, PMID 21225900);
    # ngưỡng giữ nguyên.
    mi = RSA.multiple_imputation_model(_mo_phong_cum(3000, 60, 1), "y", "x2", ["x1"], "poisson_pr", 40, "cum", {})
    assert mi["model"] == "poisson_cluster_mi" and mi["cluster"] == {"cot": "cum", "so_cum": 60}
    assert mi["bo_may"] == "tu_lap" and "PMID 21225900" in mi["phuong_phap_gop"]
    for bien, that in (("x1", 1.3), ("x2", 1.5)):
        r = _uoc(mi, bien)
        assert r["CI_95"][0] < that < r["CI_95"][1], (bien, r)
        assert r["PR_adj"] == pytest.approx(that, rel=0.08), (bien, r)
    assert 0.05 < mi["ty_le_thong_tin_thieu"]["x1"] < 0.5  # x1 thiếu 20 % ⇒ có thông tin thiếu
    assert "PR (MI)" in RSA.format_mi_text(mi) and "theo cụm" in RSA.format_mi_text(mi)


def test_mi_poisson_cum_do_phu_khoang_tin_cay_qua_nhieu_lan_lap():
    """30 lần lặp nhỏ (600 người, 30 cụm, m = 5): độ phủ KTC 95 % của log PR(x1) và trung bình ước lượng sát thật."""
    np.random.seed(7)
    phu, uoc = 0, []
    for lan in range(30):
        r = _uoc(RSA.multiple_imputation_model(_mo_phong_cum(600, 30, 100 + lan), "y", "x2", ["x1"], "poisson_pr", 5,
                                               "cum", {}), "x1")
        phu += r["CI_95"][0] <= 1.3 <= r["CI_95"][1]
        uoc.append(np.log(r["PR_adj"]))
    assert 0.8 <= phu / 30 <= 1.0, phu
    assert abs(np.mean(uoc) - LOG_PR_X1) < 0.05, np.mean(uoc)


def test_gop_rubin_dung_cong_thuc():
    """Q̄ = trung bình; T = Ū + (1 + 1/m)·B — tính tay với m = 2."""
    q_bar, se, lam = RSA._gop_rubin([[1.0], [3.0]], [[[0.5]], [[1.5]]])
    assert q_bar[0] == pytest.approx(2.0)
    assert se[0] == pytest.approx(np.sqrt(1.0 + 1.5 * 2.0))  # Ū = 1; B = var(1, 3) = 2
    assert lam[0] == pytest.approx(3.0 / 4.0)


def test_mi_poisson_cum_it_cum_bao_loi_ro():
    df = _mo_phong_cum(200, 2, 3)
    df["cum"] = 0
    mi = RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "poisson_pr", 2, "cum", {})
    assert "chỉ có 1 giá trị" in mi["error"]


# ───────────────────────────── (a) gán theo nhánh ─────────────────────────────
_TU_DIEN = ["Variable / Field Name", "Form Name", "Field Type", "Field Label",
            "Choices, Calculations, OR Slider Labels", "Text Validation Type OR Show Slider Number",
            "Branching Logic (Show field only if...)"]
_PS = ["ten_bien", "nhan", "kieu", "dinh_nghia", "bien_nguon", "quy_tac_ma_thieu", "dung_o", "nguon", "cong_thuc",
       "lap_k", "nhan_gia_tri", "nguoi_duyet"]
CT_HBA1C = "neu(co_hba1c == 0, 3, neu(hba1c_gt < 7, 1, 2))"


def _ghi_csv(p: Path, cot: list, hang: list) -> None:
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cot)
        w.writerows(hang)


def _de_tai(d: Path, nhanh_hba1c: str = "[co_hba1c] = '1'", them_ps: tuple = ()) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    _ghi_csv(d / BPS.TEP_BO_BIEN, _TU_DIEN, [
        ["record_id", "f", "text", "Mã", "", "", ""],
        ["y", "f", "yesno", "Không xét nghiệm đủ", "", "", ""],
        ["tuoi", "f", "text", "Tuổi", "", "number", ""],
        ["co_hba1c", "f", "radio", "Có HbA1c", "1, Có | 0, Không", "", ""],
        ["hba1c_gt", "f", "text", "HbA1c (%)", "", "number", nhanh_hba1c],
        ["benh_kem", "f", "checkbox", "Bệnh kèm", "1, THA | 2, Tim", "", "[co_hba1c] = '1'"],
    ])
    _ghi_csv(d / BPS.TEP_DAC_TA, _PS, [["hba1c_3muc", "HbA1c 3 mức", "Phân loại", "", "co_hba1c hba1c_gt", "", "",
                                        "", CT_HBA1C, "", "1, < 7 | 2, ≥ 7 | 3, Không làm", ""],
                                       *[[t, t, "", "", "", "", "", "", ct, "", "", ""] for t, ct in them_ps]])
    return d


def _du_lieu_hba1c(n: int = 1200, seed: int = 11) -> "pd.DataFrame":
    """co_hba1c = 1 ở ~70 %; hba1c_gt chỉ có khi co_hba1c = 1 (nhánh), thiếu 30 % trong nhóm đó (hồ sơ không ghi)."""
    rng = np.random.default_rng(seed)
    tuoi = rng.normal(60, 10, n)
    co = rng.binomial(1, 0.7, n)
    gt = np.where(co == 1, rng.normal(7.2 + 0.03 * (tuoi - 60), 1.0, n), np.nan)
    muc = np.where(co == 0, 3, np.where(gt < 7, 1, 2))
    p = np.clip(0.3 * np.exp(0.2 * (muc == 2) + 0.4 * (muc == 3) + 0.01 * (tuoi - 60)), 0, 0.99)
    df = pd.DataFrame({"y": rng.binomial(1, p), "tuoi": tuoi, "co_hba1c": co, "hba1c_gt": gt})
    df.loc[(df["co_hba1c"] == 1) & (rng.random(n) < 0.3), "hba1c_gt"] = np.nan
    return df


def _ke_hoach_va_df(tmp_path: Path, **kw):
    d = _de_tai(tmp_path / "exports" / "NH", **kw)
    df = _du_lieu_hba1c()
    kh = BPS.ke_hoach_gan_thu_dong(d, "NH", ["y", "tuoi", "hba1c_3muc"], df.columns)
    df["hba1c_3muc"] = kh.tinh_lai(df, ["hba1c_3muc"])["hba1c_3muc"].to_numpy()  # như main(): tính trước khi phân tích
    return kh, df


def test_ke_hoach_doc_nhanh_tu_tu_dien_khong_viet_cung_ten(tmp_path):
    kh, df = _ke_hoach_va_df(tmp_path)
    assert kh.nguon_cua == {"hba1c_3muc": ["co_hba1c", "hba1c_gt"]}
    assert kh.nhanh == {"hba1c_gt": "[co_hba1c] = '1'"}
    assert kh.dm.nhanh["benh_kem___2"] == "[co_hba1c] = '1'"  # cột con checkbox thừa hưởng nhánh
    thieu = df["hba1c_3muc"].isna()
    assert thieu.any() and (df.loc[thieu, "co_hba1c"] == 1).all()
    assert BPS.ke_hoach_gan_thu_dong(tmp_path / "exports" / "NH", "NH", ["tuoi"], df.columns) is None
    # gọi SAU khi biến phái sinh đã là một cột của dữ liệu (như trong main()) vẫn ra đúng kế hoạch
    assert BPS.ke_hoach_gan_thu_dong(tmp_path / "exports" / "NH", "NH", ["hba1c_3muc"], df.columns).nguon_cua == \
        kh.nguon_cua


def test_gan_theo_nhanh_khong_gan_muc_khong_lam_cho_nguoi_da_lam(tmp_path):
    kh, df = _ke_hoach_va_df(tmp_path)
    df, bg = RSA.mo_rong_bien_gia(df, ["hba1c_3muc"])
    np.random.seed(5)
    mi = RSA.multiple_imputation_model(df, "y", "tuoi", ["hba1c_3muc"], "poisson_pr", 10, None, bg, kh)
    assert mi["model"] == "poisson_hc0_mi" and mi["bo_may"] == "tu_lap", mi
    gn = mi["gan_theo_nhanh"]["bien"]["hba1c_3muc"]
    assert gn["so_o_gan"] == int(df["hba1c_3muc"].isna().sum())
    assert set(gn["ma_da_gan"]) <= {"1", "2"}, gn  # mã 3 «không làm HbA1c» không bao giờ gán cho người đã làm
    assert sum(gn["ma_da_gan"].values()) == gn["so_o_gan"] * 10
    assert mi["gan_theo_nhanh"]["so_hang_ngoai_nhanh"]["hba1c_gt"] == int((df["co_hba1c"] == 0).sum())
    assert {r["variable"] for r in mi["results"]} == {"tuoi", "hba1c_3muc_2", "hba1c_3muc_3"}
    van = RSA.format_mi_text(mi)
    assert "Gán theo nhánh «hba1c_3muc»" in van and "[co_hba1c] = '1'" in van


def test_khong_ke_hoach_thi_khong_gan_theo_nhanh(tmp_path):
    """Không có kế hoạch gán thụ động ⇒ không gán theo nhánh. 24/11/2026: mọi gán đa trị không ghép cặp đi qua bộ máy
    tự lập (BoGanPMM) — MICE dựng sẵn của statsmodels đã bỏ (kết quả phụ thuộc CPU và thứ tự hàng)."""
    _kh, df = _ke_hoach_va_df(tmp_path)
    df, bg = RSA.mo_rong_bien_gia(df, ["hba1c_3muc"])
    mi = RSA.multiple_imputation_model(df, "y", "tuoi", ["hba1c_3muc"], "poisson_pr", 3, None, bg)
    assert mi["model"] == "poisson_hc0_mi" and mi["bo_may"] == "tu_lap" and "gan_theo_nhanh" not in mi
    assert mi["phuong_phap_gan"] == RSA.NGUON_PMM


def test_bien_phai_sinh_chi_xac_dinh_trong_nhom_con_khong_bi_gan_ngoai_nhom(tmp_path):
    """`hba1c_cao` = neu(hba1c_gt >= 7, 1, 0) không xác định khi không làm HbA1c (nhánh không thoả). Bộ gán KHÔNG được
    bịa giá trị cho hàng ngoài nhóm con ⇒ báo lỗi kèm lý do (biến chỉ xác định trong nhóm con không làm hiệp biến cho
    cả quần thể), thay vì ra ước lượng trên giá trị gán ngoài nhánh."""
    d = _de_tai(tmp_path / "exports" / "NH", them_ps=(("hba1c_cao", "neu(hba1c_gt >= 7, 1, 0)"),))
    df = _du_lieu_hba1c()
    kh = BPS.ke_hoach_gan_thu_dong(d, "NH", ["y", "tuoi", "hba1c_cao"], df.columns)
    df["hba1c_cao"] = kh.tinh_lai(df, ["hba1c_cao"])["hba1c_cao"].to_numpy()
    np.random.seed(3)
    mi = RSA.multiple_imputation_model(df, "y", "tuoi", ["hba1c_cao"], "poisson_pr", 2, None, {}, kh)
    assert "ngoài nhóm con" in mi.get("error", ""), mi


def test_nhanh_cua_bien_phai_sinh_khong_thieu_khong_duoc_danh_gia(tmp_path):
    """Nhánh chỉ đánh giá cho cột nguồn của biến phái sinh CÒN THIẾU: một biến phái sinh đủ dữ liệu có nguồn mang nhánh
    tham chiếu cột vắng (vd trường calc không tính vì không dùng) không được làm hỏng cả lượt gán."""
    d = _de_tai(tmp_path / "exports" / "NH", them_ps=(("tuoi_10", "tuoi / 10"),))
    p = d / BPS.TEP_BO_BIEN
    p.write_text(p.read_text(encoding="utf-8").replace("Tuổi,,number,", "Tuổi,,number,[calc_vang] = '1'"),
                 encoding="utf-8", newline="\n")
    df = _du_lieu_hba1c()
    kh = BPS.ke_hoach_gan_thu_dong(d, "NH", ["y", "tuoi_10", "hba1c_3muc"], df.columns)
    assert kh.nhanh.get("tuoi") == "[calc_vang] = '1'"
    moi = kh.tinh_lai(df, ["hba1c_3muc", "tuoi_10"])
    df["hba1c_3muc"], df["tuoi_10"] = moi["hba1c_3muc"].to_numpy(), moi["tuoi_10"].to_numpy()
    df, bg = RSA.mo_rong_bien_gia(df, ["hba1c_3muc"])
    np.random.seed(4)
    mi = RSA.multiple_imputation_model(df, "y", "tuoi_10", ["hba1c_3muc"], "poisson_pr", 2, None, bg, kh)
    assert mi.get("bo_may") == "tu_lap" and "error" not in mi, mi


def test_nhanh_can_cot_vang_thi_bao_loi_khong_doan(tmp_path):
    kh, df = _ke_hoach_va_df(tmp_path, nhanh_hba1c="[co_hba1c] = '1' and [cot_khong_co] = '1'")
    df, bg = RSA.mo_rong_bien_gia(df, ["hba1c_3muc"])
    mi = RSA.multiple_imputation_model(df, "y", "tuoi", ["hba1c_3muc"], "poisson_pr", 2, None, bg, kh)
    assert "cot_khong_co" in mi["error"], mi


def test_main_noi_ke_hoach_gan_theo_nhanh(tmp_path, monkeypatch):
    """main() dựng kế hoạch từ thư mục đề tài và truyền cho MI — kết quả G6 mang «gan_theo_nhanh»."""
    d = _de_tai(tmp_path / "exports" / "NH")
    (d / "study_meta.json").write_text(json.dumps({"study_kind": "synthetic_test"}), encoding="utf-8", newline="\n")
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA, "_g4_khoa_song", lambda study: (True, "giả lập: G4 khoá sống"))
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    (d / "05_clean_locked").mkdir(parents=True, exist_ok=True)
    k = d / "05_clean_locked" / "k.csv"
    _du_lieu_hba1c(600).assign(record_id=lambda x: [f"R{i}" for i in range(len(x))]).to_csv(k, index=False)
    man = {"locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
           "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda study, _d: man)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(k), "--study", "NH", "--gate", "G6",
                                      "--n-imputations", "3", "--outcome", "y", "--group", "tuoi",
                                      "--covariates", "hba1c_3muc", "--outcome-type", "poisson_pr",
                                      "--hiep-bien-phan-loai", "hba1c_3muc"])
    np.random.seed(9)
    with contextlib.redirect_stdout(io.StringIO()):
        RSA.main()
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    mi = tom["multiple_imputation"]
    assert set(mi["gan_theo_nhanh"]["bien"]["hba1c_3muc"]["ma_da_gan"]) <= {"1", "2"}, mi


def _mo_phong_cum_muc_cum(so_cum: int, moi_cum: int, seed: int) -> "pd.DataFrame":
    """x2 ở MỨC CỤM (hằng trong cụm) và hiệu ứng cụm mạnh ⇒ sai số chuẩn theo cụm lớn hơn hẳn HC0."""
    rng = np.random.default_rng(seed)
    cum = np.repeat(np.arange(so_cum), moi_cum)
    u = rng.normal(0, 0.5, so_cum)[cum]
    x2 = rng.binomial(1, 0.5, so_cum)[cum]
    x1 = rng.normal(0, 1, len(cum))
    p = np.clip(0.12 * np.exp(LOG_PR_X1 * x1 + LOG_PR_X2 * x2 + u), 0, 0.99)
    df = pd.DataFrame({"y": rng.binomial(1, p), "x2": x2, "x1": x1, "cum": cum})
    df.loc[rng.random(len(df)) < 0.15, "x1"] = np.nan
    return df


def test_mi_poisson_cum_dung_sai_so_chuan_theo_cum_va_t_g_tru_1():
    """KTC của biến mức cụm phải rộng như complete-case theo cụm (CR1), không hẹp như HC0; p khớp t(G−1)."""
    df = _mo_phong_cum_muc_cum(8, 120, 4)
    np.random.seed(11)
    mi = RSA.multiple_imputation_model(df, "y", "x2", ["x1"], "poisson_pr", 10, "cum", {})
    cc = RSA.poisson_pr_model(df, "y", "x2", ["x1"], cluster_col="cum")
    r, rc = _uoc(mi, "x2"), next(x for x in cc["results"] if x["variable"] == "x2")
    rong = np.log(r["CI_95"][1] / r["CI_95"][0])
    assert rong >= 0.8 * np.log(rc["CI_95"][1] / rc["CI_95"][0]), (r, rc)
    # thống kê t = log PR / SE với SE = nửa KTC / t(0,975; G−1) ⇒ p hai phía theo t(7) phải trùng p báo cáo
    from scipy import stats as st
    se = rong / 2 / st.t.ppf(0.975, 7)
    assert r["p"] == pytest.approx(2 * st.t.sf(abs(np.log(r["PR_adj"]) / se), 7), abs=0.003), r


def test_cot_nguon_co_nhanh_khong_lam_bien_du_bao_va_an_gia_tri_ngoai_nhanh(tmp_path, monkeypatch):
    """Cột nguồn có nhánh: (1) giá trị ở hàng nhánh không thoả không vào dữ liệu gán; (2) không làm biến dự báo cho cột
    khác (ngoài nhóm con nó không có nghĩa)."""
    kh, df = _ke_hoach_va_df(tmp_path)
    df.loc[df.index[:40], "tuoi"] = np.nan
    an = df.index[(df["co_hba1c"] == 0)][:5]
    df.loc[an, "hba1c_gt"] = 99.0  # dữ liệu mâu thuẫn nhánh (trường ẩn mà có giá trị)
    df, bg = RSA.mo_rong_bien_gia(df, ["hba1c_3muc"])
    bat: dict = {}

    class BatBoGan(RSA.BoGanPMM):  # 24/11/2026: bộ gán BoGanPMM thay MICEData
        def __init__(self, khung, *a, **k):
            bat["khung"] = khung.copy()
            super().__init__(khung, *a, **k)
            bat["bg"] = self

    monkeypatch.setattr(RSA, "BoGanPMM", BatBoGan)
    mi = RSA.multiple_imputation_model(df, "y", "tuoi", ["hba1c_3muc"], "poisson_pr", 2, None, bg, kh)
    assert mi.get("bo_may") == "tu_lap", mi
    assert bat["khung"].loc[an, "hba1c_gt"].isna().all()
    assert "hba1c_gt" not in bat["bg"].du_bao["tuoi"]
    assert "co_hba1c" in bat["bg"].du_bao["tuoi"]
