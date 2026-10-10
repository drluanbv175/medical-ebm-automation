#!/usr/bin/env python3
"""dien_giai_ket_qua.py — Hợp đồng BẢN DIỄN GIẢI KẾT QUẢ (G6-T3, `dien-giai-ket-qua`) — 10/10/2026.

Bác sĩ giao: «G6-T3 (diễn giải kết quả) đảm bảo các kết quả được diễn giải và trình bày một cách tốt nhất (bao gồm số
liệu, văn phong và bảng biểu)». Trước đó G6-T3 khai đầu ra là tệp script phân tích chung — bản diễn giải không có tệp
riêng, không có gì để kiểm; `gen_research_docx --artifact interpretation` dựng docx từ JSON tự do.

Hợp đồng: `exports/<mã>/G6_DIEN_GIAI_<mã>.md` — năm mục cố định, Bảng kết quả chính có cột cố định, mỗi dòng TRUY
NGUYÊN về một tệp kết quả phân tích có thật (06_ket_qua/… hoặc 06_phan_tich_R/output/…). Công cụ CHỈ kiểm những gì
máy kiểm được — KHÔNG thay người đọc: đúng ý nghĩa lâm sàng, đúng trích y văn vẫn do người chấm chéo
(`phan-tich-thong-ke`, `binh-duyet`, `huong-dan-lam-sang`) và `kiem-chung-trich-dan`.

Ba trục kiểm:
  SỐ LIỆU   — ước lượng điểm và hai cận KTC 95% đọc được, cận dưới ≤ ước lượng ≤ cận trên; p đúng định dạng (không
              «0,000», không > 1; dưới 0,001 ghi «< 0,001»); mỗi số khớp (theo số chữ số thập phân đã báo) một số
              trong tệp kết quả được dẫn ở cột «Nguồn kết quả»; một dấu thập phân thống nhất trong bảng.
  VĂN PHONG — không cụm diễn giải quá mức: «đã chứng minh», «chứng minh rằng», «khẳng định chắc chắn», «xu hướng có ý
              nghĩa», «gần có ý nghĩa», «rất có ý nghĩa thống kê», «p = 0,000»; thiết kế KHÔNG can thiệp (cắt ngang,
              bệnh–chứng, thuần tập, chẩn đoán, dự báo, định tính) không dùng ngôn ngữ nhân quả «gây ra»/«là nguyên
              nhân»; mục 2 phải nói ý nghĩa LÂM SÀNG, mục 4 phải nêu HẠN CHẾ.
  BẢNG BIỂU — mỗi bảng có chú thích «Bảng N.» ngay trên, đủ hàng tiêu đề + hàng gạch, mọi hàng cùng số cột, không ô
              trống (ô không áp dụng ghi «—»), không còn «[CẦN …]».

Cách dùng:
    python3 tools/dien_giai_ket_qua.py mau --study <mã>          # dựng khung (không ghi đè)
    python3 tools/dien_giai_ket_qua.py kiem --study <mã> [--json] [--thiet-ke <mã thiết kế>]
Mã thoát: 0 đạt · 1 còn lỗi · 2 lỗi đầu vào (thiếu đề tài/tệp). Cần bác sĩ kiểm chứng.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

for _luong in (sys.stdout, sys.stderr):
    try:
        _luong.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

BASE = Path(__file__).resolve().parents[1]

TEN_TEP = "G6_DIEN_GIAI_{study}.md"
MUC = ("## 1. Kết quả chính", "## 2. Ý nghĩa thống kê và ý nghĩa lâm sàng", "## 3. Đối chiếu y văn",
       "## 4. Điểm mạnh và hạn chế", "## 5. Hàm ý thực hành và hướng nghiên cứu tiếp")
COT_BANG_CHINH = ("Kết cục", "Thước đo", "Ước lượng điểm", "KTC 95%", "p", "Ý nghĩa lâm sàng", "Nguồn kết quả")
# Thư mục kết quả phân tích — CÙNG bộ mà g6_quality_gate dùng (_THU_MUC_KET_QUA).
THU_MUC_KET_QUA = ("06_ket_qua", "06_phan_tich_R/output")
DUOI_VAN_BAN = (".txt", ".csv", ".tsv", ".json", ".md", ".log")
THIET_KE_KHONG_CAN_THIEP = ("cross_sectional", "case_control", "cohort", "diagnostic", "prediction", "qualitative")

_CUM_QUA_MUC = (
    (re.compile(r"\bđã\s+chứng\s+minh\b", re.I), "«đã chứng minh» — kết quả một nghiên cứu không «chứng minh»"),
    (re.compile(r"\bchứng\s+minh\s+(?:được\s+)?rằng\b", re.I), "«chứng minh rằng» — diễn giải quá mức"),
    (re.compile(r"\bkhẳng\s+định\s+chắc\s+chắn\b", re.I), "«khẳng định chắc chắn» — diễn giải quá mức"),
    (re.compile(r"\bxu\s+hướng\s+có\s+ý\s+nghĩa\b", re.I), "«xu hướng có ý nghĩa» — p không đạt thì không «gần đạt»"),
    (re.compile(r"\bgần\s+(?:có|đạt)\s+ý\s+nghĩa\b", re.I), "«gần có ý nghĩa» — p không đạt thì không «gần đạt»"),
    (re.compile(r"\brất\s+có\s+ý\s+nghĩa\s+thống\s+kê\b", re.I),
     "«rất có ý nghĩa thống kê» — p không đo độ lớn hiệu ứng"),
    (re.compile(r"\bp\s*=\s*0[.,]0+\b(?![.,]?\d*[1-9])", re.I), "«p = 0,000» — ghi «p < 0,001»"),
)
_CUM_NHAN_QUA = (
    (re.compile(r"\bgây\s+ra\b", re.I), "«gây ra»"),
    (re.compile(r"\blà\s+nguyên\s+nhân\b", re.I), "«là nguyên nhân»"),
)
_SO = re.compile(r"[-−]?\d+(?:[.,]\d+)?")
_KTC = re.compile(r"([-−]?\d+(?:[.,]\d+)?)\s*(?:–|—|-|;|,\s|đến|to)\s*([-−]?\d+(?:[.,]\d+)?)")
_CHU_THICH_BANG = re.compile(r"^\**\s*Bảng\s+\d+[.:]")
_DINH_DANH = re.compile(r"\bPMID[:\s]*\d{6,9}\b|\b10\.\d{4,9}/\S+", re.I)


class LoiDauVao(ValueError):
    """Đầu vào không dùng được — CLI trả mã 2."""


def duong_dan(study: str, out_dir: Path) -> Path:
    return Path(out_dir) / TEN_TEP.format(study=study)


def sinh_mau(study: str, out_dir: Path) -> Path:
    """Dựng khung bản diễn giải (không ghi đè bản đã có)."""
    p = duong_dan(study, out_dir)
    if p.exists():
        raise LoiDauVao(f"đã có {p.name} — không ghi đè bản diễn giải đã viết")
    bang = ("| " + " | ".join(COT_BANG_CHINH) + " |\n|" + "---|" * len(COT_BANG_CHINH) + "\n"
            "| [CẦN tên kết cục chính] | [CẦN RR/OR/HR/MD…] | [CẦN] | [CẦN cận dưới–cận trên] | [CẦN] | "
            "[CẦN so ngưỡng MCID/ý nghĩa lâm sàng có nguồn] | [CẦN 06_ket_qua/<tệp>] |\n")
    van = (f"# Diễn giải kết quả — {study}\n\n"
           f"{MUC[0]}\n\n**Bảng 1.** Kết quả kết cục chính (ước lượng, KTC 95%, p — đúng như tệp kết quả)\n\n{bang}\n"
           f"{MUC[1]}\n\n[CẦN: kết quả có ý nghĩa thống kê không, và độ lớn hiệu ứng so với ngưỡng ý nghĩa lâm sàng "
           f"(MCID/ngưỡng có nguồn) — hai trục tách riêng]\n\n"
           f"{MUC[2]}\n\n[CẦN: so với nghiên cứu trước — mỗi so sánh kèm PMID/DOI đã kiểm chứng]\n\n"
           f"{MUC[3]}\n\n[CẦN: điểm mạnh; hạn chế (sai lệch chọn, đo lường, nhiễu, cỡ mẫu, tính khái quát)]\n\n"
           f"{MUC[4]}\n\n[CẦN: hàm ý cho thực hành — không vượt quá thiết kế; hướng nghiên cứu tiếp]\n\n"
           "> Cần bác sĩ kiểm chứng.\n")
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    p.write_text(van, encoding="utf-8", newline="\n")
    return p


# ── tách bảng ───────────────────────────────────────────────────────────────────────────────────────────────────────
def _o(dong: str) -> List[str]:
    return [x.strip() for x in re.split(r"(?<!\\)\|", dong.strip().strip("|"))]


def cac_bang(van: str) -> List[Tuple[int, str, List[List[str]]]]:
    """[(dòng bắt đầu 1-based, chú thích ngay trên hoặc "", [hàng…])] — hàng đầu là tiêu đề, hàng gạch đã bỏ."""
    dong = van.splitlines()
    ra, i = [], 0
    while i < len(dong):
        if dong[i].lstrip().startswith("|"):
            bat_dau = i
            khoi = []
            while i < len(dong) and dong[i].lstrip().startswith("|"):
                khoi.append(dong[i])
                i += 1
            truoc = [d.strip() for d in dong[max(0, bat_dau - 3):bat_dau] if d.strip()]
            chu_thich = truoc[-1] if truoc and _CHU_THICH_BANG.match(truoc[-1]) else ""
            co_gach = len(khoi) > 1 and re.fullmatch(r"\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?", khoi[1].strip())
            hang = [_o(khoi[0])] + [_o(d) for d in khoi[(2 if co_gach else 1):]]
            ra.append((bat_dau + 1, chu_thich if co_gach else "\0" + chu_thich, hang))
        else:
            i += 1
    return ra


def _muc(van: str, ten: str) -> str:
    i = van.find(ten)
    if i < 0:
        return ""
    j = van.find("\n## ", i + len(ten))
    return van[i: j if j > 0 else len(van)]


def _so(chuoi: str) -> Optional[float]:
    m = _SO.search(chuoi or "")
    return float(m.group(0).replace("−", "-").replace(",", ".")) if m else None


def _so_le(chuoi: str) -> int:
    m = _SO.search(chuoi or "")
    if not m or not re.search(r"[.,]", m.group(0)):
        return 0
    return len(re.split(r"[.,]", m.group(0))[1])


def _van_ban_nguon(p: Path) -> Optional[str]:
    if p.suffix.lower() in DUOI_VAN_BAN:
        return p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() == ".xlsx":
        try:
            import openpyxl  # noqa: PLC0415

            wb = openpyxl.load_workbook(p, read_only=True, data_only=True)
            return "\n".join(str(c) for ws in wb.worksheets for row in ws.iter_rows(values_only=True)
                             for c in row if c is not None)
        except Exception:  # noqa: BLE001 — không đọc được ⇒ None (báo «không đối chiếu được»)
            return None
    return None


def _co_trong_nguon(gia_tri: float, so_le: int, van_nguon: str) -> bool:
    nguong = 0.5 * 10 ** (-so_le) + 1e-9
    for m in _SO.finditer(van_nguon):
        try:
            x = float(m.group(0).replace("−", "-").replace(",", "."))
        except ValueError:
            continue
        if abs(x - gia_tri) <= nguong:
            return True
    return False


def _kiem_bang_chinh(out_dir: Path, bang: List[List[str]], ra: List[str]) -> None:
    tieu_de = bang[0]
    thieu = [c for c in COT_BANG_CHINH if c not in tieu_de]
    if thieu:
        ra.append(f"Bảng kết quả chính thiếu cột: {', '.join(thieu)}")
        return
    vi = {c: tieu_de.index(c) for c in COT_BANG_CHINH}
    if len(bang) < 2:
        ra.append("Bảng kết quả chính chưa có dòng kết quả nào")
    dau_tp = set()
    for k, h in enumerate(bang[1:], 1):
        if len(h) != len(tieu_de):
            continue  # đã báo ở kiểm bảng chung
        uoc, ktc, p_val, nguon = h[vi["Ước lượng điểm"]], h[vi["KTC 95%"]], h[vi["p"]], h[vi["Nguồn kết quả"]]
        nhan = f"Bảng kết quả chính, dòng {k} («{h[vi['Kết cục']][:30]}»)"
        diem = _so(uoc)
        if diem is None:
            ra.append(f"{nhan}: ước lượng điểm không đọc được số")
            continue
        m = _KTC.search(ktc.replace("−", "-"))
        if not m:
            ra.append(f"{nhan}: KTC 95% phải ghi hai cận (vd «0,72–0,98»)")
            continue
        duoi, tren = (float(x.replace(",", ".")) for x in m.groups())
        if not duoi <= diem <= tren:
            ra.append(f"{nhan}: ước lượng {uoc} nằm ngoài KTC 95% {ktc}")
        for o in (uoc, m.group(1), m.group(2)):
            mm = re.search(r"\d([.,])\d", o)
            if mm:
                dau_tp.add(mm.group(1))
        if p_val not in ("—", "N/A"):
            if re.fullmatch(r"<\s*0[.,]001", p_val.replace("\u00a0", " ")):
                pass
            else:
                pv = _so(p_val)
                if pv is None or not 0 <= pv <= 1:
                    ra.append(f"{nhan}: p «{p_val}» không hợp lệ (0–1, hoặc «< 0,001», hoặc «—»)")
                elif pv < 0.001:
                    ra.append(f"{nhan}: p «{p_val}» < 0,001 — ghi «< 0,001»")
        duong = nguon.strip().strip("`").strip()
        dp = Path(duong)
        if (not duong or dp.is_absolute() or ".." in dp.parts
                or not any(duong.startswith(t + "/") for t in THU_MUC_KET_QUA)):
            ra.append(f"{nhan}: «Nguồn kết quả» phải là tệp trong {' hoặc '.join(THU_MUC_KET_QUA)}/ của đề tài")
            continue
        tep = Path(out_dir) / dp
        if not tep.is_file():
            ra.append(f"{nhan}: tệp nguồn {duong} không tồn tại")
            continue
        van_nguon = _van_ban_nguon(tep)
        if van_nguon is None:
            ra.append(f"{nhan}: không đối chiếu được số với {duong} (chỉ đọc txt/csv/tsv/json/md/log/xlsx)")
            continue
        for ten, o in (("ước lượng", uoc), ("cận dưới", m.group(1)), ("cận trên", m.group(2))):
            gia = _so(o)
            if gia is not None and not _co_trong_nguon(gia, _so_le(o), van_nguon):
                ra.append(f"{nhan}: {ten} {o} không có trong {duong} — số phải chép đúng tệp kết quả")
    if len(dau_tp) > 1:
        ra.append("Bảng kết quả chính trộn dấu thập phân «,» và «.» — dùng một kiểu thống nhất")


def kiem(study: str, out_dir: Path, ma_thiet_ke: Optional[str] = None) -> List[str]:
    """Danh sách lỗi (rỗng = đạt) của bản diễn giải; thiếu tệp ⇒ LoiDauVao."""
    p = duong_dan(study, out_dir)
    if not p.is_file():
        raise LoiDauVao(f"không thấy {p.name} — dựng khung bằng lệnh «mau»")
    van = p.read_text(encoding="utf-8")
    ra: List[str] = []
    # Cấu trúc
    vi_tri = [van.find(m) for m in MUC]
    for m, k in zip(MUC, vi_tri):
        if k < 0:
            ra.append(f"thiếu mục «{m[3:]}»")
    co = [k for k in vi_tri if k >= 0]
    if co != sorted(co):
        ra.append("năm mục không đúng thứ tự 1→5")
    if "[CẦN" in van:
        ra.append(f"còn {van.count('[CẦN')} ô «[CẦN …]» chưa điền")
    if "cần bác sĩ kiểm chứng" not in van.casefold():
        ra.append("thiếu dòng «Cần bác sĩ kiểm chứng»")
    # Bảng biểu
    bang = cac_bang(van)
    for dong, chu_thich, hang in bang:
        if chu_thich.startswith("\0"):
            ra.append(f"bảng ở dòng {dong}: thiếu hàng gạch «|---|» dưới tiêu đề")
            chu_thich = chu_thich[1:]
        if not chu_thich:
            ra.append(f"bảng ở dòng {dong}: thiếu chú thích «Bảng N.» ngay trên bảng")
        so_cot = len(hang[0])
        for k, h in enumerate(hang[1:], 1):
            if len(h) != so_cot:
                ra.append(f"bảng ở dòng {dong}, hàng {k}: {len(h)} ô ≠ {so_cot} cột tiêu đề")
            elif any(not o for o in h):
                ra.append(f"bảng ở dòng {dong}, hàng {k}: có ô trống (không áp dụng thì ghi «—»)")
    muc1 = _muc(van, MUC[0])
    dau_muc1 = van.find(muc1) if muc1 else -1
    bang_chinh = [h for d, _c, h in bang if muc1 and dau_muc1 <= _vi_tri_dong(van, d) < dau_muc1 + len(muc1)]
    if not bang_chinh:
        ra.append("mục 1 không có Bảng kết quả chính")
    else:
        _kiem_bang_chinh(out_dir, bang_chinh[0], ra)
    # Văn phong (ngoài bảng)
    ngoai_bang = "\n".join(d for d in van.splitlines() if not d.lstrip().startswith("|"))
    for bt, ly_do in _CUM_QUA_MUC:
        if bt.search(ngoai_bang):
            ra.append(f"văn phong: {ly_do}")
    if ma_thiet_ke in THIET_KE_KHONG_CAN_THIEP:
        for bt, cum in _CUM_NHAN_QUA:
            if bt.search(ngoai_bang):
                ra.append(f"văn phong: {cum} — thiết kế {ma_thiet_ke} chỉ cho thấy LIÊN QUAN, không nhân quả")
    muc2 = _muc(van, MUC[1])
    if muc2 and "lâm sàng" not in muc2[len(MUC[1]):].casefold():
        ra.append("mục 2 chưa nói ý nghĩa LÂM SÀNG (tách khỏi ý nghĩa thống kê)")
    muc3 = _muc(van, MUC[2])
    if muc3 and not _DINH_DANH.search(muc3):
        ra.append("mục 3 chưa có PMID/DOI nào cho phần đối chiếu y văn")
    muc4 = _muc(van, MUC[3])
    if muc4 and "hạn chế" not in muc4[len(MUC[3]):].casefold():
        ra.append("mục 4 chưa nêu hạn chế")
    return ra


def _vi_tri_dong(van: str, so_dong: int) -> int:
    """Vị trí ký tự đầu dòng thứ `so_dong` (1-based)."""
    k = 0
    for _ in range(so_dong - 1):
        k = van.find("\n", k) + 1
    return k


def _thu_muc(study: str) -> Path:
    return BASE / "exports" / study


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Hợp đồng bản diễn giải kết quả G6-T3 (dựng khung + kiểm).")
    sub = ap.add_subparsers(dest="lenh", required=True)
    a = sub.add_parser("mau", help="dựng khung G6_DIEN_GIAI_<mã>.md (không ghi đè)")
    a.add_argument("--study", required=True)
    a = sub.add_parser("kiem", help="kiểm số liệu · văn phong · bảng biểu")
    a.add_argument("--study", required=True)
    a.add_argument("--thiet-ke", default=None, help="mã thiết kế (mặc định suy từ hồ sơ đề tài)")
    a.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    out_dir = _thu_muc(args.study)
    if not out_dir.is_dir():
        print(f"❌ Không thấy thư mục đề tài exports/{args.study}", file=sys.stderr)
        return 2
    try:
        if args.lenh == "mau":
            p = sinh_mau(args.study, out_dir)
            print(f"✅ Đã dựng khung {p.name} — điền rồi chạy «kiem». Cần bác sĩ kiểm chứng.")
            return 0
        tk = args.thiet_ke
        if tk is None:
            try:
                sys.path.insert(0, str(BASE / "tools"))
                import skill_standards as SK  # noqa: PLC0415

                tk = SK.dac_ta_thiet_ke(out_dir).get("design_code")
            except Exception:  # noqa: BLE001 — không suy được ⇒ bỏ kiểm ngôn ngữ nhân quả
                tk = None
        loi = kiem(args.study, out_dir, tk)
    except LoiDauVao as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({"study": args.study, "thiet_ke": tk, "dat": not loi, "loi": loi}, ensure_ascii=False,
                         indent=2))
    else:
        print(("✅ Bản diễn giải đạt kiểm máy (số liệu · văn phong · bảng biểu)" if not loi
               else f"🔴 {len(loi)} lỗi:") + ("" if not loi else "\n" + "\n".join(f"  - {x}" for x in loi)))
        print("Kiểm máy không thay người đọc — ý nghĩa lâm sàng và trích dẫn do người chấm chéo. "
              "Cần bác sĩ kiểm chứng.")
    return 1 if loi else 0


if __name__ == "__main__":
    sys.exit(main())
