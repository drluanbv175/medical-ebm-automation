#!/usr/bin/env python3
"""
kiem_tin_cay_thang_do.py — Chỉ số độ tin cậy của thang đo/bộ câu hỏi trên dữ liệu PILOT.

THÊM 28/09/2026 (đề xuất R1 của đợt «Tiếp tục đề xuất nâng cấp hệ thống nghiên cứu»).
Đề tài thật C1a (khảo sát hài lòng, phiếu 75 mục) bắt buộc chạy phỏng vấn nhận thức + pilot
TRƯỚC mẫu chính (đề cương mục 4.5.1), nhưng repo chưa có công cụ nào tính các chỉ số cần báo
cáo từ dữ liệu pilot. Công cụ này chạy NGOẠI TUYẾN, tất định, chỉ in số TỔNG HỢP.

Tính cho TỪNG thang/tiểu thang (một nhóm cột mục):
  - n dùng được (loại theo hàng — listwise) và số hàng bị loại vì thiếu.
  - Tỷ lệ thiếu theo từng mục (sau khi đổi các mã thiếu khai qua --ma-thieu thành rỗng).
  - Cronbach α + khoảng tin cậy 95% theo phương pháp Feldt (phân phối F, bậc tự do
    n−1 và (n−1)(k−1)).
  - α khi bỏ từng mục + tương quan mục–tổng ĐÃ HIỆU CHỈNH (mục so với tổng các mục còn lại).
  - Tỷ lệ sàn/trần của ĐIỂM TỔNG (chỉ khi khai --min và --max; KHÔNG tự đoán thang).
  - ICC test–retest trên điểm tổng (tuỳ chọn: --lap-lai + --khoa-id): ICC(2,1) — mô hình hai
    chiều ngẫu nhiên, đồng thuận tuyệt đối, một lần đo — kèm KTC 95% theo Shrout & Fleiss.

Ngưỡng diễn giải — CHỈ dùng nguồn đã tra PubMed (28/09/2026):
  - ICC: Koo & Li 2016 (PMID 27330520, doi:10.1016/j.jcm.2016.02.012): <0,5 kém · 0,5–0,75 vừa ·
    0,75–0,9 tốt · >0,9 rất tốt, xếp theo KTC 95% (nêu trong tóm tắt bài).
  - α 0,70–0,95 và sàn/trần >15% người trả lời: Terwee 2007 (PMID 17161752,
    doi:10.1016/j.jclinepi.2006.03.012). Con số KHÔNG nằm trong tóm tắt ⇒ in kèm nhãn
    [CẦN ĐỐI CHIẾU NGUYÊN VĂN] — bác sĩ đối chiếu bảng tiêu chí trong bài trước khi trích.
  - Tương quan mục–tổng: KHÔNG đặt ngưỡng (chưa có nguồn đã xác minh) — chỉ xếp tăng dần để
    hội đồng chuyên gia xem mục yếu nhất trước.
  Phương pháp tính ICC(2,1) và KTC: Shrout & Fleiss 1979 (PMID 18839484,
  doi:10.1037//0033-2909.86.2.420).

Ranh giới: công cụ KHÔNG kết luận thang đo «hợp lệ» — độ tin cậy nội tại chỉ là MỘT thuộc
tính đo lường (COSMIN còn đòi giá trị nội dung, cấu trúc…). Không in giá trị từng người,
không in cột mã định danh. Cần bác sĩ kiểm chứng.

Cách dùng:
    python tools/kiem_tin_cay_thang_do.py pilot.csv --muc C1 C2 C3 C4 --min 1 --max 5
    python tools/kiem_tin_cay_thang_do.py pilot.xlsx --nhom "Tiep_don:A1,A2,A3" \\
        --nhom "Bac_si:B1,B2,B3,B4" --min 1 --max 5 --ma-thieu 7 9
    python tools/kiem_tin_cay_thang_do.py lan1.csv --muc C1 C2 C3 --lap-lai lan2.csv \\
        --khoa-id ma_phieu --min 1 --max 5 --json
Mã thoát: 0 tính xong · 2 lỗi đầu vào (tệp/cột/thang không hợp lệ).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

# Windows: stdout mặc định cp1252 giết print() tiếng Việt — ép UTF-8 (chốt BH55/R4)
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402

NGUON_TERWEE = "Terwee 2007, PMID 17161752 [CẦN ĐỐI CHIẾU NGUYÊN VĂN]"
NGUON_KOO_LI = "Koo & Li 2016, PMID 27330520"
NGUON_SHROUT_FLEISS = "Shrout & Fleiss 1979, PMID 18839484"
ALPHA_THAP, ALPHA_CAO = 0.70, 0.95
NGUONG_SAN_TRAN = 0.15


class LoiDauVao(ValueError):
    """Đầu vào không dùng được (tệp, cột, thang) — CLI trả mã 2."""


# ---------------------------------------------------------------- đọc dữ liệu
def doc_bang(duong_dan: str | Path) -> pd.DataFrame:
    p = Path(duong_dan)
    if not p.is_file():
        raise LoiDauVao(f"không thấy tệp dữ liệu: {p}")
    duoi = p.suffix.lower()
    if duoi in (".csv", ".txt"):
        return pd.read_csv(p, encoding="utf-8-sig")
    if duoi in (".xlsx", ".xlsm"):
        return pd.read_excel(p)
    if duoi == ".sav":
        try:
            return pd.read_spss(p)
        except ImportError as e:  # pyreadstat chưa cài
            raise LoiDauVao(
                "đọc .sav cần gói pyreadstat (chưa cài) — xuất sang .csv từ SPSS rồi chạy lại"
            ) from e
    raise LoiDauVao(f"định dạng chưa hỗ trợ: {duoi} (dùng .csv, .xlsx hoặc .sav)")


def chuan_hoa_muc(df: pd.DataFrame, cot: list[str], ma_thieu: list[float]) -> pd.DataFrame:
    """Lấy các cột mục, đổi mã thiếu thành NaN, ép số. Cột không phải số ⇒ lỗi rõ."""
    thieu_cot = [c for c in cot if c not in df.columns]
    if thieu_cot:
        raise LoiDauVao(f"không có cột: {', '.join(thieu_cot)}")
    sub = df[cot].copy()
    for c in cot:
        so = pd.to_numeric(sub[c], errors="coerce")
        chu_la = sub[c].notna() & so.isna()
        if chu_la.any():
            raise LoiDauVao(f"cột {c} có giá trị không phải số — không phải cột mục thang đo?")
        sub[c] = so
    if ma_thieu:
        sub = sub.mask(sub.isin(ma_thieu))
    return sub


# ---------------------------------------------------------------- Cronbach α
def cronbach_alpha(x: np.ndarray) -> float:
    """α = k/(k−1)·(1 − Σ var(mục)/var(tổng)); x: n×k, không thiếu. NaN nếu tổng không biến thiên."""
    n, k = x.shape
    if k < 2 or n < 2:
        return float("nan")
    var_muc = x.var(axis=0, ddof=1)
    var_tong = x.sum(axis=1).var(ddof=1)
    if var_tong <= 0:
        return float("nan")
    return float(k / (k - 1) * (1 - var_muc.sum() / var_tong))


def ktc_feldt(alpha: float, n: int, k: int, muc: float = 0.95) -> tuple[float, float]:
    """KTC của α theo Feldt: (1−α)/(1−α̂) ~ F(n−1, (n−1)(k−1))."""
    if not math.isfinite(alpha) or n < 2 or k < 2:
        return float("nan"), float("nan")
    df1, df2 = n - 1, (n - 1) * (k - 1)
    g = (1 - muc) / 2
    duoi = 1 - (1 - alpha) * stats.f.ppf(1 - g, df1, df2)
    tren = 1 - (1 - alpha) * stats.f.ppf(g, df1, df2)
    return float(duoi), float(tren)


def tuong_quan_muc_tong(x: np.ndarray) -> list[float]:
    """r Pearson giữa mỗi mục và tổng các mục CÒN LẠI (đã hiệu chỉnh)."""
    kq = []
    for j in range(x.shape[1]):
        con_lai = np.delete(x, j, axis=1).sum(axis=1)
        a, b = x[:, j], con_lai
        if a.std(ddof=1) == 0 or b.std(ddof=1) == 0:
            kq.append(float("nan"))
        else:
            kq.append(float(np.corrcoef(a, b)[0, 1]))
    return kq


# ---------------------------------------------------------------- ICC(2,1)
def icc_2_1(y: np.ndarray, muc: float = 0.95) -> dict:
    """ICC(2,1) đồng thuận tuyệt đối + KTC (Shrout & Fleiss 1979). y: n đối tượng × k lần đo."""
    n, k = y.shape
    if n < 2 or k < 2:
        raise LoiDauVao("ICC cần ít nhất 2 đối tượng và 2 lần đo")
    tb = y.mean()
    ss_hang = k * ((y.mean(axis=1) - tb) ** 2).sum()
    ss_cot = n * ((y.mean(axis=0) - tb) ** 2).sum()
    ss_tong = ((y - tb) ** 2).sum()
    ss_loi = ss_tong - ss_hang - ss_cot
    msr = ss_hang / (n - 1)
    msc = ss_cot / (k - 1)
    mse = ss_loi / ((n - 1) * (k - 1))
    mau = msr + (k - 1) * mse + k * (msc - mse) / n
    if mau <= 0:
        return {"icc": float("nan"), "ktc95": [float("nan"), float("nan")], "n": n, "k": k}
    icc = (msr - mse) / mau
    if mse <= 1e-12:  # hai lần đo trùng khớp hoàn toàn: ICC xác định, KTC không định nghĩa
        return {"icc": float(icc), "ktc95": [float("nan"), float("nan")], "n": n, "k": k}
    g = 1 - (1 - muc) / 2
    fj = msc / mse
    a = n * (1 + (k - 1) * icc) - k * icc
    v = ((k - 1) * (n - 1) * (k * icc * fj + a) ** 2) / (
        (n - 1) * k**2 * icc**2 * fj**2 + a**2
    )
    fl = stats.f.ppf(g, n - 1, v)
    fu = stats.f.ppf(g, v, n - 1)
    duoi = n * (msr - fl * mse) / (fl * (k * msc + (k * n - k - n) * mse) + n * msr)
    tren = n * (fu * msr - mse) / (k * msc + (k * n - k - n) * mse + n * fu * msr)
    return {"icc": float(icc), "ktc95": [float(duoi), float(tren)], "n": n, "k": k}


def xep_loai_koo_li(gia_tri: float) -> str:
    if not math.isfinite(gia_tri):
        return "không tính được"
    if gia_tri < 0.5:
        return "kém"
    if gia_tri < 0.75:
        return "vừa"
    if gia_tri <= 0.9:
        return "tốt"
    return "rất tốt"


# ---------------------------------------------------------------- phân tích một thang
def phan_tich_thang(
    ten: str, sub: pd.DataFrame, min_thang: float | None, max_thang: float | None
) -> dict:
    cot = list(sub.columns)
    k = len(cot)
    if k < 2:
        raise LoiDauVao(f"thang «{ten}» cần ít nhất 2 mục (đang có {k})")
    ty_le_thieu = {c: float(sub[c].isna().mean()) for c in cot}
    du = sub.dropna()
    n = len(du)
    kq: dict = {
        "ten": ten,
        "so_muc": k,
        "n_tong": int(len(sub)),
        "n_dung": int(n),
        "n_loai_vi_thieu": int(len(sub) - n),
        "ty_le_thieu_theo_muc": ty_le_thieu,
        "canh_bao": [],
    }
    x = du.to_numpy(dtype=float)
    if min_thang is not None and max_thang is not None and n:
        ngoai = ((x < min_thang) | (x > max_thang)).any(axis=0)
        if ngoai.any():
            raise LoiDauVao(
                f"thang «{ten}»: có giá trị ngoài [{min_thang}, {max_thang}] ở "
                + ", ".join(c for c, o in zip(cot, ngoai) if o)
                + " — mã thiếu chưa khai qua --ma-thieu?"
            )
    hang_so = [c for c, s in zip(cot, x.std(axis=0, ddof=1) if n > 1 else []) if s == 0]
    if hang_so:
        kq["canh_bao"].append(f"mục không biến thiên (mọi người trả lời giống nhau): {', '.join(hang_so)}")
    alpha = cronbach_alpha(x)
    duoi, tren = ktc_feldt(alpha, n, k)
    kq["alpha"] = alpha
    kq["alpha_ktc95"] = [duoi, tren]
    if math.isfinite(alpha):
        if alpha < ALPHA_THAP:
            kq["canh_bao"].append(f"α = {alpha:.3f} < {ALPHA_THAP} ({NGUON_TERWEE})")
        elif alpha > ALPHA_CAO:
            kq["canh_bao"].append(f"α = {alpha:.3f} > {ALPHA_CAO} — có thể thừa mục ({NGUON_TERWEE})")
    r_mt = tuong_quan_muc_tong(x) if n > 2 else [float("nan")] * k
    alpha_bo = [cronbach_alpha(np.delete(x, j, axis=1)) if k > 2 else float("nan") for j in range(k)]
    kq["muc"] = sorted(
        (
            {"muc": c, "r_muc_tong_hieu_chinh": r, "alpha_neu_bo_muc": a, "ty_le_thieu": ty_le_thieu[c]}
            for c, r, a in zip(cot, r_mt, alpha_bo)
        ),
        key=lambda d: (math.isnan(d["r_muc_tong_hieu_chinh"]), d["r_muc_tong_hieu_chinh"]),
    )
    if min_thang is None or max_thang is None:
        kq["san_tran"] = None
    elif n == 0:
        kq["san_tran"] = None
    else:
        tong = x.sum(axis=1)
        san, tran = float((tong == k * min_thang).mean()), float((tong == k * max_thang).mean())
        kq["san_tran"] = {
            "ty_le_san": san, "ty_le_tran": tran,
            "diem_tong_min": k * min_thang, "diem_tong_max": k * max_thang,
        }
        for nhan, gt in (("sàn", san), ("trần", tran)):
            if gt > NGUONG_SAN_TRAN:
                kq["canh_bao"].append(f"hiệu ứng {nhan}: {gt:.0%} người đạt điểm tổng cực trị > 15% ({NGUON_TERWEE})")
    return kq


def phan_tich_lap_lai(
    df1: pd.DataFrame, df2: pd.DataFrame, cot: list[str], khoa: str, ma_thieu: list[float]
) -> dict:
    for ten, d in (("lần 1", df1), ("lần 2", df2)):
        if khoa not in d.columns:
            raise LoiDauVao(f"tệp {ten} không có cột mã ghép cặp «{khoa}»")
        if d[khoa].duplicated().any():
            raise LoiDauVao(f"tệp {ten}: mã ghép cặp «{khoa}» bị trùng — không ghép cặp được")
    t1 = chuan_hoa_muc(df1, cot, ma_thieu).sum(axis=1, min_count=len(cot))
    t2 = chuan_hoa_muc(df2, cot, ma_thieu).sum(axis=1, min_count=len(cot))
    a = pd.DataFrame({"khoa": df1[khoa].to_numpy(), "t1": t1.to_numpy()})
    b = pd.DataFrame({"khoa": df2[khoa].to_numpy(), "t2": t2.to_numpy()})
    ghep = a.merge(b, on="khoa", how="inner").dropna(subset=["t1", "t2"])
    if len(ghep) < 2:
        raise LoiDauVao("ghép cặp được dưới 2 người có đủ điểm tổng ở cả hai lần — không tính được ICC")
    kq = icc_2_1(ghep[["t1", "t2"]].to_numpy(dtype=float))
    kq["n_lan1"], kq["n_lan2"], kq["n_ghep_cap"] = int(len(df1)), int(len(df2)), int(len(ghep))
    kq["xep_loai_theo_ktc"] = [xep_loai_koo_li(kq["ktc95"][0]), xep_loai_koo_li(kq["ktc95"][1])]
    kq["nguon"] = f"{NGUON_SHROUT_FLEISS} (công thức) · {NGUON_KOO_LI} (xếp loại)"
    return kq


# ---------------------------------------------------------------- CLI
def _phan_nhom(args: argparse.Namespace) -> dict[str, list[str]]:
    nhom: dict[str, list[str]] = {}
    for mo_ta in args.nhom or []:
        if ":" not in mo_ta:
            raise LoiDauVao(f"--nhom phải có dạng TEN:cot1,cot2 — nhận «{mo_ta}»")
        ten, cot = mo_ta.split(":", 1)
        ds = [c.strip() for c in cot.split(",") if c.strip()]
        if ten.strip() in nhom:
            raise LoiDauVao(f"tên nhóm trùng: {ten.strip()}")
        nhom[ten.strip()] = ds
    if args.muc:
        nhom.setdefault("Toan_thang", list(args.muc))
    if not nhom:
        raise LoiDauVao("chưa chọn cột mục: dùng --muc hoặc --nhom")
    return nhom


def _f(x: float | None, so: int = 3) -> str:
    return "—" if x is None or not math.isfinite(x) else f"{x:.{so}f}"


def in_bao_cao(kq: dict) -> str:
    dong = [f"# Độ tin cậy thang đo — {kq['tep']}", ""]
    for t in kq["thang"]:
        dong += [
            f"## {t['ten']} ({t['so_muc']} mục)",
            f"- n dùng được: {t['n_dung']}/{t['n_tong']} (loại {t['n_loai_vi_thieu']} hàng vì thiếu)",
            f"- Cronbach α = {_f(t['alpha'])} (KTC 95% Feldt: {_f(t['alpha_ktc95'][0])}–{_f(t['alpha_ktc95'][1])})",
        ]
        st = t["san_tran"]
        dong.append(
            "- Sàn/trần điểm tổng: chưa tính (chưa khai --min/--max)"
            if st is None
            else f"- Sàn/trần điểm tổng: {st['ty_le_san']:.1%} / {st['ty_le_tran']:.1%}"
        )
        dong += ["", "| Mục | r mục–tổng (hiệu chỉnh) | α nếu bỏ mục | % thiếu |", "|---|---|---|---|"]
        for m in t["muc"]:
            dong.append(
                f"| {m['muc']} | {_f(m['r_muc_tong_hieu_chinh'])} | {_f(m['alpha_neu_bo_muc'])}"
                f" | {m['ty_le_thieu']:.1%} |"
            )
        dong.append("")
        for cb in t["canh_bao"]:
            dong.append(f"- ⚠️ {cb}")
        dong.append("")
    if kq.get("lap_lai"):
        ll = kq["lap_lai"]
        dong += [
            "## Test–retest (điểm tổng)",
            f"- ICC(2,1) đồng thuận tuyệt đối = {_f(ll['icc'])} (KTC 95%: {_f(ll['ktc95'][0])}–{_f(ll['ktc95'][1])}),"
            f" ghép cặp {ll['n_ghep_cap']} người (lần 1: {ll['n_lan1']}, lần 2: {ll['n_lan2']})",
            f"- Xếp loại theo KTC: {ll['xep_loai_theo_ktc'][0]} → {ll['xep_loai_theo_ktc'][1]} ({ll['nguon']})",
            "",
        ]
    dong += [
        "_Tương quan mục–tổng xếp tăng dần; công cụ KHÔNG đặt ngưỡng loại mục — nhóm chuyên gia quyết định._",
        "_Độ tin cậy nội tại chỉ là một thuộc tính đo lường, không kết luận thang đo hợp lệ. Cần bác sĩ kiểm chứng._",
    ]
    return "\n".join(dong)


def chay(argv: list[str] | None = None) -> dict:
    ap = argparse.ArgumentParser(description="Độ tin cậy thang đo trên dữ liệu pilot (α, mục–tổng, sàn/trần, ICC).")
    ap.add_argument("du_lieu")
    ap.add_argument("--muc", nargs="+", help="các cột mục của một thang")
    ap.add_argument("--nhom", action="append", help="tiểu thang: TEN:cot1,cot2 (lặp được)")
    ap.add_argument("--min", type=float, dest="min_thang", help="điểm thấp nhất của mỗi mục")
    ap.add_argument("--max", type=float, dest="max_thang", help="điểm cao nhất của mỗi mục")
    ap.add_argument("--ma-thieu", nargs="*", type=float, default=[], help="mã coi là thiếu (vd 7 9)")
    ap.add_argument("--lap-lai", help="tệp lần đo lại (test–retest)")
    ap.add_argument("--khoa-id", help="cột mã ghép cặp giữa hai lần đo (không in ra)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", help="ghi báo cáo vào tệp này")
    args = ap.parse_args(argv)
    if (args.min_thang is None) != (args.max_thang is None):
        raise LoiDauVao("--min và --max phải khai cùng nhau")
    if args.min_thang is not None and args.min_thang >= args.max_thang:
        raise LoiDauVao("--min phải nhỏ hơn --max")
    if args.lap_lai and not args.khoa_id:
        raise LoiDauVao("--lap-lai cần --khoa-id để ghép cặp đúng người")
    df = doc_bang(args.du_lieu)
    nhom = _phan_nhom(args)
    kq: dict = {"tep": Path(args.du_lieu).name, "thang": []}
    for ten, cot in nhom.items():
        sub = chuan_hoa_muc(df, cot, args.ma_thieu)
        kq["thang"].append(phan_tich_thang(ten, sub, args.min_thang, args.max_thang))
    if args.lap_lai:
        if len(nhom) != 1:
            raise LoiDauVao("test–retest tính trên MỘT thang — chạy riêng từng tiểu thang")
        cot = next(iter(nhom.values()))
        kq["lap_lai"] = phan_tich_lap_lai(df, doc_bang(args.lap_lai), cot, args.khoa_id, args.ma_thieu)
    noi_dung = json.dumps(kq, ensure_ascii=False, indent=2) if args.json else in_bao_cao(kq)
    if args.out:
        Path(args.out).write_text(noi_dung + "\n", encoding="utf-8", newline="\n")
    else:
        print(noi_dung)
    return kq


def main(argv: list[str] | None = None) -> int:
    try:
        chay(argv)
    except LoiDauVao as e:
        print(f"LỖI ĐẦU VÀO: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
