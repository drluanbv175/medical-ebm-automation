"""
run_stats_analysis.py — Phân tích thống kê tự động từ dữ liệu thật (bác sĩ chỉ cung cấp file)

Sử dụng (kết cục nhị phân/liên tục — logistic/linear regression):
    python tools/run_stats_analysis.py \\
        --data path/to/data.csv \\
        --outcome outcome_col \\
        --group group_col \\
        --covariates age,sex,bmi \\
        --study "TEN-DE-TAI" --gate G6

Sử dụng (thiết kế sống còn/time-to-event — Cox PH + Kaplan-Meier, vá 2026-07-15):
    python tools/run_stats_analysis.py \\
        --data path/to/data.csv \\
        --time follow_time --event outcome_col \\
        --group exposure_col \\
        --covariates age,sex,bmi \\
        --study "TEN-DE-TAI" --gate G6

Trước 2026-07-15, script này KHÔNG hỗ trợ sống còn — Cox/KM thật chỉ tồn tại dưới dạng
CODE NHÚNG trong chuỗi template mà run_g6_auto.py ghi ra exports/<study>/run_analysis_cli.py
để bác sĩ tự chạy tay riêng, tách khỏi cổng G2/G4/G5 mà script NÀY đã có sẵn. Nay `--time`+
`--event` kích hoạt nhánh sống còn, TỰ THỰC THI CoxPHFitter/KaplanMeierFitter thật (lifelines)
— cùng công thức/quy ước đã dùng ở run_g6_auto.py::run_cox/plot_km, qua ĐÚNG cổng data-lock
này (không phải một script riêng biệt ít được kiểm hơn).

Multiple imputation (vá 2026-07-15): khi biến outcome/group/covariates có dữ liệu thiếu, script
TỰ CHẠY MI thật (statsmodels MICEData/MICE, m=20 mặc định, --n-imputations để đổi) song song với
complete-case — trước đây "MI" trong sensitivity_analysis.py (template do run_g6_auto.py sinh)
chỉ là mean-impute tự khai không phải MI thật.

Đầu ra (tự động vào exports/<study>/):
    G6_table1_descriptive.txt     — Bảng 1 đặc điểm mẫu
    G6_table2_main_outcome.txt    — Kết cục chính (OR/MD + 95%CI) — thiết kế nhị phân/liên tục
    G6_table3_survival.txt        — Cox PH (HR + 95%CI) — thiết kế sống còn (--time/--event)
    G6_km_curve.png               — Đường cong Kaplan-Meier (nếu có matplotlib) — thiết kế sống còn
    G6_table4_multivariate.txt    — Mô hình đa biến (complete-case) — thiết kế nhị phân/liên tục
    G6_table5_multiple_imputation.txt — MI thật (đối chiếu complete-case) — khi có dữ liệu thiếu
    G6_missing_data_summary.txt   — Tóm tắt dữ liệu thiếu
    G6_analysis_summary.json      — JSON dùng cho agent viet-ban-thao
    G6_analysis_syntax.R          — Script R tái lặp kết quả

Phụ thuộc: pandas, numpy, scipy, statsmodels (pip install scipy statsmodels); thêm lifelines
cho thiết kế sống còn, matplotlib (tuỳ chọn) để vẽ đường cong KM.
"""

import argparse
import json
import sys
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gate_contract as GC  # noqa: E402

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
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False
    print("[CẢNH BÁO] statsmodels chưa cài — hồi quy đa biến bị giới hạn. Chạy: pip install statsmodels")

try:
    import lifelines  # noqa: F401  (chỉ để kiểm sự tồn tại; import cụ thể lúc dùng)
    HAS_LIFELINES = True
except ImportError:
    HAS_LIFELINES = False
    print("[CẢNH BÁO] lifelines chưa cài — phân tích sống còn (Cox/KM) bị giới hạn. Chạy: pip install lifelines")

try:
    import matplotlib  # noqa: F401
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


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
    """Trả về 'binary' | 'continuous' | 'categorical'.

    Vá 2026-07-14: "series.dtype == object" không còn đúng trên pandas 3.x —
    cột chuỗi đọc từ CSV giờ có dtype "str" mới (StringDtype/"str"), không
    phải "object" nữa. Điều kiện cũ khiến cột định danh dạng chữ (vd
    "record_id" = "S001") bị xếp nhầm thành "continuous" rồi crash khi gọi
    scipy.stats.shapiro trên dữ liệu chuỗi. Dùng pandas.api.types.is_numeric_dtype
    — dtype-agnostic, đúng cho mọi phiên bản pandas (object/str/category/bool/
    Int64 nullable…) — thay vì so sánh dtype cụ thể."""
    n_unique = series.dropna().nunique()
    if n_unique == 2:
        return "binary"
    if not pd.api.types.is_numeric_dtype(series):
        return "categorical"
    if n_unique <= 10 and n_unique < series.dropna().count() * 0.05:
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


def _json_safe(obj):
    """Chuyển kiểu numpy/pandas sang JSON thuần để summary không crash."""
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, tuple):
        return [_json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    return obj


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
        # Vá 2026-07-11 (vòng 8): trước đây ttest_ind() không truyền equal_var → mặc định
        # equal_var=True (Student's, gộp phương sai, giả định 2 nhóm phương sai bằng nhau),
        # NHƯNG SE dựng CI ngay dưới lại là công thức Welch's (không gộp) — 2 giả định phương
        # sai KHÁC NHAU trong CÙNG 1 kết quả (p vs CI có thể mâu thuẫn suy luận khi n1≠n2 hoặc
        # phương sai 2 nhóm lệch nhau). Dùng Welch's cho cả 2 — an toàn hơn, không đòi hỏi giả
        # định phương sai bằng nhau, là mặc định khuyến nghị của thống kê hiện đại.
        t, p = sp_stats.ttest_ind(a, b, equal_var=False)
        md = a.mean() - b.mean()
        v1, v2 = a.std()**2 / len(a), b.std()**2 / len(b)
        se = np.sqrt(v1 + v2)
        # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện MEDIUM):
        # trước đây dùng z=1.96 cố định cho CI trong khi p ở trên đã dùng bậc tự do
        # Welch-Satterthwaite (nội bộ scipy ttest_ind equal_var=False) — p và CI
        # không cùng phương pháp, có thể mâu thuẫn ở mẫu nhỏ (t_{df,0.975} > 1.96
        # đáng kể khi df nhỏ, vd ≈2.78 ở df≈4 so với 1.96 — CI báo hẹp hơn thực tế,
        # có thể kết luận sai "khác biệt có ý nghĩa" khi CI đúng chuẩn lại chứa 0).
        # Dùng ĐÚNG t-critical theo df Welch-Satterthwaite để nhất quán với p.
        df_ws = (v1 + v2) ** 2 / (v1**2 / (len(a) - 1) + v2**2 / (len(b) - 1))
        t_crit = sp_stats.t.ppf(0.975, df_ws)
        ci = (round(md - t_crit * se, 3), round(md + t_crit * se, 3))
        return {"p": round(float(p), 4), "effect": f"MD={md:.3f} (95%CI {ci[0]}–{ci[1]})", "test": "Welch's t-test"}
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
                    # Vá 2026-07-14: .unique() trả về ExtensionArray (vd ArrowStringArray
                    # cho dtype "str" mới của pandas 3.x khi cột nhị phân là chữ, "Yes"/"No")
                    # — các ExtensionArray này không có .max(). dùng max() builtin (dựa vào
                    # __iter__/so sánh, hoạt động với mọi loại mảng: ndarray/IntegerArray/
                    # ArrowStringArray/Categorical…) thay vì gọi .max() trực tiếp trên mảng.
                    n1 = int((s == max(s.dropna().unique())).sum())
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
        # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện
        # HIGH): risk difference (RD) + CI 95% Wald — vòng 15 vừa thêm
        # --hypothesis-type non_inferiority/equivalence vào run_g3_auto.py
        # (margin định nghĩa trên THANG TỶ LỆ, không phải OR) nhưng
        # compare_primary_outcome() trước đây CHỈ tính OR — không thể so
        # sánh margin (thang tỷ lệ) với CI của OR (thang log-odds, khác thang
        # hoàn toàn). RD cho phép interpret_hypothesis_type() bên dưới so
        # sánh ĐÚNG thang với margin từ G3.
        rd = p1 - p0
        se_rd = np.sqrt(p0 * (1 - p0) / n0 + p1 * (1 - p1) / n1)
        result["risk_diff"] = round(rd, 4)
        result["risk_diff_ci_95"] = (round(rd - 1.96 * se_rd, 4), round(rd + 1.96 * se_rd, 4))
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


def interpret_hypothesis_type(res: dict, hypothesis_type: str, margin) -> dict:
    """Diễn giải kết cục chính theo ĐÚNG khung giả thuyết đã thiết kế ở G3
    (superiority/non_inferiority/equivalence) — xem run_g3_auto.py::
    n_two_proportion_ni().

    THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện HIGH):
    trước đây run_stats_analysis.py hoàn toàn không biết hypothesis_type —
    một đề tài NI được tính cỡ mẫu đúng ở G3 nhưng bị phân tích/diễn giải
    y hệt superiority ở G6 (chỉ nhìn p-value hai đuôi), sai nguyên tắc kết
    luận NI kinh điển (dựa vào VỊ TRÍ giới hạn CI so với margin, không phải
    p<0.05). Hàm này CHỈ tính toán số học khách quan (RD + CI đã có ở
    compare_primary_outcome()) và trình bày CẢ HAI khả năng chiều diễn giải
    (nhóm nào là thử nghiệm/chứng) — KHÔNG tự đoán chiều nào đúng, vì
    compare_primary_outcome() chỉ biết "group_0"/"group_1" (sắp theo giá
    trị), không biết ngữ nghĩa lâm sàng nào là can thiệp mới. Tự đoán sai
    chiều ở đây có thể dẫn tới kết luận non-inferiority SAI — rủi ro cao hơn
    hẳn một dòng cảnh báo thiếu, nên cố tình để bác sĩ/thống kê viên xác
    nhận chiều thay vì tự quyết."""
    if hypothesis_type not in ("non_inferiority", "equivalence"):
        return {}
    if res.get("outcome_type") != "binary" or "risk_diff_ci_95" not in res:
        return {"note": (
            "[CẦN THỐNG KÊ VIÊN — diễn giải non_inferiority/equivalence tự động ở đây CHỈ hỗ trợ "
            "kết cục NHỊ PHÂN qua risk difference. Kết cục liên tục/sống còn cần tính tay theo "
            "CÙNG nguyên tắc (so giới hạn CI của MD/HR với margin), KHÔNG dựa vào p-value.]"
        )}
    if margin is None:
        return {"note": "[CẦN — thiếu margin từ G3 checkpoint, KHÔNG thể diễn giải non_inferiority/equivalence.]"}
    lo, hi = res["risk_diff_ci_95"]
    g0, g1 = res.get("groups", ["A", "B"])
    if hypothesis_type == "non_inferiority":
        cond_group1_is_test = lo > -margin
        cond_group0_is_test = hi < margin
        note = (
            f"[CẦN BÁC SĨ/THỐNG KÊ VIÊN XÁC NHẬN CHIỀU DIỄN GIẢI — hệ KHÔNG tự đoán nhóm nào là "
            f"thử nghiệm]: NẾU nhóm '{g1}' là THỬ NGHIỆM và '{g0}' là CHỨNG → "
            f"{'ĐẠT' if cond_group1_is_test else 'CHƯA ĐẠT'} non-inferiority (cận dưới CI của RD="
            f"{lo} {'>' if cond_group1_is_test else '≤'} −margin={-margin}). NẾU ngược lại "
            f"('{g0}' là thử nghiệm) → {'ĐẠT' if cond_group0_is_test else 'CHƯA ĐẠT'} non-inferiority "
            f"(cận trên CI={hi} {'<' if cond_group0_is_test else '≥'} +margin={margin}). "
            "Kết luận NI dựa trên VỊ TRÍ giới hạn CI so với margin, KHÔNG dựa vào p-value superiority."
        )
    else:  # equivalence
        within = (lo > -margin) and (hi < margin)
        note = (
            f"{'ĐẠT' if within else 'CHƯA ĐẠT'} equivalence theo xấp xỉ CI-vs-margin đơn giản hóa: "
            f"toàn bộ CI của RD [{lo}, {hi}] {'nằm trong' if within else 'KHÔNG nằm hoàn toàn trong'} "
            f"biên [−{margin}, +{margin}]. [CẦN — đây là xấp xỉ dùng CI 95% hai phía làm proxy cho "
            "TOST (Two One-Sided Tests) thật; thống kê viên nên đối chiếu bằng phần mềm chuyên dụng "
            "(R TOSTER/PowerTOST) nếu kết luận equivalence là trọng yếu cho đề tài — cùng caveat đã "
            "ghi ở run_g3_auto.py về việc chưa tự động hóa công thức TOST ở bước cỡ mẫu.]"
        )
    return {"hypothesis_type": hypothesis_type, "margin": margin,
            "risk_diff_ci_95": [lo, hi], "note": note}


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
# 6a. MULTIPLE IMPUTATION (thay complete-case khi có dữ liệu thiếu) — vá 2026-07-15
# ════════════════════════════════════════════════════════════════════════════

def multiple_imputation_model(df: pd.DataFrame, outcome_col: str, group_col: str,
                               covariates: list, outcome_type: str = "auto",
                               n_imputations: int = 20) -> dict:
    """Multiple imputation THẬT (statsmodels MICEData+MICE, m=n_imputations mặc
    định 20, pooling theo luật Rubin qua MICEResults) — vá 2026-07-15. Trước đây
    "MI" trong exports/<study>/sensitivity_analysis.py (template do run_g6_auto.py
    sinh ra) chỉ là mean-impute tự khai KHÔNG PHẢI MI thật ("MI-demo (mean-impute;
    R mice m=20 for real)") — MI thật (mice m=20, method pmm) CHỈ tồn tại trong R
    template, bị comment `#` chờ dữ liệu thật. Hàm này thực thi MI thật bằng
    Python, không cần rời sang R.

    Chỉ chạy khi CÓ dữ liệu thiếu trong chính các biến phân tích (khác
    analyze_missingness() vốn quét TOÀN dataset kể cả biến chỉ dùng cho Bảng 1)
    — trả {"skipped": True, ...} nếu không, để main() không tạo output thừa.

    Đổi tên cột sang định danh an toàn (v0, v1, …) trước khi đưa vào
    MICEData/công thức Patsy — xác nhận bằng test thật: MICEData tự dựng công
    thức nội bộ theo TÊN CỘT GỐC lúc impute từng biến, và patsy.dmatrices ném
    SyntaxError ngay nếu tên cột có khoảng trắng/dấu gạch ngang (rất thường gặp
    trong CSV thật, vd "blood pressure"). Kết quả map ngược lại tên gốc trước
    khi trả về — bác sĩ không thấy tên nội bộ v0/v1 bao giờ."""
    if not HAS_STATSMODELS:
        return {
            "error": "statsmodels chưa cài. Chạy: pip install statsmodels",
            "note": "[CẦN BỔ SUNG — multiple imputation cần statsmodels]",
        }
    from statsmodels.imputation.mice import MICE, MICEData

    if outcome_type == "auto":
        outcome_type = detect_var_type(df[outcome_col])
    available_covs = [c for c in covariates if c in df.columns]
    predictors = [group_col] + available_covs
    analysis_cols = [outcome_col] + predictors
    sub = df[analysis_cols].copy()

    n_total = len(sub)
    n_complete = int(sub.notna().all(axis=1).sum())
    n_missing_rows = n_total - n_complete
    if n_missing_rows == 0:
        return {
            "skipped": True,
            "reason": f"Không có dữ liệu thiếu trong {len(analysis_cols)} biến phân tích "
                      f"({', '.join(analysis_cols)}) — MI không cần thiết, complete-case "
                      f"đã dùng toàn bộ {n_total} quan sát.",
        }

    safe_map = {c: f"v{i}" for i, c in enumerate(analysis_cols)}
    rev_map = {v: k for k, v in safe_map.items()}
    sub_safe = sub.rename(columns=safe_map)
    formula = f"{safe_map[outcome_col]} ~ " + " + ".join(safe_map[p] for p in predictors)
    model_class = sm.Logit if outcome_type == "binary" else sm.OLS
    fit_kwds = {"disp": 0} if outcome_type == "binary" else None

    try:
        imp = MICEData(sub_safe)
        mice = MICE(formula, model_class, imp, fit_kwds=fit_kwds)
        res = mice.fit(n_imputations=n_imputations, n_burnin=10)
    except Exception as e:
        return {"error": str(e), "note": "[CẦN BIOSTATISTICIAN — MI không hội tụ]"}

    ci = res.conf_int()
    results = []
    for i, safe_name in enumerate(res.model.exog_names):
        if safe_name == "Intercept":
            continue
        var = rev_map.get(safe_name, safe_name)
        est = float(res.params[i])
        lo, hi = float(ci[i][0]), float(ci[i][1])
        p = round(float(res.pvalues[i]), 4)
        if outcome_type == "binary":
            results.append({"variable": var, "OR_adj": round(float(np.exp(est)), 3),
                             "CI_95": [round(float(np.exp(lo)), 3), round(float(np.exp(hi)), 3)],
                             "p": p})
        else:
            results.append({"variable": var, "beta": round(est, 4),
                             "CI_95": [round(lo, 4), round(hi, 4)], "p": p})

    return {
        "model": "logistic_mi" if outcome_type == "binary" else "linear_mi",
        "n_imputations": n_imputations,
        "n_total": n_total, "n_complete_case": n_complete,
        "n_missing_rows": n_missing_rows,
        "pct_missing_rows": round(n_missing_rows / n_total * 100, 1),
        "results": results,
    }


# ════════════════════════════════════════════════════════════════════════════
# 6b. PHÂN TÍCH SỐNG CÒN (Cox PH + Kaplan-Meier) — vá 2026-07-15
# ════════════════════════════════════════════════════════════════════════════
# Trước đây Cox/KM thật (lifelines) chỉ tồn tại nhúng trong chuỗi template mà
# run_g6_auto.py ghi ra exports/<study>/run_analysis_cli.py cho bác sĩ tự chạy
# tay, TÁCH khỏi cổng data-lock/G2/G4/G5 của chính script này. Hai hàm dưới đây
# PORT lại đúng công thức/tên cột đã dùng ở run_g6_auto.py::run_cox/plot_km,
# nhưng THỰC THI THẬT tại đây — qua đúng cổng đã kiểm ở main().

def survival_model(df: pd.DataFrame, time_col: str, event_col: str,
                    group_col: str, covariates: list) -> dict:
    """Cox proportional-hazards THẬT (lifelines.CoxPHFitter) — mô hình thô (chỉ
    group_col) rồi hiệu chỉnh (thêm covariates nếu có). EPV (Events-Per-Variable,
    Peduzzi 1995 — SỬA 2026-07-24, vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện
    LOW: trước đây ghi nhầm "1996", đó là bài Peduzzi cho hồi quy LOGISTIC, không
    phải Cox; bài đúng cho ngưỡng EPV của Cox là Peduzzi P, Concato J, Feinstein AR,
    Holford TR. "Importance of events per independent variable in proportional
    hazards regression analysis. II." J Clin Epidemiol. 1995;48(12):1503-1510)
    tính theo SỐ BIẾN CỐ — cùng ngưỡng ≥10 biến cố/biến áp dụng cho logistic ở
    multivariate_model() (đó mới đúng là Peduzzi 1996)."""
    if not HAS_LIFELINES:
        return {
            "error": "lifelines chưa cài. Chạy: pip install lifelines",
            "note": "[CẦN BỔ SUNG — phân tích sống còn cần lifelines]",
        }
    from lifelines import CoxPHFitter

    avail_covs = [c for c in covariates if c in df.columns]
    essential = [time_col, event_col, group_col] + avail_covs
    data = df[essential].dropna()
    n = len(data)
    n_events = int(data[event_col].sum())
    n_predictors = 1 + len(avail_covs)

    result = {"n": n, "n_events": n_events, "time_col": time_col,
              "event_col": event_col, "group_col": group_col}
    if n_events < n_predictors * 10:
        result["epv_warning"] = (
            f"Số biến cố {n_events} có thể không đủ EPV cho {n_predictors} biến dự "
            f"báo (cần ≥10 biến cố/biến — Peduzzi 1995, J Clin Epidemiol 1995;48(12):1503-1510)."
        )

    def _fit(cols: list) -> dict:
        cph = CoxPHFitter()
        cph.fit(data[cols], duration_col=time_col, event_col=event_col)
        s = cph.summary
        hr = float(s.loc[group_col, "exp(coef)"])
        ci_low = float(s.loc[group_col, "exp(coef) lower 95%"])
        ci_up = float(s.loc[group_col, "exp(coef) upper 95%"])
        p = float(s.loc[group_col, "p"])
        return {
            "HR": round(hr, 3), "CI_95": [round(ci_low, 3), round(ci_up, 3)],
            "p": round(p, 4), "concordance": round(float(cph.concordance_index_), 4),
        }

    try:
        result["crude"] = _fit([time_col, event_col, group_col])
    except Exception as e:
        result["crude_error"] = str(e)

    if avail_covs:
        try:
            result["adjusted"] = _fit([time_col, event_col, group_col] + avail_covs)
            result["adjusted_covariates"] = avail_covs
        except Exception as e:
            result["adjusted_error"] = str(e)

    return result


def kaplan_meier_summary(df: pd.DataFrame, time_col: str, event_col: str,
                          group_col: str, out_path: Path = None) -> dict:
    """Kaplan-Meier median survival theo nhóm + log-rank test THẬT (lifelines) —
    cùng phép tính run_g6_auto.py::plot_km. Vẽ đường cong (PNG) nếu matplotlib có
    sẵn và out_path được cấp — KHÔNG bắt buộc, script vẫn trả số liệu nếu thiếu."""
    if not HAS_LIFELINES:
        return {"error": "lifelines chưa cài. Chạy: pip install lifelines"}
    from lifelines import KaplanMeierFitter
    from lifelines.statistics import logrank_test

    groups = sorted(df[group_col].dropna().unique())
    per_group = {}
    fitted = {}
    for g in groups:
        sub = df[df[group_col] == g][[time_col, event_col]].dropna()
        if sub.empty:
            continue
        kmf = KaplanMeierFitter()
        kmf.fit(sub[time_col], event_observed=sub[event_col], label=str(g))
        fitted[g] = kmf
        median = kmf.median_survival_time_
        per_group[str(g)] = {
            "n": len(sub),
            "n_events": int(sub[event_col].sum()),
            # median_survival_time_ = inf khi <50% nhóm đã có biến cố (chưa đạt
            # trung vị) — không phải NaN; cả hai đều nghĩa "chưa xác định được".
            "median_survival": (
                None if pd.isna(median) or np.isinf(median) else round(float(median), 2)
            ),
        }

    result = {"groups": per_group}
    if len(groups) == 2:
        g0, g1 = groups
        s0 = df[df[group_col] == g0][[time_col, event_col]].dropna()
        s1 = df[df[group_col] == g1][[time_col, event_col]].dropna()
        if not s0.empty and not s1.empty:
            lr = logrank_test(s0[time_col], s1[time_col],
                               event_observed_A=s0[event_col], event_observed_B=s1[event_col])
            result["logrank_p"] = round(float(lr.p_value), 4)

    if out_path is not None and HAS_MATPLOTLIB and fitted:
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots(figsize=(9, 6))
            colors = ["#2E9FDF", "#E7B800", "#66C2A5", "#FC8D62"]
            for (g, kmf), color in zip(fitted.items(), colors):
                kmf.plot_survival_function(ax=ax, color=color, ci_show=True)
            if "logrank_p" in result:
                ax.text(0.65, 0.08, f"Log-rank p = {result['logrank_p']}",
                        transform=ax.transAxes, fontsize=11,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.8))
            ax.set_xlabel("Thời gian theo dõi")
            ax.set_ylabel("Xác suất không có biến cố")
            ax.set_title(f"Kaplan-Meier — {group_col}")
            ax.legend()
            ax.set_ylim(0, 1.05)
            ax.grid(alpha=0.3)
            plt.tight_layout()
            plt.savefig(out_path, dpi=300, bbox_inches="tight")
            plt.close(fig)
            result["plot_path"] = str(out_path)
        except Exception as e:
            result["plot_error"] = str(e)

    return result


# ════════════════════════════════════════════════════════════════════════════
# 7. ĐỊNH DẠNG ĐẦU RA CHO AGENT
# ════════════════════════════════════════════════════════════════════════════

def format_table1_text(t1: dict) -> str:
    groups = t1["groups"]
    n = t1["n_per_group"]
    header = "BẢNG 1 — ĐẶC ĐIỂM MẪU\n" + "=" * 70
    group_headers = "".join(
        f"{'Nhóm ' + str(g) + ' (n=' + str(n.get(g, '-')) + ')':<22}"
        for g in groups
    )
    header += f"\n{'Biến số':<30}" + group_headers
    header += f"{'p':>10}  {'Kiểm định'}"
    lines = [header, "-" * 70]
    for row in t1["rows"]:
        var = row["variable"][:28]
        grp_vals = "".join(f"{row.get('grp_' + g, 'N/A'):<22}" for g in groups)
        p = f"{row.get('p', '')}" if row.get("p") is not None else ""
        test = row.get("test", "")
        lines.append(f"{var:<30}{grp_vals}{p:>10}  {test}")
    return "\n".join(lines)


def format_outcome_text(res: dict, outcome_col: str, hypothesis_interp: dict = None) -> str:
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
        if "risk_diff" in res:
            rd_ci = res["risk_diff_ci_95"]
            lines.append(f"  Risk difference = {res['risk_diff']} (95%CI {rd_ci[0]}–{rd_ci[1]})")
    else:
        lines.append(f"  Nhóm {g[0]}: Mean={n0.get('mean','?')} ± SD={n0.get('sd','?')}")
        lines.append(f"  Nhóm {g[1]}: Mean={n1.get('mean','?')} ± SD={n1.get('sd','?')}")
        lines.append(f"  {res.get('effect', 'N/A')}")
    if "p_value" in res:
        lines.append(f"  p = {res['p_value']} ({res.get('test','')})")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện HIGH):
    # xem interpret_hypothesis_type() — chỉ xuất hiện khi G3 thiết kế NI/
    # equivalence, KHÔNG đổi gì cho đề tài superiority (mặc định, đa số).
    # SỬA 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện liên quan
    # tới HIGH #7): điều kiện cũ `hypothesis_interp.get("hypothesis_type")` chỉ
    # đúng cho nhánh đã tính đủ (kết cục nhị phân + có margin) — 2 nhánh dự
    # phòng của interpret_hypothesis_type() (kết cục KHÔNG nhị phân; thiếu
    # margin) chỉ trả về {"note": ...} không có khóa "hypothesis_type", nên
    # cảnh báo "[CẦN THỐNG KÊ VIÊN]"/"[CẦN — thiếu margin]" bị ÂM THẦM rớt
    # mất khỏi file kết quả thật dù đã được TÍNH — bác sĩ không bao giờ thấy.
    if hypothesis_interp and hypothesis_interp.get("note"):
        lines.append("")
        if hypothesis_interp.get("hypothesis_type"):
            lines.append(f"  ── DIỄN GIẢI {hypothesis_interp['hypothesis_type'].upper()} "
                          f"(margin=±{hypothesis_interp['margin']}) ──")
        else:
            lines.append("  ── DIỄN GIẢI GIẢ THUYẾT NON_INFERIORITY/EQUIVALENCE ──")
        lines.append(f"  {hypothesis_interp['note']}")
    lines.append("\n[BÁC SĨ KIỂM TRA: số liệu lấy trực tiếp từ dữ liệu thật]")
    return "\n".join(lines)


def format_multivariate_text(mv: dict) -> str:
    if "error" in mv:
        return f"HỒI QUY ĐA BIẾN: {mv['error']}\n{mv.get('note','')}"
    if "warning" in mv:
        return f"HỒI QUY ĐA BIẾN: {mv['warning']}\n[CẦN BIOSTATISTICIAN XÁC NHẬN]"
    lines = [f"BẢNG 4 — MÔ HÌNH ĐA BIẾN ({mv['model'].upper()})", "=" * 70]
    metric_label = "AIC" if mv["model"] == "logistic" else "R²"
    metric_value = mv.get("aic", mv.get("r_squared", "?"))
    lines.append(f"  n = {mv['n']} | {metric_label} = {metric_value}")
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


def format_mi_text(mi: dict, mv: dict = None) -> str:
    """mv (kết quả complete-case của multivariate_model(), nếu có) được đặt cạnh
    MI để bác sĩ thấy trực tiếp mức chênh — đúng mục đích sensitivity analysis
    (không chỉ chạy MI rồi báo số, mà cho thấy MI đổi kết luận đến đâu)."""
    if mi.get("skipped"):
        return f"MULTIPLE IMPUTATION: {mi['reason']}"
    if "error" in mi:
        return f"MULTIPLE IMPUTATION: {mi['error']}\n{mi.get('note', '')}"
    lines = [f"BẢNG 5 — MULTIPLE IMPUTATION ({mi['model'].upper()}, m={mi['n_imputations']})", "=" * 70]
    lines.append(f"  Complete-case: n = {mi['n_complete_case']}/{mi['n_total']} "
                 f"({mi['n_missing_rows']} hàng thiếu, {mi['pct_missing_rows']}%)")
    lines.append(f"\n  {'Biến số':<22} {'OR/β (MI)':>14}  {'95%CI (MI)':>18}  {'p':>7}   {'so complete-case'}")
    lines.append("  " + "-" * 90)
    mv_lookup = {r["variable"]: r for r in (mv.get("results", []) if mv else [])}
    for r in mi.get("results", []):
        est = r.get("OR_adj", r.get("beta", "?"))
        ci = r["CI_95"]
        p = r["p"]
        star = "*" if p < 0.05 else " "
        cc = mv_lookup.get(r["variable"])
        cc_str = ""
        if cc:
            cc_est = cc.get("OR_adj", cc.get("beta", "?"))
            cc_str = f"{cc_est} ({cc['CI_95'][0]}–{cc['CI_95'][1]}, p={cc['p']})"
        lines.append(f"  {r['variable'][:20]:<22} {est:>14}  {ci[0]}–{ci[1]:<10}  {p:>6}{star}   {cc_str}")
    lines.append("\n* p < 0.05 (MI). So sánh với complete-case để đánh giá độ nhạy với giả định thiếu dữ liệu.")
    lines.append("[BÁC SĨ KIỂM TRA: MI dùng statsmodels MICEData/MICE, pooling theo luật Rubin]")
    return "\n".join(lines)


def format_survival_text(res: dict, km: dict = None, hypothesis_interp: dict = None) -> str:
    if "error" in res:
        return f"PHÂN TÍCH SỐNG CÒN: {res['error']}\n{res.get('note', '')}"
    lines = [f"BẢNG 3 — PHÂN TÍCH SỐNG CÒN (Cox PH) — {res.get('group_col', '')}", "=" * 70]
    lines.append(f"  n = {res.get('n', '?')} | Biến cố = {res.get('n_events', '?')}")
    if res.get("epv_warning"):
        lines.append(f"  ⚠ {res['epv_warning']} [CẦN BIOSTATISTICIAN XÁC NHẬN]")
    if "crude_error" in res:
        lines.append(f"  Mô hình thô: LỖI — {res['crude_error']}")
    elif "crude" in res:
        c = res["crude"]
        lines.append(f"  Thô: HR = {c['HR']} (95%CI {c['CI_95'][0]}–{c['CI_95'][1]}), "
                      f"p = {c['p']}, C-index = {c['concordance']}")
    if "adjusted_error" in res:
        lines.append(f"  Mô hình hiệu chỉnh: LỖI — {res['adjusted_error']}")
    elif "adjusted" in res:
        a = res["adjusted"]
        covs = ", ".join(res.get("adjusted_covariates", [])[:4])
        lines.append(f"  Hiệu chỉnh ({covs}): HR = {a['HR']} (95%CI {a['CI_95'][0]}–{a['CI_95'][1]}), "
                      f"p = {a['p']}, C-index = {a['concordance']}")
    if km and not km.get("error"):
        lines.append("\n  KAPLAN-MEIER:")
        for g, info in km.get("groups", {}).items():
            med = info.get("median_survival")
            med_str = f"{med}" if med is not None else "chưa đạt (>50% còn sống)"
            lines.append(f"    Nhóm {g}: n={info['n']}, biến cố={info['n_events']}, "
                          f"trung vị sống còn={med_str}")
        if "logrank_p" in km:
            lines.append(f"    Log-rank p = {km['logrank_p']}")
        if km.get("plot_path"):
            lines.append(f"    Đường cong: {km['plot_path']}")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện HIGH):
    # xem chú thích ở điểm gọi (main()) — nhánh sống còn trước đây không hề
    # diễn giải hypothesis_type/margin dù đã đọc từ G3 checkpoint.
    if hypothesis_interp and hypothesis_interp.get("note"):
        lines.append("")
        lines.append("  ── DIỄN GIẢI GIẢ THUYẾT NON_INFERIORITY/EQUIVALENCE ──")
        lines.append(f"  {hypothesis_interp['note']}")
    lines.append("\n[BÁC SĨ KIỂM TRA: số liệu lấy trực tiếp từ dữ liệu thật]")
    return "\n".join(lines)


def _generate_r_script_survival(study: str, gate: str, time_col: str, event_col: str,
                                 group_col: str, covariates: list) -> str:
    """Script R tái lặp cho thiết kế sống còn (coxph, package `survival`) — KHÔNG
    comment sẵn như bản Cox trong run_g6_auto.py's template (nơi Cox bị # vì chờ
    dữ liệu thật/G4 SAP locked); script NÀY mô tả một phân tích ĐÃ CHẠY THẬT trên
    dataset đã khóa (qua _require_locked_analysis_dataset ở main()), nên chạy được
    ngay để đối chiếu độc lập."""
    formula = " + ".join([group_col] + covariates)
    run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    return (
        f"# ══════════════════════════════════════════════\n"
        f"# Script R tái lặp (sống còn) — {study} | {gate}\n"
        f"# Tạo tự động bởi run_stats_analysis.py\n"
        f"# Ngày: {run_date}\n"
        f"# ══════════════════════════════════════════════\n"
        "set.seed(42)  # CỐ ĐỊNH SEED\n\n"
        "library(survival); library(survminer); library(tableone); library(dplyr)\n\n"
        "# 1. Đọc dữ liệu (thay đường dẫn)\n"
        'data <- read.csv("data.csv")  # hoặc read.xlsx\n\n'
        "# 2. Bảng 1\n"
        f'vars_all <- setdiff(names(data), c("{group_col}", "{event_col}", "{time_col}"))\n'
        f'tab1 <- CreateTableOne(vars = vars_all, strata = "{group_col}", data = data)\n'
        "print(tab1, showAllLevels = TRUE, smd = TRUE)\n\n"
        f'# 3. Kaplan-Meier + log-rank\n'
        f'fit_km <- survfit(Surv({time_col}, {event_col}) ~ {group_col}, data = data)\n'
        f'survdiff(Surv({time_col}, {event_col}) ~ {group_col}, data = data)  # log-rank p\n'
        'ggsurvplot(fit_km, data = data, pval = TRUE, conf.int = TRUE, risk.table = TRUE)\n\n'
        f"# 4. Cox proportional-hazards\n"
        f"model_crude <- coxph(Surv({time_col}, {event_col}) ~ {group_col}, data = data)\n"
        f"model_adj   <- coxph(Surv({time_col}, {event_col}) ~ {formula}, data = data)\n\n"
        "# HR + 95%CI (không chỉ p-value)\n"
        "exp(cbind(HR = coef(model_adj), confint(model_adj)))\n\n"
        "# 5. Kiểm tra giả định proportional-hazards (Schoenfeld residuals)\n"
        "cox.zph(model_adj)\n\n"
        "# 6. Ghi session info (tái lặp)\n"
        'sink("session_info.txt"); sessionInfo(); sink()\n'
    )


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
    trong checkpoint JSON) là điều kiện DUY NHẤT để cho chạy phân tích thật.

    Vá 2026-07-12 (audit toàn diện cổng G0-G9): ủy quyền cho gate_contract.
    ledger_approved() — nơi DUY NHẤT còn giữ logic hash+not-synthetic+not-agent
    (trước đây có 6 bản sao gần-giống-nhau rải khắp hệ thống, kể cả script THẬT
    chạy dữ liệu bệnh nhân này — sửa 1 nơi từng quên 5 nơi khác). Đồng thời có
    thêm xác minh CHỮ KÝ actor thật (HMAC, xem gate_contract.py) nếu máy đã thiết
    lập khóa ký — script này chạy TRỰC TIẾP trên dữ liệu thật nên đây là nơi
    QUAN TRỌNG NHẤT để có chữ ký thật, không chỉ hash+cờ tự khai."""
    return GC.ledger_approved(gate_id, study, artifact_path)


def _sha256_file(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_json(path: Path) -> dict:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, OSError):
        return {}
    return {}


def _data_lock_manifest_path(study: str) -> Path:
    study_dir = Path("exports") / study
    meta = _load_json(study_dir / "study_meta.json")
    rel = ((meta.get("real_data_lock") or {}).get("manifest"))
    if rel:
        return study_dir / rel
    return study_dir / "DATA_LOCK_manifest.json"


def _require_locked_analysis_dataset(study: str, data_arg: str) -> dict:
    """Chặn phân tích chính nếu --data không phải dataset đã khóa trong manifest."""
    study_dir = Path("exports") / study
    manifest_path = _data_lock_manifest_path(study)
    manifest = _load_json(manifest_path)
    blockers = []
    if not manifest:
        blockers.append("missing_DATA_LOCK_manifest")
    elif manifest.get("status") != "LOCKED_FOR_ANALYSIS":
        blockers.append(f"manifest_status_not_locked:{manifest.get('status')}")
    elif manifest.get("analysis_allowed") is not True:
        blockers.append("analysis_allowed_false")

    locked_rel = manifest.get("locked_dataset_path") if manifest else None
    locked_path = study_dir / locked_rel if locked_rel else None
    provided_path = Path(data_arg)
    if not provided_path.exists():
        blockers.append("provided_data_missing")
    if not locked_path:
        blockers.append("locked_dataset_path_missing")
    elif not locked_path.exists():
        blockers.append("locked_dataset_missing")
    elif provided_path.exists() and provided_path.resolve() != locked_path.resolve():
        blockers.append("provided_data_is_not_locked_dataset")

    expected_sha = manifest.get("sha256") if manifest else None
    if locked_path and locked_path.exists():
        actual_sha = _sha256_file(locked_path)
        if not expected_sha:
            blockers.append("locked_dataset_checksum_missing")
        elif actual_sha != expected_sha:
            blockers.append("locked_dataset_checksum_mismatch")

    if blockers:
        print("✗ DỪNG: DATA LOCK — --data phải là dataset phân tích đã khóa.")
        print(f"   Manifest: {manifest_path}")
        print(f"   File --data: {data_arg}")
        if locked_rel:
            print(f"   Dataset khóa kỳ vọng: {locked_path}")
        print("   Lý do:")
        for blocker in blockers:
            print(f"   - {blocker}")
        print("   Khóa dữ liệu bằng:")
        print("     python tools/lock_analysis_dataset.py --study <MÃ> --clean-data <df_clean.csv> "
              "--query-log <query_log.csv> --lock-date <YYYY-MM-DD> --approved-by <PI> "
              "--sap-version <x.y> --confirm-deidentified --confirm-clean-copy "
              "--confirm-no-open-query --confirm-sap-locked")
        sys.exit(1)

    print(f"✓ DATA LOCK: dùng dataset đã khóa ({locked_rel}); checksum khớp.")
    return manifest


def main():
    parser = argparse.ArgumentParser(
        description="Phân tích thống kê tự động từ file dữ liệu thật"
    )
    parser.add_argument("--data", required=True, help="Đường dẫn file CSV/Excel")
    parser.add_argument("--outcome", help="Cột kết cục chính (nhị phân 0/1 hoặc liên tục)")
    parser.add_argument("--group", help="Cột nhóm/phơi nhiễm (so sánh 2 nhóm; cũng là biến "
                                        "chính trong mô hình Cox khi dùng --time/--event)")
    parser.add_argument("--time", help="Cột thời gian theo dõi (kích hoạt Cox PH/Kaplan-Meier "
                                       "cùng --event, vá 2026-07-15) — số, cùng đơn vị mọi hàng")
    parser.add_argument("--event", help="Cột biến cố (0/1; kích hoạt Cox PH/Kaplan-Meier "
                                        "cùng --time, vá 2026-07-15)")
    parser.add_argument("--covariates", default="",
                        help="Danh sách biến hiệu chỉnh, phân cách bằng dấu phẩy")
    parser.add_argument("--n-imputations", type=int, default=20,
                        help="Số bộ dữ liệu impute (m) cho multiple imputation khi biến phân "
                             "tích có dữ liệu thiếu — mặc định 20 (vá 2026-07-15)")
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

    if bool(args.time) != bool(args.event):
        print("✗ DỪNG: --time và --event phải đi CÙNG NHAU (thiết kế sống còn cần cả hai).")
        sys.exit(1)
    if args.time and args.event and not args.group:
        print("✗ DỪNG: Cox PH cần --group (biến phơi nhiễm/exposure chính của mô hình).")
        sys.exit(1)

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
    # Vá 2026-07-12 (audit toàn diện): --i-confirm-* trước đây bỏ qua TOÀN BỘ kiểm
    # tra kể cả ledger — cờ tự khai trần, không xác minh gì, đủ để chạy phân tích
    # trên dữ liệu bệnh nhân THẬT không có phê duyệt nào (kiểm định đối kháng xác
    # nhận bypass này thật). Nay cờ CHỈ thay thế checkpoint-file (đúng ý nghĩa gốc
    # "checkpoint mất nhưng phê duyệt thật đã có") — ledger_approved() LUÔN bắt
    # buộc, không cờ nào bỏ qua được.
    g2_cp = _load_checkpoint(args.study, "G2")
    g2_checkpoint_locked = _is_locked(g2_cp.get("g2_status", g2_cp.get("G2_STATUS")))
    g2_ledger_ok = _ledger_approved(
        args.study, "G2", Path("exports") / args.study / f"G2_A3_ETHICS_PACKAGE_{args.study}.md")
    g2_quality_ok = GC.g2_quality_contract_satisfied(
        g2_cp,
        GC.load_study_meta(Path("exports") / args.study),
    )
    g2_locked = (
        (g2_checkpoint_locked or args.i_confirm_irb_approved)
        and g2_ledger_ok
        and g2_quality_ok
    )
    if not g2_locked:
        print("✗ DỪNG: G2 (phê duyệt đạo đức/IRB) chưa xác nhận LOCKED bằng phê duyệt thật.")
        print(f"   G2 checkpoint: {'✅ LOCKED' if g2_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g2_ledger_ok else '⚠️ thiếu/không khớp'}")
        if not g2_quality_ok:
            print("   G2 quality: ⚠️ chưa PASS_G2_APPROVED "
                  "(thiếu metadata/phiên bản/hiệu lực/đăng ký hợp lệ).")
        # VÁ 2026-07-27 vòng 6: in RÕ LÝ DO. Vòng kiểm định thứ năm chỉ ra bản vá chẩn
        # đoán trước đó chỉ nối vào run_g10_assemble.py (G8/G9) — CHÍNH CHỖ NGUY HIỂM
        # NHẤT này thì bỏ sót: cổng G2 gác việc phân tích dữ liệu BỆNH NHÂN THẬT, lại
        # chỉ in "thiếu/không khớp" y hệt nhau cho ba tình huống khác hẳn nhau, và ở đây
        # KHÔNG có cờ bỏ qua nào — nên một dòng rác trong sổ cái là chặn cứng cả đề tài
        # mà bác sĩ không có manh mối nào để gỡ. Đúng mẫu "sửa 1 chỗ quên chỗ anh em".
        _why = GC.gate_block_reason(
            "G2", args.study,
            Path("exports") / args.study / f"G2_A3_ETHICS_PACKAGE_{args.study}.md")
        if _why:
            print(f"   ⚠️  LÝ DO: {_why}")
        print("   KHÔNG chạy phân tích trên dữ liệu bệnh nhân THẬT khi chưa có phê duyệt đạo đức thật.")
        print("   Ghi phê duyệt thật bằng (bác sĩ TỰ TAY chạy, không nhờ agent):")
        print(f"     python tools/approve_gate.py --study \"{args.study}\" --gate G2 "
              f"--artifact exports/{args.study}/G2_A3_ETHICS_PACKAGE_{args.study}.md ...")
        print("   --i-confirm-irb-approved chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)
    g4_cp = _load_checkpoint(args.study, "G4")
    g5_cp = _load_checkpoint(args.study, "G5")
    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 16, phát hiện HIGH):
    # đọc lại hypothesis_type/margin đã ghim ở G3 (run_g3_auto.py) để diễn
    # giải kết cục chính đúng khung — xem interpret_hypothesis_type().
    g3_cp = _load_checkpoint(args.study, "G3")
    hypothesis_type = g3_cp.get("hypothesis_type", "superiority")
    hypothesis_margin = g3_cp.get("margin")
    if hypothesis_type and hypothesis_type != "superiority":
        print(f"ℹ️  G3 checkpoint: hypothesis_type={hypothesis_type}, margin={hypothesis_margin} "
              "— sẽ diễn giải kết cục chính theo khung này (không chỉ p-value superiority).")

    # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện CRITICAL):
    # trước đây script này (engine THỰC THI phân tích trên dữ liệu đã khóa)
    # hoàn toàn không đọc G0/G1 checkpoint — chạy y hệt một quy trình so sánh
    # 2 nhóm kiểu cohort/RCT (Bảng 1, OR/MD thô, logistic/linear đa biến, Cox)
    # cho BẤT KỲ design_code nào, kể cả "qualitative"/"sr_ma" (không có trục
    # phơi nhiễm/kết cục participant-level phù hợp khuôn này) và "prediction"/
    # "diagnostic" (cần AUC/calibration hoặc Se/Sp/PPV/NPV — không phải OR/HR
    # thô). Không có cảnh báo/guardrail nào chặn — khác hẳn sibling
    # run_g6_auto.py vốn đã có _WRONG_METHOD_DESIGNS cho các thiết kế này (chỉ
    # sinh TEMPLATE, không chạy thật). Vì script NÀY chạy dữ liệu THẬT đã khóa,
    # một kết quả sai-phương-pháp ở đây có nguy cơ bị dùng thẳng làm "kết cục
    # chính" trong bản thảo mà không ai được cảnh báo là sai phương pháp.
    g1_cp = _load_checkpoint(args.study, "G1")
    design_code = g1_cp.get("design_code") or (g1_cp.get("design") or {}).get("internal_code")
    specialist_modules = g1_cp.get("specialist_modules") or []
    # "qualitative"/"sr_ma": KHÔNG có trục so sánh 2-nhóm participant-level phù
    # hợp khuôn cohort/RCT của engine này — DỪNG thay vì âm thầm ép dữ liệu
    # vào Bảng 1/chi-square (định tính) hay coi mỗi study là 1 "participant"
    # (sr_ma, vốn cần pooling/heterogeneity ở tầng study, không phải cá thể).
    if design_code in ("qualitative", "sr_ma"):
        print(f"✗ DỪNG: design_code='{design_code}' (từ G1 checkpoint) KHÔNG được engine "
              "so sánh 2-nhóm cohort/RCT của run_stats_analysis.py hỗ trợ.")
        if design_code == "qualitative":
            print("   Định tính cần mã hóa chủ đề (COREQ/SRQR), KHÔNG có mô hình thống kê suy diễn "
                  "kiểu OR/MD/HR — dùng quy trình phân tích định tính chuyên biệt (agent "
                  "`nghien-cuu-dinh-tinh`), KHÔNG chạy script này.")
        else:
            print("   SR/MA cần phân tích gộp (pooled effect + heterogeneity I²/Q/τ², forest/funnel "
                  "plot) trên bảng STUDY-LEVEL, không phải participant-level — dùng agent "
                  "`meta-phan-tich`, KHÔNG chạy script này.")
        sys.exit(1)
    # "prediction"/"diagnostic": có dữ liệu định lượng nhưng thước đo ĐÚNG khác
    # hẳn OR/MD/HR thô — CẢNH BÁO rõ (không chặn cứng, vì vẫn có thể có mục
    # tiêu phụ/khám phá hợp lệ dùng đúng engine 2-nhóm này).
    _WRONG_PRIMARY_MEASURE_HINT = {
        "prediction": "AUC/C-statistic + calibration (TRIPOD+AI) — KHÔNG phải OR/HR đơn biến/đa biến",
        "diagnostic": "Se/Sp/PPV/NPV + ROC (STARD) — KHÔNG phải OR/MD so sánh 2 nhóm kiểu cohort",
    }
    if design_code in _WRONG_PRIMARY_MEASURE_HINT:
        print(f"⚠️  [CẦN THỐNG KÊ VIÊN] design_code='{design_code}' — kết quả OR/MD/HR mà script này "
              f"tính KHÔNG phải thước đo chính xác cho thiết kế này (cần {_WRONG_PRIMARY_MEASURE_HINT[design_code]}). "
              "Chỉ dùng làm phân tích PHỤ/khám phá nếu có mục tiêu phụ phù hợp; KHÔNG báo cáo làm kết cục chính.")
    if "economic" in specialist_modules:
        print("⚠️  [CẦN THỐNG KÊ VIÊN] specialist_modules phát hiện cấu phần KINH TẾ Y TẾ cộng thêm "
              "(G1) — script này KHÔNG tính ICER/chi phí-hiệu quả (CHEERS 2022); cần phân tích riêng "
              "cho cấu phần đó, không suy ra được từ Bảng 1/2/3 ở đây.")
    g4_checkpoint_locked = _is_locked(g4_cp.get("g4_status", g4_cp.get("G4_STATUS")))
    g5_checkpoint_locked = _is_locked(g5_cp.get("g5_status", g5_cp.get("G5_STATUS")))
    g4_ledger_ok = _ledger_approved(
        args.study, "G4", Path("exports") / args.study / f"G4_A5_SAP_FINAL_{args.study}.md")
    g5_ledger_ok = _ledger_approved(
        args.study, "G5", Path("exports") / args.study / "G5_checkpoint.json")
    g4_locked = (g4_checkpoint_locked or args.i_confirm_sap_locked) and g4_ledger_ok
    g5_locked = (g5_checkpoint_locked or args.i_confirm_sap_locked) and g5_ledger_ok
    if not (g4_locked and g5_locked):
        print("✗ DỪNG: G4 (SAP) hoặc G5 (khóa DB) chưa xác nhận LOCKED bằng phê duyệt thật.")
        print(f"   G4 checkpoint: {'✅ LOCKED' if g4_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g4_ledger_ok else '⚠️ thiếu/không khớp'}")
        print(f"   G5 checkpoint: {'✅ LOCKED' if g5_checkpoint_locked else '⚠️ chưa LOCKED/không tìm thấy'}"
              f"  |  approval_ledger (chữ ký thật): {'✅ khớp' if g5_ledger_ok else '⚠️ thiếu/không khớp'}")
        for _g, _art in (("G4", f"G4_A5_SAP_FINAL_{args.study}.md"),
                         ("G5", "G5_checkpoint.json")):
            _why = GC.gate_block_reason(_g, args.study, Path("exports") / args.study / _art)
            if _why:
                print(f"   ⚠️  LÝ DO {_g}: {_why}")
        print("   Không thể chạy phân tích xác nhận trên dữ liệu chưa khóa (chống p-hacking/HARKing).")
        print("   Checkpoint 'LOCKED' không còn đủ — cần bác sĩ tự tay ghi phê duyệt thật bằng:")
        print(f"     python tools/approve_gate.py --study \"{args.study}\" --gate G4 "
              f"--artifact exports/{args.study}/G4_A5_SAP_FINAL_{args.study}.md ...")
        print("   --i-confirm-sap-locked chỉ thay được checkpoint-file bị mất — KHÔNG thay được ledger.")
        sys.exit(1)

    data_lock_manifest = _require_locked_analysis_dataset(args.study, args.data)

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
        "data_lock": {
            "manifest": str(_data_lock_manifest_path(args.study)),
            "locked_dataset_path": data_lock_manifest.get("locked_dataset_path"),
            "sha256": data_lock_manifest.get("sha256"),
            "lock_date": data_lock_manifest.get("lock_date"),
            "approved_by": data_lock_manifest.get("approved_by"),
            "sap_version": data_lock_manifest.get("sap_version"),
        },
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
        hypothesis_interp = interpret_hypothesis_type(res, hypothesis_type, hypothesis_margin)
        res_txt = format_outcome_text(res, args.outcome, hypothesis_interp)
        (prefix.parent / f"{args.gate}_table2_main_outcome.txt").write_text(res_txt, encoding="utf-8")
        summary["primary_outcome"] = res
        if hypothesis_interp:
            summary["hypothesis_interpretation"] = hypothesis_interp
        print(f"✓ Kết cục chính ({res.get('outcome_type','')}): p={res.get('p_value','?')}")
        # SỬA 2026-07-24 (vòng lặp vòng 22): dùng .get("note") thay vì
        # .get("hypothesis_type") — xem chú thích tương ứng trong format_outcome_text().
        if hypothesis_interp.get("note"):
            print(f"  ℹ️  Diễn giải {hypothesis_type}: xem {args.gate}_table2_main_outcome.txt")

        # 6. Đa biến
        mv = multivariate_model(df, args.outcome, args.group, covariates, args.outcome_type)
        mv_txt = format_multivariate_text(mv)
        (prefix.parent / f"{args.gate}_table4_multivariate.txt").write_text(mv_txt, encoding="utf-8")
        summary["multivariate"] = mv
        print(f"✓ Mô hình đa biến: {mv.get('model','?')} ({mv.get('n','?')} quan sát)")

        # 6a. Multiple imputation (chỉ khi biến phân tích có dữ liệu thiếu) — vá 2026-07-15
        mi = multiple_imputation_model(df, args.outcome, args.group, covariates,
                                        args.outcome_type, args.n_imputations)
        summary["multiple_imputation"] = mi
        if mi.get("skipped"):
            print(f"ℹ️  Multiple imputation: bỏ qua ({mi['reason']})")
        elif "error" in mi:
            print(f"✗ Multiple imputation: {mi['error']}")
        else:
            mi_txt = format_mi_text(mi, mv)
            (prefix.parent / f"{args.gate}_table5_multiple_imputation.txt").write_text(
                mi_txt, encoding="utf-8")
            print(f"✓ Multiple imputation (m={mi['n_imputations']}): "
                  f"{mi['n_missing_rows']}/{mi['n_total']} hàng thiếu được impute")

        # 7. Script R tái lặp
        r_script = generate_r_script(args.study, args.gate, args.outcome,
                                      args.group, covariates, args.outcome_type)
        (prefix.parent / f"{args.gate}_analysis_syntax.R").write_text(r_script, encoding="utf-8")
        print("✓ Script R tái lặp đã tạo")

    # 5b/6b/7b. Thiết kế sống còn (Cox PH + Kaplan-Meier) — vá 2026-07-15
    if args.time and args.event:
        missing_cols = [c for c in (args.time, args.event, args.group) if c not in df.columns]
        if missing_cols:
            print(f"✗ DỪNG: thiếu cột {missing_cols} trong dữ liệu cho phân tích sống còn.")
            sys.exit(1)
        surv = survival_model(df, args.time, args.event, args.group, covariates)
        km_path = prefix.parent / f"{args.gate}_km_curve.png"
        km = kaplan_meier_summary(df, args.time, args.event, args.group, out_path=km_path)
        # THÊM 2026-07-24 (vòng lặp kiểm tra-hoàn thiện vòng 22, phát hiện HIGH):
        # trước đây hypothesis_type/margin (G3) chỉ được diễn giải cho nhánh
        # kết cục nhị phân/liên tục (--outcome) — nhánh sống còn (--time/--event,
        # dùng ĐỘC LẬP không cần --outcome) hoàn toàn không gọi interpret_
        # hypothesis_type(), dù thông báo đầu main() đã in "sẽ diễn giải theo
        # khung này" bất kể loại kết cục. Dùng res giả outcome_type="survival"
        # để tái dùng đúng nhánh dự phòng (không nhị phân) đã có sẵn — tránh
        # đoán/tính tay HR-vs-margin (rủi ro cao hơn một dòng [CẦN] rõ ràng).
        surv_hyp_interp = interpret_hypothesis_type({"outcome_type": "survival"},
                                                     hypothesis_type, hypothesis_margin)
        surv_txt = format_survival_text(surv, km, surv_hyp_interp)
        (prefix.parent / f"{args.gate}_table3_survival.txt").write_text(surv_txt, encoding="utf-8")
        summary["survival"] = surv
        summary["kaplan_meier"] = km
        if surv_hyp_interp.get("note"):
            summary["survival_hypothesis_interpretation"] = surv_hyp_interp
        if "crude" in surv:
            c = surv["crude"]
            print(f"✓ Cox PH thô: HR={c['HR']} (95%CI {c['CI_95'][0]}–{c['CI_95'][1]}), p={c['p']}")
        elif "error" in surv:
            print(f"✗ Cox PH: {surv['error']}")

        r_script_surv = _generate_r_script_survival(
            args.study, args.gate, args.time, args.event, args.group, covariates)
        (prefix.parent / f"{args.gate}_survival_syntax.R").write_text(r_script_surv, encoding="utf-8")
        print("✓ Script R (sống còn) tái lặp đã tạo")

    # 8. JSON summary (cho agent)
    json_path = prefix.parent / f"{args.gate}_analysis_summary.json"
    json_path.write_text(json.dumps(_json_safe(summary), ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n{'='*60}")
    print(f"✅ HOÀN THÀNH — Đầu ra tại: {out_dir}/")
    print(f"   Dùng cho viet-ban-thao: {args.gate}_analysis_summary.json")
    print("\nCần bác sĩ kiểm chứng.")
    return summary


if __name__ == "__main__":
    main()
