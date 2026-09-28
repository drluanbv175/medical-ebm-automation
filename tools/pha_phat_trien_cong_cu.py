#!/usr/bin/env python3
"""
pha_phat_trien_cong_cu.py — Số liệu cho PHA PHÁT TRIỂN bộ câu hỏi: hội đồng chuyên gia (CVI) + phỏng vấn nhận thức.

THÊM 28/09/2026 (đề xuất R2). Đề cương C1a (mục 4.5.1) khoá pha phát triển 4 bước TRƯỚC mẫu chính: bảng truy xuất
item → hội đồng chuyên gia I-CVI/S-CVI → phỏng vấn nhận thức 10–15 người → pilot. Repo có công cụ KIỂM đề cương nhắc
tới I-CVI (check_de_cuong.py) nhưng chưa có công cụ TÍNH; pilot đã có tools/kiem_tin_cay_thang_do.py (R1).

Ba lệnh con (ngoại tuyến, tất định, chỉ in số tổng hợp — không in mã người tham gia/mã chuyên gia):

  mau        Sinh hai tệp CSV rỗng từ danh sách mục: phiếu chấm CVI (hàng = mục, cột = chuyên gia, điểm 1–4) và
             nhật ký phỏng vấn nhận thức (mỗi dòng = một người × một mục).
  cvi        Từ phiếu chấm liên quan 4 mức: I-CVI (tỷ lệ chuyên gia chấm 3 hoặc 4), kappa hiệu chỉnh cho đồng thuận
             ngẫu nhiên (k* = (I-CVI − pc)/(1 − pc), pc = C(N,A)·0,5^N), S-CVI/Ave và S-CVI/UA — báo CẢ HAI vì hai
             cách cho số khác nhau (Polit & Beck 2006).
  nhan-thuc  Từ nhật ký: mỗi mục bao nhiêu % người phỏng vấn gặp vấn đề (hỏi lại/hiểu sai); đếm số mục vượt ngưỡng và
             đối chiếu tiêu chí dừng F5 của đề cương C1a mục 4.4.2 (≥ 3 mục có ≥ 20% người hỏi lại/hiểu sai ⇒ sửa
             công cụ rồi dry-run lại). Ngưỡng mặc định LẤY TỪ ĐỀ CƯƠNG, đổi bằng --nguong-ty-le/--nguong-so-muc.

Nguồn đã tra PubMed (28/09/2026):
  - Polit, Beck & Owen 2007 (PMID 17654487, doi:10.1002/nur.20199): kappa hiệu chỉnh; I-CVI ≥ 0,78 với ≥ 3 chuyên
    gia là bằng chứng giá trị nội dung tốt (nêu trong tóm tắt).
  - Polit & Beck 2006 (PMID 16977646, doi:10.1002/nur.20147): hai cách tính S-CVI (/UA và /Ave) phải nói rõ cách
    dùng. Ngưỡng S-CVI/Ave ≥ 0,90 KHÔNG nằm trong tóm tắt ⇒ in kèm [CẦN ĐỐI CHIẾU NGUYÊN VĂN].

Ranh giới: công cụ KHÔNG quyết định giữ/bỏ/sửa mục — hội đồng chuyên gia và chủ nhiệm quyết định; KHÔNG kết luận
công cụ «hợp lệ». Cần bác sĩ kiểm chứng.

Cách dùng:
    python tools/pha_phat_trien_cong_cu.py mau --muc A1 A2 B1 B2 --so-chuyen-gia 6 \
        --thu-muc exports/<de-tai>/pha_cong_cu
    python tools/pha_phat_trien_cong_cu.py cvi phieu_cvi.csv
    python tools/pha_phat_trien_cong_cu.py nhan-thuc nhat_ky.csv [--json]
Mã thoát: 0 xong · 1 (chỉ nhan-thuc) vi phạm tiêu chí F5 · 2 lỗi đầu vào.
"""
from __future__ import annotations

import argparse
import csv
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

NGUON_POLIT_2007 = "Polit, Beck & Owen 2007, PMID 17654487"
NGUON_POLIT_2006 = "Polit & Beck 2006, PMID 16977646 [CẦN ĐỐI CHIẾU NGUYÊN VĂN]"
NGUON_F5 = "đề cương C1a mục 4.4.2, tiêu chí F5"
I_CVI_NGUONG = 0.78
S_CVI_AVE_NGUONG = 0.90
COT_MUC = "muc"
COT_NHAT_KY = ["ma_nguoi", "muc", "van_de", "loai_van_de", "de_xuat_sua"]
LOAI_VAN_DE = ("hieu_cau_hoi", "nho_lai", "can_nhac", "chon_dap_an", "khac")


class LoiDauVao(ValueError):
    """Đầu vào không dùng được — CLI trả mã 2."""


def _doc_csv(duong: str | Path) -> tuple[list[str], list[dict[str, str]]]:
    p = Path(duong)
    if not p.is_file():
        raise LoiDauVao(f"không thấy tệp: {p}")
    with p.open(encoding="utf-8-sig", newline="") as f:
        r = csv.DictReader(f)
        if not r.fieldnames:
            raise LoiDauVao(f"{p.name}: tệp rỗng hoặc không có dòng tiêu đề")
        dong = [{(k or "").strip(): (v or "").strip() for k, v in d.items()} for d in r]
        return [c.strip() for c in r.fieldnames], dong


# ---------------------------------------------------------------- CVI
def kappa_hieu_chinh(n: int, a: int) -> float:
    """k* = (I-CVI − pc)/(1 − pc), pc = C(n, a)·0,5^n (Polit, Beck & Owen 2007)."""
    if n <= 0:
        return float("nan")
    i_cvi = a / n
    pc = math.comb(n, a) * 0.5**n
    return float("nan") if pc >= 1 else (i_cvi - pc) / (1 - pc)


def tinh_cvi(cot: list[str], dong: list[dict[str, str]]) -> dict:
    if COT_MUC not in cot:
        raise LoiDauVao(f"phiếu CVI cần cột «{COT_MUC}» (mã mục) + mỗi chuyên gia một cột")
    cg = [c for c in cot if c != COT_MUC]
    if not cg:
        raise LoiDauVao("phiếu CVI chưa có cột chuyên gia nào")
    muc_kq, trung = [], set()
    for d in dong:
        ma = d[COT_MUC]
        if not ma:
            continue
        if ma in trung:
            raise LoiDauVao(f"mã mục trùng trong phiếu CVI: {ma}")
        trung.add(ma)
        diem = []
        for c in cg:
            v = d.get(c, "")
            if v == "":
                continue
            if v not in {"1", "2", "3", "4"}:
                raise LoiDauVao(f"mục {ma}, cột {c}: điểm «{v}» không thuộc thang 1–4")
            diem.append(int(v))
        n, a = len(diem), sum(1 for x in diem if x >= 3)
        muc_kq.append({
            "muc": ma, "so_chuyen_gia_cham": n, "so_dong_y_lien_quan": a,
            "i_cvi": a / n if n else float("nan"), "kappa_hieu_chinh": kappa_hieu_chinh(n, a),
            "thieu_diem": len(cg) - n,
        })
    if not muc_kq:
        raise LoiDauVao("phiếu CVI không có mục nào")
    co_diem = [m for m in muc_kq if m["so_chuyen_gia_cham"]]
    s_ave = sum(m["i_cvi"] for m in co_diem) / len(co_diem) if co_diem else float("nan")
    s_ua = sum(1 for m in co_diem if m["so_dong_y_lien_quan"] == m["so_chuyen_gia_cham"]) / len(co_diem) \
        if co_diem else float("nan")
    canh_bao = []
    if len(cg) < 3:
        canh_bao.append(f"hội đồng {len(cg)} chuyên gia < 3 — ngưỡng I-CVI 0,78 của {NGUON_POLIT_2007} không áp được")
    duoi = [m["muc"] for m in co_diem if m["i_cvi"] < I_CVI_NGUONG]
    if duoi:
        canh_bao.append(f"{len(duoi)} mục có I-CVI < {I_CVI_NGUONG} ({NGUON_POLIT_2007}): {', '.join(duoi)}")
    if math.isfinite(s_ave) and s_ave < S_CVI_AVE_NGUONG:
        canh_bao.append(f"S-CVI/Ave = {s_ave:.2f} < {S_CVI_AVE_NGUONG} ({NGUON_POLIT_2006})")
    thieu = [m["muc"] for m in muc_kq if m["thieu_diem"]]
    if thieu:
        canh_bao.append(f"{len(thieu)} mục có chuyên gia bỏ trống điểm (I-CVI tính trên số người đã chấm): "
                        + ", ".join(thieu))
    return {
        "so_chuyen_gia": len(cg), "so_muc": len(muc_kq),
        "s_cvi_ave": s_ave, "s_cvi_ua": s_ua,
        "muc": sorted(muc_kq, key=lambda m: (math.isnan(m["i_cvi"]), m["i_cvi"])),
        "canh_bao": canh_bao,
    }


# ---------------------------------------------------------------- phỏng vấn nhận thức
def tinh_nhan_thuc(cot: list[str], dong: list[dict[str, str]], nguong_ty_le: float, nguong_so_muc: int) -> dict:
    thieu = [c for c in ("ma_nguoi", "muc", "van_de") if c not in cot]
    if thieu:
        raise LoiDauVao(f"nhật ký thiếu cột: {', '.join(thieu)}")
    theo_muc: dict[str, dict] = {}
    cap: set[tuple[str, str]] = set()
    nguoi: set[str] = set()
    for i, d in enumerate(dong, start=2):
        ma_n, ma_m, vd = d["ma_nguoi"], d["muc"], d["van_de"]
        if not ma_n and not ma_m and not vd:
            continue
        if not ma_n or not ma_m:
            raise LoiDauVao(f"dòng {i}: thiếu ma_nguoi hoặc muc")
        if vd not in {"0", "1"}:
            raise LoiDauVao(f"dòng {i}: van_de phải là 0 (không) hoặc 1 (có hỏi lại/hiểu sai), nhận «{vd}»")
        if (ma_n, ma_m) in cap:
            raise LoiDauVao(f"dòng {i}: cùng một người ghi hai lần cho mục {ma_m}")
        cap.add((ma_n, ma_m))
        nguoi.add(ma_n)
        m = theo_muc.setdefault(ma_m, {"muc": ma_m, "so_nguoi": 0, "so_co_van_de": 0, "loai": {}, "so_de_xuat": 0})
        m["so_nguoi"] += 1
        if vd == "1":
            m["so_co_van_de"] += 1
            loai = d.get("loai_van_de", "") or "chua_phan_loai"
            m["loai"][loai] = m["loai"].get(loai, 0) + 1
        if d.get("de_xuat_sua"):
            m["so_de_xuat"] += 1
    if not theo_muc:
        raise LoiDauVao("nhật ký không có dòng dữ liệu nào")
    for m in theo_muc.values():
        m["ty_le"] = m["so_co_van_de"] / m["so_nguoi"]
    vuot = sorted((m for m in theo_muc.values() if m["ty_le"] >= nguong_ty_le), key=lambda m: -m["ty_le"])
    vi_pham = len(vuot) >= nguong_so_muc
    return {
        "so_nguoi_phong_van": len(nguoi), "so_muc": len(theo_muc),
        "nguong": {"ty_le": nguong_ty_le, "so_muc": nguong_so_muc, "nguon": NGUON_F5},
        "so_muc_vuot_nguong": len(vuot), "muc_vuot_nguong": [m["muc"] for m in vuot],
        "vi_pham_f5": vi_pham,
        "muc": sorted(theo_muc.values(), key=lambda m: (-m["ty_le"], m["muc"])),
    }


# ---------------------------------------------------------------- mẫu
def sinh_mau(muc: list[str], so_cg: int, thu_muc: Path) -> list[Path]:
    if not muc:
        raise LoiDauVao("chưa có danh sách mục (--muc)")
    if len(set(muc)) != len(muc):
        raise LoiDauVao("danh sách mục có mã trùng")
    if so_cg < 1:
        raise LoiDauVao("--so-chuyen-gia phải ≥ 1")
    thu_muc.mkdir(parents=True, exist_ok=True)
    p_cvi, p_nk = thu_muc / "phieu_cvi.csv", thu_muc / "nhat_ky_phong_van_nhan_thuc.csv"
    for p in (p_cvi, p_nk):
        if p.exists():
            raise LoiDauVao(f"đã có {p} — không ghi đè dữ liệu đã nhập")
    with p_cvi.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow([COT_MUC] + [f"CG{i:02d}" for i in range(1, so_cg + 1)])
        for m in muc:
            w.writerow([m] + [""] * so_cg)
    with p_nk.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(COT_NHAT_KY)
        for m in muc:
            w.writerow(["NT01", m, "", "", ""])
    return [p_cvi, p_nk]


# ---------------------------------------------------------------- in báo cáo
def _f(x: float, so: int = 2) -> str:
    return "—" if not math.isfinite(x) else f"{x:.{so}f}"


def in_cvi(kq: dict) -> str:
    dong = [
        f"# Giá trị nội dung — hội đồng {kq['so_chuyen_gia']} chuyên gia, {kq['so_muc']} mục", "",
        f"- S-CVI/Ave = {_f(kq['s_cvi_ave'])} · S-CVI/UA = {_f(kq['s_cvi_ua'])} (báo cả hai — {NGUON_POLIT_2006})", "",
        "| Mục | Số CG chấm | Chấm 3–4 | I-CVI | Kappa hiệu chỉnh |", "|---|---|---|---|---|",
    ]
    for m in kq["muc"]:
        dong.append(f"| {m['muc']} | {m['so_chuyen_gia_cham']} | {m['so_dong_y_lien_quan']} | {_f(m['i_cvi'])} |"
                    f" {_f(m['kappa_hieu_chinh'])} |")
    dong.append("")
    dong += [f"- ⚠️ {c}" for c in kq["canh_bao"]]
    dong += ["", "_Mục xếp tăng dần theo I-CVI. Công cụ không quyết định giữ/bỏ/sửa mục — hội đồng quyết định._",
             "_Cần bác sĩ kiểm chứng._"]
    return "\n".join(dong)


def in_nhan_thuc(kq: dict) -> str:
    ng = kq["nguong"]
    ket = (f"🔴 VI PHẠM F5: {kq['so_muc_vuot_nguong']} mục ≥ {ng['ty_le']:.0%} (ngưỡng {ng['so_muc']} mục) — "
           "sửa câu chữ rồi dry-run lại (không phải dừng đề tài)" if kq["vi_pham_f5"]
           else f"🟢 Chưa vi phạm F5: {kq['so_muc_vuot_nguong']} mục ≥ {ng['ty_le']:.0%} (ngưỡng {ng['so_muc']} mục)")
    dong = [
        f"# Phỏng vấn nhận thức — {kq['so_nguoi_phong_van']} người, {kq['so_muc']} mục", "",
        f"- {ket} ({ng['nguon']})", "",
        "| Mục | Số người | Có vấn đề | Tỷ lệ | Loại vấn đề | Có đề xuất sửa |", "|---|---|---|---|---|---|",
    ]
    for m in kq["muc"]:
        loai = ", ".join(f"{k}: {v}" for k, v in sorted(m["loai"].items())) or "—"
        dong.append(f"| {m['muc']} | {m['so_nguoi']} | {m['so_co_van_de']} | {m['ty_le']:.0%} | {loai} |"
                    f" {m['so_de_xuat']} |")
    dong += ["", "_Tỷ lệ tính trên số người đã được hỏi về MỤC ĐÓ. Không in mã người tham gia._",
             "_Cần bác sĩ kiểm chứng._"]
    return "\n".join(dong)


def _json(kq: dict) -> str:
    return json.dumps(kq, ensure_ascii=False, indent=2, allow_nan=True)


def chay(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Số liệu pha phát triển bộ câu hỏi (CVI + phỏng vấn nhận thức).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a_mau = sub.add_parser("mau", help="sinh phiếu CVI + nhật ký phỏng vấn nhận thức rỗng")
    a_mau.add_argument("--muc", nargs="+", required=True)
    a_mau.add_argument("--so-chuyen-gia", type=int, required=True)
    a_mau.add_argument("--thu-muc", required=True)
    a_cvi = sub.add_parser("cvi", help="tính I-CVI, kappa hiệu chỉnh, S-CVI/Ave, S-CVI/UA")
    a_cvi.add_argument("tep")
    a_cvi.add_argument("--json", action="store_true")
    a_nt = sub.add_parser("nhan-thuc", help="tổng hợp nhật ký phỏng vấn nhận thức + tiêu chí F5")
    a_nt.add_argument("tep")
    a_nt.add_argument("--nguong-ty-le", type=float, default=0.20, help="mặc định 0,20 theo F5 đề cương C1a")
    a_nt.add_argument("--nguong-so-muc", type=int, default=3, help="mặc định 3 theo F5 đề cương C1a")
    a_nt.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if a.lenh == "mau":
        for p in sinh_mau(a.muc, a.so_chuyen_gia, Path(a.thu_muc)):
            print(f"đã tạo {p}")
        print("Điền mã ẩn danh (CG01…, NT01…) — KHÔNG ghi họ tên chuyên gia hay người bệnh. Cần bác sĩ kiểm chứng.")
        return 0
    if a.lenh == "cvi":
        kq = tinh_cvi(*_doc_csv(a.tep))
        print(_json(kq) if a.json else in_cvi(kq))
        return 0
    if not 0 < a.nguong_ty_le <= 1 or a.nguong_so_muc < 1:
        raise LoiDauVao("ngưỡng không hợp lệ: 0 < --nguong-ty-le ≤ 1 và --nguong-so-muc ≥ 1")
    kq = tinh_nhan_thuc(*_doc_csv(a.tep), a.nguong_ty_le, a.nguong_so_muc)
    print(_json(kq) if a.json else in_nhan_thuc(kq))
    return 1 if kq["vi_pham_f5"] else 0


def main(argv: list[str] | None = None) -> int:
    try:
        return chay(argv)
    except LoiDauVao as e:
        print(f"LỖI ĐẦU VÀO: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
