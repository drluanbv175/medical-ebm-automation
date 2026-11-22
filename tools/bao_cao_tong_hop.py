#!/usr/bin/env python3
"""Bộ sinh BÁO CÁO TỔNG HỢP KẾT QUẢ ĐỀ TÀI (hồ sơ nghiệm thu) từ các tài liệu đề tài đã có.

Khuôn theo hướng dẫn chung bác sĩ gửi 21/11/2026 (mục III, bản BV TƯQĐ 108 2019 — BVQY175 chưa có mẫu báo cáo riêng):
Danh sách cán bộ tham gia → Mục lục → Danh mục chữ viết tắt → Danh mục bảng biểu → Đặt vấn đề → Chương 1 Tổng quan →
Chương 2 Đối tượng và phương pháp → Chương 3 Kết quả → Chương 4 Bàn luận → Kết luận → Khuyến nghị → Tài liệu tham
khảo → Phụ lục.

Nguồn (chỉ ĐỌC, không bịa nội dung):
- Đề cương nộp Hội đồng ``DE_CUONG_NOP_HOI_DONG_<mã>.md``: đặt vấn đề, mục tiêu, tổng quan, chữ viết tắt, nhân lực,
  danh mục tài liệu tham khảo đầy đủ, phụ lục phiếu thu thập và bảng biến.
- Bản thảo G7 ``G7_A8_MANUSCRIPT_<mã>.md`` (viết SAU khi có kết quả): phương pháp (thì quá khứ), kết quả, bàn luận,
  kết luận.
- Diễn giải G6 ``G6_DIEN_GIAI_<mã>.md``: mục hàm ý thực hành → khuyến nghị.

Trích dẫn: danh mục của đề cương làm gốc; trích dẫn của bản thảo được ghép theo PMID → DOI → tiêu đề rồi đánh số lại,
tài liệu chỉ có ở bản thảo nối vào cuối. Đề mục con của nguồn hạ xuống cấp 4 để bộ kiểm cấu trúc chỉ thấy các chương.

Thiếu bản thảo G7 hoặc đề cương ⇒ KHÔNG sinh (báo cáo nghiệm thu chỉ có khi đã có kết quả thật).
Dùng: ``python tools/bao_cao_tong_hop.py --study <mã> [--goc <thư mục gốc>] [--ghi]`` (mặc định chạy khô).
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

REPO = Path(__file__).resolve().parents[1]
MAU_TEP = "BAO_CAO_TONG_HOP_{s}.md"

_DE_MUC = re.compile(r"^(#{1,6})\s+(.*\S)\s*$")
_TRICH = re.compile(r"\[(\d+(?:\s*[–\-]\s*\d+)?(?:\s*,\s*\d+(?:\s*[–\-]\s*\d+)?)*)\]")
_MUC_TLTK = re.compile(r"^\s*(?:\[(\d+)\]|(\d+)\.)\s+(.*\S)\s*$")
_PMID = re.compile(r"PMID\s*:?\s*(\d{6,9})", re.IGNORECASE)
_DOI = re.compile(r"(?:doi\s*:?\s*|doi\.org/)(10\.\d{4,9}/[^\s;,]+?)\.?(?=\s|$|;|,)", re.IGNORECASE)
# chú thích máy để lại trong danh mục tham khảo của bản thảo — không đưa vào báo cáo
_CHU_THICH_MAY = re.compile(r"\s*\*\((?:kiểm chứng|cần|chưa)[^)]*\)\*\s*", re.IGNORECASE)


def _chuan(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d")
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


def tach_muc(van: str, mau: str, cap_toi_da: int = 3) -> Optional[str]:
    """Nội dung (không kèm dòng đề mục) của đề mục ĐẦU TIÊN cấp ≤ cap_toi_da khớp ``mau`` (so không dấu), tới đề mục
    kế tiếp cùng cấp hoặc cao hơn. Không thấy ⇒ None."""
    dong = van.splitlines()
    for i, d in enumerate(dong):
        m = _DE_MUC.match(d)
        if not m or len(m.group(1)) > cap_toi_da or not re.search(mau, _chuan(m.group(2))):
            continue
        cap = len(m.group(1))
        j = next((k for k in range(i + 1, len(dong))
                  if (mm := _DE_MUC.match(dong[k])) and len(mm.group(1)) <= cap), len(dong))
        return "\n".join(dong[i + 1:j]).strip("\n")
    return None


def ha_de_muc(van: str, cap: int = 4) -> str:
    """Hạ mọi đề mục trong một khối nguồn xuống ``cap`` (giữ chữ) — bộ kiểm cấu trúc chỉ xét cấp 1–3."""
    return "\n".join(f"{'#' * cap} {m.group(2)}" if (m := _DE_MUC.match(d)) else d for d in van.splitlines())


def doc_tltk(khoi: Optional[str]) -> List[Dict[str, str]]:
    """Tách danh mục tham khảo «1. …» hoặc «[1] …» thành mục có số, chữ, PMID, DOI, khoá tiêu đề."""
    ra: List[Dict[str, str]] = []
    for d in (khoi or "").splitlines():
        m = _MUC_TLTK.match(d)
        if not m:
            continue
        chu = _CHU_THICH_MAY.sub(" ", m.group(3)).strip()
        pm, doi = _PMID.search(chu), _DOI.search(chu)
        ten = re.sub(r"^\[?tác giả\]?\s*et al\.?\s*", "", chu, flags=re.IGNORECASE)
        ra.append({"so": m.group(1) or m.group(2), "chu": chu, "pmid": pm.group(1) if pm else "",
                   "doi": doi.group(1).lower().rstrip(".") if doi else "", "ten": _chuan(ten)[:60]})
    return ra


def _cung_tai_lieu(a: Dict[str, str], b: Dict[str, str]) -> bool:
    if a["pmid"] and b["pmid"]:
        return a["pmid"] == b["pmid"]
    if a["doi"] and b["doi"]:
        return a["doi"] == b["doi"]
    n = min(len(a["ten"]), len(b["ten"]), 40)
    return n >= 25 and a["ten"][:n] == b["ten"][:n]


def gop_tltk(goc: Sequence[Dict[str, str]], them: Sequence[Dict[str, str]]
             ) -> Tuple[List[Dict[str, str]], Dict[str, int], Dict[str, int]]:
    """Danh mục chung: ``goc`` giữ thứ tự; mục của ``them`` trùng (PMID/DOI/tiêu đề) thì dùng số của ``goc``,
    không trùng thì nối cuối. Trả (danh mục, bản đồ số cũ của goc → số mới, bản đồ số cũ của them → số mới)."""
    chung = [dict(x) for x in goc]
    bd_goc = {x["so"]: i + 1 for i, x in enumerate(goc)}
    bd_them: Dict[str, int] = {}
    for x in them:
        k = next((i for i, y in enumerate(chung) if _cung_tai_lieu(x, y)), None)
        if k is None:
            chung.append(dict(x))
            k = len(chung) - 1
        bd_them[x["so"]] = k + 1
    return chung, bd_goc, bd_them


def _mo_rong(nhom: str) -> List[int]:
    so: List[int] = []
    for phan in nhom.split(","):
        phan = phan.strip()
        m = re.match(r"(\d+)\s*[–\-]\s*(\d+)$", phan)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            so.extend(range(a, b + 1) if a <= b else [a, b])
        elif phan.isdigit():
            so.append(int(phan))
    return so


def _gon(so: Sequence[int]) -> str:
    s = sorted(set(so))
    ra, i = [], 0
    while i < len(s):
        j = i
        while j + 1 < len(s) and s[j + 1] == s[j] + 1:
            j += 1
        ra.append(f"{s[i]}–{s[j]}" if j - i >= 2 else ", ".join(str(x) for x in s[i:j + 1]))
        i = j + 1
    return ", ".join(ra)


def doi_so_trich_dan(van: str, ban_do: Dict[str, int]) -> Tuple[str, List[str]]:
    """Đánh số lại mọi «[n]», «[n, m]», «[n–m]» theo ``ban_do``; số không có trong bản đồ giữ nguyên và được báo."""
    thieu: List[str] = []

    def thay(m: "re.Match[str]") -> str:
        moi = []
        for n in _mo_rong(m.group(1)):
            if str(n) in ban_do:
                moi.append(ban_do[str(n)])
            else:
                thieu.append(str(n))
                moi.append(n)
        return f"[{_gon(moi)}]"

    return _TRICH.sub(thay, van), sorted(set(thieu), key=int)


def _bang_bieu(van: str) -> List[str]:
    ra = []
    for d in van.splitlines():
        m = re.match(r"^\s*\**\s*((?:Bảng|Biểu đồ|Hình)\s+\d+(?:\.\d+)*\.?.*?)\**\s*$", d)
        if m:
            ra.append(m.group(1).strip().rstrip("*").strip())
    return ra


def _tim_tep(out_dir: Path, mau: str) -> Optional[Path]:
    ds = sorted(out_dir.glob(mau))
    return ds[0] if ds else None


def sinh(study: str, out_dir: Path) -> Dict[str, object]:
    """Dựng văn bản báo cáo. Trả {"van", "canh_bao", "nguon"} hoặc {"loi"} khi thiếu nguồn bắt buộc."""
    p_dc = _tim_tep(out_dir, f"DE_CUONG_NOP_HOI_DONG_{study}.md")
    p_bt = _tim_tep(out_dir, f"G7_A8_MANUSCRIPT_{study}.md")
    p_dg = _tim_tep(out_dir, f"G6_DIEN_GIAI_{study}.md")
    if not p_dc or not p_bt:
        return {"loi": "thiếu đề cương nộp Hội đồng hoặc bản thảo G7 — báo cáo nghiệm thu chỉ dựng khi đã có kết quả"}
    dc, bt = p_dc.read_text(encoding="utf-8"), p_bt.read_text(encoding="utf-8")
    dg = p_dg.read_text(encoding="utf-8") if p_dg else ""
    canh_bao: List[str] = []

    tl_dc, tl_bt = doc_tltk(tach_muc(dc, r"tai lieu tham khao", 1)), doc_tltk(tach_muc(bt, r"tai lieu tham khao", 2))
    chung, bd_dc, bd_bt = gop_tltk(tl_dc, tl_bt)

    def lay(van: str, mau: str, ten: str, cap: int = 3, bd: Optional[Dict[str, int]] = None) -> str:
        khoi = tach_muc(van, mau, cap)
        if khoi is None:
            canh_bao.append(f"không tìm thấy mục «{ten}» trong nguồn")
            return ""
        khoi = ha_de_muc(khoi)
        if bd is not None:
            khoi, thieu = doi_so_trich_dan(khoi, bd)
            if thieu:
                canh_bao.append(f"«{ten}»: trích dẫn không có trong danh mục: {', '.join(thieu)}")
        return khoi.strip()

    tieu_de = (re.search(r"^##\s+(.+)$", dc, re.MULTILINE) or re.search(r"^#\s+(.+)$", bt, re.MULTILINE))
    ten_de_tai = tieu_de.group(1).strip() if tieu_de else study
    nhan_luc = lay(dc, r"nhan luc", "nhân lực") or lay(dc, r"thong tin chung", "thông tin chung")
    viet_tat = lay(dc, r"chu viet tat", "chữ viết tắt")
    dat_van_de = lay(dc, r"dat van de", "đặt vấn đề", bd=bd_dc)
    muc_tieu = lay(dc, r"^\d*\.?\d*\.?\s*muc tieu$|muc tieu nghien cuu", "mục tiêu", bd=bd_dc)
    tong_quan = lay(dc, r"tong quan", "tổng quan", cap=1, bd=bd_dc) or lay(dc, r"tong quan", "tổng quan", bd=bd_dc)
    phuong_phap = lay(bt, r"phuong phap", "phương pháp (bản thảo)", cap=2, bd=bd_bt)
    ket_qua = lay(bt, r"ket qua", "kết quả (bản thảo)", cap=2, bd=bd_bt)
    ban_luan = lay(bt, r"ban luan", "bàn luận (bản thảo)", cap=2, bd=bd_bt)
    ket_luan = lay(bt, r"ket luan", "kết luận (bản thảo)", cap=2, bd=bd_bt)
    khuyen_nghi = lay(dg, r"ham y|khuyen nghi|kien nghi", "khuyến nghị (diễn giải G6)") if dg else ""
    if not dg:
        canh_bao.append("không có diễn giải G6 — mục khuyến nghị trống")
    phieu = lay(dc, r"phieu thu thap", "phụ lục phiếu thu thập", cap=1)
    bien = lay(dc, r"bang bien|bien so va ma hoa", "phụ lục bảng biến", cap=1)

    than = "\n\n".join([
        "# ĐẶT VẤN ĐỀ", dat_van_de, "**Mục tiêu nghiên cứu**", muc_tieu,
        "# CHƯƠNG 1. TỔNG QUAN TÀI LIỆU", tong_quan,
        "# CHƯƠNG 2. ĐỐI TƯỢNG VÀ PHƯƠNG PHÁP NGHIÊN CỨU", phuong_phap,
        "# CHƯƠNG 3. KẾT QUẢ NGHIÊN CỨU", ket_qua,
        "# CHƯƠNG 4. BÀN LUẬN", ban_luan,
        "# KẾT LUẬN", ket_luan,
        "# KHUYẾN NGHỊ", khuyen_nghi,
        "# TÀI LIỆU THAM KHẢO", "\n".join(f"{i}. {x['chu']}" for i, x in enumerate(chung, 1)),
        "# PHỤ LỤC", "#### Phụ lục 1. Phiếu thu thập số liệu", phieu, "#### Phụ lục 2. Bảng biến số và mã hoá", bien,
    ])
    bang = _bang_bieu(than)
    muc_luc = ["Danh sách cán bộ tham gia thực hiện đề tài", "Danh mục chữ viết tắt", "Danh mục bảng biểu",
               "Đặt vấn đề", "Chương 1. Tổng quan tài liệu", "Chương 2. Đối tượng và phương pháp nghiên cứu",
               "Chương 3. Kết quả nghiên cứu", "Chương 4. Bàn luận", "Kết luận", "Khuyến nghị",
               "Tài liệu tham khảo", "Phụ lục"]
    dau = "\n\n".join([
        "**BÁO CÁO TỔNG HỢP ĐỀ TÀI NGHIÊN CỨU KHOA HỌC CẤP CƠ SỞ**", f"**{ten_de_tai}**",
        "# DANH SÁCH CÁN BỘ THAM GIA THỰC HIỆN ĐỀ TÀI", nhan_luc,
        "# MỤC LỤC", "\n".join(f"- {x}" for x in muc_luc),
        "# DANH MỤC CHỮ VIẾT TẮT", viet_tat,
        "# DANH MỤC BẢNG BIỂU", "\n".join(f"- {x}" for x in bang) or "(Không có bảng, biểu đồ.)",
    ])
    van = re.sub(r"\n{3,}", "\n\n", dau + "\n\n" + than).strip() + "\n"
    return {"van": van, "canh_bao": canh_bao,
            "nguon": {"de_cuong": p_dc.name, "ban_thao": p_bt.name, "dien_giai": p_dg.name if p_dg else None},
            "so_tai_lieu": len(chung)}


def _ghi(p: Path, van: str) -> None:
    tam = p.with_suffix(p.suffix + ".tam")
    tam.write_text(van, encoding="utf-8", newline="\n")
    os.replace(tam, p)


def main(argv: Optional[Sequence[str]] = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Dựng báo cáo tổng hợp kết quả (nghiệm thu) từ tài liệu đề tài")
    ap.add_argument("--study", required=True)
    ap.add_argument("--goc", default=str(REPO), help="thư mục gốc chứa exports/ (mặc định: repo)")
    ap.add_argument("--ghi", action="store_true", help="ghi exports/<mã>/BAO_CAO_TONG_HOP_<mã>.md (mặc định chạy khô)")
    a = ap.parse_args(argv)
    out_dir = Path(a.goc) / "exports" / a.study
    kq = sinh(a.study, out_dir)
    if "loi" in kq:
        print(f"⛔ {kq['loi']}")
        return 2
    van = str(kq["van"])
    print(f"📄 {len(van.split())} từ · {kq['so_tai_lieu']} tài liệu tham khảo · nguồn: {kq['nguon']}")
    for c in kq["canh_bao"]:   # type: ignore[union-attr]
        print(f"  🟠 {c}")
    if a.ghi:
        p = out_dir / MAU_TEP.format(s=a.study)
        _ghi(p, van)
        print(f"✅ Đã ghi {p}")
    else:
        print("(chạy khô — thêm --ghi để ghi tệp)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
