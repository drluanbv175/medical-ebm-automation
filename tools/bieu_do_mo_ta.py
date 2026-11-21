#!/usr/bin/env python3
"""Biểu đồ MÔ TẢ số liệu nghiên cứu — tỷ lệ/trung bình kèm KTC, Likert, phân bố, tương quan, dữ liệu thiếu, theo thời
gian (chặng 4a chương trình biểu đồ, bác sĩ 21/11/2026: «phải thực hiện được tất cả biểu đồ một cách chi tiết và chính
xác nhất»; «tất cả vấn đề trong hệ thống nghiên cứu y khoa phải đạt sự toàn diện, tự động tốt nhất»).

Họ biểu đồ (PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  cot-ktc        cột tỷ lệ (KTC 95% Clopper–Pearson mặc định hoặc Wilson) hoặc trung bình (KTC t) theo nhóm; ghi
                 n/N trên cột. Không vẽ 3D, không «cột chồng giả».
  likert         thanh xếp chồng PHÂN KỲ cho câu hỏi thang Likert (khảo sát hài lòng, chất lượng sống): mức trung lập
                 nằm giữa trục 0, mức bất lợi sang trái, thuận lợi sang phải; ghi % từng mức, % thuận lợi gộp; câu hỏi
                 xếp theo % thuận lợi (tuỳ chọn giữ thứ tự bảng hỏi).
  phan-bo        histogram (kèm đường mật độ chuẩn cùng trung bình/ĐLC) · hộp · violin theo nhóm.
  qq             Q-Q chuẩn: điểm lý thuyết như qqnorm (ppoints), đường qua tứ phân vị như qqline, dải 95% từng điểm.
  tuong-quan     ma trận tương quan Pearson/Spearman (tam giác dưới, ghi hệ số và dấu * theo p).
  thieu          kiểu dữ liệu thiếu: % thiếu từng biến và các tổ hợp thiếu thường gặp (cho G5 / kế hoạch xử lý thiếu).
  theo-thoi-gian trung bình (KTC 95% t) theo thời điểm, mỗi nhóm một đường — nghiên cứu dọc, RCT đo lặp.

Độ chính xác: test giữ giá trị chuẩn của R (binom.test, prop.test, t.test, cor/cor.test, qqnorm/qqline);
`--kiem-cheo-r` chạy lại trên chính dữ liệu đề tài. Cần bác sĩ kiểm chứng.

Dữ liệu vào: CSV mỗi dòng một đối tượng. Ô trống / NA / «.» là thiếu.

Lệnh:
  python3 tools/bieu_do_mo_ta.py cot-ktc --du-lieu d.csv --bien hai_long --muc 1 [--nhom gioi] [--ktc wilson] --ra …
  python3 tools/bieu_do_mo_ta.py cot-ktc --du-lieu d.csv --bien tuoi --trung-binh [--nhom gioi] --ra …
  python3 tools/bieu_do_mo_ta.py likert --du-lieu d.csv --cot q1,q2,q3 --muc "1=Rất không hài lòng,2=Không hài lòng,
      3=Bình thường,4=Hài lòng,5=Rất hài lòng" [--nhan-cot "q1=Thời gian chờ,q2=Thái độ"] [--giu-thu-tu] --ra …
  python3 tools/bieu_do_mo_ta.py phan-bo --du-lieu d.csv --bien tuoi [--nhom gioi] [--kieu hist|hop|violin] --ra …
  python3 tools/bieu_do_mo_ta.py qq --du-lieu d.csv --bien tuoi --ra …
  python3 tools/bieu_do_mo_ta.py tuong-quan --du-lieu d.csv --cot a,b,c [--phuong-phap spearman] --ra …
  python3 tools/bieu_do_mo_ta.py thieu --du-lieu d.csv [--cot a,b,c] --ra …
  python3 tools/bieu_do_mo_ta.py theo-thoi-gian --du-lieu d.csv --thoi-diem lan_kham --bien hba1c [--nhom nhanh] --ra …
  (thêm --ngon-ngu en; --don-vi "mmHg"; --kiem-cheo-r)
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
from bieu_do_chung import LoiBieuDo, so  # noqa: E402

MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")
THIEU = {"", "NA", "na", "N/A", ".", "NaN", "nan"}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. ĐỌC DỮ LIỆU + THỐNG KÊ CƠ BẢN
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def doc_csv(p: Path, cot: Sequence[str] = ()) -> List[Dict[str, str]]:
    try:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            dong = [{(k or "").strip(): (v or "").strip() for k, v in r.items()} for r in csv.DictReader(fh)]
    except OSError as exc:
        raise LoiBieuDo(f"không đọc được {p}: {exc}") from exc
    if not dong:
        raise LoiBieuDo(f"{p}: không có dòng dữ liệu")
    thieu = [c for c in cot if c and c not in dong[0]]
    if thieu:
        raise LoiBieuDo(f"{p}: thiếu cột {', '.join(thieu)} (có: {', '.join(dong[0])})")
    return dong


def so_hoc(v: str, ten: str) -> float:
    try:
        return float(v.replace(",", "."))
    except ValueError as exc:
        raise LoiBieuDo(f"«{ten}» có giá trị không phải số: {v!r}") from exc


def ktc_ty_le(k: int, n: int, kieu: str = "clopper-pearson") -> Tuple[float, float]:
    """KTC 95% của k/n: Clopper–Pearson (= binom.test) hoặc Wilson không hiệu chỉnh (= prop.test(correct = FALSE))."""
    if n <= 0:
        raise LoiBieuDo("mẫu số bằng 0")
    if kieu == "clopper-pearson":
        from bieu_do_gop import clopper_pearson  # noqa: PLC0415

        return clopper_pearson(k, n)
    if kieu != "wilson":
        raise LoiBieuDo("ktc tỷ lệ: clopper-pearson | wilson")
    z = 1.959963984540054
    p = k / n
    tam = (p + z * z / (2 * n)) / (1 + z * z / n)
    nua = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return max(0.0, tam - nua), min(1.0, tam + nua)


def ktc_trung_binh(x: Sequence[float]) -> Dict[str, float]:
    """Trung bình, ĐLC và KTC 95% theo t (= t.test)."""
    from scipy import stats  # noqa: PLC0415

    n = len(x)
    if n < 2:
        raise LoiBieuDo("cần ≥ 2 giá trị để tính KTC trung bình")
    tb = sum(x) / n
    dlc = math.sqrt(sum((v - tb) ** 2 for v in x) / (n - 1))
    q = float(stats.t.ppf(0.975, n - 1)) * dlc / math.sqrt(n)
    return {"n": n, "trung_binh": tb, "dlc": dlc, "duoi": tb - q, "tren": tb + q}


def _cot_so(dong, ten: str) -> List[Optional[float]]:
    return [None if r[ten] in THIEU else so_hoc(r[ten], ten) for r in dong]


def thu_tu_nhom(g: Sequence[Optional[str]]) -> List[str]:
    """Nhóm là số (4, 6, 8; 1, 2, 3) ⇒ xếp tăng dần theo giá trị; nhóm chữ ⇒ giữ thứ tự xuất hiện trong dữ liệu."""
    ds = [k for k in dict.fromkeys(g) if k is not None]
    try:
        return sorted(ds, key=lambda k: float(k.replace(",", ".")))
    except (ValueError, AttributeError):
        return ds


def _nhom(dong, cot_nhom: Optional[str]) -> List[str]:
    if not cot_nhom:
        return [""] * len(dong)
    return [r[cot_nhom] if r[cot_nhom] not in THIEU else None for r in dong]


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. CỘT + KTC
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ve_cot_ktc(dong, bien: str, dich: Path, muc: Optional[str] = None, cot_nhom: Optional[str] = None,
               trung_binh: bool = False, ktc: str = "clopper-pearson", ngon_ngu: str = "vi", don_vi: str = "",
               nhan_bien: str = "") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    g = _nhom(dong, cot_nhom)
    nhom_ds = thu_tu_nhom(g)
    kq: Dict[str, Any] = {"loai": "cot_ktc", "bien": bien, "trung_binh": trung_binh, "nhom": {}, "thieu": 0}
    for k in nhom_ds:
        vals = [r[bien] for r, gg in zip(dong, g) if gg == k and r[bien] not in THIEU]
        kq["thieu"] += sum(1 for r, gg in zip(dong, g) if gg == k and r[bien] in THIEU)
        if trung_binh:
            kq["nhom"][k] = ktc_trung_binh([so_hoc(v, bien) for v in vals])
        else:
            if muc is None:
                raise LoiBieuDo("cột tỷ lệ cần --muc (mức được đếm, ví dụ 1 hoặc «Có»)")
            dem, n = sum(1 for v in vals if v == muc), len(vals)
            lo, hi = ktc_ty_le(dem, n, ktc)
            kq["nhom"][k] = {"k": dem, "n": n, "ty_le": dem / n, "duoi": lo, "tren": hi}
    fig, ax = plt.subplots(figsize=(max(3.6, 1.15 * len(nhom_ds) + 1.8), 3.9))
    x = list(range(len(nhom_ds)))
    if trung_binh:
        u = [kq["nhom"][k]["trung_binh"] for k in nhom_ds]
    else:
        u = [100 * kq["nhom"][k]["ty_le"] for k in nhom_ds]
    he = 1 if trung_binh else 100
    lo = [he * kq["nhom"][k]["duoi"] for k in nhom_ds]
    hi = [he * kq["nhom"][k]["tren"] for k in nhom_ds]
    ax.bar(x, u, width=0.58, color=[MAU[i % len(MAU)] for i in x], alpha=0.85, edgecolor="#222222", lw=0.6)
    ax.errorbar(x, u, yerr=[[a - b for a, b in zip(u, lo)], [c - a for a, c in zip(u, hi)]], fmt="none",
                ecolor="#111111", capsize=4, lw=0.9)
    for i, k in enumerate(nhom_ds):
        v = kq["nhom"][k]
        chu = (f"{so(v['trung_binh'], 1, ngon_ngu)}\n(n = {v['n']})" if trung_binh else
               f"{so(100 * v['ty_le'], 1, ngon_ngu)}%\n({v['k']}/{v['n']})")
        ax.text(i, hi[i] + (max(hi) * 0.02 if max(hi) > 0 else 0.5), chu, ha="center", va="bottom", fontsize=7.6)
    ax.set_xticks(x)
    ax.set_xticklabels([k or ("Toàn mẫu" if vi else "Overall") for k in nhom_ds])
    if not trung_binh:
        ax.set_ylim(0, min(100, max(hi) * 1.25 + 5))
        ax.set_ylabel(f"{nhan_bien or bien} = {muc} (%)")
    else:
        ax.set_ylim(min(0, min(lo) * 1.1), max(hi) * 1.25)
        ax.set_ylabel(f"{nhan_bien or bien}" + (f" ({don_vi})" if don_vi else "") + (" — trung bình" if vi else
                                                                                       " — mean"))
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    ax.yaxis.grid(True, color="#e5e5e5", lw=0.6)
    ax.set_axisbelow(True)
    kq["ghi_chu"] = (("KTC 95% theo t." if trung_binh else f"KTC 95% {ktc}.") + " Cần bác sĩ kiểm chứng.")
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. LIKERT PHÂN KỲ
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ty_le_likert(dong, cot: Sequence[str], muc: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """% từng mức trên tổng câu trả lời hợp lệ của câu hỏi; giá trị ngoài danh sách mức ⇒ lỗi (không âm thầm bỏ)."""
    ra = {}
    for c in cot:
        vals = [r[c] for r in dong if r[c] not in THIEU]
        la = sorted({v for v in vals if v not in muc})
        if la:
            raise LoiBieuDo(f"câu «{c}» có giá trị ngoài thang: {', '.join(la[:5])}")
        n = len(vals)
        if n == 0:
            raise LoiBieuDo(f"câu «{c}» không có câu trả lời")
        dem = {m: sum(1 for v in vals if v == m) for m in muc}
        ra[c] = {"n": n, "thieu": len(dong) - n, "dem": dem, "pt": {m: 100 * dem[m] / n for m in muc}}
    return ra


def ve_likert(dong, cot: Sequence[str], muc: Sequence[Tuple[str, str]], dich: Path,
              nhan_cot: Optional[Dict[str, str]] = None, giu_thu_tu: bool = False,
              ngon_ngu: str = "vi") -> Dict[str, Any]:
    """Thang lẻ: mức giữa là trung lập (chia đôi qua trục 0); thang chẵn: không có trung lập."""
    BC.kiem_ngon_ngu(ngon_ngu)
    if len(muc) < 2:
        raise LoiBieuDo("thang Likert cần ≥ 2 mức")
    plt = BC.plt_chuan()
    ma = [m for m, _ in muc]
    tl = ty_le_likert(dong, cot, ma)
    K = len(ma)
    giua = K // 2 if K % 2 else None
    am = ma[:K // 2]
    duong = ma[K // 2 + (1 if giua is not None else 0):]
    for c in cot:
        tl[c]["thuan_loi"] = sum(tl[c]["pt"][m] for m in duong)
        tl[c]["bat_loi"] = sum(tl[c]["pt"][m] for m in am)
    thu_tu = list(cot) if giu_thu_tu else sorted(cot, key=lambda c: tl[c]["thuan_loi"])
    from matplotlib import colormaps  # noqa: PLC0415

    cmap = colormaps["RdBu"]
    mau = [cmap(0.08 + 0.84 * i / (K - 1)) for i in range(K)]
    if giua is not None:
        mau[giua] = (0.82, 0.82, 0.82, 1.0)
    fig, ax = plt.subplots(figsize=(8.2, 0.42 * len(cot) + 1.6))
    for y, c in enumerate(thu_tu):
        pt = tl[c]["pt"]
        trai = -sum(pt[m] for m in am) - (pt[ma[giua]] / 2 if giua is not None else 0)
        tl[c]["bat_dau"] = trai  # mép trái thanh: mức trung lập chia đôi qua trục 0
        for i, m in enumerate(ma):
            w = pt[m]
            ax.barh(y, w, left=trai, color=mau[i], edgecolor="white", lw=0.5, height=0.66)
            if w >= 6:
                ax.text(trai + w / 2, y, so(w, 0, ngon_ngu), ha="center", va="center", fontsize=7,
                        color="white" if (i in (0, K - 1)) else "#222222")
            trai += w
    ax.axvline(0, color="#333333", lw=0.8, zorder=0)
    ax.set_yticks(range(len(thu_tu)))
    ax.tick_params(axis="y", length=0)
    ax.set_yticklabels([f"{(nhan_cot or {}).get(c, c)} (n = {tl[c]['n']})" for c in thu_tu])
    lim = max(max(tl[c]["thuan_loi"] + (tl[c]["pt"][ma[giua]] / 2 if giua is not None else 0),
                  tl[c]["bat_loi"] + (tl[c]["pt"][ma[giua]] / 2 if giua is not None else 0)) for c in cot)
    lim = min(100, math.ceil(lim / 10) * 10 + 5)
    ax.set_xlim(-lim, lim)
    vach = [v for v in range(-100, 101, 25 if lim > 60 else 20) if -lim <= v <= lim]
    ax.set_xticks(vach)
    ax.set_xticklabels([f"{abs(v)}%" for v in vach])
    ax.set_xlabel("Tỷ lệ câu trả lời (%)" if ngon_ngu == "vi" else "Responses (%)")
    for y, c in enumerate(thu_tu):
        ax.text(lim * 1.01, y, so(tl[c]["thuan_loi"], 0, ngon_ngu) + "%", va="center", fontsize=7.5, weight="bold")
    ax.text(lim * 1.01, len(thu_tu) - 0.35, "Thuận lợi" if ngon_ngu == "vi" else "Favourable", fontsize=7.5,
            va="bottom")
    import matplotlib.patches as mp  # noqa: PLC0415

    ax.legend(handles=[mp.Patch(color=mau[i], label=nh) for i, (_, nh) in enumerate(muc)], loc="upper center",
              bbox_to_anchor=(0.5, -0.12 - 0.02 * max(0, 6 - len(cot))), ncol=min(K, 5), frameon=False, fontsize=7.6)
    ax.spines["left"].set_visible(False)
    kq = {"loai": "likert", "muc": [{"ma": m, "nhan": nh} for m, nh in muc], "cau_hoi": tl, "thu_tu_ve": thu_tu,
          "ghi_chu": ("% tính trên câu trả lời hợp lệ của từng câu; mức trung lập chia đôi qua trục 0; "
                      "% thuận lợi = tổng các mức phía phải. Cần bác sĩ kiểm chứng.")}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. PHÂN BỐ · Q-Q
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ppoints(n: int) -> List[float]:
    """Điểm xác suất của qqnorm trong R: (i − a)/(n + 1 − 2a), a = 3/8 khi n ≤ 10, ngược lại 1/2."""
    a = 3 / 8 if n <= 10 else 0.5
    return [(i - a) / (n + 1 - 2 * a) for i in range(1, n + 1)]


def _phan_vi_7(xs: Sequence[float], q: float) -> float:
    """Phân vị kiểu 7 (mặc định của R quantile và numpy)."""
    s = sorted(xs)
    h = (len(s) - 1) * q
    lo = math.floor(h)
    return s[lo] + (h - lo) * (s[min(lo + 1, len(s) - 1)] - s[lo])


def qq_so_lieu(x: Sequence[float]) -> Dict[str, Any]:
    """Toạ độ Q-Q như qqnorm; đường như qqline (qua tứ phân vị 1 và 3); dải 95% từng điểm theo sai số chuẩn của
    thống kê thứ tự (Fox, car::qqPlot): SE = (độ dốc/φ(z))·√(p(1−p)/n)."""
    from scipy import stats  # noqa: PLC0415

    n = len(x)
    if n < 3:
        raise LoiBieuDo("Q-Q cần ≥ 3 giá trị")
    xs = sorted(x)
    z = [float(stats.norm.ppf(p)) for p in ppoints(n)]
    y1, y3 = _phan_vi_7(xs, 0.25), _phan_vi_7(xs, 0.75)
    z1, z3 = float(stats.norm.ppf(0.25)), float(stats.norm.ppf(0.75))
    doc = (y3 - y1) / (z3 - z1)
    chan = y1 - doc * z1
    se = [doc / float(stats.norm.pdf(zz)) * math.sqrt(p * (1 - p) / n) for zz, p in zip(z, ppoints(n))]
    return {"n": n, "ly_thuyet": z, "mau": xs, "chan": chan, "doc": doc,
            "dai_duoi": [chan + doc * zz - 1.959963984540054 * s for zz, s in zip(z, se)],
            "dai_tren": [chan + doc * zz + 1.959963984540054 * s for zz, s in zip(z, se)],
            "shapiro_p": float(stats.shapiro(xs).pvalue) if 3 <= n <= 5000 else None}


def ve_qq(x: Sequence[float], ten: str, dich: Path, ngon_ngu: str = "vi") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    q = qq_so_lieu(x)
    fig, ax = plt.subplots(figsize=(4.6, 4.4))
    ax.fill_between(q["ly_thuyet"], q["dai_duoi"], q["dai_tren"], color="#1f4e79", alpha=0.12, lw=0)
    ax.plot(q["ly_thuyet"], [q["chan"] + q["doc"] * z for z in q["ly_thuyet"]], color="#a23b2a", lw=1.0)
    ax.scatter(q["ly_thuyet"], q["mau"], s=12, color="#1f4e79", zorder=3)
    BC.dinh_dang_truc(ax, ngon_ngu, "xy")
    ax.set_xlabel("Phân vị lý thuyết (phân phối chuẩn)" if ngon_ngu == "vi" else "Theoretical normal quantiles")
    ax.set_ylabel(ten)
    if q["shapiro_p"] is not None:
        ax.text(0.03, 0.97, f"Shapiro–Wilk: {BC.p_chu(q['shapiro_p'], ngon_ngu)} (n = {q['n']})",
                transform=ax.transAxes, va="top", fontsize=7.6)
    q.update({"loai": "qq", "ghi_chu": "Điểm lý thuyết như qqnorm; đường như qqline; dải 95% từng điểm. Cần bác sĩ "
                                       "kiểm chứng."})
    BC.luu(fig, dich, so_lieu=q)
    return q


def ve_phan_bo(dong, bien: str, dich: Path, cot_nhom: Optional[str] = None, kieu: str = "hist",
               ngon_ngu: str = "vi", don_vi: str = "") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    if kieu not in ("hist", "hop", "violin"):
        raise LoiBieuDo("kieu: hist | hop | violin")
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    x = _cot_so(dong, bien)
    g = _nhom(dong, cot_nhom)
    nhom_ds = thu_tu_nhom(g)
    du = {k: [v for v, gg in zip(x, g) if gg == k and v is not None] for k in nhom_ds}
    tk = {}
    for k, v in du.items():
        if len(v) < 2:
            raise LoiBieuDo(f"nhóm «{k}» có < 2 giá trị")
        q1, md, q3 = np.percentile(v, [25, 50, 75])
        tk[k] = {**ktc_trung_binh(v), "trung_vi": float(md), "q1": float(q1), "q3": float(q3), "min": min(v),
                 "max": max(v)}
    ten_truc = bien + (f" ({don_vi})" if don_vi else "")
    if kieu == "hist":
        fig, ax = plt.subplots(figsize=(5.4, 3.9))
        tat = [v for vv in du.values() for v in vv]
        bins = np.histogram_bin_edges(tat, bins="fd" if len(tat) > 30 else "sturges")
        for i, (k, v) in enumerate(du.items()):
            ax.hist(v, bins=bins, color=MAU[i % len(MAU)], alpha=0.45 if len(du) > 1 else 0.75, edgecolor="white",
                    lw=0.4, label=f"{k or ('Toàn mẫu' if vi else 'All')} (n = {len(v)})")
            xx = np.linspace(bins[0], bins[-1], 200)
            ax.plot(xx, stats.norm.pdf(xx, tk[k]["trung_binh"], tk[k]["dlc"]) * len(v) * (bins[1] - bins[0]),
                    color=MAU[i % len(MAU)], lw=1.2)
        ax.set_xlabel(ten_truc)
        ax.set_ylabel("Số đối tượng" if vi else "Count")
        ax.legend(frameon=False, fontsize=8)
        BC.dinh_dang_truc(ax, ngon_ngu, "x")
    else:
        fig, ax = plt.subplots(figsize=(max(3.6, 1.2 * len(du) + 1.6), 4.2))
        v_ds = list(du.values())
        if kieu == "violin":
            vp = ax.violinplot(v_ds, positions=range(1, len(v_ds) + 1), showmedians=False, showextrema=False)
            for i, b in enumerate(vp["bodies"]):
                b.set_facecolor(MAU[i % len(MAU)])
                b.set_alpha(0.35)
        ax.boxplot(v_ds, positions=range(1, len(v_ds) + 1), widths=0.18 if kieu == "violin" else 0.45,
                   showfliers=True, flierprops={"marker": "o", "ms": 3, "mfc": "none", "mec": "#555555"},
                   medianprops={"color": "#222222", "lw": 1.3})
        ax.set_xticks(range(1, len(v_ds) + 1))
        ax.set_xticklabels([f"{k or ('Toàn mẫu' if vi else 'All')}\n(n = {len(du[k])})" for k in du])
        ax.set_ylabel(ten_truc)
        BC.dinh_dang_truc(ax, ngon_ngu, "y")
    kq = {"loai": "phan_bo", "kieu": kieu, "bien": bien, "thong_ke": tk, "thieu": sum(1 for v in x if v is None),
          "ghi_chu": "Hộp: trung vị, tứ phân vị, râu 1,5·KTPV; histogram kèm mật độ chuẩn cùng TB/ĐLC. Cần bác sĩ "
                     "kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5. TƯƠNG QUAN · DỮ LIỆU THIẾU · THEO THỜI GIAN
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ma_tran_tuong_quan(dong, cot: Sequence[str], phuong_phap: str = "pearson") -> Dict[str, Any]:
    """Hệ số và p từng cặp, loại thiếu theo CẶP (như cor.test từng cặp)."""
    from scipy import stats  # noqa: PLC0415

    if phuong_phap not in ("pearson", "spearman"):
        raise LoiBieuDo("phuong_phap: pearson | spearman")
    du = {c: _cot_so(dong, c) for c in cot}
    r, p, n = {}, {}, {}
    for a in cot:
        for b in cot:
            cap = [(x, y) for x, y in zip(du[a], du[b]) if x is not None and y is not None]
            if len(cap) < 3:
                raise LoiBieuDo(f"cặp {a}–{b} có < 3 quan sát đủ")
            xs, ys = [c[0] for c in cap], [c[1] for c in cap]
            kq = stats.pearsonr(xs, ys) if phuong_phap == "pearson" else stats.spearmanr(xs, ys)
            r[(a, b)], p[(a, b)], n[(a, b)] = (1.0, 0.0, len(cap)) if a == b else (float(kq[0]), float(kq[1]), len(cap))
    return {"cot": list(cot), "r": r, "p": p, "n": n, "phuong_phap": phuong_phap}


def ve_tuong_quan(dong, cot: Sequence[str], dich: Path, phuong_phap: str = "pearson",
                  ngon_ngu: str = "vi") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    m = ma_tran_tuong_quan(dong, cot, phuong_phap)
    k = len(cot)
    M = np.full((k, k), np.nan)
    for i, a in enumerate(cot):
        for j, b in enumerate(cot):
            if i >= j:
                M[i, j] = m["r"][(a, b)]
    fig, ax = plt.subplots(figsize=(0.7 * k + 2.2, 0.6 * k + 1.6))
    im = ax.imshow(M, cmap="RdBu_r", vmin=-1, vmax=1)
    for i, a in enumerate(cot):
        for j, b in enumerate(cot):
            if i > j:
                pv = m["p"][(a, b)]
                sao = "***" if pv < 0.001 else "**" if pv < 0.01 else "*" if pv < 0.05 else ""
                ax.text(j, i, so(m["r"][(a, b)], 2, ngon_ngu) + sao, ha="center", va="center", fontsize=7.2,
                        color="white" if abs(m["r"][(a, b)]) > 0.6 else "#222222")
    ax.set_xticks(range(k))
    ax.set_yticks(range(k))
    ax.set_xticklabels(cot, rotation=45, ha="right")
    ax.set_yticklabels(cot)
    for s in ax.spines.values():
        s.set_visible(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    BC.dinh_dang_truc(cb.ax, ngon_ngu, "y", nd=1)
    ten = "Pearson" if phuong_phap == "pearson" else "Spearman"
    cb.set_label(f"Hệ số tương quan {ten}" if ngon_ngu == "vi" else f"{ten} correlation")
    ax.set_title("* p < 0,05; ** p < 0,01; *** p < 0,001" if ngon_ngu == "vi" else
                 "* p < 0.05; ** p < 0.01; *** p < 0.001", fontsize=7.5, loc="left")
    kq = {"loai": "tuong_quan", "phuong_phap": phuong_phap, "cot": cot,
          "r": {f"{a}|{b}": v for (a, b), v in m["r"].items()}, "p": {f"{a}|{b}": v for (a, b), v in m["p"].items()},
          "n": {f"{a}|{b}": v for (a, b), v in m["n"].items()},
          "ghi_chu": "Loại thiếu theo cặp; p chưa hiệu chỉnh so sánh bội. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_thieu(dong, dich: Path, cot: Optional[Sequence[str]] = None, ngon_ngu: str = "vi",
             so_to_hop: int = 12) -> Dict[str, Any]:
    from collections import Counter  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    cot = list(cot) if cot else list(dong[0])
    N = len(dong)
    pt = {c: 100 * sum(1 for r in dong if r[c] in THIEU) / N for c in cot}
    mau = Counter(tuple(r[c] in THIEU for c in cot) for r in dong)
    to_hop = mau.most_common(so_to_hop)
    fig = plt.figure(figsize=(max(6.0, 0.42 * len(cot) + 3.2), 2.6 + 0.24 * len(to_hop)))
    gs = fig.add_gridspec(2, 2, width_ratios=[0.42 * len(cot) + 0.6, 1.6],
                          height_ratios=[1.2, 0.24 * len(to_hop) + 0.4], hspace=0.08, wspace=0.05)
    axb, axm, axn = fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[1, 0]), fig.add_subplot(gs[1, 1])
    axb.bar(range(len(cot)), [pt[c] for c in cot], color="#a23b2a", width=0.6)
    axb.set_xlim(-0.5, len(cot) - 0.5)
    axb.set_xticks([])
    axb.set_ylabel("% thiếu" if ngon_ngu == "vi" else "% missing")
    BC.dinh_dang_truc(axb, ngon_ngu, "y")
    for i, c in enumerate(cot):
        if pt[c] > 0:
            axb.text(i, pt[c], so(pt[c], 1, ngon_ngu), ha="center", va="bottom", fontsize=6.5)
    for y, (kieu, dem) in enumerate(to_hop):
        for x, th in enumerate(kieu):
            axm.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle(
                (x - 0.45, y - 0.4), 0.9, 0.8, color="#a23b2a" if th else "#d9e2ec", lw=0))
        axn.barh(y, 100 * dem / N, color="#1f4e79", height=0.6)
        axn.text(100 * dem / N, y, f" {dem}", va="center", fontsize=6.8)
    axm.set_xlim(-0.5, len(cot) - 0.5)
    axm.set_ylim(len(to_hop) - 0.5, -0.5)
    axm.set_xticks(range(len(cot)))
    axm.set_xticklabels(cot, rotation=60, ha="right", fontsize=7.5)
    axm.set_yticks([])
    for s in axm.spines.values():
        s.set_visible(False)
    axn.set_ylim(len(to_hop) - 0.5, -0.5)
    axn.set_yticks([])
    axn.set_xlabel("% đối tượng" if ngon_ngu == "vi" else "% of records")
    BC.dinh_dang_truc(axn, ngon_ngu, "x")
    kq = {"loai": "thieu", "N": N, "pt_thieu": pt, "du_lieu_day_du": mau.get(tuple([False] * len(cot)), 0),
          "to_hop": [{"thieu": [c for c, th in zip(cot, kieu) if th], "so": dem} for kieu, dem in to_hop],
          "ghi_chu": "Đỏ = thiếu. Kiểu thiếu gợi ý cơ chế (MCAR/MAR/MNAR) nhưng không chứng minh được. Cần bác sĩ kiểm "
                     "chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_theo_thoi_gian(dong, cot_tg: str, bien: str, dich: Path, cot_nhom: Optional[str] = None,
                      ngon_ngu: str = "vi", don_vi: str = "") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    g = _nhom(dong, cot_nhom)
    nhom_ds = thu_tu_nhom(g)
    moc = sorted({so_hoc(r[cot_tg], cot_tg) for r in dong if r[cot_tg] not in THIEU})
    fig, ax = plt.subplots(figsize=(5.8, 4.0))
    kq: Dict[str, Any] = {"loai": "theo_thoi_gian", "moc": moc, "nhom": {}}
    lech = (max(moc) - min(moc)) * 0.008 if len(moc) > 1 else 0.02
    for i, k in enumerate(nhom_ds):
        hang = []
        for m in moc:
            v = [so_hoc(r[bien], bien) for r, gg in zip(dong, g) if gg == k and r[cot_tg] not in THIEU and
                 so_hoc(r[cot_tg], cot_tg) == m and r[bien] not in THIEU]
            if len(v) >= 2:
                hang.append({"moc": m, **ktc_trung_binh(v)})
        kq["nhom"][k] = hang
        xs = [h["moc"] + (i - (len(nhom_ds) - 1) / 2) * lech for h in hang]
        ys = [h["trung_binh"] for h in hang]
        ax.errorbar(xs, ys, yerr=[[h["trung_binh"] - h["duoi"] for h in hang], [h["tren"] - h["trung_binh"]
                                                                                  for h in hang]],
                    color=MAU[i % len(MAU)], marker="o", ms=4, capsize=3, lw=1.3,
                    label=k or ("Toàn mẫu" if ngon_ngu == "vi" else "All"))
    ax.set_xticks(moc)
    BC.dinh_dang_truc(ax, ngon_ngu, "xy")
    ax.set_xlabel(cot_tg)
    ax.set_ylabel(f"{bien}" + (f" ({don_vi})" if don_vi else "") + (" — trung bình (KTC 95%)" if ngon_ngu == "vi"
                                                                     else " — mean (95% CI)"))
    if len(nhom_ds) > 1:
        ax.legend(frameon=False, fontsize=8)
    kq["ghi_chu"] = ("Trung bình mỗi thời điểm trên đối tượng có đo (không thay thế mô hình hỗn hợp cho dữ liệu lặp). "
                     "Cần bác sĩ kiểm chứng.")
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6. KIỂM CHÉO R
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def kiem_cheo_r_cot(kq: Dict[str, Any], ktc: str) -> Dict[str, Any]:
    py, ma = {}, []
    for i, (k, v) in enumerate(kq["nhom"].items()):
        if kq["trung_binh"]:
            continue
        py[f"lo{i}"], py[f"hi{i}"] = v["duoi"], v["tren"]
        f = (f"binom.test({v['k']}, {v['n']})$conf.int" if ktc == "clopper-pearson" else
             f"prop.test({v['k']}, {v['n']}, correct=FALSE)$conf.int")
        ma.append(f"ci <- {f}; cat('KQ lo{i}', ci[1], '\\n'); cat('KQ hi{i}', ci[2], '\\n')")
    if not ma:
        return {"trang_thai": "khong_kiem_cheo_duoc", "ly_do": "cột trung bình — dùng t.test ở test", "chi_tiet": []}
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo("\n".join(ma) + "\n"), dung_sai=1e-7)


def kiem_cheo_r_tuong_quan(dong, cot: Sequence[str], phuong_phap: str) -> Dict[str, Any]:
    m = ma_tran_tuong_quan(dong, cot, phuong_phap)
    py, ma = {}, []
    for i, a in enumerate(cot):
        ma.append(f"v{i} <- {BC.r_vec([float('nan') if x is None else x for x in _cot_so(dong, a)])}")
    for i, a in enumerate(cot):
        for j, b in enumerate(cot):
            if i < j:
                py[f"r{i}_{j}"] = m["r"][(a, b)]
                ma.append(f"cat('KQ r{i}_{j}', cor(v{i}, v{j}, method='{phuong_phap}', use='pairwise.complete.obs'), "
                          f"'\\n')")
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo("\n".join(ma).replace("nan", "NaN") + "\n"), dung_sai=1e-9)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 7. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _cap(s: Optional[str]) -> List[Tuple[str, str]]:
    ra = []
    for phan in (s or "").split(","):
        phan = phan.strip()
        if not phan:
            continue
        k, _, v = phan.partition("=")
        ra.append((k.strip(), (v or k).strip()))
    return ra


def main(argv: Optional[Sequence[str]] = None) -> int:
    from bieu_do_gop import _in_kiem_cheo  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("cot-ktc", "likert", "phan-bo", "qq", "tuong-quan", "thieu", "theo-thoi-gian"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--bien")
    ap.add_argument("--muc")
    ap.add_argument("--nhom")
    ap.add_argument("--trung-binh", action="store_true")
    ap.add_argument("--ktc", default="clopper-pearson", choices=("clopper-pearson", "wilson"))
    ap.add_argument("--cot")
    ap.add_argument("--nhan-cot")
    ap.add_argument("--giu-thu-tu", action="store_true")
    ap.add_argument("--kieu", default="hist", choices=("hist", "hop", "violin"))
    ap.add_argument("--phuong-phap", default="pearson", choices=("pearson", "spearman"))
    ap.add_argument("--thoi-diem")
    ap.add_argument("--don-vi", default="")
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    ap.add_argument("--kiem-cheo-r", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    cot = [c.strip() for c in (a.cot or "").split(",") if c.strip()]
    can = {"cot-ktc": [a.bien], "likert": cot, "phan-bo": [a.bien], "qq": [a.bien], "tuong-quan": cot,
           "thieu": cot, "theo-thoi-gian": [a.bien, a.thoi_diem]}[a.lenh]
    if a.lenh in ("cot-ktc", "phan-bo", "qq", "theo-thoi-gian") and not all(can):
        print("❌ thiếu --bien (và --thoi-diem cho theo-thoi-gian)")
        return 3
    if a.lenh in ("likert", "tuong-quan") and len(cot) < (1 if a.lenh == "likert" else 2):
        print("❌ thiếu --cot")
        return 3
    try:
        dong = doc_csv(a.du_lieu, [c for c in can if c] + ([a.nhom] if a.nhom else []))
        ma_kc = 0
        if a.lenh == "cot-ktc":
            kq = ve_cot_ktc(dong, a.bien, a.ra, a.muc, a.nhom, a.trung_binh, a.ktc, a.ngon_ngu, a.don_vi)
            for k, v in kq["nhom"].items():
                print(f"✅ {k or 'toàn mẫu'}: " + (f"TB = {so(v['trung_binh'], 2)} [{so(v['duoi'], 2)}; "
                                                 f"{so(v['tren'], 2)}]" if a.trung_binh else
                                                 f"{v['k']}/{v['n']} = {so(100 * v['ty_le'], 1)}% "
                                                 f"[{so(100 * v['duoi'], 1)}; {so(100 * v['tren'], 1)}]"))
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("KTC tỷ lệ (R)", kiem_cheo_r_cot(kq, a.ktc))
        elif a.lenh == "likert":
            muc = _cap(a.muc)
            if not muc:
                print("❌ likert cần --muc \"1=…,2=…\"")
                return 3
            kq = ve_likert(dong, cot, muc, a.ra, dict(_cap(a.nhan_cot)), a.giu_thu_tu, a.ngon_ngu)
            for c in kq["thu_tu_ve"][::-1]:
                print(f"✅ {c}: thuận lợi {so(kq['cau_hoi'][c]['thuan_loi'], 1)}% (n = {kq['cau_hoi'][c]['n']})")
        elif a.lenh == "phan-bo":
            ve_phan_bo(dong, a.bien, a.ra, a.nhom, a.kieu, a.ngon_ngu, a.don_vi)
            print(f"✅ phân bố {a.bien} ({a.kieu})")
        elif a.lenh == "qq":
            x = [v for v in _cot_so(dong, a.bien) if v is not None]
            q = ve_qq(x, a.bien, a.ra, a.ngon_ngu)
            print(f"✅ Q-Q {a.bien}: n = {q['n']}, Shapiro–Wilk {BC.p_chu(q['shapiro_p'])}")
        elif a.lenh == "tuong-quan":
            ve_tuong_quan(dong, cot, a.ra, a.phuong_phap, a.ngon_ngu)
            print(f"✅ tương quan {a.phuong_phap}: {len(cot)} biến")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("tương quan (R cor)", kiem_cheo_r_tuong_quan(dong, cot, a.phuong_phap))
        elif a.lenh == "thieu":
            kq = ve_thieu(dong, a.ra, cot or None, a.ngon_ngu)
            print(f"✅ dữ liệu thiếu: {kq['du_lieu_day_du']}/{kq['N']} dòng đủ")
        else:
            ve_theo_thoi_gian(dong, a.thoi_diem, a.bien, a.ra, a.nhom, a.ngon_ngu, a.don_vi)
            print(f"✅ {a.bien} theo {a.thoi_diem}")
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return ma_kc


if __name__ == "__main__":
    sys.exit(main())
