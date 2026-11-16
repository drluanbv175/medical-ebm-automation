#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phan_tich_thiet_ke_dac_thu.py — phân tích CHÍNH + kiểm chéo SPSS/R cho 4 thiết kế run_stats_analysis chưa có đường.

Vì sao (giả lập trọn vòng 8 thiết kế, bác sĩ 16/11/2026: «nhập vào SPSS và R một cách chi tiết và hoàn thiện»): bộ máy
G6 chỉ có kết cục nhị phân/liên tục/thứ bậc/Poisson/tỷ lệ/sống còn ⇒ đề tài CHẨN ĐOÁN, DỰ BÁO, TỔNG QUAN–GỘP, ĐỊNH TÍNH
qua G6 mà KHÔNG có một con số nào (chay_sap_g6 ghi «không tự động»). Mô-đun này:

  chan_doan  AUC (thống kê Mann–Whitney, KTC Hanley–McNeil) + độ nhạy/độ đặc hiệu/PPV/NPV tại NGƯỠNG SAP (KTC Wilson).
  du_bao     hồi quy logistic: OR từng yếu tố dự báo, C-statistic (AUC của xác suất dự đoán), điểm Brier.
  gop        RR gộp hiệu ứng ngẫu nhiên DerSimonian–Laird + RR hiệu ứng cố định (nghịch đảo phương sai), τ², Q, I²;
             ô 0 ⇒ cộng 0,5 vào cả bốn ô của nghiên cứu đó (cùng quy ước metafor «only0»).
  dinh_tinh  tần suất từng chủ đề đã mã hoá (mô tả — phân tích chủ đề vẫn là việc của nhóm nghiên cứu).

Mỗi lượt: đọc dữ liệu ĐÃ KHOÁ (G5, đúng hàm kiểm khoá của cổng) khi G4 đã khoá → ghi `<gate>_analysis_summary.json`
(ước lượng + đặc tả), `<gate>_ket_qua.md`, và — với `--kiem-cheo` — chạy CÙNG phép tính bằng R (pROC/glm/metafor) và
SPSS (RANK/AGGREGATE/LOGISTIC REGRESSION), so từng đại lượng, ghi `<gate>_kiem_cheo.json/.md`. Cú pháp R/SPSS được lưu
lại trong thư mục đề tài (`r/`, `spss/` — cùng chỗ cầu nối SPSS/R; KHÔNG phải `scripts/` mà dấu vân tay xác nhận G6
tính trên đó) để bác sĩ tự chạy lại trong RStudio/SPSS.

Dùng (thường qua chay_sap_g6 — đặc tả có `loai_dac_thu`):
  python3 tools/phan_tich_thiet_ke_dac_thu.py --study <mã> --gate G6 --loai chan_doan --tham-chieu xo_hoa --chi-so fib4
      --nguong 2.67 [--kiem-cheo]
Mã thoát: 0 xong (kiểm chéo, nếu có, KHOP) · 1 lỗi/lệch · 2 tham số sai/chưa khoá. Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

TOOLS = Path(__file__).resolve().parent
BASE = TOOLS.parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

CAN_KIEM = "Cần bác sĩ kiểm chứng."
Z = 1.959963984540054
LOAI = {
    "chan_doan": ("tham_chieu", "chi_so", "nguong"),
    "du_bao": ("outcome", "covariates"),
    "gop": ("nhan_nghien_cuu", "su_kien_can_thiep", "n_can_thiep", "su_kien_chung", "n_chung"),
    "dinh_tinh": ("chu_de",),
}
SAI_SO = {"mac_dinh": 1e-6, "brier": 1e-5, "or": 1e-4}


class TuChoi(RuntimeError):
    pass


# ─────────────────────────────── tính toán (Python — engine chính) ───────────────────────────────
def wilson(k: float, n: float) -> List[Optional[float]]:
    if not n:
        return [None, None]
    p = k / n
    mau = 1 + Z * Z / n
    tam = (p + Z * Z / (2 * n)) / mau
    nua = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / mau
    return [max(0.0, tam - nua), min(1.0, tam + nua)]


def _hang(x: Sequence[float]) -> List[float]:
    """Hạng trung bình khi trùng (như RANK /TIES=MEAN của SPSS và pROC)."""
    thu_tu = sorted(range(len(x)), key=lambda i: x[i])
    h = [0.0] * len(x)
    i = 0
    while i < len(thu_tu):
        j = i
        while j + 1 < len(thu_tu) and x[thu_tu[j + 1]] == x[thu_tu[i]]:
            j += 1
        for k in range(i, j + 1):
            h[thu_tu[k]] = (i + j) / 2 + 1
        i = j + 1
    return h


def auc_mann_whitney(y: Sequence[int], x: Sequence[float]) -> Dict[str, Any]:
    h = _hang(x)
    n1 = sum(1 for v in y if v == 1)
    n0 = len(y) - n1
    if not n1 or not n0:
        raise TuChoi("AUC cần cả hai nhóm (có bệnh/không bệnh)")
    auc = (sum(hi for hi, v in zip(h, y) if v == 1) - n1 * (n1 + 1) / 2) / (n1 * n0)
    q1, q2 = auc / (2 - auc), 2 * auc * auc / (1 + auc)
    se = math.sqrt(max(0.0, (auc * (1 - auc) + (n1 - 1) * (q1 - auc * auc) + (n0 - 1) * (q2 - auc * auc)) / (n1 * n0)))
    return {"auc": auc, "ci_95": [max(0.0, auc - Z * se), min(1.0, auc + Z * se)], "se_hanley_mcneil": se,
            "n_co_benh": n1, "n_khong_benh": n0}


def chan_doan(hang: List[Dict[str, Any]], tham_chieu: str, chi_so: str, nguong: float) -> Dict[str, Any]:
    y = [int(r[tham_chieu]) for r in hang]
    x = [float(r[chi_so]) for r in hang]
    kq = {"auc": auc_mann_whitney(y, x)}
    tp = sum(1 for a, b in zip(y, x) if a == 1 and b >= nguong)
    fn = sum(1 for a, b in zip(y, x) if a == 1 and b < nguong)
    fp = sum(1 for a, b in zip(y, x) if a == 0 and b >= nguong)
    tn = sum(1 for a, b in zip(y, x) if a == 0 and b < nguong)
    for ten, k, n in (("do_nhay", tp, tp + fn), ("do_dac_hieu", tn, tn + fp), ("ppv", tp, tp + fp),
                      ("npv", tn, tn + fn)):
        kq[ten] = {"uoc_luong": (k / n) if n else None, "ci_95_wilson": wilson(k, n), "k": k, "n": n}
    kq["bang_2x2"] = {"tp": tp, "fp": fp, "fn": fn, "tn": tn, "nguong": nguong}
    se, sp = kq["do_nhay"]["uoc_luong"], kq["do_dac_hieu"]["uoc_luong"]
    kq["lr_duong"] = (se / (1 - sp)) if se is not None and sp not in (None, 1) else None
    kq["lr_am"] = ((1 - se) / sp) if se is not None and sp else None
    return kq


def du_bao(hang: List[Dict[str, Any]], outcome: str, covariates: List[str]) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415
    import statsmodels.api as sm  # noqa: PLC0415

    y = np.array([float(r[outcome]) for r in hang])
    X = sm.add_constant(np.array([[float(r[c]) for c in covariates] for r in hang]), has_constant="add")
    m = sm.Logit(y, X).fit(disp=0, maxiter=200, method="newton", tol=1e-12)
    p = m.predict(X)
    ci = m.conf_int()
    he_so = [{"bien": ten, "beta": float(b), "or": float(math.exp(b)),
              "ci_95": [float(math.exp(lo)), float(math.exp(hi))], "p": float(pv)}
             for ten, b, (lo, hi), pv in zip(["(hằng số)", *covariates], m.params, ci, m.pvalues)]
    c = auc_mann_whitney([int(v) for v in y], [float(v) for v in p])
    return {"he_so": he_so, "c_statistic": c, "brier": float(np.mean((y - p) ** 2)), "n": int(len(y)),
            "n_bien_co": int(y.sum()), "epv": round(float(y.sum()) / max(1, len(covariates)), 2),
            "ghi_chu": "C-statistic trong mẫu (lạc quan); hiệu chỉnh lạc quan bằng bootstrap ở kịch bản R "
                       "(rms::validate)"}


def _o_rr(a: float, n1: float, c: float, n0: float):
    if min(a, c) == 0 or a == n1 or c == n0:
        a, c, n1, n0 = a + 0.5, c + 0.5, n1 + 1, n0 + 1
    return math.log((a / n1) / (c / n0)), 1 / a - 1 / n1 + 1 / c - 1 / n0


def gop(hang: List[Dict[str, Any]], nhan: str, a: str, n1: str, c: str, n0: str) -> Dict[str, Any]:
    tung = []
    for r in hang:
        yi, vi = _o_rr(float(r[a]), float(r[n1]), float(r[c]), float(r[n0]))
        tung.append({"nghien_cuu": str(r[nhan]), "log_rr": yi, "var": vi, "rr": math.exp(yi),
                     "ci_95": [math.exp(yi - Z * math.sqrt(vi)), math.exp(yi + Z * math.sqrt(vi))]})
    k = len(tung)
    if k < 2:
        raise TuChoi("phân tích gộp cần ≥ 2 nghiên cứu")
    w = [1 / t["var"] for t in tung]
    sw = sum(w)
    tb_co_dinh = sum(wi * t["log_rr"] for wi, t in zip(w, tung)) / sw
    q = sum(wi * (t["log_rr"] - tb_co_dinh) ** 2 for wi, t in zip(w, tung))
    tau2 = max(0.0, (q - (k - 1)) / (sw - sum(wi * wi for wi in w) / sw))
    ws = [1 / (t["var"] + tau2) for t in tung]
    sws = sum(ws)
    tb = sum(wi * t["log_rr"] for wi, t in zip(ws, tung)) / sws
    se, se_cd = math.sqrt(1 / sws), math.sqrt(1 / sw)
    for t, wi in zip(tung, ws):
        t["trong_so_ngau_nhien_pct"] = 100 * wi / sws
    return {"rr_gop_ngau_nhien": math.exp(tb), "ci_95": [math.exp(tb - Z * se), math.exp(tb + Z * se)],
            "rr_gop_co_dinh": math.exp(tb_co_dinh), "ci_95_co_dinh": [math.exp(tb_co_dinh - Z * se_cd),
                                                                        math.exp(tb_co_dinh + Z * se_cd)],
            "tau2": tau2, "q": q, "df": k - 1, "i2_pct": (max(0.0, (q - (k - 1)) / q) * 100) if q > 0 else 0.0,
            "k": k, "phuong_phap": "DerSimonian–Laird (ngẫu nhiên) + nghịch đảo phương sai (cố định); RR, log",
            "tung_nghien_cuu": tung}


def dinh_tinh(hang: List[Dict[str, Any]], chu_de: str) -> Dict[str, Any]:
    dem: Dict[str, int] = {}
    for r in hang:
        v = str(r.get(chu_de) or "").strip()
        if v:
            dem[v] = dem.get(v, 0) + 1
    n = sum(dem.values())
    return {"n_ban_go_bang": n, "so_chu_de": len(dem),
            "chu_de": [{"chu_de": k, "n": v, "pct": 100 * v / n, "ty_le": v / n, "ci_95_wilson": wilson(v, n)}
                       for k, v in sorted(dem.items(), key=lambda x: -x[1])],
            "ghi_chu": "Tần suất mô tả các mã đã gán — không thay phân tích chủ đề của nhóm nghiên cứu (COREQ/SRQR)"}


def tinh(loai: str, hang: List[Dict[str, Any]], ts: Dict[str, Any]) -> Dict[str, Any]:
    if loai == "chan_doan":
        return chan_doan(hang, ts["tham_chieu"], ts["chi_so"], float(ts["nguong"]))
    if loai == "du_bao":
        return du_bao(hang, ts["outcome"], list(ts["covariates"]))
    if loai == "gop":
        return gop(hang, ts["nhan_nghien_cuu"], ts["su_kien_can_thiep"], ts["n_can_thiep"], ts["su_kien_chung"],
                   ts["n_chung"])
    return dinh_tinh(hang, ts["chu_de"])


def cac_so_doi_chieu(loai: str, kq: Dict[str, Any]) -> Dict[str, float]:
    """Đại lượng so giữa ba phần mềm (cùng tên khoá với kết quả R/SPSS)."""
    if loai == "chan_doan":
        return {"auc": kq["auc"]["auc"], "do_nhay": kq["do_nhay"]["uoc_luong"],
                "do_dac_hieu": kq["do_dac_hieu"]["uoc_luong"], "tp": kq["bang_2x2"]["tp"], "tn": kq["bang_2x2"]["tn"]}
    if loai == "du_bao":
        return {"c_statistic": kq["c_statistic"]["auc"], "brier": kq["brier"],
                **{f"or_{h['bien']}": h["or"] for h in kq["he_so"][1:]}}
    if loai == "gop":
        return {"rr_gop": kq["rr_gop_ngau_nhien"], "ci_duoi": kq["ci_95"][0], "ci_tren": kq["ci_95"][1],
                "tau2": kq["tau2"], "i2": kq["i2_pct"]}
    return {f"n_{i}": c["n"] for i, c in enumerate(kq["chu_de"])}


# ─────────────────────────────── dữ liệu khoá ───────────────────────────────
def thu_muc_de_tai(study: str) -> Path:
    import run_stats_analysis as RSA  # noqa: PLC0415

    return Path(RSA._thu_muc_de_tai(study))


def doc_du_lieu(study: str, can: Sequence[str], loc: Optional[str] = None) -> tuple[List[Dict[str, Any]], Path, int]:
    """Bộ dữ liệu ĐÃ KHOÁ (G5) — đúng hàm kiểm khoá của cổng; biến PHÁI SINH (vd FIB-4, trường «calc») tính bằng ĐÚNG
    công thức đã duyệt của `_bien-phai-sinh.csv` như run_stats_analysis; giữ ca ĐỦ mọi cột cần (listwise, ghi số bị
    loại). `loc` = biểu thức lọc quần thể (nhóm con/độ nhạy) — ĐÚNG bộ lọc của run_stats_analysis (BPS.loc_python)."""
    import bien_phai_sinh as BPS  # noqa: PLC0415
    import cau_noi_spss as S  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    try:
        csv_khoa, _ = S.tim_du_lieu_khoa(study)
    except Exception as e:  # noqa: BLE001
        raise TuChoi(f"chưa có dữ liệu ĐÃ KHOÁ (G5) dùng được: {e}") from e
    df = pd.read_csv(csv_khoa, encoding="utf-8-sig")
    try:
        cot_loc = BPS.cot_cua_cay(BPS.phan_tich(loc)) if loc else []
        df, _ps = BPS.ap_dung_cho_phan_tich(df, thu_muc_de_tai(study), study, [*can, *cot_loc])
        if loc:
            mat_na, _ngay = BPS.loc_python(df, thu_muc_de_tai(study), study, loc)
            df = df[mat_na.to_numpy()].copy()
            if not len(df):
                raise TuChoi(f"lọc quần thể «{loc}» không còn ca nào")
    except (BPS.TuChoi, BPS.LoiCongThuc) as e:
        raise TuChoi(f"biến phái sinh/lọc — {e}") from e
    thieu = [c for c in can if c not in df.columns]
    if thieu:
        raise TuChoi(f"dữ liệu khoá thiếu cột (không có công thức phái sinh đã duyệt): {', '.join(thieu)}")
    du = df[list(can)].replace("", pd.NA).dropna()
    return du.to_dict("records"), csv_khoa, len(df) - len(du)


def _g4_da_khoa(study: str) -> None:
    import run_stats_analysis as RSA  # noqa: PLC0415

    ok, ly_do = RSA._g4_khoa_song(study)
    if not ok:
        raise TuChoi(f"SAP (G4) chưa khoá — không chạy phân tích chính: {ly_do}")


# ─────────────────────────────── kịch bản R / SPSS ───────────────────────────────
def kich_ban_r(loai: str, ts: Dict[str, Any], csv_p: Path, ra: Path) -> str:
    dau = (f'# R — {loai} (sinh bởi phan_tich_thiet_ke_dac_thu.py; chạy được trong RStudio)\n'
           f'df <- read.csv("{csv_p.as_posix()}", stringsAsFactors = FALSE, check.names = FALSE)\n'
           f'out <- file("{ra.as_posix()}", "w", encoding = "UTF-8")\n'
           'ghi <- function(k, v) writeLines(sprintf("%s=%.15g", k, v), out)\n')
    if loai == "chan_doan":
        y, x, ng = ts["tham_chieu"], ts["chi_so"], float(ts["nguong"])
        than = (f'r <- pROC::roc(df[["{y}"]], df[["{x}"]], levels = c(0, 1), direction = "<", quiet = TRUE)\n'
                'ghi("auc", as.numeric(pROC::auc(r)))\n'
                f'print(pROC::ci.auc(r))  # KTC DeLong (tham khảo)\n'
                f'duong <- df[["{x}"]] >= {ng!r}\n'
                f'ghi("tp", sum(duong & df[["{y}"]] == 1)); ghi("tn", sum(!duong & df[["{y}"]] == 0))\n'
                f'ghi("do_nhay", mean(duong[df[["{y}"]] == 1])); ghi("do_dac_hieu", mean(!duong[df[["{y}"]] == 0]))\n')
    elif loai == "du_bao":
        y, cv = ts["outcome"], list(ts["covariates"])
        than = (f'm <- glm({y} ~ {" + ".join(cv)}, data = df, family = binomial(), '
                'control = glm.control(epsilon = 1e-14, maxit = 200))\n'
                'p <- fitted(m)\n'
                f'ghi("c_statistic", as.numeric(pROC::auc(pROC::roc(df[["{y}"]], p, levels = c(0, 1), direction = "<", '
                'quiet = TRUE))))\n'
                f'ghi("brier", mean((df[["{y}"]] - p)^2))\n'
                + "".join(f'ghi("or_{c}", exp(coef(m)[["{c}"]]))\n' for c in cv)
                + 'print(summary(m)); print(exp(cbind(OR = coef(m), confint.default(m))))\n'
                  '# Hiệu chỉnh lạc quan (bootstrap 200 lần, seed cố định) — C hiệu chỉnh = Dxy/2 + 0.5:\n'
                  f'set.seed(20261115); v <- rms::validate(rms::lrm({y} ~ {" + ".join(cv)}, data = df, x = TRUE, '
                  'y = TRUE), B = 200)\nprint(v)\n')
    elif loai == "gop":
        than = (f'es <- metafor::escalc(measure = "RR", ai = df[["{ts["su_kien_can_thiep"]}"]], '
                f'n1i = df[["{ts["n_can_thiep"]}"]], ci = df[["{ts["su_kien_chung"]}"]], '
                f'n2i = df[["{ts["n_chung"]}"]], '
                f'slab = df[["{ts["nhan_nghien_cuu"]}"]])\n'
                'm <- metafor::rma(yi, vi, data = es, method = "DL")\n'
                'ghi("rr_gop", exp(as.numeric(m$b))); ghi("ci_duoi", exp(m$ci.lb)); ghi("ci_tren", exp(m$ci.ub))\n'
                'ghi("tau2", m$tau2); ghi("i2", m$I2)\nprint(m)\n'
                '# metafor::forest(m, atransf = exp)  # biểu đồ rừng\n')
    else:
        cd = ts["chu_de"]
        than = (f'bang <- sort(table(df[["{cd}"]][df[["{cd}"]] != ""]), decreasing = TRUE)\n'
                'for (i in seq_along(bang)) ghi(sprintf("n_%d", i - 1), as.numeric(bang[[i]]))\nprint(bang)\n')
    return dau + than + "close(out)\n"


def _gia_tri_spss(loai: str, ts: Dict[str, Any]) -> List[tuple[str, str]]:
    if loai == "chan_doan":
        return [(ts["tham_chieu"], "F8.0"), (ts["chi_so"], "F20.10")]
    if loai == "du_bao":
        return [(ts["outcome"], "F8.0"), *[(c, "F20.10") for c in ts["covariates"]]]
    if loai == "gop":
        return [(ts["nhan_nghien_cuu"], "A60"), *[(ts[k], "F20.6") for k in LOAI["gop"][1:]]]
    return [(ts["chu_de"], "A400")]


def kich_ban_spss(loai: str, ts: Dict[str, Any], csv_p: Path, ra: Path) -> str:
    bien = _gia_tri_spss(loai, ts)
    dau = ["* SPSS — " + loai + " (sinh bởi phan_tich_thiet_ke_dac_thu.py; mở và Run trong SPSS).",
           f"GET DATA /TYPE=TXT /FILE='{csv_p}' /ENCODING='UTF8' /DELIMITERS=',' /QUALIFIER='\"' "
           "/ARRANGEMENT=DELIMITED /FIRSTCASE=2",
           "  /VARIABLES=" + " ".join(f"{b} {f}" for b, f in bien) + ".", "DATASET NAME dl."]
    if loai == "chan_doan":
        y, x, ng = ts["tham_chieu"], ts["chi_so"], float(ts["nguong"])
        than = [f"RANK VARIABLES={x} (A) /RANK INTO r_x /TIES=MEAN /PRINT=NO.",
                f"COMPUTE rd = r_x * {y}.", f"COMPUTE duong = ({x} >= {ng!r}).",
                f"COMPUTE tpv = duong * {y}.", f"COMPUTE tnv = (1 - duong) * (1 - {y}).",
                f"AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /n1=SUM({y}) /nn=N({y}) /sr1=SUM(rd) /tp=SUM(tpv) "
                "/tn=SUM(tnv).",
                "COMPUTE n0 = nn - n1.", "COMPUTE auc = (sr1 - n1 * (n1 + 1) / 2) / (n1 * n0).",
                "COMPUTE do_nhay = tp / n1.", "COMPUTE do_dac_hieu = tn / n0.",
                "ROC " + x + " BY " + y + " (1) /PLOT=CURVE(REFERENCE) /PRINT=SE "
                "/CRITERIA=CUTOFF(INCLUDE) TESTPOS(LARGE).",
                "SELECT IF $CASENUM = 1.", "FORMATS auc do_nhay do_dac_hieu tp tn (F24.15).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=auc do_nhay do_dac_hieu tp tn."]
    elif loai == "du_bao":
        y, cv = ts["outcome"], list(ts["covariates"])
        than = [f"LOGISTIC REGRESSION VARIABLES {y} /METHOD=ENTER {' '.join(cv)} /SAVE=PRED(phat) "
                "/CRITERIA=PIN(.05) POUT(.10) ITERATE(200) BCON(0) LCON(0) CUT(.5) /PRINT=CI(95).",
                "RANK VARIABLES=phat (A) /RANK INTO r_p /TIES=MEAN /PRINT=NO.",
                f"COMPUTE rd = r_p * {y}.", f"COMPUTE b2 = ({y} - phat) ** 2.",
                f"AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /n1=SUM({y}) /nn=N({y}) /sr1=SUM(rd) /brier=MEAN(b2).",
                "COMPUTE n0 = nn - n1.", "COMPUTE c_statistic = (sr1 - n1 * (n1 + 1) / 2) / (n1 * n0).",
                "SELECT IF $CASENUM = 1.", "FORMATS c_statistic brier (F24.15).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=c_statistic brier."]
    elif loai == "gop":
        a, n1, c, n0 = (ts[k] for k in LOAI["gop"][1:])
        than = [f"COMPUTE aa = {a}.", f"COMPUTE cc = {c}.", f"COMPUTE m1 = {n1}.", f"COMPUTE m0 = {n0}.",
                "DO IF (MIN(aa, cc) = 0 OR aa = m1 OR cc = m0).",
                "  COMPUTE aa = aa + 0.5.", "  COMPUTE cc = cc + 0.5.",
                "  COMPUTE m1 = m1 + 1.", "  COMPUTE m0 = m0 + 1.",
                "END IF.", "COMPUTE yi = LN((aa / m1) / (cc / m0)).", "COMPUTE vi = 1/aa - 1/m1 + 1/cc - 1/m0.",
                "COMPUTE wi = 1 / vi.", "COMPUTE wy = wi * yi.", "COMPUTE w2 = wi * wi.",
                "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /sw=SUM(wi) /swy=SUM(wy) /sw2=SUM(w2) /k=N(yi).",
                "COMPUTE qi = wi * (yi - swy / sw) ** 2.", "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /q=SUM(qi).",
                "COMPUTE tau2 = MAX(0, (q - (k - 1)) / (sw - sw2 / sw)).", "COMPUTE ws = 1 / (vi + tau2).",
                "COMPUTE wsy = ws * yi.", "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /sws=SUM(ws) /swsy=SUM(wsy).",
                "COMPUTE tb = swsy / sws.", "COMPUTE se = SQRT(1 / sws).", "COMPUTE rr_gop = EXP(tb).",
                f"COMPUTE ci_duoi = EXP(tb - {Z!r} * se).", f"COMPUTE ci_tren = EXP(tb + {Z!r} * se).",
                "COMPUTE i2 = 0.", "IF (q > 0) i2 = MAX(0, (q - (k - 1)) / q) * 100.",
                "SELECT IF $CASENUM = 1.", "FORMATS rr_gop ci_duoi ci_tren tau2 i2 (F24.15).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=rr_gop ci_duoi ci_tren tau2 i2."]
    else:
        cd = ts["chu_de"]
        than = [f"SELECT IF ({cd} <> '').", f"AGGREGATE /OUTFILE=* /BREAK={cd} /n=N.", "SORT CASES BY n (D).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=n."]
    return "\n".join(dau + than) + "\n"


def _doc_kq_r(p: Path) -> Dict[str, float]:
    ra: Dict[str, float] = {}
    for d in p.read_text(encoding="utf-8").splitlines():
        if "=" in d:
            k, v = d.split("=", 1)
            ra[k.strip()] = float(v)
    return ra


def _doc_kq_spss(p: Path, loai: str) -> Dict[str, float]:
    with p.open(encoding="utf-8-sig", newline="") as f:
        dong = list(csv.DictReader(f))
    if loai == "dinh_tinh":
        return {f"n_{i}": float(r["n"]) for i, r in enumerate(dong)}
    return {k.strip(): float(v) for k, v in dong[0].items()}


# SPSS chỉ xuất các đại lượng tính được bằng RANK/AGGREGATE (dự báo: C-statistic + Brier — hai số này đã phụ thuộc mọi
# hệ số của mô hình); R so ĐỦ mọi đại lượng kể cả OR từng yếu tố.
DAI_LUONG_SPSS = {"du_bao": ("c_statistic", "brier")}


def so_khop(py: Dict[str, float], khac: Dict[str, float], chi: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    lech = []
    for k, v in ((k, py[k]) for k in (chi or py)):
        if k not in khac:
            lech.append(f"{k}: thiếu")
            continue
        tol = SAI_SO["brier"] if k == "brier" else SAI_SO["or"] if k.startswith("or_") else SAI_SO["mac_dinh"]
        if abs(float(v) - float(khac[k])) > tol * max(1.0, abs(float(v))):
            lech.append(f"{k}: Python {v:.10g} ≠ {khac[k]:.10g}")
    return {"trang_thai": "KHOP" if not lech else "LECH", "lech": lech, "so_dai_luong": len(chi or py)}


def kiem_cheo(loai: str, ts: Dict[str, Any], hang: List[Dict[str, Any]], d: Path, gate: str,
              py: Dict[str, float]) -> Dict[str, Any]:
    can = [b for b, _ in _gia_tri_spss(loai, ts)]
    tam = Path(tempfile.mkdtemp(prefix="ptdt_"))
    ket: Dict[str, Any] = {}
    try:
        csv_p = tam / "du_lieu.csv"
        with csv_p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(can)
            w.writerows([[r[c] for c in can] for r in hang])
        (d / "r").mkdir(exist_ok=True)  # KHÔNG ghi vào scripts/ — dấu vân tay xác nhận G6 tính trên scripts/
        (d / "spss").mkdir(exist_ok=True)
        # R
        r_ra = tam / "r_kq.txt"
        ma_r = kich_ban_r(loai, ts, csv_p, r_ra)
        (d / "r" / f"{gate}_{loai}.R").write_text(ma_r.replace(csv_p.as_posix(), "<du_lieu_khoa.csv>")
                                                        .replace(r_ra.as_posix(), "<ket_qua.txt>"),
                                                        encoding="utf-8", newline="\n")
        try:
            import cau_noi_r as CR  # noqa: PLC0415

            (tam / "kb.R").write_text(ma_r, encoding="utf-8", newline="\n")
            kq = subprocess.run([str(CR.tim_r()), str(tam / "kb.R")], capture_output=True, text=True, timeout=900,
                                cwd=str(tam), check=False)
            ket["r"] = (so_khop(py, _doc_kq_r(r_ra)) if r_ra.is_file() else
                        {"trang_thai": "LOI", "lech": [(kq.stderr or kq.stdout).strip()[-400:]]})
        except Exception as e:  # noqa: BLE001 — không chạy được R ⇒ KHÔNG ĐO ĐƯỢC, không phải «khớp»
            ket["r"] = {"trang_thai": "KHONG_DO_DUOC", "lech": [f"{type(e).__name__}: {e}"]}
        # SPSS
        try:
            import cau_noi_spss as S  # noqa: PLC0415

            ngan = Path(tempfile.mkdtemp(prefix="ptdt", dir=str(S._goc_tam_ngan())))
            shutil.copy2(csv_p, ngan / "dl.csv")
            sp_ra = ngan / "kq.csv"
            ma_sps = kich_ban_spss(loai, ts, ngan / "dl.csv", sp_ra)
            (ngan / "kb.sps").write_text(ma_sps, encoding="utf-8", newline="\n")
            (d / "spss" / f"{gate}_{loai}.sps").write_text(
                ma_sps.replace(str(ngan / "dl.csv"), "<du_lieu_khoa.csv>").replace(str(sp_ra), "<ket_qua.csv>"),
                encoding="utf-8", newline="\n")
            ma, _out, err = S.chay_spss(S.tim_spss(), ["--cu-phap", str(ngan / "kb.sps")], thu_muc=ngan, thoi_han=900)
            ket["spss"] = (so_khop(py, _doc_kq_spss(sp_ra, loai), DAI_LUONG_SPSS.get(loai)) if sp_ra.is_file() else
                           {"trang_thai": "LOI", "lech": [str(err)[-400:]]})
            shutil.rmtree(ngan, ignore_errors=True)
        except Exception as e:  # noqa: BLE001
            ket["spss"] = {"trang_thai": "KHONG_DO_DUOC", "lech": [f"{type(e).__name__}: {e}"]}
    finally:
        shutil.rmtree(tam, ignore_errors=True)
    tt = [v["trang_thai"] for v in ket.values()]
    tong = "LECH" if "LECH" in tt else "LOI" if "LOI" in tt else "KHOP" if all(t == "KHOP" for t in tt) else \
        "KHONG_DO_DUOC"
    return {"trang_thai": tong, "phan_mem": ket, "dai_luong_python": py}


# ─────────────────────────────── ghi kết quả ───────────────────────────────
def md_ket_qua(study: str, gate: str, loai: str, kq: Dict[str, Any], kc: Optional[Dict[str, Any]]) -> str:
    def so(v, n=3):
        return "—" if v is None else f"{v:.{n}f}".replace(".", ",")

    luc = datetime.now().isoformat(timespec="seconds")
    dl = [f"# Kết quả phân tích {gate} — {study} ({loai})", "",
          f"_Chạy {luc} · dữ liệu đã khoá (G5) · SAP đã khoá (G4)._", ""]
    if loai == "chan_doan":
        a = kq["auc"]
        dl += [f"- AUC = {so(a['auc'])} (KTC 95% {so(a['ci_95'][0])}–{so(a['ci_95'][1])}); có bệnh {a['n_co_benh']}, "
               f"không bệnh {a['n_khong_benh']}", f"- Ngưỡng {kq['bang_2x2']['nguong']}: "]
        for ten, nhan in (("do_nhay", "Độ nhạy"), ("do_dac_hieu", "Độ đặc hiệu"), ("ppv", "PPV"), ("npv", "NPV")):
            x = kq[ten]
            dl.append(f"  - {nhan} = {so(x['uoc_luong'])} ({x['k']}/{x['n']}; KTC 95% Wilson "
                      f"{so(x['ci_95_wilson'][0])}–{so(x['ci_95_wilson'][1])})")
    elif loai == "du_bao":
        c = kq["c_statistic"]
        dl += [f"- C-statistic (trong mẫu) = {so(c['auc'])} (KTC 95% {so(c['ci_95'][0])}–{so(c['ci_95'][1])}); "
               f"Brier = {so(kq['brier'], 4)}; n = {kq['n']}, biến cố = {kq['n_bien_co']}, EPV = {kq['epv']}", "",
               "| Yếu tố | OR | KTC 95% | p |", "|---|---|---|---|"]
        dl += [f"| {h['bien']} | {so(h['or'])} | {so(h['ci_95'][0])}–{so(h['ci_95'][1])} | {so(h['p'], 4)} |"
               for h in kq["he_so"][1:]]
    elif loai == "gop":
        dl += [f"- RR gộp (ngẫu nhiên, DL) = {so(kq['rr_gop_ngau_nhien'])} (KTC 95% {so(kq['ci_95'][0])}–"
               f"{so(kq['ci_95'][1])}); RR cố định = {so(kq['rr_gop_co_dinh'])}; τ² = {so(kq['tau2'], 4)}; "
               f"I² = {so(kq['i2_pct'], 1)}%; Q = {so(kq['q'], 2)} (df {kq['df']}); k = {kq['k']}", "",
               "| Nghiên cứu | RR | KTC 95% | Trọng số (%) |", "|---|---|---|---|"]
        dl += [f"| {t['nghien_cuu']} | {so(t['rr'])} | {so(t['ci_95'][0])}–{so(t['ci_95'][1])} | "
               f"{so(t['trong_so_ngau_nhien_pct'], 1)} |" for t in kq["tung_nghien_cuu"]]
    else:
        dl += [f"- {kq['n_ban_go_bang']} bản gỡ băng, {kq['so_chu_de']} chủ đề", "", "| Chủ đề | n | % |",
               "|---|---|---|"]
        dl += [f"| {c['chu_de']} | {c['n']} | {so(c['pct'], 1)} |" for c in kq["chu_de"]]
    if kc:
        dl += ["", f"**Kiểm chéo SPSS/R: {kc['trang_thai']}** — "
               + "; ".join(f"{k}: {v['trang_thai']}" for k, v in kc["phan_mem"].items())]
    return "\n".join(dl + ["", CAN_KIEM, ""])


def chay(study: str, gate: str, loai: str, ts: Dict[str, Any], kiem_cheo_bat: bool) -> int:
    if loai not in LOAI:
        raise TuChoi(f"--loai phải thuộc {sorted(LOAI)}")
    thieu = [k for k in LOAI[loai] if ts.get(k) in (None, "", [])]
    if thieu:
        raise TuChoi(f"thiếu tham số: {', '.join(thieu)}")
    _g4_da_khoa(study)
    can = ([ts[k] for k in LOAI[loai] if k not in ("nguong", "covariates")] + list(ts.get("covariates") or []))
    hang, csv_khoa, bo = doc_du_lieu(study, can, ts.get("loc"))
    print(f"✓ Đọc dữ liệu khoá {csv_khoa.name}: {len(hang)} ca dùng được (loại {bo} ca thiếu dữ liệu)")
    kq = tinh(loai, hang, ts)
    d = thu_muc_de_tai(study)
    py = cac_so_doi_chieu(loai, kq)
    kc = kiem_cheo(loai, ts, hang, d, gate, py) if kiem_cheo_bat else None
    tom = {"gate": gate, "study": study, "loai_dac_thu": loai, "n_total": len(hang), "n_loai_thieu": bo,
           "dac_thu": kq, "dac_ta_phan_tich": {"loai_dac_thu": loai, **ts},
           "du_lieu_khoa": csv_khoa.name, "chay_luc": datetime.now().isoformat(timespec="seconds"),
           "disclaimer": CAN_KIEM}
    (d / f"{gate}_analysis_summary.json").write_text(json.dumps(tom, ensure_ascii=False, indent=1), encoding="utf-8",
                                                    newline="\n")
    (d / f"{gate}_ket_qua.md").write_text(md_ket_qua(study, gate, loai, kq, kc), encoding="utf-8", newline="\n")
    if kc is not None:
        (d / f"{gate}_kiem_cheo.json").write_text(json.dumps(kc, ensure_ascii=False, indent=1), encoding="utf-8",
                                                 newline="\n")
        print(f"✓ Kiểm chéo SPSS/R: {kc['trang_thai']} — "
              + "; ".join(f"{k} {v['trang_thai']}" for k, v in kc["phan_mem"].items()))
    print(f"✓ {d / f'{gate}_ket_qua.md'}\n{CAN_KIEM}")
    return 0 if (kc is None or kc["trang_thai"] == "KHOP") else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Phân tích chính + kiểm chéo SPSS/R: chẩn đoán · dự báo · gộp · định tính")
    ap.add_argument("--study", required=True)
    ap.add_argument("--gate", default="G6")
    ap.add_argument("--data", default=None, help="(bỏ qua — luôn dùng dữ liệu ĐÃ KHOÁ của đề tài)")
    ap.add_argument("--loai", required=True, choices=sorted(LOAI))
    for k in ("tham_chieu", "chi_so", "outcome", "nhan_nghien_cuu", "su_kien_can_thiep", "n_can_thiep",
              "su_kien_chung", "n_chung", "chu_de"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, default=None)
    ap.add_argument("--nguong", type=float, default=None)
    ap.add_argument("--covariates", default="")
    ap.add_argument("--loc", default=None, help="biểu thức lọc quần thể (nhóm con/độ nhạy) — như run_stats_analysis")
    ap.add_argument("--kiem-cheo", action="store_true")
    a = ap.parse_args(argv)
    ts = {k: getattr(a, k) for k in LOAI[a.loai] if k != "covariates"}
    if a.loai == "du_bao":
        ts["covariates"] = [c.strip() for c in a.covariates.split(",") if c.strip()]
    if a.loc:
        ts["loc"] = a.loc
    try:
        return chay(a.study, a.gate, a.loai, ts, a.kiem_cheo)
    except TuChoi as e:
        print(f"✗ DỪNG: {e}\n{CAN_KIEM}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
