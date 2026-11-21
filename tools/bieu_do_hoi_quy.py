#!/usr/bin/env python3
"""Biểu đồ HỒI QUY — forest ước lượng thô/hiệu chỉnh, phân nhóm, spline đáp ứng liều, xác suất dự báo của mô hình
logistic thứ tự, chẩn đoán hồi quy tuyến tính (chặng 4b chương trình biểu đồ, bác sĩ 21/11/2026).

Họ biểu đồ (PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  forest-uoc-luong  forest từ BẢNG ước lượng (OR/PR/RR/HR/β) theo biến và mức, dòng «tham chiếu», hai mô hình (thô ·
                    hiệu chỉnh) cạnh nhau; cột chữ ước lượng [KTC] và p.
  nhom-nho          forest phân nhóm (subgroup) từ bảng: n, ước lượng [KTC] từng phân nhóm, p tương tác mỗi biến phân
                    nhóm (CONSORT/STROBE: phân tích nhóm nhỏ phải kèm kiểm định tương tác).
  spline            đường đáp ứng liều bằng spline bậc ba giới hạn (Harrell; nút ở phân vị 5–35–65–95 cho 4 nút) trong
                    hồi quy logistic (OR) hoặc tuyến tính (hiệu số), hiệu chỉnh biến kèm; so với giá trị tham chiếu
                    (mặc định trung vị); dải KTC 95% (delta); kiểm định phi tuyến Wald; phân bố phơi nhiễm ở dải dưới —
                    khớp rms::lrm/ols + Predict(ref.zero = TRUE) + anova.
  xac-suat-thu-tu   xác suất dự báo từng mức kết cục của mô hình logistic tỷ lệ chênh (proportional odds) theo một
                    phơi nhiễm, biến kèm cố định — khớp MASS::polr predict(type = "probs").
  chan-doan-lm      bốn đồ thị chẩn đoán hồi quy tuyến tính (phần dư – giá trị dự báo, Q-Q phần dư chuẩn hoá, scale-
                    location, phần dư – đòn bẩy kèm đường Cook 0,5/1) — khớp hatvalues/rstandard/cooks.distance.

Độ chính xác: test giữ giá trị chuẩn của R (rms, MASS, stats) trên MASS::birthwt (công khai). Không có R ⇒ «không
kiểm chéo được». Cần bác sĩ kiểm chứng.

Dữ liệu vào:
  forest-uoc-luong: CSV cột bien, muc, uoc_luong, duoi, tren, p, mo_hinh (để trống ước lượng ⇒ dòng tham chiếu).
  nhom-nho: CSV cột bien, muc, n, uoc_luong, duoi, tren, p_tuong_tac (p_tuong_tac ghi ở một dòng bất kỳ của biến).
  spline / xac-suat-thu-tu / chan-doan-lm: CSV từng đối tượng.

Lệnh:
  python3 tools/bieu_do_hoi_quy.py forest-uoc-luong --du-lieu bang.csv --do OR --ra …
  python3 tools/bieu_do_hoi_quy.py nhom-nho --du-lieu bang.csv --do HR --ra …
  python3 tools/bieu_do_hoi_quy.py spline --du-lieu d.csv --ket-cuc low --phoi-nhiem lwt --bien-kem smoke
      [--so-nut 4] [--tham-chieu 121] [--tuyen-tinh] --ra …
  python3 tools/bieu_do_hoi_quy.py xac-suat-thu-tu --du-lieu d.csv --ket-cuc hai_long --phoi-nhiem thoi_gian_cho
      [--bien-kem tuoi] [--gia-tri-kem tuoi=45] --ra …
  python3 tools/bieu_do_hoi_quy.py chan-doan-lm --du-lieu d.csv --ket-cuc bwt --bien-doc-lap lwt,smoke,age --ra …
Mã thoát: 0 xong · 1 kiểm chéo R LỆCH · 2 dữ liệu sai/thiếu · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import bieu_do_chung as BC  # noqa: E402
from bieu_do_chung import LoiBieuDo, so  # noqa: E402
from bieu_do_mo_ta import THIEU, doc_csv, so_hoc  # noqa: E402

Z975 = 1.959963984540054
MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")
TY_SO = ("OR", "PR", "RR", "HR", "IRR")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. FOREST TỪ BẢNG ƯỚC LƯỢNG · PHÂN NHÓM
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _f(v: str) -> Optional[float]:
    return None if v in THIEU else so_hoc(v, "ước lượng")


def doc_bang_uoc_luong(dong: Sequence[Dict[str, str]], do: str) -> Dict[str, Any]:
    """Gom theo biến → mức → mô hình. Kiểm tính hợp lệ: dưới ≤ ước lượng ≤ trên; tỷ số phải > 0."""
    if not dong:
        raise LoiBieuDo("bảng ước lượng rỗng")
    for c in ("bien", "muc", "uoc_luong", "duoi", "tren"):
        if c not in dong[0]:
            raise LoiBieuDo(f"bảng thiếu cột «{c}»")
    mo_hinh = list(dict.fromkeys((r.get("mo_hinh") or "").strip() for r in dong))
    bien: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for r in dong:
        u, lo, hi = _f(r["uoc_luong"]), _f(r["duoi"]), _f(r["tren"])
        ten = f"{r['bien']} – {r['muc']}"
        if u is not None:
            if lo is None or hi is None or not (lo <= u <= hi):
                raise LoiBieuDo(f"{ten}: cần dưới ≤ ước lượng ≤ trên")
            if do in TY_SO and lo <= 0:
                raise LoiBieuDo(f"{ten}: tỷ số phải > 0")
        bien.setdefault(r["bien"], {}).setdefault(r["muc"], {})[(r.get("mo_hinh") or "").strip()] = {
            "u": u, "lo": lo, "hi": hi, "p": _f(r.get("p", "")) if r.get("p") not in (None, "") else None,
            "n": r.get("n", ""), "p_tuong_tac": _f(r.get("p_tuong_tac", "")) if r.get("p_tuong_tac") else None}
    return {"bien": bien, "mo_hinh": mo_hinh}


def ve_forest_uoc_luong(dong, do: str, dich: Path, ngon_ngu: str = "vi", nhom_nho: bool = False,
                        tieu_de: str = "") -> Dict[str, Any]:
    from bieu_do_gop import _gioi_han_truc, _truc_log  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    b = doc_bang_uoc_luong(dong, do)
    mh = b["mo_hinh"]
    log = do in TY_SO
    ref = 1.0 if log else 0.0
    hang: List[Tuple[str, Any]] = []
    for ten_b, muc in b["bien"].items():
        p_tt = next((v["p_tuong_tac"] for m in muc.values() for v in m.values() if v.get("p_tuong_tac") is not None),
                    None)
        hang.append(("bien", (ten_b, p_tt)))
        for ten_m, theo_mh in muc.items():
            hang.append(("muc", (ten_m, theo_mh)))
    n = len(hang)
    rong_chu = 2.2 * len(mh)
    dai = max(len(str(v[0])) for _, v in hang)
    rong_trai = min(3.0, 0.075 * dai + 0.7 + (0.4 if nhom_nho else 0))
    fig = plt.figure(figsize=(rong_trai + 3.2 + rong_chu, 0.26 * (n + 2) + 0.7))
    gs = fig.add_gridspec(1, 3, width_ratios=[rong_trai, 3.2, rong_chu], wspace=0.03)
    ax_t, ax, ax_p = fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), fig.add_subplot(gs[2])
    for a in (ax_t, ax_p):
        a.axis("off")
        a.set_xlim(0, 1)
    for a in (ax_t, ax, ax_p):
        a.set_ylim(-0.6, n + 0.9)
    ax_t.text(0, n + 0.4, "Biến / mức" if vi else "Variable / level", weight="bold", va="center")
    if nhom_nho:
        ax_t.text(0.97, n + 0.4, "n", weight="bold", va="center", ha="right")
    for j, m in enumerate(mh):
        dau = ("■ ", "● ", "◆ ")[j % 3] if len(mh) > 1 else ""
        ax_p.text((j + 0.04) / len(mh), n + 0.4, dau + (m or do) + f" [{BC.nhan('ktc95', ngon_ngu)}]", weight="bold",
                  va="center", fontsize=8.5, color=MAU[j % len(MAU)] if len(mh) > 1 else "#222222")
    lo_all, hi_all = [ref], [ref]
    for _, v in hang:
        if isinstance(v[1], dict):
            for e in v[1].values():
                if e["u"] is not None:
                    lo_all.append(e["lo"])
                    hi_all.append(e["hi"])
    x_min, x_max = _gioi_han_truc(lo_all, hi_all, log, ref)
    lech = {m: (j - (len(mh) - 1) / 2) * 0.22 for j, m in enumerate(mh)}
    so_lieu = []
    for i, (loai, v) in enumerate(hang):
        y = n - 1 - i
        if loai == "bien":
            ten_b, p_tt = v
            ax_t.text(0, y, ten_b, weight="bold", va="center")
            if p_tt is not None:
                ax_p.text(0.98, y, f"{'p tương tác' if vi else 'p interaction'} {BC.p_chu(p_tt, ngon_ngu)[2:]}",
                          va="center", ha="right", fontsize=7.8, style="italic")
            continue
        ten_m, theo_mh = v
        ax_t.text(0.05, y, ten_m, va="center")
        for j, m in enumerate(mh):
            e = theo_mh.get(m)
            if e is None:
                continue
            if nhom_nho and e.get("n"):
                ax_t.text(0.97, y, str(e["n"]), va="center", ha="right")
            if e["u"] is None:
                ax_p.text((j + 0.04) / len(mh), y, ("1 (tham chiếu)" if log else "0 (tham chiếu)") if vi else
                          ("1 (reference)" if log else "0 (reference)"), va="center", color="#555555", fontsize=8)
                so_lieu.append({"bien": hang[[k for k in range(i, -1, -1) if hang[k][0] == "bien"][0]][1][0],
                                "muc": ten_m, "mo_hinh": m, "tham_chieu": True})
                continue
            yy = y + lech[m]
            l2, h2 = BC.mui_ten_vuot(ax, yy, x_min, x_max, e["lo"], e["hi"], log)
            ax.plot([l2, h2], [yy, yy], color=MAU[j % len(MAU)], lw=1.0)
            ax.plot([e["u"]], [yy], marker=("s", "o", "D")[j % 3], ms=4.6, color=MAU[j % len(MAU)])
            chu = f"{so(e['u'], 2, ngon_ngu)} [{so(e['lo'], 2, ngon_ngu)}; {so(e['hi'], 2, ngon_ngu)}]"
            if e.get("p") is not None:
                chu += f"; {BC.p_chu(e['p'], ngon_ngu)}"
            ax_p.text((j + 0.04) / len(mh), y, chu, va="center", fontsize=8, color=MAU[j % len(MAU)] if len(mh) > 1
                      else "#222222")
            so_lieu.append({"muc": ten_m, "mo_hinh": m, "uoc_luong": e["u"], "ktc": (e["lo"], e["hi"]), "p": e["p"]})
    ax.axvline(ref, color="#555555", lw=0.8, zorder=0)
    if log:
        _truc_log(ax, x_min, x_max, ngon_ngu)
    else:
        BC.dinh_dang_truc(ax, ngon_ngu, "x")
    ax.set_xlim(x_min, x_max)
    ax.set_yticks([])
    ax.spines["left"].set_visible(False)
    from bieu_do_gop import TEN_DO  # noqa: PLC0415

    ten_do = {"PR": ("Tỷ số tỷ lệ hiện mắc", "Prevalence ratio"), "IRR": ("Tỷ số tỷ suất", "Incidence rate ratio"),
              "B": ("Hệ số β", "β coefficient")}.get(do)
    ax.set_xlabel(((ten_do[0] if vi else ten_do[1]) if ten_do else TEN_DO.get(do, TEN_DO["GEN"])["vi" if vi else "en"])
                  + f" ({BC.nhan('ktc95', ngon_ngu)})")
    if tieu_de:
        fig.suptitle(tieu_de, fontsize=10)
    kq = {"loai": "nhom_nho" if nhom_nho else "forest_uoc_luong", "thuoc_do": do, "mo_hinh": mh, "dong": so_lieu,
          "ghi_chu": "Vẽ đúng số trong bảng ước lượng (không ước lượng lại). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. SPLINE BẬC BA GIỚI HẠN (Harrell / Hmisc::rcspline.eval)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
PHAN_VI_NUT = {3: (0.10, 0.50, 0.90), 4: (0.05, 0.35, 0.65, 0.95), 5: (0.05, 0.275, 0.50, 0.725, 0.95),
               6: (0.05, 0.23, 0.41, 0.59, 0.77, 0.95), 7: (0.025, 0.1833, 0.3417, 0.50, 0.6583, 0.8167, 0.975)}


def nut_harrell(x: Sequence[float], k: int) -> List[float]:
    """Nút như rcspline.eval: phân vị (kiểu 7) theo bảng Harrell; n < 100 ⇒ nút ngoài cùng = giá trị thứ 5 từ hai
    đầu. Nút trùng ⇒ lỗi (phơi nhiễm quá ít giá trị khác nhau)."""
    import numpy as np  # noqa: PLC0415

    if k not in PHAN_VI_NUT:
        raise LoiBieuDo("số nút phải từ 3 đến 7")
    xs = np.sort(np.asarray(x, float))
    nut = [float(np.quantile(xs, q)) for q in PHAN_VI_NUT[k]]
    if len(xs) < 100:
        nut[0], nut[-1] = float(xs[4]), float(xs[-5])
    if len(set(nut)) < k:
        raise LoiBieuDo("nút spline trùng nhau — phơi nhiễm có quá ít giá trị khác nhau")
    return nut


def co_so_rcs(x, nut: Sequence[float]):
    """Ma trận cơ sở [x, X₂…X_{k−1}] của spline bậc ba giới hạn, chuẩn hoá chia (t_k − t₁)² (rcspline.eval norm = 2)."""
    import numpy as np  # noqa: PLC0415

    x = np.asarray(x, float)
    t = list(nut)
    k = len(t)
    d = (t[-1] - t[0]) ** 2
    cot = [x]
    for j in range(k - 2):
        a = np.clip(x - t[j], 0, None) ** 3
        b = np.clip(x - t[k - 2], 0, None) ** 3 * (t[k - 1] - t[j]) / (t[k - 1] - t[k - 2])
        c = np.clip(x - t[k - 1], 0, None) ** 3 * (t[k - 2] - t[j]) / (t[k - 1] - t[k - 2])
        cot.append((a - b + c) / d)
    return np.column_stack(cot)


def _ols(X, y):
    import numpy as np  # noqa: PLC0415

    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    r = y - X @ b
    s2 = float(r @ r) / (len(y) - X.shape[1])
    return b, XtX_inv * s2


def spline(x, y, kem=None, so_nut: int = 4, tham_chieu: Optional[float] = None, tuyen_tinh: bool = False,
           diem: int = 200) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415
    from bieu_do_chan_doan import _hoi_quy_logistic  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    nut = nut_harrell(x, so_nut)
    B = co_so_rcs(x, nut)
    X = np.column_stack([np.ones(len(y)), B] + ([kem] if kem is not None and kem.size else []))
    if tuyen_tinh:
        b, V = _ols(X, y)
    else:
        if set(np.unique(y).tolist()) - {0, 1}:
            raise LoiBieuDo("kết cục logistic phải là 0/1 (dùng --tuyen-tinh cho kết cục liên tục)")
        b, V = _hoi_quy_logistic(X, y)
    ks = B.shape[1]
    bs, Vs = b[1:1 + ks], V[1:1 + ks, 1:1 + ks]
    ref = float(np.median(x)) if tham_chieu is None else float(tham_chieu)
    xs = np.linspace(float(np.min(x)), float(np.max(x)), diem)
    D = co_so_rcs(xs, nut) - co_so_rcs([ref], nut)
    f = D @ bs
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, Vs, D))
    nl = bs[1:]
    chi2 = float(nl @ np.linalg.solve(Vs[1:, 1:], nl)) if ks > 1 else 0.0
    tf = (lambda z: z) if tuyen_tinh else np.exp
    return {"nut": nut, "tham_chieu": ref, "x": xs.tolist(), "uoc_luong": tf(f).tolist(),
            "duoi": tf(f - Z975 * se).tolist(), "tren": tf(f + Z975 * se).tolist(), "he_so": b.tolist(),
            "V_spline": Vs.tolist(),
            "phi_tuyen": {"chi2": chi2, "df": ks - 1, "p": float(stats.chi2.sf(chi2, ks - 1))},
            "tuyen_tinh": tuyen_tinh, "n": int(len(y))}


def du_doan_spline(kq: Dict[str, Any], x_moi: Sequence[float], ktc: bool = False):
    """OR (hoặc hiệu số) tại các điểm x_moi so với tham chiếu; ktc=True ⇒ (ước lượng, dưới, trên) theo delta."""
    import numpy as np  # noqa: PLC0415

    D = co_so_rcs(x_moi, kq["nut"]) - co_so_rcs([kq["tham_chieu"]], kq["nut"])
    f = D @ np.asarray(kq["he_so"][1:1 + len(kq["nut"]) - 1])
    tf = (lambda z: z) if kq["tuyen_tinh"] else np.exp
    if not ktc:
        return tf(f).tolist()
    se = np.sqrt(np.einsum("ij,jk,ik->i", D, np.asarray(kq["V_spline"]), D))
    return tf(f).tolist(), tf(f - Z975 * se).tolist(), tf(f + Z975 * se).tolist()


def ve_spline(x, y, dich: Path, ten_x: str, kem=None, so_nut: int = 4, tham_chieu: Optional[float] = None,
              tuyen_tinh: bool = False, ngon_ngu: str = "vi", don_vi: str = "", ten_kem: Sequence[str] = ()) -> Dict:

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    s = spline(x, y, kem, so_nut, tham_chieu, tuyen_tinh)
    fig = plt.figure(figsize=(5.8, 5.2))
    gs = fig.add_gridspec(2, 1, height_ratios=[4.2, 1.0], hspace=0.06)
    ax = fig.add_subplot(gs[0])
    axh = fig.add_subplot(gs[1], sharex=ax)
    ax.fill_between(s["x"], s["duoi"], s["tren"], color="#1f4e79", alpha=0.16, lw=0)
    ax.plot(s["x"], s["uoc_luong"], color="#1f4e79", lw=1.6)
    ax.axhline(0.0 if tuyen_tinh else 1.0, color="#555555", lw=0.8, ls="--")
    ax.axvline(s["tham_chieu"], color="#999999", lw=0.6, ls=":")
    if not tuyen_tinh:
        ax.set_yscale("log")
        from matplotlib.ticker import FuncFormatter  # noqa: PLC0415

        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _p: BC.so(v, 2 if v < 1 else 1, ngon_ngu).rstrip("0")
                                                   .rstrip(",.")))
    else:
        BC.dinh_dang_truc(ax, ngon_ngu, "y")
    for t in s["nut"]:
        ax.plot([t], [0.0 if tuyen_tinh else 1.0], marker="|", color="#a23b2a", ms=10, mew=1.2)
    ax.tick_params(labelbottom=False)
    ylab = ("Hiệu số so với tham chiếu" if vi else "Difference vs reference") if tuyen_tinh else \
        ("Tỷ số chênh so với tham chiếu (thang log)" if vi else "Odds ratio vs reference (log scale)")
    ax.set_ylabel(ylab)
    chu = [f"{'Tham chiếu' if vi else 'Reference'}: {ten_x} = {so(s['tham_chieu'], 1, ngon_ngu)}",
           f"{'Phi tuyến' if vi else 'Non-linearity'}: χ² = {so(s['phi_tuyen']['chi2'], 2, ngon_ngu)} "
           f"(df = {s['phi_tuyen']['df']}), {BC.p_chu(s['phi_tuyen']['p'], ngon_ngu)}",
           f"{len(s['nut'])} {'nút (|)' if vi else 'knots (|)'}" + (
               (f"; {'hiệu chỉnh' if vi else 'adjusted for'}: {', '.join(ten_kem)}") if ten_kem else "")]
    ax.text(0.02, 0.97, "\n".join(chu), transform=ax.transAxes, va="top", fontsize=7.6)
    axh.hist(x, bins=30, color="#9aa7b5", edgecolor="white", lw=0.3)
    axh.set_yticks([])
    axh.spines["left"].set_visible(False)
    BC.dinh_dang_truc(axh, ngon_ngu, "x")
    axh.set_xlabel(ten_x + (f" ({don_vi})" if don_vi else ""))
    s.update({"loai": "spline", "ghi_chu": "Spline bậc ba giới hạn (Harrell); KTC 95% phương pháp delta; kiểm định phi "
                                           "tuyến Wald (như anova của rms). Cần bác sĩ kiểm chứng."})
    BC.luu(fig, dich, so_lieu=s)
    return s


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. LOGISTIC TỶ LỆ CHÊNH (proportional odds) — như MASS::polr
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ty_le_chenh_thu_tu(y, X) -> Dict[str, Any]:
    """logit P(Y ≤ k) = ζ_k − Xβ (tham số hoá của polr). Ước lượng hợp lý cực đại bằng Newton (scipy, gradient giải
    tích); y là mức thứ tự 0..K−1."""
    import numpy as np  # noqa: PLC0415
    from scipy import optimize, special  # noqa: PLC0415

    K = int(y.max()) + 1
    if K < 3:
        raise LoiBieuDo("kết cục thứ tự cần ≥ 3 mức")
    p = X.shape[1]

    def _zeta(th):
        return np.cumsum(np.r_[th[0], np.exp(th[1:K - 1])])

    def _am_ll(par):
        b, z = par[:p], _zeta(par[p:])
        eta = X @ b
        tren = np.where(y < K - 1, special.expit(z[np.minimum(y, K - 2)] - eta), 1.0)
        duoi = np.where(y > 0, special.expit(z[np.maximum(y - 1, 0)] - eta), 0.0)
        return -float(np.sum(np.log(np.clip(tren - duoi, 1e-300, None))))

    tan = np.bincount(y, minlength=K).cumsum()[:-1] / len(y)
    z0 = special.logit(tan)
    x0 = np.r_[np.zeros(p), z0[0], np.log(np.diff(z0))]
    kq = optimize.minimize(_am_ll, x0, method="BFGS", options={"gtol": 1e-10, "maxiter": 5000})
    kq = optimize.minimize(_am_ll, kq.x, method="Nelder-Mead", options={"xatol": 1e-12, "fatol": 1e-14,
                                                                        "maxiter": 40000})
    return {"beta": kq.x[:p].tolist(), "zeta": _zeta(kq.x[p:]).tolist(), "K": K, "am_loglik": float(kq.fun)}


def xac_suat_thu_tu(m: Dict[str, Any], X_moi) -> List[List[float]]:
    import numpy as np  # noqa: PLC0415
    from scipy import special  # noqa: PLC0415

    eta = np.asarray(X_moi, float) @ np.asarray(m["beta"])
    cum = special.expit(np.asarray(m["zeta"])[None, :] - eta[:, None])
    cum = np.column_stack([np.zeros(len(eta)), cum, np.ones(len(eta))])
    return np.diff(cum, axis=1).tolist()


def ve_xac_suat_thu_tu(y_goc: Sequence[str], x, dich: Path, ten_x: str, kem=None, gia_tri_kem=None,
                       ten_kem: Sequence[str] = (), ngon_ngu: str = "vi", nhan_muc: Optional[Dict[str, str]] = None,
                       don_vi: str = "") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    muc = sorted(set(y_goc), key=lambda v: float(v) if v.replace(".", "", 1).lstrip("-").isdigit() else v)
    y = np.array([muc.index(v) for v in y_goc])
    X = np.column_stack([x] + ([kem] if kem is not None and kem.size else []))
    m = ty_le_chenh_thu_tu(y, X)
    xs = np.linspace(float(np.min(x)), float(np.max(x)), 120)
    gk = np.asarray(gia_tri_kem if gia_tri_kem is not None else (kem.mean(0) if kem is not None and kem.size else []),
                    float)
    Xm = np.column_stack([xs] + ([np.tile(gk, (len(xs), 1))] if gk.size else []))
    P = np.asarray(xac_suat_thu_tu(m, Xm))
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    from matplotlib import colormaps  # noqa: PLC0415

    cmap = colormaps["RdBu"]
    mau = [cmap(0.1 + 0.8 * i / (len(muc) - 1)) for i in range(len(muc))]
    ax.stackplot(xs, P.T, colors=mau, alpha=0.9, labels=[(nhan_muc or {}).get(v, v) for v in muc], lw=0)
    ax.set_xlim(float(xs[0]), float(xs[-1]))
    ax.set_ylim(0, 1)
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    BC.dinh_dang_truc(ax, ngon_ngu, "y", nd=1)
    ax.set_xlabel(ten_x + (f" ({don_vi})" if don_vi else ""))
    ax.set_ylabel("Xác suất dự báo (cộng dồn)" if vi else "Predicted probability (stacked)")
    h, lab = ax.get_legend_handles_labels()
    ax.legend(h[::-1], lab[::-1], frameon=False, fontsize=7.8, loc="center left", bbox_to_anchor=(1.01, 0.5))
    OR = math.exp(m["beta"][0])
    ax.set_title((f"OR chung theo mỗi đơn vị {ten_x} = {so(OR, 3, ngon_ngu)}" if vi else
                  f"Common OR per unit {ten_x} = {so(OR, 3, ngon_ngu)}") +
                 ((f"; {'cố định' if vi else 'fixed'} " + ", ".join(f"{t} = {so(v, 2, ngon_ngu)}" for t, v in
                                                                   zip(ten_kem, gk))) if gk.size else ""), fontsize=8.5)
    kq = {"loai": "xac_suat_thu_tu", "muc": muc, "mo_hinh": m, "x": xs.tolist(), "xac_suat": P.tolist(),
          "gia_tri_kem": gk.tolist(),
          "ghi_chu": "Mô hình tỷ lệ chênh (polr): logit P(Y ≤ k) = ζ_k − Xβ; OR > 1 nghĩa là "
                                                 "phơi nhiễm tăng ⇒ mức kết cục cao hơn. Kiểm giả định tỷ lệ chênh "
                                                 "(Brant) riêng. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. CHẨN ĐOÁN HỒI QUY TUYẾN TÍNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def chan_doan_lm(X, y) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    Xc = np.column_stack([np.ones(len(y)), X])
    n, p = Xc.shape
    H = Xc @ np.linalg.inv(Xc.T @ Xc) @ Xc.T
    h = np.diag(H)
    yhat = H @ y
    e = y - yhat
    s = math.sqrt(float(e @ e) / (n - p))
    rstd = e / (s * np.sqrt(1 - h))
    cook = rstd ** 2 * h / (p * (1 - h))
    return {"n": n, "p": p, "du_bao": yhat.tolist(), "phan_du": e.tolist(), "rstandard": rstd.tolist(),
            "hat": h.tolist(), "cook": cook.tolist()}


def ve_chan_doan_lm(X, y, dich: Path, ngon_ngu: str = "vi") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415
    from statsmodels.nonparametric.smoothers_lowess import lowess  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    d = chan_doan_lm(X, y)
    yh, e, r, h, ck = (np.asarray(d[k]) for k in ("du_bao", "phan_du", "rstandard", "hat", "cook"))
    fig, axs = plt.subplots(2, 2, figsize=(8.2, 7.0))
    a = axs[0, 0]
    a.scatter(yh, e, s=10, color="#1f4e79", alpha=0.7)
    lw = lowess(e, yh, frac=2 / 3, it=3)
    a.plot(lw[:, 0], lw[:, 1], color="#a23b2a", lw=1.1)
    a.axhline(0, color="#777777", lw=0.7, ls="--")
    a.set_xlabel("Giá trị dự báo" if vi else "Fitted values")
    a.set_ylabel("Phần dư" if vi else "Residuals")
    a = axs[0, 1]
    th = stats.norm.ppf([(i - 0.5) / len(r) for i in range(1, len(r) + 1)])
    a.scatter(th, np.sort(r), s=10, color="#1f4e79", alpha=0.7)
    a.plot([th[0], th[-1]], [th[0], th[-1]], color="#a23b2a", lw=1.0, ls="--")
    a.set_xlabel("Phân vị lý thuyết" if vi else "Theoretical quantiles")
    a.set_ylabel("Phần dư chuẩn hoá" if vi else "Standardised residuals")
    a = axs[1, 0]
    sq = np.sqrt(np.abs(r))
    a.scatter(yh, sq, s=10, color="#1f4e79", alpha=0.7)
    lw = lowess(sq, yh, frac=2 / 3, it=3)
    a.plot(lw[:, 0], lw[:, 1], color="#a23b2a", lw=1.1)
    a.set_xlabel("Giá trị dự báo" if vi else "Fitted values")
    a.set_ylabel("√|phần dư chuẩn hoá|" if vi else "√|standardised residuals|")
    a = axs[1, 1]
    a.scatter(h, r, s=10, color="#1f4e79", alpha=0.7)
    hh = np.linspace(max(1e-4, h.min() * 0.9), h.max() * 1.1, 100)
    for c in (0.5, 1.0):
        bien = np.sqrt(c * d["p"] * (1 - hh) / hh)
        a.plot(hh, bien, color="#a23b2a", lw=0.7, ls=":")
        a.plot(hh, -bien, color="#a23b2a", lw=0.7, ls=":")
    a.set_ylim(min(r.min(), -3) * 1.1, max(r.max(), 3) * 1.1)
    a.set_xlabel("Đòn bẩy (leverage)" if vi else "Leverage")
    a.set_ylabel("Phần dư chuẩn hoá" if vi else "Standardised residuals")
    for i in np.argsort(-ck)[:3]:
        a.annotate(str(i + 1), (h[i], r[i]), fontsize=7, xytext=(3, 3), textcoords="offset points")
    for a in axs.ravel():
        BC.dinh_dang_truc(a, ngon_ngu, "xy")
    fig.tight_layout()
    d.update({"loai": "chan_doan_lm", "cook_lon_nhat": [{"dong": int(i + 1), "cook": float(ck[i])}
                                                         for i in np.argsort(-ck)[:5]],
              "ghi_chu": "Như plot.lm: phần dư–dự báo, Q-Q, scale-location, phần dư–đòn bẩy (đường Cook 0,5 và 1). "
                         "Cần bác sĩ kiểm chứng."})
    BC.luu(fig, dich, so_lieu=d)
    return d


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5. KIỂM CHÉO R
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def kiem_cheo_spline_r(x, y, kem, ten_kem: Sequence[str], so_nut: int, tham_chieu: Optional[float],
                       tuyen_tinh: bool, x_moi: Sequence[float]) -> Dict[str, Any]:
    s = spline(x, y, kem, so_nut, tham_chieu, tuyen_tinh)
    py = {f"or{i}": v for i, v in enumerate(du_doan_spline(s, x_moi))}
    py["chi2"] = s["phi_tuyen"]["chi2"]
    kem_r = "".join(f", k{i} = {BC.r_vec(kem[:, i])}" for i in range(kem.shape[1])) if kem is not None and kem.size \
        else ""
    cong = "".join(f" + k{i}" for i in range(kem.shape[1])) if kem is not None and kem.size else ""
    co_dinh = "".join(f", k{i} = 0" for i in range(kem.shape[1])) if kem is not None and kem.size else ""
    ham = "ols" if tuyen_tinh else "lrm"
    ma = (f"suppressMessages(library(rms))\nd <- data.frame(y = {BC.r_vec(y)}, x = {BC.r_vec(x)}{kem_r})\n"
          f"dd <- datadist(d); dd$limits['Adjust to', 'x'] <- {s['tham_chieu']!r}; options(datadist = 'dd')\n"
          f"f <- {ham}(y ~ rcs(x, {so_nut}){cong}, data = d)\n"
          f"p <- as.data.frame(Predict(f, x = {BC.r_vec(x_moi)}{co_dinh}, ref.zero = TRUE"
          f"{'' if tuyen_tinh else ', fun = exp'}))\n"
          f"for (i in seq_len(nrow(p))) cat('KQ', paste0('or', i - 1), p$yhat[i], '\\n')\n"
          f"a <- anova(f); cat('KQ chi2', a[' Nonlinear', if ('{ham}' == 'ols') 'F' else 'Chi-Square'], '\\n')\n")
    if tuyen_tinh:
        py.pop("chi2")  # ols: anova dùng F, không so χ²
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-5)


def kiem_cheo_polr_r(y_goc: Sequence[str], x, kem, X_moi) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    muc = sorted(set(y_goc), key=lambda v: float(v) if v.replace(".", "", 1).lstrip("-").isdigit() else v)
    y = np.array([muc.index(v) for v in y_goc])
    X = np.column_stack([x] + ([kem] if kem is not None and kem.size else []))
    m = ty_le_chenh_thu_tu(y, X)
    P = xac_suat_thu_tu(m, X_moi)
    py = {f"p{i}_{j}": P[i][j] for i in range(len(P)) for j in range(len(P[0]))}
    cot_kem = "".join(f", k{i} = {BC.r_vec(kem[:, i])}" for i in range(kem.shape[1])) if kem is not None and kem.size \
        else ""
    cong = "".join(f" + k{i}" for i in range(kem.shape[1])) if kem is not None and kem.size else ""
    moi = ", ".join([f"x = {BC.r_vec([r[0] for r in X_moi])}"] +
                    [f"k{i} = {BC.r_vec([r[i + 1] for r in X_moi])}" for i in range(X.shape[1] - 1)])
    ma = (f"suppressMessages(library(MASS))\nd <- data.frame(y = factor({BC.r_vec(y)}), x = {BC.r_vec(x)}{cot_kem})\n"
          f"m <- polr(y ~ x{cong}, data = d, method = 'logistic')\n"
          f"p <- predict(m, newdata = data.frame({moi}), type = 'probs')\n"
          "for (i in seq_len(nrow(p))) for (j in seq_len(ncol(p))) cat('KQ', paste0('p', i - 1, '_', j - 1), p[i, j], "
          "'\\n')\n")
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-5)


def kiem_cheo_lm_r(X, y) -> Dict[str, Any]:
    d = chan_doan_lm(X, y)
    py = {}
    for i in (0, len(y) // 2, len(y) - 1):
        py[f"h{i}"], py[f"c{i}"], py[f"r{i}"] = d["hat"][i], d["cook"][i], d["rstandard"][i]
    cot = "".join(f", x{j} = {BC.r_vec(X[:, j])}" for j in range(X.shape[1]))
    ma = (f"d <- data.frame(y = {BC.r_vec(y)}{cot})\nm <- lm(y ~ ., data = d)\n"
          f"for (i in c({0}, {len(y) // 2}, {len(y) - 1})) {{ cat('KQ', paste0('h', i), hatvalues(m)[i + 1], '\\n'); "
          "cat('KQ', paste0('c', i), cooks.distance(m)[i + 1], '\\n'); "
          "cat('KQ', paste0('r', i), rstandard(m)[i + 1], '\\n') }\n")
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-8)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _ma_tran(dong, cot: Sequence[str]):
    """Lọc dòng đủ dữ liệu ở mọi cột cần; trả (dict cột → mảng, số dòng loại)."""
    import numpy as np  # noqa: PLC0415

    giu = [r for r in dong if all(r[c] not in THIEU for c in cot)]
    if len(giu) < 10:
        raise LoiBieuDo(f"chỉ {len(giu)} dòng đủ dữ liệu — quá ít để ước lượng")
    return {c: np.array([so_hoc(r[c], c) for r in giu]) for c in cot}, len(dong) - len(giu), giu


def main(argv: Optional[Sequence[str]] = None) -> int:
    import numpy as np  # noqa: PLC0415
    from bieu_do_gop import _in_kiem_cheo  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("forest-uoc-luong", "nhom-nho", "spline", "xac-suat-thu-tu", "chan-doan-lm"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--do", default="OR")
    ap.add_argument("--ket-cuc")
    ap.add_argument("--phoi-nhiem")
    ap.add_argument("--bien-kem", default="")
    ap.add_argument("--gia-tri-kem", default="")
    ap.add_argument("--bien-doc-lap", default="")
    ap.add_argument("--so-nut", type=int, default=4)
    ap.add_argument("--tham-chieu", type=float)
    ap.add_argument("--tuyen-tinh", action="store_true")
    ap.add_argument("--don-vi", default="")
    ap.add_argument("--tieu-de", default="")
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    ap.add_argument("--kiem-cheo-r", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    kem_ten = [c.strip() for c in a.bien_kem.split(",") if c.strip()]
    try:
        ma_kc = 0
        if a.lenh in ("forest-uoc-luong", "nhom-nho"):
            kq = ve_forest_uoc_luong(doc_csv(a.du_lieu), a.do.upper(), a.ra, a.ngon_ngu, a.lenh == "nhom-nho",
                                     a.tieu_de)
            print(f"✅ {a.lenh}: {len(kq['dong'])} dòng × {len(kq['mo_hinh'])} mô hình")
        elif a.lenh == "spline":
            if not (a.ket_cuc and a.phoi_nhiem):
                print("❌ spline cần --ket-cuc và --phoi-nhiem")
                return 3
            du, loai, _ = _ma_tran(doc_csv(a.du_lieu, [a.ket_cuc, a.phoi_nhiem, *kem_ten]),
                                   [a.ket_cuc, a.phoi_nhiem, *kem_ten])
            kem = np.column_stack([du[c] for c in kem_ten]) if kem_ten else None
            s = ve_spline(du[a.phoi_nhiem], du[a.ket_cuc] if a.tuyen_tinh else du[a.ket_cuc].astype(int), a.ra,
                          a.phoi_nhiem, kem, a.so_nut, a.tham_chieu, a.tuyen_tinh, a.ngon_ngu, a.don_vi, kem_ten)
            print(f"✅ spline {a.so_nut} nút {[round(t, 3) for t in s['nut']]} · "
                  f"phi tuyến p = {so(s['phi_tuyen']['p'], 3)}"
                  + (f" · loại {loai} dòng thiếu" if loai else ""))
            if a.kiem_cheo_r:
                xm = np.quantile(du[a.phoi_nhiem], [0.1, 0.3, 0.7, 0.9]).tolist()
                ma_kc = _in_kiem_cheo("spline (rms)", kiem_cheo_spline_r(
                    du[a.phoi_nhiem], du[a.ket_cuc], kem, kem_ten, a.so_nut, a.tham_chieu, a.tuyen_tinh, xm))
        elif a.lenh == "xac-suat-thu-tu":
            if not (a.ket_cuc and a.phoi_nhiem):
                print("❌ xac-suat-thu-tu cần --ket-cuc và --phoi-nhiem")
                return 3
            dong = doc_csv(a.du_lieu, [a.ket_cuc, a.phoi_nhiem, *kem_ten])
            du, loai, giu = _ma_tran(dong, [a.phoi_nhiem, *kem_ten])
            giu2 = [(r, i) for i, r in enumerate(giu) if r[a.ket_cuc] not in THIEU]
            idx = [i for _, i in giu2]
            y_goc = [r[a.ket_cuc] for r, _ in giu2]
            kem = np.column_stack([du[c][idx] for c in kem_ten]) if kem_ten else None
            gk = None
            if a.gia_tri_kem:
                gtd = dict(p.split("=") for p in a.gia_tri_kem.split(",") if "=" in p)
                gk = [float(gtd[c]) if c in gtd else float(kem[:, j].mean()) for j, c in enumerate(kem_ten)]
            kq = ve_xac_suat_thu_tu(y_goc, du[a.phoi_nhiem][idx], a.ra, a.phoi_nhiem, kem, gk, kem_ten, a.ngon_ngu,
                                    don_vi=a.don_vi)
            print(f"✅ xác suất dự báo {len(kq['muc'])} mức · OR chung = {so(math.exp(kq['mo_hinh']['beta'][0]), 3)}")
            if a.kiem_cheo_r:
                xs = np.quantile(du[a.phoi_nhiem][idx], [0.1, 0.5, 0.9])
                gkv = kq["gia_tri_kem"]
                ma_kc = _in_kiem_cheo("polr (MASS)", kiem_cheo_polr_r(y_goc, du[a.phoi_nhiem][idx], kem,
                                                                      [[v, *gkv] for v in xs]))
        else:
            dl = [c.strip() for c in a.bien_doc_lap.split(",") if c.strip()]
            if not (a.ket_cuc and dl):
                print("❌ chan-doan-lm cần --ket-cuc và --bien-doc-lap")
                return 3
            du, loai, _ = _ma_tran(doc_csv(a.du_lieu, [a.ket_cuc, *dl]), [a.ket_cuc, *dl])
            X = np.column_stack([du[c] for c in dl])
            d = ve_chan_doan_lm(X, du[a.ket_cuc], a.ra, a.ngon_ngu)
            print(f"✅ chẩn đoán lm: n = {d['n']}, Cook lớn nhất dòng {d['cook_lon_nhat'][0]['dong']} = "
                  f"{so(d['cook_lon_nhat'][0]['cook'], 3)}")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("chẩn đoán lm (R)", kiem_cheo_lm_r(X, du[a.ket_cuc]))
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return ma_kc


if __name__ == "__main__":
    sys.exit(main())
