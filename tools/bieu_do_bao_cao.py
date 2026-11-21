#!/usr/bin/env python3
"""Biểu đồ BÁO CÁO — sơ đồ luồng có số thật, nguy cơ sai lệch, kinh tế y tế (chặng 5b chương trình biểu đồ, bác sĩ
21/11/2026: «phải thực hiện được tất cả biểu đồ một cách chi tiết và chính xác nhất»).

Họ biểu đồ (PNG 300 dpi + PDF vector + JSON số liệu đã vẽ):
  so-do-luong   sơ đồ chọn đối tượng CONSORT / STROBE / STARD / PRISMA có SỐ THẬT: hộp chính theo trục dọc, hộp loại
                trừ (kèm lý do) bên phải, tách nhánh (nhóm can thiệp/chứng) sau bước phân bổ. KIỂM SỐ HỌC: n bước sau
                = n bước trước − tổng loại trừ ở giữa; chi tiết lý do phải cộng đủ số loại — lệch ⇒ từ chối vẽ (lỗi
                hay gặp nhất của sơ đồ luồng khi nộp bài).
  rob           nguy cơ sai lệch kiểu «đèn giao thông» (từng nghiên cứu × miền) + biểu đồ TÓM TẮT % theo miền (có trọng
                số nếu khai) — nhận RoB 2, ROBINS-I/ROBINS-E, QUADAS-2/3, hay bộ miền tự đặt.
  ce-plane      mặt phẳng chi phí – hiệu quả từ các lần lặp phân tích độ nhạy xác suất (PSA): đám điểm ΔC–ΔE, điểm
                trung bình, ICER, đường ngưỡng sẵn lòng chi trả λ, % lặp mỗi góc phần tư, % có hiệu quả chi phí tại λ.
  ceac          đường cong chấp nhận hiệu quả chi phí: P(λ·ΔE − ΔC > 0) theo λ (CHEERS 2022).
  tornado       biểu đồ lốc xoáy phân tích độ nhạy một chiều: thanh từ kết quả ở giá trị thấp đến cao của từng
                tham số, xếp theo độ rộng, đường kết quả cơ sở.

Ranh giới: vẽ đúng số khai; không mô phỏng PSA, không chấm RoB thay người đánh giá. Cần bác sĩ kiểm chứng.

Dữ liệu vào:
  so-do-luong: CSV cột buoc, n, loai (chinh | loai), [nhanh], [ly_do] — ly_do dạng
      «Không đủ tiêu chuẩn: 12; Từ chối: 5».
  rob: CSV cột nghien_cuu, các cột miền …, [trong_so]; giá trị Thấp/Low/+ · Một số lo ngại/Some concerns/? ·
       Cao/High/− · Nghiêm trọng/Serious · Rất nghiêm trọng/Critical · Không thông tin/No information.
  ce-plane / ceac: CSV cột d_chi_phi, d_hieu_qua (mỗi dòng một lần lặp PSA).
  tornado: CSV cột tham_so, ket_qua_thap, ket_qua_cao [, gia_tri_thap, gia_tri_cao].

Lệnh:
  python3 tools/bieu_do_bao_cao.py so-do-luong --du-lieu luong.csv [--chuan CONSORT] --ra …
  python3 tools/bieu_do_bao_cao.py rob --du-lieu rob.csv [--cong-cu "RoB 2"] --ra …
  python3 tools/bieu_do_bao_cao.py ce-plane --du-lieu psa.csv --nguong-chi-tra 50000000 [--don-vi-chi-phi VNĐ]
      [--don-vi-hieu-qua QALY] --ra …
  python3 tools/bieu_do_bao_cao.py ceac --du-lieu psa.csv --lambda-toi-da 150000000 --ra …
  python3 tools/bieu_do_bao_cao.py tornado --du-lieu tornado.csv --co-so 32000000 [--ten-ket-qua ICER] --ra …
Mã thoát: 0 xong · 2 dữ liệu sai/thiếu (gồm lệch số học sơ đồ luồng) · 3 tham số sai.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

BASE = Path(__file__).resolve().parents[1]
if str(BASE / "tools") not in sys.path:
    sys.path.insert(0, str(BASE / "tools"))

import bieu_do_chung as BC  # noqa: E402
from bieu_do_chung import LoiBieuDo, so  # noqa: E402
from bieu_do_mo_ta import THIEU, doc_csv, ktc_ty_le, so_hoc  # noqa: E402

MAU = ("#1f4e79", "#a23b2a", "#2e7d32", "#6a3d9a", "#b8860b", "#00838f")


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 1. SƠ ĐỒ LUỒNG CÓ SỐ — kiểm số học
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def _ly_do(s: str) -> List[Dict[str, Any]]:
    ra = []
    for phan in (s or "").split(";"):
        phan = phan.strip()
        if not phan:
            continue
        m = re.match(r"^(.*?)[:=]\s*(\d+)\s*$", phan)
        if not m:
            raise LoiBieuDo(f"lý do loại trừ phải dạng «Lý do: số» (gặp «{phan}»)")
        ra.append({"ly_do": m.group(1).strip(), "n": int(m.group(2))})
    return ra


def kiem_so_hoc_luong(dong: Sequence[Dict[str, str]]) -> Dict[str, Any]:
    """Dựng các nhánh và kiểm: n chính sau = n chính trước − Σ loại trừ giữa hai hộp chính (theo từng nhánh); Σ chi
    tiết lý do = n hộp loại. Trả {"nhanh": {tên: [bước…]}, "loi": [...]}. Hộp chính đầu tiên của một nhánh mới lấy
    gốc là hộp chính cuối cùng của trục chung (bước phân bổ) — tổng n các nhánh phải bằng n bước phân bổ."""
    for c in ("buoc", "n", "loai"):
        if c not in dong[0]:
            raise LoiBieuDo(f"sơ đồ luồng thiếu cột «{c}»")
    loi: List[str] = []
    nhanh: Dict[str, List[Dict[str, Any]]] = {}
    for r in dong:
        loai = r["loai"].strip().lower()
        if loai not in ("chinh", "loai"):
            raise LoiBieuDo(f"cột loai chỉ nhận chinh | loai (gặp «{r['loai']}»)")
        try:
            n = int(r["n"])
        except ValueError as exc:
            raise LoiBieuDo(f"n phải là số nguyên ở bước «{r['buoc']}»") from exc
        if n < 0:
            raise LoiBieuDo(f"n âm ở bước «{r['buoc']}»")
        b = {"buoc": r["buoc"], "n": n, "loai": loai, "ly_do": _ly_do(r.get("ly_do", ""))}
        if b["ly_do"] and sum(x["n"] for x in b["ly_do"]) != n:
            loi.append(f"«{r['buoc']}»: chi tiết lý do cộng {sum(x['n'] for x in b['ly_do'])} ≠ {n}")
        nhanh.setdefault((r.get("nhanh") or "").strip(), []).append(b)
    chung = nhanh.get("", [])
    goc_chung = next((b for b in reversed(chung) if b["loai"] == "chinh"), None)
    for ten, buoc in nhanh.items():
        truoc, loai_giua = None, 0  # hộp chính đầu nhánh được kiểm bằng TỔNG các nhánh (dưới), không trừ từ gốc
        for b in buoc:
            if b["loai"] == "loai":
                loai_giua += b["n"]
                continue
            if truoc is not None and b["n"] != truoc["n"] - loai_giua:
                loi.append(f"nhánh «{ten or 'chung'}»: «{b['buoc']}» n = {b['n']} nhưng «{truoc['buoc']}» "
                           f"{truoc['n']} − loại {loai_giua} = {truoc['n'] - loai_giua}")
            truoc, loai_giua = b, 0
    ten_nhanh = [k for k in nhanh if k]
    if ten_nhanh and goc_chung is not None:
        dau = [next((b for b in nhanh[k] if b["loai"] == "chinh"), None) for k in ten_nhanh]
        if all(dau) and sum(b["n"] for b in dau) != goc_chung["n"]:
            loi.append(f"tổng n đầu các nhánh {sum(b['n'] for b in dau)} ≠ «{goc_chung['buoc']}» {goc_chung['n']}")
    return {"nhanh": nhanh, "loi": loi}


def _chu_hop(b: Dict[str, Any]) -> str:
    chu = f"{b['buoc']} (n = {b['n']})"
    if b["ly_do"]:
        chu += "\n" + "\n".join(f"• {d['ly_do']} (n = {d['n']})" for d in b["ly_do"])
    return chu


def _kich_thuoc(chu: str, w_min: float = 2.2) -> tuple:
    """(rộng, cao) hộp theo inch: phông 7,6 pt ≈ 0,064 inch/ký tự, 0,15 inch/dòng."""
    dong = chu.split("\n")
    return max(w_min, 0.064 * max(len(d) for d in dong) + 0.3), 0.16 + 0.15 * len(dong)


def dan_trang_luong(k: Dict[str, Any]) -> Dict[str, Any]:
    """Lượt 1: toạ độ (inch) mọi hộp và mũi tên. Trục chung: hộp chính dọc giữa, hộp loại trừ bên phải nằm trong
    khoảng giữa hai hộp chính; nhánh: mọi hộp xếp dọc nối tiếp (kiểu CONSORT), mũi tên nối đáy hộp trước – đỉnh hộp
    sau (không xuyên qua hộp)."""
    chung = k["nhanh"].get("", [])
    nhanh = [t for t in k["nhanh"] if t]
    hop, ten_nhanh, mui = [], [], []
    w_chinh = max([_kich_thuoc(_chu_hop(b))[0] for b in chung if b["loai"] == "chinh"] + [2.4])
    w_loai = max([_kich_thuoc(_chu_hop(b))[0] for b in chung if b["loai"] == "loai"] + [0.0])
    w_nhanh = max([_kich_thuoc(_chu_hop(b))[0] for t in nhanh for b in k["nhanh"][t]] + [2.2])
    rong = max(w_chinh + (0.5 + w_loai) * 2 if w_loai else w_chinh, (w_nhanh + 0.5) * max(len(nhanh), 1)) + 0.4
    xc = rong / 2
    y = 0.0
    day_truoc = None
    i = 0
    while i < len(chung):
        b = chung[i]
        if b["loai"] == "chinh":
            w, h = w_chinh, _kich_thuoc(_chu_hop(b))[1]
            if day_truoc is not None:
                mui.append(((xc, day_truoc), (xc, y)))
            hop.append({"x": xc, "y": y, "w": w, "h": h, "chu": _chu_hop(b), "trai": False})
            day_truoc = y - h
            y = day_truoc
            loai_sau = []
            while i + 1 < len(chung) and chung[i + 1]["loai"] == "loai":
                i += 1
                loai_sau.append(chung[i])
            khe = max(0.45, sum(_kich_thuoc(_chu_hop(x))[1] for x in loai_sau) + 0.18 * (len(loai_sau) + 1))
            yy = y - (khe - sum(_kich_thuoc(_chu_hop(x))[1] for x in loai_sau) - 0.18 * (len(loai_sau) - 1)) / 2
            for x in loai_sau:
                hx = _kich_thuoc(_chu_hop(x))[1]
                xl = xc + w_chinh / 2 + 0.5 + w_loai / 2
                hop.append({"x": xl, "y": yy, "w": w_loai, "h": hx, "chu": _chu_hop(x), "trai": True})
                mui.append(((xc, yy - hx / 2), (xl - w_loai / 2, yy - hx / 2)))
                yy -= hx + 0.18
            y -= khe
        i += 1
    y_nhanh = y - 0.35
    for j, t in enumerate(nhanh):
        xj = rong * (j + 0.5) / len(nhanh)
        ten_nhanh.append({"x": xj, "y": y_nhanh + 0.25, "chu": t, "mau": j})
        yy, day = y_nhanh, day_truoc
        for n_, b in enumerate(k["nhanh"][t]):
            w, h = w_nhanh, _kich_thuoc(_chu_hop(b))[1]
            if day is not None:
                mui.append(((xc if n_ == 0 else xj, day), (xj, yy)))
            hop.append({"x": xj, "y": yy, "w": w, "h": h, "chu": _chu_hop(b), "trai": b["loai"] == "loai"})
            day = yy - h
            yy = day - 0.35
        y = min(y, yy)
    return {"hop": hop, "mui": mui, "ten_nhanh": ten_nhanh, "rong": rong, "cao": -y + 0.6}


def ve_so_do_luong(dong, dich: Path, chuan: str = "", ngon_ngu: str = "vi", bo_kiem_so: bool = False) -> Dict:
    import matplotlib.patches as mp  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    k = kiem_so_hoc_luong(dong)
    if k["loi"] and not bo_kiem_so:
        raise LoiBieuDo("số học sơ đồ luồng không khớp — " + " | ".join(k["loi"]))
    plt = BC.plt_chuan()
    dt = dan_trang_luong(k)
    fig = plt.figure(figsize=(dt["rong"], dt["cao"]))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, dt["rong"])
    ax.set_ylim(-dt["cao"] + 0.3, 0.3)
    ax.axis("off")
    for h in dt["hop"]:
        ax.add_patch(mp.Rectangle((h["x"] - h["w"] / 2, h["y"] - h["h"]), h["w"], h["h"], fc="white", ec="#222222",
                                  lw=0.8))
        ax.text(h["x"] - h["w"] / 2 + 0.12 if h["trai"] else h["x"], h["y"] - h["h"] / 2, h["chu"],
                ha="left" if h["trai"] else "center", va="center", fontsize=7.6)
    for (x0, y0), (x1, y1) in dt["mui"]:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops={"arrowstyle": "-|>", "lw": 0.8, "color": "#222222",
                                                                  "shrinkA": 0, "shrinkB": 0})
    for t in dt["ten_nhanh"]:
        ax.text(t["x"], t["y"], t["chu"], ha="center", fontsize=8.5, weight="bold", color=MAU[t["mau"] % len(MAU)])
    if chuan:
        ax.text(0.1, 0.15, chuan, fontsize=8, style="italic", color="#555555")
    kq = {"loai": "so_do_luong", "chuan": chuan, "nhanh": k["nhanh"], "loi_so_hoc": k["loi"],
          "ghi_chu": "Số học từng bước đã kiểm (n sau = n trước − loại trừ). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 2. NGUY CƠ SAI LỆCH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
MUC_ROB = [  # (mã, nhãn vi, nhãn en, màu, ký hiệu, các cách viết được nhận)
    ("thap", "Thấp", "Low", "#2e7d32", "+", {"thấp", "thap", "low", "+", "l"}),
    ("lo_ngai", "Một số lo ngại", "Some concerns", "#e6b800", "?",
     {"một số lo ngại", "mot so lo ngai", "some concerns", "?", "unclear", "không rõ", "moderate", "trung bình",
      "có lo ngại", "co lo ngai", "lo ngại", "lo ngai"}),  # «Có lo ngại»: nhãn từ điển G5 kịch bản tổng quan
    ("cao", "Cao", "High", "#c62828", "−", {"cao", "high", "-", "−", "h"}),
    ("nghiem_trong", "Nghiêm trọng", "Serious", "#8e0000", "!", {"nghiêm trọng", "serious"}),
    ("rat_nghiem_trong", "Rất nghiêm trọng", "Critical", "#4a0000", "×", {"rất nghiêm trọng", "critical"}),
    ("khong_tt", "Không thông tin", "No information", "#9e9e9e", "·", {"không thông tin", "no information", "ni"}),
]


def muc_rob(v: str) -> str:
    s = (v or "").strip().lower()
    for ma, *_, nhan in MUC_ROB:
        if s in nhan:
            return ma
    raise LoiBieuDo(f"mức nguy cơ sai lệch không nhận ra: «{v}»")


def ve_rob(dong, dich: Path, cong_cu: str = "", ngon_ngu: str = "vi") -> Dict[str, Any]:
    import matplotlib.patches as mp  # noqa: PLC0415

    BC.kiem_ngon_ngu(ngon_ngu)
    if "nghien_cuu" not in dong[0]:
        raise LoiBieuDo("bảng RoB cần cột nghien_cuu")
    mien = [c for c in dong[0] if c not in ("nghien_cuu", "trong_so")]
    if not mien:
        raise LoiBieuDo("bảng RoB không có cột miền")
    M = [[muc_rob(r[c]) for c in mien] for r in dong]
    w = [so_hoc(r["trong_so"], "trong_so") if "trong_so" in r and r["trong_so"] not in THIEU else 1.0 for r in dong]
    info = {ma: (vi_, en, mau, kh) for ma, vi_, en, mau, kh, _ in MUC_ROB}
    vi = ngon_ngu == "vi"
    plt = BC.plt_chuan()
    n = len(dong)
    fig = plt.figure(figsize=(max(6.0, 0.62 * len(mien) + 3.4), 0.34 * n + 0.42 * len(mien) + 2.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[0.34 * n + 0.8, 0.42 * len(mien) + 0.8], hspace=0.35)
    ax, axt = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])
    for i, r in enumerate(dong):
        for j, ma in enumerate(M[i]):
            ax.add_patch(mp.Circle((j, n - 1 - i), 0.33, color=info[ma][2]))
            ax.text(j, n - 1 - i, info[ma][3], ha="center", va="center", color="white", fontsize=9, weight="bold")
    ax.set_xlim(-0.6, len(mien) - 0.4)
    ax.set_ylim(-0.6, n - 0.4)
    ax.set_aspect("equal")
    ax.set_xticks(range(len(mien)))
    ax.set_xticklabels(mien, fontsize=8)
    ax.xaxis.tick_top()
    ax.set_yticks(range(n))
    ax.set_yticklabels([r["nghien_cuu"] for r in dong][::-1], fontsize=8)
    ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    if cong_cu:
        ax.set_title(cong_cu, fontsize=9, loc="left", pad=22)
    tom = {}
    co_mat = [ma for ma, *_ in MUC_ROB if any(ma in hang for hang in M)]
    for j, c in enumerate(mien):
        tong = sum(w)
        tom[c] = {ma: 100 * sum(wi for wi, hang in zip(w, M) if hang[j] == ma) / tong for ma in co_mat}
        trai = 0.0
        for ma in co_mat:
            axt.barh(len(mien) - 1 - j, tom[c][ma], left=trai, color=info[ma][2], height=0.7, edgecolor="white", lw=0.4)
            trai += tom[c][ma]
    axt.set_yticks(range(len(mien)))
    axt.set_yticklabels(mien[::-1], fontsize=8)
    axt.set_xlim(0, 100)
    axt.set_xlabel(("% nghiên cứu" if vi else "% of studies") + (" (có trọng số)" if "trong_so" in dong[0] and vi
                                                                  else " (weighted)" if "trong_so" in dong[0] else ""))
    axt.tick_params(axis="y", length=0)
    axt.legend(handles=[mp.Patch(color=info[ma][2], label=info[ma][0 if vi else 1]) for ma in co_mat],
               loc="upper center", bbox_to_anchor=(0.5, -0.32), ncol=min(len(co_mat), 4), frameon=False, fontsize=7.6)
    kq = {"loai": "rob", "cong_cu": cong_cu, "mien": mien, "danh_gia": {r["nghien_cuu"]: dict(zip(mien, hang))
                                                                         for r, hang in zip(dong, M)},
          "tom_tat_pt": tom, "ghi_chu": "Vẽ đúng đánh giá đã chấm (không tự chấm). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 3. KINH TẾ Y TẾ — CE plane · CEAC · tornado
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def doc_psa(dong) -> Dict[str, List[float]]:
    for c in ("d_chi_phi", "d_hieu_qua"):
        if c not in dong[0]:
            raise LoiBieuDo(f"tệp PSA thiếu cột «{c}»")
    dc = [so_hoc(r["d_chi_phi"], "d_chi_phi") for r in dong if r["d_chi_phi"] not in THIEU]
    de = [so_hoc(r["d_hieu_qua"], "d_hieu_qua") for r in dong if r["d_hieu_qua"] not in THIEU]
    if len(dc) != len(de) or len(dc) < 10:
        raise LoiBieuDo("PSA cần ≥ 10 lần lặp đủ cả ΔC và ΔE")
    return {"dc": dc, "de": de}


def ceac(dc: Sequence[float], de: Sequence[float], lam: Sequence[float]) -> List[float]:
    """P(λ·ΔE − ΔC > 0) với từng λ — tỷ lệ lần lặp có lợi ích ròng tiền tệ dương."""
    n = len(dc)
    return [sum(1 for c, e in zip(dc, de) if l_ * e - c > 0) / n for l_ in lam]


def goc_phan_tu(dc: Sequence[float], de: Sequence[float]) -> Dict[str, float]:
    n = len(dc)
    return {"DB_dat_hon_hieu_qua_hon": 100 * sum(1 for c, e in zip(dc, de) if e > 0 and c > 0) / n,
            "TN_re_hon_hieu_qua_hon_troi": 100 * sum(1 for c, e in zip(dc, de) if e > 0 and c <= 0) / n,
            "TB_dat_hon_kem_hon_bi_troi": 100 * sum(1 for c, e in zip(dc, de) if e <= 0 and c > 0) / n,
            "TN_re_hon_kem_hon": 100 * sum(1 for c, e in zip(dc, de) if e <= 0 and c <= 0) / n}


def ve_ce_plane(dc, de, dich: Path, lam: float, don_vi_c: str = "", don_vi_e: str = "",
                ngon_ngu: str = "vi") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    plt = BC.plt_chuan()
    vi = ngon_ngu == "vi"
    mc, me = sum(dc) / len(dc), sum(de) / len(de)
    icer = mc / me if me != 0 else float("nan")
    fig, ax = plt.subplots(figsize=(5.8, 4.8))
    ax.scatter(de, dc, s=5, color="#1f4e79", alpha=0.25, lw=0)
    ax.scatter([me], [mc], s=50, color="#a23b2a", edgecolor="black", zorder=4,
               label=f"{'Trung bình' if vi else 'Mean'}: ICER = {so(icer, 0, ngon_ngu)}")
    xl = max(abs(min(de)), abs(max(de))) * 1.1
    yl = max(abs(min(dc)), abs(max(dc)), abs(lam * xl)) * 1.05
    ax.plot([-xl, xl], [-lam * xl, lam * xl], color="#2e7d32", lw=1.0, ls="--",
            label=f"λ = {so(lam, 0, ngon_ngu)}" + (f" {don_vi_c}/{don_vi_e}" if don_vi_c and don_vi_e else ""))
    ax.axhline(0, color="#555555", lw=0.7)
    ax.axvline(0, color="#555555", lw=0.7)
    ax.set_xlim(-xl, xl)
    ax.set_ylim(-yl, yl)
    gp = goc_phan_tu(dc, de)
    for (x, y, k) in ((0.97, 0.97, "DB_dat_hon_hieu_qua_hon"), (0.97, 0.03, "TN_re_hon_hieu_qua_hon_troi"),
                      (0.03, 0.97, "TB_dat_hon_kem_hon_bi_troi"), (0.03, 0.03, "TN_re_hon_kem_hon")):
        ax.text(x, y, so(gp[k], 1, ngon_ngu) + "%", transform=ax.transAxes, ha="right" if x > 0.5 else "left",
                va="top" if y > 0.5 else "bottom", fontsize=8, color="#555555")
    p_ce = ceac(dc, de, [lam])[0]
    ax.set_xlabel(("Hiệu quả tăng thêm ΔE" if vi else "Incremental effect ΔE") + (f" ({don_vi_e})" if don_vi_e else ""))
    ax.set_ylabel(("Chi phí tăng thêm ΔC" if vi else "Incremental cost ΔC") + (f" ({don_vi_c})" if don_vi_c else ""))
    BC.dinh_dang_truc(ax, ngon_ngu, "xy")
    ax.legend(frameon=False, fontsize=7.8, loc="upper left", bbox_to_anchor=(0.0, 0.9))
    ax.set_title((f"Có hiệu quả chi phí tại λ: {so(100 * p_ce, 1, ngon_ngu)}% lần lặp" if vi else
                  f"Cost-effective at λ: {so(100 * p_ce, 1, ngon_ngu)}% of iterations"), fontsize=8.5)
    kq = {"loai": "ce_plane", "lap": len(dc), "tb_d_chi_phi": mc, "tb_d_hieu_qua": me, "icer": icer, "lambda": lam,
          "goc_phan_tu_pt": gp, "p_hieu_qua_chi_phi": p_ce,
          "ghi_chu": "ICER = TB(ΔC)/TB(ΔE). Ngưỡng λ do bác sĩ/nhà quản lý chọn theo bối cảnh. Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_ceac(dc, de, dich: Path, lam_max: float, don_vi: str = "", ngon_ngu: str = "vi", diem: int = 101) -> Dict:
    BC.kiem_ngon_ngu(ngon_ngu)
    if lam_max <= 0:
        raise LoiBieuDo("λ tối đa phải > 0")
    plt = BC.plt_chuan()
    lam = [lam_max * i / (diem - 1) for i in range(diem)]
    p = ceac(dc, de, lam)
    fig, ax = plt.subplots(figsize=(5.8, 3.9))
    ax.plot(lam, p, color="#1f4e79", lw=1.6, label="Can thiệp" if ngon_ngu == "vi" else "Intervention")
    ax.plot(lam, [1 - v for v in p], color="#a23b2a", lw=1.2, ls="--",
            label="So sánh" if ngon_ngu == "vi" else "Comparator")
    ax.set_ylim(0, 1.02)
    ax.set_xlim(0, lam_max)
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    BC.dinh_dang_truc(ax, ngon_ngu, "y", nd=1)
    ax.set_xlabel(("Ngưỡng sẵn lòng chi trả λ" if ngon_ngu == "vi" else "Willingness to pay λ") +
                  (f" ({don_vi})" if don_vi else ""))
    ax.set_ylabel("Xác suất có hiệu quả chi phí" if ngon_ngu == "vi" else "Probability cost-effective")
    ax.legend(frameon=False, fontsize=8)
    kq = {"loai": "ceac", "lambda": lam, "xac_suat": p, "ghi_chu": "P(λ·ΔE − ΔC > 0). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_tornado(dong, dich: Path, co_so: float, ten_kq: str = "", ngon_ngu: str = "vi") -> Dict[str, Any]:
    BC.kiem_ngon_ngu(ngon_ngu)
    for c in ("tham_so", "ket_qua_thap", "ket_qua_cao"):
        if c not in dong[0]:
            raise LoiBieuDo(f"bảng tornado thiếu cột «{c}»")
    hang = [{"tham_so": r["tham_so"], "thap": so_hoc(r["ket_qua_thap"], "ket_qua_thap"),
             "cao": so_hoc(r["ket_qua_cao"], "ket_qua_cao"), "gt_thap": r.get("gia_tri_thap", ""),
             "gt_cao": r.get("gia_tri_cao", "")} for r in dong]
    hang.sort(key=lambda h: abs(h["cao"] - h["thap"]))
    plt = BC.plt_chuan()
    fig, ax = plt.subplots(figsize=(6.4, 0.42 * len(hang) + 1.4))
    for i, h in enumerate(hang):
        ax.barh(i, h["thap"] - co_so, left=co_so, color="#1f4e79", height=0.6)
        ax.barh(i, h["cao"] - co_so, left=co_so, color="#a23b2a", height=0.6)
        for gt, x in ((h["gt_thap"], h["thap"]), (h["gt_cao"], h["cao"])):
            if gt:
                ax.text(x, i, f" {gt} ", va="center", ha="left" if x >= co_so else "right", fontsize=7.2)
    ax.axvline(co_so, color="#222222", lw=0.9)
    ax.set_yticks(range(len(hang)))
    ax.set_yticklabels([h["tham_so"] for h in hang])
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    vi = ngon_ngu == "vi"
    ax.set_xlabel((ten_kq or ("Kết quả" if vi else "Outcome")) + (f" ({'cơ sở' if vi else 'base'} = "
                                                                 f"{so(co_so, 0, ngon_ngu)})"))
    import matplotlib.patches as mp  # noqa: PLC0415

    ax.legend(handles=[mp.Patch(color="#1f4e79", label="Giá trị thấp của tham số" if vi else "Low parameter value"),
                       mp.Patch(color="#a23b2a", label="Giá trị cao của tham số" if vi else "High parameter value")],
              frameon=False, fontsize=7.6, loc="lower right")
    kq = {"loai": "tornado", "co_so": co_so, "tham_so": hang[::-1],
          "ghi_chu": "Xếp theo độ rộng (tham số ảnh hưởng nhất ở trên). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


def ve_chu_de(dong, cot: str, dich: Path, ngon_ngu: str = "vi", nhan: str = "") -> Dict[str, Any]:
    """Tần suất các CHỦ ĐỀ/MÃ đã gán trong nghiên cứu định tính (21/11/2026): mỗi dòng là một đơn vị phân tích (bản gỡ
    băng, đoạn trích); thanh ngang = % đơn vị mang chủ đề, KTC 95% Wilson — cùng phép đếm `phan_tich_thiet_ke_dac_thu.
    dinh_tinh` của G6 (giá trị rỗng bị bỏ). Chỉ là MÔ TẢ tần suất: không thay phân tích chủ đề của nhóm nghiên cứu."""
    BC.kiem_ngon_ngu(ngon_ngu)
    if not dong or cot not in dong[0]:
        raise LoiBieuDo(f"bảng chủ đề thiếu cột «{cot}»")
    dem: Dict[str, int] = {}
    for r in dong:
        v = str(r.get(cot) or "").strip()
        if v:  # đúng phép đếm của G6 (chỉ bỏ ô rỗng) — số trên hình phải trùng số G6 đã ghi
            dem[v] = dem.get(v, 0) + 1
    n = sum(dem.values())
    if not n:
        raise LoiBieuDo(f"cột «{cot}» không có chủ đề nào được gán")
    hang = []
    for k, v in sorted(dem.items(), key=lambda x: (-x[1], x[0])):
        lo, hi = ktc_ty_le(v, n, "wilson")
        hang.append({"chu_de": k, "n": v, "ty_le": v / n, "duoi": max(0.0, lo), "tren": min(1.0, hi)})
    vi = ngon_ngu == "vi"
    plt = BC.plt_chuan()
    fig, ax = plt.subplots(figsize=(6.6, 0.42 * len(hang) + 1.5))
    y = list(range(len(hang)))[::-1]
    u = [100 * h["ty_le"] for h in hang]
    ax.barh(y, u, height=0.6, color="#1f4e79", alpha=0.85)
    ax.errorbar(u, y, xerr=[[a - 100 * h["duoi"] for a, h in zip(u, hang)],
                            [100 * h["tren"] - a for a, h in zip(u, hang)]], fmt="none", ecolor="#111111",
                capsize=3, lw=0.8)
    for yy, h in zip(y, hang):
        ax.text(100 * h["tren"] + 1, yy, f"{so(100 * h['ty_le'], 1, ngon_ngu)}% ({h['n']}/{n})", va="center",
                fontsize=7.4)
    ax.set_yticks(y)
    ax.set_yticklabels([h["chu_de"] for h in hang], fontsize=8)
    ax.set_xlim(0, 100)
    ax.set_xlabel(("% đơn vị phân tích mang chủ đề (KTC 95% Wilson)" if vi else
                   "% of analytic units with the theme (95% Wilson CI)"))
    if nhan:
        ax.set_title(nhan, fontsize=9)
    BC.dinh_dang_truc(ax, ngon_ngu, "x")
    ax.xaxis.grid(True, color="#e5e5e5", lw=0.6)
    ax.set_axisbelow(True)
    kq = {"loai": "chu_de", "cot": cot, "n": n, "so_chu_de": len(hang), "chu_de": hang,
          "ghi_chu": "Tần suất mô tả các mã đã gán — không thay phân tích chủ đề (COREQ/SRQR). Cần bác sĩ kiểm chứng."}
    BC.luu(fig, dich, so_lieu=kq)
    return kq


# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
# 4. DÒNG LỆNH
# ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("lenh", choices=("so-do-luong", "rob", "ce-plane", "ceac", "tornado", "chu-de"))
    ap.add_argument("--du-lieu", required=True, type=Path)
    ap.add_argument("--ra", required=True, type=Path)
    ap.add_argument("--chuan", default="")
    ap.add_argument("--bo-kiem-so", action="store_true", help="vẽ dù số học lệch (KHÔNG dùng cho bản nộp)")
    ap.add_argument("--cong-cu", default="")
    ap.add_argument("--nguong-chi-tra", type=float)
    ap.add_argument("--lambda-toi-da", type=float)
    ap.add_argument("--don-vi-chi-phi", default="")
    ap.add_argument("--don-vi-hieu-qua", default="")
    ap.add_argument("--co-so", type=float)
    ap.add_argument("--ten-ket-qua", default="")
    ap.add_argument("--cot", default="", help="chu-de: cột chứa chủ đề/mã đã gán")
    ap.add_argument("--ngon-ngu", default="vi", choices=BC.NGON_NGU)
    try:
        a = ap.parse_args(argv)
    except SystemExit as exc:
        return 3 if exc.code else 0
    try:
        dong = doc_csv(a.du_lieu)
        if a.lenh == "so-do-luong":
            kq = ve_so_do_luong(dong, a.ra, a.chuan, a.ngon_ngu, a.bo_kiem_so)
            print(f"✅ sơ đồ luồng: {sum(len(v) for v in kq['nhanh'].values())} hộp" +
                  (f" · ⚠ lệch số học: {kq['loi_so_hoc']}" if kq["loi_so_hoc"] else " · số học khớp"))
        elif a.lenh == "chu-de":
            if not a.cot:
                print("❌ chu-de cần --cot")
                return 3
            kq = ve_chu_de(dong, a.cot, a.ra, a.ngon_ngu)
            print(f"✅ chủ đề: {kq['so_chu_de']} chủ đề trên {kq['n']} đơn vị phân tích")
        elif a.lenh == "rob":
            kq = ve_rob(dong, a.ra, a.cong_cu, a.ngon_ngu)
            print(f"✅ RoB: {len(kq['danh_gia'])} nghiên cứu × {len(kq['mien'])} miền")
        elif a.lenh in ("ce-plane", "ceac"):
            psa = doc_psa(dong)
            if a.lenh == "ce-plane":
                if a.nguong_chi_tra is None:
                    print("❌ ce-plane cần --nguong-chi-tra")
                    return 3
                kq = ve_ce_plane(psa["dc"], psa["de"], a.ra, a.nguong_chi_tra, a.don_vi_chi_phi, a.don_vi_hieu_qua,
                                 a.ngon_ngu)
                print(f"✅ CE plane: ICER = {so(kq['icer'], 0)} · có hiệu quả chi phí "
                      f"{so(100 * kq['p_hieu_qua_chi_phi'], 1)}%")
            else:
                if a.lambda_toi_da is None:
                    print("❌ ceac cần --lambda-toi-da")
                    return 3
                ve_ceac(psa["dc"], psa["de"], a.ra, a.lambda_toi_da, a.don_vi_chi_phi, a.ngon_ngu)
                print("✅ CEAC")
        else:
            if a.co_so is None:
                print("❌ tornado cần --co-so")
                return 3
            ve_tornado(dong, a.ra, a.co_so, a.ten_ket_qua, a.ngon_ngu)
            print("✅ tornado")
        print(f"   → {a.ra.with_suffix('.png')}")
    except LoiBieuDo as exc:
        print(f"❌ {exc}")
        return 2
    print("Cần bác sĩ kiểm chứng.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
