"""
run_stats_analysis.py — Phân tích thống kê tự động từ dữ liệu thật (bác sĩ chỉ cung cấp file)

Sử dụng:
    python tools/run_stats_analysis.py \\
        --data path/to/data.csv \\
        --outcome outcome_col \\
        --group group_col \\
        --covariates age,sex,bmi \\
        --study "TEN-DE-TAI" --gate G6

CHƯA hỗ trợ phân tích sống còn/time-to-event (Cox/Kaplan-Meier) — script này chỉ so sánh
2 nhóm nhị phân/liên tục. Không có cờ --time/--event nào trong argparse của script này; một
lệnh dùng 2 cờ đó sẽ lỗi ngay. Với thiết kế cohort/HR cần Cox+KM thật, dùng script CLI do
run_g6_auto.py sinh ra (exports/<study>/run_analysis_cli.py — dùng lifelines CoxPHFitter/
KaplanMeierFitter thật, cùng cổng G2/G4/G5 như script này).

Đầu ra (tự động vào exports/<study>/):
    G6_table1_descriptive.txt     — Bảng 1 đặc điểm mẫu
    G6_table2_main_outcome.txt    — Kết cục chính (OR/MD + 95%CI)
    G6_table4_multivariate.txt    — Mô hình đa biến
    G6_missing_data_summary.txt   — Tóm tắt dữ liệu thiếu
    G6_analysis_summary.json      — JSON dùng cho agent viet-ban-thao
    G6_analysis_syntax.R          — Script R tái lặp kết quả

Phụ thuộc: pandas, numpy, scipy, statsmodels (pip install scipy statsmodels)
"""

import argparse
import json
import sys
import warnings
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ── Kiểm tra thư viện tuỳ chọn ──────────────────────────────────────────────
try:
    from scipy import stats as sp_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    print("[CẢNH BÁO] scipy chưa cài — một số kiểm định bị giới hạn. Chạy: pip install scipy")

try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("[CẢNH BÁO] statsmodels chưa cài — hồi quy đa biến bị giới hạn. Chạy: pip install statsmodels")


# ════════════════════════════════════════════════════════════════════════════
# 1. TẢI DỮ LIỆU
# ════════════════════════════════════════════════════════════════════════════

def load_data(path: str) -> pd.DataFrame:
    """Đọc CSV hoặc Excel, tự phát hiện định dạng."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu: {path}")
    if p.suffix.lower() in (".xlsx", ".xls", ".xlsm"):
        df = pd.read_excel(p)
    else:
        try:
            df = pd.read_csv(p, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(p, encoding="latin-1")
    print(f"✓ Đọc dữ liệu: {len(df)} hàng × {len(df.columns)} cột từ '{p.name}'")
    return df


# ════════════════════════════════════════════════════════════════════════════
# 2. TỰ PHÁT HIỆN LOẠI BIẾN
# ════════════════════════════════════════════════════════════════════════════

def detect_var_type(series: pd.Series) -> str:
    """Trả về 'binary' | 'continuous' | 'categorical'."""
    n_unique = series.dropna().nunique()
    if n_unique == 2:
        return "binary"
    if n_unique <= 10 and (series.dtype == object or n_unique < series.dropna().count() * 0.05):
        return "categorical"
    return "continuous"


def detect_normality(series: pd.Series) -> bool:
    """Shapiro-Wilk (n<50) hoặc D'Agostino (n≥50). True = phân phối chuẩn."""
    data = series.dropna().values
    if len(data) < 3:
        return False
    if not HAS_SCIPY:
        return True  # giả định chuẩn khi không có scipy
    if len(data) < 50:
        _, p = sp_stats.shapiro(data[:5000])
    else:
        _, p = sp_stats.normaltest(data)
    return p > 0.05


# ════════════════════════════════════════════════════════════════════════════
# 3. PHÂN TÍCH DỮ LIỆU THIẾU
# ════════════════════════════════════════════════════════════════════════════

def analyze_missingness(df: pd.DataFrame) -> dict:
    """Báo cáo tỷ lệ thiếu cho từng cột."""
    n = len(df)
    missing = {}
    for col in df.columns:
        n_miss = df[col].isna().sum()
        pct = n_miss / n * 100
        if pct > 0:
            missing[col] = {"n_missing": int(n_miss), "pct": round(pct, 1)}
    total_complete = int((df.notna().all(axis=1)).sum())
    return {
        "n_total": n,
        "n_complete_cases": total_complete,
        "pct_complete": round(total_complete / n * 100, 1),
        "variables_with_missing": missing,
        "max_missing_pct": max((v["pct"] for v in missing.values()), default=0.0),
        "recommendation": _missing_recommendation(missing, n),
    }


def _missing_recommendation(missing: dict, n: int) -> str:
    if not missing:
        return "Không có dữ liệu thiếu — dùng toàn bộ quan sát."
    max_pct = max(v["pct"] for v in missing.values())
    if max_pct < 5:
        return "Thiếu <5% — Complete Case Analysis chấp nhận được (kiểm MCAR nếu có thể)."
    if max_pct < 20:
        return "Thiếu 5–20% — Xem xét Multiple Imputation (m≥20). [CẦN BIOSTATISTICIAN XÁC NHẬN]"
    return "Thiếu >20% — Sensitivity analysis best/worst case bắt buộc. [CẦN BIOSTATISTICIAN XÁC NHẬN]"


# ════════════════════════════════════════════════════════════════════════════
# 4. BẢNG 1 — ĐẶC ĐIỂM MẪU
# ════════════════════════════════════════════════════════════════════════════

def _compare_continuous(a: pd.Series, b: pd.Series) -> dict:
    """t-test hoặc Mann-Whitney tuỳ phân phối. Trả về p, MD (95%CI)."""
    a, b = a.dropna(), b.dropna()
    if len(a) < 2 or len(b) < 2:
        return {"p": None, "effect": "N/A", "test": "N/A"}
    normal_a = detect_normality(a) if HAS_SCIPY else True
    normal_b = detect_normality(b) if HAS_SCIPY else True
    if normal_a and normal_b and HAS_SCIPY:
        t, p = sp_stats.ttest_ind(a, b)
        md = a.mean() - b.mean()
        se = np.sqrt(a.std()**2 / len(a) + b.std()**2 / len(b))
        ci = (round(md - 1.96 * se, 3), round(md + 1.96 * se, 3))
        return {"p": round(float(p), 4), "effect": f"MD={md:.3f} (95%CI {ci[0]}–{ci[1]})", "test": "t-test"}
    elif HAS_SCIPY:
        u, p = sp_stats.mannwhitneyu(a, b, alternative="two-sided")
        med_diff = a.median() - b.median()
        return {"p": round(float(p), 4), "effect": f"Median diff={med_diff:.3f}", "test": "Mann-Whitney"}
    else:
        return {"p": None, "effect": f"Mean diff={a.mean() - b.mean():.3f}", "test": "basic"}


def _compare_categorical(col: pd.Series, grp: pd.Series) -> dict:
    """Chi-square hoặc Fisher's exact cho biến phân loại."""
    if not HAS_SCIPY:
        return {"p": None, "effect": "N/A", "test": "N/A"}
    ct = pd.crosstab(col, grp)
    if ct.shape == (2, 2):
        _, p, _, _ = sp_stats.chi2_contingency(ct)
        if ct.values.min() < 5:
            _, p = sp_stats.fisher_exact(ct.values)
            return {"p": round(float(p), 4), "effect": "N/A", "test": "Fisher exact"}
        return {"p": round(float(p), 4), "effect": "N/A", "test": "Chi-square"}
    chi2, p, _, _ = sp_stats.chi2_contingency(ct)
    return {"p": round(float(p), 4), "effect": "N/A", "test": "Chi-square"}


def table1_descriptive(df: pd.DataFrame, group_col: str, vars_: list) -> dict:
    """Tạo Bảng 1 đặc điểm mẫu theo nhóm."""
    groups = sorted(df[group_col].dropna().unique())
    rows = []
    for var in vars_:
        if var == group_col or var not in df.columns:
            continue
        vtype = detect_var_type(df[var])
        row = {"variable": var, "type": vtype}
        grp_data = {g: df.loc[df[group_col] == g, var] for g in groups}
        if vtype == "continuous":
            for g in groups:
                s = grp_data[g].dropna()
                normal = detect_normality(s) if HAS_SCIPY else True
                if normal:
                    row[f"grp_{g}"] = f"{s.mean():.2f} ± {s.std():.2f}"
                else:
                    row[f"grp_{g}"] = f"{s.median():.2f} [{s.quantile(.25):.2f}–{s.quantile(.75):.2f}]"
            if len(groups) == 2 and HAS_SCIPY:
                comp = _compare_continuous(grp_data[groups[0]], grp_data[groups[1]])
                row["p"] = comp["p"]
                row["test"] = comp["test"]
        elif vtype in ("binary", "categorical"):
            for g in groups:
                s = grp_data[g].dropna()
                if vtype == "binary":
                    n1 = int((s == s.dropna().unique().max()).sum())
                    row[f"grp_{g}"] = f"{n1} ({n1/len(s)*100:.1f}%)"
                else:
                    counts = s.value_counts()
                    row[f"grp_{g}"] = "; ".join(f"{k}: {v}({v/len(s)*100:.0f}%)" for k, v in counts.items())
            if len(groups) == 2 and HAS_SCIPY:
                comp = _compare_categorical(df[var], df[group_col])
                row["p"] = comp["p"]
                row["test"] = comp["test"]
        rows.append(row)

    # Tổng số mỗi nhóm
    n_per_group = {g: int((df[group_col] == g).sum()) for g in groups}
    return {"groups": [str(g) for g in groups], "n_per_group": n_per_group, "rows": rows}


# ════════════════════════════════════════════════════════════════════════════
# 5. KẾT CỤC CHÍNH — So sánh 2 nhóm
# ════════════════════════════════════════════════════════════════════════════

def compare_primary_outcome(df: pd.DataFrame, outcome_col: str,
                             group_col: str, outcome_type: str = "auto") -> dict:
    """Tính crude effect (OR/MD) + 95%CI cho kết cục chính."""
    if outcome_type == "auto":
        outcome_type = detect_var_type(df[outcome_col])

    groups = sorted(df[group_col].dropna().unique())
    if len(groups) != 2:
        return {"error": f"group_col cần đúng 2 nhóm, tìm thấy {len(groups)}: {groups}"}

    g0, g1 = groups
    s0 = df.loc[df[group_col] == g0, outcome_col].dropna()
    s1 = df.loc[df[group_col] == g1, outcome_col].dropna()

    result = {"outcome_type": outcome_type, "groups": [str(g0), str(g1)]}

    if outcome_type == "binary":
        n0, e0 = len(s0), int(s0.sum())
        n1, e1 = len(s1), int(s1.sum())
        p0, p1 = e0 / n0, e1 / n1
        result["group_0"] = {"n": n0, "events": e0, "pct": round(p0 * 100, 1)}
        result["group_1"] = {"n": n1, "events": e1, "pct": round(p1 * 100, 1)}
        if p0 > 0 and p1 > 0 and p0 < 1 and p1 < 1:
            or_crude = (e1 / (n1 - e1)) / (e0 / (n0 - e0))
            se_log = np.sqrt(1/e0 + 1/(n0-e0) + 1/e1 + 1/(n1-e1))
            ci = (round(np.exp(np.log(or_crude) - 1.96 * se_log), 3),
                  round(np.exp(np.log(or_crude) + 1.96 * se_log), 3))
            result["or_crude"] = round(or_crude, 3)
            result["ci_95"] = ci
        if HAS_SCIPY:
            ct = pd.crosstab(df[outcome_col], df[group_col])
            _, p, _, _ = sp_stats.chi2_contingency(ct)
            result["p_value"] = round(float(p), 4)
            result["test"] = "Chi-square"
    else:
        comp = _compare_continuous(s0, s1)
        result["group_0"] = {"n": len(s0), "mean": round(s0.mean(), 3), "sd": round(s0.std(), 3)}
        result["group_1"] = {"n": len(s1), "mean": round(s1.mean(), 3), "sd": round(s1.std(), 3)}
        result["md_crude"] = round(s1.mean() - s0.mean(), 3)
        result["effect"] = comp["effect"]
        result["p_value"] = comp["p"]
        result["test"] = comp["test"]

    return result


# ════════════════════════════════════════════════════════════════════════════
# 6. MÔ HÌNH ĐA BIẾN
# ════════════════════════════════════════════════════════════════════════════

def multivariate_model(df: pd.DataFrame, outcome_col: str, group_col: str,
                        covariates: list, outcome_type: str = "auto") -> dict:
    """Logistic (nhị phân) hoặc Linear regression (liên tục)."""
    if not HAS_STATSMODELS:
        return {
            "error": "statsmodels chưa cài. Chạy: pip install statsmodels",
            "note": "[CẦN BỔ SUNG — Hồi quy đa biến cần statsmodels]",
        }
    if outcome_type == "auto":
        outcome_type = detect_var_type(df[outcome_col])

    available_covs = [c for c in covariates if c in df.columns]
    predictors = [group_col] + available_covs
    data = df[[outcome_col] + predictors].dropna()

    # Audit 2026-07-11: EPV (Events-Per-Variable, Peduzzi 1996) cho hồi quy LOGISTIC
    # phải tính theo SỐ BIẾN CỐ (nhóm hiếm hơn của outcome nhị phân), không phải tổng
    # N — trước đây dùng chung len(data) cho cả 2 nhánh binary/liên tục, âm thầm
    # KHÔNG bảo vệ được trường hợp N lớn nhưng biến cố hiếm (vd 500 dòng, 25 biến cố).
    if outcome_type == "binary":
        y_raw = data[outcome_col]
        n_events = int(min((y_raw == y_raw.unique()[0]).sum(), (y_raw != y_raw.unique()[0]).sum())) \
            if y_raw.nunique() == 2 else len(data)
        if n_events < len(predictors) * 10:
            return {"warning": f"Số biến cố (nhóm hiếm hơn) {n_events} có thể không đủ EPV "
                                f"cho {len(predictors)} biến dự báo (cần ≥10 biến cố/biến — Peduzzi 1996)."}
    elif len(data) < len(predictors) * 10:
        return {"warning": f"Cỡ mẫu {len(data)} có thể không đủ cho {len(predictors)} biến dự báo."}

    X = pd.get_dummies(data[predictors], drop_first=True)
    X = sm.add_constant(X)
    y = data[outcome_col].astype(float)

    try:
        if outcome_type == "binary":
            model = sm.Logit(y, X).fit(disp=False, maxiter=200)
            coefs = model.params
            conf = model.conf_int()
            results = []
            for var in coefs.index:
                if var == "const":
                    continue
                or_adj = round(float(np.exp(coefs[var])), 3)
                ci_low = round(float(np.exp(conf.loc[var, 0])), 3)
                ci_up = round(float(np.exp(conf.loc[var, 1])), 3)
                p = round(float(model.pvalues[var]), 4)
                results.append({"variable": var, "OR_adj": or_adj,
                                 "CI_95": [ci_low, ci_up], "p": p})
            return {"model": "logistic", "n": len(data), "aic": round(model.aic, 2),
                    "results": results, "convergence": model.mle_retvals.get("converged", True)}
        else:
            model = sm.OLS(y, X).fit()
            coefs = model.params
            conf = model.conf_int()
            results = []
            for var in coefs.index:
                if var == "const":
                    continue
                beta = round(float(coefs[var]), 4)
                ci = [round(float(conf.loc[var, 0]), 4), round(float(conf.loc[var, 1]), 4)]
                p = round(float(model.pvalues[var]), 4)
                results.append({"variable": var, "beta": beta, "CI_95": ci, "p": p})
            return {"model": "linear", "n": len(data), "r_squared": round(model.rsquared, 4),
                    "results": results}
    except Exception as e:
        return {"error": str(e), "note": "[CẦN BIOSTATISTICIAN — mô hình không hội tụ]"}


# ════════════════════════════════════════════════════════════════════════════
# 7. ĐỊNH DẠNG ĐẦU RA CHO AGENT
# ════════════════════════════════════════════════════════════════════════════

def format_table1_text(t1: dict) -> str:
    groups = t1["groups"]
    n = t1["n_per_group"]
    header = f"BẢNG 1 — ĐẶC ĐIỂM MẪU\n" + "=" * 70
    header += f"\n{'Biến số':<30}" + "".join(f"{'Nhóm ' + str(g) + ' (n=' + str(n.get(g,'-')) + ')':<22}" for g in groups)
    header += f"{'p':>10}  {'Kiểm định'}"
    lines = [header, "-" * 70]
    for row in t1["rows"]:
        var = row["variable"][:28]
        grp_vals = "".join(f"{row.get('grp_' + g, 'N/A'):<22}" for g in groups)
        p = f"{row.get('p', '')}" if row.get("p") is not None else ""
        test = row.get("test", "")
        lines.append(f"{var:<30}{grp_vals}{p:>10}  {test}")
    return "\n".join(lines)


def format_outcome_text(res: dict, outcome_col: str) -> str:
    if "error" in res:
        return f"LỖI: {res['error']}"
    g = res.get("groups", ["A", "B"])
    n0 = res.get("group_0", {})
    n1 = res.get("group_1", {})
    lines = [f"BẢNG 2 — KẾT CỤC CHÍNH: {outcome_col}", "=" * 70]
    if res["outcome_type"] == "binary":
        lines.append(f"  Nhóm {g[0]}: {n0.get('events','?')}/{n0.get('n','?')} ({n0.get('pct','?')}%)")
        lines.append(f"  Nhóm {g[1]}: {n1.get('events','?')}/{n1.get('n','?')} ({n1.get('pct','?')}%)")
        if "or_crude" in res:
            ci = res["ci_95"]
            lines.append(f"  OR thô = {res['or_crude']} (95%CI {ci[0]}–{ci[1]})")
    else:
        lines.append(f"  Nhóm {g[0]}: Mean={n0.get('mean','?')} ± SD={n0.get('sd','?')}")
        lines.append(f"  Nhóm {g[1]}: Mean={n1.get('mean','?')} ± SD={n1.get('sd','?')}")
        lines.append(f"  {res.get('effect', 'N/A')}")
    if "p_value" in res:
        lines.append(f"  p = {res['p_value']} ({res.get('test','')})")
    lines.append("\n[BÁC SĨ KIỂM TRA: số liệu lấy trực tiếp từ dữ liệu thật]")
    return "\n".join(lines)


def format_multivariate_text(mv: dict) -> str:
    if "error" in mv:
        return f"HỒI QUY ĐA BIẾN: {mv['error']}\n{mv.get('note','')}"
    lines = [f"BẢNG 4 — MÔ HÌNH ĐA BIẾN ({mv['model'].upper()})", "=" * 70]
    lines.append(f"  n = {mv['n']} | {'AIC' if mv['model']=='logistic' else 'R²'} = {mv.get('aic', mv.get('r_squared','?'))}")
    lines.append(f"\n  {'Biến số':<28} {'OR/β hiệu chỉnh':>18}  {'95%CI':>20}  {'p':>8}")
    lines.append("  " + "-" * 60)
    for r in mv.get("results", []):
        est = r.get("OR_adj", r.get("beta", "?"))
        ci = r["CI_95"]
        ci_str = f"{ci[0]}–{ci[1]}"
        p = r["p"]
        star = " *" if p < 0.05 else ""
        lines.append(f"  {r['variable'][:28]:<28} {est:>18}  {ci_str:>20}  {p:>8}{star}")
    lines.append("\n* p < 0.05")
    return "\n".join(lines)


def generate_r_script(study: str, gate: str, outcome_col: str, group_col: str,
                       covariates: list, outcome_type: str) -> str:
    """Script R tái lặp kết quả (để audit/tái lặp độc lập)."""
    formula = " + ".join([group_col] + covariates)
    family = "binomial" if outcome_type == "binary" else "gaussian"
    # Pre-compute conditionals to avoid backslash-in-f-string (Python < 3.12)
    model_comment = "# Logistic regression" if family == "binomial" else "# Linear regression"
    coef_code = ("exp(cbind(OR = coef(model_adj), confint(model_adj)))"
                 if family == "binomial"
                 else "cbind(beta = coef(model_adj), confint(model_adj))")
    hosmer_block = (
        "# Hosmer-Lemeshow (logistic)\n"
        "library(ResourceSelection)\n"
        f"hoslem.test(data${outcome_col}, fitted(model_adj))"
        if family == "binomial" else ""
    )
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"# ══════════════════════════════════════════════\n"
        f"# Script R tái lặp — {study} | {gate}\n"
        f"# Tạo tự động bởi run_stats_analysis.py\n"
        f"# Ngày: {run_date}\n"
        f"# ══════════════════════════════════════════════\n"
        "set.seed(42)  # CỐ ĐỊNH SEED\n\n"
        "library(tableone); library(dplyr)\n\n"
        "# 1. Đọc dữ liệu (thay đường dẫn)\n"
        'data <- read.csv("data.csv")  # hoặc read.xlsx\n\n'
        "# 2. Bảng 1\n"
        f'vars_all <- setdiff(names(data), c("{group_col}", "{outcome_col}"))\n'
        f'tab1 <- CreateTableOne(vars = vars_all, strata = "{group_col}", data = data)\n'
        "print(tab1, showAllLevels = TRUE, smd = TRUE)\n\n"
        f"# 3. Kết cục chính\n{model_comment}\n"
        f"model_crude <- glm({outcome_col} ~ {group_col}, data = data, family = {family})\n"
        f"model_adj   <- glm({outcome_col} ~ {formula}, data = data, family = {family})\n\n"
        f"# OR/β + 95%CI (không chỉ p-value)\n{coef_code}\n\n"
        "# 4. Kiểm tra giả định\n"
        f"library(car); vif(model_adj)\n{hosmer_block}\n\n"
        "# 5. Ghi session info (tái lặp)\n"
        'sink("session_info.txt"); sessionInfo(); sink()\n'
    )


# ════════════════════════════════════════════════════════════════════════════
# 8. ĐIỂM VÀO CHÍNH (CLI)
# ════════════════════════════════════════════════════════════════════════════

def _is_locked(status) -> bool:
    """Kiểm tra trạng thái đã LOCKED chính xác (không khớp nhầm "CHƯA LOCKED"/"UNLOCKED").
    Cùng logic với run_g6_auto.py — giữ đồng bộ nếu sửa 1 trong 2 chỗ."""
    import re
    s = str(status or "").strip().upper()
    if re.search(r'(UN|CH[ƯU]A|KH[ÔO]NG|NOT)\s*LOCKED', s):
        return False
    return bool(re.match(r'^LOCKED\b', s))


def _load_checkpoint(study: str, gate: str) -> dict:
    p = Path("exports") / study / f"{gate}_checkpoint.json"
    if p.exists():
        try:
            with open(p, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _ledger_approved(study: str, gate_id: str, artifact_path: Path) -> bool:
    """Vá 2026-07-09 (kiểm định đối kháng độc lập — phát hiện qua audit guardrail):
    TRƯỚC ĐÂY hàm này không tồn tại — _is_locked() (chỉ đọc 1 trường text tự do
    trong checkpoint JSON) là điều kiện DUY NHẤT để cho chạy phân tích thật. Bất kỳ
    ai/agent nào tự tay ghi {"g4_status": "LOCKED"} vào G4_checkpoint.json là script
    này tin ngay, dù chưa từng có phê duyệt thật nào — chính lỗ hổng mà cơ chế
    ApprovalLedger cryptographic-binding (BL-06, 2026-07-08) được xây ra để chặn,
    nhưng chưa từng được nối vào đây. Hàm này đóng khoảng trống đó: True CHỈ khi có
    phê duyệt THẬT (không synthetic, không agent tự tạo — 2 điều kiện đã có sẵn ở
    ApprovalLedger.add_approval()) cho đúng gate_id, VÀ evidence_hash khớp NỘI DUNG
    HIỆN TẠI của artifact_path (nếu artifact bị sửa sau khi duyệt, hash lệch → coi
    như CHƯA duyệt). Đọc thô JSON (không import runtime.approval_ledger) để nhất
    quán với cách 2 template CLI nhúng của run_g6_auto.py đã làm — 1 trong 2 nơi ở
    đó (case-control) đã có hàm y hệt, cohort/Cox thì thiếu — cả 3 nơi giờ đồng bộ."""
    import hashlib
    ledger_p = Path("exports") / study / "approval_ledger.json"
    if not ledger_p.exists() or not artifact_path.exists():
        return False
    try:
        records = json.loads(ledger_p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    matches = [r for r in records if r.get("gate_id") == gate_id
               and r.get("decision") == "APPROVED" and not r.get("is_synthetic")]
    if not matches:
        return False
    latest = sorted(matches, key=lambda r: r.get("timestamp_utc", ""))[-1]
    try:
        actual_hash = hashlib.sha256(artifact_path.read_bytes()).hexdigest()
    except OSError:
        return False
    return actual_hash == latest.get("evidence_hash")


def main():
    parser = argparse.ArgumentParser(
        description="Phân tích thống kê tự động từ file dữ liệu thật"
    )
    parser.add_argument("--data", required=True, help="Đường dẫn file CSV/Excel")
    parser.add_argument("--outcome", help="Cột kết cục chính (nhị phân 0/1 hoặc liên tục)")
    parser.add_argument("--group", help="Cột nhóm (so sánh 2 nhóm)")
    parser.add_argument("--covariates", default="",
                        help="Danh sách biến hiệu chỉnh, phân cách bằng dấu phẩy")
    parser.add_argument("--outcome-type", default="auto",
                        choices=["auto", "binary", "continuous"],
                        help="Loại kết cục (mặc định: tự phát hiện)")
    parser.add_argument("--study", default="STUDY", help="Tên đề tài (dùng đặt tên file đầu ra)")
    parser.add_argument("--gate", default="G6", help="Cổng phân tích (mặc định: G6)")
    parser.add_argument("--vars", default="", help="Biến cho Bảng 1 (mặc định: tất cả)")
    parser.add_argument("--i-confirm-sap-locked", action="store_true",
                        help="Ghi đè kiểm tra G4/G5 checkpoint khi không có file checkpoint "
                             "(vd chạy thủ công ngoài pipeline) nhưng SAP+DB thực tế đã khóa. "
                             "KHÔNG dùng để né việc chưa khóa thật.")
    parser.add_argument("--i-confirm-irb-approved", action="store_true",
                        help="Ghi đè kiểm tra G2 (đạo đức/IRB) khi không có file checkpoint "
                             "nhưng IRB thực tế ĐÃ phê duyệt. KHÔNG dùng để né việc chưa duyệt thật.")
    args = parser.parse_args()

    # 2026-07-07: cổng kỹ thuật chặn chạy phân tích thật khi G4 (SAP)/G5 (DB) chưa khóa —
    # trước đây script này không kiểm tra gì, chỉ agent tự nhớ nhắc (đã xảy ra rủi ro
    # data dredging/p-hacking nếu SAP còn nháp). Không có checkpoint + không có cờ
    # --i-confirm-sap-locked → coi như CHƯA khóa, từ chối chạy.
    #
    # Vá 2026-07-09 (kiểm định đối kháng — checkpoint text tự do vẫn có thể bị sửa tay):
    # BẮT BUỘC CẢ HAI — checkpoint nói LOCKED VÀ có phê duyệt thật khớp hash trong
    # approval_ledger.json (_ledger_approved) — không còn chỉ dựa vào 1 trường text.
    #
    # Vá 2026-07-10 (kiểm định đối kháng đa-agent): THÊM cổng G2 (đạo đức/IRB) — trước đây
    # script CHẠY-DỮ-LIỆU-THẬT này chỉ chặn theo G4/G5, KHÔNG hề kiểm G2, dù sibling
    # run_g6_auto.py (vốn chỉ SINH template, không đụng dữ liệu thật) đã có cổng G2. Nghĩa là
    # có thể chạy phân tích thật trên dữ liệu bệnh nhân THẬT mà không có cổng kỹ thuật nào
    # xác nhận đã được Hội đồng Đạo đức phê duyệt — đúng rủi ro dùng-dữ-liệu-chưa-được-duyệt
    # mà cơ chế approval_ledger (BL-06) sinh ra để chặn. Nay chặn cả G2 (checkpoint VÀ ledger).
    g2_cp = _load_checkpoint(args.study, "G2")
    g2_checkpoint_locked = _is_locked(g2_cp.get("g2_status", g2_cp.get("G2_STATUS")))
    g2_ledger_ok = _ledger_approved(
        args.study, "G2", Path("exports") / args.study / f"G2_A3_ETHICS_PACKAGE_{args.study}.md")
    g2_locked = g2_checkpoint_locked and g2_ledger_ok
    if not g2_locked and not args.i_confirm_irb_approved:
        print("✗ DỪNG: G2 (phê duyệt đạo đức/IRB) chưa xác nhận LOCKED bằng phê duyệt thật.")
        print(f"   G2 checkpoint: {'✅ LOCKED' if g2_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger: {'✅ khớp hash' if g2_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   KHÔNG chạy phân tích trên dữ liệu bệnh nhân THẬT khi chưa có phê duyệt đạo đức thật.")
        print("   Ghi phê duyệt thật bằng:")
        print(f"     python tools/approve_gate.py --study \"{args.study}\" --gate G2 "
              f"--artifact exports/{args.study}/G2_A3_ETHICS_PACKAGE_{args.study}.md ...")
        print("   Nếu IRB THỰC TẾ đã phê duyệt nhưng thiếu file checkpoint, thêm --i-confirm-irb-approved.")
        sys.exit(1)
    g4_cp = _load_checkpoint(args.study, "G4")
    g5_cp = _load_checkpoint(args.study, "G5")
    g4_checkpoint_locked = _is_locked(g4_cp.get("g4_status", g4_cp.get("G4_STATUS")))
    g5_checkpoint_locked = _is_locked(g5_cp.get("g5_status", g5_cp.get("G5_STATUS")))
    g4_ledger_ok = _ledger_approved(
        args.study, "G4", Path("exports") / args.study / f"G4_A5_SAP_FINAL_{args.study}.md")
    g5_ledger_ok = _ledger_approved(
        args.study, "G5", Path("exports") / args.study / "G5_checkpoint.json")
    g4_locked = g4_checkpoint_locked and g4_ledger_ok
    g5_locked = g5_checkpoint_locked and g5_ledger_ok
    if not (g4_locked and g5_locked) and not args.i_confirm_sap_locked:
        print("✗ DỪNG: G4 (SAP) hoặc G5 (khóa DB) chưa xác nhận LOCKED bằng phê duyệt thật.")
        print(f"   G4 checkpoint: {'✅ LOCKED' if g4_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger: {'✅ khớp hash' if g4_ledger_ok else '⚠️ thiếu/không khớp'}")
        print(f"   G5 checkpoint: {'✅ LOCKED' if g5_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger: {'✅ khớp hash' if g5_ledger_ok else '⚠️ thiếu/không khớp'}")
        print("   Không thể chạy phân tích xác nhận trên dữ liệu chưa khóa (chống p-hacking/HARKing).")
        print("   Checkpoint 'LOCKED' không còn đủ — cần bác sĩ tự tay ghi phê duyệt thật bằng:")
        print(f"     python tools/approve_gate.py --study \"{args.study}\" --gate G4 "
              f"--artifact exports/{args.study}/G4_A5_SAP_FINAL_{args.study}.md ...")
        print("   Nếu SAP+DB THỰC TẾ đã khóa nhưng thiếu file checkpoint (vd chạy ngoài pipeline),")
        print("   thêm cờ --i-confirm-sap-locked sau khi tự xác nhận chắc chắn.")
        sys.exit(1)

    # 1. Tải dữ liệu
    df = load_data(args.data)

    covariates = [c.strip() for c in args.covariates.split(",") if c.strip()]
    vars_for_t1 = ([v.strip() for v in args.vars.split(",") if v.strip()]
                   or [c for c in df.columns if c not in [args.group, args.outcome]])

    # 2. Output dir
    out_dir = Path("exports") / args.study
    out_dir.mkdir(parents=True, exist_ok=True)
    prefix = out_dir / f"{args.gate}"

    summary = {
        "study": args.study, "gate": args.gate,
        "generated": datetime.now().isoformat(),
        "data_source": str(args.data),
        "n_total": len(df),
        "disclaimer": "Cần bác sĩ kiểm chứng."
    }

    # 3. Dữ liệu thiếu
    miss = analyze_missingness(df)
    summary["missing_data"] = miss
    miss_txt = (
        f"TÓM TẮT DỮ LIỆU THIẾU\n{'='*50}\n"
        f"Tổng n = {miss['n_total']} | Hoàn chỉnh = {miss['n_complete_cases']} ({miss['pct_complete']}%)\n"
        f"Khuyến nghị: {miss['recommendation']}\n"
    )
    if miss["variables_with_missing"]:
        miss_txt += "\nChi tiết:\n"
        for col, info in miss["variables_with_missing"].items():
            miss_txt += f"  {col}: {info['n_missing']} thiếu ({info['pct']}%)\n"
    (prefix.parent / f"{args.gate}_missing_data_summary.txt").write_text(miss_txt, encoding="utf-8")
    print(f"✓ Phân tích dữ liệu thiếu: {miss['pct_complete']}% hoàn chỉnh")

    # 4. Bảng 1
    if args.group and args.group in df.columns:
        t1 = table1_descriptive(df, args.group, vars_for_t1)
        t1_txt = format_table1_text(t1)
        (prefix.parent / f"{args.gate}_table1_descriptive.txt").write_text(t1_txt, encoding="utf-8")
        summary["table1"] = {"n_per_group": t1["n_per_group"]}
        print(f"✓ Bảng 1: {len(t1['rows'])} biến, {len(t1['groups'])} nhóm")

    # 5. Kết cục chính
    if args.outcome and args.group and args.outcome in df.columns:
        res = compare_primary_outcome(df, args.outcome, args.group, args.outcome_type)
        res_txt = format_outcome_text(res, args.outcome)
        (prefix.parent / f"{args.gate}_table2_main_outcome.txt").write_text(res_txt, encoding="utf-8")
        summary["primary_outcome"] = res
        print(f"✓ Kết cục chính ({res.get('outcome_type','')}): p={res.get('p_value','?')}")

        # 6. Đa biến
        mv = multivariate_model(df, args.outcome, args.group, covariates, args.outcome_type)
        mv_txt = format_multivariate_text(mv)
        (prefix.parent / f"{args.gate}_table4_multivariate.txt").write_text(mv_txt, encoding="utf-8")
        summary["multivariate"] = mv
        print(f"✓ Mô hình đa biến: {mv.get('model','?')} ({mv.get('n','?')} quan sát)")

        # 7. Script R tái lặp
        r_script = generate_r_script(args.study, args.gate, args.outcome,
                                      args.group, covariates, args.outcome_type)
        (prefix.parent / f"{args.gate}_analysis_syntax.R").write_text(r_script, encoding="utf-8")
        print("✓ Script R tái lặp đã tạo")

    # 8. JSON summary (cho agent)
    json_path = prefix.parent / f"{args.gate}_analysis_summary.json"
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH — Đầu ra tại: {out_dir}/")
    print(f"   Dùng cho viet-ban-thao: {args.gate}_analysis_summary.json")
    print(f"\nCần bác sĩ kiểm chứng.")
    return summary


if __name__ == "__main__":
    main()
