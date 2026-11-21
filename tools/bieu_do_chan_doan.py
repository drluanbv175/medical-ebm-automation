#!/usr/bin/env python3
"""Biểu đồ CHẨN ĐOÁN và MÔ HÌNH DỰ BÁO — tính đúng, vẽ đúng chuẩn STARD 2015 / TRIPOD+AI (chặng 2 của chương trình
biểu đồ, bác sĩ 21/11/2026: «phải thực hiện được tất cả biểu đồ một cách chi tiết và chính xác nhất»).

Trước bản này: `phan_tich_thiet_ke_dac_thu.py` tính AUC nhưng không vẽ; `khung_bieu_bang.ve_hinh` chỉ vẽ khung ROC/hiệu
chuẩn rỗng cho đề cương; không có công cụ nào vẽ đường hiệu chuẩn có số, phân tích đường cong quyết định (DCA), toán đồ
Fagan hay so sánh hai đường ROC.

Họ biểu đồ (mỗi lệnh ghi PNG 300 dpi + PDF vector + JSON số liệu đã vẽ, qua `bieu_do_chung`):
  roc         ROC thực nghiệm một hoặc nhiều xét nghiệm trên CÙNG đối tượng: AUC + KTC 95% DeLong, điểm cắt Youden
              (ngưỡng, độ nhạy, độ đặc hiệu), so sánh cặp DeLong (z, p) — như pROC::roc/ci.auc/roc.test/coords.
  pr          đường precision–recall kèm đường nền tỷ lệ hiện mắc và độ chính xác trung bình (AP).
  hieu-chuan  đường hiệu chuẩn (TRIPOD+AI): đường lowess, điểm theo nhóm thập phân vị có KTC 95%, đường lý tưởng; chỉ
              số C, Brier, E/O, chặn hiệu chuẩn (CITL, offset), chặn + độ dốc hiệu chuẩn lại, Emax/Eavg — như
              rms::val.prob; phân bố nguy cơ dự báo theo kết cục ở dải dưới.
  dca         phân tích đường cong quyết định (Vickers 2006): lợi ích ròng theo ngưỡng xác suất, so với «can thiệp tất
              cả» và «không can thiệp» — như dcurves::dca (dương tính khi nguy cơ ≥ ngưỡng).
  fagan       toán đồ Fagan: xác suất tiền nghiệm → LR+ / LR− → xác suất hậu nghiệm.
  phan-bo     phân bố giá trị xét nghiệm theo tình trạng bệnh (hộp + chấm), có vạch điểm cắt.

Độ chính xác: test giữ giá trị chuẩn do R tính trên dữ liệu công khai — pROC::aSAH (s100b, ndka) và dcurves::df_binary;
`--kiem-cheo-r` chạy lại pROC/rms/dcurves trên chính dữ liệu của đề tài. Không có R ⇒ «không kiểm chéo được».

Ranh giới: công cụ CHỈ tính/vẽ; chọn điểm cắt dùng lâm sàng, diễn giải lợi ích ròng là quyết định của bác sĩ. Điểm cắt
Youden tối ưu hoá trên CHÍNH mẫu nên lạc quan — cần kiểm định ngoài. Cần bác sĩ kiểm chứng.

Dữ liệu vào (CSV, UTF-8): mỗi dòng một đối tượng; cột kết cục 0/1 (nhận cả TRUE/FALSE, có/không); cột điểm/xác suất.
Dòng thiếu giá trị ở cột đang dùng bị loại và đếm (in ra, ghi JSON).

Lệnh:
  python3 tools/bieu_do_chan_doan.py roc --du-lieu d.csv --ket-cuc benh --diem xn1,xn2 --ra … [--huong cao|thap]
  python3 tools/bieu_do_chan_doan.py pr --du-lieu d.csv --ket-cuc benh --diem xn1 --ra …
  python3 tools/bieu_do_chan_doan.py hieu-chuan --du-lieu d.csv --ket-cuc y --diem nguy_co --ra … [--so-nhom 10]
  python3 tools/bieu_do_chan_doan.py dca --du-lieu d.csv --ket-cuc y --diem m1,m2 --ra … [--nguong 0.01:0.50:0.01]
  python3 tools/bieu_do_chan_doan.py fagan --tien-nghiem 0.30 --lr-duong 5.2 --lr-am 0.25 --ra …
  python3 tools/bieu_do_chan_doan.py phan-bo --du-lieu d.csv --ket-cuc benh --diem xn1 --ra … [--diem-cat 0.205]
  (thêm --ngon-ngu en cho bản thảo tiếng Anh; --kiem-cheo-r để đối chiếu R)
Mã thoát: 0 xong · 1 kiểm chéo R LỆCH · 2 dữ liệu sai/thiếu · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import bieu_do_chung as BC  # noqa: E402
from bieu_do_chung import LoiBieuDo, nhan, so  # noqa: E402

Z975 = 1.959963984540054
MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")
NET = ("-", "--", "-.", ":", (0, (5, 1, 1, 1)), (0, (3, 1)))
_DUNG = {"1", "true", "yes", "co", "có", "dương", "duong", "+"}
_SAI = {"0", "false", "no", "khong", "không", "âm", "am", "-"}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. ĐỌC DỮ LIỆU
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _01(v: str, ten: str) -> int:
    s = str(v).strip().lower()
    if s in _DUNG:
        return 1
    if s in _SAI:
        return 0
    try:
        x = float(s.replace(",", "."))
    except ValueError as exc:
        raise LoiBieuDo(f"kết cục «{ten}» phải là 0/1, nhận {v!r}") from exc
    if x in (0.0, 1.0):
        return int(x)
    raise LoiBieuDo(f"kết cục «{ten}» phải là 0/1, nhận {v!r}")


def doc_du_lieu(p: Path, cot_kq: str, cot_diem: Sequence[str]) -> Dict[str, Any]:
    """Đọc CSV → {"y": array 0/1, "x": {cột: array}, "loai": số dòng bị loại vì thiếu}. Thiếu cột ⇒ lỗi rõ."""
    import numpy as np  # noqa: PLC0415

    try:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            dong = list(csv.DictReader(fh))
    except OSError as exc:
        raise LoiBieuDo(f"không đọc được {p}: {exc}") from exc
    if not dong:
        raise LoiBieuDo(f"{p}: không có dòng dữ liệu")
    thieu = [c for c in (cot_kq, *cot_diem) if c not in dong[0]]
    if thieu:
        raise LoiBieuDo(f"{p}: thiếu cột {', '.join(thieu)} (có: {', '.join(dong[0])})")
    y, xs, loai = [], {c: [] for c in cot_diem}, 0
    for r in dong:
        vals = [str(r.get(c) or "").strip() for c in (cot_kq, *cot_diem)]
        if any(v in ("", "NA", "na", "NaN", ".") for v in vals):
            loai += 1
            continue
        y.append(_01(vals[0], cot_kq))
        for c, v in zip(cot_diem, vals[1:]):
            try:
                xs[c].append(float(v.replace(",", ".")))
            except ValueError as exc:
                raise LoiBieuDo(f"cột «{c}» có giá trị không phải số: {v!r}") from exc
    ya = np.array(y, int)
    if ya.sum() == 0 or ya.sum() == len(ya):
        raise LoiBieuDo("kết cục chỉ có một giá trị — không tính được ROC/hiệu chuẩn")
    return {"y": ya, "x": {c: np.array(v, float) for c, v in xs.items()}, "loai": loai}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. ROC — AUC, DeLong (theo hạng, Sun & Xu 2014), Youden, PR
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _hang_giua(a):
    from scipy.stats import rankdata  # noqa: PLC0415

    return rankdata(a, method="average")


def _thanh_phan_delong(y, x):
    """V10 (mỗi ca bệnh) và V01 (mỗi ca chứng) — thành phần cấu trúc DeLong 1988, tính qua hạng giữa (O(N log N))."""
    import numpy as np  # noqa: PLC0415

    ca, chung = x[y == 1], x[y == 0]
    m, n = len(ca), len(chung)
    hang_tat = _hang_giua(np.concatenate([ca, chung]))
    v10 = (hang_tat[:m] - _hang_giua(ca)) / n
    v01 = 1.0 - (hang_tat[m:] - _hang_giua(chung)) / m
    return v10, v01


def delong(y, xs: Sequence[Any]) -> Dict[str, Any]:
    """AUC + ma trận hiệp phương sai DeLong cho một hoặc nhiều điểm số trên cùng đối tượng (pROC method="delong")."""
    import numpy as np  # noqa: PLC0415

    tp = [_thanh_phan_delong(y, x) for x in xs]
    m, n = int((y == 1).sum()), int((y == 0).sum())
    auc = np.array([v10.mean() for v10, _ in tp])
    V10 = np.vstack([v10 for v10, _ in tp])
    V01 = np.vstack([v01 for _, v01 in tp])
    S = np.atleast_2d(np.cov(V10)) / m + np.atleast_2d(np.cov(V01)) / n
    return {"auc": auc, "cov": S, "m": m, "n": n}


def roc_thuc_nghiem(y, x) -> Dict[str, Any]:
    """Các điểm ROC tại MỌI ngưỡng (trung điểm giữa hai giá trị liên tiếp, như pROC); dương tính khi x > ngưỡng."""
    import numpy as np  # noqa: PLC0415

    u = np.unique(x)
    nguong = np.concatenate([[-np.inf], (u[:-1] + u[1:]) / 2, [np.inf]])
    ca, chung = x[y == 1], x[y == 0]
    se = np.array([(ca > t).mean() for t in nguong])
    sp = np.array([(chung <= t).mean() for t in nguong])
    return {"nguong": nguong, "do_nhay": se, "do_dac_hieu": sp}


def youden(r: Dict[str, Any]) -> Dict[str, float]:
    """Ngưỡng tối đa hoá Se + Sp − 1 (trùng ⇒ ngưỡng đầu tiên theo chiều tăng, như pROC «best» một ngưỡng)."""
    import numpy as np  # noqa: PLC0415

    j = r["do_nhay"] + r["do_dac_hieu"] - 1
    hop = [i for i in range(len(j)) if np.isfinite(r["nguong"][i])]
    i = max(hop, key=lambda k: (round(float(j[k]), 12), -k))
    return {"nguong": float(r["nguong"][i]), "do_nhay": float(r["do_nhay"][i]),
            "do_dac_hieu": float(r["do_dac_hieu"][i]), "J": float(j[i])}


def phan_tich_roc(y, xs: Dict[str, Any], huong: str = "cao") -> Dict[str, Any]:
    """Toàn bộ số cho hình ROC: từng xét nghiệm (AUC, KTC DeLong, Youden, điểm đường cong) + so sánh cặp DeLong."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    if huong not in ("cao", "thap"):
        raise LoiBieuDo("huong: cao (giá trị cao = bệnh) | thap")
    dau = 1.0 if huong == "cao" else -1.0
    ten = list(xs)
    d = delong(y, [dau * xs[t] for t in ten])
    kq: Dict[str, Any] = {"m_benh": d["m"], "n_khong_benh": d["n"], "huong": huong, "xet_nghiem": {}, "so_sanh": []}
    for i, t in enumerate(ten):
        se_auc = math.sqrt(max(float(d["cov"][i, i]), 0.0))
        a = float(d["auc"][i])
        r = roc_thuc_nghiem(y, dau * xs[t])
        yd = youden(r)
        yd["nguong"] = dau * yd["nguong"]
        kq["xet_nghiem"][t] = {"auc": a, "se_auc": se_auc, "ktc": (max(0.0, a - Z975 * se_auc), min(1.0, a + Z975 *
                                                                                                    se_auc)),
                               "youden": yd, "fpr": (1 - r["do_dac_hieu"]).tolist(), "tpr": r["do_nhay"].tolist()}
    for i in range(len(ten)):
        for j in range(i + 1, len(ten)):
            v = float(d["cov"][i, i] + d["cov"][j, j] - 2 * d["cov"][i, j])
            z = float((d["auc"][i] - d["auc"][j]) / math.sqrt(v)) if v > 0 else float("nan")
            kq["so_sanh"].append({"a": ten[i], "b": ten[j], "chenh_auc": float(d["auc"][i] - d["auc"][j]), "z": z,
                                  "p": float(2 * stats.norm.sf(abs(z))) if np.isfinite(z) else float("nan"),
                                  "cov": float(d["cov"][i, j])})
    return kq


def precision_recall(y, x) -> Dict[str, Any]:
    """Đường PR (bậc thang) và độ chính xác trung bình AP = Σ (R_k − R_{k−1})·P_k (sắp giảm dần theo điểm)."""
    import numpy as np  # noqa: PLC0415

    thu_tu = np.argsort(-x, kind="stable")
    ys, xsx = y[thu_tu], x[thu_tu]
    cut = np.r_[np.where(np.diff(xsx) != 0)[0], len(xsx) - 1]
    tp = np.cumsum(ys)[cut]
    fp = (cut + 1) - tp
    prec = tp / (tp + fp)
    rec = tp / ys.sum()
    ap = float(np.sum(np.diff(np.r_[0.0, rec]) * prec))
    return {"precision": prec.tolist(), "recall": rec.tolist(), "ap": ap, "ty_le_hien_mac": float(y.mean())}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. HIỆU CHUẨN — như rms::val.prob
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _hoi_quy_logistic(X, y, offset=None, toi_da: int = 100):
    """IRLS có offset; trả (hệ số, ma trận hiệp phương sai)."""
    import numpy as np  # noqa: PLC0415

    off = np.zeros(len(y)) if offset is None else offset
    b = np.zeros(X.shape[1])
    for _ in range(toi_da):
        eta = X @ b + off
        mu = 1 / (1 + np.exp(-eta))
        w = np.clip(mu * (1 - mu), 1e-12, None)
        z = eta - off + (y - mu) / w
        XtW = X.T * w
        moi = np.linalg.solve(XtW @ X, XtW @ z)
        if np.max(np.abs(moi - b)) < 1e-12:
            b = moi
            break
        b = moi
    mu = 1 / (1 + np.exp(-(X @ b + off)))
    cov = np.linalg.inv((X.T * (mu * (1 - mu))) @ X)
    return b, cov


def _lowess(p, y):
    """lowess(p, y, iter = 0) của R: f = 2/3, delta = 0,01·khoảng giá trị."""
    import numpy as np  # noqa: PLC0415
    from statsmodels.nonparametric.smoothers_lowess import lowess  # noqa: PLC0415

    kq = lowess(y.astype(float), p, frac=2 / 3, it=0, delta=0.01 * float(np.ptp(p)), return_sorted=True)
    return kq[:, 0], kq[:, 1]


def hieu_chuan(y, p, so_nhom: int = 10) -> Dict[str, Any]:
    """Chỉ số hiệu chuẩn + dữ liệu vẽ. p phải trong (0, 1)."""
    import numpy as np  # noqa: PLC0415

    if np.any((p <= 0) | (p >= 1)):
        raise LoiBieuDo("xác suất dự báo phải nằm trong (0; 1) — điểm số chưa đổi sang xác suất thì không vẽ "
                        "hiệu chuẩn")
    lp = np.log(p / (1 - p))
    b, cov = _hoi_quy_logistic(np.column_stack([np.ones(len(y)), lp]), y)
    citl, cov0 = _hoi_quy_logistic(np.ones((len(y), 1)), y, offset=lp)
    lx, ly = _lowess(p, y)
    ux = np.unique(lx)
    uy = np.array([ly[lx == u].mean() for u in ux])  # approx(ties = mean)
    can = np.interp(p, ux, uy)
    er = np.abs(p - can)
    d = delong(y, [p])
    thu_tu = np.argsort(p, kind="stable")
    nhom = []
    for khoi in np.array_split(thu_tu, so_nhom):
        if len(khoi) == 0:
            continue
        k, nk = int(y[khoi].sum()), len(khoi)
        from bieu_do_gop import clopper_pearson  # noqa: PLC0415

        lo, hi = clopper_pearson(k, nk)
        nhom.append({"n": nk, "du_bao_tb": float(p[khoi].mean()), "quan_sat": k / nk, "ktc": (lo, hi)})
    return {
        "n": int(len(y)), "so_bien_co": int(y.sum()), "c": float(d["auc"][0]),
        "c_ktc": (float(d["auc"][0] - Z975 * math.sqrt(d["cov"][0, 0])),
                  float(d["auc"][0] + Z975 * math.sqrt(d["cov"][0, 0]))),
        "brier": float(np.mean((p - y) ** 2)), "e_tren_o": float(p.sum() / y.sum()),
        "citl": float(citl[0]), "citl_ktc": (float(citl[0] - Z975 * math.sqrt(cov0[0, 0])),
                                             float(citl[0] + Z975 * math.sqrt(cov0[0, 0]))),
        "chan_hieu_chuan_lai": float(b[0]), "do_doc": float(b[1]),
        "do_doc_ktc": (float(b[1] - Z975 * math.sqrt(cov[1, 1])), float(b[1] + Z975 * math.sqrt(cov[1, 1]))),
        "emax": float(er.max()), "eavg": float(er.mean()), "e90": float(np.quantile(er, 0.9)),
        "lowess": {"x": lx.tolist(), "y": ly.tolist()}, "nhom": nhom,
    }


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. DCA — lợi ích ròng (Vickers 2006), như dcurves::dca
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def loi_ich_rong(y, p, nguong: Sequence[float]) -> List[float]:
    """NB(pt) = TP/n − FP/n · pt/(1 − pt), dương tính khi p ≥ pt."""
    import numpy as np  # noqa: PLC0415

    n = len(y)
    ra = []
    for t in nguong:
        duong = p >= t
        tp = float(np.sum(duong & (y == 1)))
        fp = float(np.sum(duong & (y == 0)))
        ra.append(tp / n - fp / n * t / (1 - t))
    return ra


def dca(y, ps: Dict[str, Any], nguong: Sequence[float]) -> Dict[str, Any]:
    if any(not (0 < t < 1) for t in nguong):
        raise LoiBieuDo("ngưỡng xác suất phải trong (0; 1)")
    prev = float(y.mean())
    return {"nguong": list(nguong), "ty_le_hien_mac": prev,
            "tat_ca": [prev - (1 - prev) * t / (1 - t) for t in nguong], "khong": [0.0] * len(nguong),
            "mo_hinh": {k: loi_ich_rong(y, v, nguong) for k, v in ps.items()}}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5. FAGAN
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def hau_nghiem(tien: float, lr: float) -> float:
    if not (0 < tien < 1) or lr <= 0:
        raise LoiBieuDo("xác suất tiền nghiệm trong (0; 1), LR > 0")
    o = tien / (1 - tien) * lr
    return o / (1 + o)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6. VẼ
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _khung_vuong(ax, ngon_ngu: str, xlab: str, ylab: str) -> None:
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    BC.dinh_dang_truc(ax, ngon_ngu, "xy", nd=1)
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)


def ve_roc(y, xs: Dict[str, Any], dich: Path, huong: str = "cao", ngon_ngu: str = "vi", danh_dau_youden: bool = True,
           so_loai: int = 0) -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    kq = phan_tich_roc(y, xs, huong)
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    ax.plot([0, 1], [0, 1], color="#888888", lw=0.8, ls="--", zorder=1)
    for i, (t, r) in enumerate(kq["xet_nghiem"].items()):
        mau = MAU[i % len(MAU)]
        nhan_ct = (f"{t}: AUC = {so(r['auc'], 3, ngon_ngu)} ({nhan('ktc95', ngon_ngu)} {so(r['ktc'][0], 3, ngon_ngu)}–"
                   f"{so(r['ktc'][1], 3, ngon_ngu)})")
        ax.step(r["fpr"], r["tpr"], where="post", color=mau, lw=1.4, ls=NET[i % len(NET)], label=nhan_ct, zorder=3)
        if danh_dau_youden:
            yd = r["youden"]
            ax.plot([1 - yd["do_dac_hieu"]], [yd["do_nhay"]], marker="o", ms=6, mfc="white", mec=mau, mew=1.3, zorder=4)
            chu = (f"{so(yd['nguong'], 3, ngon_ngu)} ({BC.phan_tram(yd['do_nhay'], 0, ngon_ngu)}; "
                   f"{BC.phan_tram(yd['do_dac_hieu'], 0, ngon_ngu)})")
            ax.annotate(chu, (1 - yd["do_dac_hieu"], yd["do_nhay"]), xytext=(8, -12 - 11 * i),
                        textcoords="offset points",
                        fontsize=7.5, color=mau)
    _khung_vuong(ax, ngon_ngu, nhan("mot_tru_dac_hieu", ngon_ngu), nhan("do_nhay", ngon_ngu))
    ax.legend(loc="lower right", frameon=False, fontsize=8)
    dong = []
    for s in kq["so_sanh"]:
        dong.append(f"DeLong {s['a']} – {s['b']}: z = {so(s['z'], 2, ngon_ngu)}, {BC.p_chu(s['p'], ngon_ngu)}")
    if danh_dau_youden:
        dong.append("○ Youden: ngưỡng (độ nhạy; độ đặc hiệu)" if ngon_ngu == "vi" else
                    "○ Youden: cut-off (sensitivity; specificity)")
    if dong:
        ax.text(0.98, 0.32 + 0.0 * len(kq["xet_nghiem"]), "\n".join(dong), transform=ax.transAxes, ha="right",
                va="bottom", fontsize=7.5)
    kq.update({"loai": "roc", "ngon_ngu": ngon_ngu, "so_dong_loai_vi_thieu": so_loai,
               "ghi_chu": "AUC Mann–Whitney; KTC 95% DeLong; điểm cắt Youden tối ưu trên chính mẫu (lạc quan). "
                          "Cần bác sĩ kiểm chứng."})
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_pr(y, xs: Dict[str, Any], dich: Path, ngon_ngu: str = "vi", so_loai: int = 0) -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    fig, ax = plt.subplots(figsize=(5.4, 5.4))
    kq: Dict[str, Any] = {"loai": "pr", "xet_nghiem": {}, "so_dong_loai_vi_thieu": so_loai}
    prev = float(y.mean())
    for i, (t, x) in enumerate(xs.items()):
        r = precision_recall(y, x)
        ax.step(r["recall"], r["precision"], where="post", color=MAU[i % len(MAU)], ls=NET[i % len(NET)], lw=1.4,
                label=f"{t}: AP = {so(r['ap'], 3, ngon_ngu)}")
        kq["xet_nghiem"][t] = r
    ax.axhline(prev, color="#888888", lw=0.8, ls="--",
               label=(f"Tỷ lệ hiện mắc = {so(prev, 3, ngon_ngu)}" if ngon_ngu == "vi" else
                      f"Prevalence = {so(prev, 3, ngon_ngu)}"))
    _khung_vuong(ax, ngon_ngu, "Độ nhạy (recall)" if ngon_ngu == "vi" else "Recall (sensitivity)",
                 "Giá trị dự báo dương (precision)" if ngon_ngu == "vi" else "Precision (PPV)")
    ax.legend(loc="lower left", frameon=False, fontsize=8)
    kq["ty_le_hien_mac"] = prev
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_hieu_chuan(y, p, dich: Path, ten: str = "", so_nhom: int = 10, ngon_ngu: str = "vi",
                  so_loai: int = 0) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    h = hieu_chuan(y, p, so_nhom)
    fig = plt.figure(figsize=(5.2, 6.6))
    gs = fig.add_gridspec(2, 1, height_ratios=[4.6, 1.3], hspace=0.08)
    ax = fig.add_subplot(gs[0])
    axh = fig.add_subplot(gs[1], sharex=ax)  # cùng trục hoành với hình trên (không lệch như khi khoá tỷ lệ vuông)
    lo = 0.0
    hi = float(min(1.0, max(np.max(p), max(n["quan_sat"] for n in h["nhom"]), max(n["ktc"][1] for n in h["nhom"]))
                   * 1.05 + 0.02))
    ax.plot([lo, hi], [lo, hi], color="#888888", lw=0.8, ls="--", label="Lý tưởng" if ngon_ngu == "vi" else "Ideal")
    ax.plot(h["lowess"]["x"], h["lowess"]["y"], color="#1f4e79", lw=1.4,
            label="Đường lowess" if ngon_ngu == "vi" else "Lowess calibration")
    gx = [n["du_bao_tb"] for n in h["nhom"]]
    gy = [n["quan_sat"] for n in h["nhom"]]
    ax.errorbar(gx, gy, yerr=[[a - n["ktc"][0] for a, n in zip(gy, h["nhom"])],
                              [n["ktc"][1] - a for a, n in zip(gy, h["nhom"])]],
                fmt="s", ms=4, color="#a23b2a", ecolor="#a23b2a", elinewidth=0.8, capsize=2.5,
                label=(f"{len(h['nhom'])} nhóm theo nguy cơ dự báo (KTC 95%)" if ngon_ngu == "vi" else
                       f"{len(h['nhom'])} risk groups (95% CI)"))
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.tick_params(labelbottom=False)
    ax.set_ylabel("Tỷ lệ quan sát" if ngon_ngu == "vi" else "Observed proportion")
    BC.dinh_dang_truc(ax, ngon_ngu, "y", nd=1)
    v = lambda x, nd=2: so(x, nd, ngon_ngu)  # noqa: E731
    chu = [f"C = {v(h['c'], 3)} ({v(h['c_ktc'][0], 3)}–{v(h['c_ktc'][1], 3)})",
           f"Brier = {v(h['brier'], 3)}", f"E/O = {v(h['e_tren_o'])}",
           ("Chặn hiệu chuẩn (CITL)" if ngon_ngu == "vi" else "Calibration-in-the-large")
           + f" = {v(h['citl'])} ({v(h['citl_ktc'][0])}; {v(h['citl_ktc'][1])})",
           (f"Độ dốc hiệu chuẩn = {v(h['do_doc'])} ({v(h['do_doc_ktc'][0])}; {v(h['do_doc_ktc'][1])})" if ngon_ngu ==
            "vi" else f"Calibration slope = {v(h['do_doc'])} ({v(h['do_doc_ktc'][0])}; {v(h['do_doc_ktc'][1])})"),
           f"Emax = {v(h['emax'], 3)}; Eavg = {v(h['eavg'], 3)}"]
    ax.text(0.03, 0.97, "\n".join(chu), transform=ax.transAxes, va="top", fontsize=7.6)
    ax.legend(loc="lower right", frameon=False, fontsize=7.6)
    if ten:
        ax.set_title(ten)
    # dải dưới: phân bố nguy cơ dự báo — kết cục 1 lên trên, 0 xuống dưới; MỖI nhóm chuẩn hoá theo cột cao nhất của
    # nhóm đó (nhóm hiếm biến cố không bị nhóm đông «đè» thành vạch phẳng)
    bins = np.linspace(lo, hi, 51)
    c1, _ = np.histogram(p[y == 1], bins)
    c0, _ = np.histogram(p[y == 0], bins)
    w = bins[1] - bins[0]
    axh.bar(bins[:-1], c1 / max(c1.max(), 1), width=w, align="edge", color="#444444")
    axh.bar(bins[:-1], -c0 / max(c0.max(), 1), width=w, align="edge", color="#aaaaaa")
    axh.axhline(0, color="#222222", lw=0.6)
    axh.set_ylim(-1.15, 1.15)
    axh.set_yticks([])
    axh.spines["left"].set_visible(False)
    vi = ngon_ngu == "vi"
    axh.text(0.99, 0.98, (f"kết cục = 1 (n = {int(y.sum())})" if vi else f"outcome = 1 (n = {int(y.sum())})"),
             transform=axh.transAxes, ha="right", va="top", fontsize=7)
    axh.text(0.99, 0.02, (f"kết cục = 0 (n = {int((y == 0).sum())})" if vi else
                          f"outcome = 0 (n = {int((y == 0).sum())})"), transform=axh.transAxes, ha="right", va="bottom",
             fontsize=7)
    BC.dinh_dang_truc(axh, ngon_ngu, "x", nd=1)
    axh.set_xlabel("Nguy cơ dự báo" if ngon_ngu == "vi" else "Predicted risk")
    h.update({"loai": "hieu_chuan", "ngon_ngu": ngon_ngu, "so_dong_loai_vi_thieu": so_loai,
              "ghi_chu": "Chỉ số như rms::val.prob; CITL ước lượng với độ dốc cố định 1 (offset). Hiệu chuẩn trên "
                         "chính mẫu phát triển mô hình luôn đẹp — cần kiểm định nội (bootstrap) hoặc ngoài. Cần bác sĩ "
                         "kiểm chứng."})
    BC.luu(fig, dich, so_lieu=h)
    return h


def ve_dca(y, ps: Dict[str, Any], nguong: Sequence[float], dich: Path, ngon_ngu: str = "vi",
           so_loai: int = 0) -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    d = dca(y, ps, nguong)
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    ax.plot(nguong, d["tat_ca"], color="#999999", lw=1.0,
            label="Can thiệp tất cả" if ngon_ngu == "vi" else "Treat all")
    ax.plot(nguong, d["khong"], color="#222222", lw=1.0,
            label="Không can thiệp" if ngon_ngu == "vi" else "Treat none")
    for i, (k, nb) in enumerate(d["mo_hinh"].items()):
        ax.plot(nguong, nb, color=MAU[i % len(MAU)], ls=NET[i % len(NET)], lw=1.5, label=k)
    prev = d["ty_le_hien_mac"]
    ax.set_ylim(-0.05 * max(prev, 0.2), prev * 1.08)
    ax.set_xlim(min(nguong), max(nguong))
    BC.dinh_dang_truc(ax, ngon_ngu, "xy")
    ax.set_xlabel("Ngưỡng xác suất" if ngon_ngu == "vi" else "Threshold probability")
    ax.set_ylabel("Lợi ích ròng" if ngon_ngu == "vi" else "Net benefit")
    ax.legend(frameon=False, fontsize=8, loc="upper right")
    d.update({"loai": "dca", "ngon_ngu": ngon_ngu, "so_dong_loai_vi_thieu": so_loai,
              "ghi_chu": "Lợi ích ròng = TP/n − FP/n·pt/(1−pt), dương tính khi nguy cơ ≥ ngưỡng (Vickers 2006). Khoảng "
                         "ngưỡng hợp lý do bác sĩ chọn theo bối cảnh lâm sàng. Cần bác sĩ kiểm chứng."})
    BC.luu(fig, dich, so_lieu=d)
    return d


def ve_fagan(tien: float, lr_duong: Optional[float], lr_am: Optional[float], dich: Path,
             ngon_ngu: str = "vi") -> Dict[str, Any]:
    """Toán đồ Fagan: trục trái −logit(tiền nghiệm), giữa log(LR)/2, phải logit(hậu nghiệm) — đường thẳng qua hai
    điểm đầu luôn cắt trục phải đúng xác suất hậu nghiệm (vì logit hậu = logit tiền + log LR)."""
    BC.kiem_ngon_ngu(ngon_ngu)
    if lr_duong is None and lr_am is None:
        raise LoiBieuDo("cần ít nhất LR+ hoặc LR−")
    plt = BC.plt_chuan()
    lg = lambda q: math.log(q / (1 - q))  # noqa: E731
    fig, ax = plt.subplots(figsize=(4.6, 6.2))
    xs = (-1.0, 0.0, 1.0)
    for x in xs:
        ax.plot([x, x], [-7.6, 7.6], color="#222222", lw=0.8)
    pct = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.99, 0.995, 0.999]
    for q in pct:
        ax.plot([-1.04, -1.0], [-lg(q)] * 2, color="#222222", lw=0.6)
        ax.text(-1.07, -lg(q), BC.so(100 * q, 1 if q < 0.01 or q > 0.99 else 0, ngon_ngu).rstrip("0").rstrip(",.")
                if q < 0.01 or q > 0.99 else BC.so(100 * q, 0, ngon_ngu), ha="right", va="center", fontsize=7)
        ax.plot([1.0, 1.04], [lg(q)] * 2, color="#222222", lw=0.6)
        ax.text(1.07, lg(q), BC.so(100 * q, 1 if q < 0.01 or q > 0.99 else 0, ngon_ngu).rstrip("0").rstrip(",.")
                if q < 0.01 or q > 0.99 else BC.so(100 * q, 0, ngon_ngu), ha="left", va="center", fontsize=7)
    for lr in (0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000):
        yv = math.log(lr) / 2
        ax.plot([-0.03, 0.03], [yv, yv], color="#222222", lw=0.6)
        ax.text(0.05, yv, f"{lr:g}".replace(".", "," if ngon_ngu == "vi" else "."), ha="left", va="center", fontsize=7)
    kq: Dict[str, Any] = {"loai": "fagan", "tien_nghiem": tien}
    for lr, ten, mau, net in ((lr_duong, "LR+", "#a23b2a", "-"), (lr_am, "LR−", "#1f4e79", "--")):
        if lr is None:
            continue
        post = hau_nghiem(tien, lr)
        ax.plot([-1, 1], [-lg(tien), lg(post)], color=mau, lw=1.4, ls=net,
                label=(f"{ten} = {so(lr, 2, ngon_ngu)} → {BC.phan_tram(post, 1, ngon_ngu)}"))
        kq["lr_duong" if ten == "LR+" else "lr_am"] = {"lr": lr, "hau_nghiem": post}
    ax.set_xlim(-1.7, 1.7)
    ax.set_ylim(-7.8, 7.8)
    ax.axis("off")
    vi = ngon_ngu == "vi"
    ax.text(-1, 8.1, "Xác suất\ntiền nghiệm (%)" if vi else "Pre-test\nprobability (%)", ha="center", va="bottom",
            fontsize=8.5)
    ax.text(0, 8.1, "Tỷ số\nkhả dĩ" if vi else "Likelihood\nratio", ha="center", va="bottom", fontsize=8.5)
    ax.text(1, 8.1, "Xác suất\nhậu nghiệm (%)" if vi else "Post-test\nprobability (%)", ha="center", va="bottom",
            fontsize=8.5)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, -0.1), frameon=False, fontsize=8)
    kq["ghi_chu"] = "Hậu nghiệm = odds tiền nghiệm × LR. Cần bác sĩ kiểm chứng."
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_phan_bo(y, x, ten: str, dich: Path, diem_cat: Optional[float] = None, ngon_ngu: str = "vi",
               nhan_nhom: Tuple[str, str] = ("", ""), so_loai: int = 0) -> Dict[str, Any]:
    """Hộp (trung vị, tứ phân vị, râu 1,5·IQR) + mọi chấm (rung tất định, không ngẫu nhiên) theo tình trạng bệnh."""
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    n0, n1 = nhan_nhom[0] or ("Không bệnh" if vi else "Non-diseased"), nhan_nhom[1] or ("Bệnh" if vi else "Diseased")
    fig, ax = plt.subplots(figsize=(4.4, 4.6))
    du = [x[y == 0], x[y == 1]]
    ax.boxplot(du, positions=[1, 2], widths=0.45, showfliers=False, medianprops={"color": "#222222", "lw": 1.2},
               boxprops={"lw": 0.8}, whiskerprops={"lw": 0.8}, capprops={"lw": 0.8})
    tk = {}
    for i, v in enumerate(du):
        rung = ((np.arange(len(v)) * 0.618034) % 1 - 0.5) * 0.32  # rung tất định (tỷ lệ vàng) — hình tái lập được
        ax.scatter(i + 1 + rung, v, s=8, color=MAU[i], alpha=0.55, lw=0, zorder=3)
        q1, md, q3 = np.percentile(v, [25, 50, 75])
        tk[(n0, n1)[i]] = {"n": int(len(v)), "trung_vi": float(md), "q1": float(q1), "q3": float(q3)}
    if diem_cat is not None:
        ax.axhline(diem_cat, color="#a23b2a", lw=0.9, ls="--")
        ax.text(2.45, diem_cat, f"{'Điểm cắt' if vi else 'Cut-off'} {so(diem_cat, 3, ngon_ngu)}", va="bottom",
                ha="right", fontsize=7.5, color="#a23b2a")
    ax.set_xticks([1, 2])
    ax.set_xticklabels([f"{n0}\n(n = {len(du[0])})", f"{n1}\n(n = {len(du[1])})"])
    ax.set_ylabel(ten)
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    kq = {"loai": "phan_bo", "nhom": tk, "diem_cat": diem_cat, "so_dong_loai_vi_thieu": so_loai}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 7. KIỂM CHÉO R
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def kiem_cheo_roc_r(y, xs: Dict[str, Any], huong: str = "cao") -> Dict[str, Any]:
    kq = phan_tich_roc(y, xs, huong)
    ten = list(xs)
    huong_r = "<" if huong == "cao" else ">"
    dong = ["suppressMessages(library(pROC))", f"y <- {BC.r_vec(y)}"]
    py: Dict[str, float] = {}
    for i, t in enumerate(ten):
        r = kq["xet_nghiem"][t]
        dong += [f"x{i} <- {BC.r_vec(xs[t])}",
                 f'r{i} <- roc(y, x{i}, levels=c(0,1), direction="{huong_r}", quiet=TRUE)',
                 f'c{i} <- ci.auc(r{i}, method="delong")',
                 f'cat("KQ auc{i}", auc(r{i}), "\\n"); cat("KQ lo{i}", c{i}[1], "\\n")',
                 f'cat("KQ hi{i}", c{i}[3], "\\n")',
                 f'b{i} <- coords(r{i}, "best", best.method="youden", ret=c("threshold","sensitivity","specificity"))',
                 f'if (nrow(b{i}) == 1) {{ cat("KQ ng{i}", b{i}$threshold, "\\n"); '
                 f'cat("KQ se{i}", b{i}$sensitivity, "\\n"); cat("KQ sp{i}", b{i}$specificity, "\\n") }}']
        py.update({f"auc{i}": r["auc"], f"lo{i}": r["ktc"][0], f"hi{i}": r["ktc"][1], f"ng{i}": r["youden"]["nguong"],
                   f"se{i}": r["youden"]["do_nhay"], f"sp{i}": r["youden"]["do_dac_hieu"]})
    for s in kq["so_sanh"]:
        i, j = ten.index(s["a"]), ten.index(s["b"])
        dong.append(f't{i}{j} <- roc.test(r{i}, r{j}, method="delong"); cat("KQ p{i}{j}", t{i}{j}$p.value, "\\n")')
        py[f"p{i}{j}"] = s["p"]
    r_kq = BC.chay_r_kiem_cheo("\n".join(dong) + "\n")
    # pROC chỉ in một ngưỡng khi «best» không trùng; nếu R trả nhiều ngưỡng (trùng J) thì bỏ so ngưỡng
    for i in range(len(ten)):
        if r_kq.get("trang_thai") == "da_chay" and f"ng{i}" not in r_kq["kq"]:
            for k in (f"ng{i}", f"se{i}", f"sp{i}"):
                py.pop(k, None)
    return BC.doi_chieu(py, r_kq, dung_sai=1e-6)


def kiem_cheo_hieu_chuan_r(y, p) -> Dict[str, Any]:
    h = hieu_chuan(y, p)
    ma = f"""suppressMessages(library(rms))
y <- {BC.r_vec(y)}; p <- {BC.r_vec(p)}
v <- val.prob(p, y, pl=FALSE)
cat("KQ c", v["C (ROC)"], "\\n"); cat("KQ brier", v["Brier"], "\\n"); cat("KQ chan", v["Intercept"], "\\n")
cat("KQ doc", v["Slope"], "\\n"); cat("KQ emax", v["Emax"], "\\n"); cat("KQ eavg", v["Eavg"], "\\n")
cat("KQ citl", coef(glm(y ~ offset(qlogis(p)), family=binomial))[1], "\\n")
"""
    py = {"c": h["c"], "brier": h["brier"], "chan": h["chan_hieu_chuan_lai"], "doc": h["do_doc"], "emax": h["emax"],
          "eavg": h["eavg"], "citl": h["citl"]}
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-5)


def kiem_cheo_dca_r(y, ps: Dict[str, Any], nguong: Sequence[float]) -> Dict[str, Any]:
    d = dca(y, ps, nguong)
    ten = list(ps)
    cot = ", ".join(f"m{i} = {BC.r_vec(ps[t])}" for i, t in enumerate(ten))
    ma = (f"suppressMessages(library(dcurves))\nd <- data.frame(y = {BC.r_vec(y)}, {cot})\n"
          f"x <- as.data.frame(dca(y ~ {' + '.join(f'm{i}' for i in range(len(ten)))}, data=d, "
          f"thresholds={BC.r_vec(nguong)})$dca)\n"
          "for (i in seq_len(nrow(x))) cat('KQ', paste0(x$variable[i], '_', format(x$threshold[i], nsmall=4)), "
          "x$net_benefit[i], '\\n')\n")
    py: Dict[str, float] = {}
    for k, t in enumerate(nguong):
        nhan_t = f"{t:.4f}"
        py[f"all_{nhan_t}"] = d["tat_ca"][k]
        for i, ten_m in enumerate(ten):
            py[f"m{i}_{nhan_t}"] = d["mo_hinh"][ten_m][k]
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-9)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 8. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _nguong(s: str) -> List[float]:
    try:
        a, b, c = (float(x) for x in s.split(":"))
    except ValueError as exc:
        raise LoiBieuDo("--nguong dạng bắt_đầu:kết_thúc:bước, ví dụ 0.01:0.50:0.01") from exc
    if c <= 0 or not (0 < a <= b < 1):
        raise LoiBieuDo("--nguong phải trong (0; 1) và bước > 0")
    n = int(round((b - a) / c)) + 1
    return [round(a + i * c, 10) for i in range(n)]


def main(argv: Optional[Sequence[str]] = None) -> int:
    from bieu_do_gop import _in_kiem_cheo  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("roc", "pr", "hieu-chuan", "dca", "fagan", "phan-bo"))
    ap.add_argument("--du-lieu", type=Path)
    ap.add_argument("--ket-cuc")
    ap.add_argument("--diem", help="một hoặc nhiều cột, cách nhau dấu phẩy")
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--huong", default="cao", choices=("cao", "thap"))
    ap.add_argument("--so-nhom", type=int, default=10)
    ap.add_argument("--nguong", default="0.01:0.50:0.01")
    ap.add_argument("--tien-nghiem", type=float)
    ap.add_argument("--lr-duong", type=float)
    ap.add_argument("--lr-am", type=float)
    ap.add_argument("--diem-cat", type=float)
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    ap.add_argument("--khong-youden", action="store_true")
    ap.add_argument("--kiem-cheo-r", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        if a.lenh == "fagan":
            if a.tien_nghiem is None:
                print("❌ fagan cần --tien-nghiem")
                return 3
            kq = ve_fagan(a.tien_nghiem, a.lr_duong, a.lr_am, a.ra, a.ngon_ngu)
            for k in ("lr_duong", "lr_am"):
                if k in kq:
                    print(f"✅ {k}: {so(kq[k]['lr'], 2)} → hậu nghiệm {BC.phan_tram(kq[k]['hau_nghiem'], 1)}")
            print(f"   → {a.ra.with_suffix('.png')}\nCần bác sĩ kiểm chứng.")
            return 0
        if not (a.du_lieu and a.ket_cuc and a.diem):
            print("❌ cần --du-lieu, --ket-cuc, --diem")
            return 3
        cot = [c.strip() for c in a.diem.split(",") if c.strip()]
        d = doc_du_lieu(a.du_lieu, a.ket_cuc, cot)
        y, xs, loai = d["y"], d["x"], d["loai"]
        if loai:
            print(f"   ⚠ loại {loai} dòng thiếu giá trị ở cột đang dùng")
        ma_kc = 0
        if a.lenh == "roc":
            kq = ve_roc(y, xs, a.ra, a.huong, a.ngon_ngu, not a.khong_youden, loai)
            for t, r in kq["xet_nghiem"].items():
                yd = r["youden"]
                print(f"✅ {t}: AUC = {so(r['auc'], 3)} [{so(r['ktc'][0], 3)}; {so(r['ktc'][1], 3)}] · Youden "
                      f"{so(yd['nguong'], 3)} (Se {BC.phan_tram(yd['do_nhay'], 1)}, "
                      f"Sp {BC.phan_tram(yd['do_dac_hieu'], 1)})")
            for s in kq["so_sanh"]:
                print(f"   DeLong {s['a']} – {s['b']}: z = {so(s['z'], 2)}, {BC.p_chu(s['p'])}")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("ROC (pROC)", kiem_cheo_roc_r(y, xs, a.huong))
        elif a.lenh == "pr":
            kq = ve_pr(y, xs, a.ra, a.ngon_ngu, loai)
            for t, r in kq["xet_nghiem"].items():
                print(f"✅ {t}: AP = {so(r['ap'], 3)}")
        elif a.lenh == "hieu-chuan":
            if len(cot) != 1:
                print("❌ hieu-chuan nhận đúng MỘT cột xác suất dự báo")
                return 3
            h = ve_hieu_chuan(y, xs[cot[0]], a.ra, cot[0], a.so_nhom, a.ngon_ngu, loai)
            print(f"✅ C = {so(h['c'], 3)} · Brier = {so(h['brier'], 3)} · CITL = {so(h['citl'], 2)} · độ dốc = "
                  f"{so(h['do_doc'], 2)} · E/O = {so(h['e_tren_o'], 2)}")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("hiệu chuẩn (rms::val.prob)", kiem_cheo_hieu_chuan_r(y, xs[cot[0]]))
        elif a.lenh == "dca":
            ng = _nguong(a.nguong)
            ve_dca(y, xs, ng, a.ra, a.ngon_ngu, loai)
            print(f"✅ DCA: {len(xs)} mô hình × {len(ng)} ngưỡng")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("DCA (dcurves)", kiem_cheo_dca_r(y, xs, ng[:: max(1, len(ng) // 10)]))
        else:
            if len(cot) != 1:
                print("❌ phan-bo nhận đúng MỘT cột")
                return 3
            ve_phan_bo(y, xs[cot[0]], cot[0], a.ra, a.diem_cat, a.ngon_ngu, so_loai=loai)
            print("✅ phân bố theo tình trạng bệnh")
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return ma_kc


if __name__ == "__main__":
    sys.exit(main())
