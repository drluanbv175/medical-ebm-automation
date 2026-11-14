"""F2 (14/11/2026) — Poisson vững (PR) + hiệp biến phân loại cho run_stats_analysis và cầu nối SPSS/R.

Soát chuỗi SPSS/R theo yêu cầu bác sĩ: (1) SAP BTM mục tiêu 3 cam kết hồi quy Poisson liên kết log phương sai vững để
ước lượng PR — Python, SPSS, R đều chưa có; (2) cả ba phần mềm coi hiệp biến PHÂN LOẠI mã số (khung giờ 1–4, nhóm đối
tượng 1–4…) là LIÊN TỤC — kiểm chéo vẫn «khớp» nhưng mô hình lệch SAP («biến phân loại k mức tính k−1»).

Fixture `tests/fixtures/spss_oxml/poisson/` là đầu ra THẬT của SPSS 31.0.1 (OXML) và R 4.6.2 (G6_r_ket_qua.json) chạy
14/11/2026 trên dữ liệu giả 600 ca (3 hiệp biến phân loại, có ô thiếu) — test chạy được khi máy không có SPSS/R.
Không PII.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
np = pytest.importorskip("numpy")
pd = pytest.importorskip("pandas")
pytest.importorskip("statsmodels")
import cau_noi_r as R  # noqa: E402
import cau_noi_spss as S  # noqa: E402
import run_stats_analysis as RSA  # noqa: E402

FX = Path(__file__).resolve().parent / "fixtures" / "spss_oxml" / "poisson"


# ───────────────────────── biến giả hiệp biến phân loại ─────────────────────────


def test_bien_gia_tham_chieu_ma_nho_nhat_va_thieu_lan_truyen():
    df = pd.DataFrame({"kg": [3, 1, 2, None, 3, 1], "x": [1, 2, 3, 4, 5, 6]})
    df2, bg = RSA.mo_rong_bien_gia(df, ["kg"])
    assert bg == {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}
    assert df2["kg_2"].tolist()[:3] == [0.0, 0.0, 1.0] and pd.isna(df2["kg_3"].iloc[3])
    assert df2["kg_3"].tolist()[4] == 1.0 and "kg" in df2 and list(df.columns) == ["kg", "x"]
    assert RSA.mo_rong_hiep_bien(["x", "kg", "y"], bg) == ["x", "kg_2", "kg_3", "y"]


@pytest.mark.parametrize(
    "gia_tri, mau",
    [
        (["1", "2", "KDD"], "không phải số"),
        ([1.5, 2, 1], "nguyên ≥ 0"),
        ([-1, 2, 1], "nguyên ≥ 0"),
        ([2, 2, None], "chỉ có 1 mức"),
    ],
)
def test_bien_gia_tu_choi_ma_khong_hop_le(gia_tri, mau):
    with pytest.raises(RSA.LoiBienPhanLoai, match=mau):
        RSA.mo_rong_bien_gia(pd.DataFrame({"kg": gia_tri}), ["kg"])


def test_bien_gia_trung_ten_cot_bi_chan():
    with pytest.raises(RSA.LoiBienPhanLoai, match="trùng một cột"):
        RSA.mo_rong_bien_gia(pd.DataFrame({"kg": [1, 2, 1], "kg_2": [0, 0, 0]}), ["kg"])
    with pytest.raises(RSA.LoiBienPhanLoai, match="không có trong dữ liệu"):
        RSA.mo_rong_bien_gia(pd.DataFrame({"a": [1, 2]}), ["kg"])


# ───────────────────────── Poisson vững HC0 ─────────────────────────


def _du_lieu_pr(n: int = 400, seed: int = 3) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    g = rng.integers(0, 2, n)
    kg = rng.choice([1, 2, 3], n)
    tuoi = rng.normal(55, 10, n).round(1)
    p = np.clip(np.exp(-1.2 + 0.5 * g + 0.2 * (kg == 2) + 0.004 * (tuoi - 55)), 0, 0.95)
    df = pd.DataFrame({"y": (rng.random(n) < p).astype(int), "g": g, "kg": kg, "tuoi": tuoi})
    df.loc[rng.random(n) < 0.08, "tuoi"] = np.nan
    return df


def test_pr_tho_bang_ty_so_ty_le_va_se_hc0_bang_cong_thuc_delta():
    """Một biến nhị phân: PR Poisson = p1/p0 đúng tuyệt đối; SE vững HC0 của log PR = √[(1−p1)/(n1·p1) + (1−p0)/(n0·p0)]
    (Zou 2004) — kiểm độc lập với statsmodels, cùng TẬP CA đầy đủ (tuổi thiếu bị loại cả ở PR thô)."""
    df = _du_lieu_pr()
    pr = RSA.poisson_pr_model(df, "y", "g", ["tuoi"])
    d = df.dropna()
    p1, p0 = d.loc[d.g == 1, "y"].mean(), d.loc[d.g == 0, "y"].mean()
    n1, n0 = (d.g == 1).sum(), (d.g == 0).sum()
    r = next(x for x in pr["tho"] if x["variable"] == "g")
    assert r["PR"] == pytest.approx(p1 / p0, abs=5e-5) and pr["n"] == len(d)
    se = np.sqrt((1 - p1) / (n1 * p1) + (1 - p0) / (n0 * p0))
    assert r["CI_95"] == pytest.approx([p1 / p0 * np.exp(-1.959964 * se), p1 / p0 * np.exp(1.959964 * se)], abs=2e-4)
    assert {x["variable"] for x in pr["results"]} == {"g", "tuoi"} and pr["phuong_sai"].startswith("HC0")


def test_pr_bien_phan_loai_cac_bien_gia_chung_mot_mo_hinh_tho():
    df, bg = RSA.mo_rong_bien_gia(_du_lieu_pr(), ["kg"])
    pr = RSA.poisson_pr_model(df, "y", "g", ["tuoi", "kg"], bg)
    assert [x["variable"] for x in pr["tho"]] == ["g", "tuoi", "kg_2", "kg_3"]
    assert [x["variable"] for x in pr["results"]] == ["g", "tuoi", "kg_2", "kg_3"]
    assert pr["nhom_bien"] == {"g": ["g"], "tuoi": ["tuoi"], "kg": ["kg_2", "kg_3"]}


def test_pr_tu_choi_cum_va_ket_cuc_khong_nhi_phan():
    df = _du_lieu_pr()
    assert "cụm" in RSA.poisson_pr_model(df, "y", "g", ["tuoi"], cluster_col="kg")["error"]
    df["y"] = df["y"] * 2
    assert "0/1" in RSA.poisson_pr_model(df, "y", "g", ["tuoi"])["error"]


def test_mi_poisson_ten_bien_gia_va_mo_hinh():
    df, bg = RSA.mo_rong_bien_gia(_du_lieu_pr(n=1500, seed=5), ["kg"])
    np.random.seed(20261114)  # MICE dùng bộ sinh số ngẫu nhiên toàn cục của numpy
    mi = RSA.multiple_imputation_model(df, "y", "g", ["tuoi", "kg"], "poisson_pr", 5, None, bg)
    assert mi["model"] == "poisson_hc0_mi"
    assert {r["variable"] for r in mi["results"]} == {"g", "tuoi", "kg_2", "kg_3"}
    # 8 % thiếu ở tuổi ⇒ PR gộp phải sát PR complete-case; lỡ chạy logistic thì ra OR (xa PR rõ rệt khi tỷ lệ ~30–50 %)
    cc = RSA.poisson_pr_model(df, "y", "g", ["tuoi", "kg"], bg)
    pr_mi = next(r["PR_adj"] for r in mi["results"] if r["variable"] == "g")
    pr_cc = next(r["PR_adj"] for r in cc["results"] if r["variable"] == "g")
    assert pr_mi == pytest.approx(pr_cc, rel=0.10), (pr_mi, pr_cc)
    assert "cụm" in RSA.multiple_imputation_model(df, "y", "g", ["tuoi"], "poisson_pr", 2, "kg", bg)["error"]


# ───────────────────────── run_stats_analysis main ─────────────────────────


def _main(tmp_path: Path, monkeypatch, them: list[str], df: pd.DataFrame | None = None) -> tuple[Path, str]:
    locked = {"g2_status": "LOCKED", "g4_status": "LOCKED", "g5_status": "LOCKED"}
    monkeypatch.setattr(RSA, "BASE", tmp_path)
    monkeypatch.setattr(RSA, "_load_checkpoint", lambda study, gate: dict(locked))
    monkeypatch.setattr(RSA, "_ledger_approved", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "g2_quality_contract_satisfied", lambda *a, **k: True)
    monkeypatch.setattr(RSA.GC, "resolve_design_code", lambda *a, **k: ("cross_sectional", None))
    monkeypatch.setattr(RSA.G5Q, "evaluate_study", lambda *a, **k: {"status": RSA.G5Q.STATUS_LOCKED})
    d = tmp_path / "exports" / "PR"
    (d / "05_clean_locked").mkdir(parents=True, exist_ok=True)
    k = d / "05_clean_locked" / "k.csv"
    (df if df is not None else _du_lieu_pr()).to_csv(k, index=False)
    man = {"locked_dataset_path": "05_clean_locked/k.csv", "sha256": hashlib.sha256(k.read_bytes()).hexdigest(),
           "status": "LOCKED_FOR_ANALYSIS", "analysis_allowed": True}  # fmt: skip
    monkeypatch.setattr(RSA, "_require_locked_analysis_dataset", lambda study, _d: man)
    monkeypatch.setattr(sys, "argv", ["run_stats_analysis.py", "--data", str(k), "--study", "PR", "--gate", "G6",
                                      "--n-imputations", "2", *them])  # fmt: skip
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        RSA.main()
    return d, buf.getvalue()


def test_main_poisson_phan_loai_ghi_tom_tat_va_bang(tmp_path, monkeypatch):
    d, ra = _main(tmp_path, monkeypatch, ["--outcome", "y", "--group", "g", "--covariates", "tuoi,kg",
                                          "--outcome-type", "poisson_pr", "--hiep-bien-phan-loai", "kg"])  # fmt: skip
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert tom["dac_ta_phan_tich"]["hiep_bien_phan_loai"]["kg"]["ten"] == ["kg_2", "kg_3"]
    assert tom["dac_ta_phan_tich"]["covariates"] == ["tuoi", "kg"]  # cầu nối nhận tên GỐC + bảng biến giả
    assert tom["poisson_pr"]["model"] == "poisson_robust_hc0" and "multivariate" not in tom
    assert tom["primary_outcome"]["outcome_type"] == "binary"  # so thô như nhị phân
    assert tom["multiple_imputation"]["model"] == "poisson_hc0_mi"
    bang = (d / "G6_table4_poisson_pr.txt").read_text(encoding="utf-8")
    assert "PR THÔ" in bang and "kg_3" in bang and "HC0" in bang
    assert "kg_2" not in (d / "G6_table1_descriptive.txt").read_text(encoding="utf-8")  # Bảng 1 dùng cột gốc


def test_main_logistic_dung_bien_gia_cua_hiep_bien_phan_loai(tmp_path, monkeypatch):
    d, _ra = _main(tmp_path, monkeypatch, ["--outcome", "y", "--group", "g", "--covariates", "kg",
                                           "--outcome-type", "binary", "--hiep-bien-phan-loai", "kg"])  # fmt: skip
    tom = json.loads((d / "G6_analysis_summary.json").read_text(encoding="utf-8"))
    assert [r["variable"] for r in tom["multivariate"]["results"]] == ["g", "kg_2", "kg_3"]


@pytest.mark.parametrize(
    "them, mau",
    [
        (["--covariates", "tuoi", "--hiep-bien-phan-loai", "kg"], "phải nằm trong --covariates"),
        (["--covariates", "tuoi", "--hiep-bien-phan-loai", "tuoi"], "nguyên ≥ 0"),
    ],
)
def test_main_bien_phan_loai_sai_thi_dung(tmp_path, monkeypatch, them, mau):
    with pytest.raises(SystemExit) as e:
        _main(tmp_path, monkeypatch, ["--outcome", "y", "--group", "g", "--outcome-type", "binary", *them])
    assert e.value.code == 1


# ───────────────────────── cầu nối SPSS ─────────────────────────


def _man(cot_so: dict[str, bool]) -> dict:
    return {"sav": "/tmp/x.sav", "bien": [{"cot": c, "ten": c, "so": so, "bo": False, "muc": ["0", "1"], "nhan": c,
                                           "nhan_gia_tri": {}, "ma_chu": {}} for c, so in cot_so.items()]}  # fmt: skip


def test_spss_them_bien_gia_va_cu_phap_poisson(tmp_path):
    bg = {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}
    dt = {"outcome": "y", "group": "g", "covariates": ["tuoi", "kg"], "covariates_mo_hinh": ["tuoi", "kg_2", "kg_3"],
          "outcome_type": "poisson_pr", "time": None, "event": None, "cot_cum": None, "don_vi_phoi_nhiem": None,
          "hiep_bien_phan_loai": bg}  # fmt: skip
    man = S.them_bien_gia(_man({"y": True, "g": True, "tuoi": True, "kg": True}), dt)
    assert "IF (NOT MISSING(kg)) kg_3 = (kg = 3)." in man["khoi_bien_gia"]
    vb, _cb, phu = S.cu_phap_phan_tich("PR", man, dt, tmp_path)
    assert phu["poisson_nhom_bien"] == [["g"], ["tuoi"], ["kg_2", "kg_3"]]
    assert vb.count("DISTRIBUTION=POISSON LINK=LOG") == 4 and vb.count("COVB=ROBUST") == 4
    assert vb.count("TEMPORARY.") == 3 and "LOGISTIC REGRESSION" not in vb  # thô: cùng tập ca; không chạy logistic
    assert vb.index("kg_2 = (kg = 2)") < vb.index("GENLIN y")
    with pytest.raises(S.TuChoi, match="CHUỖI"):
        S.them_bien_gia(_man({"kg": False}), dt)
    with pytest.raises(S.TuChoi, match="không có trong .sav"):
        S.them_bien_gia(_man({"y": True}), dt)


def test_spss_doc_va_doi_chieu_poisson_tu_dau_ra_that(tmp_path):
    kq_dir = tmp_path / "kq"
    kq_dir.mkdir()
    for f in FX.glob("oms_*.xml"):
        shutil.copy(f, kq_dir / f.name)
    tom = json.loads((FX / "tom_tat_python.json").read_text(encoding="utf-8"))
    dt = {"outcome": "khong_xn_du", "group": "insulin", "outcome_type": "poisson_pr"}
    man = {"bien": []}
    kq = S.doc_ket_qua(kq_dir, dt, man)
    assert set(kq["poisson_hieu_chinh"]["he_so"]) == {r["variable"] for r in tom["poisson_pr"]["results"]}
    assert set(kq["poisson_tho"]["he_so"]) == {r["variable"] for r in tom["poisson_pr"]["tho"]}
    dong = S.doi_chieu(tom, kq)
    pois = [x for x in dong if x["muc"].startswith("Poisson")]
    lech = [x for x in pois if x["trang_thai"] != "khop"]
    assert len(pois) == 18 and not lech, lech


def test_spss_logistic_vao_bien_gia_khong_vao_ma_goc(tmp_path):
    bg = {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}
    dt = {"outcome": "y", "group": "g", "covariates": ["kg"], "covariates_mo_hinh": ["kg_2", "kg_3"],
          "outcome_type": "binary", "time": None, "event": None, "cot_cum": None, "don_vi_phoi_nhiem": None,
          "hiep_bien_phan_loai": bg}  # fmt: skip
    man = S.them_bien_gia(_man({"y": True, "g": True, "kg": True}), dt)
    vb, _cb, _phu = S.cu_phap_phan_tich("LG", man, dt, tmp_path)
    vao = next(x for x in vb.splitlines() if "/METHOD=ENTER" in x)
    assert vao.split("ENTER", 1)[1].split() == ["g", "kg_2", "kg_3"]


# ───────────────────────── cầu nối R ─────────────────────────


def test_r_script_co_bien_gia_va_khoi_poisson(tmp_path):
    bg = {"kg": {"tham_chieu": "1", "muc": ["2", "3"], "ten": ["kg_2", "kg_3"]}}
    dt = {"outcome": "y", "group": "g", "covariates": ["tuoi", "kg"], "covariates_mo_hinh": ["tuoi", "kg_2", "kg_3"],
          "hiep_bien_phan_loai": bg, "time": None, "event": None, "cot_cum": None}  # fmt: skip
    assert R.nhom_bien_r(dt) == [["g"], ["tuoi"], ["kg_2", "kg_3"]]
    ma = R.ma_r_bien_gia(dt)
    assert 'D[["kg_3"]] <- ifelse(is.na(D[["kg"]]), NA_real_, as.numeric(D[["kg"]] == 3.0))' in ma
    vb = R.sinh_script_r("PR", tmp_path / "k.csv", "ab" * 32, tmp_path / "r.json", dt, "poisson_pr", None, ma)
    assert 'NHOM_BIEN <- list(c("g"), c("tuoi"), c("kg_2", "kg_3"))' in vb
    assert 'HIEP_BIEN <- c("tuoi", "kg_2", "kg_3")' in vb
    assert 'sandwich::vcovHC(fit, type = "HC0")' in vb and "stats::poisson(link = \"log\")" in vb
    assert vb.index('D[["kg_2"]] <-') < vb.index("POISSON <- identical(LOAI")


def test_r_doi_chieu_poisson_tu_dau_ra_that():
    tom = json.loads((FX / "tom_tat_python.json").read_text(encoding="utf-8"))
    r = json.loads((FX / "G6_r_ket_qua.json").read_text(encoding="utf-8"))
    dong = R.doi_chieu(tom, r)
    pois = [x for x in dong if x["muc"].startswith("Poisson")]
    lech = [x for x in pois if x["trang_thai"] != "khop"]
    assert len(pois) == 18 and not lech, lech
    assert {x["trang_thai"] for x in dong} == {"khop"}


def test_r_doi_chieu_bat_pr_lech():
    tom = json.loads((FX / "tom_tat_python.json").read_text(encoding="utf-8"))
    r = json.loads((FX / "G6_r_ket_qua.json").read_text(encoding="utf-8"))
    he = r["ket_qua"]["poisson_hieu_chinh"]["he_so"]["insulin"]
    he["uoc_luong"] *= 1.05
    he["b"] = float(np.log(he["uoc_luong"]))
    dong = R.doi_chieu(tom, r)
    assert any(x["muc"].startswith("Poisson HC0 — PR hiệu chỉnh — insulin") and x["trang_thai"] == "lech" for x in dong)
