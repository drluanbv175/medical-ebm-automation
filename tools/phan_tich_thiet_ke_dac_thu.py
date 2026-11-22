#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""phan_tich_thiet_ke_dac_thu.py — phân tích CHÍNH + kiểm chéo SPSS/R cho 4 thiết kế run_stats_analysis chưa có đường.

Vì sao (giả lập trọn vòng 8 thiết kế, bác sĩ 16/11/2026: «nhập vào SPSS và R một cách chi tiết và hoàn thiện»): bộ máy
G6 chỉ có kết cục nhị phân/liên tục/thứ bậc/Poisson/tỷ lệ/sống còn ⇒ đề tài CHẨN ĐOÁN, DỰ BÁO, TỔNG QUAN–GỘP, ĐỊNH TÍNH
qua G6 mà KHÔNG có một con số nào (chay_sap_g6 ghi «không tự động»). Mô-đun này:

  chan_doan  AUC (thống kê Mann–Whitney, KTC Hanley–McNeil) + độ nhạy/độ đặc hiệu/PPV/NPV tại NGƯỠNG SAP (KTC Wilson).
  du_bao     hồi quy logistic: OR từng yếu tố dự báo, C-statistic (AUC của xác suất dự đoán), điểm Brier.
  gop        RR gộp hiệu ứng ngẫu nhiên DerSimonian–Laird + RR hiệu ứng cố định (nghịch đảo phương sai), τ², Q, I²;
             (22/11/2026, PRISMA 2020 mục 17/19/20c/21) biến cố/số người từng nhánh của từng nghiên cứu, tổng và hiệu
             ứng tuyệt đối trên 1000 người, kiểm định Egger khi k ≥ 10 (SAP §5), phân nhóm tiền định `--phan-nhom`
             (SAP §7: DL riêng từng nhóm + Q giữa nhóm), bảng đặc điểm từng nghiên cứu cho Bảng 1 của tổng quan;
             ô 0 ⇒ cộng 0,5 vào cả bốn ô của nghiên cứu đó (cùng quy ước metafor «only0»).
  dinh_tinh  tần suất từng chủ đề đã mã hoá (mô tả — phân tích chủ đề vẫn là việc của nhóm nghiên cứu).
  kinh_te    (16/11/2026, biến thể khó) đánh giá chi phí–hiệu quả ĐI KÈM thử nghiệm trên dữ liệu cá thể: chi phí và
             hiệu quả trung bình từng nhánh, ΔC, ΔE, ICER + góc phần tư (dùng health_econ_calc.icer), bootstrap phi
             tham số PHÂN TẦNG theo nhánh (B = 2000, seed cố định) cho KTC 95% của ΔC/ΔE/NMB, mặt phẳng chi phí–hiệu
             quả và đường CEAC tại các bội số của ngưỡng WTP SAP khai. Báo cáo theo CHEERS 2022 (PMID 35017145).

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
import re
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
    "kinh_te": ("nhom", "chi_phi", "hieu_qua", "nguong_wtp"),
}
#: tham số TUỲ CHỌN theo loại (22/11/2026): gộp — biến phân nhóm tiền định của SAP §7 (Q giữa nhóm) và `mo_hinh`
#: («ngau_nhien» mặc định = DerSimonian–Laird của phân tích chính; «co_dinh» = nghịch đảo phương sai — độ nhạy SAP §9
#: «Hiệu ứng cố định so với hiệu ứng ngẫu nhiên»). Cả hai luôn được tính trong MỘT lượt; `mo_hinh` chọn ước lượng báo
#: làm kết quả của mục đặc tả và đại lượng kiểm chéo metafor (method = "DL" hay "FE").
LOAI_TUY_CHON = {"gop": ("phan_nhom", "mo_hinh"),
                 # định tính: cột mã của người mã hoá THỨ HAI (cùng bộ mã, gán độc lập) ⇒ kappa Cohen (SAP §9
                 # confirmability) — số và tỷ lệ cặp trùng báo kèm
                 "dinh_tinh": ("chu_de_nguoi_2",)}
MO_HINH_GOP = ("ngau_nhien", "co_dinh")
SO_LAP_KT, HAT_GIONG_KT = 2000, 20261115  # bootstrap kinh tế: số lần lặp + seed (ghi vào kết quả, R dùng cùng seed)
BOI_SO_WTP = (0.0, 0.25, 0.5, 1.0, 1.5, 2.0, 3.0)  # CEAC: λ = bội số × ngưỡng WTP SAP khai
NHAN_GOC = {"dong_bac": "Đông Bắc (tốn hơn, hiệu quả hơn)", "dong_nam": "Đông Nam (rẻ hơn, hiệu quả hơn)",
            "tay_bac": "Tây Bắc (tốn hơn, kém hiệu quả hơn)", "tay_nam": "Tây Nam (rẻ hơn, kém hiệu quả hơn)"}
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


def _so_dem(v: Any) -> Any:
    """Số đếm chép từ dữ liệu khoá: giá trị nguyên ⇒ int (tóm tắt ghi «77», không «77.0» — G7 chép nguyên văn)."""
    f = float(v)
    return int(f) if f.is_integer() else f


def _ma_nhom(v: Any) -> str:
    """Mã phân nhóm dạng chuỗi, cùng khoá với nhãn lựa chọn của từ điển G5 (pandas đọc mã 2 thành 2.0)."""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v).strip()


def _gop_dl(tung: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """DerSimonian–Laird + nghịch đảo phương sai trên log RR của các nghiên cứu (`log_rr`, `var`). k = 1 ⇒ τ² = 0, Q = 0
    (như metafor::rma). Trả cả μ, se ở thang log để phân nhóm kiểm định khác biệt giữa nhóm trên đúng các số này."""
    k = len(tung)
    w = [1 / t["var"] for t in tung]
    sw = sum(w)
    tb_co_dinh = sum(wi * t["log_rr"] for wi, t in zip(w, tung)) / sw
    q = sum(wi * (t["log_rr"] - tb_co_dinh) ** 2 for wi, t in zip(w, tung))
    c = sw - sum(wi * wi for wi in w) / sw
    tau2 = max(0.0, (q - (k - 1)) / c) if c > 0 else 0.0
    ws = [1 / (t["var"] + tau2) for t in tung]
    sws = sum(ws)
    tb = sum(wi * t["log_rr"] for wi, t in zip(ws, tung)) / sws
    se, se_cd = math.sqrt(1 / sws), math.sqrt(1 / sw)
    return {"rr_gop_ngau_nhien": math.exp(tb), "ci_95": [math.exp(tb - Z * se), math.exp(tb + Z * se)],
            "rr_gop_co_dinh": math.exp(tb_co_dinh), "ci_95_co_dinh": [math.exp(tb_co_dinh - Z * se_cd),
                                                                        math.exp(tb_co_dinh + Z * se_cd)],
            "tau2": tau2, "q": q, "df": k - 1, "i2_pct": (max(0.0, (q - (k - 1)) / q) * 100) if q > 0 else 0.0,
            "k": k, "log_rr_gop": tb, "se_log_rr_gop": se, "trong_so": [100 * wi / sws for wi in ws]}


#: SAP §5 của khuôn tổng quan («biểu đồ phễu + kiểm định Egger khi ≥ 10 nghiên cứu») = Cochrane Handbook 13.3.5.4
EGGER_K_TOI_THIEU = 10


def egger(yi: Sequence[float], vi: Sequence[float]) -> Dict[str, Any]:
    """Kiểm định Egger (Egger 1997, PMID 9310563): hồi quy có trọng số 1/vᵢ của log RR theo sai số chuẩn √vᵢ, kiểm hệ
    số của sai số chuẩn bằng t với k − 2 bậc tự do — cùng phép của metafor::regtest(model = "lm", predictor = "sei") và
    của biểu đồ phễu (`bieu_do_gop.egger`). Chạy khi k ≥ EGGER_K_TOI_THIEU; dưới ngưỡng ⇒ `da_chay` False kèm lý do."""
    from scipy import stats  # noqa: PLC0415

    k = len(yi)
    if k < EGGER_K_TOI_THIEU:
        return {"da_chay": False, "k": k, "nguong_k": EGGER_K_TOI_THIEU,
                "ly_do": f"k = {k} < {EGGER_K_TOI_THIEU} nghiên cứu — SAP §5 chỉ kiểm định Egger khi ≥ "
                         f"{EGGER_K_TOI_THIEU} nghiên cứu (kém lực khi ít hơn, Cochrane Handbook 13.3.5.4)"}
    x = [math.sqrt(v) for v in vi]
    w = [1 / v for v in vi]
    sw, swx, swy = sum(w), sum(a * b for a, b in zip(w, x)), sum(a * b for a, b in zip(w, yi))
    swxx, swxy = sum(a * b * b for a, b in zip(w, x)), sum(a * b * c for a, b, c in zip(w, x, yi))
    d = sw * swxx - swx * swx
    if d <= 1e-12 * sw * swxx:
        return {"da_chay": False, "k": k, "nguong_k": EGGER_K_TOI_THIEU,
                "ly_do": "mọi nghiên cứu cùng sai số chuẩn — không ước lượng được hồi quy Egger"}
    b1 = (sw * swxy - swx * swy) / d
    b0 = (swy - b1 * swx) / sw
    s2 = sum(wi * (y - b0 - b1 * xi) ** 2 for wi, xi, y in zip(w, x, yi)) / (k - 2)
    se_b1 = math.sqrt(s2 * sw / d)
    t = b1 / se_b1
    return {"da_chay": True, "k": k, "nguong_k": EGGER_K_TOI_THIEU, "he_so_bat_doi_xung": b1, "se": se_b1,
            "chan_hoi_quy": b0, "t": t, "df": k - 2, "p": float(2 * stats.t.sf(abs(t), k - 2)),
            "phuong_phap": "Egger: hồi quy có trọng số 1/v của log RR theo sai số chuẩn, kiểm định t (k − 2 bậc tự "
                           "do) hệ số của sai số chuẩn — metafor::regtest(model = \"lm\", predictor = \"sei\")"}


def khoa_ma_nhom(m: str) -> tuple:
    """Thứ tự phân nhóm: mã số theo giá trị (1, 2, …, 10), mã chữ sau — bảng §3b của G7 và forest cùng thứ tự."""
    return (0, float(m), m) if re.fullmatch(r"-?\d+(\.\d+)?", m) else (1, 0.0, m)


def phan_nhom_gop(tung: Sequence[Dict[str, Any]], bien: str, nhan_nhom: Optional[Dict[str, str]] = None
                  ) -> Dict[str, Any]:
    """Phân nhóm tiền định (SAP §7): gộp DL RIÊNG từng phân nhóm (τ² riêng, như RevMan và metafor fit từng tập con) rồi
    kiểm định khác biệt giữa nhóm Q = Σ w_g (μ_g − μ̄)², w_g = 1/se_g², df = G − 1 — tương đương metafor::rma(yi = μ_g,
    sei = se_g, method = "FE")$QE. Phân nhóm chỉ một nghiên cứu vẫn vào kiểm định bằng chính ước lượng của nó."""
    from scipy import stats  # noqa: PLC0415

    nhan_nhom = nhan_nhom or {}
    ma = sorted({t["nhom"] for t in tung}, key=khoa_ma_nhom)
    nhom = []
    for m in ma:
        con = [t for t in tung if t["nhom"] == m]
        g = _gop_dl(con)
        nhom.append({"ma": m, "nhan": nhan_nhom.get(m, m), "k": g["k"], "rr": g["rr_gop_ngau_nhien"],
                     "ci_95": g["ci_95"], "tau2": g["tau2"], "q": g["q"], "df": g["df"], "i2_pct": g["i2_pct"],
                     "log_rr": g["log_rr_gop"], "se_log_rr": g["se_log_rr_gop"],
                     "nghien_cuu": [t["nghien_cuu"] for t in con]})
    ra: Dict[str, Any] = {"bien": bien, "nhom": nhom, "so_nhom": len(nhom),
                          "phuong_phap": "Gộp DerSimonian–Laird riêng từng phân nhóm; kiểm định khác biệt giữa nhóm Q "
                                         "= Σ w_g (μ_g − μ̄)², w_g = 1/se_g², χ² với G − 1 bậc tự do"}
    if len(nhom) < 2:
        return ra | {"ly_do": "chỉ có một phân nhóm trong dữ liệu — không kiểm định khác biệt giữa nhóm"}
    wg = [1 / g["se_log_rr"] ** 2 for g in nhom]
    mbar = sum(w * g["log_rr"] for w, g in zip(wg, nhom)) / sum(wg)
    qb = sum(w * (g["log_rr"] - mbar) ** 2 for w, g in zip(wg, nhom))
    return ra | {"q_giua_nhom": qb, "df_giua_nhom": len(nhom) - 1,
                 "p_giua_nhom": float(stats.chi2.sf(qb, len(nhom) - 1))}


def gop(hang: List[Dict[str, Any]], nhan: str, a: str, n1: str, c: str, n0: str, phan_nhom: Optional[str] = None,
        nhan_nhom: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    tung = []
    for r in hang:
        yi, vi = _o_rr(float(r[a]), float(r[n1]), float(r[c]), float(r[n0]))
        tung.append({"nghien_cuu": str(r[nhan]), "log_rr": yi, "var": vi, "rr": math.exp(yi),
                     "ci_95": [math.exp(yi - Z * math.sqrt(vi)), math.exp(yi + Z * math.sqrt(vi))],
                     # 22/11/2026 (PRISMA 2020 mục 19): thống kê tóm tắt TỪNG NHÁNH của từng nghiên cứu — số chép
                     # nguyên từ dữ liệu khoá (trước chỉ có log RR/var); hiệu chỉnh 0,5 khi có ô 0 ghi rõ
                     "su_kien_can_thiep": _so_dem(r[a]), "n_can_thiep": _so_dem(r[n1]),
                     "su_kien_chung": _so_dem(r[c]), "n_chung": _so_dem(r[n0]),
                     "hieu_chinh_o_0": bool(min(float(r[a]), float(r[c])) == 0 or float(r[a]) == float(r[n1])
                                            or float(r[c]) == float(r[n0])),
                     **({"nhom": _ma_nhom(r[phan_nhom])} if phan_nhom else {})})
    k = len(tung)
    if k < 2:
        raise TuChoi("phân tích gộp cần ≥ 2 nghiên cứu")
    g = _gop_dl(tung)
    for t, wi in zip(tung, g.pop("trong_so")):
        t["trong_so_ngau_nhien_pct"] = wi
    tong = {x: _so_dem(sum(float(t[x]) for t in tung))
            for x in ("su_kien_can_thiep", "n_can_thiep", "su_kien_chung", "n_chung")}
    tong["nguoi"] = _so_dem(float(tong["n_can_thiep"]) + float(tong["n_chung"]))
    # Hiệu ứng tuyệt đối dự kiến của bảng tóm tắt phát hiện (GRADE, khuôn GRADEpro): nguy cơ nhóm chứng = tỷ lệ gộp thô
    # nhóm chứng; hiệu số trên 1000 người = 1000 · nguy cơ chứng · (RR − 1), KTC từ KTC của RR gộp ngẫu nhiên.
    ncc = float(tong["su_kien_chung"]) / float(tong["n_chung"])
    rr, (lo, hi) = g["rr_gop_ngau_nhien"], g["ci_95"]
    ra = {**{x: v for x, v in g.items() if x not in ("log_rr_gop", "se_log_rr_gop")},
          "phuong_phap": "DerSimonian–Laird (ngẫu nhiên) + nghịch đảo phương sai (cố định); RR, log",
          "tung_nghien_cuu": tung, "tong": tong,
          "hieu_ung_tuyet_doi": {"nguy_co_nhom_chung": ncc, "bien_co_chung_moi_1000": 1000 * ncc,
                                 "bien_co_can_thiep_moi_1000": 1000 * ncc * rr,
                                 "hieu_so_moi_1000": 1000 * ncc * (rr - 1),
                                 "ci_95_hieu_so_moi_1000": [1000 * ncc * (lo - 1), 1000 * ncc * (hi - 1)],
                                 "cach_tinh": "nguy cơ nhóm chứng = tổng biến cố / tổng người nhánh chứng; hiệu số = "
                                              "1000 × nguy cơ chứng × (RR gộp ngẫu nhiên − 1), KTC theo KTC của RR"},
          "egger": egger([t["log_rr"] for t in tung], [t["var"] for t in tung])}
    if phan_nhom:
        ra["phan_nhom"] = phan_nhom_gop(tung, phan_nhom, nhan_nhom)
    return ra


def dong_thuan_hai_nguoi(hang: List[Dict[str, Any]], a: str, b: str) -> Dict[str, Any]:
    """Kappa Cohen giữa hai người mã hoá trên các bản có CẢ HAI mã — dùng `phan_tich_sap_bo_sung._kappa` (một công thức
    kappa cho mọi đường G6)."""
    import phan_tich_sap_bo_sung as PSB  # noqa: PLC0415

    cap = [(str(r.get(a) or "").strip(), str(r.get(b) or "").strip()) for r in hang]
    cap = [(x, y) for x, y in cap if x and y]
    k = PSB._kappa([x for x, _ in cap], [y for _, y in cap]) if cap else None
    return {"cot_nguoi_1": a, "cot_nguoi_2": b, "n_cap": len(cap), "n_trung": sum(1 for x, y in cap if x == y),
            "ty_le_trung": (sum(1 for x, y in cap if x == y) / len(cap)) if cap else None, "kappa": k,
            "cach_tinh": "kappa Cohen trên các bản có mã của cả hai người (một mã chính mỗi bản)"}


def dinh_tinh(hang: List[Dict[str, Any]], chu_de: str, chu_de_nguoi_2: Optional[str] = None) -> Dict[str, Any]:
    dem: Dict[str, int] = {}
    for r in hang:
        v = str(r.get(chu_de) or "").strip()
        if v:
            dem[v] = dem.get(v, 0) + 1
    n = sum(dem.values())
    return {"n_ban_go_bang": n, "so_chu_de": len(dem),
            "chu_de": [{"chu_de": k, "n": v, "pct": 100 * v / n, "ty_le": v / n, "ci_95_wilson": wilson(v, n)}
                       for k, v in sorted(dem.items(), key=lambda x: -x[1])],
            "ghi_chu": "Tần suất mô tả các mã đã gán — không thay phân tích chủ đề của nhóm nghiên cứu (COREQ/SRQR)",
            **({"dong_thuan_hai_nguoi": dong_thuan_hai_nguoi(hang, chu_de, chu_de_nguoi_2)} if chu_de_nguoi_2 else {})}


def _phan_vi(xs: Sequence[float], q: float) -> float:
    """Phân vị kiểu 7 (nội suy tuyến tính — mặc định của R `quantile`)."""
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = math.floor(h)
    return s[lo] + (h - lo) * (s[min(lo + 1, len(s) - 1)] - s[lo])


def kinh_te(hang: List[Dict[str, Any]], nhom: str, chi_phi: str, hieu_qua: str, wtp: float,
            so_lap: int = SO_LAP_KT, hat_giong: int = HAT_GIONG_KT, tra_lap: bool = False) -> Dict[str, Any]:
    """CEA đi kèm thử nghiệm: nhánh 1 = can thiệp, 0 = so sánh. ICER = ΔC/ΔE (đơn vị tiền trên một đơn vị hiệu quả).
    Bất định: bootstrap phân tầng (lấy lại có hoàn lại TRONG từng nhánh), KTC phân vị; CEAC = tỷ lệ lần lặp có
    NMB = λ·ΔE − ΔC > 0 — KHÔNG phải xác suất Bayes, là tần suất trong mẫu bootstrap."""
    import random  # noqa: PLC0415

    import health_econ_calc as HEC  # noqa: PLC0415

    if wtp is None or float(wtp) < 0:
        raise TuChoi("ngưỡng WTP phải là số không âm (SAP khai)")
    c = {g: [float(r[chi_phi]) for r in hang if int(float(r[nhom])) == g] for g in (0, 1)}
    e = {g: [float(r[hieu_qua]) for r in hang if int(float(r[nhom])) == g] for g in (0, 1)}
    if min(len(c[0]), len(c[1])) < 2:
        raise TuChoi("cần ≥ 2 người mỗi nhánh (nhóm mã 0/1)")
    tb = {k: {g: sum(v[g]) / len(v[g]) for g in (0, 1)} for k, v in (("c", c), ("e", e))}
    co_so = HEC.icer(tb["c"][0], tb["e"][0], tb["c"][1], tb["e"][1], wtp=float(wtp))
    rng = random.Random(hat_giong)
    n0, n1 = len(c[0]), len(c[1])
    lap = []
    for _ in range(so_lap):
        i1 = [rng.randrange(n1) for _ in range(n1)]
        i0 = [rng.randrange(n0) for _ in range(n0)]
        dc = sum(c[1][i] for i in i1) / n1 - sum(c[0][i] for i in i0) / n0
        de = sum(e[1][i] for i in i1) / n1 - sum(e[0][i] for i in i0) / n0
        lap.append((dc, de))
    goc = {"dong_bac": sum(dc > 0 and de > 0 for dc, de in lap), "dong_nam": sum(dc <= 0 and de > 0 for dc, de in lap),
           "tay_bac": sum(dc > 0 and de <= 0 for dc, de in lap), "tay_nam": sum(dc <= 0 and de <= 0 for dc, de in lap)}
    nmb = [float(wtp) * de - dc for dc, de in lap]
    ceac = [{"boi_so": b, "wtp": b * float(wtp), "ty_le_chi_phi_hieu_qua": sum(b * float(wtp) * de - dc > 0
                                                                              for dc, de in lap) / so_lap}
            for b in BOI_SO_WTP]
    return {"n": {"can_thiep": n1, "so_sanh": n0},
            "chi_phi_tb": {"can_thiep": tb["c"][1], "so_sanh": tb["c"][0]},
            "hieu_qua_tb": {"can_thiep": tb["e"][1], "so_sanh": tb["e"][0]},
            "delta_c": co_so["delta_cost"], "delta_e": co_so["delta_effect"], "icer": co_so["icer"],
            "goc_phan_tu": co_so["quadrant"], "nguong_wtp": float(wtp),
            "nmb_tai_wtp": co_so["nmb_incremental_at_wtp"],
            "ci_95_delta_c": [_phan_vi([x[0] for x in lap], 0.025), _phan_vi([x[0] for x in lap], 0.975)],
            "ci_95_delta_e": [_phan_vi([x[1] for x in lap], 0.025), _phan_vi([x[1] for x in lap], 0.975)],
            "ci_95_nmb": [_phan_vi(nmb, 0.025), _phan_vi(nmb, 0.975)],
            "mat_phang_bootstrap_pct": {k: 100 * v / so_lap for k, v in goc.items()}, "ceac": ceac,
            "bootstrap": {"so_lap": so_lap, "hat_giong": hat_giong, "kieu": "phi tham số, phân tầng theo nhánh"},
            **({"lap": lap} if tra_lap else {}),  # 21/11/2026: hinh_g6 vẽ mặt phẳng CE từ CÙNG các lần lặp
            "chuan_bao_cao": "CHEERS 2022 (PMID 35017145)",
            "ghi_chu": "CEAC là tần suất NMB > 0 trong mẫu bootstrap — không phải xác suất Bayes; ICER âm phải đọc "
                       "cùng góc phần tư (thống trị/bị thống trị), không xếp hạng như ICER dương."}


def tinh(loai: str, hang: List[Dict[str, Any]], ts: Dict[str, Any],
         nhan_nhom: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    if loai == "chan_doan":
        return chan_doan(hang, ts["tham_chieu"], ts["chi_so"], float(ts["nguong"]))
    if loai == "du_bao":
        return du_bao(hang, ts["outcome"], list(ts["covariates"]))
    if loai == "gop":
        return gop(hang, ts["nhan_nghien_cuu"], ts["su_kien_can_thiep"], ts["n_can_thiep"], ts["su_kien_chung"],
                   ts["n_chung"], ts.get("phan_nhom") or None, nhan_nhom)
    if loai == "kinh_te":
        return kinh_te(hang, ts["nhom"], ts["chi_phi"], ts["hieu_qua"], float(ts["nguong_wtp"]))
    return dinh_tinh(hang, ts["chu_de"], ts.get("chu_de_nguoi_2") or None)


def cac_so_doi_chieu(loai: str, kq: Dict[str, Any]) -> Dict[str, float]:
    """Đại lượng so giữa ba phần mềm (cùng tên khoá với kết quả R/SPSS)."""
    if loai == "chan_doan":
        return {"auc": kq["auc"]["auc"], "do_nhay": kq["do_nhay"]["uoc_luong"],
                "do_dac_hieu": kq["do_dac_hieu"]["uoc_luong"], "tp": kq["bang_2x2"]["tp"], "tn": kq["bang_2x2"]["tn"]}
    if loai == "du_bao":
        return {"c_statistic": kq["c_statistic"]["auc"], "brier": kq["brier"],
                **{f"or_{h['bien']}": h["or"] for h in kq["he_so"][1:]}}
    if loai == "gop":
        ra = {"rr_gop": kq["rr_gop_ngau_nhien"], "ci_duoi": kq["ci_95"][0], "ci_tren": kq["ci_95"][1],
              "tau2": kq["tau2"], "i2": kq["i2_pct"],
              # hiệu ứng cố định (nghịch đảo phương sai) — metafor::rma(method = "FE"); so ở MỌI lượt gộp
              "rr_gop_co_dinh": kq["rr_gop_co_dinh"], "ci_duoi_co_dinh": kq["ci_95_co_dinh"][0],
              "ci_tren_co_dinh": kq["ci_95_co_dinh"][1]}
        hu = kq.get("hieu_ung_tuyet_doi") or {}
        if hu:
            ra |= {"nguy_co_chung": hu["nguy_co_nhom_chung"], "hieu_so_1000": hu["hieu_so_moi_1000"]}
        eg = kq.get("egger") or {}
        if eg.get("da_chay"):
            ra |= {"egger_t": eg["t"], "egger_p": eg["p"]}
        pn = kq.get("phan_nhom") or {}
        for g in pn.get("nhom") or []:
            ra[f"rr_nhom_{g['ma']}"] = g["rr"]
        if pn.get("q_giua_nhom") is not None:
            ra |= {"q_giua_nhom": pn["q_giua_nhom"], "p_giua_nhom": pn["p_giua_nhom"]}
        return ra
    if loai == "kinh_te":  # đại lượng TẤT ĐỊNH — bootstrap phụ thuộc bộ sinh số ngẫu nhiên của từng phần mềm, không so
        ra = {"chi_phi_tb_1": kq["chi_phi_tb"]["can_thiep"], "chi_phi_tb_0": kq["chi_phi_tb"]["so_sanh"],
              "hieu_qua_tb_1": kq["hieu_qua_tb"]["can_thiep"], "hieu_qua_tb_0": kq["hieu_qua_tb"]["so_sanh"],
              "delta_c": kq["delta_c"], "delta_e": kq["delta_e"]}
        return ra | ({"icer": kq["icer"]} if kq["icer"] is not None else {})
    ra = {f"n_{i}": c["n"] for i, c in enumerate(kq["chu_de"])}
    dt = kq.get("dong_thuan_hai_nguoi") or {}
    return ra | ({"kappa": dt["kappa"]} if dt.get("kappa") is not None else {})


# ─────────────────────────────── dữ liệu khoá ───────────────────────────────
def thu_muc_de_tai(study: str) -> Path:
    import run_stats_analysis as RSA  # noqa: PLC0415

    return Path(RSA._thu_muc_de_tai(study))


def _doc_df_khoa(study: str, can: Sequence[str], loc: Optional[str] = None) -> tuple[Any, Path, Dict[str, Any]]:
    """(DataFrame ĐÃ KHOÁ sau phái sinh + lọc quần thể, đường dẫn bản khoá, manifest khoá) — dùng chung cho phân tích
    chính (`doc_du_lieu`) và Bảng 1 (`bang1_dac_thu`, 17/11/2026) để hai bảng tính trên CÙNG quần thể."""
    import bien_phai_sinh as BPS  # noqa: PLC0415
    import cau_noi_spss as S  # noqa: PLC0415
    import pandas as pd  # noqa: PLC0415

    try:
        csv_khoa, manifest = S.tim_du_lieu_khoa(study)
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
    return df, csv_khoa, (manifest if isinstance(manifest, dict) else {})


def doc_du_lieu(study: str, can: Sequence[str], loc: Optional[str] = None) -> tuple[List[Dict[str, Any]], Path, int]:
    """Bộ dữ liệu ĐÃ KHOÁ (G5) — đúng hàm kiểm khoá của cổng; biến PHÁI SINH (vd FIB-4, trường «calc») tính bằng ĐÚNG
    công thức đã duyệt của `_bien-phai-sinh.csv` như run_stats_analysis; giữ ca ĐỦ mọi cột cần (listwise, ghi số bị
    loại). `loc` = biểu thức lọc quần thể (nhóm con/độ nhạy) — ĐÚNG bộ lọc của run_stats_analysis (BPS.loc_python)."""
    import pandas as pd  # noqa: PLC0415

    df, csv_khoa, _man = _doc_df_khoa(study, can, loc)
    thieu = [c for c in can if c not in df.columns]
    if thieu:
        raise TuChoi(f"dữ liệu khoá thiếu cột (không có công thức phái sinh đã duyệt): {', '.join(thieu)}")
    du = df[list(can)].replace("", pd.NA).dropna()
    return du.to_dict("records"), csv_khoa, len(df) - len(du)


# Bảng 1 theo thiết kế (17/11/2026 — giả lập trọn vòng: tóm tắt G6 của 4 thiết kế đặc thù KHÔNG có `table1` ⇒ G7 không
# chép được Bảng 1, bản thảo chỉ còn ô trống mà nhãn của bộ giả lập che thành «đạt»). Biến chia nhóm theo đúng bảng đặc
# điểm mẫu của chuẩn báo cáo: dự báo — theo có/không kết cục (TRIPOD+AI mục 23a); chẩn đoán — theo chuẩn tham chiếu
# (STARD mục 20); định tính — mô tả người tham gia (COREQ mục 16); tổng quan–gộp — đặc điểm các nghiên cứu đưa vào
# (PRISMA 2020 mục 17). Một nhóm ⇒ không kiểm định.
def _bien_bang1(df: Any, loai: str, ts: Dict[str, Any], nhom: Optional[str]) -> List[str]:
    """Biến mô tả của Bảng 1 — bộ lọc chung `run_stats_analysis.bien_bang1_mo_ta`; bỏ thêm biến chia nhóm, nhãn nghiên
    cứu (gộp) và chính kết cục định tính (chủ đề) — kết cục trình bày ở bảng kết quả, không ở Bảng 1."""
    import run_stats_analysis as RSA  # noqa: PLC0415

    return RSA.bien_bang1_mo_ta(df, list(df.columns), (nhom, ts.get("nhan_nghien_cuu"), ts.get("chu_de")))


def _nhan_lua_chon(study: str, toi_thieu: int = 3) -> Dict[str, Dict[str, str]]:
    """{biến: {mã: nhãn}} của trường radio/dropdown ≥ `toi_thieu` lựa chọn trong từ điển G5 (hoặc bộ biến riêng G3) —
    biến mã hoá nhiều mức (loại thuốc, NYHA) phải là biến PHÂN LOẠI ở Bảng 1, không phải «2.00 [1.00–3.00]»; bảng đặc
    điểm từng nghiên cứu và phân nhóm (gộp) dùng mọi trường có lựa chọn (`toi_thieu` = 2)."""
    d = thu_muc_de_tai(study)
    tep = next((x for x in (d / f"G5_REDCap_dictionary_{study}.csv", d / "_bo-bien-rieng.csv") if x.is_file()), None)
    if tep is None:
        return {}
    ra: Dict[str, Dict[str, str]] = {}
    with tep.open(encoding="utf-8-sig", newline="") as fh:
        for r in csv.DictReader(fh):
            if (r.get("Field Type") or "").strip() not in ("radio", "dropdown"):
                continue
            lua = {}
            for muc in str(r.get("Choices, Calculations, OR Slider Labels") or "").split("|"):
                ma, _, nhan = muc.partition(",")
                if ma.strip() and nhan.strip():
                    lua[ma.strip()] = nhan.strip()
            if len(lua) >= toi_thieu:
                ra[str(r.get("Variable / Field Name") or "").strip()] = lua
    return ra


def bang1_dac_thu(study: str, loai: str, ts: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Bảng 1 THÔ (khuôn `run_stats_analysis.table1_descriptive` — `chay` đổi sang `bang1_cho_tom_tat` cho tóm tắt mà G7
    chép và `format_table1_text` cho `<gate>_table1_descriptive.txt`) của thiết kế đặc thù; None với loại không có bảng
    đặc điểm mẫu riêng (kinh tế — đi kèm thử nghiệm đã có Bảng 1). Lỗi tính ⇒ {"error": …}, không im lặng."""
    import run_stats_analysis as RSA  # noqa: PLC0415

    nhom = {"du_bao": ts.get("outcome"), "chan_doan": ts.get("tham_chieu")}.get(loai)
    if loai not in ("du_bao", "chan_doan", "dinh_tinh", "gop"):
        return None
    can = [str(x) for x in (ts.get(k) for k in LOAI[loai] if k not in ("nguong", "covariates")) if x]
    try:
        df, _csv, _man = _doc_df_khoa(study, can, ts.get("loc"))
        if not nhom:
            df = df.assign(_nhom_bang1=RSA.NHOM_TOAN_BO)
            nhom = "_nhom_bang1"
        for bien, lua in _nhan_lua_chon(study).items():
            if bien in df.columns and bien != nhom:
                df[bien] = df[bien].map(lambda v, _l=lua: None if v is None or v != v else _l.get(
                    str(int(v)) if isinstance(v, float) and v.is_integer() else str(v), str(v)))
        return RSA.table1_descriptive(df, nhom, _bien_bang1(df, loai, ts, nhom), kiem_dinh_nen=True)
    except (TuChoi, ValueError, ZeroDivisionError, KeyError) as e:
        return {"error": f"không dựng được Bảng 1: {e}"}


def _nhan_truong(study: str) -> Dict[str, str]:
    """{biến: nhãn} của từ điển G5 (hoặc bộ biến riêng G3) — tiêu đề cột của bảng đặc điểm từng nghiên cứu."""
    d = thu_muc_de_tai(study)
    tep = next((x for x in (d / f"G5_REDCap_dictionary_{study}.csv", d / "_bo-bien-rieng.csv") if x.is_file()), None)
    if tep is None:
        return {}
    with tep.open(encoding="utf-8-sig", newline="") as fh:
        return {str(r.get("Variable / Field Name") or "").strip(): str(r.get("Field Label") or "").strip()
                for r in csv.DictReader(fh) if str(r.get("Variable / Field Name") or "").strip()}


def _gia_tri_o(v: Any, lua: Optional[Dict[str, str]]) -> Any:
    """Một ô của bảng đặc điểm: mã lựa chọn ⇒ nhãn từ điển; số nguyên ⇒ int; số thực/chuỗi giữ nguyên; trống ⇒ None."""
    if v is None or (isinstance(v, float) and v != v) or (isinstance(v, str) and not v.strip()):
        return None
    if lua:
        return lua.get(_ma_nhom(v), _ma_nhom(v))
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):  # DataFrame.to_dict("records") trả kiểu Python gốc
        return _so_dem(v)
    return str(v).strip()


def bang_dac_diem_nghien_cuu(study: str, ts: Dict[str, Any], dung: Sequence[str]) -> Dict[str, Any]:
    """Bảng ĐẶC ĐIỂM TỪNG NGHIÊN CỨU được đưa vào tổng hợp (PRISMA 2020 mục 17, 22/11/2026) — thay «Bảng 1. Đặc điểm nền
    người tham gia» (trung bình gộp mọi nghiên cứu, khuôn nghiên cứu gốc) mà G7 từng chép cho tổng quan. Một dòng mỗi
    nghiên cứu ĐÃ VÀO phân tích (`dung` — nhãn nghiên cứu sau khi bỏ ca thiếu), cùng quần thể (`loc`); cột = biến của
    dữ liệu khoá qua bộ lọc Bảng 1 dùng chung, trừ nhãn nghiên cứu và số biến cố (trình bày ở bảng kết quả từng nghiên
    cứu); mã lựa chọn đổi sang nhãn từ điển G5, giá trị chép nguyên. Lỗi ⇒ {"error": …}."""
    import run_stats_analysis as RSA  # noqa: PLC0415

    nhan = ts["nhan_nghien_cuu"]
    can = [str(ts[k]) for k in LOAI["gop"]] + ([str(ts["phan_nhom"])] if ts.get("phan_nhom") else [])
    try:
        df, _csv, _man = _doc_df_khoa(study, can, ts.get("loc"))
        bo = (nhan, ts["su_kien_can_thiep"], ts["su_kien_chung"])
        cot = RSA.bien_bang1_mo_ta(df, [c for c in df.columns if not str(c).startswith("_")], bo)
        lua, ten = _nhan_lua_chon(study, toi_thieu=2), _nhan_truong(study)
        dung_set = {str(x) for x in dung}
        dong = [{"nghien_cuu": str(r[nhan]), "gia_tri": {c: _gia_tri_o(r[c], lua.get(c)) for c in cot}}
                for r in df.to_dict("records") if str(r[nhan]) in dung_set]
    except (TuChoi, ValueError, KeyError) as e:
        return {"error": f"không dựng được bảng đặc điểm từng nghiên cứu: {e}"}
    if not dong:
        return {"error": "không còn nghiên cứu nào của phân tích trong dữ liệu khoá"}
    return {"cot": [{"bien": c, "nhan": ten.get(c) or c} for c in cot], "dong": dong, "k": len(dong),
            "nhan_nghien_cuu": {"bien": nhan, "nhan": ten.get(nhan) or nhan},
            "ghi_chu": "Một dòng mỗi nghiên cứu được đưa vào tổng hợp; giá trị chép từ dữ liệu đã khoá, mã lựa chọn "
                       "đổi sang nhãn từ điển G5."}


def _ghi_nguyen_tu(p: Path, noi_dung: str) -> None:
    """Ghi tệp qua tệp tạm cùng thư mục + os.replace (không để tệp dở dang khi lỗi giữa chừng), xuống dòng LF."""
    import os  # noqa: PLC0415

    tam = p.with_name(f".{p.name}.tam")
    with tam.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write(noi_dung)
    os.replace(tam, p)


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
                # SAP §9 «hiệu ứng cố định so với ngẫu nhiên»: nghịch đảo phương sai, cùng yi/vi
                'mf <- metafor::rma(yi, vi, data = es, method = "FE")\n'
                'ghi("rr_gop_co_dinh", exp(as.numeric(mf$b))); ghi("ci_duoi_co_dinh", exp(mf$ci.lb)); '
                'ghi("ci_tren_co_dinh", exp(mf$ci.ub))\nprint(mf)\n'
                # 22/11/2026: hiệu ứng tuyệt đối của bảng tóm tắt phát hiện (GRADE) — cùng cách tính Python
                f'ncc <- sum(df[["{ts["su_kien_chung"]}"]]) / sum(df[["{ts["n_chung"]}"]])\n'
                'ghi("nguy_co_chung", ncc); ghi("hieu_so_1000", 1000 * ncc * (exp(as.numeric(m$b)) - 1))\n'
                # Egger — SAP §5: chỉ khi ≥ EGGER_K_TOI_THIEU nghiên cứu (Python chỉ so khi đã chạy)
                f'if (nrow(es) >= {EGGER_K_TOI_THIEU}) {{ e <- metafor::regtest(m, model = "lm", predictor = "sei")\n'
                '  ghi("egger_t", e$zval); ghi("egger_p", e$pval); print(e) }\n'
                + (f'g <- as.character(df[["{ts["phan_nhom"]}"]]); g <- sub("\\\\.0+$", "", g)\n'
                   '# Phân nhóm SAP §7: DL riêng từng phân nhóm; Q giữa nhóm = QE mô hình cố định trên ước lượng nhóm\n'
                   'mu <- c(); se <- c()\n'
                   'for (lv in unique(g)) { mg <- metafor::rma(yi, vi, data = es[g == lv, ], method = "DL")\n'
                   '  mu <- c(mu, as.numeric(mg$b)); se <- c(se, mg$se); ghi(paste0("rr_nhom_", lv), '
                   'exp(as.numeric(mg$b))) }\n'
                   'if (length(mu) >= 2) { mb <- metafor::rma(yi = mu, sei = se, method = "FE")\n'
                   '  ghi("q_giua_nhom", mb$QE); ghi("p_giua_nhom", mb$QEp) }\n'
                   if ts.get("phan_nhom") else "")
                + '# metafor::forest(m, atransf = exp)  # biểu đồ rừng\n')
    elif loai == "kinh_te":
        g, cc, ee, lam = ts["nhom"], ts["chi_phi"], ts["hieu_qua"], float(ts["nguong_wtp"])
        boi = ", ".join(repr(b) for b in BOI_SO_WTP)
        than = (f'g <- df[["{g}"]]; cc <- df[["{cc}"]]; ee <- df[["{ee}"]]\n'
                'c1 <- mean(cc[g == 1]); c0 <- mean(cc[g == 0]); e1 <- mean(ee[g == 1]); e0 <- mean(ee[g == 0])\n'
                'ghi("chi_phi_tb_1", c1); ghi("chi_phi_tb_0", c0); ghi("hieu_qua_tb_1", e1); ghi("hieu_qua_tb_0", e0)\n'
                'ghi("delta_c", c1 - c0); ghi("delta_e", e1 - e0); ghi("icer", (c1 - c0) / (e1 - e0))\n'
                '# Bootstrap phân tầng theo nhánh (tham khảo: bộ sinh số của R khác Python nên KTC/CEAC lệch nhỏ)\n'
                f'set.seed({HAT_GIONG_KT}); B <- {SO_LAP_KT}\n'
                'bt <- replicate(B, { i1 <- sample(which(g == 1), replace = TRUE); '
                'i0 <- sample(which(g == 0), replace = TRUE)\n'
                '  c(mean(cc[i1]) - mean(cc[i0]), mean(ee[i1]) - mean(ee[i0])) })\n'
                'print(quantile(bt[1, ], c(0.025, 0.975))); print(quantile(bt[2, ], c(0.025, 0.975)))\n'
                f'for (b in c({boi})) cat(sprintf("CEAC WTP=%.0f: %.3f\\n", b * {lam!r}, '
                f'mean(b * {lam!r} * bt[2, ] - bt[1, ] > 0)))\n'
                '# plot(bt[2, ], bt[1, ], xlab = "ΔE", ylab = "ΔC")  # mặt phẳng chi phí–hiệu quả\n')
    else:
        cd = ts["chu_de"]
        than = (f'bang <- sort(table(df[["{cd}"]][df[["{cd}"]] != ""]), decreasing = TRUE)\n'
                'for (i in seq_along(bang)) ghi(sprintf("n_%d", i - 1), as.numeric(bang[[i]]))\nprint(bang)\n'
                + (f'a <- trimws(df[["{cd}"]]); b <- trimws(df[["{ts["chu_de_nguoi_2"]}"]])\n'
                   '# Kappa Cohen hai người mã hoá (cặp có cả hai mã)\n'
                   'o <- !is.na(a) & !is.na(b) & a != "" & b != ""; a <- a[o]; b <- b[o]\n'
                   'm <- sort(union(a, b)); po <- mean(a == b)\n'
                   'pe <- sum(sapply(m, function(x) mean(a == x) * mean(b == x)))\n'
                   'ghi("kappa", (po - pe) / (1 - pe))\n' if ts.get("chu_de_nguoi_2") else ""))
    return dau + than + "close(out)\n"


def _gia_tri_spss(loai: str, ts: Dict[str, Any]) -> List[tuple[str, str]]:
    if loai == "chan_doan":
        return [(ts["tham_chieu"], "F8.0"), (ts["chi_so"], "F20.10")]
    if loai == "du_bao":
        return [(ts["outcome"], "F8.0"), *[(c, "F20.10") for c in ts["covariates"]]]
    if loai == "gop":  # biến phân nhóm (tuỳ chọn) chỉ R dùng — đọc dạng chuỗi cho mọi kiểu mã
        return [(ts["nhan_nghien_cuu"], "A60"), *[(ts[k], "F20.6") for k in LOAI["gop"][1:]],
                *([(ts["phan_nhom"], "A60")] if ts.get("phan_nhom") else [])]
    if loai == "kinh_te":
        return [(ts["nhom"], "F8.0"), (ts["chi_phi"], "F20.4"), (ts["hieu_qua"], "F20.10")]
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
                # 22/11/2026: hiệu ứng tuyệt đối (GRADE) + Egger dạng đóng của hồi quy có trọng số 1/vi theo √vi
                f"AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /tc=SUM({c}) /tn0=SUM({n0}).",
                "COMPUTE nguy_co_chung = tc / tn0.", "COMPUTE hieu_so_1000 = 1000 * nguy_co_chung * (rr_gop - 1).",
                "COMPUTE xi = SQRT(vi).", "COMPUTE wx = wi * xi.", "COMPUTE wxx = wi * xi * xi.",
                "COMPUTE wxy = wi * xi * yi.",
                "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /swx=SUM(wx) /swxx=SUM(wxx) /swxy=SUM(wxy).",
                "COMPUTE dd = sw * swxx - swx * swx.", "COMPUTE b1 = (sw * swxy - swx * swy) / dd.",
                "COMPUTE b0 = (swy - b1 * swx) / sw.", "COMPUTE ri = wi * (yi - b0 - b1 * xi) ** 2.",
                "AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /rss=SUM(ri).",
                "COMPUTE egger_t = b1 / SQRT(rss / (k - 2) * sw / dd).",
                "COMPUTE egger_p = 2 * (1 - CDF.T(ABS(egger_t), k - 2)).",
                "SELECT IF $CASENUM = 1.",
                "FORMATS rr_gop ci_duoi ci_tren tau2 i2 nguy_co_chung hieu_so_1000 egger_t egger_p (F24.15).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=rr_gop ci_duoi ci_tren tau2 i2 nguy_co_chung hieu_so_1000 egger_t egger_p."]
    elif loai == "kinh_te":
        g, cc, ee = ts["nhom"], ts["chi_phi"], ts["hieu_qua"]
        than = [f"COMPUTE cc1 = {cc} * ({g} = 1).", f"COMPUTE ee1 = {ee} * ({g} = 1).",
                f"AGGREGATE /OUTFILE=* MODE=ADDVARIABLES /n1=SUM({g}) /nn=N({g}) /sc=SUM({cc}) /sc1=SUM(cc1) "
                f"/se=SUM({ee}) /se1=SUM(ee1).",
                "COMPUTE chi_phi_tb_1 = sc1 / n1.", "COMPUTE chi_phi_tb_0 = (sc - sc1) / (nn - n1).",
                "COMPUTE hieu_qua_tb_1 = se1 / n1.", "COMPUTE hieu_qua_tb_0 = (se - se1) / (nn - n1).",
                "COMPUTE delta_c = chi_phi_tb_1 - chi_phi_tb_0.", "COMPUTE delta_e = hieu_qua_tb_1 - hieu_qua_tb_0.",
                "COMPUTE icer = delta_c / delta_e.", "SELECT IF $CASENUM = 1.",
                "FORMATS chi_phi_tb_1 chi_phi_tb_0 delta_c icer (F24.6) hieu_qua_tb_1 hieu_qua_tb_0 delta_e (F24.15).",
                f"SAVE TRANSLATE /OUTFILE='{ra}' /TYPE=CSV /ENCODING='UTF8' /FIELDNAMES /CELLS=VALUES /REPLACE "
                "/KEEP=chi_phi_tb_1 chi_phi_tb_0 hieu_qua_tb_1 hieu_qua_tb_0 delta_c delta_e icer."]
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
    ra: Dict[str, float] = {}
    for k, v in dong[0].items():  # ô trống (giá trị thiếu hệ thống, vd ICER khi ΔE = 0) ⇒ không có khoá, không gán 0
        try:
            ra[k.strip()] = float(v)
        except (TypeError, ValueError):
            continue
    return ra


# SPSS chỉ xuất các đại lượng tính được bằng RANK/AGGREGATE (dự báo: C-statistic + Brier — hai số này đã phụ thuộc mọi
# hệ số của mô hình); R so ĐỦ mọi đại lượng kể cả OR từng yếu tố. Gộp (22/11/2026): SPSS so ước lượng chung, hiệu ứng
# tuyệt đối và Egger; phân nhóm (số nhóm thay đổi theo dữ liệu) chỉ R so.
DAI_LUONG_SPSS = {"du_bao": ("c_statistic", "brier")}
# 22/11/2026: hiệu ứng cố định của gộp (metafor method = "FE") và kappa hai người mã hoá (định tính) — chỉ R so.
_CHI_R = ("rr_nhom_", "q_giua_nhom", "p_giua_nhom", "rr_gop_co_dinh", "ci_duoi_co_dinh", "ci_tren_co_dinh", "kappa")


def dai_luong_spss(loai: str, py: Dict[str, float]) -> Optional[List[str]]:
    if loai in ("gop", "dinh_tinh"):
        return [k for k in py if not k.startswith(_CHI_R)]
    return list(DAI_LUONG_SPSS[loai]) if loai in DAI_LUONG_SPSS else None


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
            ket["spss"] = (so_khop(py, _doc_kq_spss(sp_ra, loai), dai_luong_spss(loai, py)) if sp_ra.is_file() else
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
               "| Nghiên cứu | Biến cố/N can thiệp | Biến cố/N chứng | RR | KTC 95% | Trọng số (%) |",
               "|---|---|---|---|---|---|"]
        dl += [f"| {t['nghien_cuu']} | {t.get('su_kien_can_thiep', '—')}/{t.get('n_can_thiep', '—')} | "
               f"{t.get('su_kien_chung', '—')}/{t.get('n_chung', '—')} | {so(t['rr'])} | {so(t['ci_95'][0])}–"
               f"{so(t['ci_95'][1])} | {so(t['trong_so_ngau_nhien_pct'], 1)} |" for t in kq["tung_nghien_cuu"]]
        eg = kq.get("egger") or {}
        if eg.get("da_chay"):
            dl += ["", f"- Kiểm định Egger (k = {eg['k']}): hệ số bất đối xứng {so(eg['he_so_bat_doi_xung'])}, "
                       f"t = {so(eg['t'], 2)} (df {eg['df']}), p = {so(eg['p'], 3)}"]
        elif eg:
            dl += ["", f"- Kiểm định Egger: không chạy — {eg.get('ly_do')}"]
        hu = kq.get("hieu_ung_tuyet_doi") or {}
        if hu:
            dl.append(f"- Hiệu ứng tuyệt đối (trên 1000 người): nhóm chứng {so(hu['bien_co_chung_moi_1000'], 1)}, "
                      f"can thiệp {so(hu['bien_co_can_thiep_moi_1000'], 1)}; hiệu số {so(hu['hieu_so_moi_1000'], 1)} "
                      f"(KTC 95% {so(hu['ci_95_hieu_so_moi_1000'][0], 1)} đến "
                      f"{so(hu['ci_95_hieu_so_moi_1000'][1], 1)})")
        pn = kq.get("phan_nhom") or {}
        if pn:
            dl += ["", f"Phân nhóm theo `{pn['bien']}`:", "", "| Phân nhóm | k | RR | KTC 95% | I² (%) |",
                   "|---|---|---|---|---|"]
            dl += [f"| {g['nhan']} | {g['k']} | {so(g['rr'])} | {so(g['ci_95'][0])}–{so(g['ci_95'][1])} | "
                   f"{so(g['i2_pct'], 1)} |" for g in pn["nhom"]]
            if pn.get("q_giua_nhom") is not None:
                dl += ["", f"- Khác biệt giữa phân nhóm: Q = {so(pn['q_giua_nhom'], 2)} (df {pn['df_giua_nhom']}), "
                           f"p = {so(pn['p_giua_nhom'], 3)}"]
    elif loai == "kinh_te":
        def tien(v):
            return "—" if v is None else f"{v:,.0f}".replace(",", ".")

        dl += [f"- Chi phí trung bình: can thiệp {tien(kq['chi_phi_tb']['can_thiep'])} · so sánh "
               f"{tien(kq['chi_phi_tb']['so_sanh'])}; hiệu quả trung bình: can thiệp "
               f"{so(kq['hieu_qua_tb']['can_thiep'])} · so sánh {so(kq['hieu_qua_tb']['so_sanh'])} "
               f"(n = {kq['n']['can_thiep']} / {kq['n']['so_sanh']})",
               f"- ΔC = {tien(kq['delta_c'])} (KTC 95% bootstrap {tien(kq['ci_95_delta_c'][0])} đến "
               f"{tien(kq['ci_95_delta_c'][1])}); ΔE = {so(kq['delta_e'])} (KTC 95% {so(kq['ci_95_delta_e'][0])} đến "
               f"{so(kq['ci_95_delta_e'][1])})",
               f"- ICER = {tien(kq['icer'])} trên một đơn vị hiệu quả — {kq['goc_phan_tu']}",
               f"- NMB tại ngưỡng WTP {tien(kq['nguong_wtp'])} = {tien(kq['nmb_tai_wtp'])} (KTC 95% "
               f"{tien(kq['ci_95_nmb'][0])} đến {tien(kq['ci_95_nmb'][1])})",
               "- Mặt phẳng chi phí–hiệu quả (% lần lặp bootstrap): " + "; ".join(
                   f"{NHAN_GOC.get(k, k)} {so(v, 1)}%" for k, v in kq["mat_phang_bootstrap_pct"].items()), "",
               "| Ngưỡng WTP (bội số) | WTP | Tỷ lệ lần lặp chi phí–hiệu quả |", "|---|---|---|"]
        dl += [f"| ×{so(x['boi_so'], 2)} | {tien(x['wtp'])} | {so(x['ty_le_chi_phi_hieu_qua'])} |" for x in kq["ceac"]]
        dl += ["", f"_Bootstrap {kq['bootstrap']['kieu']}, B = {kq['bootstrap']['so_lap']}, seed "
                   f"{kq['bootstrap']['hat_giong']}. Báo cáo theo {kq['chuan_bao_cao']}. {kq['ghi_chu']}_"]
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
    if ts.get("mo_hinh") not in (None, *MO_HINH_GOP):
        raise TuChoi(f"mo_hinh phải thuộc {list(MO_HINH_GOP)}")
    _g4_da_khoa(study)
    can = ([ts[k] for k in LOAI[loai] if k not in ("nguong", "covariates", "nguong_wtp")]
           + list(ts.get("covariates") or [])
           + [ts[k] for k in LOAI_TUY_CHON.get(loai, ()) if ts.get(k) and k != "mo_hinh"])
    hang, csv_khoa, bo = doc_du_lieu(study, can, ts.get("loc"))
    print(f"✓ Đọc dữ liệu khoá {csv_khoa.name}: {len(hang)} ca dùng được (loại {bo} ca thiếu dữ liệu)")
    nhan_nhom = _nhan_lua_chon(study, toi_thieu=2).get(str(ts["phan_nhom"])) if ts.get("phan_nhom") else None
    kq = tinh(loai, hang, ts, nhan_nhom)
    d = thu_muc_de_tai(study)
    py = cac_so_doi_chieu(loai, kq)
    kc = kiem_cheo(loai, ts, hang, d, gate, py) if kiem_cheo_bat else None
    import cau_noi_spss as S  # noqa: PLC0415

    man = S.tim_du_lieu_khoa(study)[1] or {}  # cùng hàm kiểm khoá đã dùng khi đọc dữ liệu ở trên
    luc = datetime.now().isoformat(timespec="seconds")
    tom = {"gate": gate, "study": study, "loai_dac_thu": loai, "n_total": len(hang), "n_loai_thieu": bo,
           "dac_thu": kq, "dac_ta_phan_tich": {"loai_dac_thu": loai, **ts},
           "du_lieu_khoa": csv_khoa.name, "chay_luc": luc,
           # 17/11/2026: cùng khoá nguồn gốc với tóm tắt run_stats_analysis — G7 (doc_tom_tat_g6_hop_le) chỉ dựng Kết
           # quả từ tóm tắt chứng minh được sinh từ ĐÚNG bản khoá (sha256 trùng manifest); thiếu khoá này G7 fail-closed
           # và bản thảo 4 thiết kế đặc thù luôn là khung trống.
           "generated": luc,
           "data_lock": {"locked_dataset_path": man.get("locked_dataset_path"), "sha256": man.get("sha256"),
                         "lock_date": man.get("lock_date"), "approved_by": man.get("approved_by"),
                         "sap_version": man.get("sap_version")},
           "disclaimer": CAN_KIEM}
    t1 = bang1_dac_thu(study, loai, ts)
    if t1 is not None:
        import run_stats_analysis as RSA  # noqa: PLC0415

        loi_t1 = t1.get("error")
        tom["table1"] = {"error": loi_t1} if loi_t1 else RSA.bang1_cho_tom_tat(t1)
        _ghi_nguyen_tu(d / f"{gate}_table1_descriptive.txt",
                       f"BẢNG 1 — ĐẶC ĐIỂM MẪU\nLỖI: {loi_t1}\n" if loi_t1 else RSA.format_table1_text(t1) + "\n")
    if loai == "gop":  # PRISMA 2020 mục 17 — đặc điểm TỪNG nghiên cứu (G7 dùng bảng này làm Bảng 1 của tổng quan)
        tom["bang_dac_diem_nghien_cuu"] = bang_dac_diem_nghien_cuu(
            study, ts, [t["nghien_cuu"] for t in kq["tung_nghien_cuu"]])
    _ghi_nguyen_tu(d / f"{gate}_analysis_summary.json", json.dumps(tom, ensure_ascii=False, indent=1))
    _ghi_nguyen_tu(d / f"{gate}_ket_qua.md", md_ket_qua(study, gate, loai, kq, kc))
    if kc is not None:
        _ghi_nguyen_tu(d / f"{gate}_kiem_cheo.json", json.dumps(kc, ensure_ascii=False, indent=1))
        print(f"✓ Kiểm chéo SPSS/R: {kc['trang_thai']} — "
              + "; ".join(f"{k} {v['trang_thai']}" for k, v in kc["phan_mem"].items()))
    print(f"✓ {d / f'{gate}_ket_qua.md'}\n{CAN_KIEM}")
    return 0 if (kc is None or kc["trang_thai"] == "KHOP") else 1


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Phân tích chính + kiểm chéo SPSS/R: chẩn đoán · dự báo · gộp · định tính "
                                             "· kinh tế")
    ap.add_argument("--study", required=True)
    ap.add_argument("--gate", default="G6")
    ap.add_argument("--data", default=None, help="(bỏ qua — luôn dùng dữ liệu ĐÃ KHOÁ của đề tài)")
    ap.add_argument("--loai", required=True, choices=sorted(LOAI))
    for k in ("tham_chieu", "chi_so", "outcome", "nhan_nghien_cuu", "su_kien_can_thiep", "n_can_thiep",
              "su_kien_chung", "n_chung", "chu_de", "nhom", "chi_phi", "hieu_qua"):
        ap.add_argument("--" + k.replace("_", "-"), dest=k, default=None)
    ap.add_argument("--phan-nhom", dest="phan_nhom", default=None,
                    help="gop: biến phân nhóm tiền định của SAP §7 — gộp riêng từng nhóm + Q giữa nhóm")
    ap.add_argument("--chu-de-nguoi-2", dest="chu_de_nguoi_2", default=None,
                    help="dinh_tinh: cột mã của người mã hoá thứ hai ⇒ kappa Cohen (SAP §9 confirmability)")
    ap.add_argument("--mo-hinh", dest="mo_hinh", default=None, choices=MO_HINH_GOP,
                    help="gop: ước lượng báo làm kết quả — ngau_nhien (DL, mặc định) hoặc co_dinh "
                         "(nghịch đảo phương sai)")
    ap.add_argument("--nguong", type=float, default=None)
    ap.add_argument("--nguong-wtp", dest="nguong_wtp", type=float, default=None,
                    help="kinh_te: ngưỡng sẵn lòng chi trả cho một đơn vị hiệu quả (SAP khai)")
    ap.add_argument("--covariates", default="")
    ap.add_argument("--loc", default=None, help="biểu thức lọc quần thể (nhóm con/độ nhạy) — như run_stats_analysis")
    ap.add_argument("--kiem-cheo", action="store_true")
    a = ap.parse_args(argv)
    ts = {k: getattr(a, k) for k in LOAI[a.loai] if k != "covariates"}
    ts |= {k: getattr(a, k) for k in LOAI_TUY_CHON.get(a.loai, ()) if getattr(a, k, None)}
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
