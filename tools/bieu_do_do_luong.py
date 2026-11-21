#!/usr/bin/env python3
"""Biểu đồ KIỂM ĐỊNH CÔNG CỤ ĐO LƯỜNG (COSMIN) — scree + phân tích song song, hệ số tải, sơ đồ CFA, Bland–Altman
(chặng 5a chương trình biểu đồ, bác sĩ 21/11/2026: «phải thực hiện được tất cả biểu đồ một cách chi tiết và chính xác
nhất»).

Họ biểu đồ (PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  scree        trị riêng của ma trận tương quan (Pearson) + đường phân tích song song Horn (phân vị 95 của trị riêng
               dữ liệu ngẫu nhiên chuẩn cùng n × p, hạt giống cố định ⇒ tái lập) và đường Kaiser = 1; gợi ý số nhân tố
               = số trị riêng thực vượt đường song song. Chỉ là GỢI Ý — quyết định số nhân tố cần lý thuyết.
  he-so-tai    bản đồ nhiệt hệ số tải (câu hỏi × nhân tố) từ BẢNG kết quả EFA/CFA (lavaan, psych, SPSS…), ghi số,
               tô đậm |λ| ≥ ngưỡng (mặc định 0,40), cột h² nếu có.
  so-do-cfa    sơ đồ đường dẫn CFA: nhân tố (elip) → câu hỏi (chữ nhật) với hệ số tải chuẩn hoá trên mũi tên, tương
               quan giữa các nhân tố (cung hai đầu), phương sai sai số; chỉ số phù hợp (CFI, TLI, RMSEA, SRMR) nếu khai.
  bland-altman hiệu số theo trung bình hai phép đo: độ chệch (bias) + KTC 95%, giới hạn đồng thuận ±1,96 ĐLC + KTC
               95% của từng giới hạn (Bland & Altman 1999: SE ≈ √(3s²/n)), kiểm định chệch tỷ lệ (hồi quy hiệu số
               theo trung bình).

Độ chính xác: test giữ giá trị chuẩn của R (eigen(cor()), mean/sd/t.test) trên datasets::attitude. Hệ số tải KHÔNG được
ước lượng ở đây — vẽ đúng số trong bảng kết quả của phần mềm thống kê. Cần bác sĩ kiểm chứng.

Lệnh:
  python3 tools/bieu_do_do_luong.py scree --du-lieu d.csv --cot q1,q2,… [--lap 500] [--hat-giong 2026] --ra …
  python3 tools/bieu_do_do_luong.py he-so-tai --du-lieu tai.csv [--nguong 0.4] --ra …
      (tai.csv: cột cau_hoi, nhan_to_1, nhan_to_2, … [, h2])
  python3 tools/bieu_do_do_luong.py so-do-cfa --du-lieu cfa.csv [--tuong-quan tq.csv] [--chi-so "CFI=0.95,RMSEA=0.06"]
      --ra …   (cfa.csv: cột nhan_to, cau_hoi, he_so_tai [, sai_so]; tq.csv: nhan_to_a, nhan_to_b, r)
  python3 tools/bieu_do_do_luong.py bland-altman --du-lieu d.csv --do-1 lan1 --do-2 lan2 [--don-vi …] --ra …
Mã thoát: 0 xong · 2 dữ liệu sai/thiếu · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import bieu_do_chung as BC  # noqa: E402
from bieu_do_chung import LoiBieuDo, so  # noqa: E402
from bieu_do_mo_ta import THIEU, doc_csv, so_hoc  # noqa: E402

MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. SCREE + PHÂN TÍCH SONG SONG HORN
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def tri_rieng(X) -> List[float]:
    """Trị riêng (giảm dần) của ma trận tương quan Pearson."""
    import numpy as np  # noqa: PLC0415

    return sorted(np.linalg.eigvalsh(np.corrcoef(np.asarray(X, float), rowvar=False)).tolist(), reverse=True)


def song_song_horn(n: int, p: int, lap: int = 500, hat_giong: int = 2026, phan_vi: float = 95) -> List[float]:
    """Phân vị `phan_vi` của trị riêng từ `lap` bộ dữ liệu chuẩn ngẫu nhiên n × p (hạt giống cố định ⇒ tái lập)."""
    import numpy as np  # noqa: PLC0415

    rng = np.random.default_rng(hat_giong)
    ev = np.empty((lap, p))
    for i in range(lap):
        ev[i] = np.sort(np.linalg.eigvalsh(np.corrcoef(rng.standard_normal((n, p)), rowvar=False)))[::-1]
    return np.percentile(ev, phan_vi, axis=0).tolist()


def ve_scree(X, ten_cot: Sequence[str], dich: Path, lap: int = 500, hat_giong: int = 2026,
             ngon_ngu: str = "vi") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    X = np.asarray(X, float)
    n, p = X.shape
    if p < 3 or n <= p:
        raise LoiBieuDo(f"cần ≥ 3 câu hỏi và số đối tượng > số câu hỏi (đang n = {n}, p = {p})")
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    ev = tri_rieng(X)
    pa = song_song_horn(n, p, lap, hat_giong)
    so_nt = 0
    for a, b in zip(ev, pa):
        if a > b:
            so_nt += 1
        else:
            break
    kaiser = sum(1 for a in ev if a > 1)
    fig, ax = plt.subplots(figsize=(5.4, 4.0))
    k = list(range(1, p + 1))
    ax.plot(k, ev, marker="o", color="#1f4e79", lw=1.4, label="Trị riêng thực" if vi else "Observed eigenvalues")
    ax.plot(k, pa, marker="^", ms=4, color="#a23b2a", lw=1.0, ls="--",
            label=(f"Phân tích song song (P95, {lap} lần)" if vi else f"Parallel analysis (P95, {lap} sets)"))
    ax.axhline(1, color="#888888", lw=0.7, ls=":", label="Kaiser = 1")
    ax.set_xticks(k)
    ax.set_xlabel("Thứ tự nhân tố" if vi else "Factor number")
    ax.set_ylabel("Trị riêng" if vi else "Eigenvalue")
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    ax.legend(frameon=False, fontsize=8)
    ax.text(0.98, 0.55, (f"Gợi ý số nhân tố — song song: {so_nt}; Kaiser: {kaiser}" if vi else
                         f"Suggested factors — parallel: {so_nt}; Kaiser: {kaiser}"), transform=ax.transAxes,
            ha="right", fontsize=7.8)
    kq = {"loai": "scree", "n": n, "p": p, "cau_hoi": list(ten_cot), "tri_rieng": ev, "song_song_p95": pa,
          "so_nhan_to_song_song": so_nt, "so_nhan_to_kaiser": kaiser, "lap": lap, "hat_giong": hat_giong,
          "ty_le_phuong_sai": [e / p for e in ev],
          "ghi_chu": "Phân tích song song Horn (dữ liệu chuẩn ngẫu nhiên, P95). Số nhân tố cuối cùng do lý thuyết và "
                     "nhóm nghiên cứu quyết định. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. HỆ SỐ TẢI · SƠ ĐỒ CFA
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def ve_he_so_tai(dong, dich: Path, nguong: float = 0.40, ngon_ngu: str = "vi") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    if "cau_hoi" not in dong[0]:
        raise LoiBieuDo("bảng hệ số tải cần cột cau_hoi")
    nt = [c for c in dong[0] if c not in ("cau_hoi", "h2")]
    if not nt:
        raise LoiBieuDo("bảng hệ số tải không có cột nhân tố")
    M = np.array([[so_hoc(r[c], c) if r[c] not in THIEU else np.nan for c in nt] for r in dong])
    if np.nanmax(np.abs(M)) > 1.0 + 1e-9:
        raise LoiBieuDo("hệ số tải chuẩn hoá phải trong [−1; 1]")
    co_h2 = "h2" in dong[0]
    plt = BC.plt_chuan()
    fig, ax = plt.subplots(figsize=(1.0 * len(nt) + 2.6 + (0.9 if co_h2 else 0), 0.36 * len(dong) + 1.2))
    ax.imshow(np.abs(np.nan_to_num(M)), cmap="Blues", vmin=0, vmax=1, aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            if not np.isnan(M[i, j]):
                manh = abs(M[i, j]) >= nguong
                ax.text(j, i, so(M[i, j], 2, ngon_ngu), ha="center", va="center", fontsize=8,
                        weight="bold" if manh else None, color="white" if abs(M[i, j]) > 0.65 else "#222222")
    ax.set_xticks(range(len(nt)))
    ax.set_xticklabels(nt)
    ax.set_yticks(range(len(dong)))
    ax.set_yticklabels([r["cau_hoi"] for r in dong])
    ax.xaxis.tick_top()
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if co_h2:
        for i, r in enumerate(dong):
            ax.text(len(nt) - 0.35, i, f"  h² = {so(so_hoc(r['h2'], 'h2'), 2, ngon_ngu)}", va="center", fontsize=7.6)
    ax.set_xlim(-0.5, len(nt) - 0.5 + (0.9 if co_h2 else 0))
    chu = (f"In đậm: |λ| ≥ {so(nguong, 2, ngon_ngu)}" if ngon_ngu == "vi" else f"Bold: |λ| ≥ {so(nguong, 2, ngon_ngu)}")
    ax.set_xlabel(chu, fontsize=7.8)
    chinh = {r["cau_hoi"]: nt[int(np.nanargmax(np.abs(M[i])))] for i, r in enumerate(dong)}
    cheo = [r["cau_hoi"] for i, r in enumerate(dong) if np.sum(np.abs(np.nan_to_num(M[i])) >= nguong) > 1]
    yeu = [r["cau_hoi"] for i, r in enumerate(dong) if np.nanmax(np.abs(M[i])) < nguong]
    kq = {"loai": "he_so_tai", "nhan_to": nt, "nguong": nguong, "nhan_to_chinh": chinh, "tai_cheo": cheo,
          "tai_yeu": yeu, "ghi_chu": "Vẽ đúng hệ số tải trong bảng kết quả (không ước lượng lại). Câu tải chéo/tải yếu "
                                     "chỉ là gợi ý xem xét. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_so_do_cfa(dong, dich: Path, tuong_quan: Optional[Sequence[Dict[str, str]]] = None,
                 chi_so: Optional[Dict[str, float]] = None, ngon_ngu: str = "vi") -> Dict[str, Any]:
    import matplotlib.patches as mp  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    for c in ("nhan_to", "cau_hoi", "he_so_tai"):
        if c not in dong[0]:
            raise LoiBieuDo(f"bảng CFA thiếu cột «{c}»")
    nt = list(dict.fromkeys(r["nhan_to"] for r in dong))
    plt = BC.plt_chuan()
    n_cau = len(dong)
    cao = max(3.0, 0.42 * n_cau + 0.8)
    fig, ax = plt.subplots(figsize=(7.2, cao))
    ax.set_xlim(0, 10)
    ax.set_ylim(-0.5, n_cau + 0.5)
    ax.axis("off")
    y_cau, i = {}, 0
    tam_nt = {}
    for k in nt:
        cac = [r for r in dong if r["nhan_to"] == k]
        ys = []
        for r in cac:
            y = n_cau - 0.5 - i
            i += 1
            ys.append(y)
            y_cau[r["cau_hoi"]] = y
            ax.add_patch(mp.FancyBboxPatch((6.2, y - 0.18), 1.6, 0.36, boxstyle="square,pad=0.02", fc="white",
                                           ec="#222222", lw=0.8))
            ax.text(7.0, y, r["cau_hoi"], ha="center", va="center", fontsize=8)
            if r.get("sai_so") not in (None, "", "NA"):
                ax.annotate("", xy=(7.8, y), xytext=(8.6, y), arrowprops={"arrowstyle": "-|>", "lw": 0.6,
                                                                          "color": "#333333"})
                ax.text(8.65, y, so(so_hoc(r["sai_so"], "sai_so"), 2, ngon_ngu), va="center", fontsize=7.2,
                        color="#555555")
        yc = sum(ys) / len(ys)
        tam_nt[k] = yc
        ax.add_patch(mp.Ellipse((2.2, yc), 2.2, 0.75, fc="#eef3f9", ec="#1f4e79", lw=1.0))
        ax.text(2.2, yc, k, ha="center", va="center", fontsize=8.5, weight="bold")
        for r in cac:
            lam = so_hoc(r["he_so_tai"], "he_so_tai")
            if abs(lam) > 1 + 1e-9:
                raise LoiBieuDo(f"{r['cau_hoi']}: hệ số tải chuẩn hoá phải trong [−1; 1]")
            y = y_cau[r["cau_hoi"]]
            ax.annotate("", xy=(6.2, y), xytext=(3.3, yc), arrowprops={"arrowstyle": "-|>", "lw": 0.7,
                                                                        "color": "#333333"})
            xm, ym = 3.3 + (6.2 - 3.3) * 0.62, yc + (y - yc) * 0.62
            ax.text(xm, ym, so(lam, 2, ngon_ngu), fontsize=7.4, ha="center", va="center",
                    bbox={"fc": "white", "ec": "none", "pad": 0.4}, color="#a23b2a" if abs(lam) < 0.4 else "#222222")
    tq_ra = []
    w_max = 0.0
    for r in tuong_quan or []:
        a, b = r["nhan_to_a"], r["nhan_to_b"]
        if a not in tam_nt or b not in tam_nt:
            raise LoiBieuDo(f"tương quan giữa nhân tố lạ: {a}–{b}")
        rv = so_hoc(r["r"], "r")
        ya, yb = tam_nt[a], tam_nt[b]
        # cung lồng nhau phình sang trái: cặp càng xa cung càng rộng ⇒ không cắt nhau, nhãn ở đỉnh cung
        import numpy as np  # noqa: PLC0415

        w = 0.25 + 0.16 * abs(ya - yb)
        w_max = max(w_max, w)
        tt = np.linspace(0, 1, 60)
        cx, cy = 1.1 - w * np.sin(np.pi * tt), ya + (yb - ya) * tt
        ax.plot(cx, cy, color="#333333", lw=0.7)
        for x0, y0, x1, y1 in ((cx[2], cy[2], cx[0], cy[0]), (cx[-3], cy[-3], cx[-1], cy[-1])):
            ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "-|>", "lw": 0.7,
                                                                      "color": "#333333"})
        ax.text(1.1 - w - 0.05, (ya + yb) / 2, so(rv, 2, ngon_ngu), fontsize=7.6, ha="right", va="center",
                bbox={"fc": "white", "ec": "none", "pad": 0.3})
        tq_ra.append({"a": a, "b": b, "r": rv})
    ax.set_xlim(min(0.0, 1.1 - w_max - 0.75), 10)  # chừa chỗ cho cung tương quan rộng nhất + nhãn
    if chi_so:
        ax.text(0.0, -0.35, "; ".join(f"{k} = {so(v, 3, ngon_ngu)}" for k, v in chi_so.items()), fontsize=7.8)
    kq = {"loai": "so_do_cfa", "nhan_to": nt, "cau_hoi": {r["cau_hoi"]: {"nhan_to": r["nhan_to"],
                                                                        "he_so_tai": so_hoc(r["he_so_tai"], "λ")}
                                                         for r in dong},
          "tuong_quan": tq_ra, "chi_so_phu_hop": chi_so or {},
          "ghi_chu": "Hệ số tải chuẩn hoá lấy từ kết quả CFA (vd lavaan standardizedSolution); tô đỏ khi |λ| < 0,40. "
                     "Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. BLAND–ALTMAN
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def bland_altman(a: Sequence[float], b: Sequence[float]) -> Dict[str, Any]:
    """Hiệu số d = a − b; bias = TB(d); LoA = bias ± 1,96·ĐLC(d); KTC 95% của bias (t) và của mỗi LoA (SE ≈ √(3s²/n),
    Bland & Altman 1999); chệch tỷ lệ: hồi quy d theo (a + b)/2."""
    from scipy import stats  # noqa: PLC0415

    n = len(a)
    if n != len(b) or n < 3:
        raise LoiBieuDo("hai phép đo phải cùng độ dài và ≥ 3 cặp")
    d = [x - y for x, y in zip(a, b)]
    m = [(x + y) / 2 for x, y in zip(a, b)]
    bias = sum(d) / n
    s = math.sqrt(sum((v - bias) ** 2 for v in d) / (n - 1))
    t = float(stats.t.ppf(0.975, n - 1))
    se_loa = math.sqrt(3 * s * s / n)
    lo, hi = bias - 1.96 * s, bias + 1.96 * s
    hq = stats.linregress(m, d)
    return {"n": n, "bias": bias, "dlc": s, "bias_ktc": (bias - t * s / math.sqrt(n), bias + t * s / math.sqrt(n)),
            "loa": (lo, hi), "loa_duoi_ktc": (lo - t * se_loa, lo + t * se_loa),
            "loa_tren_ktc": (hi - t * se_loa, hi + t * se_loa), "trung_binh": m, "hieu_so": d,
            "chech_ty_le": {"do_doc": float(hq.slope), "p": float(hq.pvalue)},
            "ngoai_loa": sum(1 for v in d if v < lo or v > hi)}


def ve_bland_altman(a, b, dich: Path, ten_1: str = "Phép đo 1", ten_2: str = "Phép đo 2", don_vi: str = "",
                    ngon_ngu: str = "vi") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    ba = bland_altman(a, b)
    fig, ax = plt.subplots(figsize=(5.8, 4.2))
    ax.scatter(ba["trung_binh"], ba["hieu_so"], s=16, color="#1f4e79", alpha=0.75, zorder=3)
    x0, x1 = min(ba["trung_binh"]), max(ba["trung_binh"])
    for y, (k_lo, k_hi), ten, net in ((ba["bias"], ba["bias_ktc"], "Độ chệch" if vi else "Bias", "-"),
                                (ba["loa"][0], ba["loa_duoi_ktc"], "−1,96 ĐLC" if vi else "−1.96 SD", "--"),
                                (ba["loa"][1], ba["loa_tren_ktc"], "+1,96 ĐLC" if vi else "+1.96 SD", "--")):
        ax.axhline(y, color="#a23b2a" if net == "--" else "#222222", lw=1.0, ls=net)
        ax.axhspan(k_lo, k_hi, color="#a23b2a" if net == "--" else "#555555", alpha=0.10, lw=0)
        ax.text(x1, y, f" {ten}: {so(y, 2, ngon_ngu)}", va="bottom", ha="right", fontsize=7.6)
    ax.axhline(0, color="#999999", lw=0.6, ls=":")
    ax.set_xlim(x0 - 0.04 * (x1 - x0), x1 + 0.04 * (x1 - x0))
    dv = f" ({don_vi})" if don_vi else ""
    ax.set_xlabel((f"Trung bình {ten_1} và {ten_2}" if vi else f"Mean of {ten_1} and {ten_2}") + dv)
    ax.set_ylabel(f"{ten_1} − {ten_2}" + dv)
    BC.dinh_dang_truc(ax, ngon_ngu, "xy")
    ax.text(0.02, 0.02, (f"Chệch tỷ lệ: độ dốc = {so(ba['chech_ty_le']['do_doc'], 3, ngon_ngu)}, "
                         f"{BC.p_chu(ba['chech_ty_le']['p'], ngon_ngu)}; ngoài giới hạn: {ba['ngoai_loa']}/{ba['n']}")
            if vi else (f"Proportional bias: slope = {so(ba['chech_ty_le']['do_doc'], 3, ngon_ngu)}, "
                        f"{BC.p_chu(ba['chech_ty_le']['p'], ngon_ngu)}; outside LoA: {ba['ngoai_loa']}/{ba['n']}"),
            transform=ax.transAxes, fontsize=7.6)
    ba.update({"loai": "bland_altman", "ghi_chu": "Dải mờ: KTC 95% của độ chệch và của từng giới hạn đồng thuận "
                                                  "(Bland & Altman 1999). Ngưỡng chấp nhận lâm sàng do bác sĩ định "
                                                  "trước. Cần bác sĩ kiểm chứng."})
    BC.luu(fig, dich, so_lieu=ba)
    return ba


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def main(argv: Optional[Sequence[str]] = None) -> int:
    import numpy as np  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("scree", "he-so-tai", "so-do-cfa", "bland-altman"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--cot", default="")
    ap.add_argument("--lap", type=int, default=500)
    ap.add_argument("--hat-giong", type=int, default=2026)
    ap.add_argument("--nguong", type=float, default=0.40)
    ap.add_argument("--tuong-quan", type=Path)
    ap.add_argument("--chi-so", default="")
    ap.add_argument("--do-1")
    ap.add_argument("--do-2")
    ap.add_argument("--don-vi", default="")
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        if a.lenh == "scree":
            cot = [c.strip() for c in a.cot.split(",") if c.strip()]
            dong = doc_csv(a.du_lieu, cot)
            cot = cot or list(dong[0])
            giu = [r for r in dong if all(r[c] not in THIEU for c in cot)]
            X = np.array([[so_hoc(r[c], c) for c in cot] for r in giu])
            kq = ve_scree(X, cot, a.ra, a.lap, a.hat_giong, a.ngon_ngu)
            print(f"✅ scree: {kq['p']} câu, n = {kq['n']} (loại {len(dong) - len(giu)} dòng thiếu) · gợi ý song song "
                  f"{kq['so_nhan_to_song_song']}, Kaiser {kq['so_nhan_to_kaiser']}")
        elif a.lenh == "he-so-tai":
            kq = ve_he_so_tai(doc_csv(a.du_lieu), a.ra, a.nguong, a.ngon_ngu)
            print(f"✅ hệ số tải: {len(kq['nhan_to_chinh'])} câu × {len(kq['nhan_to'])} nhân tố · tải chéo "
                  f"{len(kq['tai_cheo'])}, tải yếu {len(kq['tai_yeu'])}")
        elif a.lenh == "so-do-cfa":
            tq = doc_csv(a.tuong_quan) if a.tuong_quan else None
            cs = {k.strip(): float(v) for k, v in (p.split("=") for p in a.chi_so.split(",") if "=" in p)}
            kq = ve_so_do_cfa(doc_csv(a.du_lieu), a.ra, tq, cs, a.ngon_ngu)
            print(f"✅ sơ đồ CFA: {len(kq['nhan_to'])} nhân tố, {len(kq['cau_hoi'])} câu")
        else:
            if not (a.do_1 and a.do_2):
                print("❌ bland-altman cần --do-1 và --do-2")
                return 3
            dong = doc_csv(a.du_lieu, [a.do_1, a.do_2])
            cap = [(so_hoc(r[a.do_1], a.do_1), so_hoc(r[a.do_2], a.do_2)) for r in dong
                   if r[a.do_1] not in THIEU and r[a.do_2] not in THIEU]
            ba = ve_bland_altman([c[0] for c in cap], [c[1] for c in cap], a.ra, a.do_1, a.do_2, a.don_vi, a.ngon_ngu)
            print(f"✅ Bland–Altman: bias = {so(ba['bias'], 3)}, LoA [{so(ba['loa'][0], 3)}; {so(ba['loa'][1], 3)}]")
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
