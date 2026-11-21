#!/usr/bin/env python3
"""Biểu đồ SỐNG CÒN / thời gian đến biến cố — tính đúng, vẽ đúng chuẩn công bố (chặng 3 chương trình biểu đồ, bác sĩ
21/11/2026: «phải thực hiện được tất cả biểu đồ một cách chi tiết và chính xác nhất»).

Trước bản này: `run_stats_analysis.py` vẽ một đường Kaplan–Meier tối giản (không KTC, không bảng số nguy cơ, không
dấu kiểm duyệt); `khung_bieu_bang` chỉ có khung KM rỗng; không có tần suất tích luỹ khi có biến cố cạnh tranh hay đồ thị
kiểm giả định nguy cơ tỷ lệ.

Họ biểu đồ (PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  km       Kaplan–Meier theo nhóm: bậc thang, dấu «+» kiểm duyệt, dải KTC 95% (log-log mặc định; log/plain tuỳ chọn —
           cùng công thức survival::survfit), trung vị + KTC, kiểm định log-rank (survdiff), HR Cox (Efron) so với nhóm
           tham chiếu, BẢNG SỐ NGUY CƠ dưới trục; `--dao` vẽ tỷ lệ tích luỹ 1 − S(t).
  loglog   log(−log S(t)) theo log t từng nhóm — hai đường song song gợi ý nguy cơ tỷ lệ (kiểm giả định Cox).
  cif      tần suất tích luỹ (Aalen–Johansen) khi có biến cố CẠNH TRANH — không dùng 1 − KM (thổi phồng nguy cơ khi
           biến cố cạnh tranh nhiều); khớp survival::survfit đa trạng thái.

Độ chính xác: test giữ giá trị chuẩn do R survival 3.8 tính trên survival::lung và survival::mgus2; `--kiem-cheo-r`
chạy lại survfit/survdiff/coxph trên chính dữ liệu của đề tài. Không có R ⇒ «không kiểm chéo được».

Ranh giới: chỉ tính/vẽ; chọn mốc thời gian, nhóm tham chiếu, diễn giải là việc của bác sĩ/thống kê viên. Kiểm định
Gray cho CIF chưa có (cần cmprsk) — hình CIF không ghi p. Cần bác sĩ kiểm chứng.

Dữ liệu vào (CSV): cột thời gian (> 0), cột biến cố 0/1 (km, loglog) hoặc mã sự kiện 0 = kiểm duyệt, 1, 2, … (cif),
tuỳ chọn cột nhóm. Mã 1/2 kiểu survival::Surv (1 = kiểm duyệt) bị TỪ CHỐI — mã hoá lại 0/1 cho rõ.

Lệnh:
  python3 tools/bieu_do_song_con.py km --du-lieu d.csv --thoi-gian tg --bien-co bc [--nhom gioi] [--tham-chieu Nam]
      [--ktc log-log|log|plain] [--moc 0,180,365,730] [--don-vi ngày] [--dao] --ra …
  python3 tools/bieu_do_song_con.py loglog --du-lieu d.csv --thoi-gian tg --bien-co bc --nhom gioi --ra …
  python3 tools/bieu_do_song_con.py cif --du-lieu d.csv --thoi-gian tg --su-kien sk [--nhom gioi]
      [--nhan-su-kien "1=Tiến triển,2=Tử vong"] [--moc …] --ra …
  (thêm --ngon-ngu en; --kiem-cheo-r)
Mã thoát: 0 xong · 1 kiểm chéo R LỆCH · 2 dữ liệu sai/thiếu · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import bieu_do_chung as BC  # noqa: E402
from bieu_do_chung import LoiBieuDo, so  # noqa: E402

Z975 = 1.959963984540054
MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")
NET = ("-", "--", "-.", ":", (0, (5, 1, 1, 1)), (0, (3, 1)))


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. ĐỌC DỮ LIỆU
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def doc_du_lieu(p: Path, cot_tg: str, cot_bc: str, cot_nhom: Optional[str] = None,
                ma_su_kien: bool = False) -> Dict[str, Any]:
    """→ {"t", "e" (0/1 hoặc mã 0..K), "g" (nhãn nhóm, "" khi không phân nhóm), "loai"}."""
    import numpy as np  # noqa: PLC0415

    try:
        with open(p, encoding="utf-8-sig", newline="") as fh:
            dong = list(csv.DictReader(fh))
    except OSError as exc:
        raise LoiBieuDo(f"không đọc được {p}: {exc}") from exc
    if not dong:
        raise LoiBieuDo(f"{p}: không có dòng dữ liệu")
    can = [cot_tg, cot_bc] + ([cot_nhom] if cot_nhom else [])
    thieu = [c for c in can if c not in dong[0]]
    if thieu:
        raise LoiBieuDo(f"{p}: thiếu cột {', '.join(thieu)}")
    t, e, g, loai = [], [], [], 0
    for r in dong:
        v = [str(r.get(c) or "").strip() for c in can]
        if any(x in ("", "NA", "na", ".", "NaN") for x in v):
            loai += 1
            continue
        try:
            tt, ee = float(v[0].replace(",", ".")), float(v[1].replace(",", "."))
        except ValueError as exc:
            raise LoiBieuDo(f"thời gian/biến cố không phải số: {v[:2]}") from exc
        if tt <= 0:
            raise LoiBieuDo(f"thời gian phải > 0 (gặp {v[0]})")
        if ee != int(ee) or ee < 0:
            raise LoiBieuDo(f"mã biến cố phải là số nguyên ≥ 0 (gặp {v[1]})")
        t.append(tt)
        e.append(int(ee))
        g.append(v[2] if cot_nhom else "")
    ea = np.array(e, int)
    gia_tri = set(ea.tolist())
    if not ma_su_kien:
        if gia_tri == {1, 2} or (2 in gia_tri):
            raise LoiBieuDo("cột biến cố có mã 2 — mã hoá lại 0 = kiểm duyệt, 1 = biến cố (không đoán quy ước 1/2)")
        if 1 not in gia_tri:
            raise LoiBieuDo("không có biến cố nào (toàn bộ kiểm duyệt)")
    elif not (gia_tri - {0}):
        raise LoiBieuDo("không có sự kiện nào (toàn bộ kiểm duyệt)")
    return {"t": np.array(t, float), "e": ea, "g": np.array(g, dtype=object), "loai": loai}


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. KAPLAN–MEIER (như survival::survfit) · TRUNG VỊ · LOG-RANK · COX
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def kaplan_meier(t, e, ktc: str = "log-log") -> Dict[str, Any]:
    """Ước lượng KM tại mỗi thời điểm có biến cố; phương sai Greenwood; KTC 95% theo `ktc` (log-log · log · plain)."""
    import numpy as np  # noqa: PLC0415

    if ktc not in ("log-log", "log", "plain"):
        raise LoiBieuDo("ktc: log-log | log | plain")
    tg = np.unique(t[e == 1])
    S, V, n_ds, d_ds, s_cur, v_cur = [], [], [], [], 1.0, 0.0
    for u in tg:
        n = int(np.sum(t >= u))
        d = int(np.sum((t == u) & (e == 1)))
        s_cur *= 1 - d / n
        v_cur += d / (n * (n - d)) if n > d else float("inf")
        S.append(s_cur)
        V.append(v_cur)
        n_ds.append(n)
        d_ds.append(d)
    S, V = np.array(S), np.array(V)
    lo, hi = np.full(len(S), np.nan), np.full(len(S), np.nan)
    for i, (s, v) in enumerate(zip(S, V)):
        if s <= 0 or not math.isfinite(v):
            continue
        if ktc == "log":
            lo[i], hi[i] = s * math.exp(-Z975 * math.sqrt(v)), min(1.0, s * math.exp(Z975 * math.sqrt(v)))
        elif ktc == "plain":
            lo[i], hi[i] = max(0.0, s - Z975 * s * math.sqrt(v)), min(1.0, s + Z975 * s * math.sqrt(v))
        elif s < 1:
            se2 = math.sqrt(v) / abs(math.log(s))
            lo[i] = math.exp(-math.exp(math.log(-math.log(s)) + Z975 * se2))
            hi[i] = math.exp(-math.exp(math.log(-math.log(s)) - Z975 * se2))
        else:
            lo[i] = hi[i] = 1.0
    kiem_duyet = np.sort(t[e == 0])
    return {"t": tg, "S": S, "lo": lo, "hi": hi, "n_nguy_co": np.array(n_ds), "so_bien_co": np.array(d_ds),
            "kiem_duyet": kiem_duyet, "n": int(len(t)), "tong_bien_co": int(e.sum()), "ktc": ktc}


def tai_moc(km: Dict[str, Any], t_goc, moc: Sequence[float]) -> List[Dict[str, Any]]:
    """S, KTC và số nguy cơ tại các mốc (như summary(survfit, times=)): S của thời điểm biến cố lớn nhất ≤ mốc."""
    import numpy as np  # noqa: PLC0415

    ra = []
    for m in moc:
        i = int(np.searchsorted(km["t"], m, side="right")) - 1
        s, lo, hi = (1.0, 1.0, 1.0) if i < 0 else (float(km["S"][i]), float(km["lo"][i]), float(km["hi"][i]))
        ra.append({"moc": m, "n_nguy_co": int(np.sum(t_goc >= m)), "S": s, "lo": lo, "hi": hi})
    return ra


def _cat_05(t, S) -> Optional[float]:
    """Thời điểm đầu tiên đường ≤ 0,5; nếu đường bằng ĐÚNG 0,5 trên một đoạn ⇒ trung bình hai đầu đoạn (survfit)."""
    for i, s in enumerate(S):
        if s is None or (isinstance(s, float) and math.isnan(s)):
            continue
        if s < 0.5 - 1e-12:
            return float(t[i])
        if abs(s - 0.5) <= 1e-12:
            return float((t[i] + t[i + 1]) / 2) if i + 1 < len(t) else float(t[i])
    return None


def trung_vi(km: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """Trung vị sống còn + KTC 95% đọc từ hai đường KTC (như survfit): cận dưới = lúc đường KTC DƯỚI cắt 0,5 (sớm hơn),
    cận trên = lúc đường KTC TRÊN cắt 0,5 (muộn hơn; không cắt ⇒ chưa đạt)."""
    return {"trung_vi": _cat_05(km["t"], km["S"]), "duoi": _cat_05(km["t"], km["lo"]),
            "tren": _cat_05(km["t"], km["hi"])}


def log_rank(t, e, g) -> Dict[str, Any]:
    """Kiểm định log-rank nhiều nhóm (như survdiff): χ² = (O − E)ᵀ V⁻¹ (O − E), df = G − 1."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    nhom = list(dict.fromkeys(g.tolist()))
    G = len(nhom)
    if G < 2:
        raise LoiBieuDo("log-rank cần ≥ 2 nhóm")
    Ob, E, V = np.zeros(G), np.zeros(G), np.zeros((G, G))
    for u in np.unique(t[e == 1]):
        nguy = t >= u
        n = nguy.sum()
        d = ((t == u) & (e == 1)).sum()
        ng = np.array([(nguy & (g == k)).sum() for k in nhom], float)
        dg = np.array([((t == u) & (e == 1) & (g == k)).sum() for k in nhom], float)
        Ob += dg
        E += d * ng / n
        if n > 1:
            V += d * (n - d) / (n - 1) * (np.diag(ng / n) - np.outer(ng, ng) / n ** 2)
    z = (Ob - E)[:-1]
    chi2 = float(z @ np.linalg.solve(V[:-1, :-1], z))
    return {"nhom": nhom, "quan_sat": Ob.tolist(), "ky_vong": E.tolist(), "chi2": chi2, "df": G - 1,
            "p": float(stats.chi2.sf(chi2, G - 1))}


def cox_nhom(t, e, g, tham_chieu: Optional[str] = None) -> Dict[str, Any]:
    """Cox một biến phân nhóm (xử lý trùng Efron, như coxph mặc định) — HR mỗi nhóm so với nhóm tham chiếu."""
    import numpy as np  # noqa: PLC0415
    from scipy import stats  # noqa: PLC0415

    nhom = list(dict.fromkeys(g.tolist()))
    ref = tham_chieu if tham_chieu is not None else nhom[0]
    if ref not in nhom:
        raise LoiBieuDo(f"nhóm tham chiếu «{ref}» không có trong dữ liệu ({', '.join(nhom)})")
    khac = [k for k in nhom if k != ref]
    X = np.column_stack([(g == k).astype(float) for k in khac])
    b = np.zeros(X.shape[1])
    thoi_diem = np.unique(t[e == 1])
    for _ in range(50):
        U, info = np.zeros_like(b), np.zeros((len(b), len(b)))
        r = np.exp(X @ b)
        for u in thoi_diem:
            nguy = t >= u
            chet = (t == u) & (e == 1)
            d = int(chet.sum())
            s0 = r[nguy].sum()
            s1 = (r[nguy, None] * X[nguy]).sum(0)
            s2 = (r[nguy, None, None] * X[nguy][:, :, None] * X[nguy][:, None, :]).sum(0)
            c0 = r[chet].sum()
            c1 = (r[chet, None] * X[chet]).sum(0)
            c2 = (r[chet, None, None] * X[chet][:, :, None] * X[chet][:, None, :]).sum(0)
            U += X[chet].sum(0)
            for j in range(d):  # Efron
                f = j / d
                a0, a1, a2 = s0 - f * c0, s1 - f * c1, s2 - f * c2
                U -= a1 / a0
                info += a2 / a0 - np.outer(a1, a1) / a0 ** 2
        buoc = np.linalg.solve(info, U)
        b = b + buoc
        if np.max(np.abs(buoc)) < 1e-10:
            break
    cov = np.linalg.inv(info)
    ra = {"tham_chieu": ref, "hr": {}}
    for i, k in enumerate(khac):
        se = math.sqrt(cov[i, i])
        ra["hr"][k] = {"hr": math.exp(b[i]), "ktc": (math.exp(b[i] - Z975 * se), math.exp(b[i] + Z975 * se)),
                       "p": float(2 * stats.norm.sf(abs(b[i] / se)))}
    return ra


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. TẦN SUẤT TÍCH LUỸ CÓ BIẾN CỐ CẠNH TRANH (Aalen–Johansen)
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def aalen_johansen(t, ma) -> Dict[str, Any]:
    """CIF_k(t) = Σ_{t_j ≤ t} S(t_j⁻)·d_kj/n_j, S = KM với MỌI sự kiện là biến cố (như survfit đa trạng thái)."""
    import numpy as np  # noqa: PLC0415

    nguyen = sorted(set(ma.tolist()) - {0})
    tg = np.unique(t[ma > 0])
    s_truoc, cif, S_ra = 1.0, {k: [] for k in nguyen}, []
    tich = {k: 0.0 for k in nguyen}
    for u in tg:
        n = int(np.sum(t >= u))
        d_tat = int(np.sum((t == u) & (ma > 0)))
        for k in nguyen:
            tich[k] += s_truoc * int(np.sum((t == u) & (ma == k))) / n
            cif[k].append(tich[k])
        s_truoc *= 1 - d_tat / n
        S_ra.append(s_truoc)
    return {"t": tg, "cif": {k: np.array(v) for k, v in cif.items()}, "S": np.array(S_ra), "nguyen_nhan": nguyen}


def cif_tai_moc(aj: Dict[str, Any], moc: Sequence[float]) -> List[Dict[str, Any]]:
    import numpy as np  # noqa: PLC0415

    ra = []
    for m in moc:
        i = int(np.searchsorted(aj["t"], m, side="right")) - 1
        ra.append({"moc": m, **{f"cif_{k}": (0.0 if i < 0 else float(aj["cif"][k][i])) for k in aj["nguyen_nhan"]},
                   "khong_su_kien": 1.0 if i < 0 else float(aj["S"][i])})
    return ra


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. VẼ
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _moc_mac_dinh(tmax: float) -> List[float]:
    import numpy as np  # noqa: PLC0415

    buoc = 10 ** math.floor(math.log10(tmax / 5)) if tmax > 0 else 1
    for h in (1, 2, 2.5, 5, 10):
        if tmax / (buoc * h) <= 7:
            buoc *= h
            break
    return [float(x) for x in np.arange(0, tmax + 1e-9, buoc)]


def _bac_thang(t, S, t0: float = 0.0, y0: float = 1.0):
    """(x, y) bậc thang bắt đầu tại (t0, y0): y0 = 1 cho S(t) của KM, y0 = 0 cho tần suất tích luỹ."""
    import numpy as np  # noqa: PLC0415

    return np.r_[t0, t], np.r_[y0, S]


def ve_km(t, e, g, dich: Path, ktc: str = "log-log", moc: Optional[Sequence[float]] = None, don_vi: str = "",
          tham_chieu: Optional[str] = None, dao: bool = False, ngon_ngu: str = "vi",
          so_loai: int = 0) -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    nhom = list(dict.fromkeys(g.tolist()))
    moc = list(moc) if moc else _moc_mac_dinh(float(t.max()))
    co_nhom = len(nhom) > 1
    cao_bang = 0.32 * (len(nhom) + 1.2)
    fig = plt.figure(figsize=(6.4, 4.4 + cao_bang))
    gs = fig.add_gridspec(2, 1, height_ratios=[4.4, cao_bang], hspace=0.42)
    ax, axb = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    kq: Dict[str, Any] = {"loai": "km", "ktc": ktc, "dao": dao, "moc": moc, "nhom": {},
                          "so_dong_loai_vi_thieu": so_loai}
    for i, k in enumerate(nhom):
        m = g == k
        km = kaplan_meier(t[m], e[m], ktc)
        tv = trung_vi(km)
        mau, net = MAU[i % len(MAU)], NET[i % len(NET)]
        x, yv = _bac_thang(km["t"], km["S"])
        _, lo = _bac_thang(km["t"], np.nan_to_num(km["lo"], nan=0.0))
        _, hi = _bac_thang(km["t"], np.nan_to_num(km["hi"], nan=0.0))
        x = np.r_[x, max(float(t[m].max()), float(x[-1]))]
        yv, lo, hi = np.r_[yv, yv[-1]], np.r_[lo, lo[-1]], np.r_[hi, hi[-1]]
        f = (lambda a: 1 - a) if dao else (lambda a: a)
        ten = (f"{k} (n = {km['n']}; {km['tong_bien_co']} {'biến cố' if vi else 'events'})" if co_nhom else
               (f"n = {km['n']}; {km['tong_bien_co']} {'biến cố' if vi else 'events'}"))
        ax.step(x, f(yv), where="post", color=mau, ls=net, lw=1.5, label=ten, zorder=3)
        ax.fill_between(x, f(lo), f(hi), step="post", color=mau, alpha=0.13, lw=0, zorder=1)
        cd = km["kiem_duyet"]
        if len(cd):
            idx = np.searchsorted(km["t"], cd, side="right") - 1
            sc = np.where(idx < 0, 1.0, km["S"][np.clip(idx, 0, None)])
            ax.plot(cd, f(sc), ls="none", marker="|", ms=5, mew=0.9, color=mau, zorder=4)
        if tv["trung_vi"] is not None and not dao:
            ax.plot([0, tv["trung_vi"]], [0.5, 0.5], color="#999999", lw=0.6, ls=":")
            ax.plot([tv["trung_vi"]] * 2, [0, 0.5], color=mau, lw=0.6, ls=":")
        kq["nhom"][k] = {"n": km["n"], "bien_co": km["tong_bien_co"], "trung_vi": tv, "tai_moc": tai_moc(km, t[m], moc),
                         "duong": {"t": km["t"].tolist(), "S": km["S"].tolist(), "lo": km["lo"].tolist(),
                                   "hi": km["hi"].tolist()}}
    chu = []
    if co_nhom:
        lr = log_rank(t, e, g)
        kq["log_rank"] = lr
        chu.append(f"Log-rank: χ² = {so(lr['chi2'], 2, ngon_ngu)} (df = {lr['df']}), {BC.p_chu(lr['p'], ngon_ngu)}")
        cx = cox_nhom(t, e, g, tham_chieu)
        kq["cox"] = cx
        for k, h in cx["hr"].items():
            chu.append(f"HR {k} vs {cx['tham_chieu']}: {so(h['hr'], 2, ngon_ngu)} ({so(h['ktc'][0], 2, ngon_ngu)}–"
                       f"{so(h['ktc'][1], 2, ngon_ngu)}), {BC.p_chu(h['p'], ngon_ngu)}")
    for k, v in kq["nhom"].items():
        tv = v["trung_vi"]
        if tv["trung_vi"] is not None:
            ktc_tv = (f"{so(tv['duoi'], 0, ngon_ngu) if tv['duoi'] is not None else '—'}–"
                      f"{so(tv['tren'], 0, ngon_ngu) if tv['tren'] is not None else ('chưa đạt' if vi else 'NR')}")
            chu.append(f"{'Trung vị' if vi else 'Median'}{(' ' + k) if co_nhom else ''}: "
                       f"{so(tv['trung_vi'], 0, ngon_ngu)} ({ktc_tv})")
    ax.text(0.98, 0.98 if dao is False else 0.02, "\n".join(chu), transform=ax.transAxes, ha="right",
            va="top" if not dao else "bottom", fontsize=7.6)
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, max(moc[-1], float(t.max())) * 1.01)
    ax.set_xticks(moc)
    ax.tick_params(labelbottom=True)
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    BC.dinh_dang_truc(ax, ngon_ngu, "y", nd=1)
    ax.set_ylabel(("Tỷ lệ tích luỹ có biến cố" if vi else "Cumulative incidence") if dao else
                  ("Xác suất sống còn (chưa có biến cố)" if vi else "Survival probability"))
    ax.set_xlabel(("Thời gian" if vi else "Time") + (f" ({don_vi})" if don_vi else ""))
    ax.legend(loc="lower left" if not dao else "upper left", frameon=False, fontsize=8)
    # bảng số nguy cơ
    axb.set_xlim(ax.get_xlim())
    axb.set_ylim(-0.5, len(nhom) - 0.5)
    axb.set_xticks(moc)
    axb.tick_params(axis="x", length=0, labelbottom=False)
    axb.set_yticks(range(len(nhom)))
    axb.set_yticklabels(nhom[::-1] if co_nhom else ["N"])
    axb.tick_params(axis="y", length=0, pad=18)
    for s in ("top", "right", "bottom", "left"):
        axb.spines[s].set_visible(False)
    for i, k in enumerate(nhom):
        yb = len(nhom) - 1 - i
        for mm in kq["nhom"][k]["tai_moc"]:
            axb.text(mm["moc"], yb, str(mm["n_nguy_co"]), ha="center", va="center", fontsize=8,
                     color=MAU[i % len(MAU)])
        axb.get_yticklabels()[yb].set_color(MAU[i % len(MAU)])
    axb.set_title("Số đối tượng còn nguy cơ" if vi else "Number at risk", fontsize=8.5, loc="left")
    kq["ghi_chu"] = (f"KM, phương sai Greenwood, KTC 95% kiểu {ktc}; HR từ Cox (Efron); trung vị đọc tại S = 0,5. "
                     "Cần bác sĩ kiểm chứng.")
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_loglog(t, e, g, dich: Path, don_vi: str = "", ngon_ngu: str = "vi") -> Dict[str, Any]:
    import numpy as np  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    fig, ax = plt.subplots(figsize=(5.4, 4.2))
    kq: Dict[str, Any] = {"loai": "loglog", "nhom": {}}
    for i, k in enumerate(dict.fromkeys(g.tolist())):
        km = kaplan_meier(t[g == k], e[g == k])
        ok = (km["S"] > 0) & (km["S"] < 1)
        x, y = km["t"][ok], np.log(-np.log(km["S"][ok]))
        ax.step(x, y, where="post", color=MAU[i % len(MAU)], ls=NET[i % len(NET)], lw=1.4, label=str(k))
        kq["nhom"][k] = {"t": x.tolist(), "log_minus_log_S": y.tolist()}
    ax.set_xscale("log")
    from matplotlib.ticker import FuncFormatter  # noqa: PLC0415

    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _p: BC.so(v, 0 if v >= 1 else 2, ngon_ngu)))
    BC.dinh_dang_truc(ax, ngon_ngu, "y")
    vi = ngon_ngu == "vi"
    ax.set_xlabel(("Thời gian, thang log" if vi else "Time, log scale") + (f" ({don_vi})" if don_vi else ""))
    ax.set_ylabel("log(−log S(t))")
    ax.legend(frameon=False, fontsize=8)
    ax.text(0.98, 0.02, "Hai đường song song → phù hợp giả định nguy cơ tỷ lệ" if vi else
            "Parallel curves support proportional hazards", transform=ax.transAxes, ha="right", fontsize=7.5)
    kq["ghi_chu"] = ("Kiểm trực quan giả định nguy cơ tỷ lệ; nên kèm kiểm định Schoenfeld (cox.zph). "
                     "Cần bác sĩ kiểm chứng.")
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_cif(t, ma, g, dich: Path, nhan_su_kien: Optional[Dict[int, str]] = None, moc: Optional[Sequence[float]] = None,
           don_vi: str = "", ngon_ngu: str = "vi", so_loai: int = 0) -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    nhom = list(dict.fromkeys(g.tolist()))
    moc = list(moc) if moc else _moc_mac_dinh(float(t.max()))
    fig, ax = plt.subplots(figsize=(6.2, 4.4))
    kq: Dict[str, Any] = {"loai": "cif", "nhom": {}, "moc": moc, "so_dong_loai_vi_thieu": so_loai}
    for i, k in enumerate(nhom):
        aj = aalen_johansen(t[g == k], ma[g == k])
        duong = {}
        for j, c in enumerate(aj["nguyen_nhan"]):
            x, y = _bac_thang(aj["t"], aj["cif"][c], y0=0.0)  # CIF bắt đầu từ 0 (KM mới bắt đầu từ 1)
            duong[c] = {"t": x.tolist(), "cif": y.tolist()}  # hình vẽ đúng đường ghi vào JSON
            ten_c = (nhan_su_kien or {}).get(c, f"{'Sự kiện' if vi else 'Event'} {c}")
            ax.step(duong[c]["t"], duong[c]["cif"], where="post", color=MAU[i % len(MAU)], ls=NET[j % len(NET)],
                    lw=1.5, label=f"{ten_c}{(' — ' + str(k)) if len(nhom) > 1 else ''}")
        kq["nhom"][k] = {"tai_moc": cif_tai_moc(aj, moc), "nguyen_nhan": aj["nguyen_nhan"], "duong": duong}
    ax.set_xlim(0, max(moc[-1], float(t.max())) * 1.01)
    ax.set_ylim(0, None)
    ax.set_xticks(moc)
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    BC.dinh_dang_truc(ax, ngon_ngu, "y", nd=2)
    ax.set_xlabel(("Thời gian" if vi else "Time") + (f" ({don_vi})" if don_vi else ""))
    ax.set_ylabel("Tần suất tích luỹ (Aalen–Johansen)" if vi else "Cumulative incidence (Aalen–Johansen)")
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    kq["ghi_chu"] = ("Aalen–Johansen, có tính biến cố cạnh tranh; chưa có kiểm định Gray (cần cmprsk). Cần bác sĩ "
                     "kiểm chứng.")
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 5. KIỂM CHÉO R
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _r_du_lieu(t, e, g) -> str:
    nhom = list(dict.fromkeys(g.tolist()))
    ma_nhom = [nhom.index(x) for x in g.tolist()]
    return (f"tt <- {BC.r_vec(t)}; ee <- {BC.r_vec(e)}\n"
            f"gg <- factor({BC.r_vec(ma_nhom)}, levels={BC.r_vec(range(len(nhom)))})\n")


def kiem_cheo_km_r(t, e, g, moc: Sequence[float], ktc: str = "log-log",
                   tham_chieu: Optional[str] = None) -> Dict[str, Any]:
    nhom = list(dict.fromkeys(g.tolist()))
    py: Dict[str, float] = {}
    for i, k in enumerate(nhom):
        km = kaplan_meier(t[g == k], e[g == k], ktc)
        for j, mm in enumerate(tai_moc(km, t[g == k], moc)):
            py[f"s{i}_{j}"], py[f"n{i}_{j}"] = mm["S"], float(mm["n_nguy_co"])
            if mm["S"] < 1 and not math.isnan(mm["lo"]):
                py[f"lo{i}_{j}"], py[f"hi{i}_{j}"] = mm["lo"], mm["hi"]
        tv = trung_vi(km)
        for ten in ("trung_vi", "duoi", "tren"):
            if tv[ten] is not None:
                py[f"{ten}{i}"] = tv[ten]
    ma = (f"suppressMessages(library(survival))\n{_r_du_lieu(t, e, g)}"
          f'f <- survfit(Surv(tt, ee) ~ gg, conf.type="{ktc}")\n'
          f"moc <- {BC.r_vec(moc)}\n")
    for i in range(len(nhom)):
        ma += (f"fi <- survfit(Surv(tt[gg=={i}], ee[gg=={i}]) ~ 1, conf.type=\"{ktc}\")\n"
               f"s <- summary(fi, times=moc, extend=TRUE)\n"
               f"for (j in seq_along(moc)) {{ cat('KQ', paste0('s{i}_', j-1), s$surv[j], '\\n'); "
               f"cat('KQ', paste0('n{i}_', j-1), s$n.risk[j], '\\n'); "
               f"if (!is.na(s$lower[j]) && s$surv[j] < 1) {{ cat('KQ', paste0('lo{i}_', j-1), s$lower[j], '\\n'); "
               f"cat('KQ', paste0('hi{i}_', j-1), s$upper[j], '\\n') }} }}\n"
               f"tb <- summary(fi)$table\n"
               f"if (!is.na(tb['median'])) cat('KQ trung_vi{i}', tb['median'], '\\n')\n"
               f"if (!is.na(tb['0.95LCL'])) cat('KQ duoi{i}', tb['0.95LCL'], '\\n')\n"
               f"if (!is.na(tb['0.95UCL'])) cat('KQ tren{i}', tb['0.95UCL'], '\\n')\n")
    if len(nhom) > 1:
        lr = log_rank(t, e, g)
        py["logrank_chi2"] = lr["chi2"]
        ref = tham_chieu if tham_chieu is not None else nhom[0]
        cx = cox_nhom(t, e, g, ref)
        ma += (f"sd <- survdiff(Surv(tt, ee) ~ gg); cat('KQ logrank_chi2', sd$chisq, '\\n')\n"
               f"gg2 <- relevel(gg, ref='{nhom.index(ref)}')\n"
               f"cx <- coxph(Surv(tt, ee) ~ gg2); hr <- exp(coef(cx)); ci <- exp(confint(cx))\n")
        for k, h in cx["hr"].items():
            j = nhom.index(k)
            py[f"hr{j}"], py[f"hrlo{j}"], py[f"hrhi{j}"] = h["hr"], h["ktc"][0], h["ktc"][1]
            ma += (f"cat('KQ hr{j}', hr['gg2{j}'], '\\n'); cat('KQ hrlo{j}', ci['gg2{j}', 1], '\\n'); "
                   f"cat('KQ hrhi{j}', ci['gg2{j}', 2], '\\n')\n")
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-7)


def kiem_cheo_cif_r(t, ma_sk, g, moc: Sequence[float]) -> Dict[str, Any]:
    nhom = list(dict.fromkeys(g.tolist()))
    py: Dict[str, float] = {}
    nguyen = sorted(set(ma_sk.tolist()) - {0})
    for i, k in enumerate(nhom):
        for j, mm in enumerate(cif_tai_moc(aalen_johansen(t[g == k], ma_sk[g == k]), moc)):
            for c in nguyen:
                if f"cif_{c}" in mm:
                    py[f"c{i}_{j}_{c}"] = mm[f"cif_{c}"]
    lv = ", ".join(str(x) for x in [0, *nguyen])
    ma = f"suppressMessages(library(survival))\n{_r_du_lieu(t, ma_sk, g)}moc <- {BC.r_vec(moc)}\n"
    for i in range(len(nhom)):
        ma += (f"fi <- survfit(Surv(tt[gg=={i}], factor(ee[gg=={i}], levels=c({lv}))) ~ 1)\n"
               f"s <- summary(fi, times=moc, extend=TRUE)\n"
               f"for (j in seq_along(moc)) for (c in seq_along(c({lv}))[-1]) "
               f"cat('KQ', paste0('c{i}_', j-1, '_', c({lv})[c]), s$pstate[j, c], '\\n')\n")
    return BC.doi_chieu(py, BC.chay_r_kiem_cheo(ma), dung_sai=1e-7)


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 6. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _moc(s: Optional[str]) -> Optional[List[float]]:
    if not s:
        return None
    try:
        v = [float(x) for x in s.split(",")]
    except ValueError as exc:
        raise LoiBieuDo("--moc dạng 0,180,365 (số cách nhau dấu phẩy)") from exc
    if v != sorted(v) or v[0] < 0:
        raise LoiBieuDo("--moc phải tăng dần, ≥ 0")
    return v


def _nhan_su_kien(s: Optional[str]) -> Dict[int, str]:
    ra: Dict[int, str] = {}
    for phan in (s or "").split(","):
        if "=" in phan:
            k, v = phan.split("=", 1)
            ra[int(k.strip())] = v.strip()
    return ra


def main(argv: Optional[Sequence[str]] = None) -> int:
    from bieu_do_gop import _in_kiem_cheo  # noqa: PLC0415

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("km", "loglog", "cif"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--thoi-gian", required=True)
    ap.add_argument("--bien-co", help="km/loglog: cột 0/1")
    ap.add_argument("--su-kien", help="cif: cột mã 0 = kiểm duyệt, 1, 2, …")
    ap.add_argument("--nhom")
    ap.add_argument("--tham-chieu")
    ap.add_argument("--ktc", default="log-log", choices=("log-log", "log", "plain"))
    ap.add_argument("--moc")
    ap.add_argument("--don-vi", default="")
    ap.add_argument("--dao", action="store_true")
    ap.add_argument("--nhan-su-kien")
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    ap.add_argument("--kiem-cheo-r", action="store_true")
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        moc = _moc(a.moc)
        ma_kc = 0
        if a.lenh in ("km", "loglog"):
            if not a.bien_co:
                print("❌ cần --bien-co")
                return 3
            d = doc_du_lieu(a.du_lieu, a.thoi_gian, a.bien_co, a.nhom)
            if d["loai"]:
                print(f"   ⚠ loại {d['loai']} dòng thiếu giá trị")
            if a.lenh == "km":
                kq = ve_km(d["t"], d["e"], d["g"], a.ra, a.ktc, moc, a.don_vi, a.tham_chieu, a.dao, a.ngon_ngu,
                           d["loai"])
                for k, v in kq["nhom"].items():
                    tv = v["trung_vi"]
                    print(f"✅ {k or 'toàn mẫu'}: n = {v['n']}, biến cố = {v['bien_co']}, trung vị = "
                          f"{so(tv['trung_vi'], 0) if tv['trung_vi'] is not None else 'chưa đạt'}")
                if "log_rank" in kq:
                    print(f"   log-rank χ² = {so(kq['log_rank']['chi2'], 2)}, {BC.p_chu(kq['log_rank']['p'])}")
                if a.kiem_cheo_r:
                    ma_kc = _in_kiem_cheo("KM/log-rank/Cox (survival)",
                                          kiem_cheo_km_r(d["t"], d["e"], d["g"], kq["moc"], a.ktc, a.tham_chieu))
            else:
                if not a.nhom:
                    print("❌ loglog cần --nhom")
                    return 3
                ve_loglog(d["t"], d["e"], d["g"], a.ra, a.don_vi, a.ngon_ngu)
                print("✅ log(−log S)")
        else:
            if not a.su_kien:
                print("❌ cif cần --su-kien")
                return 3
            d = doc_du_lieu(a.du_lieu, a.thoi_gian, a.su_kien, a.nhom, ma_su_kien=True)
            kq = ve_cif(d["t"], d["e"], d["g"], a.ra, _nhan_su_kien(a.nhan_su_kien), moc, a.don_vi, a.ngon_ngu,
                        d["loai"])
            print(f"✅ CIF Aalen–Johansen: {len(kq['nhom'])} nhóm")
            if a.kiem_cheo_r:
                ma_kc = _in_kiem_cheo("CIF (survfit đa trạng thái)", kiem_cheo_cif_r(d["t"], d["e"], d["g"], kq["moc"]))
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return ma_kc


if __name__ == "__main__":
    sys.exit(main())
