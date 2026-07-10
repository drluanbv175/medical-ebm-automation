#!/usr/bin/env python3
"""app_data_analysis.py — Giao diện phân tích thống kê thật (Streamlit).
Chạy: streamlit run tools/app_data_analysis.py
"""
import io
import json
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from scipy import stats

warnings.filterwarnings("ignore")

BASE = Path(__file__).resolve().parent.parent

# ─────────────────────────── CẤU HÌNH ────────────────────────────
st.set_page_config(
    page_title="EBM Copilot — Phân tích thống kê",
    page_icon="📊", layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── PII SCAN ────────────────────────────
PII_COL_KEYWORDS = ["tên","name","họ","address","địa chỉ","phone","điện thoại",
    "email","cmnd","cccd","dob","ngày sinh","birthday","passport","mã bệnh nhân",
    "patient_id","pid","medical_record","mã hn","số hn"]
PII_VALUE_PATTERNS = [
    (r'\b0[3-9]\d{8}\b', "Số điện thoại VN"),
    (r'\b\d{9}\b|\b\d{12}\b', "CMND/CCCD"),
    (r'\b(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[0-2])[-/](19|20)\d{2}\b', "Ngày sinh"),
    (r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', "Email"),
    (r'\b(Nguyễn|Trần|Lê|Phạm|Hoàng|Phan|Vũ|Đặng|Bùi|Đỗ|Hồ|Ngô|Dương)\s+[A-ZĐÁÉÍÓÚÀÈÌÒÙÂÊÔĂẠẶẬ]', "Họ tên VN"),
]

def scan_pii(df):
    issues = []
    for col in df.columns:
        if any(k in col.lower() for k in PII_COL_KEYWORDS):
            issues.append(f"Tên cột nghi PII: **{col}**")
    for col in df.select_dtypes(include="object").columns:
        sample = df[col].dropna().astype(str).head(50)
        for pat, label in PII_VALUE_PATTERNS:
            if sample.str.contains(pat, regex=True).any():
                issues.append(f"Cột **{col}**: phát hiện dạng {label}")
                break
    return issues

# ─────────────────────────── TABLE 1 ────────────────────────────
def table1(df, group_col=None, cont_cols=None, cat_cols=None):
    rows = []
    if cont_cols is None:
        cont_cols = [c for c in df.select_dtypes(include=np.number).columns if c != group_col]
    if cat_cols is None:
        cat_cols = [c for c in df.select_dtypes(include=["object","category"]).columns if c != group_col]

    if group_col and group_col in df.columns:
        groups = df[group_col].dropna().unique()
        cols_hdr = ["Biến"] + [f"{group_col}={g}" for g in groups] + ["p-value"]
    else:
        groups = None
        cols_hdr = ["Biến", "Tổng (N={})".format(len(df))]

    for col in cont_cols:
        if col not in df.columns: continue
        row = [f"**{col}** (TB±SD)"]
        if groups is not None:
            vals_list = [df[df[group_col]==g][col].dropna() for g in groups]
            row += [f"{v.mean():.2f}±{v.std():.2f}" for v in vals_list]
            try:
                if len(groups) == 2:
                    _, p = stats.ttest_ind(*vals_list, equal_var=False)
                else:
                    _, p = stats.f_oneway(*vals_list)
                row.append(f"{p:.3f}")
            except ValueError: row.append("—")
        else:
            v = df[col].dropna()
            row.append(f"{v.mean():.2f}±{v.std():.2f}")
        rows.append(row)

    for col in cat_cols:
        if col not in df.columns: continue
        row = [f"**{col}** n(%)"]
        vals = df[col].dropna()
        if groups is not None:
            row += ["—" for _ in groups]
            # chi-square
            try:
                ct = pd.crosstab(df[group_col], df[col])
                _, p, _, _ = stats.chi2_contingency(ct)
                row.append(f"{p:.3f}")
            except ValueError: row.append("—")
        else:
            row.append(f"{len(vals)} ({100*len(vals)/len(df):.1f}%)")
        rows.append(row)

    return pd.DataFrame(rows, columns=cols_hdr[:len(rows[0])] if rows else cols_hdr)

# ─────────────────────────── PHÂN TÍCH ────────────────────────────
def run_cohort(df, exposure, outcome, time_col, covariates):
    results = {}
    # KM curve via lifelines
    try:
        from lifelines import CoxPHFitter, KaplanMeierFitter
        dff = df[[exposure, outcome, time_col] + covariates].dropna()
        # KM
        km_data = {}
        for grp in dff[exposure].unique():
            sub = dff[dff[exposure] == grp]
            kmf = KaplanMeierFitter()
            kmf.fit(sub[time_col], sub[outcome], label=str(grp))
            km_data[str(grp)] = {"timeline": kmf.timeline.tolist(),
                                  "surv":     kmf.survival_function_.values.flatten().tolist(),
                                  "ci_lower": kmf.confidence_interval_.iloc[:,0].tolist(),
                                  "ci_upper": kmf.confidence_interval_.iloc[:,1].tolist()}
        results["km"] = km_data
        results["km_available"] = True
        # Cox
        cox_df = dff.copy()
        cox_df[time_col] = pd.to_numeric(cox_df[time_col])
        cox_df[outcome]  = pd.to_numeric(cox_df[outcome])
        cph = CoxPHFitter()
        cox_vars = [exposure] + covariates
        cph.fit(cox_df[[time_col, outcome] + cox_vars], time_col, outcome)
        s = cph.summary
        results["cox"] = {
            "hr":   np.exp(s["coef"]).to_dict(),
            "lower":np.exp(s["coef lower 95%"]).to_dict(),
            "upper":np.exp(s["coef upper 95%"]).to_dict(),
            "p":    s["p"].to_dict(),
        }
        results["cox_available"] = True
    except Exception as e:
        results["cox_available"] = False
        results["km_available"] = False
        results["error"] = str(e)
    return results

def run_logistic(df, exposure, outcome, covariates):
    import statsmodels.formula.api as smf
    results = {}
    dff = df[[exposure, outcome] + covariates].dropna()
    try:
        formula = f"{outcome} ~ {exposure}" + (f" + {' + '.join(covariates)}" if covariates else "")
        model = smf.logit(formula, data=dff).fit(disp=0)
        results["coef"]  = np.exp(model.params).to_dict()
        results["lower"] = np.exp(model.conf_int()[0]).to_dict()
        results["upper"] = np.exp(model.conf_int()[1]).to_dict()
        results["p"]     = model.pvalues.to_dict()
        results["n"]     = len(dff)
        results["available"] = True
    except Exception as e:
        results["available"] = False
        results["error"] = str(e)
    return results

def run_linear(df, outcome, predictors):
    import statsmodels.formula.api as smf
    results = {}
    try:
        formula = f"{outcome} ~ {' + '.join(predictors)}"
        model = smf.ols(formula, data=df[predictors+[outcome]].dropna()).fit()
        results["coef"]  = model.params.to_dict()
        results["lower"] = model.conf_int()[0].to_dict()
        results["upper"] = model.conf_int()[1].to_dict()
        results["p"]     = model.pvalues.to_dict()
        results["r2"]    = round(model.rsquared, 4)
        results["n"]     = int(model.nobs)
        results["available"] = True
    except Exception as e:
        results["available"] = False
        results["error"] = str(e)
    return results

def run_roc(df, test_col, reference_col):
    from sklearn.metrics import auc, roc_auc_score, roc_curve
    results = {}
    try:
        dff = df[[test_col, reference_col]].dropna()
        y = pd.to_numeric(dff[reference_col], errors="coerce")
        score = pd.to_numeric(dff[test_col], errors="coerce")
        dff2 = pd.DataFrame({"y": y, "score": score}).dropna()
        fpr, tpr, thresholds = roc_curve(dff2["y"], dff2["score"])
        auc_val = auc(fpr, tpr)
        # 95%CI via DeLong approximation (scipy bootstrap)
        boot_aucs = []
        rng = np.random.default_rng(42)
        for _ in range(1000):
            idx = rng.integers(0, len(dff2), len(dff2))
            try:
                boot_aucs.append(roc_auc_score(dff2["y"].iloc[idx], dff2["score"].iloc[idx]))
            except ValueError: pass  # mẫu bootstrap chỉ có 1 lớp — AUC không xác định, bỏ qua lần này
        ci_lo, ci_hi = np.percentile(boot_aucs, [2.5, 97.5])
        # Best cutoff (Youden)
        youden = tpr - fpr
        best_idx = np.argmax(youden)
        best_thresh = thresholds[best_idx]
        pred = (dff2["score"] >= best_thresh).astype(int)
        sens = float(((pred==1) & (dff2["y"]==1)).sum() / (dff2["y"]==1).sum())
        spec = float(((pred==0) & (dff2["y"]==0)).sum() / (dff2["y"]==0).sum())
        ppv  = float(((pred==1) & (dff2["y"]==1)).sum() / (pred==1).sum()) if (pred==1).sum() else 0
        npv  = float(((pred==0) & (dff2["y"]==0)).sum() / (pred==0).sum()) if (pred==0).sum() else 0
        results.update({"fpr":fpr.tolist(),"tpr":tpr.tolist(),"auc":round(auc_val,4),
            "ci_lo":round(ci_lo,4),"ci_hi":round(ci_hi,4),
            "best_cutoff":round(float(best_thresh),4),
            "sensitivity":round(sens,4),"specificity":round(spec,4),
            "ppv":round(ppv,4),"npv":round(npv,4),"n":len(dff2),"available":True})
    except Exception as e:
        results["available"] = False
        results["error"] = str(e)
    return results

def run_meta(df, effect_col, se_col, study_col, ci_lower_col=None, ci_upper_col=None, sm="OR"):
    results = {}
    try:
        dff = df[[effect_col, study_col]].copy()
        if se_col and se_col in df.columns:
            dff["se"] = pd.to_numeric(df[se_col], errors="coerce")
        elif ci_lower_col and ci_upper_col and ci_lower_col in df.columns:
            lo = pd.to_numeric(df[ci_lower_col], errors="coerce")
            hi = pd.to_numeric(df[ci_upper_col], errors="coerce")
            dff["se"] = (np.log(hi) - np.log(lo)) / (2*1.96) if sm in ["OR","HR","RR"] else (hi-lo)/(2*1.96)
        else:
            results["available"] = False
            results["error"] = "Cần cột SE hoặc CI lower/upper"
            return results
        dff["effect"] = pd.to_numeric(df[effect_col], errors="coerce")
        dff = dff.dropna()
        log_e = np.log(dff["effect"]) if sm in ["OR","HR","RR"] else dff["effect"]
        se    = dff["se"].values
        # Random effects (DerSimonian-Laird)
        w = 1/se**2
        fe_est = np.sum(w*log_e) / np.sum(w)
        Q = np.sum(w*(log_e-fe_est)**2)
        df_Q = len(dff)-1
        tau2 = max(0, (Q-df_Q)/(np.sum(w)-np.sum(w**2)/np.sum(w)))
        w_re = 1/(se**2 + tau2)
        re_est = np.sum(w_re*log_e) / np.sum(w_re)
        re_se = np.sqrt(1/np.sum(w_re))
        z = stats.norm.ppf(0.975)
        re_lo, re_hi = re_est - z*re_se, re_est + z*re_se
        if sm in ["OR","HR","RR"]:
            re_est, re_lo, re_hi = np.exp(re_est), np.exp(re_lo), np.exp(re_hi)
            per_eff = np.exp(log_e).tolist()
        else:
            per_eff = log_e.tolist()
        I2 = max(0, 100*(Q-df_Q)/Q) if Q>0 else 0
        results.update({
            "pooled":round(float(re_est),4), "lo":round(float(re_lo),4), "hi":round(float(re_hi),4),
            "I2":round(I2,1), "Q":round(float(Q),3), "p_Q":round(float(1-stats.chi2.cdf(Q,df_Q)),4),
            "tau2":round(float(tau2),4), "n_studies":len(dff),
            "studies":dff[study_col].tolist(),
            "per_effect":per_eff,
            "per_lo": np.exp(log_e-z*se).tolist() if sm in ["OR","HR","RR"] else (log_e-z*se).tolist(),
            "per_hi": np.exp(log_e+z*se).tolist() if sm in ["OR","HR","RR"] else (log_e+z*se).tolist(),
            "sm":sm,"available":True})
    except Exception as e:
        results["available"] = False
        results["error"] = str(e)
    return results

# ─────────────────────────── BIỂU ĐỒ ────────────────────────────
def plot_km(km_data):
    fig = go.Figure()
    colors = px.colors.qualitative.Set2
    for i,(grp, d) in enumerate(km_data.items()):
        c = colors[i % len(colors)]
        fig.add_trace(go.Scatter(x=d["timeline"]+d["timeline"][::-1],
            y=d["ci_upper"]+d["ci_lower"][::-1],
            fill="toself", fillcolor=c, opacity=0.2, line=dict(color="rgba(0,0,0,0)"),
            showlegend=False, hoverinfo="skip"))
        fig.add_trace(go.Scatter(x=d["timeline"], y=d["surv"], name=f"Nhóm {grp}",
            mode="lines", line=dict(color=c, width=2.5), hovertemplate="t=%{x}<br>S(t)=%{y:.3f}"))
    fig.update_layout(title="Đường cong Kaplan-Meier", xaxis_title="Thời gian",
        yaxis_title="Xác suất sống còn không biến cố",
        yaxis_range=[0,1.05], hovermode="x unified",
        legend=dict(x=0.7, y=0.95), height=420)
    return fig

def plot_roc(roc_res):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0,1], y=[0,1], mode="lines",
        line=dict(dash="dash", color="grey"), name="Ngẫu nhiên"))
    fig.add_trace(go.Scatter(x=roc_res["fpr"], y=roc_res["tpr"], mode="lines",
        fill="tozeroy", fillcolor="rgba(70,130,180,0.15)",
        line=dict(color="steelblue", width=2.5),
        name=f"AUC = {roc_res['auc']} (95%CI {roc_res['ci_lo']}–{roc_res['ci_hi']})"))
    fig.update_layout(title="Đường cong ROC", xaxis_title="1 - Độ đặc hiệu (FPR)",
        yaxis_title="Độ nhạy (TPR)", yaxis_range=[0,1.05], xaxis_range=[-0.05,1.05],
        height=420)
    return fig

def plot_forest(meta_res):
    studies = meta_res["studies"]
    eff = meta_res["per_effect"]
    lo  = meta_res["per_lo"]
    hi  = meta_res["per_hi"]
    fig = go.Figure()
    for i,(s,e,l,h) in enumerate(zip(studies,eff,lo,hi)):
        fig.add_trace(go.Scatter(x=[l,h], y=[i,i], mode="lines",
            line=dict(color="steelblue",width=2), showlegend=False))
        fig.add_trace(go.Scatter(x=[e], y=[i], mode="markers",
            marker=dict(size=10,color="steelblue"), name=s, showlegend=False,
            hovertemplate=f"{s}: {e:.3f} [{l:.3f}–{h:.3f}]"))
    n = len(studies)
    fig.add_vline(x=meta_res["pooled"], line_dash="solid", line_color="red", line_width=2)
    fig.add_vline(x=1 if meta_res["sm"] in ["OR","HR","RR"] else 0, line_dash="dash", line_color="grey")
    fig.add_shape(type="rect",
        x0=meta_res["lo"], x1=meta_res["hi"], y0=n-0.3, y1=n+0.3,
        fillcolor="red", opacity=0.4, line_width=0)
    fig.update_layout(title=f"Forest Plot — Pooled {meta_res['sm']}={meta_res['pooled']} "
        f"(95%CI {meta_res['lo']}–{meta_res['hi']}), I²={meta_res['I2']}%",
        xaxis_title=meta_res["sm"],
        yaxis=dict(tickvals=list(range(n+1)),
                   ticktext=studies+["<b>Pooled (RE)</b>"],
                   autorange="reversed"),
        height=max(300, 80*(n+2)))
    return fig

def plot_regression(res, exposure, is_or=True):
    coefs = {k:v for k,v in res["coef"].items() if k!="Intercept"}
    lo    = {k:v for k,v in res["lower"].items() if k!="Intercept"}
    hi    = {k:v for k,v in res["upper"].items() if k!="Intercept"}
    pvals = {k:v for k,v in res["p"].items() if k!="Intercept"}
    names = list(coefs.keys())
    vals  = [coefs[n] for n in names]
    lows  = [lo[n]    for n in names]
    highs = [hi[n]    for n in names]
    colors= ["red" if pvals[n]<0.05 else "steelblue" for n in names]
    fig = go.Figure()
    for i,(n,v,l,h,c) in enumerate(zip(names,vals,lows,highs,colors)):
        fig.add_trace(go.Scatter(x=[l,h], y=[i,i], mode="lines",
            line=dict(color=c,width=2), showlegend=False))
        fig.add_trace(go.Scatter(x=[v], y=[i], mode="markers",
            marker=dict(size=10,color=c), name=n, showlegend=False,
            hovertemplate=f"{n}={'OR' if is_or else 'Beta'}={v:.3f} [{l:.3f}–{h:.3f}], p={pvals[n]:.3f}"))
    fig.add_vline(x=1 if is_or else 0, line_dash="dash", line_color="grey")
    fig.update_layout(title="Biểu đồ hệ số hồi quy (với 95%CI)",
        xaxis_title="OR (95%CI)" if is_or else "Beta (95%CI)",
        yaxis=dict(tickvals=list(range(len(names))), ticktext=names, autorange="reversed"),
        height=max(300, 60*len(names)))
    return fig

# ─────────────────────────── XUẤT DOCX ────────────────────────────
def export_docx(study, design, tab1_df, analysis_res):
    from docx import Document
    doc = Document()
    doc.add_heading(f"Kết quả phân tích — {study}", 0)
    doc.add_paragraph(f"Thiết kế: {design} | Ngày phân tích: {pd.Timestamp.today().date()}")
    doc.add_paragraph("⚠ Cần bác sĩ kiểm chứng toàn bộ kết quả trước khi sử dụng.")
    # Table 1
    doc.add_heading("Bảng 1 — Đặc điểm nền", 1)
    if tab1_df is not None and len(tab1_df) > 0:
        t = doc.add_table(rows=1+len(tab1_df), cols=len(tab1_df.columns))
        t.style = "Light Shading Accent 1"
        for j,col in enumerate(tab1_df.columns):
            t.rows[0].cells[j].text = col
        for i,row in tab1_df.iterrows():
            for j,val in enumerate(row):
                t.rows[i+1].cells[j].text = str(val)
    # Kết quả chính
    doc.add_heading("Bảng 2 — Kết quả phân tích chính", 1)
    if analysis_res and analysis_res.get("available"):
        if "cox" in analysis_res and analysis_res["cox_available"]:
            doc.add_paragraph("Cox Proportional Hazards:")
            for var,hr in analysis_res["cox"]["hr"].items():
                lo = analysis_res["cox"]["lower"][var]
                hi = analysis_res["cox"]["upper"][var]
                p  = analysis_res["cox"]["p"][var]
                doc.add_paragraph(f"  {var}: HR = {hr:.3f} (95%CI {lo:.3f}–{hi:.3f}), p = {p:.3f}")
        elif "coef" in analysis_res:
            for var,val in analysis_res["coef"].items():
                if var == "Intercept": continue
                lo = analysis_res["lower"][var]
                hi = analysis_res["upper"][var]
                p  = analysis_res["p"][var]
                doc.add_paragraph(f"  {var}: OR/Beta = {val:.3f} (95%CI {lo:.3f}–{hi:.3f}), p = {p:.3f}")
        elif "auc" in analysis_res:
            doc.add_paragraph(f"  AUC = {analysis_res['auc']} (95%CI {analysis_res['ci_lo']}–{analysis_res['ci_hi']})")
            doc.add_paragraph(f"  Ngưỡng tối ưu (Youden): {analysis_res['best_cutoff']}")
            doc.add_paragraph(f"  Độ nhạy: {analysis_res['sensitivity']*100:.1f}% | Độ đặc hiệu: {analysis_res['specificity']*100:.1f}%")
        elif "pooled" in analysis_res:
            sm = analysis_res["sm"]
            doc.add_paragraph(f"  Pooled {sm} = {analysis_res['pooled']} (95%CI {analysis_res['lo']}–{analysis_res['hi']})")
            doc.add_paragraph(f"  I² = {analysis_res['I2']}% | Q-test p = {analysis_res['p_Q']}")
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# ─────────────────────────── SIDEBAR ────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/stethoscope.png", width=60)
    st.title("EBM Copilot\nPhân tích thống kê")
    st.markdown("---")
    # Chọn đề tài
    exports_dir = BASE / "exports"
    studies = [d.name for d in exports_dir.iterdir() if d.is_dir()] if exports_dir.exists() else []
    study = st.selectbox("📁 Đề tài (từ G0-G5)", ["-- Chọn --"] + sorted(studies))
    if study != "-- Chọn --":
        cp_path = exports_dir / study / "G1_checkpoint.json"
        design_code = "cohort"
        if cp_path.exists():
            with open(cp_path) as f:
                cp = json.load(f)
            design_code = cp.get("design_code", "cohort")
        st.info(f"Thiết kế: **{design_code}**")
    else:
        design_code = "cohort"
    st.markdown("---")
    # Upload file
    st.subheader("📤 Tải dữ liệu (đã ẩn danh)")
    uploaded = st.file_uploader("CSV hoặc Excel", type=["csv","xlsx","xls"])
    st.caption("⚠ Chỉ upload dữ liệu ĐÃ ẨN DANH (không CMND, tên, địa chỉ)")
    st.markdown("---")
    st.caption("*Cần bác sĩ kiểm chứng*")

# ─────────────────────────── MAIN ────────────────────────────
if uploaded is None:
    st.markdown("""
    ## 👋 Chào mừng đến với EBM Copilot — Phân tích Thống kê

    ### Cách dùng:
    1. **Chọn đề tài** từ sidebar (đã chạy G0-G5)
    2. **Upload dữ liệu** CSV/Excel — dữ liệu PHẢI đã ẩn danh trước
    3. **Kiểm tra PII** — hệ thống tự quét và cảnh báo
    4. **Ánh xạ biến** — chỉ định cột nào là exposure/outcome/covariate
    5. **Chạy phân tích** — nhận kết quả thật với 95%CI
    6. **Xuất DOCX** — bảng kết quả sẵn sàng cho bản thảo G7

    ### Loại thiết kế hỗ trợ:
    | Thiết kế | Phân tích | Biểu đồ |
    |---|---|---|
    | Cohort | Cox regression (HR) | Kaplan-Meier |
    | RCT | Logistic/Linear | Forest plot nhóm |
    | Cắt ngang | Logistic regression (OR) | Coefficients plot |
    | Chẩn đoán | ROC/AUC + Se/Sp | ROC curve |
    | SR/MA | Random-effects meta | Forest plot |

    > **Bảo mật:** Không kết nối HIS/EMR/eHospital. Không lưu dữ liệu lên cloud.
    > Mọi tính toán chạy 100% trên máy cục bộ.
    """)
    st.stop()

# Đọc dữ liệu
try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
    st.success(f"✅ Đọc file: **{uploaded.name}** — {len(df)} dòng × {len(df.columns)} cột")
except Exception as e:
    st.error(f"❌ Không đọc được file: {e}")
    st.stop()

# PII scan
pii_issues = scan_pii(df)
if pii_issues:
    st.error("🔴 PHÁT HIỆN PII — Không được phân tích trước khi ẩn danh hoàn toàn!")
    for issue in pii_issues:
        st.warning(f"• {issue}")
    st.info("Xóa/hash các cột PII rồi upload lại. Không ghi ID bệnh nhân thật.")
    if not st.checkbox("⚠ Tôi xác nhận dữ liệu này không có PII thật (chỉ ID nghiên cứu mã hóa)"):
        st.stop()

# TABS
tab_data, tab_t1, tab_main, tab_plot, tab_export = st.tabs([
    "📋 Dữ liệu", "📊 Bảng 1", "🔬 Phân tích chính", "📈 Biểu đồ", "📄 Xuất DOCX"
])

# ─── Tab: Dữ liệu ───
with tab_data:
    st.subheader(f"Dữ liệu: {len(df)} dòng × {len(df.columns)} cột")
    st.dataframe(df.head(20), use_container_width=True)
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Kiểu dữ liệu:**")
        dtype_df = pd.DataFrame({"Cột":df.columns,"Kiểu":df.dtypes.astype(str),"Thiếu (%)":df.isnull().mean().round(3)*100})
        st.dataframe(dtype_df, use_container_width=True)
    with col2:
        st.write("**Thống kê mô tả:**")
        st.dataframe(df.describe().round(3), use_container_width=True)

# ─── Tab: Bảng 1 ───
with tab_t1:
    st.subheader("Bảng 1 — Đặc điểm nền")
    cols = list(df.columns)
    group_col = st.selectbox("Biến nhóm (strata)", ["-- Không phân nhóm --"] + cols)
    if group_col == "-- Không phân nhóm --": group_col = None
    num_cols  = st.multiselect("Biến liên tục (TB±SD)", df.select_dtypes(np.number).columns.tolist(),
                               default=df.select_dtypes(np.number).columns.tolist()[:5])
    cat_cols  = st.multiselect("Biến phân loại (n,%)",  df.select_dtypes(["object","category"]).columns.tolist(),
                               default=df.select_dtypes(["object","category"]).columns.tolist()[:3])
    if st.button("Tạo Bảng 1"):
        with st.spinner("Đang tạo Bảng 1..."):
            t1 = table1(df, group_col, num_cols, cat_cols)
            st.dataframe(t1, use_container_width=True)
            st.session_state["tab1_df"] = t1
            if group_col:
                st.caption("p-value: t-test/ANOVA (biến liên tục), Chi-square (biến phân loại)")

# ─── Tab: Phân tích chính ───
with tab_main:
    st.subheader("Phân tích chính")
    cols = list(df.columns)
    design_sel = st.selectbox("Thiết kế", ["cohort","rct","cross_sectional","diagnostic","sr_ma"],
                              index=["cohort","rct","cross_sectional","diagnostic","sr_ma"].index(design_code) if design_code in ["cohort","rct","cross_sectional","diagnostic","sr_ma"] else 0)
    st.markdown("---")

    analysis_res = None

    if design_sel in ["cohort"]:
        st.write("**Cox Proportional Hazards + Kaplan-Meier**")
        c1, c2, c3 = st.columns(3)
        exposure   = c1.selectbox("Phơi nhiễm (biến nhóm)", cols)
        outcome    = c2.selectbox("Biến cố (0/1)", cols)
        time_col   = c3.selectbox("Thời gian theo dõi", cols)
        covariates = st.multiselect("Covariates (điều chỉnh)", [c for c in cols if c not in [exposure,outcome,time_col]])
        if st.button("🔬 Chạy Cox regression"):
            with st.spinner("Đang chạy Cox regression..."):
                analysis_res = run_cohort(df, exposure, outcome, time_col, covariates)
                st.session_state["analysis_res"] = analysis_res
                st.session_state["design_sel"] = design_sel
                if analysis_res.get("cox_available"):
                    cox = analysis_res["cox"]
                    tbl = pd.DataFrame({"HR": cox["hr"], "95%CI Lo": cox["lower"],
                                        "95%CI Hi": cox["upper"], "p": cox["p"]}).round(4)
                    st.success("✅ Cox regression hoàn tất")
                    st.dataframe(tbl, use_container_width=True)
                    st.caption("Đơn vị: HR (hazard ratio); p-value Wald test")
                else:
                    st.error(f"Lỗi: {analysis_res.get('error')}")

    elif design_sel in ["rct","cross_sectional"]:
        st.write("**Logistic Regression (OR) hoặc Linear Regression (Beta)**")
        c1, c2 = st.columns(2)
        exposure  = c1.selectbox("Biến phơi nhiễm/can thiệp", cols)
        outcome   = c2.selectbox("Biến kết cục", cols)
        covariates = st.multiselect("Covariates", [c for c in cols if c not in [exposure,outcome]])
        outcome_type = st.radio("Loại kết cục", ["Nhị phân (0/1) → OR", "Liên tục → Beta"])
        if st.button("🔬 Chạy hồi quy"):
            with st.spinner("Đang phân tích..."):
                if "Nhị phân" in outcome_type:
                    analysis_res = run_logistic(df, exposure, outcome, covariates)
                    is_or = True
                else:
                    analysis_res = run_linear(df, outcome, [exposure]+covariates)
                    is_or = False
                st.session_state["analysis_res"] = analysis_res
                st.session_state["is_or"] = is_or
                st.session_state["design_sel"] = design_sel
                if analysis_res.get("available"):
                    tbl = pd.DataFrame({
                        "OR/Beta": analysis_res["coef"],
                        "95%CI Lo": analysis_res["lower"],
                        "95%CI Hi": analysis_res["upper"],
                        "p": analysis_res["p"]}).round(4)
                    st.success(f"✅ N={analysis_res.get('n','?')}" + (f" | R²={analysis_res.get('r2','?')}" if not is_or else ""))
                    st.dataframe(tbl.drop(index=["Intercept"],errors="ignore"), use_container_width=True)
                else:
                    st.error(f"Lỗi: {analysis_res.get('error')}")

    elif design_sel == "diagnostic":
        st.write("**Chẩn đoán: ROC/AUC + Độ nhạy/Độ đặc hiệu**")
        c1, c2 = st.columns(2)
        test_col = c1.selectbox("Kết quả test chỉ số (score/giá trị)", cols)
        ref_col  = c2.selectbox("Tiêu chuẩn vàng (0/1)", cols)
        if st.button("🔬 Tính ROC/AUC"):
            with st.spinner("Đang tính..."):
                analysis_res = run_roc(df, test_col, ref_col)
                st.session_state["analysis_res"] = analysis_res
                st.session_state["design_sel"] = design_sel
                if analysis_res.get("available"):
                    r = analysis_res
                    col1,col2,col3,col4 = st.columns(4)
                    col1.metric("AUC", f"{r['auc']}", f"95%CI {r['ci_lo']}–{r['ci_hi']}")
                    col2.metric("Độ nhạy", f"{r['sensitivity']*100:.1f}%", f"cutoff={r['best_cutoff']}")
                    col3.metric("Độ đặc hiệu", f"{r['specificity']*100:.1f}%")
                    col4.metric("PPV / NPV", f"{r['ppv']*100:.1f}% / {r['npv']*100:.1f}%")
                    st.caption(f"N={r['n']} | Ngưỡng Youden tối ưu: {r['best_cutoff']} | CI 1000-bootstrap")
                else:
                    st.error(f"Lỗi: {analysis_res.get('error')}")

    elif design_sel == "sr_ma":
        st.write("**Meta-analysis (Random-effects DerSimonian-Laird)**")
        c1, c2, c3 = st.columns(3)
        study_col  = c1.selectbox("Cột tên nghiên cứu", cols)
        effect_col = c2.selectbox("Cột hiệu ứng (OR/HR/RR/MD)", cols)
        sm         = c3.selectbox("Loại hiệu ứng", ["OR","HR","RR","MD","SMD"])
        c4, c5 = st.columns(2)
        se_col = c4.selectbox("SE (nếu có)", ["-- Không có --"]+cols)
        ci_lo_col = c5.selectbox("CI lower (nếu không có SE)", ["-- Không có --"]+cols)
        ci_hi_col = st.selectbox("CI upper", ["-- Không có --"]+cols)
        if st.button("🔬 Chạy meta-analysis"):
            with st.spinner("Đang phân tích gộp..."):
                se = se_col if se_col != "-- Không có --" else None
                lo = ci_lo_col if ci_lo_col != "-- Không có --" else None
                hi = ci_hi_col if ci_hi_col != "-- Không có --" else None
                analysis_res = run_meta(df, effect_col, se, study_col, lo, hi, sm)
                st.session_state["analysis_res"] = analysis_res
                st.session_state["design_sel"] = design_sel
                if analysis_res.get("available"):
                    r = analysis_res
                    col1,col2,col3 = st.columns(3)
                    col1.metric(f"Pooled {sm}", f"{r['pooled']}", f"95%CI {r['lo']}–{r['hi']}")
                    col2.metric("I²", f"{r['I2']}%")
                    col3.metric("N nghiên cứu", r["n_studies"])
                    st.caption(f"Q={r['Q']}, p={r['p_Q']} | τ²={r['tau2']}")
                else:
                    st.error(f"Lỗi: {analysis_res.get('error')}")

# ─── Tab: Biểu đồ ───
with tab_plot:
    st.subheader("Biểu đồ")
    res = st.session_state.get("analysis_res")
    des = st.session_state.get("design_sel", design_code)
    if res is None:
        st.info("Chạy phân tích chính trước để xem biểu đồ.")
    elif des == "cohort" and res.get("km_available"):
        st.plotly_chart(plot_km(res["km"]), use_container_width=True)
        if res.get("cox_available"):
            cph_df = pd.DataFrame({"HR":res["cox"]["hr"],"lo":res["cox"]["lower"],"hi":res["cox"]["upper"],"p":res["cox"]["p"]})
            cph_df = cph_df.reset_index().rename(columns={"index":"biến"})
            fig2 = go.Figure()
            for _,row in cph_df.iterrows():
                c = "red" if row["p"]<0.05 else "steelblue"
                fig2.add_trace(go.Scatter(x=[row["lo"],row["hi"]], y=[row["biến"],row["biến"]],
                    mode="lines", line=dict(color=c,width=2), showlegend=False))
                fig2.add_trace(go.Scatter(x=[row["HR"]], y=[row["biến"]], mode="markers",
                    marker=dict(size=10,color=c), showlegend=False,
                    hovertemplate=f"{row['biến']}: HR={row['HR']:.3f}, p={row['p']:.3f}"))
            fig2.add_vline(x=1, line_dash="dash", line_color="grey")
            fig2.update_layout(title="Cox HR (95%CI)", xaxis_title="HR",
                yaxis=dict(autorange="reversed"), height=350)
            st.plotly_chart(fig2, use_container_width=True)
    elif des == "diagnostic" and res.get("available"):
        st.plotly_chart(plot_roc(res), use_container_width=True)
    elif des == "sr_ma" and res.get("available"):
        st.plotly_chart(plot_forest(res), use_container_width=True)
    elif des in ["rct","cross_sectional"] and res and res.get("available"):
        is_or = st.session_state.get("is_or", True)
        st.plotly_chart(plot_regression(res, "", is_or), use_container_width=True)

# ─── Tab: Xuất DOCX ───
with tab_export:
    st.subheader("Xuất kết quả sang Word (.docx)")
    res = st.session_state.get("analysis_res")
    t1  = st.session_state.get("tab1_df")
    if res is None:
        st.info("Chạy phân tích chính trước.")
    else:
        study_name = study if study != "-- Chọn --" else "EBM_Study"
        st.write("**Sẽ xuất:**")
        st.write("- Bảng 1 (đặc điểm nền)")
        st.write("- Bảng 2 (kết quả phân tích chính với 95%CI)")
        st.write("- Disclaimer 'Cần bác sĩ kiểm chứng'")
        if st.button("📄 Tạo DOCX"):
            buf = export_docx(study_name, design_sel if 'design_sel' in st.session_state else design_code, t1, res)
            fname = f"G6_RESULTS_{study_name}_{pd.Timestamp.today().date()}.docx"
            st.download_button("⬇ Tải DOCX", data=buf.getvalue(), file_name=fname,
                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            st.success(f"✅ Sẵn sàng tải: {fname}")
            if study != "-- Chọn --":
                save_path = exports_dir / study / fname
                with open(save_path,"wb") as f: f.write(buf.getvalue())
                st.caption(f"Cũng đã lưu vào: {save_path}")
