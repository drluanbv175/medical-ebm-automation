#!/usr/bin/env python3
"""Biểu đồ PHÂN TÍCH GỘP — tính đúng và vẽ đúng chuẩn công bố (bác sĩ 21/11/2026, kèm ảnh «Summary ROC plots of the
BSDS, HCL-32 and MDQ»: «không chỉ riêng biểu đồ SROC mà phải thực hiện được tất cả biểu đồ một cách chi tiết và chính
xác nhất»).

Trước bản này, agent `meta-phan-tich` ghi rõ «Forest/funnel plot: KHÔNG có công cụ tự động nào trong hệ thống»;
`meta_analysis_calc.py` chỉ tính số; không có gì cho phân tích gộp ĐỘ CHÍNH XÁC CHẨN ĐOÁN (SROC/mô hình hai biến).

Họ biểu đồ (mỗi lệnh ghi PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  forest      forest plot: từng nghiên cứu (ô vuông ∝ trọng số, KTC 95%), kim cương gộp, KHOẢNG DỰ BÁO 95%
              (t với k−2 bậc tự do — IntHout 2016), dòng không đồng nhất (τ², I², Q, p), kiểm định hiệu ứng chung,
              phân nhóm (kim cương từng nhóm + kiểm định khác biệt giữa nhóm), cột n/N hai nhánh khi có dữ liệu 2×2.
  pheu        funnel plot: đường giả-KTC 95% quanh ước lượng gộp, tuỳ chọn ĐƯỜNG VIỀN ý nghĩa (contour-enhanced,
              Peters 2008), kiểm định Egger (hồi quy có trọng số), trim-and-fill (Duval–Tweedie L0, cùng thuật toán
              metafor::trimfill) với nghiên cứu bù vẽ chấm rỗng.
  bo-tung-nc  phân tích bỏ-từng-nghiên-cứu (leave-one-out) dạng forest.
  dta-forest  forest CẶP độ nhạy / độ đặc hiệu (coupled forest) — TP, FP, FN, TN, KTC 95% chính xác Clopper–Pearson.
  sroc        SROC theo MÔ HÌNH HAI BIẾN (Reitsma 2005, REML): điểm tóm tắt, vùng tin cậy 95%, vùng dự báo 95%,
              đường SROC kiểu Rutter–Gatsonis (Harbord 2007) CHỈ trong khoảng 1 − độ đặc hiệu quan sát được, chấm
              nghiên cứu ∝ cỡ mẫu; nhiều xét nghiệm/nhóm trên cùng một hình (như ảnh bác sĩ gửi); LR+, LR−, DOR
              kèm KTC (phương pháp delta).
  deeks       funnel Deeks cho sai lệch công bố của nghiên cứu chẩn đoán (Deeks 2005): ln DOR theo 1/√ESS.

Độ chính xác: các phép tính được ĐỐI CHIẾU với R (metafor::rma, rma.mv, trimfill, regtest) — test giữ giá trị chuẩn
do metafor 5.0.1 tính trên dat.bcg và dat.kearon1998 (gói metadat), và `--kiem-cheo-r` chạy lại R trên chính dữ liệu
của đề tài. Không có R ⇒ «không kiểm chéo được» (không bao giờ báo khớp).

Ranh giới: công cụ CHỈ vẽ/tính trên số liệu đã trích xuất; quyết định có nên gộp (đồng nhất lâm sàng–phương pháp),
chọn mô hình, diễn giải là việc của agent `meta-phan-tich` và bác sĩ. Cần bác sĩ kiểm chứng.

Dữ liệu vào (CSV, UTF-8):
  forest/pheu/bo-tung-nc: cột `nghien_cuu` + MỘT bộ: (`yi`,`vi`) | (`yi`,`sei`) | (`su_kien_1`,`tong_1`,`su_kien_2`,
      `tong_2`) cho OR/RR/RD | (`tb_1`,`dlc_1`,`n_1`,`tb_2`,`dlc_2`,`n_2`) cho MD/SMD | (`hr`,`duoi`,`tren`) cho HR;
      tuỳ chọn `nhom` (phân nhóm), `nam`.
  dta-forest/sroc/deeks: `nghien_cuu`,`tp`,`fp`,`fn`,`tn`; tuỳ chọn `nhom` (xét nghiệm hoặc phân nhóm), `nam`.

Lệnh:
  python3 tools/bieu_do_gop.py forest --du-lieu gop.csv --do RR --ra exports/<mã>/bieu-bang/forest
      [--phuong-phap REML|DL|FE] [--hk] [--ngon-ngu vi|en] [--nhan-trai "Ưu thế can thiệp"]
      [--nhan-phai "Ưu thế chứng"] [--kiem-cheo-r]
  python3 tools/bieu_do_gop.py pheu --du-lieu gop.csv --do RR --ra … [--duong-vien] [--trim-fill] [--kiem-cheo-r]
  python3 tools/bieu_do_gop.py bo-tung-nc --du-lieu gop.csv --do RR --ra …
  python3 tools/bieu_do_gop.py dta-forest --du-lieu dta.csv --ra …
  python3 tools/bieu_do_gop.py sroc --du-lieu dta.csv --ra … [--duong rutter-gatsonis|reitsma] [--kiem-cheo-r]
  python3 tools/bieu_do_gop.py deeks --du-lieu dta.csv --ra …
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
TY_SO = ("OR", "RR", "HR")  # vẽ trên trục log, giá trị không hiệu ứng = 1
TEN_DO = {
    "OR": {"vi": "Tỷ số chênh", "en": "Odds ratio"},
    "RR": {"vi": "Nguy cơ tương đối", "en": "Risk ratio"},
    "HR": {"vi": "Tỷ số nguy cơ tức thời", "en": "Hazard ratio"},
    "RD": {"vi": "Hiệu số nguy cơ", "en": "Risk difference"},
    "MD": {"vi": "Hiệu số trung bình", "en": "Mean difference"},
    "SMD": {"vi": "Hiệu số trung bình chuẩn hoá (Hedges g)", "en": "Standardised mean difference (Hedges g)"},
    "GEN": {"vi": "Cỡ hiệu ứng", "en": "Effect size"},
}
MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")
DAU = ("o", "s", "D", "^", "v", "P")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. CỠ HIỆU ỨNG — cùng công thức metafor::escalc (để đối chiếu R khớp tới số lẻ)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _f(x: Any, ten: str) -> float:
    try:
        v = float(str(x).strip().replace(",", "."))
    except (TypeError, ValueError) as exc:
        raise LoiBieuDo(f"«{ten}» không phải số: {x!r}") from exc
    if math.isnan(v):
        raise LoiBieuDo(f"«{ten}» trống")
    return v


def co_hieu_ung(dong: Dict[str, Any], do: str) -> Optional[Dict[str, Any]]:
    """Một dòng CSV → {yi, vi, n1/N1…}. Hai nhánh đều 0 sự kiện (OR/RR) ⇒ None (loại khỏi gộp — Cochrane Handbook
    10.4.4.2). Ô bằng 0 ⇒ cộng 0,5 vào cả bốn ô của nghiên cứu đó (escalc mặc định add=1/2, to="only0")."""
    ten = str(dong.get("nghien_cuu") or "").strip() or "?"
    if dong.get("yi") not in (None, ""):
        yi = _f(dong["yi"], f"{ten}: yi")
        if dong.get("vi") not in (None, ""):
            vi = _f(dong["vi"], f"{ten}: vi")
        elif dong.get("sei") not in (None, ""):
            vi = _f(dong["sei"], f"{ten}: sei") ** 2
        else:
            raise LoiBieuDo(f"{ten}: có yi nhưng thiếu vi/sei")
        if vi <= 0:
            raise LoiBieuDo(f"{ten}: phương sai phải > 0")
        return {"yi": yi, "vi": vi}
    if do in ("OR", "RR", "RD"):
        a, n1 = _f(dong.get("su_kien_1"), f"{ten}: su_kien_1"), _f(dong.get("tong_1"), f"{ten}: tong_1")
        c, n2 = _f(dong.get("su_kien_2"), f"{ten}: su_kien_2"), _f(dong.get("tong_2"), f"{ten}: tong_2")
        if not (0 <= a <= n1 and 0 <= c <= n2 and n1 > 0 and n2 > 0):
            raise LoiBieuDo(f"{ten}: sự kiện phải trong [0, tổng]")
        b, d = n1 - a, n2 - c
        goc = {"su_kien_1": int(a), "tong_1": int(n1), "su_kien_2": int(c), "tong_2": int(n2)}
        if do == "RD":
            p1, p2 = a / n1, c / n2
            vi = p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2
            if vi <= 0:
                raise LoiBieuDo(f"{ten}: phương sai hiệu số nguy cơ = 0 (cả hai nhánh 0% hoặc 100%)")
            return {"yi": p1 - p2, "vi": vi, **goc}
        if (a == 0 and c == 0) or (b == 0 and d == 0):
            return None
        if 0 in (a, b, c, d):
            a, b, c, d = a + 0.5, b + 0.5, c + 0.5, d + 0.5
        if do == "OR":
            return {"yi": math.log(a * d / (b * c)), "vi": 1 / a + 1 / b + 1 / c + 1 / d, **goc}
        n1c, n2c = a + b, c + d
        return {"yi": math.log((a / n1c) / (c / n2c)), "vi": 1 / a - 1 / n1c + 1 / c - 1 / n2c, **goc}
    if do in ("MD", "SMD"):
        m1, s1, n1 = (_f(dong.get(k), f"{ten}: {k}") for k in ("tb_1", "dlc_1", "n_1"))
        m2, s2, n2 = (_f(dong.get(k), f"{ten}: {k}") for k in ("tb_2", "dlc_2", "n_2"))
        if min(n1, n2) < 2 or min(s1, s2) < 0:
            raise LoiBieuDo(f"{ten}: n ≥ 2 và ĐLC ≥ 0")
        goc = {"n_1": int(n1), "n_2": int(n2)}
        if do == "MD":
            return {"yi": m1 - m2, "vi": s1 ** 2 / n1 + s2 ** 2 / n2, **goc}
        df = n1 + n2 - 2
        sp = math.sqrt(((n1 - 1) * s1 ** 2 + (n2 - 1) * s2 ** 2) / df)
        if sp == 0:
            raise LoiBieuDo(f"{ten}: ĐLC gộp = 0 ⇒ SMD vô định")
        j = math.exp(math.lgamma(df / 2) - math.log(math.sqrt(df / 2)) - math.lgamma((df - 1) / 2))  # J chính xác
        g = j * (m1 - m2) / sp
        return {"yi": g, "vi": 1 / n1 + 1 / n2 + g ** 2 / (2 * (n1 + n2)), **goc}
    if do == "HR":
        hr, lo, hi = (_f(dong.get(k), f"{ten}: {k}") for k in ("hr", "duoi", "tren"))
        if not (0 < lo < hr < hi):
            raise LoiBieuDo(f"{ten}: cần 0 < dưới < HR < trên")
        se = (math.log(hi) - math.log(lo)) / (2 * Z975)
        return {"yi": math.log(hr), "vi": se ** 2}
    raise LoiBieuDo(f"{ten}: thiếu cột cho thước đo {do} (xem docstring)")


def doc_csv(p: Path) -> List[Dict[str, str]]:
    try:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            dong = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    except OSError as exc:
        raise LoiBieuDo(f"không đọc được {p}: {exc}") from exc
    if not dong:
        raise LoiBieuDo(f"{p}: không có dòng dữ liệu")
    return dong


def chuan_bi_gop(dong: Sequence[Dict[str, Any]], do: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Trả (nghiên cứu dùng được, ghi chú loại). Mỗi phần tử có nghien_cuu, nhom, yi, vi, sei."""
    ra, loai = [], []
    for r in dong:
        ten = str(r.get("nghien_cuu") or "").strip()
        if not ten:
            raise LoiBieuDo("thiếu tên nghiên cứu (cột nghien_cuu)")
        e = co_hieu_ung(r, do)
        if e is None:
            loai.append(f"{ten}: cả hai nhánh 0 sự kiện — loại khỏi gộp")
            continue
        e.update({"nghien_cuu": ten, "nhom": str(r.get("nhom") or "").strip(), "sei": math.sqrt(e["vi"])})
        if r.get("nam"):
            e["nam"] = str(r["nam"]).strip()
        ra.append(e)
    if len(ra) < 2:
        raise LoiBieuDo(f"chỉ còn {len(ra)} nghiên cứu dùng được — không gộp")
    return ra, loai


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. GỘP MỘT BIẾN — FE · DL · REML (Fisher scoring, như metafor) · Hartung–Knapp · khoảng dự báo
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _wls(y, v, X, tau2):
    import numpy as np  # noqa: PLC0415

    w = 1.0 / (v + tau2)
    XtW = X.T * w
    Ainv = np.linalg.inv(XtW @ X)
    return w, Ainv @ (XtW @ y), Ainv


def tau2_reml(y, v, X, toi_da: int = 500, sai_so: float = 1e-12) -> float:
    """τ² REML bằng Fisher scoring: τ² += (y'PPy − tr P) / tr(PP), P = W − WX(X'WX)⁻¹X'W; kẹp ở 0 (như metafor)."""
    import numpy as np  # noqa: PLC0415

    k, p = X.shape
    _, b0, _ = _wls(y, v, X, 0.0)
    r0 = y - X @ b0
    tau2 = max(0.0, float(r0 @ r0) / (k - p) - float(np.mean(v)))
    for _ in range(toi_da):
        w = 1.0 / (v + tau2)
        WX = X * w[:, None]
        P = np.diag(w) - WX @ np.linalg.inv(X.T @ WX) @ WX.T
        Py = P @ y
        moi = max(0.0, tau2 + (float(Py @ Py) - float(np.trace(P))) / float(np.trace(P @ P)))
        if abs(moi - tau2) < sai_so:
            return moi
        tau2 = moi
    return tau2


def gop(yi: Sequence[float], vi: Sequence[float], phuong_phap: str = "REML", hk: bool = False,
        muc: float = 0.95) -> Dict[str, Any]:
    """Gộp nghịch đảo phương sai. Trả mu, se, KTC, z/t, p, τ², I² (theo τ² — như metafor), H², Q, df, p_Q,
    khoảng dự báo (k ≥ 3, t_{k−2} — IntHout 2016), trọng số %, ước lượng hiệu ứng cố định đi kèm."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    y, v = np.asarray(yi, float), np.asarray(vi, float)
    k = len(y)
    if k < 2 or np.any(v <= 0):
        raise LoiBieuDo("cần ≥ 2 nghiên cứu, phương sai > 0")
    pp = phuong_phap.upper()
    if pp not in ("FE", "DL", "REML"):
        raise LoiBieuDo("phuong_phap phải là FE/DL/REML")
    wf = 1 / v
    mu_fe = float(np.sum(wf * y) / np.sum(wf))
    Q = float(np.sum(wf * (y - mu_fe) ** 2))
    df = k - 1
    c = float(np.sum(wf) - np.sum(wf ** 2) / np.sum(wf))
    if pp == "FE":
        tau2 = 0.0
    elif pp == "DL":
        tau2 = max(0.0, (Q - df) / c)
    else:
        tau2 = tau2_reml(y, v, np.ones((k, 1)))
    w = 1 / (v + tau2)
    mu = float(np.sum(w * y) / np.sum(w))
    se = math.sqrt(1 / float(np.sum(w)))
    a = 1 - (1 - muc) / 2
    if hk:
        se = se * math.sqrt(float(np.sum(w * (y - mu) ** 2) / (k - 1)))
        q = float(stats.t.ppf(a, k - 1))
        p = float(2 * stats.t.sf(abs(mu / se), k - 1))
    else:
        q = float(stats.norm.ppf(a))
        p = float(2 * stats.norm.sf(abs(mu / se)))
    s2_dien_hinh = df * float(np.sum(wf)) / (float(np.sum(wf)) ** 2 - float(np.sum(wf ** 2)))
    if pp == "FE":
        I2 = max(0.0, 100 * (Q - df) / Q) if Q > 0 else 0.0
        H2 = Q / df if df else 1.0
    else:
        I2 = 100 * tau2 / (tau2 + s2_dien_hinh)
        H2 = (tau2 + s2_dien_hinh) / s2_dien_hinh
    pi = None
    if pp != "FE" and k >= 3:
        rong = float(stats.t.ppf(a, k - 2)) * math.sqrt(tau2 + se ** 2)
        pi = (mu - rong, mu + rong)
    return {
        "k": k, "phuong_phap": pp, "hk": bool(hk), "mu": mu, "se": se, "ktc": (mu - q * se, mu + q * se),
        "thong_ke": mu / se, "p": p, "tau2": tau2, "tau": math.sqrt(tau2), "I2": I2, "H2": H2, "Q": Q, "df": df,
        "p_Q": float(stats.chi2.sf(Q, df)) if df > 0 else float("nan"), "khoang_du_bao": pi,
        "trong_so_pt": [float(x) for x in 100 * w / np.sum(w)], "mu_fe": mu_fe,
    }


def egger(yi: Sequence[float], vi: Sequence[float]) -> Dict[str, Any]:
    """Egger: hồi quy yi ~ sei có trọng số 1/vi; kiểm hệ số của sei bằng t (k−2 bậc tự do) — tương đương
    metafor::regtest(model="lm", predictor="sei") và Egger 1997 cổ điển. Cần ≥ 3 nghiên cứu (khuyến nghị ≥ 10)."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    y, v = np.asarray(yi, float), np.asarray(vi, float)
    k = len(y)
    if k < 3:
        return {"k": k, "t": None, "p": None, "ghi_chu": "cần ≥ 3 nghiên cứu"}
    X = np.column_stack([np.ones(k), np.sqrt(v)])
    w = 1 / v
    XtW = X.T * w
    A = np.linalg.inv(XtW @ X)
    b = A @ (XtW @ y)
    s2 = float(np.sum(w * (y - X @ b) ** 2) / (k - 2))
    t = float(b[1] / math.sqrt(A[1, 1] * s2))
    return {"k": k, "he_so": float(b[1]), "chan": float(b[0]), "t": t, "df": k - 2,
            "p": float(2 * stats.t.sf(abs(t), k - 2)),
            "ghi_chu": "" if k >= 10 else "dưới 10 nghiên cứu — kiểm định Egger kém lực (Cochrane Handbook 13.3.5.4)"}


def _tau2_dl_hoi_quy(y, v, X) -> float:
    import numpy as np  # noqa: PLC0415

    w = 1 / v
    WX = X * w[:, None]
    P = np.diag(w) - WX @ np.linalg.inv(X.T @ WX) @ WX.T
    k, p = X.shape
    return max(0.0, (float(y @ P @ y) - (k - p)) / float(np.trace(P)))


def _he_so_hoi_quy_meta(y, v, X, pp: str):
    """Hồi quy meta một biến điều chỉnh — bước chọn phía của trim-and-fill (như metafor)."""
    tau2 = 0.0 if pp == "FE" else tau2_reml(y, v, X) if pp == "REML" else _tau2_dl_hoi_quy(y, v, X)
    return _wls(y, v, X, tau2)[1]


def trim_fill(yi: Sequence[float], vi: Sequence[float], phuong_phap: str = "REML", phia: Optional[str] = None,
              toi_da: int = 100) -> Dict[str, Any]:
    """Trim-and-fill (Duval & Tweedie 2000, ước lượng L0) — CÙNG thuật toán metafor::trimfill: chọn phía bằng hồi quy
    yi ~ √vi (hệ số > 0 ⇒ thiếu bên trái), lặp cắt k0 nghiên cứu cực trị, lấp đối xứng quanh ước lượng của tập đã cắt,
    gộp lại toàn bộ bằng cùng phương pháp. Kết quả là PHÂN TÍCH ĐỘ NHẠY, không phải ước lượng «đã sửa sai lệch»."""
    import numpy as np  # noqa: PLC0415

    y0, v0 = np.asarray(yi, float), np.asarray(vi, float)
    k = len(y0)
    pp = phuong_phap.upper()
    if phia is None:
        b = _he_so_hoi_quy_meta(y0, v0, np.column_stack([np.ones(k), np.sqrt(v0)]), pp)
        phia = "left" if (math.isnan(b[1]) or b[1] > 0) else "right"
    dau = -1.0 if phia == "right" else 1.0
    y = dau * y0
    thu_tu = np.argsort(y, kind="stable")
    y, v = y[thu_tu], v0[thu_tu]
    k0_cu, k0, lap, beta = -1, 0, 0, 0.0
    while abs(k0 - k0_cu) > 0:
        k0_cu = k0
        lap += 1
        if lap > toi_da:
            raise LoiBieuDo("trim-and-fill không hội tụ")
        beta = gop(y[: k - k0], v[: k - k0], pp)["mu"]
        yc = y - beta
        hang = np.empty(k)
        hang[np.argsort(np.abs(yc), kind="stable")] = np.arange(1, k + 1)
        co_dau = np.sign(yc) * hang
        Sr = float(np.sum(co_dau[co_dau > 0]))
        k0 = int(round(max(0.0, (4 * Sr - k * (k + 1)) / (2 * k - 1))))
    y_bu, v_bu = (2 * beta - y[k - k0:], v[k - k0:]) if k0 > 0 else (np.array([]), np.array([]))
    g_tat = gop(dau * np.concatenate([y, y_bu]), np.concatenate([v, v_bu]), pp)
    return {"k0": k0, "phia": phia, "yi_bu": [float(x) for x in dau * y_bu], "vi_bu": [float(x) for x in v_bu],
            "gop_sau_bu": g_tat}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. MÔ HÌNH HAI BIẾN CHO ĐỘ CHÍNH XÁC CHẨN ĐOÁN (Reitsma 2005) + SROC (Harbord 2007)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def chuan_bi_dta(dong: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ra = []
    for r in dong:
        ten = str(r.get("nghien_cuu") or "").strip()
        if not ten:
            raise LoiBieuDo("thiếu tên nghiên cứu (cột nghien_cuu)")
        tp, fp, fn, tn = (_f(r.get(c), f"{ten}: {c}") for c in ("tp", "fp", "fn", "tn"))
        if min(tp, fp, fn, tn) < 0 or any(abs(x - round(x)) > 1e-9 for x in (tp, fp, fn, tn)):
            raise LoiBieuDo(f"{ten}: TP/FP/FN/TN phải là số nguyên ≥ 0")
        if tp + fn == 0 or fp + tn == 0:
            raise LoiBieuDo(f"{ten}: không có người bệnh hoặc không có người không bệnh — không tính được Se/Sp")
        ra.append({"nghien_cuu": ten, "nhom": str(r.get("nhom") or "").strip(), "nam": str(r.get("nam") or "").strip(),
                   "tp": int(tp), "fp": int(fp), "fn": int(fn), "tn": int(tn)})
    if not ra:
        raise LoiBieuDo("không có nghiên cứu")
    return ra


def clopper_pearson(x: int, n: int, muc: float = 0.95) -> Tuple[float, float]:
    """KTC chính xác Clopper–Pearson của một tỷ lệ x/n."""
    from scipy import stats  # noqa: PLC0415

    a = (1 - muc) / 2
    lo = 0.0 if x == 0 else float(stats.beta.ppf(a, x, n - x + 1))
    hi = 1.0 if x == n else float(stats.beta.ppf(1 - a, x + 1, n - x))
    return lo, hi


def logit_dta(r: Dict[str, Any], hieu_chinh: str = "chi_o_0") -> Tuple[float, float, float, float]:
    """(logit Se, var, logit Sp, var). Hiệu chỉnh 0,5: «chi_o_0» chỉ nghiên cứu có ô 0 (mặc định, như metafor
    to="only0"), «tat_ca» mọi nghiên cứu, «khong» không cộng (ô 0 ⇒ lỗi)."""
    tp, fp, fn, tn = r["tp"], r["fp"], r["fn"], r["tn"]
    a = 0.5 if hieu_chinh == "tat_ca" or (hieu_chinh == "chi_o_0" and 0 in (tp, fp, fn, tn)) else 0.0
    if a == 0 and 0 in (tp, fp, fn, tn):
        raise LoiBieuDo(f"{r['nghien_cuu']}: có ô 0 mà hieu_chinh=khong")
    tp, fp, fn, tn = tp + a, fp + a, fn + a, tn + a
    return math.log(tp / fn), 1 / tp + 1 / fn, math.log(tn / fp), 1 / tn + 1 / fp


def _expit(x: float) -> float:
    return 1 / (1 + math.exp(-x)) if x >= 0 else math.exp(x) / (1 + math.exp(x))


def _logit(p: float) -> float:
    return math.log(p / (1 - p))


def hai_bien(nghien_cuu: Sequence[Dict[str, Any]], hieu_chinh: str = "chi_o_0") -> Dict[str, Any]:
    """Mô hình hai biến hiệu ứng ngẫu nhiên (Reitsma 2005) ước lượng REML — tương đương
    metafor::rma.mv(yi, V, mods=~outcome-1, random=~outcome|study, struct="UN", method="REML").

    Trả mu (logit Se, logit Sp), hiệp phương sai của mu, τ² hai chiều, ρ, Se/Sp tóm tắt + KTC, LR+, LR−, DOR + KTC
    (delta trên thang log), tham số HSROC (Harbord 2007). k < 4 ⇒ từ chối (mô hình không ước lượng tin cậy được)."""
    import numpy as np  # noqa: PLC0415
    from scipy import optimize  # noqa: PLC0415

    k = len(nghien_cuu)
    if k < 4:
        raise LoiBieuDo(f"chỉ {k} nghiên cứu — mô hình hai biến cần ≥ 4 (khuyến cáo Cochrane DTA Handbook ch. 10)")
    L = [logit_dta(r, hieu_chinh) for r in nghien_cuu]
    Y = np.array([[a, c] for a, _, c, _ in L])
    S = np.array([[b, d] for _, b, _, d in L])

    def _sigma(theta):
        s1, s2, rho = math.exp(theta[0]), math.exp(theta[1]), math.tanh(theta[2])
        return np.array([[s1 * s1, rho * s1 * s2], [rho * s1 * s2, s2 * s2]]), rho

    def _am_ll(theta):
        Sig, _ = _sigma(theta)
        A, bb, ld, Vinv = np.zeros((2, 2)), np.zeros(2), 0.0, []
        for i in range(k):
            V = Sig + np.diag(S[i])
            sign, ld_i = np.linalg.slogdet(V)
            if sign <= 0:
                return 1e12
            Vi = np.linalg.inv(V)
            Vinv.append(Vi)
            ld += ld_i
            A += Vi
            bb += Vi @ Y[i]
        sa, la = np.linalg.slogdet(A)
        if sa <= 0:
            return 1e12
        mu = np.linalg.solve(A, bb)
        return 0.5 * (ld + la + sum(float((Y[i] - mu) @ Vinv[i] @ (Y[i] - mu)) for i in range(k)))

    v1 = max(float(np.var(Y[:, 0], ddof=1) - np.mean(S[:, 0])), 0.05)
    v2 = max(float(np.var(Y[:, 1], ddof=1) - np.mean(S[:, 1])), 0.05)
    tot = None
    for r0 in (0.0, -0.5, 0.5, -0.9, 0.9):  # nhiều điểm khởi đầu: tránh cực trị địa phương
        x0 = np.array([0.5 * math.log(v1), 0.5 * math.log(v2), math.atanh(r0)])
        kq = optimize.minimize(_am_ll, x0, method="L-BFGS-B", bounds=[(-12, 6), (-12, 6), (-6, 6)],
                               options={"ftol": 1e-14, "gtol": 1e-10})
        kq2 = optimize.minimize(_am_ll, kq.x, method="Nelder-Mead",
                                options={"xatol": 1e-11, "fatol": 1e-13, "maxiter": 20000})
        tot_i = kq2 if kq2.fun <= kq.fun else kq
        if tot is None or tot_i.fun < tot.fun - 1e-12:
            tot = tot_i
    Sig, rho = _sigma(tot.x)
    Vinv = [np.linalg.inv(Sig + np.diag(S[i])) for i in range(k)]
    Vmu = np.linalg.inv(sum(Vinv))
    mu = Vmu @ sum(Vinv[i] @ Y[i] for i in range(k))
    se1, se2 = math.sqrt(Vmu[0, 0]), math.sqrt(Vmu[1, 1])
    Se, Sp = _expit(mu[0]), _expit(mu[1])
    canh_bao = []
    if abs(rho) > 0.98:
        canh_bao.append(f"ρ = {rho:.3f} chạm biên — cân nhắc mô hình rút gọn (hai mô hình một biến, ρ = 0)")
    if Sig[0, 0] < 1e-6 or Sig[1, 1] < 1e-6:
        canh_bao.append("một phương sai giữa các nghiên cứu ≈ 0 — mô hình có thể quá tham số")

    def _se_delta(g):
        g = np.asarray(g, float)
        return math.sqrt(float(g @ Vmu @ g))

    def _ktc_log(u, s):
        return {"uoc_luong": math.exp(u), "ktc": (math.exp(u - Z975 * s), math.exp(u + Z975 * s))}

    sA, sB, sAB = math.sqrt(Sig[0, 0]), math.sqrt(Sig[1, 1]), Sig[0, 1]
    return {
        "k": k, "hieu_chinh": hieu_chinh, "mu": [float(mu[0]), float(mu[1])], "Vmu": Vmu.tolist(),
        "se_mu": [se1, se2], "Sigma": Sig.tolist(), "tau2": [float(Sig[0, 0]), float(Sig[1, 1])], "rho": float(rho),
        "do_nhay": {"uoc_luong": Se, "ktc": (_expit(mu[0] - Z975 * se1), _expit(mu[0] + Z975 * se1))},
        "do_dac_hieu": {"uoc_luong": Sp, "ktc": (_expit(mu[1] - Z975 * se2), _expit(mu[1] + Z975 * se2))},
        "lr_duong": _ktc_log(math.log(Se) - math.log(1 - Sp), _se_delta([1 - Se, Sp])),
        "lr_am": _ktc_log(math.log(1 - Se) - math.log(Sp), _se_delta([-Se, -(1 - Sp)])),
        "dor": _ktc_log(float(mu[0] + mu[1]), _se_delta([1, 1])),
        "hsroc": {"Lambda": (sB / sA) ** 0.5 * mu[0] + (sA / sB) ** 0.5 * mu[1],
                  "Theta": 0.5 * ((sB / sA) ** 0.5 * mu[0] - (sA / sB) ** 0.5 * mu[1]),
                  "beta": math.log(sB / sA), "sigma2_alpha": 2 * (sA * sB + sAB),
                  "sigma2_theta": 0.5 * (sA * sB - sAB)},
        "am_loglik_reml": float(tot.fun), "canh_bao": canh_bao,
    }


def _do_doc(m: Dict[str, Any], kieu: str) -> float:
    sA, sB = math.sqrt(m["tau2"][0]), math.sqrt(m["tau2"][1])
    return sA / sB if kieu == "rutter-gatsonis" else -m["rho"] * sA / sB


def duong_sroc(m: Dict[str, Any], fpr_min: float, fpr_max: float, kieu: str = "rutter-gatsonis",
               so_diem: int = 200) -> Tuple[List[float], List[float]]:
    """Đường SROC trong [fpr_min, fpr_max] (Cochrane: KHÔNG ngoại suy ngoài khoảng đặc hiệu quan sát được).

    rutter-gatsonis (mặc định, như RevMan/metandi): logit TPR = μ_A + (σ_A/σ_B)(logit FPR − μ_FPR) — chính là
    logit TPR = Λ·e^{−β/2} + e^{−β}·logit FPR của Harbord 2007. reitsma: kỳ vọng có điều kiện logit TPR | logit FPR,
    độ dốc −ρσ_A/σ_B."""
    import numpy as np  # noqa: PLC0415

    muA, muB = m["mu"]
    doc = _do_doc(m, kieu)
    lo, hi = max(fpr_min, 1e-4), min(fpr_max, 1 - 1e-4)
    if hi <= lo:
        return [lo], [_expit(muA)]
    xs = np.linspace(_logit(lo), _logit(hi), so_diem)
    return [_expit(x) for x in xs], [_expit(muA + doc * (x + muB)) for x in xs]


def auc_sroc(m: Dict[str, Any], kieu: str = "rutter-gatsonis") -> float:
    """Diện tích dưới đường SROC trên toàn khoảng FPR (0, 1) — như mada::AUC; đọc thận trọng vì ngoài khoảng quan sát
    là ngoại suy."""
    from scipy import integrate  # noqa: PLC0415

    muA, muB = m["mu"]
    doc = _do_doc(m, kieu)
    return float(integrate.quad(lambda x: _expit(muA + doc * (_logit(x) + muB)), 1e-10, 1 - 1e-10, limit=200)[0])


def elip(m: Dict[str, Any], loai: str = "tin_cay", muc: float = 0.95,
         so_diem: int = 240) -> Tuple[List[float], List[float]]:
    """Vùng tin cậy (Var μ̂) hoặc vùng dự báo (Σ + Var μ̂) 95% của điểm tóm tắt — elip trong không gian
    (logit FPR, logit TPR) với bán kính √χ²₂(0,95), đổi về thang xác suất (Reitsma 2005; Harbord 2007)."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    V = np.array(m["Vmu"])
    if loai == "du_bao":
        V = V + np.array(m["Sigma"])
    C = np.array([[V[1, 1], -V[0, 1]], [-V[0, 1], V[0, 0]]])  # (logit FPR, logit TPR); logit FPR = −logit Sp
    tam = np.array([-m["mu"][1], m["mu"][0]])
    t = np.linspace(0, 2 * math.pi, so_diem)
    diem = tam[:, None] + math.sqrt(float(stats.chi2.ppf(muc, 2))) * np.linalg.cholesky(C) @ np.vstack(
        [np.cos(t), np.sin(t)])
    return [_expit(x) for x in diem[0]], [_expit(y) for y in diem[1]]


def deeks(nghien_cuu: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Deeks 2005: hồi quy ln DOR ~ 1/√ESS có trọng số ESS (ESS = 4·n₁·n₀/(n₁+n₀)); cộng 0,5 mọi ô; kiểm độ dốc bằng t
    (k−2 bậc tự do). p < 0,10 gợi ý bất đối xứng (ngưỡng của bài gốc)."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    k = len(nghien_cuu)
    if k < 3:
        raise LoiBieuDo("Deeks cần ≥ 3 nghiên cứu")
    ldor, x, w = [], [], []
    for r in nghien_cuu:
        tp, fp, fn, tn = (r[c] + 0.5 for c in ("tp", "fp", "fn", "tn"))
        n1, n0 = r["tp"] + r["fn"], r["fp"] + r["tn"]
        ess = 4 * n1 * n0 / (n1 + n0)
        ldor.append(math.log(tp * tn / (fp * fn)))
        x.append(1 / math.sqrt(ess))
        w.append(ess)
    y, xa, wa = np.array(ldor), np.array(x), np.array(w)
    X = np.column_stack([np.ones(k), xa])
    A = np.linalg.inv((X.T * wa) @ X)
    b = A @ ((X.T * wa) @ y)
    s2 = float(np.sum(wa * (y - X @ b) ** 2) / (k - 2))
    t = float(b[1] / math.sqrt(A[1, 1] * s2))
    return {"k": k, "chan": float(b[0]), "doc": float(b[1]), "t": t, "df": k - 2,
            "p": float(2 * stats.t.sf(abs(t), k - 2)), "ln_dor": y.tolist(), "nghich_can_ess": xa.tolist()}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. VẼ
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _vach_log(lo: float, hi: float) -> List[float]:
    """Vạch trục log: 0,01 · 0,02 · 0,05 · 0,1 · 0,2 · 0,5 · 1 · 2 · 5 · 10…; khoảng hẹp (< 3 vạch) dùng bộ dày hơn."""
    chon = [v for v in (0.01, 0.02, 0.05, 0.1, 0.2, 0.5, 1, 2, 5, 10, 20, 50, 100) if lo <= v <= hi]
    if len(chon) > 7:
        chon = [v for v in chon if v in (0.01, 0.1, 0.5, 1, 2, 10, 100)]
    if len(chon) < 3:
        chon = [v for v in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 1, 1.25, 1.5, 2, 3, 4, 5, 10) if lo <= v <= hi]
        if len(chon) > 7:
            chon = chon[::2] if 1 in chon[::2] else chon[1::2]
    return chon or [1]


def _nhan_vach(v: float, ngon_ngu: str) -> str:
    """Nhãn vạch trục log gọn: 0,25 · 0,5 · 1 · 2 · 10 (không «1,00», không «0,50»)."""
    s = f"{v:.2f}".rstrip("0").rstrip(".") if v < 1 else f"{v:g}"
    return s.replace(".", ",") if ngon_ngu == "vi" else s


def _truc_log(ax, x_min: float, x_max: float, ngon_ngu: str) -> None:
    from matplotlib.ticker import FixedLocator, NullLocator  # noqa: PLC0415

    ax.set_xscale("log")
    vach = _vach_log(x_min, x_max)
    ax.xaxis.set_major_locator(FixedLocator(vach))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.set_xticklabels([_nhan_vach(v, ngon_ngu) for v in vach])


def _gioi_han_truc(lo_all: Sequence[float], hi_all: Sequence[float], log: bool, ref: float) -> Tuple[float, float]:
    lo, hi = min(min(lo_all), ref), max(max(hi_all), ref)
    if log:
        lo, hi = math.log(lo), math.log(hi)
        rong = hi - lo
        lo, hi = max(lo - 0.05 * rong, math.log(0.01)), min(hi + 0.05 * rong, math.log(100))
        return math.exp(lo), math.exp(hi)
    rong = hi - lo or 1.0
    return lo - 0.05 * rong, hi + 0.05 * rong


def _chu_ktc(u: float, lo: float, hi: float, log: bool, ngon_ngu: str, nd: int = 2) -> str:
    tf = math.exp if log else (lambda z: z)
    return f"{so(tf(u), nd, ngon_ngu)} [{so(tf(lo), nd, ngon_ngu)}; {so(tf(hi), nd, ngon_ngu)}]"


def _dong_khong_dong_nhat(g: Dict[str, Any], ngon_ngu: str) -> str:
    return (f"{nhan('khong_dong_nhat', ngon_ngu)}: τ² = {so(g['tau2'], 3, ngon_ngu)}; "
            f"I² = {so(g['I2'], 0, ngon_ngu)}%; Q = {so(g['Q'], 2, ngon_ngu)} (df = {g['df']}), "
            f"{BC.p_chu(g['p_Q'], ngon_ngu)}")


def _ten_truc(do: str, ngon_ngu: str) -> str:
    return TEN_DO.get(do, TEN_DO["GEN"])["en" if ngon_ngu == "en" else "vi"]


def _gop_ra_json(g: Dict[str, Any], log: bool) -> Dict[str, Any]:
    tf = math.exp if log else (lambda z: z)
    pi = g.get("khoang_du_bao")
    return {"k": g["k"], "phuong_phap": g["phuong_phap"], "hk": g["hk"], "uoc_luong": tf(g["mu"]),
            "ktc": (tf(g["ktc"][0]), tf(g["ktc"][1])), "thang_goc": {"mu": g["mu"], "se": g["se"]},
            "khoang_du_bao": (tf(pi[0]), tf(pi[1])) if pi else None, "tau2": g["tau2"], "I2": g["I2"],
            "Q": g["Q"], "df": g["df"], "p_Q": g["p_Q"], "thong_ke": g["thong_ke"], "p": g["p"]}


def kiem_dinh_khac_biet_nhom(ket_nhom: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Q giữa các phân nhóm (như RevMan): Σ w_g (μ_g − μ̄)², w_g = 1/se_g², df = G − 1."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    mus = np.array([g["mu"] for g in ket_nhom.values()])
    ws = np.array([1 / g["se"] ** 2 for g in ket_nhom.values()])
    mbar = float(np.sum(ws * mus) / np.sum(ws))
    Qb = float(np.sum(ws * (mus - mbar) ** 2))
    return {"Q": Qb, "df": len(mus) - 1, "p": float(stats.chi2.sf(Qb, len(mus) - 1))}


def ve_forest(ds: Sequence[Dict[str, Any]], do: str, dich: Path, phuong_phap: str = "REML", hk: bool = False,
              ngon_ngu: str = "vi", nhan_trai: str = "", nhan_phai: str = "", tieu_de: str = "",
              ghi_chu_loai: Sequence[str] = ()) -> Dict[str, Any]:
    """Forest plot đầy đủ; trả số liệu đã vẽ (ghi kèm JSON)."""
    import matplotlib.patches as mp  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    log = do in TY_SO
    ref = 1.0 if log else 0.0
    tf = math.exp if log else (lambda z: z)
    nhom_ds = list(dict.fromkeys(e["nhom"] for e in ds))
    co_nhom = len([g for g in nhom_ds if g]) >= 2
    g_tong = gop([e["yi"] for e in ds], [e["vi"] for e in ds], phuong_phap, hk)
    trong_so = dict(zip([id(e) for e in ds], g_tong["trong_so_pt"]))
    hang: List[Dict[str, Any]] = []
    ket_nhom: Dict[str, Dict[str, Any]] = {}
    # 22/11/2026: kiểm định khác biệt giữa nhóm dùng MỌI phân nhóm, kể cả phân nhóm chỉ một nghiên cứu (ước lượng của
    # chính nó) — như RevMan và metafor (rma trên ước lượng nhóm); trùng `phan_tich_thiet_ke_dac_thu.phan_nhom_gop` (G6)
    uoc_nhom: Dict[str, Dict[str, Any]] = {}
    for ten_nhom in (nhom_ds if co_nhom else [""]):
        cac = [e for e in ds if (e["nhom"] == ten_nhom or not co_nhom)]
        if co_nhom:
            hang.append({"loai": "tieu_de_nhom", "chu": ten_nhom or "—"})
        hang.extend({"loai": "nc", "e": e} for e in cac)
        if co_nhom:
            if len(cac) >= 2:
                gn = gop([e["yi"] for e in cac], [e["vi"] for e in cac], phuong_phap, hk)
                ket_nhom[ten_nhom] = uoc_nhom[ten_nhom] = gn
                hang.append({"loai": "kim_cuong", "g": gn, "chu": "Phân nhóm" if ngon_ngu == "vi" else "Subtotal",
                             "trong_so": sum(trong_so[id(e)] for e in cac)})
                hang.append({"loai": "chu", "chu": _dong_khong_dong_nhat(gn, ngon_ngu), "nho": True})
            elif cac:
                uoc_nhom[ten_nhom] = {"mu": cac[0]["yi"], "se": math.sqrt(cac[0]["vi"])}
            hang.append({"loai": "trong"})
    ten_mh = nhan("gop_co_dinh" if phuong_phap.upper() == "FE" else "gop_ngau_nhien", ngon_ngu)
    if hk:
        ten_mh += " (Hartung–Knapp)"
    hang.append({"loai": "kim_cuong", "g": g_tong, "chu": ten_mh, "dam": True})
    if g_tong["khoang_du_bao"]:
        hang.append({"loai": "du_bao", "g": g_tong})
    hang.append({"loai": "chu", "chu": _dong_khong_dong_nhat(g_tong, ngon_ngu), "nho": True})
    hang.append({"loai": "chu", "nho": True, "chu": f"{nhan('kiem_dinh_tong', ngon_ngu)}: {'t' if hk else 'z'} = "
                 f"{so(g_tong['thong_ke'], 2, ngon_ngu)}, {BC.p_chu(g_tong['p'], ngon_ngu)}"})
    kiem_nhom = None
    if co_nhom and len(uoc_nhom) >= 2:
        kiem_nhom = kiem_dinh_khac_biet_nhom(uoc_nhom)
        hang.append({"loai": "chu", "nho": True,
                     "chu": f"{nhan('khac_biet_nhom', ngon_ngu)}: χ² = {so(kiem_nhom['Q'], 2, ngon_ngu)} "
                            f"(df = {kiem_nhom['df']}), {BC.p_chu(kiem_nhom['p'], ngon_ngu)}"})

    co_2x2 = all("su_kien_1" in e for e in ds)
    co_n = all("n_1" in e for e in ds)
    lo_all = [tf(e["yi"] - Z975 * e["sei"]) for e in ds] + [tf(g_tong["ktc"][0])]
    hi_all = [tf(e["yi"] + Z975 * e["sei"]) for e in ds] + [tf(g_tong["ktc"][1])]
    if g_tong["khoang_du_bao"]:
        lo_all.append(tf(g_tong["khoang_du_bao"][0]))
        hi_all.append(tf(g_tong["khoang_du_bao"][1]))
    x_min, x_max = _gioi_han_truc(lo_all, hi_all, log, ref)

    n_hang = len(hang)
    rong_trai = 2.6 + (1.5 if (co_2x2 or co_n) else 0)
    fig = plt.figure(figsize=(rong_trai + 3.2 + 2.3, 0.24 * (n_hang + 2.6) + 0.5))
    gs = fig.add_gridspec(1, 3, width_ratios=[rong_trai, 3.2, 2.3], wspace=0.02)
    ax_t, ax, ax_p = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    for a in (ax_t, ax_p):
        a.axis("off")
        a.set_xlim(0, 1)
    y_tren = n_hang + 1.0
    for a in (ax_t, ax, ax_p):
        a.set_ylim(-0.6, y_tren + 0.6)
    ax_t.text(0.0, y_tren, nhan("nghien_cuu", ngon_ngu), weight="bold", va="center")
    if co_2x2 or co_n:
        mau_cot = "n/N" if co_2x2 else "n"
        ax_t.text(0.62, y_tren, f"{mau_cot} (1)", weight="bold", va="center", ha="center")
        ax_t.text(0.86, y_tren, f"{mau_cot} (2)", weight="bold", va="center", ha="center")
    ax_p.text(0.04, y_tren, f"{do if do != 'GEN' else ''} [{nhan('ktc95', ngon_ngu)}]".strip(), weight="bold",
              va="center")
    ax_p.text(0.98, y_tren, nhan("trong_so", ngon_ngu), weight="bold", va="center", ha="right")
    so_lieu_hang = []
    max_w = max(g_tong["trong_so_pt"]) or 1.0
    for i, h in enumerate(hang):
        y = n_hang - i
        if h["loai"] == "tieu_de_nhom":
            ax_t.text(0.0, y, h["chu"], weight="bold", style="italic", va="center")
        elif h["loai"] == "nc":
            e = h["e"]
            lo, hi = e["yi"] - Z975 * e["sei"], e["yi"] + Z975 * e["sei"]
            w = trong_so[id(e)]
            nam = e.get("nam")
            ax_t.text(0.03, y, e["nghien_cuu"] + (f" {nam}" if nam and nam not in e["nghien_cuu"] else ""), va="center")
            if co_2x2:
                ax_t.text(0.62, y, f"{e['su_kien_1']}/{e['tong_1']}", va="center", ha="center")
                ax_t.text(0.86, y, f"{e['su_kien_2']}/{e['tong_2']}", va="center", ha="center")
            elif co_n:
                ax_t.text(0.62, y, str(e["n_1"]), va="center", ha="center")
                ax_t.text(0.86, y, str(e["n_2"]), va="center", ha="center")
            l2, h2 = BC.mui_ten_vuot(ax, y, x_min, x_max, tf(lo), tf(hi), log)
            ax.plot([l2, h2], [y, y], color="#222222", lw=0.9, solid_capstyle="butt")
            if x_min <= tf(e["yi"]) <= x_max:
                ax.plot([tf(e["yi"])], [y], marker="s", ms=3.0 + 7.0 * math.sqrt(w / max_w), color="#4a4a4a",
                        mec="#222222", mew=0.5)
            ax_p.text(0.04, y, _chu_ktc(e["yi"], lo, hi, log, ngon_ngu), va="center")
            ax_p.text(0.98, y, so(w, 1, ngon_ngu) + "%", va="center", ha="right")
            so_lieu_hang.append({"nghien_cuu": e["nghien_cuu"], "nhom": e["nhom"], "uoc_luong": tf(e["yi"]),
                                 "ktc": (tf(lo), tf(hi)), "trong_so_pt": w})
        elif h["loai"] == "kim_cuong":
            g = h["g"]
            lo, hi = g["ktc"]
            dam = bool(h.get("dam"))
            ax.add_patch(mp.Polygon([(tf(lo), y), (tf(g["mu"]), y + 0.34), (tf(hi), y), (tf(g["mu"]), y - 0.34)],
                                    closed=True, fc="#1f1f1f" if dam else "#8c8c8c", ec="#111111", lw=0.6))
            ax_t.text(0.0 if dam else 0.03, y, h["chu"], va="center", weight="bold" if dam else None)
            ax_p.text(0.04, y, _chu_ktc(g["mu"], lo, hi, log, ngon_ngu), va="center", weight="bold" if dam else None)
            tsn = 100.0 if dam else h.get("trong_so")
            if tsn is not None:
                ax_p.text(0.98, y, so(tsn, 1, ngon_ngu) + "%", va="center", ha="right",
                          weight="bold" if dam else None)
        elif h["loai"] == "du_bao":
            lo, hi = h["g"]["khoang_du_bao"]
            l2, h2 = BC.mui_ten_vuot(ax, y, x_min, x_max, tf(lo), tf(hi), log)
            ax.plot([l2, h2], [y, y], color="#1f1f1f", lw=2.2, solid_capstyle="butt")
            ax_t.text(0.03, y, nhan("khoang_du_bao", ngon_ngu), va="center", style="italic")
            ax_p.text(0.04, y, f"[{so(tf(lo), 2, ngon_ngu)}; {so(tf(hi), 2, ngon_ngu)}]", va="center", style="italic")
        elif h["loai"] == "chu":
            ax_t.text(0.0, y, h["chu"], va="center", fontsize=8 if h.get("nho") else None, clip_on=False)
    ax.axvline(ref, color="#555555", lw=0.8, zorder=0)
    ax.axvline(tf(g_tong["mu"]), color="#777777", lw=0.7, ls=(0, (4, 3)), zorder=0)
    if log:
        _truc_log(ax, x_min, x_max, ngon_ngu)
    else:
        BC.dinh_dang_truc(ax, ngon_ngu, "x")
    ax.set_xlim(x_min, x_max)
    ax.spines["left"].set_visible(False)
    ax.set_yticks([])
    ax.set_xlabel(f"{_ten_truc(do, ngon_ngu)} ({nhan('ktc95', ngon_ngu)})")
    for x_ax, chu, ha in ((0.0, ("← " + nhan_trai) if nhan_trai else "", "left"),
                          (1.0, (nhan_phai + " →") if nhan_phai else "", "right")):
        if chu:
            ax.annotate(chu, xy=(x_ax, 0), xycoords="axes fraction", xytext=(0, -34), textcoords="offset points",
                        ha=ha, va="top", fontsize=8)
    if tieu_de:
        fig.suptitle(tieu_de, fontsize=10, y=1.0)
    so_lieu = {
        "loai": "forest", "thuoc_do": do, "ngon_ngu": ngon_ngu, "thang_log": log, "nghien_cuu": so_lieu_hang,
        "gop": _gop_ra_json(g_tong, log), "phan_nhom": {k: _gop_ra_json(v, log) for k, v in ket_nhom.items()},
        "kiem_dinh_khac_biet_nhom": kiem_nhom, "loai_khoi_gop": list(ghi_chu_loai),
        "ghi_chu": "Khoảng dự báo dùng t (k−2 bậc tự do); I² tính theo τ² (như metafor). Cần bác sĩ kiểm chứng.",
    }
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


def ve_pheu(ds: Sequence[Dict[str, Any]], do: str, dich: Path, phuong_phap: str = "REML", duong_vien: bool = False,
            co_trim_fill: bool = False, ngon_ngu: str = "vi") -> Dict[str, Any]:
    """Funnel plot (trục tung sai số chuẩn đảo ngược, 0 ở trên cùng)."""
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    log = do in TY_SO
    tf = np.exp if log else (lambda z: z)
    y = np.array([e["yi"] for e in ds])
    se = np.array([e["sei"] for e in ds])
    g = gop(y, se ** 2, phuong_phap)
    eg = egger(y, se ** 2)
    tfk = trim_fill(y, se ** 2, phuong_phap) if co_trim_fill else None
    se_max = float(se.max()) * 1.08
    fig, ax = plt.subplots(figsize=(6.8 if (duong_vien or co_trim_fill) else 5.2, 4.3))
    ss = np.linspace(0, se_max, 100)
    if duong_vien:  # vùng ý nghĩa quanh 0 (Peters 2008): 0,10 > p ≥ 0,05 · 0,05 > p ≥ 0,01 · p < 0,01
        z1, z2, z3 = 1.6448536, 1.9599640, 2.5758293
        for zi, zo, mau in ((z1, z2, "#e6e6e6"), (z2, z3, "#c8c8c8")):
            ax.fill_betweenx(ss, tf(-zo * ss), tf(-zi * ss), color=mau, lw=0)
            ax.fill_betweenx(ss, tf(zi * ss), tf(zo * ss), color=mau, lw=0)
        ax.fill_betweenx(ss, tf(z3 * ss), tf(z3 * ss + 50), color="#a6a6a6", lw=0)
        ax.fill_betweenx(ss, tf(-z3 * ss - 50), tf(-z3 * ss), color="#a6a6a6", lw=0)
    ax.plot(tf(g["mu"] - Z975 * ss), ss, color="#333333", lw=0.8, ls="--")
    ax.plot(tf(g["mu"] + Z975 * ss), ss, color="#333333", lw=0.8, ls="--")
    ax.axvline(tf(g["mu"]), color="#222222", lw=0.9)
    if log:
        ax.axvline(1.0, color="#777777", lw=0.6, ls=":")
    ax.scatter(tf(y), se, s=26, facecolor="#333333", edgecolor="#111111", lw=0.5, zorder=3,
               label=nhan("nghien_cuu", ngon_ngu))
    if tfk and tfk["k0"]:
        ax.scatter(tf(np.array(tfk["yi_bu"])), np.sqrt(tfk["vi_bu"]), s=26, facecolor="white", edgecolor="#111111",
                   lw=0.8, zorder=3, label=nhan("nghien_cuu_bo_sung", ngon_ngu))
        ax.axvline(tf(tfk["gop_sau_bu"]["mu"]), color="#222222", lw=0.8, ls=(0, (1, 1.5)))
    ax.set_ylim(se_max, 0)
    x_moi = list(tf(y)) + [tf(g["mu"] - Z975 * se_max), tf(g["mu"] + Z975 * se_max)]
    if tfk and tfk["k0"]:
        x_moi += list(tf(np.array(tfk["yi_bu"])))
    if log:
        lo, hi = min(x_moi) * 0.9, max(x_moi) * 1.1
        _truc_log(ax, lo, hi, ngon_ngu)
        ax.set_xlim(lo, hi)
    else:
        rong = max(x_moi) - min(x_moi)
        ax.set_xlim(min(x_moi) - 0.05 * rong, max(x_moi) + 0.05 * rong)
        BC.dinh_dang_truc(ax, ngon_ngu, "x")
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    duoi_log = (" (thang log)" if ngon_ngu == "vi" else " (log scale)") if log else ""
    ax.set_xlabel(_ten_truc(do, ngon_ngu) + duoi_log)
    ax.set_ylabel(nhan("sai_so_chuan", ngon_ngu))
    chu = f"Egger: t = {so(eg['t'], 2, ngon_ngu)}, {BC.p_chu(eg['p'], ngon_ngu)}" if eg.get("t") is not None else ""
    if tfk:
        phia = ("trái" if tfk["phia"] == "left" else "phải") if ngon_ngu == "vi" else tfk["phia"]
        chu += ("\n" if chu else "") + f"Trim-and-fill: k0 = {tfk['k0']} ({phia})"
    if chu:
        ax.text(0.02, 0.02, chu, transform=ax.transAxes, fontsize=8, va="bottom")
    if duong_vien or (tfk and tfk["k0"]):
        import matplotlib.patches as mp  # noqa: PLC0415
        from matplotlib.lines import Line2D  # noqa: PLC0415

        tay, _ = ax.get_legend_handles_labels()
        vi = ngon_ngu == "vi"
        tay += [Line2D([], [], color="#222222", lw=0.9, label="Ước lượng gộp" if vi else "Pooled estimate"),
                Line2D([], [], color="#333333", lw=0.8, ls="--", label="Giả-KTC 95%" if vi else "Pseudo 95% CI")]
        if tfk and tfk["k0"]:
            tay.append(Line2D([], [], color="#222222", lw=0.8, ls=(0, (1, 1.5)),
                              label="Gộp sau trim-and-fill" if vi else "After trim-and-fill"))
        if duong_vien:
            tay += [mp.Patch(fc="white", ec="#999999", lw=0.5, label=("0,10 < p ≤ 1" if vi else "0.10 < p ≤ 1")),
                    mp.Patch(fc="#e6e6e6", label=("0,05 < p ≤ 0,10" if vi else "0.05 < p ≤ 0.10")),
                    mp.Patch(fc="#c8c8c8", label=("0,01 < p ≤ 0,05" if vi else "0.01 < p ≤ 0.05")),
                    mp.Patch(fc="#a6a6a6", label=("p ≤ 0,01" if vi else "p ≤ 0.01"))]
        if not (tfk and tfk["k0"]):
            tay = [h for h in tay if not hasattr(h, "get_offsets")]
        ax.legend(handles=tay, frameon=False, loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=8)
    so_lieu = {"loai": "pheu", "thuoc_do": do, "gop": _gop_ra_json(g, log), "egger": eg, "duong_vien": bool(duong_vien),
               "trim_fill": ({"k0": tfk["k0"], "phia": tfk["phia"], "gop_sau_bu": _gop_ra_json(tfk["gop_sau_bu"], log)}
                             if tfk else None),
               "ghi_chu": "Funnel/Egger kém tin cậy khi < 10 nghiên cứu; trim-and-fill là phân tích độ nhạy. "
                          "Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


def ve_bo_tung_nc(ds: Sequence[Dict[str, Any]], do: str, dich: Path, phuong_phap: str = "REML",
                  ngon_ngu: str = "vi") -> Dict[str, Any]:
    """Leave-one-out: mỗi dòng là ước lượng gộp khi BỎ nghiên cứu đó; vạch đứt là ước lượng gộp đủ."""
    BC.kiem_ngon_ngu(ngon_ngu)
    if len(ds) < 3:
        raise LoiBieuDo("bỏ-từng-nghiên-cứu cần ≥ 3 nghiên cứu")
    plt = BC.plt_chuan()
    log = do in TY_SO
    tf = math.exp if log else (lambda z: z)
    g = gop([e["yi"] for e in ds], [e["vi"] for e in ds], phuong_phap)
    kq = []
    for i, e in enumerate(ds):
        con = [x for j, x in enumerate(ds) if j != i]
        gi = gop([x["yi"] for x in con], [x["vi"] for x in con], phuong_phap)
        nam = e.get("nam")
        kq.append({"bo": e["nghien_cuu"] + (f" {nam}" if nam and nam not in e["nghien_cuu"] else ""), "mu": gi["mu"],
                   "ktc": gi["ktc"], "I2": gi["I2"], "tau2": gi["tau2"], "p": gi["p"]})
    n = len(kq) + 1
    fig = plt.figure(figsize=(8.4, 0.24 * (n + 3) + 0.6))
    gs = fig.add_gridspec(1, 3, width_ratios=[2.4, 3.2, 2.8], wspace=0.02)
    ax_t, ax, ax_p = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    for a in (ax_t, ax_p):
        a.axis("off")
        a.set_xlim(0, 1)
    for a in (ax_t, ax, ax_p):
        a.set_ylim(-0.6, n + 1.6)
    ax_t.text(0, n + 1, "Bỏ nghiên cứu" if ngon_ngu == "vi" else "Omitting", weight="bold", va="center")
    ax_p.text(0.03, n + 1, f"{do} [{nhan('ktc95', ngon_ngu)}]", weight="bold", va="center")
    ax_p.text(0.98, n + 1, "I²", weight="bold", va="center", ha="right")
    lo_all = [tf(r["ktc"][0]) for r in kq] + [tf(g["ktc"][0])]
    hi_all = [tf(r["ktc"][1]) for r in kq] + [tf(g["ktc"][1])]
    x_min, x_max = _gioi_han_truc(lo_all, hi_all, log, 1.0 if log else 0.0)
    for i, r in enumerate(kq):
        y = n - i
        ax_t.text(0.03, y, r["bo"], va="center")
        ax.plot([tf(r["ktc"][0]), tf(r["ktc"][1])], [y, y], color="#222222", lw=0.9)
        ax.plot([tf(r["mu"])], [y], marker="o", ms=4.5, color="#222222")
        ax_p.text(0.03, y, _chu_ktc(r["mu"], *r["ktc"], log, ngon_ngu), va="center")
        ax_p.text(0.98, y, so(r["I2"], 0, ngon_ngu) + "%", va="center", ha="right")
    import matplotlib.patches as mp  # noqa: PLC0415

    ax.add_patch(mp.Polygon([(tf(g["ktc"][0]), 1), (tf(g["mu"]), 1.32), (tf(g["ktc"][1]), 1), (tf(g["mu"]), 0.68)],
                            closed=True, fc="#1f1f1f"))
    ax_t.text(0.0, 1, (f"Gộp đủ {g['k']} nghiên cứu" if ngon_ngu == "vi" else f"All {g['k']} studies"), va="center",
              weight="bold")
    ax_p.text(0.03, 1, _chu_ktc(g["mu"], *g["ktc"], log, ngon_ngu), va="center", weight="bold")
    ax_p.text(0.98, 1, so(g["I2"], 0, ngon_ngu) + "%", va="center", ha="right", weight="bold")
    ax.axvline(tf(g["mu"]), color="#555555", lw=0.8, ls="--")
    ax.axvline(1.0 if log else 0.0, color="#999999", lw=0.6)
    if log:
        _truc_log(ax, x_min, x_max, ngon_ngu)
    else:
        BC.dinh_dang_truc(ax, ngon_ngu, "x")
    ax.set_xlim(x_min, x_max)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    ax.set_xlabel(_ten_truc(do, ngon_ngu))
    so_lieu = {"loai": "bo_tung_nc", "thuoc_do": do, "gop_du": _gop_ra_json(g, log),
               "ket_qua": [{"bo": r["bo"], "uoc_luong": tf(r["mu"]), "ktc": (tf(r["ktc"][0]), tf(r["ktc"][1])),
                            "I2": r["I2"], "tau2": r["tau2"], "p": r["p"]} for r in kq]}
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


def _chu_p(x: Dict[str, Any], ngon_ngu: str) -> str:
    return f"{so(x['uoc_luong'], 2, ngon_ngu)} [{so(x['ktc'][0], 2, ngon_ngu)}; {so(x['ktc'][1], 2, ngon_ngu)}]"


def ve_dta_forest(ds: Sequence[Dict[str, Any]], dich: Path, ngon_ngu: str = "vi",
                  tom_tat: Optional[Dict[str, Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Forest CẶP độ nhạy – độ đặc hiệu (kiểu Cochrane DTA): TP FP FN TN, Se [KTC], Sp [KTC] chính xác."""
    import matplotlib.patches as mp  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    nhom_ds = list(dict.fromkeys(r["nhom"] for r in ds))
    hang: List[Tuple[str, Any]] = []
    for gn in nhom_ds:
        if len(nhom_ds) > 1:
            hang.append(("nhom", gn or "—"))
        hang.extend(("nc", r) for r in ds if r["nhom"] == gn)
        if tom_tat and gn in tom_tat:
            hang.append(("tom_tat", tom_tat[gn]))
        if len(nhom_ds) > 1:
            hang.append(("trong", None))
    while hang and hang[-1][0] == "trong":
        hang.pop()
    n = len(hang)
    dai = max([len(r["nghien_cuu"]) + (len(r.get("nam") or "") + 1) for r in ds] + [28])
    w_ten = 0.072 * dai + 0.15  # inch — cột tên theo tên dài nhất (phông 9,5 pt ≈ 0,072 inch/ký tự)
    w_t = w_ten + 4 * 0.42 + 1.45
    fig = plt.figure(figsize=(w_t + 1.45 + 2.1 + 0.35 + 2.1, 0.23 * (n + 2.5) + 0.6))
    gs = fig.add_gridspec(1, 5, width_ratios=[w_t, 1.45, 2.1, 0.35, 2.1], wspace=0.0)
    ax_t, ax_g = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    ax_se, ax_sp = fig.add_subplot(gs[2]), fig.add_subplot(gs[4])
    for a in (ax_t, ax_g):
        a.axis("off")
        a.set_xlim(0, 1)
    for a in (ax_t, ax_g, ax_se, ax_sp):
        a.set_ylim(-0.6, n + 1.6)
    xc = {c: (w_ten + 0.42 * (i + 1) - 0.04) / w_t for i, c in enumerate(("tp", "fp", "fn", "tn"))}
    x_se = (w_ten + 4 * 0.42 + 0.72) / w_t
    for x, chu, ha in ((0.0, nhan("nghien_cuu", ngon_ngu), "left"), (xc["tp"], "TP", "right"),
                       (xc["fp"], "FP", "right"), (xc["fn"], "FN", "right"), (xc["tn"], "TN", "right"),
                       (x_se, nhan("do_nhay", ngon_ngu), "center")):
        ax_t.text(x, n + 1, chu, weight="bold", va="center", ha=ha)
    ax_g.text(0.5, n + 1, nhan("do_dac_hieu", ngon_ngu), weight="bold", va="center", ha="center")
    so_lieu_nc = []
    for i, (loai, v) in enumerate(hang):
        y = n - i
        if loai == "nhom":
            ax_t.text(0.0, y, v, weight="bold", style="italic", va="center")
        elif loai == "nc":
            r = v
            se_lo, se_hi = clopper_pearson(r["tp"], r["tp"] + r["fn"])
            sp_lo, sp_hi = clopper_pearson(r["tn"], r["tn"] + r["fp"])
            se_u, sp_u = r["tp"] / (r["tp"] + r["fn"]), r["tn"] / (r["tn"] + r["fp"])
            nam = r.get("nam")
            ax_t.text(0.02, y, r["nghien_cuu"] + (f" {nam}" if nam and nam not in r["nghien_cuu"] else ""),
                      va="center")
            for c in ("tp", "fp", "fn", "tn"):
                ax_t.text(xc[c], y, str(r[c]), va="center", ha="right")
            ax_t.text(x_se, y, f"{so(se_u, 2, ngon_ngu)} [{so(se_lo, 2, ngon_ngu)}; {so(se_hi, 2, ngon_ngu)}]",
                      va="center", ha="center")
            ax_g.text(0.5, y, f"{so(sp_u, 2, ngon_ngu)} [{so(sp_lo, 2, ngon_ngu)}; {so(sp_hi, 2, ngon_ngu)}]",
                      va="center", ha="center")
            for a, u, lo, hi in ((ax_se, se_u, se_lo, se_hi), (ax_sp, sp_u, sp_lo, sp_hi)):
                a.plot([lo, hi], [y, y], color="#222222", lw=0.9)
                a.plot([u], [y], marker="s", ms=4.2, color="#333333")
            so_lieu_nc.append({"nghien_cuu": r["nghien_cuu"], "nhom": r["nhom"], "do_nhay": se_u,
                               "do_nhay_ktc": (se_lo, se_hi), "do_dac_hieu": sp_u, "do_dac_hieu_ktc": (sp_lo, sp_hi)})
        elif loai == "tom_tat":
            m = v
            for a, khoa in ((ax_se, "do_nhay"), (ax_sp, "do_dac_hieu")):
                u, (lo, hi) = m[khoa]["uoc_luong"], m[khoa]["ktc"]
                a.add_patch(mp.Polygon([(lo, y), (u, y + 0.32), (hi, y), (u, y - 0.32)], closed=True, fc="#1f1f1f"))
            ax_t.text(0.02, y, "Tóm tắt (mô hình hai biến)" if ngon_ngu == "vi" else "Summary (bivariate model)",
                      va="center", weight="bold")
            ax_t.text(x_se, y, _chu_p(m["do_nhay"], ngon_ngu), va="center", ha="center", weight="bold")
            ax_g.text(0.5, y, _chu_p(m["do_dac_hieu"], ngon_ngu), va="center", ha="center", weight="bold")
    for a, ten in ((ax_se, nhan("do_nhay", ngon_ngu)), (ax_sp, nhan("do_dac_hieu", ngon_ngu))):
        a.set_xlim(0, 1)
        a.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
        BC.dinh_dang_truc(a, ngon_ngu, "x", nd=1)
        a.set_yticks([])
        a.spines["left"].set_visible(False)
        a.set_xlabel(ten)
    so_lieu = {"loai": "dta_forest", "ngon_ngu": ngon_ngu, "nghien_cuu": so_lieu_nc,
               "phuong_phap_ktc": "Clopper–Pearson (chính xác)",
               "tom_tat": {k: {"do_nhay": v["do_nhay"], "do_dac_hieu": v["do_dac_hieu"]} for k, v in
                           (tom_tat or {}).items()}}
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


def ve_sroc(ds: Sequence[Dict[str, Any]], dich: Path, kieu: str = "rutter-gatsonis", ngon_ngu: str = "vi",
            hieu_chinh: str = "chi_o_0", tieu_de: str = "") -> Dict[str, Any]:
    """SROC nhiều xét nghiệm/nhóm trên một hình: chấm nghiên cứu (diện tích ∝ cỡ mẫu), điểm tóm tắt, vùng tin cậy
    95% (nét đứt), vùng dự báo 95% (chấm), đường SROC trong khoảng FPR quan sát."""
    from matplotlib.lines import Line2D  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    if kieu not in ("rutter-gatsonis", "reitsma"):
        raise LoiBieuDo("kieu đường SROC: rutter-gatsonis | reitsma")
    plt = BC.plt_chuan()
    nhom_ds = list(dict.fromkeys(r["nhom"] for r in ds))
    n_max = max(r["tp"] + r["fp"] + r["fn"] + r["tn"] for r in ds)
    fig, ax = plt.subplots(figsize=(5.6, 5.6))
    ket: Dict[str, Any] = {}
    chu_giai = []
    for i, gn in enumerate(nhom_ds):
        cac = [r for r in ds if r["nhom"] == gn]
        mau, dau = MAU[i % len(MAU)], DAU[i % len(DAU)]
        fpr = [r["fp"] / (r["fp"] + r["tn"]) for r in cac]
        tpr = [r["tp"] / (r["tp"] + r["fn"]) for r in cac]
        n_ = [r["tp"] + r["fp"] + r["fn"] + r["tn"] for r in cac]
        ax.scatter(fpr, tpr, s=[12 + 110 * x / n_max for x in n_], facecolor="none", edgecolor=mau, lw=0.8,
                   marker=dau, alpha=0.85, zorder=2)
        muc: Dict[str, Any] = {"k": len(cac), "nghien_cuu": [
            {"nghien_cuu": r["nghien_cuu"], "fpr": f, "tpr": t, "n": m} for r, f, t, m in zip(cac, fpr, tpr, n_)]}
        if len(cac) >= 4:
            m = hai_bien(cac, hieu_chinh)
            fpr_hc = [_expit(-logit_dta(r, hieu_chinh)[2]) for r in cac]
            xs, ys = duong_sroc(m, min(fpr_hc), max(fpr_hc), kieu)
            ax.plot(xs, ys, color=mau, lw=1.4, zorder=3)
            ex, ey = elip(m, "tin_cay")
            ax.plot(ex, ey, color=mau, lw=1.0, ls=(0, (5, 2.5)), zorder=3)
            px, py = elip(m, "du_bao")
            ax.plot(px, py, color=mau, lw=0.9, ls=(0, (1, 1.6)), zorder=3)
            ax.plot([1 - m["do_dac_hieu"]["uoc_luong"]], [m["do_nhay"]["uoc_luong"]], marker=dau, ms=8.5, color=mau,
                    mec="black", mew=0.7, zorder=4)
            muc.update({"mo_hinh": m, "auc_sroc": auc_sroc(m, kieu), "khoang_fpr_duong": (min(fpr_hc), max(fpr_hc)),
                        "duong": {"fpr": xs, "tpr": ys}})
        else:
            muc.update({"mo_hinh": None, "ghi_chu": "dưới 4 nghiên cứu — chỉ vẽ chấm, không ước lượng tóm tắt"})
        ket[gn or "_"] = muc
        if gn:
            chu_giai.append(Line2D([], [], color=mau, marker=dau, mec="black", lw=1.4, ms=7, label=gn))
    chu_giai += [
        Line2D([], [], color="#333333", marker="o", ls="none", mec="black", ms=7, label=nhan("diem_tom_tat", ngon_ngu)),
        Line2D([], [], color="#333333", lw=1.4, label=nhan("duong_sroc", ngon_ngu)),
        Line2D([], [], color="#333333", lw=1.0, ls=(0, (5, 2.5)), label=nhan("vung_tin_cay", ngon_ngu)),
        Line2D([], [], color="#333333", lw=0.9, ls=(0, (1, 1.6)), label=nhan("vung_du_bao", ngon_ngu)),
        Line2D([], [], color="#333333", marker="o", ls="none", mfc="none", ms=6, label=nhan("nghien_cuu", ngon_ngu)),
    ]
    ax.legend(handles=chu_giai, loc="lower right", frameon=False, fontsize=8)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_aspect("equal")
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    BC.dinh_dang_truc(ax, ngon_ngu, "xy", nd=1)
    ax.set_xlabel(nhan("mot_tru_dac_hieu", ngon_ngu))
    ax.set_ylabel(nhan("do_nhay", ngon_ngu))
    ax.spines["top"].set_visible(True)
    ax.spines["right"].set_visible(True)
    if tieu_de:
        ax.set_title(tieu_de)
    so_lieu = {"loai": "sroc", "kieu_duong": kieu, "hieu_chinh": hieu_chinh, "ngon_ngu": ngon_ngu, "nhom": ket,
               "phuong_phap": "Mô hình hai biến hiệu ứng ngẫu nhiên (Reitsma 2005), REML; vùng 95% theo χ² 2 bậc tự "
                              "do; đường SROC chỉ trong khoảng FPR quan sát. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


def ve_deeks(ds: Sequence[Dict[str, Any]], dich: Path, ngon_ngu: str = "vi") -> Dict[str, Any]:
    """Funnel Deeks: DOR (trục log) theo 1/√ESS, đường hồi quy, kết quả kiểm định độ dốc."""
    import numpy as np  # noqa: PLC0415
    from matplotlib.ticker import FuncFormatter  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    d = deeks(ds)
    fig, ax = plt.subplots(figsize=(5.0, 4.2))
    yv = np.array(d["nghich_can_ess"])
    ax.scatter(np.exp(d["ln_dor"]), yv, s=24, facecolor="#333333", edgecolor="#111111", lw=0.5, zorder=3)
    yy = np.linspace(0, yv.max() * 1.08, 50)
    ax.plot(np.exp(d["chan"] + d["doc"] * yy), yy, color="#222222", lw=0.9)
    ax.set_xscale("log")
    ax.set_ylim(yv.max() * 1.08, 0)
    ax.set_xlabel("Tỷ số chênh chẩn đoán (DOR, thang log)" if ngon_ngu == "vi" else "Diagnostic odds ratio (log scale)")
    ax.set_ylabel("1/√ESS")
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: _nhan_vach(v, ngon_ngu)))
    ax.text(0.02, 0.02, f"Deeks: t = {so(d['t'], 2, ngon_ngu)} (df = {d['df']}), {BC.p_chu(d['p'], ngon_ngu)}",
            transform=ax.transAxes, fontsize=8)
    so_lieu = {"loai": "deeks", **d, "ghi_chu": "p < 0,10 gợi ý bất đối xứng (Deeks 2005). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=so_lieu)
    return so_lieu


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5. KIỂM CHÉO R
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def kiem_cheo_gop_r(yi: Sequence[float], vi: Sequence[float], phuong_phap: str = "REML",
                    hk: bool = False) -> Dict[str, Any]:
    """Chạy metafor trên CHÍNH yi/vi đã tính, đối chiếu từng số (mu, se, τ², I², Q, KTC, PI, Egger, trim-and-fill)."""
    g = gop(yi, vi, phuong_phap, hk)
    eg = egger(yi, vi)
    py = {"mu": g["mu"], "se": g["se"], "tau2": g["tau2"], "I2": g["I2"], "Q": g["Q"], "ci_lb": g["ktc"][0],
          "ci_ub": g["ktc"][1]}
    if g["khoang_du_bao"] and not hk:
        py.update({"pi_lb": g["khoang_du_bao"][0], "pi_ub": g["khoang_du_bao"][1]})
    if eg.get("p") is not None:
        py["egger_p"] = eg["p"]
    co_tf = len(yi) >= 3
    if co_tf:
        tfk = trim_fill(yi, vi, phuong_phap)
        py.update({"tf_k0": float(tfk["k0"]), "tf_mu": tfk["gop_sau_bu"]["mu"]})
    method = phuong_phap.upper()
    ma = f"""suppressMessages(library(metafor))
yi <- {BC.r_vec(yi)}; vi <- {BC.r_vec(vi)}
r <- rma(yi, vi, method="{method}"{', test="knha"' if hk else ''})
cat("KQ mu", r$beta[1], "\\n"); cat("KQ se", r$se, "\\n"); cat("KQ tau2", r$tau2, "\\n")
cat("KQ I2", r$I2, "\\n"); cat("KQ Q", r$QE, "\\n"); cat("KQ ci_lb", r$ci.lb, "\\n"); cat("KQ ci_ub", r$ci.ub, "\\n")
k <- length(yi)
if (k >= 3 && "{method}" != "FE") {{ q <- qt(.975, k-2); w <- sqrt(r$tau2 + r$se^2)
  cat("KQ pi_lb", r$beta[1] - q*w, "\\n"); cat("KQ pi_ub", r$beta[1] + q*w, "\\n") }}
if (k >= 3) {{ e <- regtest(r, model="lm", predictor="sei"); cat("KQ egger_p", e$pval, "\\n") }}
if ({'TRUE' if co_tf else 'FALSE'}) {{ t <- trimfill(rma(yi, vi, method="{method}"))
  cat("KQ tf_k0", t$k0, "\\n"); cat("KQ tf_mu", t$beta[1], "\\n") }}
"""
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-4)


def kiem_cheo_dta_r(ds: Sequence[Dict[str, Any]], hieu_chinh: str = "chi_o_0") -> Dict[str, Any]:
    """metafor::rma.mv hai biến (struct UN, REML) trên CÙNG logit/phương sai đã tính."""
    m = hai_bien(ds, hieu_chinh)
    L = [logit_dta(r, hieu_chinh) for r in ds]
    ma = f"""suppressMessages(library(metafor))
y1 <- {BC.r_vec(x[0] for x in L)}; v1 <- {BC.r_vec(x[1] for x in L)}
y2 <- {BC.r_vec(x[2] for x in L)}; v2 <- {BC.r_vec(x[3] for x in L)}
n <- length(y1)
d <- data.frame(study=rep(seq_len(n), each=2), outcome=factor(rep(c("se","sp"), n)), yi=c(rbind(y1,y2)),
                vi=c(rbind(v1,v2)))
m <- rma.mv(yi, vi, mods=~ outcome - 1, random=~ outcome | study, struct="UN", data=d, method="REML")
cat("KQ mu1", m$beta[1], "\\n"); cat("KQ mu2", m$beta[2], "\\n"); cat("KQ se1", m$se[1], "\\n")
cat("KQ se2", m$se[2], "\\n"); cat("KQ tau2_1", m$tau2[1], "\\n"); cat("KQ tau2_2", m$tau2[2], "\\n")
cat("KQ rho", m$rho, "\\n"); cat("KQ cov12", vcov(m)[1,2], "\\n")
"""
    py = {"mu1": m["mu"][0], "mu2": m["mu"][1], "se1": m["se_mu"][0], "se2": m["se_mu"][1], "tau2_1": m["tau2"][0],
          "tau2_2": m["tau2"][1], "rho": m["rho"], "cov12": m["Vmu"][0][1]}
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-3)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _in_kiem_cheo(ten: str, kc: Dict[str, Any]) -> int:
    tt = kc["trang_thai"]
    if tt == "khong_kiem_cheo_duoc":
        print(f"⚪ {ten}: KHÔNG kiểm chéo được bằng R — {kc.get('ly_do', '')[:200]}")
        return 0
    print(f"{'✅' if tt == 'khop' else '❌'} {ten}: kiểm chéo R {tt} (dung sai {kc['dung_sai']:g})")
    for c in kc["chi_tiet"]:
        if not c["khop"]:
            print(f"   lệch {c['khoa']}: Python {c['python']!r} · R {c['r']!r}")
    return 0 if tt == "khop" else 1


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("forest", "pheu", "bo-tung-nc", "dta-forest", "sroc", "deeks"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--ra", required=True, type=Path, help="đường dẫn gốc (không đuôi) — ghi .png/.pdf/.json")
    ap.add_argument("--do", default="GEN", choices=tuple(TEN_DO))
    ap.add_argument("--phuong-phap", default="REML", choices=("REML", "DL", "FE"))
    ap.add_argument("--hk", action="store_true", help="Hartung–Knapp–Sidik–Jonkman cho KTC của ước lượng gộp")
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    ap.add_argument("--nhan-trai", default="")
    ap.add_argument("--nhan-phai", default="")
    ap.add_argument("--tieu-de", default="")
    ap.add_argument("--duong-vien", action="store_true", help="funnel: tô vùng ý nghĩa quanh 0 (contour-enhanced)")
    ap.add_argument("--trim-fill", action="store_true")
    ap.add_argument("--duong", default="rutter-gatsonis", choices=("rutter-gatsonis", "reitsma"))
    ap.add_argument("--hieu-chinh", default="chi_o_0", choices=("chi_o_0", "tat_ca", "khong"))
    ap.add_argument("--kiem-cheo-r", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        dong = doc_csv(a.du_lieu)
        ma_kc = 0
        if a.lenh in ("forest", "pheu", "bo-tung-nc"):
            ds, loai = chuan_bi_gop(dong, a.do)
            if a.lenh == "forest":
                sl = ve_forest(ds, a.do, a.ra, a.phuong_phap, a.hk, a.ngon_ngu, a.nhan_trai, a.nhan_phai, a.tieu_de,
                               loai)
                g = sl["gop"]
                print(f"✅ forest: k = {g['k']} · {a.do} = {so(g['uoc_luong'], 2)} [{so(g['ktc'][0], 2)}; "
                      f"{so(g['ktc'][1], 2)}] · I² = {so(g['I2'], 0)}% → {a.ra.with_suffix('.png')}")
            elif a.lenh == "pheu":
                sl = ve_pheu(ds, a.do, a.ra, a.phuong_phap, a.duong_vien, a.trim_fill, a.ngon_ngu)
                print(f"✅ phễu: Egger p = {so(sl['egger'].get('p'), 3)} → {a.ra.with_suffix('.png')}")
            else:
                ve_bo_tung_nc(ds, a.do, a.ra, a.phuong_phap, a.ngon_ngu)
                print(f"✅ bỏ-từng-nghiên-cứu → {a.ra.with_suffix('.png')}")
            for x in loai:
                print(f"   ⚠ {x}")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("gộp", kiem_cheo_gop_r([e["yi"] for e in ds], [e["vi"] for e in ds],
                                                             a.phuong_phap, a.hk))
        else:
            ds = chuan_bi_dta(dong)
            nhom = list(dict.fromkeys(r["nhom"] for r in ds))
            if a.lenh == "dta-forest":
                tom = {gn: hai_bien([r for r in ds if r["nhom"] == gn], a.hieu_chinh) for gn in nhom
                       if sum(r["nhom"] == gn for r in ds) >= 4}
                ve_dta_forest(ds, a.ra, a.ngon_ngu, tom)
                print(f"✅ forest cặp Se/Sp: {len(ds)} nghiên cứu → {a.ra.with_suffix('.png')}")
            elif a.lenh == "sroc":
                sl = ve_sroc(ds, a.ra, a.duong, a.ngon_ngu, a.hieu_chinh, a.tieu_de)
                for gn, m in sl["nhom"].items():
                    if m.get("mo_hinh"):
                        mh = m["mo_hinh"]
                        print(f"✅ SROC {gn if gn != '_' else ''}: k = {mh['k']} · "
                              f"Se = {_chu_p(mh['do_nhay'], 'vi')} · Sp = {_chu_p(mh['do_dac_hieu'], 'vi')} · "
                              f"AUC = {so(m['auc_sroc'], 3)}")
                        for cb in mh["canh_bao"]:
                            print(f"   ⚠ {cb}")
                print(f"   → {a.ra.with_suffix('.png')}")
            else:
                sl = ve_deeks(ds, a.ra, a.ngon_ngu)
                print(f"✅ Deeks: p = {so(sl['p'], 3)} → {a.ra.with_suffix('.png')}")
            if a.kiem_cheo_r and a.lenh in ("sroc", "dta-forest"):
                for gn in nhom:
                    cac = [r for r in ds if r["nhom"] == gn]
                    if len(cac) >= 4:
                        ma_kc = max(ma_kc, _in_kiem_cheo(f"hai biến {gn}".strip(), kiem_cheo_dta_r(cac, a.hieu_chinh)))
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return ma_kc


if __name__ == "__main__":
    sys.exit(main())
